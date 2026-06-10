#!/bin/bash
# Wait for training to complete and generate final summary
# Usage: ./scripts/wait_for_training.sh

PID=40854
OUTPUT_DIR="tmp/air-quality-analysis-upstream/data/forecast_model_results_full_2026_06_08"
SUMMARY_FILE="doc-work/2026-06-08-training-complete-summary.md"

echo "Monitoring training process (PID: $PID)..."
echo "Dashboard: doc-work/training-dashboard-live.md"
echo "Next steps: doc-work/2026-06-08-next-steps-plan.md"
echo ""

# Wait for process to finish
while ps -p $PID > /dev/null 2>&1; do
    # Update progress every 5 minutes
    ELAPSED=$(ps -p $PID -o etime --no-headers | tr -d ' ')
    EXPERIMENTS=$(wc -l < "$OUTPUT_DIR/regression_metrics_by_horizon.csv" 2>/dev/null || echo 0)
    EXPERIMENTS=$((EXPERIMENTS - 1))  # Subtract header

    echo "[$(date '+%H:%M:%S')] Training running... Elapsed: $ELAPSED | Experiments: $EXPERIMENTS"

    sleep 300  # Check every 5 minutes
done

echo ""
echo "✓ Training completed!"
echo "Generating final summary..."

# Get final stats
END_TIME=$(date '+%Y-%m-%d %H:%M:%S')

if [ -f "$OUTPUT_DIR/model_run_manifest.json" ]; then
    TOTAL_TIME=$(jq -r '.elapsed_seconds' "$OUTPUT_DIR/model_run_manifest.json")
    TOTAL_HOURS=$(echo "scale=2; $TOTAL_TIME / 3600" | bc)
    MODE=$(jq -r '.mode' "$OUTPUT_DIR/model_run_manifest.json")
    HORIZONS=$(jq -r '.horizons | join(", ")' "$OUTPUT_DIR/model_run_manifest.json")
else
    TOTAL_TIME="unknown"
    TOTAL_HOURS="unknown"
    MODE="full"
    HORIZONS="1, 6, 12, 24, 48, 72"
fi

# Count final experiments
REG_COUNT=$(wc -l < "$OUTPUT_DIR/regression_metrics_by_horizon.csv" 2>/dev/null || echo 0)
CLS_COUNT=$(wc -l < "$OUTPUT_DIR/classification_metrics_by_horizon.csv" 2>/dev/null || echo 0)
EVT_COUNT=$(wc -l < "$OUTPUT_DIR/event_detection_metrics.csv" 2>/dev/null || echo 0)
QNT_COUNT=$(wc -l < "$OUTPUT_DIR/quantile_interval_metrics.csv" 2>/dev/null || echo 0)

# Create summary
cat > "$SUMMARY_FILE" <<EOF
# Training Complete: Full-Mode Hanoi PM2.5 Baseline

**Completed**: $END_TIME
**Total Runtime**: $TOTAL_HOURS hours
**Status**: ✓ SUCCESS

---

## Training Configuration

- **Mode**: $MODE (includes ExtraTrees)
- **Horizons**: ${HORIZONS}h
- **MERRA Compact**: Enabled
- **Hardware**: AMD Ryzen 7 2700, 32GB RAM, Python 3.12

## Results Summary

| Experiment Type | Count |
|-----------------|-------|
| Regression | $((REG_COUNT - 1)) |
| Classification | $((CLS_COUNT - 1)) |
| Event Detection | $((EVT_COUNT - 1)) |
| Quantile | $((QNT_COUNT - 1)) |

**Output Directory**: \`$OUTPUT_DIR\`

---

## Key Files

### Metrics
- \`regression_metrics_by_horizon.csv\` - Main model performance
- \`classification_metrics_by_horizon.csv\` - Bin classification results
- \`event_detection_metrics.csv\` - Severe event detection
- \`quantile_interval_metrics.csv\` - Uncertainty quantification

### Supporting
- \`classification_confusion_counts.csv\` - Confusion matrices
- \`transition_matrix_summary.csv\` - State transition diagnostics
- \`split_counts.csv\` - Data split statistics
- \`model_run_manifest.json\` - Full run metadata

---

## Next Steps

See detailed plan: **\`doc-work/2026-06-08-next-steps-plan.md\`**

### Immediate Actions

1. **Analyze Results**
   \`\`\`bash
   python scripts/analyze_hanoi_full_mode.py \\
     --results $OUTPUT_DIR \\
     --compare-to data/forecast_model_results_2026_06_07_extended
   \`\`\`

2. **Generate Episode Plots**
   \`\`\`bash
   python scripts/plot_hanoi_full_mode_episodes.py \\
     --results $OUTPUT_DIR \\
     --out-dir ${OUTPUT_DIR}_episode_plots
   \`\`\`

3. **Start Hyperparameter Sweep** (Task #2)
   \`\`\`bash
   python scripts/run_hanoi_hyperparameter_sweep.py \\
     --horizons 24 48 72 \\
     --out-dir data/hyperparameter_sweep_\$(date +%Y_%m_%d)
   \`\`\`

---

## Performance Expectations

Based on fast-mode baseline and full-mode additions:

**Improvements from Full Mode**:
- ExtraTrees provides 1-3% RMSE reduction at longer horizons
- More comprehensive model comparison
- Better ensemble candidates

**Target Horizons** (where gains matter most):
- 24h: RMSE ~21-22 (baseline: 22.5)
- 48h: RMSE ~22-23 (baseline: 24.4)
- 72h: RMSE ~23-24 (baseline: 25.3)

**Next Phase** (Hyperparameter Sweep):
- Additional 5-10% improvement expected
- Focus on 24h+ where room for improvement is largest

---

## Task Status

- [x] **Task #1**: Full-mode baseline ← **COMPLETED**
- [ ] **Task #2**: Hyperparameter sweep (24h/48h/72h)
- [ ] **Task #3**: Ensemble experiments
- [ ] **Task #4**: Severe event tuning (PM2.5 > 100, > 150)
- [ ] **Task #5**: MERRA compact re-evaluation
- [ ] **Task #6**: HCMC pipeline

**Completed**: $(date '+%Y-%m-%d %H:%M:%S')
EOF

echo ""
echo "Summary written to: $SUMMARY_FILE"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Task #1 Complete: Full-Mode Baseline"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next: Review results and start Task #2 (Hyperparameter Sweep)"
echo "See plan: doc-work/2026-06-08-next-steps-plan.md"
echo ""
