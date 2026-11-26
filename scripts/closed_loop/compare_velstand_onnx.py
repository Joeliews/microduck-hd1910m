#!/usr/bin/env python3
"""Replay dumped official-plant observations through Python ONNX Runtime.

The observations and Rust actions come from ``step_compare.json``. This
process does not build a plant, does not call ``env.step``, and does not
resimulate a trajectory. It also does not treat a small error as a pass:
official ``0daab160`` has no numeric actor-versus-ONNX bar, so the report
status stays ``executed_not_acceptance``.

Run it with ``OFFICIAL_RL_PYTHON``. The published velstand graph is
feedforward (``obs[1,61] -> actions[1,14]``, input name ``obs``).
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

EXPECTED_SHA = "ce894d30b3343036d499bfac1102bdaa58d59a21c1b58401ecb70fb6a2f63e0a"
OBS_LEN = 61
ACTION_LEN = 14
REL_EPS = 1e-12


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def f32_from_bits(rows: list) -> list[list[float]]:
    if sys.byteorder != "little":
        fail("obs_f32_bits are little-endian; this host is not")
    decoded = []
    for row in rows:
        if len(row) not in (OBS_LEN, ACTION_LEN):
            fail(f"bit row width {len(row)} is neither {OBS_LEN} nor {ACTION_LEN}")
        decoded.append([
            struct.unpack("<f", struct.pack("<I", int(bits) & 0xFFFFFFFF))[0]
            for bits in row
        ])
    return decoded


def element_errors(rust_row: list[float], python_row: list[float]) -> tuple[list[float], list[float]] | None:
    if len(rust_row) != len(python_row) or len(rust_row) != ACTION_LEN:
        return None
    absolute = [abs(left - right) for left, right in zip(rust_row, python_row)]
    relative = [err / max(abs(right), REL_EPS) for err, right in zip(absolute, python_row)]
    return absolute, relative


def aggregate(rows: list[list[float]]) -> dict:
    flat = [value for row in rows for value in row]
    if not flat:
        return {"max": None, "mean": None, "count": 0}
    return {"max": max(flat), "mean": sum(flat) / len(flat), "count": len(flat)}


def max_abs_pair(left_rows: list, right_rows: list) -> dict:
    """Difference between two recorded vectors. Not the ONNX comparison."""
    missing = 0
    highs = []
    for left, right in zip(left_rows, right_rows):
        if left is None or right is None:
            missing += 1
            continue
        if len(left) != ACTION_LEN or len(right) != ACTION_LEN:
            missing += 1
            continue
        highs.append(max(abs(float(a) - float(b)) for a, b in zip(left, right)))
    return {
        "steps_compared": len(highs),
        "missing_or_bad_width": missing,
        "max": max(highs) if highs else None,
        "mean_of_step_max": (sum(highs) / len(highs)) if highs else None,
    }


def session_contract(session) -> dict:
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    input_names = [item.name for item in inputs]
    output_names = [item.name for item in outputs]
    recurrent = len(inputs) != 1 or any(
        token in name.lower() for name in input_names for token in ("hidden", "cell", "h0", "c0", "state")
    )
    input_name = input_names[0] if len(inputs) == 1 else None
    output_shape = list(outputs[0].shape) if outputs else []
    return {
        "input_names": input_names,
        "output_names": output_names,
        "input_name": input_name,
        "input_name_is_obs": input_name == "obs",
        "output_shape": [str(dim) for dim in output_shape],
        "recurrent_state": recurrent,
        "feedforward": len(inputs) == 1 and input_name == "obs" and not recurrent,
    }


def replay(session, obs_rows: list[list[float]]) -> list[list[float]]:
    import numpy as np

    name = session.get_inputs()[0].name
    actions = []
    for obs in obs_rows:
        array = np.asarray([obs], dtype=np.float32)
        if array.shape != (1, OBS_LEN):
            fail(f"replay obs shape {array.shape} is not (1, {OBS_LEN})")
        result = session.run(None, {name: array})
        flat = np.asarray(result[0], dtype=np.float32).reshape(-1)
        actions.append([float(value) for value in flat])
    return actions


def load_rows(dump: dict, decimal_key: str, bits_key: str, width: int) -> list[list[float]]:
    bits = dump.get(bits_key)
    if isinstance(bits, list) and bits:
        rows = f32_from_bits(bits)
    else:
        rows = dump.get(decimal_key)
        if not isinstance(rows, list):
            fail(f"dump is missing {decimal_key}")
        rows = [[float(value) for value in row] for row in rows]
    for row in rows:
        if len(row) != width:
            fail(f"{decimal_key} row width {len(row)} != {width}")
    return rows


def compare(dump_path: Path, onnx_path: Path, out_path: Path) -> dict:
    onnx_sha = sha256_file(onnx_path)
    dump = json.loads(dump_path.read_text())
    report = {
        "status": "executed_not_acceptance",
        "numeric_pass_bar": None,
        "note": "Official 0daab160 has no numeric actor-versus-ONNX pass bar. Errors are recorded. A small error is not a pass, and this replay is not 20 ms acceptance.",
        "onnx_sha256": onnx_sha,
        "expected_sha256": EXPECTED_SHA,
        "dump_sha256": sha256_file(dump_path),
        "dump_onnx_sha256": dump.get("onnx_sha256"),
        "plant": dump.get("plant"),
        "official_commit": dump.get("official_commit"),
        "bam_lock": dump.get("bam_lock"),
        "control_dt_s": dump.get("control_dt_s"),
        "rejected_short_train_prefix": "cf280a27",
        "resimulated": False,
    }
    if onnx_sha != EXPECTED_SHA:
        report["status"] = "blocked"
        report["error"] = "onnx is not the published velstand.onnx"
        out_path.write_text(json.dumps(report, indent=2) + "\n")
        fail(report["error"])
    if dump.get("onnx_sha256") != EXPECTED_SHA:
        report["status"] = "blocked"
        report["error"] = "dump was not produced from the published velstand.onnx"
        out_path.write_text(json.dumps(report, indent=2) + "\n")
        fail(report["error"])

    import onnxruntime as ort

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    contract = session_contract(session)
    report["session"] = contract
    report["provider"] = "CPUExecutionProvider"
    obs_rows = load_rows(dump, "obs", "obs_f32_bits", OBS_LEN)
    rust_rows = load_rows(dump, "rust_action", "rust_action_f32_bits", ACTION_LEN)
    report["steps"] = len(obs_rows)
    if len(obs_rows) != len(rust_rows):
        report["shape_mismatches"] = abs(len(obs_rows) - len(rust_rows))
        report["error"] = "obs and rust_action row counts differ"
        out_path.write_text(json.dumps(report, indent=2) + "\n")
        return report
    if not contract["feedforward"]:
        report["shape_mismatches"] = 0
        report["error"] = "session is not the feedforward obs input; no hidden state was invented"
        report["abs"] = None
        report["rel"] = None
        out_path.write_text(json.dumps(report, indent=2) + "\n")
        return report

    python_rows = replay(session, obs_rows)
    absolute_rows = []
    relative_rows = []
    per_step_abs_max = []
    mismatches = 0
    for rust_row, python_row in zip(rust_rows, python_rows):
        parsed = element_errors(rust_row, python_row)
        if parsed is None:
            mismatches += 1
            per_step_abs_max.append(None)
            continue
        absolute, relative = parsed
        absolute_rows.append(absolute)
        relative_rows.append(relative)
        per_step_abs_max.append(max(absolute))
    report["shape_mismatches"] = mismatches
    report["abs"] = aggregate(absolute_rows)
    report["rel"] = aggregate(relative_rows)
    report["rel"]["denominator"] = "max(|python_action|, 1e-12)"
    report["per_step_abs_max"] = per_step_abs_max
    report["wire_vs_rust"] = max_abs_pair(rust_rows, dump.get("sidecar_received_action") or [])
    report["processed_vs_rust"] = max_abs_pair(rust_rows, dump.get("sidecar_processed_action") or [])
    report["processed_note"] = "sidecar_processed_action is the plant term after env.step. It is not the ONNX output and was not substituted for either side."
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    dump = None
    onnx = None
    out = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--dump":
            dump = Path(args[i + 1])
            i += 2
        elif args[i] == "--onnx":
            onnx = Path(args[i + 1])
            i += 2
        elif args[i] == "--out":
            out = Path(args[i + 1])
            i += 2
        else:
            fail(f"unknown argument {args[i]}")
    if dump is None or onnx is None or out is None:
        fail("usage: compare_velstand_onnx.py --dump step_compare.json --onnx velstand.onnx --out compare_report.json")
    compare(dump, onnx, out)


if __name__ == "__main__":
    main()
