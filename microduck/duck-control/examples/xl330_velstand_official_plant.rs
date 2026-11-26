//! XL330 velstand against the official BAM plant.
//!
//! Rust owns `Policy::infer`, `Observation::build`, and the 50 Hz clock.
//! Physics is one step of the sidecar `scripts/closed_loop/official_velstand_plant.py`,
//! which must identify itself as BAM M6 + all-collisions backlash + rough.
//! `scene_walk.xml` and XML position PD are not this plant.
//!
//! A finished window is `executed_not_acceptance`. A missing sidecar writes
//! `blocked` and invents no timing numbers. This binary does not claim the
//! user's GPU already ran it.

use std::env;
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::net::TcpStream;
use std::path::PathBuf;
use std::process::Command;
use std::time::Instant;

use duck_control::imu::ImuData;
use duck_control::obs::{Command as ObsCommand, Observation};
use duck_control::policy::{Net, Policy, PolicyPaths};
use duck_control::{DEFAULT_POSITION, JOINT_NAMES, NUM_JOINTS};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const POLICY_JOINTS: &str = "left_hip_yaw,left_hip_roll,left_hip_pitch,left_knee,left_ankle,neck_pitch,head_pitch,head_yaw,head_roll,right_hip_yaw,right_hip_roll,right_hip_pitch,right_knee,right_ankle";
const EXPECTED_SHA: &str = "ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a";
const PLANT_ID: &str = "bam_m6_allcollisions_backlash_rough";
const CONTROL_DT: f64 = 0.02;
const DURATION_S: f64 = 4.0;
const FALL_TILT_DEG: f64 = 60.0;
const FALL_HEIGHT_M: f64 = 0.05;

fn main() {
    if let Err(err) = run() {
        eprintln!("xl330_velstand_official_plant: {err}");
        std::process::exit(2);
    }
}

fn run() -> Result<(), String> {
    let mut onnx = None;
    let mut addr = None;
    let mut out = None;
    let mut compare = false;
    let mut args = env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--onnx" => onnx = args.next(),
            "--addr" => addr = args.next(),
            "--out" => out = args.next(),
            "--compare" => compare = true,
            other => return Err(format!("unknown argument {other}")),
        }
    }
    let onnx = onnx.ok_or("usage: xl330_velstand_official_plant --onnx VELSTAND.onnx --addr HOST:PORT --out DIR [--compare]")?;
    let addr = addr.ok_or("missing --addr")?;
    let out = PathBuf::from(out.ok_or("missing --out")?);
    fs::create_dir_all(&out).map_err(|e| e.to_string())?;
    let sha = sha256_file(&onnx)?;
    if sha != EXPECTED_SHA {
        let report = json!({
            "status": "blocked",
            "error": format!("sha256 {sha} != official velstand {EXPECTED_SHA}"),
            "model_sha256": sha,
        });
        fs::write(out.join("metrics.json"), serde_json::to_string_pretty(&report).unwrap() + "\n").ok();
        return Err("refusing a weight that is not the published velstand.onnx".into());
    }

    let stream = match TcpStream::connect(&addr) {
        Ok(stream) => stream,
        Err(err) => {
            let report = json!({
                "status": "blocked",
                "error": format!("sidecar not connected at {addr}: {err}"),
                "model_sha256": sha,
                "claim": "no official-plant steps were taken",
            });
            fs::write(out.join("metrics.json"), serde_json::to_string_pretty(&report).unwrap() + "\n").map_err(|e| e.to_string())?;
            return Err(err.to_string());
        }
    };
    stream.set_read_timeout(Some(std::time::Duration::from_secs(120))).ok();
    let mut reader = BufReader::new(stream.try_clone().map_err(|e| e.to_string())?);
    let mut writer = stream;

    let hello = rpc(&mut reader, &mut writer, json!({"op": "hello"}))?;
    let names = hello["joint_names"].as_array().map(|items| items.iter().filter_map(|v| v.as_str()).collect::<Vec<_>>().join(","));
    if hello["plant"] != PLANT_ID || hello["rough"] != true || hello["decimation"] != 4 || names.as_deref() != Some(POLICY_JOINTS) {
        let report = json!({
            "status": "blocked",
            "error": "sidecar is not the official BAM rough backlash plant",
            "hello": hello,
            "model_sha256": sha,
        });
        fs::write(out.join("metrics.json"), serde_json::to_string_pretty(&report).unwrap() + "\n").ok();
        return Err("refusing a plant that is not bam_m6_allcollisions_backlash_rough".into());
    }
    let physics_dt = hello["physics_dt"].as_f64().unwrap_or(0.0);
    if (physics_dt - 0.005).abs() > 1e-9 {
        return Err(format!("physics dt {physics_dt} is not 0.005"));
    }

    let mut policy = Policy::load(&PolicyPaths { walk: onnx.into(), ..Default::default() }, 0.05)
        .map_err(|e| e.to_string())?;
    let mut state = rpc(&mut reader, &mut writer, json!({"op": "reset"}))?;
    let mut last_action = [0.0f32; 14];
    let steps = (DURATION_S / CONTROL_DT).round() as usize;
    let mut total_ms = Vec::with_capacity(steps);
    let mut infer_ms = Vec::with_capacity(steps);
    let mut round_trip_ms = Vec::with_capacity(steps);
    let mut env_step_ms: Vec<Option<f64>> = Vec::with_capacity(steps);
    let mut height = Vec::with_capacity(steps);
    let mut tilt = Vec::with_capacity(steps);
    let mut first_failure = Value::Null;
    let mut n_fail = 0usize;
    let mut exception = false;
    let mut cmp_obs: Vec<Vec<f32>> = Vec::new();
    let mut cmp_obs_bits: Vec<Vec<u32>> = Vec::new();
    let mut cmp_action: Vec<Vec<f32>> = Vec::new();
    let mut cmp_action_bits: Vec<Vec<u32>> = Vec::new();
    let mut cmp_received: Vec<Value> = Vec::new();
    let mut cmp_processed: Vec<Value> = Vec::new();

    for step in 0..steps {
        let q = read14(&state, "q")?;
        let qd = read14(&state, "qd")?;
        let home = read14(&state, "home")?;
        let gyro = read3(&state, "gyro")?;
        let gravity = read3(&state, "gravity")?;
        let obs = observation(&q, &qd, &home, gyro, gravity, &last_action);
        let t0 = Instant::now();
        let action = match policy.infer(&obs, Net::Walk) {
            Ok(action) if action.iter().all(|v| v.is_finite()) => action,
            Ok(_) => {
                exception = true;
                first_failure = json!({"step": step, "error": "non-finite action"});
                break;
            }
            Err(err) => {
                exception = true;
                first_failure = json!({"step": step, "error": err.to_string()});
                break;
            }
        };
        let infer_elapsed = t0.elapsed().as_secs_f64() * 1e3;
        last_action = action;
        let t_rpc = Instant::now();
        let step_msg = if compare {
            json!({"op": "step", "action": action, "echo": true})
        } else {
            json!({"op": "step", "action": action})
        };
        state = rpc(&mut reader, &mut writer, step_msg)?;
        let rpc_elapsed = t_rpc.elapsed().as_secs_f64() * 1e3;
        if compare {
            cmp_obs.push(obs.as_slice().to_vec());
            cmp_obs_bits.push(obs.as_slice().iter().map(|v| v.to_bits()).collect());
            cmp_action.push(action.to_vec());
            cmp_action_bits.push(action.iter().map(|v| v.to_bits()).collect());
            cmp_received.push(optional_vector(&state, "received_action", 14));
            cmp_processed.push(optional_vector(&state, "processed_action", 14));
        }
        total_ms.push(t0.elapsed().as_secs_f64() * 1e3);
        infer_ms.push(infer_elapsed);
        round_trip_ms.push(rpc_elapsed);
        env_step_ms.push(state.get("env_step_ms").and_then(Value::as_f64));
        if state.get("ok") == Some(&Value::Bool(false)) {
            exception = true;
            first_failure = json!({"step": step, "error": state});
            break;
        }
        let trunk_z = state["trunk_z"].as_f64().unwrap_or(f64::NAN);
        let g = read3(&state, "gravity")?;
        let tilt_deg = (-g[2]).clamp(-1.0, 1.0).acos().to_degrees();
        height.push(trunk_z);
        tilt.push(tilt_deg);
        if !trunk_z.is_finite() || tilt_deg > FALL_TILT_DEG || trunk_z < FALL_HEIGHT_M {
            n_fail += 1;
            if first_failure.is_null() {
                first_failure = json!({"step": step, "height_m": trunk_z, "tilt_deg": tilt_deg});
            }
        }
    }
    let _ = rpc(&mut reader, &mut writer, json!({"op": "close"}));
    let over = total_ms.iter().filter(|v| **v > 20.0).count();
    let step_times = json!({
        "unit": "ms",
        "budget_ms": 20.0,
        "over_20ms_rule": "count of total_ms strictly greater than 20.0; the budget is not loosened",
        "percentile": "linear interpolation between nearest ranks on the sorted sample, same function as metrics.json",
        "scope": "total_ms is Policy::infer plus one sidecar env.step round trip. infer_ms is only Policy::infer. step_round_trip_ms is the sidecar RPC. env_step_ms is the plant timer around env.step and omits JSON and sense().",
        "total_ms": total_ms.clone(),
        "infer_ms": infer_ms.clone(),
        "step_round_trip_ms": round_trip_ms.clone(),
        "env_step_ms": env_step_ms.clone(),
    });
    fs::write(out.join("step_times.json"), serde_json::to_string_pretty(&step_times).unwrap() + "\n").map_err(|e| e.to_string())?;
    let compare_sha = if compare {
        let dump = json!({
            "status": "executed_not_acceptance",
            "claim": "Closed-loop obs and Rust Policy::infer actions for a later Python ONNX Runtime replay. Not a numeric pass, not 20 ms acceptance, not a new plant trajectory.",
            "obs_len": 61,
            "action_len": 14,
            "control_dt_s": CONTROL_DT,
            "control_hz": 50,
            "obs_layout": "0..3 gyro, 3..6 projected gravity, 6..20 q-home, 20..34 qd, 34..48 previous raw action, 48..61 command. Mouth excluded.",
            "joint_order": POLICY_JOINTS.split(',').collect::<Vec<_>>(),
            "normalization": "Policy::infer feeds this obs to the graph. Sub/Div live inside the published ONNX. The dump is not normalized again.",
            "rust_infer_scale": 1.0,
            "action_scale_note": "Policy::infer returns the raw network output and does not multiply by an action scale. The published velstand manifest action_scale is 1.0. sidecar_processed_action, when present, is the plant term after env.step and is not a substitute for rust_action.",
            "onnx_sha256": sha,
            "rejected_short_train_prefix": "cf280a27",
            "plant": PLANT_ID,
            "official_commit": hello.get("commit").cloned().unwrap_or(Value::Null),
            "bam_lock": hello.get("bam_lock").cloned().unwrap_or(Value::Null),
            "feedforward_contract": true,
            "recurrent_state": false,
            "recurrent_note": "The published velstand manifest is feedforward. This dump has no hidden state to replay. The Python compare checks the session inputs and does not invent a reset.",
            "obs_f32_bits_endian": "little",
            "step": (0..cmp_obs.len()).collect::<Vec<_>>(),
            "obs": cmp_obs,
            "obs_f32_bits": cmp_obs_bits,
            "rust_action": cmp_action,
            "rust_action_f32_bits": cmp_action_bits,
            "sidecar_received_action": cmp_received,
            "sidecar_processed_action": cmp_processed,
        });
        let path = out.join("step_compare.json");
        fs::write(&path, serde_json::to_string_pretty(&dump).unwrap() + "\n").map_err(|e| e.to_string())?;
        Some(sha256_file(path.to_str().ok_or("step_compare path is not utf-8")?)?)
    } else {
        None
    };
    let mut report = json!({
        "status": "executed_not_acceptance",
        "claim": "Rust Policy::infer drove the official BAM rough backlash sidecar. Not an acceptance pass, not the flat XML-PD loop, not a claim that this cloud VM ran the user's GPU.",
        "plant": hello,
        "model_sha256": sha,
        "rejected_short_train_prefix": "cf280a27",
        "logical_hz": 50.0,
        "control_dt_s": CONTROL_DT,
        "physics_dt_s": physics_dt,
        "decimation": 4,
        "seed_note": "sidecar seed is the plant builder seed, not reserved eval seeds 10/11/12",
        "steps": height.len(),
        "duration_s": height.len() as f64 * CONTROL_DT,
        "height_m": {"min": vmin(&height), "max": vmax(&height), "final": height.last().copied()},
        "tilt_deg": {"max": vmax(&tilt), "final": tilt.last().copied(), "p95": percentile(&tilt, 95.0)},
        "fell": n_fail > 0,
        "n_fail_steps": n_fail,
        "exception": exception,
        "first_failure": first_failure,
        "wall_clock_ms": {
            "p50": percentile(&total_ms, 50.0),
            "p95": percentile(&total_ms, 95.0),
            "p99": percentile(&total_ms, 99.0),
            "max": vmax(&total_ms),
            "over_20ms": over,
            "scope": "rust infer plus one official env.step round trip; not the board",
            "samples": "step_times.json",
            "infer_ms": timing_summary(&infer_ms),
            "step_round_trip_ms": timing_summary(&round_trip_ms),
            "env_step_ms": timing_summary_opt(&env_step_ms),
        },
        "dropped_frames": 0,
        "dropped_frame_policy": "logical ticks are not skipped; an overrun is a timeout, not a dropped physics step",
        "git_head": command_stdout("git", &["rev-parse", "HEAD"]),
    });
    if let Some(compare_sha) = compare_sha {
        report["step_compare"] = json!({
            "file": "step_compare.json",
            "sha256": compare_sha,
            "status": "executed_not_acceptance",
            "note": "SHA of the closed-loop dump. compare_report.json, when the wrapper runs it, is the Python replay and is still not a pass or 20 ms acceptance.",
        });
    }
    fs::write(out.join("metrics.json"), serde_json::to_string_pretty(&report).unwrap() + "\n").map_err(|e| e.to_string())?;
    println!("wrote {}", out.join("metrics.json").display());
    if exception {
        return Err("official plant loop stopped on an exception".into());
    }
    Ok(())
}

fn rpc(reader: &mut BufReader<TcpStream>, writer: &mut TcpStream, msg: Value) -> Result<Value, String> {
    writer.write_all(format!("{msg}\n").as_bytes()).map_err(|e| e.to_string())?;
    writer.flush().map_err(|e| e.to_string())?;
    let mut line = String::new();
    let n = reader.read_line(&mut line).map_err(|e| e.to_string())?;
    if n == 0 {
        return Err("sidecar closed the connection".into());
    }
    serde_json::from_str(&line).map_err(|e| e.to_string())
}

fn optional_vector(state: &Value, key: &str, width: usize) -> Value {
    let Some(arr) = state.get(key).and_then(Value::as_array) else {
        return Value::Null;
    };
    if arr.len() != width || arr.iter().any(|v| v.as_f64().is_none()) {
        return Value::Null;
    }
    Value::Array(arr.clone())
}

fn read14(state: &Value, key: &str) -> Result<[f64; 14], String> {
    let arr = state[key].as_array().ok_or_else(|| format!("missing {key}"))?;
    if arr.len() != 14 {
        return Err(format!("{key} width {}", arr.len()));
    }
    let mut out = [0.0; 14];
    for (i, value) in arr.iter().enumerate() {
        out[i] = value.as_f64().ok_or("non-numeric state")?;
    }
    Ok(out)
}

fn read3(state: &Value, key: &str) -> Result<[f64; 3], String> {
    let arr = state[key].as_array().ok_or_else(|| format!("missing {key}"))?;
    if arr.len() != 3 {
        return Err(format!("{key} width {}", arr.len()));
    }
    Ok([
        arr[0].as_f64().unwrap_or(f64::NAN),
        arr[1].as_f64().unwrap_or(f64::NAN),
        arr[2].as_f64().unwrap_or(f64::NAN),
    ])
}

fn mouth_index() -> usize {
    JOINT_NAMES.iter().position(|name| *name == "mouth").expect("mouth")
}

fn with_mouth(q14: &[f64; 14]) -> [f64; NUM_JOINTS] {
    let mut out = [0.0; NUM_JOINTS];
    let mut slot = 0;
    for joint in 0..NUM_JOINTS {
        if joint == mouth_index() {
            continue;
        }
        out[joint] = q14[slot];
        slot += 1;
    }
    out
}

fn observation(q: &[f64; 14], qd: &[f64; 14], home: &[f64; 14], gyro: [f64; 3], gravity: [f64; 3], last: &[f32; 14]) -> Observation {
    let _ = DEFAULT_POSITION;
    let imu = ImuData { gyro, gravity, quat: [1.0, 0.0, 0.0, 0.0] };
    Observation::build(&imu, &with_mouth(q), &with_mouth(qd), &with_mouth(home), last, &ObsCommand::default())
}

fn timing_summary(values: &[f64]) -> Value {
    if values.is_empty() {
        return json!({"p50": null, "p95": null, "p99": null, "max": null});
    }
    json!({
        "p50": percentile(values, 50.0),
        "p95": percentile(values, 95.0),
        "p99": percentile(values, 99.0),
        "max": vmax(values),
    })
}

fn timing_summary_opt(values: &[Option<f64>]) -> Value {
    let present: Vec<f64> = values.iter().copied().flatten().filter(|v| v.is_finite()).collect();
    let mut summary = timing_summary(&present);
    summary["missing"] = json!(values.len() - present.len());
    summary
}

fn percentile(values: &[f64], q: f64) -> f64 {
    if values.is_empty() {
        return f64::NAN;
    }
    let mut v = values.to_vec();
    v.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let pos = (q / 100.0) * (v.len() - 1) as f64;
    let lo = pos.floor() as usize;
    let hi = pos.ceil() as usize;
    v[lo] * (1.0 - (pos - lo as f64)) + v[hi] * (pos - lo as f64)
}

fn vmin(values: &[f64]) -> Option<f64> { values.iter().copied().filter(|v| v.is_finite()).reduce(f64::min) }
fn vmax(values: &[f64]) -> Option<f64> { values.iter().copied().filter(|v| v.is_finite()).reduce(f64::max) }

fn sha256_file(path: &str) -> Result<String, String> {
    let bytes = std::fs::read(path).map_err(|e| e.to_string())?;
    Ok(Sha256::digest(bytes).iter().map(|byte| format!("{byte:02x}")).collect())
}

fn command_stdout(cmd: &str, args: &[&str]) -> String {
    Command::new(cmd).args(args).output().ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "unknown".into())
}
