#!/bin/bash
# Generate chart PNG using browser screenshot with proper wait

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HTML_FILE="$REPO_ROOT/assets/images/research/generate_chart.html"
OUTPUT_FILE="$REPO_ROOT/assets/images/research/pm25-ai-assisted-modeling-2026.png"
TEMP_HTML="$TMPDIR/chart_with_callback.html"
TEMP_FILE="$TMPDIR/chart_temp_$$.png"

echo "=========================================="
echo "Generating Chart PNG with Browser"
echo "=========================================="

# Create a wrapper HTML that auto-screenshots after delay
cat > "$TEMP_HTML" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Chart Ready</title>
    <style>
        body { margin: 0; padding: 20px; font-family: Arial; background: white; }
        #chart { width: 1200px; height: 700px; }
        #status { position: absolute; top: 10px; right: 10px;
                  background: lime; padding: 10px; font-weight: bold;
                  border: 2px solid green; display: none; }
    </style>
</head>
<body>
    <div id="status">READY_TO_SCREENSHOT</div>
    <div id="chart"></div>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script>
        const data = [
            {model: 'Mean baseline', rmse: 32.0, mae: 23.3, r2: -0.001},
            {model: 'Linear weather', rmse: 25.9, mae: 18.2, r2: 0.345},
            {model: 'Random Forest', rmse: 20.0, mae: 13.3, r2: 0.610},
            {model: 'HGB weather', rmse: 19.5, mae: 13.0, r2: 0.629},
            {model: 'HGB weather+time', rmse: 14.6, mae: 9.1, r2: 0.793},
            {model: 'HGB rich lags<br>(chronological)', rmse: 14.5, mae: 8.5, r2: 0.814},
            {model: 'HGB rich lags', rmse: 10.8, mae: 6.8, r2: 0.883},
            {model: 'Blend rich lags', rmse: 10.7, mae: 6.7, r2: 0.886}
        ];
        data.sort((a, b) => b.rmse - a.rmse);
        const models = data.map(d => d.model);
        const rmse = data.map(d => d.rmse);
        const colors = rmse.map((val, idx) => {
            const ratio = idx / (rmse.length - 1);
            let r, g, b;
            if (ratio < 0.5) {
                r = 255; g = Math.round(255 * ratio * 2); b = 0;
            } else {
                r = Math.round(255 * (1 - (ratio - 0.5) * 2)); g = 255; b = 0;
            }
            return `rgb(${r},${g},${b})`;
        });
        const trace = {
            type: 'bar', x: rmse, y: models, orientation: 'h',
            text: rmse.map(r => r.toFixed(1)), textposition: 'outside',
            textfont: {size: 14, color: 'black', family: 'Arial', weight: 'bold'},
            marker: {color: colors, line: {color: 'black', width: 1.5}}
        };
        const improvement = 100 * (data[0].rmse - data[data.length-1].rmse) / data[0].rmse;
        const layout = {
            title: {text: '<b>Hanoi PM2.5 Model Comparison (2018)</b><br>Ordered by RMSE: Worst to Best', font: {size: 20}},
            xaxis: {title: {text: '<b>RMSE (µg/m³)</b>', font: {size: 16}}, gridcolor: '#e0e0e0', range: [0, Math.max(...rmse) * 1.18]},
            yaxis: {title: {text: '<b>Model</b>', font: {size: 16}}, automargin: true, tickfont: {size: 13}},
            margin: {l: 220, r: 80, t: 120, b: 80},
            plot_bgcolor: 'white', paper_bgcolor: 'white',
            annotations: [{text: `Total improvement: ${improvement.toFixed(1)}%`, xref: 'paper', yref: 'paper',
                x: 0.98, y: 0.02, showarrow: false, font: {size: 12, style: 'italic'}, bgcolor: 'wheat', borderpad: 8, opacity: 0.8}],
            width: 1200, height: 700
        };
        Plotly.newPlot('chart', [trace], layout, {responsive: false}).then(function() {
            // Show ready indicator after chart is rendered
            setTimeout(function() {
                document.getElementById('status').style.display = 'block';
                document.title = 'READY_TO_SCREENSHOT';
            }, 1000);
        });
    </script>
</body>
</html>
EOF

echo "Step 1: Created wrapper HTML with ready callback"

# Try Chrome with better timing
echo "Step 2: Taking screenshot with Chrome..."
timeout 30 google-chrome \
    --headless=new \
    --disable-gpu \
    --window-size=1240,750 \
    --force-device-scale-factor=2 \
    --screenshot="$TEMP_FILE" \
    --hide-scrollbars \
    --run-all-compositor-stages-before-draw \
    --disable-background-timer-throttling \
    --disable-renderer-backgrounding \
    --disable-backgrounding-occluded-windows \
    "file://$TEMP_HTML" 2>/dev/null

if [ -f "$TEMP_FILE" ] && [ $(stat -c%s "$TEMP_FILE" 2>/dev/null || stat -f%z "$TEMP_FILE" 2>/dev/null) -gt 10000 ]; then
    mv "$TEMP_FILE" "$OUTPUT_FILE"
    echo "✓ Chart generated: $OUTPUT_FILE"
    echo "  Size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"

    # Commit
    cd "$REPO_ROOT"
    git add "$OUTPUT_FILE"
    echo "✓ Staged for commit"
    echo ""
    echo "=========================================="
    echo "Success! Chart generated and staged."
    echo "=========================================="
else
    echo "ERROR: Screenshot failed or file too small"
    ls -lh "$TEMP_FILE" 2>/dev/null || echo "No temp file created"
    exit 1
fi
