#!/bin/bash
# Pointer for the official training plant. This script does not install uv, does not
# sync the training stack, and does not start PPO. The cloud VM has no RTX 5090.
set -euo pipefail
TRAIN_COMMIT="53fb7d115b1be79c6d07e8fd4eab311285e16f2a"
DEVELOP_COMMIT="0daab160d3fb1c2cbaba16a4a19052f36709dd9e"
cat <<EOF
Official repo: https://github.com/pollen-robotics/microduck_rl
velstand.onnx was trained at ${TRAIN_COMMIT} (task Mjlab-VelStand-Rough-Backlash-MicroDuck).
The headless bench script scripts/velstand_bench.py is on develop ${DEVELOP_COMMIT}.
Do not point this at the feetech tree microduck_rl/ inside the fork.

On the WSL machine, after you have already created that checkout and its environment:

  cd "\$MICRODUCK_RL_OFFICIAL"
  git checkout ${DEVELOP_COMMIT}
  uv run python scripts/velstand_bench.py /path/to/velstand.onnx --device cuda:0

This cloud script stops here.
EOF
if [[ -n "${MICRODUCK_RL_OFFICIAL:-}" && -d "${MICRODUCK_RL_OFFICIAL}/.git" ]]; then
  echo "MICRODUCK_RL_OFFICIAL=$MICRODUCK_RL_OFFICIAL"
  git -C "$MICRODUCK_RL_OFFICIAL" rev-parse HEAD
  git -C "$MICRODUCK_RL_OFFICIAL" remote get-url origin
else
  echo "MICRODUCK_RL_OFFICIAL is not set to a checkout. That is expected on the cloud VM."
fi
