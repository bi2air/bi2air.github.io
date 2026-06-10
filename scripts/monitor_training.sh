#!/bin/bash
# Training Monitor - Auto-updating dashboard for Hanoi PM2.5 training
# Usage: ./monitor_training.sh [output_dir] [log_file]

OUTPUT_DIR="${1:-tmp/air-quality-analysis-upstream/data/forecast_model_results_full_2026_06_08}"
LOG_FILE="${2:-/tmp/training_monitor.log}"
STATUS_FILE="/tmp/training_status.txt"
DASHBOARD_FILE="doc-work/training-dashboard.md"
PID_FILE="/tmp/training_pid.txt"

# Find the training process
TRAINING_PID=$(ps aux | grep "run_hanoi_forecast_experiments.py" | grep -v grep | grep python | awk '{print $2}')

if [ -z "$TRAINING_PID" ]; then
    echo "❌ Training process not found" | tee "$STATUS_FILE"
    exit 1
fi

echo "$TRAINING_PID" > "$PID_FILE"

# Function to format time
format_time() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))
    printf "%02d:%02d:%02d" $hours $minutes $secs
}

# Main monitoring loop
while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Check if process is still running
    if ! ps -p "$TRAINING_PID" > /dev/null 2>&1; then
        echo "✓ Training completed at $TIMESTAMP" | tee "$STATUS_FILE"

        # Final dashboard update
        cat > "$DASHBOARD_FILE" <<EOF
# Hanoi PM2.5 Training Dashboard

**Status**: ✓ COMPLETED
**Completed At**: $TIMESTAMP

## Final Results
EOF

        # Add final metrics if available
        if [ -f "$OUTPUT_DIR/model_run_manifest.json" ]; then
            echo "**Total Runtime**: $(jq -r '.elapsed_seconds' "$OUTPUT_DIR/model_run_manifest.json")s" >> "$DASHBOARD_FILE"
            echo "**Mode**: $(jq -r '.mode' "$OUTPUT_DIR/model_run_manifest.json")" >> "$DASHBOARD_FILE"
            echo "**Horizons**: $(jq -r '.horizons | join(", ")' "$OUTPUT_DIR/model_run_manifest.json")h" >> "$DASHBOARD_FILE"
        fi

        echo "" >> "$DASHBOARD_FILE"
        echo "Check results at: \`$OUTPUT_DIR\`" >> "$DASHBOARD_FILE"

        break
    fi

    # Get process stats
    PROC_STATS=$(ps -p "$TRAINING_PID" -o etime,pcpu,pmem,rss --no-headers)
    ELAPSED=$(echo "$PROC_STATS" | awk '{print $1}')
    CPU_PCT=$(echo "$PROC_STATS" | awk '{print $2}')
    MEM_PCT=$(echo "$PROC_STATS" | awk '{print $3}')
    RSS_KB=$(echo "$PROC_STATS" | awk '{print $4}')
    MEM_MB=$((RSS_KB / 1024))

    # Count completed experiments
    if [ -f "$OUTPUT_DIR/regression_metrics_by_horizon.csv" ]; then
        TOTAL_LINES=$(wc -l < "$OUTPUT_DIR/regression_metrics_by_horizon.csv")
        EXPERIMENTS=$((TOTAL_LINES - 1))  # Subtract header
    else
        EXPERIMENTS=0
    fi

    # Estimate progress based on expected experiments
    # Fast mode: ~95 experiments (6 horizons × ~16 experiments per horizon)
    # Full mode adds ExtraTrees: ~120-140 experiments
    EXPECTED_TOTAL=130
    PROGRESS_PCT=$((EXPERIMENTS * 100 / EXPECTED_TOTAL))
    if [ $PROGRESS_PCT -gt 100 ]; then
        PROGRESS_PCT=100
    fi

    # Estimate remaining time (rough)
    if [ $EXPERIMENTS -gt 10 ]; then
        # Convert elapsed time to seconds
        ELAPSED_SEC=$(echo "$ELAPSED" | awk -F: '{ if (NF==3) print ($1 * 3600) + ($2 * 60) + $3; else if (NF==2) print ($1 * 60) + $2; else print $1 }')
        SEC_PER_EXP=$((ELAPSED_SEC / EXPERIMENTS))
        REMAINING_EXP=$((EXPECTED_TOTAL - EXPERIMENTS))
        REMAINING_SEC=$((SEC_PER_EXP * REMAINING_EXP))
        ETA_STR=$(format_time $REMAINING_SEC)
        COMPLETION_TIME=$(date -d "+${REMAINING_SEC} seconds" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date '+%Y-%m-%d %H:%M:%S')
    else
        ETA_STR="Calculating..."
        COMPLETION_TIME="Estimating..."
    fi

    # Generate progress bar
    BAR_WIDTH=50
    FILLED=$((PROGRESS_PCT * BAR_WIDTH / 100))
    BAR=$(printf "█%.0s" $(seq 1 $FILLED))$(printf "░%.0s" $(seq 1 $((BAR_WIDTH - FILLED))))

    # Update dashboard
    cat > "$DASHBOARD_FILE" <<EOF
# Hanoi PM2.5 Training Dashboard

**Last Updated**: $TIMESTAMP
**Status**: 🔄 RUNNING (PID: $TRAINING_PID)

## Progress

\`\`\`
Progress: [$BAR] ${PROGRESS_PCT}%
Experiments: $EXPERIMENTS / ~$EXPECTED_TOTAL completed
\`\`\`

## Timing

| Metric | Value |
|--------|-------|
| **Elapsed Time** | $ELAPSED |
| **Estimated Remaining** | $ETA_STR |
| **Estimated Completion** | $COMPLETION_TIME |

## Resource Usage

| Resource | Usage |
|----------|-------|
| **CPU** | ${CPU_PCT}% (multi-core) |
| **Memory** | ${MEM_MB} MB (${MEM_PCT}% of 32GB) |
| **Threads** | ~$((${CPU_PCT%.*} / 100)) cores active |

## Current Stage

Based on experiment count, currently processing:
EOF

    # Determine current horizon based on experiment count
    if [ $EXPERIMENTS -lt 25 ]; then
        echo "- **Horizon**: 1h (short-term forecast)" >> "$DASHBOARD_FILE"
    elif [ $EXPERIMENTS -lt 45 ]; then
        echo "- **Horizon**: 6h (near-term forecast)" >> "$DASHBOARD_FILE"
    elif [ $EXPERIMENTS -lt 65 ]; then
        echo "- **Horizon**: 12h (half-day forecast)" >> "$DASHBOARD_FILE"
    elif [ $EXPERIMENTS -lt 85 ]; then
        echo "- **Horizon**: 24h (day-ahead forecast)" >> "$DASHBOARD_FILE"
    elif [ $EXPERIMENTS -lt 105 ]; then
        echo "- **Horizon**: 48h (2-day forecast)" >> "$DASHBOARD_FILE"
    else
        echo "- **Horizon**: 72h (3-day forecast)" >> "$DASHBOARD_FILE"
    fi

    cat >> "$DASHBOARD_FILE" <<EOF
- **Models**: Ridge, HGB, LightGBM, XGBoost, ExtraTrees
- **Experiments**: Regression, Classification, Event Detection, Quantile, Transition

## Output Directory

\`$OUTPUT_DIR\`

## Hardware

- **CPU**: AMD Ryzen 7 2700 (8 cores / 16 threads)
- **RAM**: 32GB
- **GPU**: GTX 1660 Super 6GB (available but not used by sklearn)
- **Python**: 3.12 (conda env: dev)

---

*This dashboard auto-updates every 60 seconds*
*Monitor: \`scripts/monitor_training.sh\`*
EOF

    # Write compact status to log
    echo "[$TIMESTAMP] Progress: ${PROGRESS_PCT}% | Experiments: $EXPERIMENTS/$EXPECTED_TOTAL | CPU: ${CPU_PCT}% | Mem: ${MEM_MB}MB | ETA: $ETA_STR" >> "$LOG_FILE"

    # Write status file for quick checks
    echo "Training: ${PROGRESS_PCT}% complete | ETA: $ETA_STR | Elapsed: $ELAPSED" > "$STATUS_FILE"

    # Wait 60 seconds before next update
    sleep 60
done

# Final notification
echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "TRAINING COMPLETED AT $TIMESTAMP" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
