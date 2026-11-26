#!/usr/bin/env python3
"""Project self-built behavior entries for nine official ONNX policies.

Not an official script and not ``official_path``. Does not call
``scripts/velstand_bench.py`` and does not build a VelStand plant.
``infer_policy.py``, ``uv run play``, ``play_latest.py``, ``body_server`` and
``robotd --sim`` are not this bench.

Without ``SELF_BUILT_EVAL_RUN=1`` the process exits before creating an
environment and writes no score. An authorized run that cannot see a 61-wide
deployed observation stops as ``blocked``. That is not a pass.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

RL_COMMIT = "0daab160d3fb1c2cbaba16a4a19052f36709dd9e"
HELDOUT = (20, 21, 22)
EPISODES = 16
FAIL_TILT_DEG = 60.0
FAIL_HEIGHT_M = 0.06
FAIL_FRACTION_MAX = 0.10

# SHA256 values are the published ONNX contracts already in policy-matrix-20.md.
POLICIES = {
    "alpha_walking": {
        "sha256": "e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c",
        "kind": "continuous",
        "task_id": None,
        "roller": False,
        "action_scale": 1.0,
    },
    "alpha_stand": {
        "sha256": "1569268713e40deea795dd2922dba50d3621e15a872855408b6b1b125b1c094b",
        "kind": "continuous",
        "task_id": None,
        "roller": False,
        "action_scale": 1.0,
    },
    "roller": {
        "sha256": "7b581097a9bc4782a695fd7654edb0c565649ad593ae439563ddf4b2b2e8a8c7",
        "kind": "continuous",
        "task_id": "Mjlab-Velocity-Swizzle-MicroDuck",
        "roller": True,
        "action_scale": 0.8,
    },
    "alpha_sitstand": {
        "sha256": "a6f102d9fd655782ba85bfffe18175c34621da719cffcdd673be7982a06fc254",
        "kind": "episodic",
        "task_id": "Mjlab-SitStand-Flat-MicroDuck",
        "roller": False,
        "action_scale": 1.0,
        "duration_s": 3.0,
    },
    "alpha_ground_pick": {
        "sha256": "ffbf5109982ff999b0ba53afe86b9ae731bbec679d67fb7f8ab4c52152c88872",
        "kind": "episodic",
        "task_id": None,
        "roller": False,
        "action_scale": 1.0,
        "duration_s": 2.8,
    },
    "roller_crouch": {
        "sha256": "a1a084be240469c76ac9d3fa44d4792f16d4b1da60398b3ecd3cfc5e2244d990",
        "kind": "episodic",
        "task_id": None,
        "roller": True,
        "action_scale": 0.8,
        "duration_s": 3.5,
    },
    "roulade": {
        "sha256": "3d60da08fc13f29c1b57f41977aa898132c0d60042100149d8e775affcbca32b",
        "kind": "episodic",
        "task_id": None,
        "registry_hint": "Mjlab-Roulade-Flat-MicroDuck",
        "roller": False,
        "action_scale": 1.0,
        "duration_s": 1.0,
    },
    "ball_kick_left": {
        "sha256": "d6928284dccd3dd61e08bf2f760effa74309fbefd97b2b31afb2a60f526d196a",
        "kind": "episodic",
        "task_id": "Mjlab-BallKick-Flat-MicroDuck",
        "foot": "left",
        "roller": False,
        "action_scale": 1.0,
        "duration_s": 0.5,
    },
    "ball_kick_right": {
        "sha256": "147a32c388c6b19111b3ac3b550a9a6dc8b8bf267118af4d8c3712522eedb5af",
        "kind": "episodic",
        "task_id": "Mjlab-BallKick-Flat-MicroDuck",
        "foot": "right",
        "roller": False,
        "action_scale": 1.0,
        "duration_s": 0.5,
    },
}


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def parse_args(argv: list[str]) -> dict:
    out = {"policy": None, "task_id": None, "acknowledge_unpinned": False, "onnx": None, "check": False}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--policy":
            out["policy"] = argv[i + 1]
            i += 2
        elif arg == "--task-id":
            out["task_id"] = argv[i + 1]
            i += 2
        elif arg == "--acknowledge-unpinned-task":
            out["acknowledge_unpinned"] = True
            i += 1
        elif arg == "--onnx":
            out["onnx"] = argv[i + 1]
            i += 2
        elif arg == "--check":
            out["check"] = True
            i += 1
        elif arg in ("--use-velstand-bench", "--velstand-bench"):
            fail("refusing velstand_bench; this entry is not the VelStand plant")
        else:
            fail(f"unknown argument {arg}")
    return out


def resolve(args: dict) -> tuple[str, dict, str, bool]:
    name = args["policy"]
    if name not in POLICIES:
        fail("policy must be one of the nine self-built entries, not velstand")
    spec = POLICIES[name]
    task = args["task_id"] or spec.get("task_id")
    if task is None:
        fail(f"{name} has no pinned task_id; pass --task-id and --acknowledge-unpinned-task")
    if "VelStand" in task or "velstand" in task:
        fail(f"refusing VelStand task {task}")
    unpinned = spec.get("task_id") is None
    if unpinned and not args["acknowledge_unpinned"]:
        fail(f"{name} task_id is not pinned by the published artifact; pass --acknowledge-unpinned-task")
    if spec.get("task_id") and task != spec["task_id"]:
        fail(f"{name} is pinned to {spec['task_id']}, not {task}")
    hint = spec.get("registry_hint")
    if hint and task != hint and not args["acknowledge_unpinned"]:
        fail(f"{name} registry hint is {hint}")
    return name, spec, task, unpinned


def official_root() -> Path:
    raw = os.environ.get("MICRODUCK_RL_OFFICIAL", "").strip()
    if not raw:
        fail("set MICRODUCK_RL_OFFICIAL to pollen-robotics/microduck_rl at 0daab160")
    root = Path(raw).resolve()
    if not (root / ".git").exists():
        fail(f"{root} is not a git checkout")
    remote = subprocess.check_output(["git", "-C", str(root), "remote", "get-url", "origin"], text=True)
    if "pollen-robotics/microduck_rl" not in remote:
        fail(f"refusing {remote.strip()}")
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if head != RL_COMMIT:
        fail(f"checkout {head} != {RL_COMMIT}")
    fork = Path(__file__).resolve().parents[2] / "microduck_rl"
    if root == fork.resolve():
        fail("refusing this fork's microduck_rl/")
    return root


def roller_xml(task_cfg) -> bool:
    text = str(getattr(getattr(task_cfg, "scene", None), "entities", ""))
    robot = None
    entities = getattr(getattr(task_cfg, "scene", None), "entities", None)
    if isinstance(entities, dict):
        robot = entities.get("robot")
    xml = ""
    if robot is not None:
        xml = str(getattr(getattr(robot, "spec_fn", None), "__defaults__", "")) + str(robot)
    blob = (text + xml).lower()
    return "roller" in blob or "wheel" in blob


def policy_obs_dim(env) -> int | None:
    manager = getattr(env, "observation_manager", None)
    if manager is None:
        return None
    groups = getattr(manager, "group_obs_dim", None)
    if isinstance(groups, dict):
        for key in ("policy", "actor"):
            dim = groups.get(key)
            if isinstance(dim, tuple) and dim and dim[-1] == 61:
                return 61
            if dim == 61:
                return 61
    return None


def authorized_run(name: str, spec: dict, task: str, unpinned: bool, onnx: str | None) -> None:
    if os.environ.get("SELF_BUILT_EVAL_RUN") != "1":
        fail("SELF_BUILT_EVAL_RUN is not 1. No environment was built and no score was written.")
    if not onnx:
        fail("pass --onnx. No score was written.")
    root = official_root()
    sys.path.insert(0, str(root / "src"))
    os.chdir(root)
    import gymnasium as gym
    import mjlab_microduck.tasks  # noqa: F401

    if task not in gym.registry:
        fail(f"{task} is not in the official registry. No score was written.")
    env = gym.make(task, num_envs=EPISODES)
    try:
        if spec["roller"] and not roller_xml(env.unwrapped.cfg):
            fail(f"{task} did not look like roller physics. Refusing a wheel-less fallback. No score was written.")
        if policy_obs_dim(env.unwrapped) != 61:
            fail("deployed 61-d observation was not found. Refusing a zero or privileged obs. No score was written.")
        fail("command interface was not confirmed on this env. No score was written.")
    finally:
        env.close()


def main() -> None:
    args = parse_args(sys.argv[1:])
    name, spec, task, unpinned = resolve(args)
    plan = {
        "label": "自建验收",
        "official_path": False,
        "status": "not_run",
        "policy": name,
        "task_id": task,
        "task_unpinned_by_artifact": unpinned,
        "heldout_seeds": list(HELDOUT),
        "episodes_per_seed": EPISODES,
        "fail_tilt_deg": FAIL_TILT_DEG,
        "fail_height_m": FAIL_HEIGHT_M,
        "fail_fraction_max": FAIL_FRACTION_MAX,
        "action_scale": spec["action_scale"],
        "roller_physics_required": spec["roller"],
        "onnx_sha256": spec["sha256"],
        "pass": False,
    }
    if args["check"]:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        print("check only; not an evaluation", file=sys.stderr)
        return
    authorized_run(name, spec, task, unpinned, args["onnx"])


if __name__ == "__main__":
    main()
