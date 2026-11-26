#!/usr/bin/env python3
"""Project-defined PyTorch actor versus exported ONNX comparison.

This is not ``compare_velstand_onnx.py``. That file replays dumped closed-loop
observations through Rust's ONNX file with Python ONNX Runtime. This file would
compare a training actor to the exported ONNX on the same observations.

Official 0daab160 has no numeric actor-versus-ONNX bar. The max-abs line of
1e-5 is acceptance-criteria.md section 5 and is project-defined. Meeting it
would not be a behavior pass and would not be a 20 ms wall-clock pass.

Without ``ACTOR_ONNX_COMPARE_RUN=1`` this process writes nothing and exits.
"""

from __future__ import annotations

import os
import sys

PROJECT_MAX_ABS = 1e-5


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    if os.environ.get("ACTOR_ONNX_COMPARE_RUN") != "1":
        print("Actor-versus-ONNX compare is not authorized. No result was written.", file=sys.stderr)
        print("This is not the Rust ONNX replay and not a 20 ms retry.", file=sys.stderr)
        print(f"Project-defined bar, not an official one: per-step max abs <= {PROJECT_MAX_ABS}.", file=sys.stderr)
        print("  export MICRODUCK_RL_OFFICIAL=...   # clean 0daab160", file=sys.stderr)
        print("  export OFFICIAL_RL_PYTHON=...", file=sys.stderr)
        print("  export ACTOR_ONNX_COMPARE_RUN=1", file=sys.stderr)
        print("  compare_actor_onnx.py --checkpoint ACTOR.pt --onnx VELSTAND.onnx --obs step_compare.json --out actor_onnx_report.json", file=sys.stderr)
        raise SystemExit(2)
    fail("authorized actor-versus-ONNX loading is not executed from this cloud handover. No pass was written.")


if __name__ == "__main__":
    main()
