#!/usr/bin/env python3
"""HD-1910 conditional-sim plant. Not an acceptance run.

The scene stays the official velstand plant: all-collisions backlash XML,
rough terrain, physics 0.005 s, decimation 4. The actuator is the Feetech
7.4 V BAM m6 from an isolated ``ftservo/ftservo-bam`` checkout at
``bab3967811f0bec8b79898cb03e7f5812fe581f9``. This process does not edit that
checkout, does not edit the official-rl pin of Rhoban BAM
``62bd8ce12154340be97e06f7f41a0ca8f116d967``, and does not treat PyPI
``better-actuator-models==1.0.2`` as the parameter source.

Without ``HD_CONDITIONAL_SIM_RUN=1`` it exits before building an environment
and writes no result. A later authorized run is still conditional sim, not
on-machine identification and not real-robot acceptance.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

RL_COMMIT = "0daab160d3fb1c2cbaba16a4a19052f36709dd9e"
RHODAN_BAM_PIN = "62bd8ce12154340be97e06f7f41a0ca8f116d967"
FT_COMMIT = "bab3967811f0bec8b79898cb03e7f5812fe581f9"
M6_SHA = "81a441fb921130bcc9bcfbd9ee0c77e3c38d9ab758bc7e0559fb029c436355ba"
MOTOR_NAME = "feetech_hd1910_7_4V"
MODEL_NAME = "m6"
KP_FW = 32.0
VIN = 7.4
PLANT_ID = "hd1910_ftservo_official_m6_allcollisions_backlash_rough"
M6_REL = Path("bam/params/feetech_hd1910_7_4V/m6.json")


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def git(root: Path, *args: str) -> str:
    out = subprocess.check_output(["git", "-C", str(root), *args], text=True)
    return out.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def require_rl() -> Path:
    raw = os.environ.get("MICRODUCK_RL_OFFICIAL", "").strip()
    if not raw:
        fail("set MICRODUCK_RL_OFFICIAL to pollen-robotics/microduck_rl at 0daab160; the fork tree is refused")
    root = Path(raw).resolve()
    if not (root / ".git").exists():
        fail(f"{root} is not a git checkout")
    remote = git(root, "remote", "get-url", "origin")
    if "pollen-robotics/microduck_rl" not in remote:
        fail(f"refusing {remote}")
    head = git(root, "rev-parse", "HEAD")
    if head != RL_COMMIT:
        fail(f"official checkout {head} != {RL_COMMIT}")
    lock = (root / "uv.lock").read_text(errors="replace")
    if RHODAN_BAM_PIN not in lock:
        fail(f"uv.lock no longer pins Rhoban BAM {RHODAN_BAM_PIN}; refusing to continue")
    return root


def require_ftservo() -> tuple[Path, dict]:
    raw = os.environ.get("FTSERVO_BAM", "").strip()
    if not raw:
        fail("set FTSERVO_BAM to an isolated ftservo/ftservo-bam checkout at bab39678")
    root = Path(raw).resolve()
    if not (root / ".git").exists():
        fail(f"{root} is not a git checkout")
    remote = git(root, "remote", "get-url", "origin")
    if "ftservo/ftservo-bam" not in remote and "ftservo-bam" not in remote:
        fail(f"refusing {remote}; parameters must come from ftservo/ftservo-bam")
    head = git(root, "rev-parse", "HEAD")
    if head != FT_COMMIT:
        fail(f"ftservo checkout {head} != {FT_COMMIT}")
    dirty = git(root, "status", "--porcelain")
    if dirty:
        fail("ftservo checkout is dirty; refusing to load a rewritten m6.json")
    path = root / M6_REL
    if sha256_file(path) != M6_SHA:
        fail(f"{path} is not the archived m6 sha {M6_SHA}")
    data = json.loads(path.read_text())
    if data.get("actuator") != "hd1910" or data.get("model") != "m6":
        fail("m6.json is not actuator=hd1910 model=m6")
    if "error_gain_ratio" in data:
        fail("m6.json unexpectedly contains error_gain_ratio")
    if data.get("armature") != 0.0018273861091867637:
        fail("refusing an armature that is not the file value 0.0018273861091867637")
    body = (root / "bam/feetech/actuator.py").read_text().split("class HD1910Actuator", 1)[1]
    body = body.split("\nclass ", 1)[0].replace(" ", "")
    for snippet in ("vin=7.4", "kp=32", "error_gain=0.163", "max_pwm=0.97"):
        if snippet not in body:
            fail(f"HD1910Actuator.__init__ is missing {snippet}")
    registry = (root / "bam/actuators.py").read_text()
    if '"hd1910"' not in registry:
        fail("ftservo registry has no lowercase hd1910 key")
    return root, data


def use_ftservo_bam(ft_root: Path) -> None:
    """Import ``bam`` from the isolated checkout, not from site-packages."""
    sys.path.insert(0, str(ft_root))
    import bam

    bam_file = Path(bam.__file__).resolve()
    if ft_root not in bam_file.parents:
        fail(f"import bam resolved to {bam_file}, not {ft_root}")
    if "site-packages" in bam_file.parts:
        fail("refusing site-packages bam; PyPI better-actuator-models==1.0.2 is not this prior")
    loaded = Path(bam.__file__).resolve().parent / "params" / MOTOR_NAME / f"{MODEL_NAME}.json"
    if sha256_file(loaded) != M6_SHA:
        fail(f"bam would load {loaded}, which is not sha {M6_SHA}")


def retarget(cfg) -> list[str]:
    actuators = list(cfg.scene.entities["robot"].articulation.actuators)
    if not actuators:
        fail("velstand plant has no actuators")
    names = []
    for item in actuators:
        if not hasattr(item, "motor_name") or not hasattr(item, "kp_fw"):
            fail(f"{type(item).__name__} cannot be retargeted off XL330")
        item.motor_name = MOTOR_NAME
        item.model = MODEL_NAME
        item.kp_fw = KP_FW
        if hasattr(item, "vin_range"):
            item.vin_range = (VIN, VIN)
        if hasattr(item, "vin"):
            item.vin = VIN
        if hasattr(item, "vin_drop_gain_range"):
            # Sag is still a missing measurement. Do not keep the XL330 range.
            item.vin_drop_gain_range = (0.0, 0.0)
        if item.motor_name != MOTOR_NAME or item.model != MODEL_NAME or float(item.kp_fw) != KP_FW:
            fail("HD retarget did not stick")
        if float(item.kp_fw) == 200.0:
            fail("refusing XL330 kp_fw 200")
        names.append(type(item).__name__)
    if not any("Bam" in name and "Backlash" in name for name in names):
        fail(f"actuators {names} are not Backlash encoder BAM")
    return names


def build_env(rl_root: Path, device: str, seed: int):
    sys.path.insert(1, str(rl_root / "src"))
    os.chdir(rl_root)
    from mjlab.envs import ManagerBasedRlEnv
    from mjlab_microduck.robot.microduck_constants import MICRODUCK_ALLCOLLISIONS_BACKLASH_ROBOT_CFG
    from mjlab_microduck.tasks.backlash import make_backlash_variant
    from mjlab_microduck.tasks.microduck_velstand_env_cfg import make_microduck_velstand_env_cfg
    from official_velstand_plant import drop_curricula_for_missing_events

    cfg = make_microduck_velstand_env_cfg(play=False, rough=True)
    cfg = make_backlash_variant(cfg, MICRODUCK_ALLCOLLISIONS_BACKLASH_ROBOT_CFG)
    if cfg.scene.terrain.terrain_type != "generator":
        fail(f"terrain_type is {cfg.scene.terrain.terrain_type}, wanted generator (rough)")
    dt = float(cfg.sim.mujoco.timestep)
    decimation = int(cfg.decimation)
    if abs(dt - 0.005) > 1e-9 or decimation != 4:
        fail(f"official step is not 0.005 x 4 (got {dt} x {decimation})")
    names = retarget(cfg)
    for key in ("fallen_too_long", "time_out", "fell_over"):
        cfg.terminations.pop(key, None)
    for key in ("push_robot", "topple_push"):
        cfg.events.pop(key, None)
    drop_curricula_for_missing_events(cfg)
    cfg.scene.num_envs = 1
    cfg.seed = seed
    env = ManagerBasedRlEnv(cfg=cfg, device=device)
    return env, dt, decimation, names


def serve(rl_root: Path, host: str, port: int, device: str, seed: int) -> None:
    from official_velstand_plant import (
        POLICY_JOINTS,
        action_joint_names,
        processed_policy_action,
        scatter,
        sense,
    )

    env, dt, decimation, actuators = build_env(rl_root, device, seed)
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
    print(
        f"ready port={bound} plant={PLANT_ID} commit={RL_COMMIT} "
        f"ftservo={FT_COMMIT} motor={MOTOR_NAME} model={MODEL_NAME} kp_fw={KP_FW:g} vin={VIN}",
        flush=True,
    )
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
                    "commit": RL_COMMIT,
                    "ftservo": FT_COMMIT,
                    "motor_name": MOTOR_NAME,
                    "model": MODEL_NAME,
                    "kp_fw": KP_FW,
                    "vin": VIN,
                    "m6_sha256": M6_SHA,
                    "rhoban_bam_pin_untouched": RHODAN_BAM_PIN,
                    "actuators": actuators,
                    "physics_dt": dt,
                    "decimation": decimation,
                    "control_dt": dt * decimation,
                    "rough": True,
                    "conditional_sim": True,
                    "on_machine_ident": False,
                    "acceptance": False,
                })
            elif op == "reset":
                env.reset()
                send(sense(env))
            elif op == "step":
                raw_action = msg["action"]
                action = scatter(raw_action, index, len(action_names)).to(env.device).unsqueeze(0)
                started = time.perf_counter()
                env.step(action)
                payload = sense(env)
                payload["env_step_ms"] = (time.perf_counter() - started) * 1e3
                if msg.get("echo"):
                    payload["received_action"] = [float(value) for value in raw_action]
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


def unauthorized() -> None:
    print("HD conditional sim is not authorized. No environment was built and no result was written.", file=sys.stderr)
    print("This is not an executed run.", file=sys.stderr)
    print("On Ubuntu 22.04, after an isolated checkout exists and you intend to run:", file=sys.stderr)
    print("  export MICRODUCK_RL_OFFICIAL=/path/to/microduck_rl   # clean 0daab160", file=sys.stderr)
    print("  export FTSERVO_BAM=/path/to/ftservo-bam              # clean bab39678", file=sys.stderr)
    print("  export OFFICIAL_RL_PYTHON=/path/to/official-rl/bin/python3", file=sys.stderr)
    print("  export HD_CONDITIONAL_SIM_RUN=1", file=sys.stderr)
    print("  scripts/closed_loop/run_hd1910_conditional_plant.sh", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    if os.environ.get("HD_CONDITIONAL_SIM_RUN") != "1":
        unauthorized()
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    rl_root = require_rl()
    ft_root, _data = require_ftservo()
    if rl_root == ft_root or rl_root in ft_root.parents or ft_root in rl_root.parents:
        fail("FTSERVO_BAM must be an isolated checkout, not inside the official-rl tree")
    use_ftservo_bam(ft_root)
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
    serve(rl_root, host, port, device, seed)


if __name__ == "__main__":
    main()
