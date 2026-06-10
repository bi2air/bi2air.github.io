#!/bin/bash
# Automated chart generation pipeline for 2018 PM2.5 analysis

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HTML_FILE="$REPO_ROOT/assets/images/research/generate_chart.html"
OUTPUT_FILE="$REPO_ROOT/assets/images/research/pm25-ai-assisted-modeling-2026.png"

echo "=========================================="
echo "2018 PM2.5 Model Comparison Chart Pipeline"
echo "=========================================="

cd "$REPO_ROOT/tmp/air-quality-analysis"

# Step 1: Run RandomForest analysis
echo ""
echo "Step 1: Running RandomForest analysis..."
python3 run_rf_analysis.py

# Step 2: Generate chart using Chrome headless
echo ""
echo "Step 2: Generating chart with headless Chrome..."

# Convert file path to file:// URL
HTML_URL="file://$HTML_FILE"

# Use Chrome to render and screenshot
google-chrome \
    --headless \
    --disable-gpu \
    --window-size=1200,800 \
    --screenshot="$OUTPUT_FILE" \
    --hide-scrollbars \
    --force-device-scale-factor=2 \
    "$HTML_URL" 2>/dev/null || {
    echo "ERROR: Chrome screenshot failed. Trying alternative method..."

    # Try with different Chrome flags
    google-chrome \
        --headless=new \
        --screenshot="$OUTPUT_FILE" \
        --window-size=1200,800 \
        --default-background-color=0 \
        "$HTML_URL" 2>/dev/null || {
        echo "ERROR: Could not generate screenshot with Chrome."
        echo "Please open $HTML_FILE in a browser and click 'Download PNG'"
        exit 1
    }
}

# Step 3: Verify output
if [ -f "$OUTPUT_FILE" ]; then
    file_size=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
    echo ""
    echo "✓ Chart generated successfully!"
    echo "  Output: $OUTPUT_FILE"
    echo "  Size: $file_size bytes"

    # Step 4: Stage for git commit
    cd "$REPO_ROOT"
    git add "$OUTPUT_FILE"
    git add docs/research/hanoi-pm25-ai-assisted-modeling-2018.md

    echo ""
    echo "✓ Files staged for commit"
    echo ""
    echo "=========================================="
    echo "Pipeline complete! Ready to commit:"
    echo "  git commit -m 'Add 2018 RF metrics and worst-to-best chart'"
    echo "=========================================="
else
    echo ""
    echo "ERROR: Output file not created"
    exit 1
fi
