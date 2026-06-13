#!/usr/bin/env python3
"""
Generate static PNG chart for 2018 model comparison
Uses matplotlib instead of Plotly for reliable static image generation
"""

import sys
import json
from pathlib import Path

# Try to import matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    print("✓ matplotlib available")
except ImportError:
    print("ERROR: matplotlib not available")
    print("Please install: pip install matplotlib")
    print("\nAlternative: Use the Plotly HTML file in a browser:")
    print("  1. Open: file:///home/uno/working/gitpage/assets/images/research/generate_chart.html")
    print("  2. Click 'Download PNG' button")
    print("  3. Move to: assets/images/research/pm25-ai-assisted-modeling-2026.png")
    sys.exit(1)

# Setup paths
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = REPO_ROOT / "assets" / "images" / "research" / "pm25-ai-assisted-modeling-2026.png"

print("="*60)
print("Generating Static Chart with Matplotlib")
print("="*60)

# Model data with complete metrics
models_data = [
    ('Mean baseline', 32.0, 23.3, -0.001),
    ('Linear weather', 25.9, 18.2, 0.345),
    ('Random Forest', 20.0, 13.3, 0.610),
    ('HGB weather', 19.5, 13.0, 0.629),
    ('HGB weather+time', 14.6, 9.1, 0.793),
    ('HGB rich lags\n(chronological)', 14.5, 8.5, 0.814),
    ('HGB rich lags', 10.8, 6.8, 0.883),
    ('Blend rich lags', 10.7, 6.7, 0.886),
]

# Sort from worst to best (descending RMSE)
models_data_sorted = sorted(models_data, key=lambda x: x[1], reverse=True)

models = [m[0] for m in models_data_sorted]
rmse_values = [m[1] for m in models_data_sorted]

print("\nModels (worst to best):")
for i, (model, rmse, mae, r2) in enumerate(models_data_sorted):
    print(f"  {i+1}. {model.replace(chr(10), ' '):<35} RMSE={rmse:.1f}")

# Create figure
fig, ax = plt.subplots(figsize=(12, 7))

# Create color gradient (red to green)
n_models = len(models)
colors = []
for i in range(n_models):
    ratio = i / (n_models - 1)
    if ratio < 0.5:
        # Red to yellow
        r = 1.0
        g = ratio * 2
        b = 0.0
    else:
        # Yellow to green
        r = 1.0 - (ratio - 0.5) * 2
        g = 1.0
        b = 0.0
    colors.append((r, g, b))

# Create horizontal bar chart
bars = ax.barh(models, rmse_values, color=colors, edgecolor='black', linewidth=1.0, height=0.7)

# Add RMSE values on the bars
for i, (model, rmse) in enumerate(zip(models, rmse_values)):
    ax.text(rmse + 0.8, i, f"{rmse:.1f}",
            va='center', ha='left', fontsize=11, fontweight='bold')

# Styling
ax.set_xlabel('RMSE (µg/m³)', fontsize=13, fontweight='bold')
ax.set_ylabel('Model', fontsize=13, fontweight='bold')
ax.set_title('Hanoi PM2.5 Model Comparison (2018)\\nOrdered by RMSE: Worst to Best',
             fontsize=15, fontweight='bold', pad=20)
ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_xlim(0, max(rmse_values) * 1.18)
ax.set_axisbelow(True)

# Add improvement annotation
baseline_rmse = models_data_sorted[0][1]
best_rmse = models_data_sorted[-1][1]
improvement = 100 * (baseline_rmse - best_rmse) / baseline_rmse
ax.text(0.98, 0.02, f'Total improvement: {improvement:.1f}%',
        transform=ax.transAxes, fontsize=10, style='italic',
        verticalalignment='bottom', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Adjust layout and save
plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight', facecolor='white')
print(f"\n✓ Chart saved to: {OUTPUT_FILE}")
print(f"  Size: {OUTPUT_FILE.stat().st_size:,} bytes")

print("\n" + "="*60)
print("Chart generation complete!")
print("="*60)
print("\nNext steps:")
print("  1. View: xdg-open", OUTPUT_FILE)
print("  2. Verify RandomForest is visible at position 3")
print("  3. Commit: git add", OUTPUT_FILE)
print("="*60)
