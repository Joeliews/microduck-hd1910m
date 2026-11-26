#!/usr/bin/env python3
"""Official velstand plant sidecar for the Rust control loop.

Imports ``pollen-robotics/microduck_rl`` from ``MICRODUCK_RL_OFFICIAL``. The
fork tree ``microduck_rl/`` is refused. The plant is one environment of
``Mjlab-VelStand-Rough-Backlash-MicroDuck``: BAM M6, encoder-through-backlash,
all-collisions backlash XML, mjlab rough terrain. One ``env.step`` is one
logical 20 ms tick (physics 0.005 s, decimation 4).

This process does not train. It does not modify the official checkout.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_COMMIT = "0daab160d3fb1c2cbaba16a4a19052f36709dd9e"
BAM_LOCK = "62bd8ce12154340be97e06f7f41a0ca8f116d967"
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
PLANT_ID = "bam_m6_allcollisions_backlash_rough"


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def git(root: Path, *args: str) -> str:
    out = subprocess.check_output(["git", "-C", str(root), *args], text=True)
    return out.strip()


def require_official_checkout() -> Path:
    raw = os.environ.get("MICRODUCK_RL_OFFICIAL", "").strip()
    if not raw:
        fail("set MICRODUCK_RL_OFFICIAL to a pollen-robotics/microduck_rl checkout; the fork copy is not the official stack")
    root = Path(raw).resolve()
    if not (root / ".git").exists():
        fail(f"{root} is not a git checkout")
    remote = git(root, "remote", "get-url", "origin")
    if "pollen-robotics/microduck_rl" not in remote:
        fail(f"refusing {remote}; official plant must come from pollen-robotics/microduck_rl")
    head = git(root, "rev-parse", "HEAD")
    if head != EXPECTED_COMMIT:
        fail(f"checkout {head} != required {EXPECTED_COMMIT}")
    lock = (root / "uv.lock").read_text(errors="replace")
    if BAM_LOCK not in lock:
        fail(f"uv.lock does not pin BAM {BAM_LOCK}")
    return root


def build_env(device: str, seed: int):
    import torch
    from mjlab.envs import ManagerBasedRlEnv
    from mjlab_microduck.robot.microduck_constants import MICRODUCK_ALLCOLLISIONS_BACKLASH_ROBOT_CFG
    from mjlab_microduck.tasks.backlash import make_backlash_variant
    from mjlab_microduck.tasks.microduck_velstand_env_cfg import make_microduck_velstand_env_cfg

    cfg = make_microduck_velstand_env_cfg(play=False, rough=True)
    cfg = make_backlash_variant(cfg, MICRODUCK_ALLCOLLISIONS_BACKLASH_ROBOT_CFG)
    if cfg.scene.terrain.terrain_type != "generator":
        fail(f"terrain_type is {cfg.scene.terrain.terrain_type}, wanted generator (rough)")
    dt = float(cfg.sim.mujoco.timestep)
    decimation = int(cfg.decimation)
    if abs(dt - 0.005) > 1e-9 or decimation != 4:
        fail(f"official step is not 0.005 x 4 (got {dt} x {decimation})")
    actuator_names = [type(item).__name__ for item in cfg.scene.entities["robot"].articulation.actuators]
    if not any("Bam" in name and "Backlash" in name for name in actuator_names):
        fail(f"actuators {actuator_names} are not Backlash encoder BAM")
    for key in ("fallen_too_long", "time_out", "fell_over"):
        cfg.terminations.pop(key, None)
    # A 4 s window should not be kicked by the training pushes. Dropping the
    # event without its curriculum term makes reset call push_curriculum and
    # raise "Event term 'topple_push' not found".
    for key in ("push_robot", "topple_push"):
        cfg.events.pop(key, None)
    drop_curricula_for_missing_events(cfg)
    cfg.scene.num_envs = 1
    cfg.seed = seed
    env = ManagerBasedRlEnv(cfg=cfg, device=device)
    return env, dt, decimation, actuator_names


def curriculum_event_name(term):
    params = getattr(term, "params", None)
    if isinstance(params, dict):
        return params.get("event_name")
    return getattr(params, "event_name", None)


def drop_curricula_for_missing_events(cfg) -> None:
    active = set(cfg.events)
    for name in list(cfg.curriculum):
        event_name = curriculum_event_name(cfg.curriculum[name])
        if event_name is not None and event_name not in active:
            cfg.curriculum.pop(name)
    if "topple_push" not in cfg.events and "topple_push_range" in cfg.curriculum:
        fail("topple_push_range is still registered after topple_push was removed")


def as_list(tensor) -> list[float]:
    return [float(v) for v in tensor.detach().cpu().reshape(-1)]


def sense(env) -> dict:
    robot = env.scene["robot"]
    names = list(robot.joint_names)
    name_to_id = {name: i for i, name in enumerate(names)}
    missing = [name for name in POLICY_JOINTS if name not in name_to_id or f"passive_{name}_backlash" not in name_to_id]
    if missing:
        fail(f"backlash plant is missing servo or encoder joint for {missing}")
    qpos = robot.data.joint_pos[0]
    qvel = robot.data.joint_vel[0]
    default = robot.data.default_joint_pos[0]
    q, qd, home = [], [], []
    for name in POLICY_JOINTS:
        main = name_to_id[name]
        backlash = name_to_id[f"passive_{name}_backlash"]
        # Encoder sits on the output side of the gear play: servo plus backlash hinge.
        q.append(float(qpos[main] + qpos[backlash]))
        qd.append(float(qvel[main] + qvel[backlash]))
        home.append(float(default[main]))
    data = robot.data
    gyro = getattr(data, "root_link_ang_vel_b", None)
    if gyro is None:
        gyro = data.root_ang_vel_b
    gravity = data.projected_gravity_b
    origin = float(env.scene.env_origins[0, 2])
    trunk_z = float(data.root_link_pos_w[0, 2]) - origin
    return {
        "ok": True,
        "q": q,
        "qd": qd,
        "home": home,
        "gyro": as_list(gyro[0]),
        "gravity": as_list(gravity[0]),
        "trunk_z": trunk_z,
    }


def scatter(action: list[float], index: dict[str, int], width: int):
    import torch

    if len(action) != len(POLICY_JOINTS):
        fail("action width is not 14")
    out = torch.zeros(width, dtype=torch.float32)
    for name, value in zip(POLICY_JOINTS, action):
        out[index[name]] = float(value)
    return out


def processed_policy_action(term, index: dict[str, int]) -> list[float] | None:
    """Plant action after env.step, in policy joint order.

    This is not the ONNX output. Callers must not substitute it for the Rust action.
    """
    tensor = getattr(term, "processed_actions", None)
    if tensor is None:
        tensor = getattr(term, "_processed_actions", None)
    if tensor is None:
        return None
    flat = as_list(tensor[0] if getattr(tensor, "ndim", 1) > 1 else tensor)
    if any(index[name] >= len(flat) for name in POLICY_JOINTS):
        return None
    return [flat[index[name]] for name in POLICY_JOINTS]


def action_joint_names(term) -> list[str]:
    """Names in JointPositionAction order.

    mjlab 1.3.0 stores them on BaseAction as ``_target_names`` and exposes
    ``target_names``. It does not have ``joint_names`` or ``_joint_names``.
    ``_target_ids`` index ``_entity.joint_names`` in that same order.
    """
    public = getattr(term, "target_names", None)
    if public:
        return [str(name) for name in public]
    stored = getattr(term, "_target_names", None)
    if stored:
        return [str(name) for name in stored]
    entity = getattr(term, "_entity", None)
    ids = getattr(term, "_target_ids", None)
    if entity is None or ids is None:
        fail("JointPositionAction has no target_names, _target_names, or _entity/_target_ids")
    joint_names = list(entity.joint_names)
    resolved = []
    for raw in ids.detach().cpu().reshape(-1):
        index = int(raw)
        if index < 0 or index >= len(joint_names):
            fail(f"action target id {index} is outside joint_names ({len(joint_names)})")
        resolved.append(joint_names[index])
    return resolved


def serve(host: str, port: int, device: str, seed: int) -> None:
    root = require_official_checkout()
    sys.path.insert(0, str(root / "src"))
    os.chdir(root)
    env, dt, decimation, actuators = build_env(device, seed)
    term = env.action_manager.get_term("joint_pos")
    action_names = action_joint_names(term)
    missing = [name for name in POLICY_JOINTS if name not in action_names]
    if missing:
        fail(f"action term is missing {missing}")
    index = {name: action_names.index(name) for name in POLICY_JOINTS}
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((host, port))
    listener.listen(1)
    bound = listener.getsockname()[1]
    print(f"ready port={bound} plant={PLANT_ID} commit={EXPECTED_COMMIT}", flush=True)
    conn, _addr = listener.accept()
    reader = conn.makefile("r", encoding="utf-8")
    writer = conn.makefile("w", encoding="utf-8")

    def send(payload: dict) -> None:
        writer.write(json.dumps(payload) + "\n")
        writer.flush()

    try:
        for line in reader:
            msg = json.loads(line)
            op = msg.get("op")
            if op == "hello":
                send({
                    "ok": True,
                    "plant": PLANT_ID,
                    "commit": EXPECTED_COMMIT,
                    "bam_lock": BAM_LOCK,
                    "actuators": actuators,
                    "physics_dt": dt,
                    "decimation": decimation,
                    "control_dt": dt * decimation,
                    "rough": True,
                    "joint_names": POLICY_JOINTS,
                    "fork_tree": False,
                })
            elif op == "reset":
                env.reset()
                send(sense(env))
            elif op == "step":
                raw_action = msg["action"]
                action = scatter(raw_action, index, len(action_names)).to(env.device).unsqueeze(0)
                started = time.perf_counter()
                env.step(action)
                env_step_ms = (time.perf_counter() - started) * 1e3
                payload = sense(env)
                payload["env_step_ms"] = env_step_ms
                if msg.get("echo"):
                    payload["received_action"] = [float(v) for v in raw_action]
                    processed = processed_policy_action(term, index)
                    if processed is not None:
                        payload["processed_action"] = processed
                send(payload)
            elif op == "close":
                send({"ok": True})
                return
            else:
                send({"ok": False, "error": f"unknown op {op}"})
    finally:
        conn.close()
        listener.close()
        env.close()


def main() -> None:
    host = "127.0.0.1"
    port = 0
    device = os.environ.get("OFFICIAL_PLANT_DEVICE", "cuda:0")
    seed = int(os.environ.get("OFFICIAL_PLANT_SEED", "0"))
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--host":
            host = args[i + 1]
            i += 2
        elif args[i] == "--port":
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--device":
            device = args[i + 1]
            i += 2
        elif args[i] == "--seed":
            seed = int(args[i + 1])
            i += 2
        else:
            fail(f"unknown argument {args[i]}")
    serve(host, port, device, seed)


if __name__ == "__main__":
    main()
