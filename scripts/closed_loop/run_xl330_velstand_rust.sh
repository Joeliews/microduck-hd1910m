#!/bin/bash
# Short Rust control-core loop against MuJoCo. Does not train and does not touch hardware.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export MUJOCO_DIR="${MUJOCO_DIR:-/home/ubuntu/.local/lib/python3.12/site-packages/mujoco}"
export ORT_DYLIB_PATH="${ORT_DYLIB_PATH:-/home/ubuntu/.local/lib/python3.12/site-packages/onnxruntime/capi/libonnxruntime.so.1.23.2}"
ONNX="${ONNX:-/tmp/microduck-policies/velstand.onnx}"
OUT="${OUT:-$ROOT/docs/closed-loop/evidence/xl330-velstand-rust-r1}"
SCENE="$ROOT/microduck_rl/src/mjlab_microduck/robot/microduck/scene_walk.xml"
cd "$ROOT/microduck"
cargo +1.89.0 build --release --example xl330_velstand_mujoco --features mujoco-plant -p duck-control
exec ./target/release/examples/xl330_velstand_mujoco "$SCENE" "$ONNX" "$OUT"
