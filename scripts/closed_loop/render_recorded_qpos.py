#!/usr/bin/env python3
"""Replay qpos recorded by the Rust MuJoCo loop. Does not run the policy again."""

import argparse
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--qpos", type=Path, required=True)
    parser.add_argument("--gif", type=Path, required=True)
    args = parser.parse_args()
    rows = [np.fromstring(line, sep=",") for line in args.qpos.read_text().splitlines() if line.strip()]
    model = mujoco.MjModel.from_xml_path(str(args.scene))
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=360, width=480)
    frames = []
    for row in rows[::5]:
        data.qpos[:] = row
        mujoco.mj_forward(model, data)
        cam = mujoco.MjvCamera()
        mujoco.mjv_defaultFreeCamera(model, cam)
        trunk = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "trunk_base")
        cam.lookat[:] = data.xpos[trunk]
        cam.distance = 0.45
        cam.azimuth = 140.0
        cam.elevation = -15.0
        renderer.update_scene(data, camera=cam)
        frames.append(Image.fromarray(renderer.render()))
    args.gif.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(args.gif, save_all=True, append_images=frames[1:], duration=100, loop=0)
    print(f"wrote {args.gif} frames={len(frames)}")


if __name__ == "__main__":
    main()
