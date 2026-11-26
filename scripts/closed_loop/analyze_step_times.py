#!/usr/bin/env python3
"""Recompute an official-plant timing split from step_times.json.

Does not start a plant, does not rerun the 4 s loop, and does not loosen the
20 ms budget. Logical 50 Hz is not a wall-clock pass. Host time is not board time.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BUDGET_MS = 20.0


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    pos = (q / 100.0) * (len(ordered) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def finite(rows) -> list[float]:
    out = []
    for value in rows or []:
        if isinstance(value, (int, float)) and value == value:
            out.append(float(value))
    return out


def summary(values: list[float]) -> dict:
    if not values:
        return {"p50": None, "p95": None, "p99": None, "max": None, "count": 0}
    return {
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
        "max": max(values),
        "count": len(values),
    }


def analyze(payload: dict) -> dict:
    total = finite(payload.get("total_ms"))
    infer = finite(payload.get("infer_ms"))
    rpc = finite(payload.get("step_round_trip_ms"))
    env = finite(payload.get("env_step_ms"))
    gaps = [a - b for a, b in zip(rpc, env)] if len(rpc) == len(env) and rpc else []
    timeouts = sum(1 for value in total if value > BUDGET_MS)
    report = {
        "status": "executed_not_acceptance",
        "pass": False,
        "budget_ms": BUDGET_MS,
        "budget_loosened": False,
        "logical_50hz_is_wall_clock_pass": False,
        "host_is_board": False,
        "reran_plant": False,
        "total_ms": summary(total),
        "infer_ms": summary(infer),
        "step_round_trip_ms": summary(rpc),
        "env_step_ms": summary(env),
        "rpc_json_sense_ms": summary(gaps),
        "timeouts": timeouts,
        "over_20ms": timeouts,
        "dropped_frames": payload.get("dropped_frames"),
        "dropped_frame_policy": "logical ticks are not skipped; an overrun is a timeout, not a dropped physics step",
        "note": "timeouts count total_ms strictly greater than 20. infer_ms is only Policy::infer. A small infer time is not a closed-loop pass.",
    }
    if "dropped_frames" not in payload:
        report["dropped_frames"] = None
        report["dropped_frames_note"] = "absent from this step_times.json; not invented"
    return report


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] != "--step-times":
        fail("usage: analyze_step_times.py --step-times step_times.json")
    path = Path(sys.argv[2])
    if not path.is_file():
        fail(f"missing {path}. No plant was started and no timing was invented.")
    payload = json.loads(path.read_text())
    print(json.dumps(analyze(payload), indent=2))


if __name__ == "__main__":
    main()
