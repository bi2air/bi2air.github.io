#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT_DIR/tmp/air-quality-analysis-upstream/models/standardized_holdout_open_meteo/artifacts"
MODELS=()
HORIZONS=()
NOTE=""

while (($#)); do
  case "$1" in
    --models)
      IFS=',' read -r -a parsed_models <<< "$2"
      MODELS+=("${parsed_models[@]}")
      shift 2
      ;;
    --model)
      MODELS+=("$2")
      shift 2
      ;;
    --note)
      NOTE="$2"
      shift 2
      ;;
    *)
      HORIZONS+=("$1")
      shift
      ;;
  esac
done

if ((${#HORIZONS[@]} == 0)); then
  echo "usage: $0 [--models model1,model2] [--model model] [--note text] horizon [horizon ...]" >&2
  exit 1
fi

if ((${#MODELS[@]} == 0)); then
  MODELS=(xgb_full hgb_full xgb_pm_only hgb_pm_only linear_ar sarima_24h)
fi

source /home/uno/miniconda3/etc/profile.d/conda.sh
conda activate dev

mkdir -p "$MODELS_DIR"

for horizon in "${HORIZONS[@]}"; do
  python "$ROOT_DIR/scripts/export_standardized_model_artifact.py" \
    --horizon "$horizon" \
    --models "${MODELS[@]}" \
    --output-dir "$MODELS_DIR" \
    --note "$NOTE"
done
