#!/bin/bash
# Replayable HD-1910 conditional-sim handoff.
# Does not train, does not modify pollen-robotics or ftservo checkouts,
# and does not replace the Rhoban BAM pin inside official-rl.
# Without HD_CONDITIONAL_SIM_RUN=1 this script exits and writes no result.
# A later authorized run is still not on-machine identification and not acceptance.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if [[ "${HD_CONDITIONAL_SIM_RUN:-}" != "1" ]]; then
  echo "HD conditional sim is not authorized. No environment was built and no result was written." >&2
  echo "This is not an executed run." >&2
  echo "Dependencies, all required before a later local run:" >&2
  echo "  MICRODUCK_RL_OFFICIAL  clean pollen-robotics/microduck_rl at 0daab160d3fb1c2cbaba16a4a19052f36709dd9e" >&2
  echo "  FTSERVO_BAM            isolated ftservo/ftservo-bam at bab3967811f0bec8b79898cb03e7f5812fe581f9" >&2
  echo "  OFFICIAL_RL_PYTHON     official-rl python3. Do not use the system interpreter." >&2
  echo "  The ftservo checkout supplies bam. Do not pip install better-actuator-models==1.0.2 over the Rhoban pin 62bd8ce12154340be97e06f7f41a0ca8f116d967." >&2
  echo "  Do not point FTSERVO_BAM at this fork's microduck_rl or at the sts3215 JSON." >&2
  echo "Command:" >&2
  echo "  HD_CONDITIONAL_SIM_RUN=1 MICRODUCK_RL_OFFICIAL=... FTSERVO_BAM=... OFFICIAL_RL_PYTHON=... $0" >&2
  exit 2
fi
if [[ -z "${MICRODUCK_RL_OFFICIAL:-}" || -z "${FTSERVO_BAM:-}" || -z "${OFFICIAL_RL_PYTHON:-}" ]]; then
  echo "authorized run is missing MICRODUCK_RL_OFFICIAL, FTSERVO_BAM, or OFFICIAL_RL_PYTHON. No result was written." >&2
  exit 2
fi
if [[ ! -x "$OFFICIAL_RL_PYTHON" ]]; then
  echo "OFFICIAL_RL_PYTHON is not executable. No result was written." >&2
  exit 2
fi
OUT="${OUT:-$HOME/microduck-loop/evidence/2026-11-26/hd1910-ftservo-m6-conditional}"
case "$(basename "$OUT")" in
  official-velstand-rust-official-plant|official-velstand-rust-official-plant-r2|official-velstand-rust-official-plant-r3|official-velstand-rust-official-plant-r4|official-velstand-rust-onnx-compare|official-velstand-zero-shot|official-velstand-official-weight-heldout-10-11-12|official-eval-paths-inventory)
    echo "refusing to overwrite existing evidence: $OUT" >&2
    exit 2
    ;;
esac
mkdir -p "$OUT"
"$OFFICIAL_RL_PYTHON" "$ROOT/scripts/closed_loop/hd1910_conditional_plant.py" --port 0 >"$OUT/sidecar.log" 2>&1
echo "sidecar exited. See $OUT/sidecar.log. This script does not invent a completed-run summary." >&2
