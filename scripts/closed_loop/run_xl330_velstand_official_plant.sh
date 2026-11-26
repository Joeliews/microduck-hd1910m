#!/bin/bash
# Short Rust loop against the official BAM + backlash + rough plant.
# Does not train, does not modify the official checkout, and does not stop other agents.
# Ubuntu 22.04 on the user machine may not have rustc yet. Install rustup in the
# user account only. Do not change Ubuntu 26.04, do not overwrite official-cu,
# and do not kill AgentsDock.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if [[ -z "${MICRODUCK_RL_OFFICIAL:-}" ]]; then
  echo "Set MICRODUCK_RL_OFFICIAL to a pollen-robotics/microduck_rl checkout at 0daab160d3fb1c2cbaba16a4a19052f36709dd9e." >&2
  echo "Do not point it at this fork's microduck_rl/." >&2
  exit 2
fi
if ! command -v rustc >/dev/null 2>&1; then
  echo "rustc is missing. In this user account only:" >&2
  echo "  curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain 1.89.0" >&2
  exit 2
fi
ONNX="${ONNX:-/tmp/microduck-policies/velstand.onnx}"
OUT="${OUT:-$ROOT/docs/closed-loop/evidence/xl330-velstand-official-plant-r1}"
export ORT_DYLIB_PATH="${ORT_DYLIB_PATH:-}"
if [[ -z "$ORT_DYLIB_PATH" ]]; then
  echo "Set ORT_DYLIB_PATH to libonnxruntime.so (floor 1.23)." >&2
  exit 2
fi
mkdir -p "$OUT"
cd "$ROOT/microduck"
cargo +1.89.0 build --release --example xl330_velstand_official_plant -p duck-control
python3 "$ROOT/scripts/closed_loop/official_velstand_plant.py" --port 0 >"$OUT/sidecar.log" 2>&1 &
SIDE=$!
cleanup() { kill "$SIDE" >/dev/null 2>&1 || true; }
trap cleanup EXIT
PORT=""
for _ in $(seq 1 600); do
  if grep -q '^ready port=' "$OUT/sidecar.log" 2>/dev/null; then
    PORT="$(sed -n 's/^ready port=\([0-9]*\).*/\1/p' "$OUT/sidecar.log" | head -1)"
    break
  fi
  if ! kill -0 "$SIDE" >/dev/null 2>&1; then
    echo "sidecar exited before ready. See $OUT/sidecar.log" >&2
    exit 2
  fi
  sleep 1
done
if [[ -z "$PORT" ]]; then
  echo "sidecar did not become ready. See $OUT/sidecar.log" >&2
  exit 2
fi
"$ROOT/microduck/target/release/examples/xl330_velstand_official_plant" \
  --onnx "$ONNX" --addr "127.0.0.1:$PORT" --out "$OUT"
