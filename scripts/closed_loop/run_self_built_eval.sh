#!/bin/bash
# Handoff for a later local self-built eval. Not velstand_bench and not an official path.
# Without SELF_BUILT_EVAL_RUN=1 this exits and writes no score.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if [[ "${1:-}" == "--check" ]]; then
  shift
  exec python3 "$ROOT/scripts/closed_loop/self_built_eval.py" --check "$@"
fi
if [[ "${SELF_BUILT_EVAL_RUN:-}" != "1" ]]; then
  echo "Self-built eval is not authorized. No environment was built and no score was written." >&2
  echo "This is not an executed run and not official_path." >&2
  echo "  export MICRODUCK_RL_OFFICIAL=/path/to/microduck_rl   # clean 0daab160" >&2
  echo "  export OFFICIAL_RL_PYTHON=/path/to/official-rl/bin/python3" >&2
  echo "  export SELF_BUILT_EVAL_RUN=1" >&2
  echo "  $0 --policy alpha_sitstand --onnx /path/to/alpha_sitstand.onnx" >&2
  echo "Unpinned policies also need --task-id and --acknowledge-unpinned-task." >&2
  echo "Do not point this at scripts/velstand_bench.py." >&2
  exit 2
fi
if [[ -z "${OFFICIAL_RL_PYTHON:-}" || ! -x "$OFFICIAL_RL_PYTHON" ]]; then
  echo "OFFICIAL_RL_PYTHON is missing. No score was written." >&2
  exit 2
fi
exec "$OFFICIAL_RL_PYTHON" "$ROOT/scripts/closed_loop/self_built_eval.py" "$@"
