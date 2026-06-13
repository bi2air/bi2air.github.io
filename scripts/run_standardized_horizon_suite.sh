#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE_TAG="$(date +%F)"
MODELS=()
HORIZONS=()

while (($#)); do
  case "$1" in
    --date-tag)
      DATE_TAG="$2"
      shift 2
      ;;
    --models)
      IFS=',' read -r -a parsed_models <<< "$2"
      MODELS+=("${parsed_models[@]}")
      shift 2
      ;;
    --model)
      MODELS+=("$2")
      shift 2
      ;;
    *)
      HORIZONS+=("$1")
      shift
      ;;
  esac
done

if ((${#HORIZONS[@]} == 0)); then
  echo "usage: $0 [--date-tag YYYY-MM-DD] [--models model1,model2] [--model model] horizon [horizon ...]" >&2
  exit 1
fi

source /home/uno/miniconda3/etc/profile.d/conda.sh
conda activate dev

mkdir -p "$ROOT_DIR/tmp/standardized_runs"

for horizon in "${HORIZONS[@]}"; do
  inputs=()
  if ((${#MODELS[@]} > 0)); then
    model_slug="$(IFS=-; echo "${MODELS[*]}")"
    out_path="$ROOT_DIR/tmp/standardized_runs/h${horizon}_${model_slug}_${DATE_TAG}.json"
    python "$ROOT_DIR/scripts/evaluate_horizon_standardized.py" \
      --horizon "$horizon" \
      --models "${MODELS[@]}" \
      --out "$out_path"
    inputs+=("$out_path")
  else
    out_path="$ROOT_DIR/tmp/standardized_runs/h${horizon}_all_${DATE_TAG}.json"
    python "$ROOT_DIR/scripts/evaluate_horizon_standardized.py" \
      --horizon "$horizon" \
      --out "$out_path"
    inputs+=("$out_path")
  fi

  if ((${#MODELS[@]} > 0)); then
    for candidate in "$ROOT_DIR"/tmp/standardized_runs/h"${horizon}"_*_"${DATE_TAG}".json; do
      if [[ -f "$candidate" ]]; then
        case " ${inputs[*]} " in
          *" $candidate "*) ;;
          *) inputs+=("$candidate") ;;
        esac
      fi
    done
  fi

  table_path="${ROOT_DIR}/tmp/standardized_runs/h${horizon}_combined_summary_${DATE_TAG}.md"
  python "$ROOT_DIR/scripts/render_standardized_horizon_table.py" \
    --inputs "${inputs[@]}" \
    --out "$table_path"
done
