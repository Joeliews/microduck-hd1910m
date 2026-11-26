//! XL330 velstand, Rust control core, MuJoCo CPU.
//!
//! `Policy::infer` and `Observation::build` run in this process, and each control
//! tick calls `plant_step_n`, which calls `mj_step`. The plant is `scene_walk.xml`
//! position actuators on a flat floor: not BAM, not rough, not backlash, and not
//! an acceptance pass.
//!
//! Build: `cargo build --example xl330_velstand_mujoco --features mujoco-plant`
//! with `MUJOCO_DIR` containing MuJoCo 3.3.7's header and `libmujoco.so.3.3.7`,
//! and `ORT_DYLIB_PATH` pointing at libonnxruntime (floor 1.23).

use std::env;
use std::fs::{self, File};
use std::io::Write;
use std::os::raw::{c_char, c_int};
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
const PHYSICS_DT: f64 = 0.005;
const DECIMATION: i32 = 4;
const CONTROL_DT: f64 = PHYSICS_DT * DECIMATION as f64;
const DURATION_S: f64 = 4.0;
const PUSH_TIME_S: f64 = 1.0;
const PUSH_VX: f64 = 0.3;
const ACTION_SCALE: f64 = 1.0;
const FALL_TILT_DEG: f64 = 60.0;
const FALL_HEIGHT_M: f64 = 0.05;

fn main() {
    if let Err(err) = run() {
        eprintln!("xl330_velstand_mujoco: {err}");
        std::process::exit(2);
    }
}

fn run() -> Result<(), String> {
    #[cfg(not(feature = "mujoco-plant"))]
    {
        Err("rebuild with --features mujoco-plant".into())
    }
    #[cfg(feature = "mujoco-plant")]
    plant::run_plant()
}

#[cfg(feature = "mujoco-plant")]
mod plant {
    use super::*;

    #[repr(C)]
    struct Plant {
        _private: [u8; 0],
    }
    unsafe extern "C" {
        fn plant_open(xml: *const c_char, err: *mut c_char, err_n: c_int) -> *mut Plant;
        fn plant_close(plant: *mut Plant);
        fn plant_reset_stand(plant: *mut Plant) -> c_int;
        fn plant_set_physics_dt(plant: *mut Plant, dt: f64);
        fn plant_physics_dt(plant: *const Plant) -> f64;
        fn plant_zero_sensor_noise(plant: *mut Plant);
        fn plant_nq(plant: *const Plant) -> c_int;
        fn plant_actuator_joint_names(plant: *const Plant, buf: *mut c_char, n: c_int) -> c_int;
        fn plant_home_ctrl(plant: *const Plant, out: *mut f64);
        fn plant_copy_q(plant: *const Plant, out: *mut f64);
        fn plant_copy_qpos(plant: *const Plant, out: *mut f64);
        fn plant_set_ctrl(plant: *mut Plant, ctrl: *const f64);
        fn plant_step_n(plant: *mut Plant, n: c_int);
        fn plant_kick_vx(plant: *mut Plant, vx: f64);
        fn plant_sense(plant: *const Plant, gyro: *mut f64, quat: *mut f64, qd: *mut f64, trunk_z: *mut f64);
        fn plant_warning_count(plant: *const Plant) -> c_int;
    }

    struct Guard(*mut Plant);
    impl Drop for Guard {
        fn drop(&mut self) { unsafe { plant_close(self.0) } }
    }

    pub(super) struct Sample {
        pub gyro: [f64; 3],
        pub quat: [f64; 4],
        pub q: [f64; 14],
        pub qd: [f64; 14],
        pub trunk_z: f64,
    }

    pub fn run_plant() -> Result<(), String> {
        let mut args = env::args().skip(1);
        let scene = args.next().ok_or("usage: xl330_velstand_mujoco SCENE.xml VELSTAND.onnx OUT_DIR")?;
        let onnx = args.next().ok_or("missing onnx path")?;
        let out = PathBuf::from(args.next().ok_or("missing output directory")?);
        fs::create_dir_all(&out).map_err(|e| e.to_string())?;
        let sha = sha256_file(&onnx)?;
        if sha != EXPECTED_SHA {
            return Err(format!("velstand sha256 {sha} != {EXPECTED_SHA}"));
        }

        let mut err = [0u8; 1024];
        let scene_c = std::ffi::CString::new(scene.clone()).map_err(|e| e.to_string())?;
        let raw = unsafe { plant_open(scene_c.as_ptr(), err.as_mut_ptr() as *mut c_char, err.len() as c_int) };
        if raw.is_null() {
            let message = cstr(&err);
            let report = json!({"status": "blocked", "error": message, "model_sha256": sha, "scene": scene});
            fs::write(out.join("metrics.json"), serde_json::to_string_pretty(&report).unwrap() + "\n").map_err(|e| e.to_string())?;
            return Err(message);
        }
        let plant = Guard(raw);
        unsafe {
            plant_set_physics_dt(plant.0, PHYSICS_DT);
            plant_zero_sensor_noise(plant.0);
        }
        let names = actuator_names(plant.0)?;
        if names != POLICY_JOINTS {
            return Err(format!("actuator order {names} != policy order"));
        }
        let nq = unsafe { plant_nq(plant.0) };

        let mut policy = Policy::load(
            &PolicyPaths { walk: onnx.into(), ..Default::default() },
            0.05,
        )
        .map_err(|e| e.to_string())?;

        let mut cases = serde_json::Map::new();
        let mut failures = serde_json::Map::new();
        let mut exception = false;
        for (name, push) in [("stand_zero", false), ("stand_push_0.3mps", true)] {
            let case = run_case(plant.0, &mut policy, nq, push, &out, name)?;
            if case.get("exception").and_then(|v| v.as_bool()) == Some(true) {
                exception = true;
            }
            let fail = &case["first_failure"];
            if !fail.is_null() {
                failures.insert(name.to_string(), fail.clone());
            }
            println!(
                "{name} {} height_min {:.4} tilt_max {:.2} wall_p50_ms {:.3}",
                if case["fell"].as_bool().unwrap_or(false) { "fell" } else { "upright_window" },
                case["height_m"]["min"].as_f64().unwrap_or(f64::NAN),
                case["tilt_deg"]["max"].as_f64().unwrap_or(f64::NAN),
                case["wall_clock_ms"]["p50"].as_f64().unwrap_or(f64::NAN),
            );
            cases.insert(name.to_string(), Value::Object(case));
        }

        let report = json!({
            "status": "executed_not_acceptance",
            "claim": "Rust Policy::infer called mj_step through plant_step_n. XML position PD, flat scene_walk, one deterministic run. Not BAM, not rough, not backlash, not board realtime, not an acceptance pass.",
            "policy": "velstand",
            "model_sha256": sha,
            "onnx_metadata_action_scale": ACTION_SCALE,
            "normalization": "raw 61-vector into the ONNX graph; Sub/Div lives inside the file and this loop does not normalize again",
            "loop_state": "feed-forward graph; Policy has no reset. Each case zeroes last_action and reloads the STAND keyframe.",
            "joint_order": POLICY_JOINTS.split(',').collect::<Vec<_>>(),
            "scene": scene,
            "physics_dt_s": unsafe { plant_physics_dt(plant.0) },
            "decimation": DECIMATION,
            "control_dt_s": CONTROL_DT,
            "logical_hz": 1.0 / CONTROL_DT,
            "action_scale": ACTION_SCALE,
            "terrain": "flat plane in scene_walk.xml",
            "roller_mode": false,
            "seed": null,
            "seeds_executed": 1,
            "multi_seed": false,
            "timeout_policy": "a control tick whose wall time exceeds 20 ms is a timeout. Physics steps are not skipped.",
            "dropped_frame_policy": "logical ticks are never dropped, so dropped_frames is 0 even if a tick overruns the wall-clock budget",
            "exception_policy": "an inference error or a non-finite state stops that case, is written into failures.json, and the process exits 2 after the report is on disk",
            "git_head": command_stdout("git", &["rev-parse", "HEAD"]),
            "rustc": command_stdout("rustup", &["run", "1.89.0", "rustc", "--version"]),
            "intra_op_threads": 1,
            "cases": cases,
        });
        fs::write(out.join("metrics.json"), serde_json::to_string_pretty(&report).unwrap() + "\n").map_err(|e| e.to_string())?;
        fs::write(out.join("failures.json"), serde_json::to_string_pretty(&Value::Object(failures)).unwrap() + "\n").map_err(|e| e.to_string())?;
        println!("wrote {}", out.join("metrics.json").display());
        if exception {
            return Err("control loop stopped on an exception; see failures.json".into());
        }
        Ok(())
    }

    fn run_case(
        plant: *mut Plant,
        policy: &mut Policy,
        nq: c_int,
        push: bool,
        out: &std::path::Path,
        name: &str,
    ) -> Result<serde_json::Map<String, Value>, String> {
        if unsafe { plant_reset_stand(plant) } != 0 {
            return Err("STAND keyframe missing".into());
        }
        let mut home_q = [0.0; 14];
        let mut home_ctrl = [0.0; 14];
        unsafe {
            plant_copy_q(plant, home_q.as_mut_ptr());
            plant_home_ctrl(plant, home_ctrl.as_mut_ptr());
        }
        let mut last_action = [0.0f32; 14];
        let steps = (DURATION_S / CONTROL_DT).round() as usize;
        let push_step = (PUSH_TIME_S / CONTROL_DT).round() as usize;
        let mut wall_ms = Vec::with_capacity(steps);
        let mut height = Vec::with_capacity(steps);
        let mut tilt = Vec::with_capacity(steps);
        let mut action_abs = Vec::with_capacity(steps);
        let mut series = File::create(out.join(format!("{name}.series.csv"))).map_err(|e| e.to_string())?;
        writeln!(series, "step,height_m,tilt_deg,wall_ms").map_err(|e| e.to_string())?;
        let mut qpos_log = File::create(out.join(format!("{name}.qpos.csv"))).map_err(|e| e.to_string())?;
        let warnings_before = unsafe { plant_warning_count(plant) };
        let mut first_failure: Option<Value> = None;
        let mut n_fail = 0usize;
        let mut exception = false;
        let mut obs0 = None;
        let mut rel0 = 0.0f32;

        for step in 0..steps {
            let t0 = Instant::now();
            let sample = sense(plant);
            let obs = observation(&sample, &home_q, &last_action);
            if step == 0 {
                obs0 = Some(obs.as_slice()[0..6].to_vec());
                rel0 = obs.as_slice()[6..20].iter().copied().map(f32::abs).fold(0.0, f32::max);
            }
            let action = match policy.infer(&obs, Net::Walk) {
                Ok(action) if action.iter().all(|v| v.is_finite()) => action,
                Ok(_) => {
                    exception = true;
                    first_failure = Some(json!({"step": step, "error": "non-finite action"}));
                    wall_ms.push(t0.elapsed().as_secs_f64() * 1e3);
                    break;
                }
                Err(err) => {
                    exception = true;
                    first_failure = Some(json!({"step": step, "error": err.to_string()}));
                    wall_ms.push(t0.elapsed().as_secs_f64() * 1e3);
                    break;
                }
            };
            last_action = action;
            let mut ctrl = [0.0; 14];
            for i in 0..14 {
                ctrl[i] = home_ctrl[i] + ACTION_SCALE * f64::from(action[i]);
            }
            unsafe {
                plant_set_ctrl(plant, ctrl.as_ptr());
                plant_step_n(plant, DECIMATION);
                if push && step == push_step {
                    plant_kick_vx(plant, PUSH_VX);
                }
            }
            let elapsed = t0.elapsed().as_secs_f64() * 1e3;
            wall_ms.push(elapsed);
            let post = sense(plant);
            if !post.trunk_z.is_finite() {
                exception = true;
                first_failure = Some(json!({"step": step, "error": "non-finite trunk height"}));
                break;
            }
            let tilt_deg = tilt_from_gz(gravity(&post.quat)[2]);
            height.push(post.trunk_z);
            tilt.push(tilt_deg);
            action_abs.push(action.iter().copied().map(f32::abs).fold(0.0, f32::max) as f64);
            writeln!(series, "{step},{:.6},{:.6},{:.6}", post.trunk_z, tilt_deg, elapsed).map_err(|e| e.to_string())?;
            write_qpos(&mut qpos_log, plant, nq)?;
            if tilt_deg > FALL_TILT_DEG || post.trunk_z < FALL_HEIGHT_M {
                n_fail += 1;
                if first_failure.is_none() {
                    first_failure = Some(json!({
                        "step": step,
                        "t_s": step as f64 * CONTROL_DT,
                        "height_m": post.trunk_z,
                        "tilt_deg": tilt_deg,
                        "action": action,
                    }));
                }
            }
        }

        let over = wall_ms.iter().filter(|v| **v > 20.0).count();
        let home_delta = home_q.iter().zip(rounded_home()).map(|(a, b)| (a - b).abs()).fold(0.0, f64::max);
        let mut map = serde_json::Map::new();
        map.insert("push_vx_at_1s".into(), json!(if push { PUSH_VX } else { 0.0 }));
        map.insert("steps".into(), json!(height.len()));
        map.insert("duration_s".into(), json!(height.len() as f64 * CONTROL_DT));
        map.insert("initial_obs_0_6".into(), json!(obs0));
        map.insert("initial_joint_pos_rel_max_abs".into(), json!(rel0));
        map.insert("home_minus_official_rounded_max_abs".into(), json!(home_delta));
        map.insert("height_m".into(), json!({"min": vmin(&height), "max": vmax(&height), "final": height.last().copied()}));
        map.insert("tilt_deg".into(), json!({"max": vmax(&tilt), "final": tilt.last().copied(), "p95": percentile(&tilt, 95.0)}));
        map.insert("action_abs_max".into(), json!(vmax(&action_abs)));
        map.insert("fell".into(), json!(n_fail > 0));
        map.insert("n_fail_steps".into(), json!(n_fail));
        map.insert("exception".into(), json!(exception));
        map.insert("first_failure".into(), first_failure.unwrap_or(Value::Null));
        map.insert("wall_clock_ms".into(), json!({
            "p50": percentile(&wall_ms, 50.0),
            "p95": percentile(&wall_ms, 95.0),
            "p99": percentile(&wall_ms, 99.0),
            "max": vmax(&wall_ms),
            "over_20ms": over,
            "scope": "rust Policy::infer plus 4 mj_step calls; not the board",
        }));
        map.insert("dropped_frames".into(), json!(0));
        map.insert("mujoco_warnings_during_case".into(), json!(unsafe { plant_warning_count(plant) } - warnings_before));
        map.insert("series_csv".into(), json!(format!("{name}.series.csv")));
        map.insert("qpos_csv".into(), json!(format!("{name}.qpos.csv")));
        Ok(map)
    }

    fn sense(plant: *mut Plant) -> Sample {
        let mut gyro = [0.0; 3];
        let mut quat = [0.0; 4];
        let mut qd = [0.0; 14];
        let mut q = [0.0; 14];
        let mut trunk_z = 0.0;
        unsafe {
            plant_sense(plant, gyro.as_mut_ptr(), quat.as_mut_ptr(), qd.as_mut_ptr(), &mut trunk_z);
            plant_copy_q(plant, q.as_mut_ptr());
        }
        Sample { gyro, quat, q, qd, trunk_z }
    }

    fn write_qpos(file: &mut File, plant: *mut Plant, nq: c_int) -> Result<(), String> {
        let mut qpos = vec![0.0; nq as usize];
        unsafe { plant_copy_qpos(plant, qpos.as_mut_ptr()) };
        for (i, value) in qpos.iter().enumerate() {
            if i > 0 { write!(file, ",").map_err(|e| e.to_string())?; }
            write!(file, "{value:.8}").map_err(|e| e.to_string())?;
        }
        writeln!(file).map_err(|e| e.to_string())
    }

    fn actuator_names(plant: *mut Plant) -> Result<String, String> {
        let mut buf = vec![0u8; 512];
        let rc = unsafe { plant_actuator_joint_names(plant, buf.as_mut_ptr() as *mut c_char, buf.len() as c_int) };
        if rc != 0 { return Err("could not read actuator joint names".into()); }
        Ok(cstr(&buf))
    }
}

fn mouth_index() -> usize {
    JOINT_NAMES.iter().position(|name| *name == "mouth").expect("mouth joint")
}

fn with_mouth(q14: &[f64; 14]) -> [f64; NUM_JOINTS] {
    let mut out = [0.0; NUM_JOINTS];
    let mut slot = 0;
    for joint in 0..NUM_JOINTS {
        if joint == mouth_index() { continue; }
        out[joint] = q14[slot];
        slot += 1;
    }
    out
}

fn rounded_home() -> [f64; 14] {
    let mut home = [0.0; 14];
    let mut slot = 0;
    for (i, value) in DEFAULT_POSITION.iter().enumerate() {
        if i == mouth_index() { continue; }
        home[slot] = *value;
        slot += 1;
    }
    home
}

fn gravity(quat: &[f64; 4]) -> [f64; 3] {
    let (w, x, y, z) = (quat[0], quat[1], quat[2], quat[3]);
    let r20 = 2.0 * (x * z - y * w);
    let r21 = 2.0 * (y * z + x * w);
    let r22 = 1.0 - 2.0 * (x * x + y * y);
    [-r20, -r21, -r22]
}

fn tilt_from_gz(gz: f64) -> f64 {
    (-gz).clamp(-1.0, 1.0).acos().to_degrees()
}

#[cfg(feature = "mujoco-plant")]
fn observation(sample: &plant::Sample, home_q: &[f64; 14], last_action: &[f32; 14]) -> Observation {
    let imu = ImuData { gyro: sample.gyro, gravity: gravity(&sample.quat), quat: sample.quat };
    Observation::build(&imu, &with_mouth(&sample.q), &with_mouth(&sample.qd), &with_mouth(home_q), last_action, &ObsCommand::default())
}

fn percentile(values: &[f64], q: f64) -> f64 {
    if values.is_empty() { return f64::NAN; }
    let mut v = values.to_vec();
    v.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let pos = (q / 100.0) * (v.len() - 1) as f64;
    let lo = pos.floor() as usize;
    let hi = pos.ceil() as usize;
    v[lo] * (1.0 - (pos - lo as f64)) + v[hi] * (pos - lo as f64)
}

fn vmin(values: &[f64]) -> Option<f64> { values.iter().copied().reduce(f64::min) }
fn vmax(values: &[f64]) -> Option<f64> { values.iter().copied().reduce(f64::max) }

fn cstr(buf: &[u8]) -> String {
    let n = buf.iter().position(|b| *b == 0).unwrap_or(buf.len());
    String::from_utf8_lossy(&buf[..n]).into_owned()
}

fn sha256_file(path: &str) -> Result<String, String> {
    let bytes = std::fs::read(path).map_err(|e| e.to_string())?;
    let digest = Sha256::digest(bytes);
    Ok(digest.iter().map(|byte| format!("{byte:02x}")).collect())
}

fn command_stdout(cmd: &str, args: &[&str]) -> String {
    Command::new(cmd).args(args).output().ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "unknown".into())
}
