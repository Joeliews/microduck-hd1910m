#!/usr/bin/env python3
"""Short CPU MuJoCo closed loop for official XL330 velstand.onnx.

This is a physics loop: the ONNX action is written into MuJoCo position
actuators and the next observation is read back from the stepped state.
It is not the official training plant. Official velstand
(Mjlab-VelStand-Rough-Backlash-MicroDuck, commit 53fb7d1) runs inside mjlab
on a CUDA Warp sim with the Rhoban BAM M6 actuator, the all-collisions
backlash model, and rough terrain. This script loads scene_walk.xml, whose
blob matches that commit, and uses the XML ``chosen_actuator`` position PD
(kp 0.55, forcerange ±0.96). No domain randomization, no backlash hinges,
no rough heightfield, no action low-pass.

A finished run is evidence that the loop executed. It is not an acceptance
pass, not a board 50 Hz result, and not a Rust-core result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
import urllib.request
from pathlib import Path

import mujoco
import numpy as np
import onnxruntime as ort

POLICY_JOINTS = [
    "left_hip_yaw",
    "left_hip_roll",
    "left_hip_pitch",
    "left_knee",
    "left_ankle",
    "neck_pitch",
    "head_pitch",
    "head_yaw",
    "head_roll",
    "right_hip_yaw",
    "right_hip_roll",
    "right_hip_pitch",
    "right_knee",
    "right_ankle",
]

# Rounded constants from pollen-robotics/microduck duck-control model.rs
# DEFAULT_POSITION, mouth removed. The MJCF STAND keyframe is the plant home.
OFFICIAL_ROUNDED_HOME = np.array(
    [
        0.0,
        -0.0873,
        -0.4579,
        -0.0049,
        0.4530,
        0.3491,
        0.3491,
        0.0,
        0.0,
        0.0,
        0.0873,
        0.4579,
        0.0049,
        -0.4530,
    ],
    dtype=np.float64,
)

VELSTAND_SHA256 = "ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a"
VELSTAND_URL = "https://huggingface.co/pollen-robotics/microduck-policies/resolve/main/velstand.onnx"
SCENE_WALK_BLOB = "7aa25e52b609da73d759c7adc99233c7e63239bc"
ROBOT_WALK_BLOB = "96de481cce278f089145cf07b7088b173a7bbede"

PHYSICS_DT = 0.005
DECIMATION = 4
CONTROL_DT = PHYSICS_DT * DECIMATION
DURATION_S = 4.0
PUSH_TIME_S = 1.0
PUSH_VX = 0.3
FALL_TILT_DEG = 60.0
FALL_HEIGHT_M = 0.05
ACTION_SCALE = 1.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def download_onnx(dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file():
        digest = sha256_file(dest)
        if digest == VELSTAND_SHA256:
            return digest
        dest.unlink()
    urllib.request.urlretrieve(VELSTAND_URL, dest)
    digest = sha256_file(dest)
    if digest != VELSTAND_SHA256:
        raise SystemExit(f"velstand.onnx sha256 {digest} != {VELSTAND_SHA256}")
    return digest


def quat_to_matrix(quat: np.ndarray) -> np.ndarray:
    w, x, y, z = quat
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def sensor(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> np.ndarray:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, name)
    if sid < 0:
        raise SystemExit(f"missing sensor {name}")
    adr = int(model.sensor_adr[sid])
    dim = int(model.sensor_dim[sid])
    return data.sensordata[adr : adr + dim].copy()


def percentile(values: np.ndarray, q: float) -> float:
    if values.size == 0:
        return float("nan")
    return float(np.percentile(values, q))


def load_plant(scene: Path) -> tuple[mujoco.MjModel, np.ndarray, np.ndarray, list[int]]:
    robot_xml = scene.parent / "robot_walk.xml"
    if git_blob_sha1(scene) != SCENE_WALK_BLOB or git_blob_sha1(robot_xml) != ROBOT_WALK_BLOB:
        raise SystemExit("scene_walk.xml / robot_walk.xml blob does not match official 53fb7d1")
    model = mujoco.MjModel.from_xml_path(str(scene))
    model.opt.timestep = PHYSICS_DT
    model.sensor_noise[:] = 0.0
    names = []
    qadr = []
    for act_id in range(model.nu):
        joint_id = int(model.actuator_trnid[act_id, 0])
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_id)
        names.append(name)
        qadr.append(int(model.jnt_qposadr[joint_id]))
    if names != POLICY_JOINTS:
        raise SystemExit(f"actuator joint order {names} != policy order")
    data = mujoco.MjData(model)
    key = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "STAND")
    if key < 0:
        raise SystemExit("STAND keyframe missing")
    mujoco.mj_resetDataKeyframe(model, data, key)
    home = np.array([data.qpos[adr] for adr in qadr], dtype=np.float64)
    home_ctrl = data.ctrl.copy()
    if not np.allclose(home_ctrl, home, atol=1e-9):
        raise SystemExit("STAND ctrl does not match STAND joint positions")
    return model, home, home_ctrl, qadr


def observe(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    home: np.ndarray,
    qadr: list[int],
    last_action: np.ndarray,
) -> np.ndarray:
    quat = sensor(model, data, "orientation")
    gyro = sensor(model, data, "imu_ang_vel")
    gravity = quat_to_matrix(quat).T @ np.array([0.0, 0.0, -1.0])
    q = np.array([data.qpos[adr] for adr in qadr], dtype=np.float64)
    qd = np.array([data.qvel[int(model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)])] for name in POLICY_JOINTS])
    obs = np.zeros(61, dtype=np.float32)
    obs[0:3] = gyro.astype(np.float32)
    obs[3:6] = gravity.astype(np.float32)
    obs[6:20] = (q - home).astype(np.float32)
    obs[20:34] = qd.astype(np.float32)
    obs[34:48] = last_action.astype(np.float32)
    return obs


def trunk_height(model: mujoco.MjModel, data: mujoco.MjData) -> float:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "trunk_base")
    return float(data.xpos[bid, 2])


def run_case(
    model: mujoco.MjModel,
    session: ort.InferenceSession,
    home: np.ndarray,
    home_ctrl: np.ndarray,
    qadr: list[int],
    push: bool,
    renderer: mujoco.Renderer | None,
) -> dict:
    data = mujoco.MjData(model)
    key = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "STAND")
    mujoco.mj_resetDataKeyframe(model, data, key)
    mujoco.mj_forward(model, data)
    last_action = np.zeros(14, dtype=np.float32)
    input_name = session.get_inputs()[0].name
    steps = int(round(DURATION_S / CONTROL_DT))
    push_step = int(round(PUSH_TIME_S / CONTROL_DT))
    wall_ms = np.zeros(steps, dtype=np.float64)
    height = np.zeros(steps, dtype=np.float64)
    tilt = np.zeros(steps, dtype=np.float64)
    action_abs = np.zeros(steps, dtype=np.float64)
    frames = []
    first_fail = None
    fail_steps = []
    obs0 = None
    for step in range(steps):
        t0 = time.perf_counter()
        obs = observe(model, data, home, qadr, last_action)
        if step == 0:
            obs0 = obs.copy()
        action = session.run(None, {input_name: obs.reshape(1, 61)})[0].reshape(14).astype(np.float32)
        last_action = action
        data.ctrl[:] = home_ctrl + ACTION_SCALE * action
        for _ in range(DECIMATION):
            mujoco.mj_step(model, data)
        if push and step == push_step:
            data.qvel[0] += PUSH_VX
            mujoco.mj_forward(model, data)
        wall_ms[step] = (time.perf_counter() - t0) * 1e3
        g = obs[3:6] if step == 0 else observe(model, data, home, qadr, last_action)[3:6]
        # Re-read post-step state for the recorded metrics. The extra observe()
        # above also advances nothing; it only reads sensors.
        post = observe(model, data, home, qadr, last_action)
        g = post[3:6]
        height[step] = trunk_height(model, data)
        tilt[step] = float(np.degrees(np.arccos(np.clip(-g[2], -1.0, 1.0))))
        action_abs[step] = float(np.max(np.abs(action)))
        failed = tilt[step] > FALL_TILT_DEG or height[step] < FALL_HEIGHT_M or not np.isfinite(height[step])
        if failed:
            fail_steps.append(step)
            if first_fail is None:
                first_fail = {
                    "step": step,
                    "t_s": step * CONTROL_DT,
                    "height_m": height[step],
                    "tilt_deg": tilt[step],
                    "qpos": data.qpos.tolist(),
                    "action": action.tolist(),
                }
        if renderer is not None and step % 5 == 0:
            renderer.update_scene(data, camera="track")
            frames.append(renderer.render().copy())
    over_20 = int(np.sum(wall_ms > 20.0))
    return {
        "push_vx_at_1s": PUSH_VX if push else 0.0,
        "steps": steps,
        "duration_s": steps * CONTROL_DT,
        "initial_obs_0_6": obs0[:6].tolist() if obs0 is not None else None,
        "initial_joint_pos_rel_max_abs": float(np.max(np.abs(obs0[6:20]))) if obs0 is not None else None,
        "height_m": {
            "min": float(np.min(height)),
            "max": float(np.max(height)),
            "final": float(height[-1]),
        },
        "tilt_deg": {
            "max": float(np.max(tilt)),
            "final": float(tilt[-1]),
            "p95": percentile(tilt, 95),
        },
        "action_abs_max": float(np.max(action_abs)),
        "fell": first_fail is not None,
        "n_fail_steps": len(fail_steps),
        "first_failure": first_fail,
        "wall_clock_ms": {
            "p50": percentile(wall_ms, 50),
            "p95": percentile(wall_ms, 95),
            "p99": percentile(wall_ms, 99),
            "max": float(np.max(wall_ms)),
            "over_20ms": over_20,
            "scope": "python onnx + 4 mujoco substeps; not Rust; not the board",
        },
        "frames": frames,
        "series": {"height_m": height.tolist(), "tilt_deg": tilt.tolist(), "wall_ms": wall_ms.tolist()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--scene",
        type=Path,
        default=root / "microduck_rl/src/mjlab_microduck/robot/microduck/scene_walk.xml",
    )
    parser.add_argument("--onnx", type=Path, default=Path("/tmp/microduck-policies/velstand.onnx"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    digest = download_onnx(args.onnx)
    model, home, home_ctrl, qadr = load_plant(args.scene)
    session = ort.InferenceSession(str(args.onnx), providers=["CPUExecutionProvider"])
    opts = session.get_session_options()
    renderer = None
    render_error = None
    try:
        renderer = mujoco.Renderer(model, height=360, width=480)
    except Exception as exc:  # noqa: BLE001 — record the GL blocker, keep the physics run
        renderer = None
        render_error = f"{type(exc).__name__}: {exc}"

    global_renderer = renderer

    def run(push: bool) -> dict:
        nonlocal global_renderer
        try:
            result = run_case(model, session, home, home_ctrl, qadr, push, None)
        except Exception:
            raise
        if global_renderer is None:
            result["video"] = None
            return result
        # Second pass only for frames would double the dynamics if noise were on.
        # Sensor noise is zero and the ONNX is deterministic, so a render pass matches.
        data = mujoco.MjData(model)
        key = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "STAND")
        mujoco.mj_resetDataKeyframe(model, data, key)
        mujoco.mj_forward(model, data)
        last_action = np.zeros(14, dtype=np.float32)
        input_name = session.get_inputs()[0].name
        steps = int(round(DURATION_S / CONTROL_DT))
        push_step = int(round(PUSH_TIME_S / CONTROL_DT))
        frames = []
        try:
            for step in range(steps):
                obs = observe(model, data, home, qadr, last_action)
                action = session.run(None, {input_name: obs.reshape(1, 61)})[0].reshape(14).astype(np.float32)
                last_action = action
                data.ctrl[:] = home_ctrl + ACTION_SCALE * action
                for _ in range(DECIMATION):
                    mujoco.mj_step(model, data)
                if push and step == push_step:
                    data.qvel[0] += PUSH_VX
                    mujoco.mj_forward(model, data)
                if step % 5 == 0:
                    cam = mujoco.MjvCamera()
                    mujoco.mjv_defaultFreeCamera(model, cam)
                    trunk = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "trunk_base")
                    cam.lookat[:] = data.xpos[trunk]
                    cam.distance = 0.45
                    cam.azimuth = 140.0
                    cam.elevation = -15.0
                    global_renderer.update_scene(data, camera=cam)
                    frames.append(global_renderer.render().copy())
        except Exception as exc:  # noqa: BLE001
            result["video_error"] = f"{type(exc).__name__}: {exc}"
            frames = []
        result["frames"] = frames
        return result

    cases = {}
    for name, push in (("stand_zero", False), ("stand_push_0.3mps", True)):
        raw = run(push)
        frames = raw.pop("frames")
        gif_name = None
        if frames:
            gif_name = f"{name}.gif"
            from PIL import Image

            images = [Image.fromarray(frame) for frame in frames]
            images[0].save(
                args.out / gif_name,
                save_all=True,
                append_images=images[1:],
                duration=100,
                loop=0,
            )
        series = raw.pop("series")
        np.savez_compressed(args.out / f"{name}.npz", **{k: np.asarray(v) for k, v in series.items()})
        raw["video_gif"] = gif_name
        raw["series_npz"] = f"{name}.npz"
        cases[name] = raw
        print(
            name,
            "fell" if raw["fell"] else "upright_window",
            "height_min",
            round(raw["height_m"]["min"], 4),
            "tilt_max",
            round(raw["tilt_deg"]["max"], 2),
            "wall_p50_ms",
            round(raw["wall_clock_ms"]["p50"], 3),
        )

    report = {
        "status": "executed_not_acceptance",
        "claim": "CPU MuJoCo XML position-actuator loop ran. Not BAM, not rough, not backlash, not mjlab, not Rust, not board 50 Hz, not a matrix pass.",
        "policy": "velstand",
        "model_sha256": digest,
        "onnxruntime": ort.__version__,
        "mujoco": mujoco.__version__,
        "providers": session.get_providers(),
        "intra_op_note": "session options left at ONNX Runtime defaults; intra_op thread count was not pinned",
        "graph_input": session.get_inputs()[0].name,
        "graph_input_shape": [dim if isinstance(dim, int) else str(dim) for dim in session.get_inputs()[0].shape],
        "graph_output": session.get_outputs()[0].name,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "scene": str(args.scene),
        "scene_walk_git_blob": SCENE_WALK_BLOB,
        "robot_walk_git_blob": ROBOT_WALK_BLOB,
        "official_microduck_rl_commit_for_xml": "53fb7d115b1be79c6d07e8fd4eab311285e16f2a",
        "plant": {
            "xml": "scene_walk.xml + robot_walk.xml chosen_actuator position kp=0.55 forcerange=±0.96",
            "not_used": [
                "Rhoban BAM M6",
                "robot_allcollisions_backlash.xml",
                "rough terrain",
                "domain randomization",
                "deployment head lowpass 0.5 and leg lowpass 0.7",
                "walking action_scale 0.9",
            ],
            "physics_dt_s": PHYSICS_DT,
            "decimation": DECIMATION,
            "control_dt_s": CONTROL_DT,
            "logical_hz": 1.0 / CONTROL_DT,
            "action_scale": ACTION_SCALE,
            "command": "twist 0, head 0, body 0",
            "sensor_noise": "XML noise zeroed for a deterministic run",
            "seed": None,
            "seeds_executed": 1,
            "multi_seed": False,
        },
        "joint_order": POLICY_JOINTS,
        "home_from_stand_keyframe": home.tolist(),
        "home_minus_official_rounded_max_abs": float(np.max(np.abs(home - OFFICIAL_ROUNDED_HOME))),
        "mujoco_gl": __import__("os").environ.get("MUJOCO_GL"),
        "camera": "free lookat trunk_base, distance 0.45 m, azimuth 140, elevation -15; 480x360 every 5th control step",
        "render_error": render_error,
        "session_intra_op_num_threads": opts.intra_op_num_threads,
        "cases": cases,
    }
    (args.out / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    failures = {name: case["first_failure"] for name, case in cases.items() if case["first_failure"]}
    (args.out / "failures.json").write_text(json.dumps(failures, indent=2) + "\n")
    print("wrote", args.out / "metrics.json")


if __name__ == "__main__":
    main()
