#!/usr/bin/env python3
"""
Generate 2018 model comparison chart ordered from worst to best RMSE
"""

import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import json

print("="*60)
print("Generating 2018 Model Comparison Chart")
print("="*60)

# Load RandomForest results
with open('rf_results.json', 'r') as f:
    rf_data = json.load(f)
print(f"\n✓ Loaded RandomForest results: RMSE={rf_data['rmse']:.1f}, MAE={rf_data['mae']:.1f}, R²={rf_data['r2']:.3f}")

# Complete model results (RMSE in µg/m³)
models_data = [
    ('Mean baseline', 32.0, 23.3, -0.001, 'random'),
    ('Linear weather', 25.9, 18.2, 0.345, 'random'),
    ('Random Forest', rf_data['rmse'], rf_data['mae'], rf_data['r2'], 'random'),
    ('HGB weather', 19.5, 13.0, 0.629, 'random'),
    ('HGB weather+time', 14.6, 9.1, 0.793, 'random'),
    ('HGB rich lags\n(chronological)', 14.5, 8.5, 0.814, 'chronological'),
    ('HGB rich lags', 10.8, 6.8, 0.883, 'random'),
    ('Blend rich lags', 10.7, 6.7, 0.886, 'random'),
]

# Sort from worst to best (descending RMSE)
models_data_sorted = sorted(models_data, key=lambda x: x[1], reverse=True)

models = [m[0] for m in models_data_sorted]
rmse_values = [m[1] for m in models_data_sorted]

# Create figure
fig, ax = plt.subplots(figsize=(12, 7))

# Create color gradient (red for worst, green for best)
n_models = len(models)
colors = []
for i in range(n_models):
    ratio = i / (n_models - 1)
    # Red to yellow to green gradient
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
ax.set_title('Hanoi PM2.5 Model Comparison (2018)\nOrdered by RMSE: Worst to Best',
             fontsize=15, fontweight='bold', pad=20)
ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
ax.set_xlim(0, max(rmse_values) * 1.18)
ax.set_axisbelow(True)

# Add improvement percentage annotation
baseline_rmse = models_data_sorted[0][1]
best_rmse = models_data_sorted[-1][1]
improvement = 100 * (baseline_rmse - best_rmse) / baseline_rmse
ax.text(0.98, 0.02, f'Total improvement: {improvement:.1f}%',
        transform=ax.transAxes, fontsize=10, style='italic',
        verticalalignment='bottom', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

# Adjust layout
plt.tight_layout()

# Save figure
output_path = '../../../assets/images/research/pm25-ai-assisted-modeling-2026.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"\n✓ Chart saved to: {output_path}")

# Also save to img directory
output_path2 = 'img/2018_model_comparison_worst_to_best.png'
plt.savefig(output_path2, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Chart also saved to: {output_path2}")

# Print summary table
print("\n" + "="*80)
print("Model Performance Summary (sorted worst to best by RMSE):")
print("="*80)
print(f"{'Model':<35} {'RMSE':>8} {'MAE':>8} {'R²':>8} {'Split':>15}")
print("-"*80)
for name, rmse, mae, r2, split in models_data_sorted:
    model_clean = name.replace('\n', ' ')
    mae_str = f"{mae:.1f}" if mae > 0 else "—"
    r2_str = f"{r2:.3f}" if r2 > -0.01 else f"{r2:.3f}"
    print(f"{model_clean:<35} {rmse:>8.1f} {mae_str:>8} {r2_str:>8} {split:>15}")
print("="*80)

print(f"\nBest model: {models_data_sorted[-1][0].replace(chr(10), ' ')}")
print(f"  RMSE: {models_data_sorted[-1][1]:.1f} µg/m³")
print(f"  MAE:  {models_data_sorted[-1][2]:.1f} µg/m³")
print(f"  R²:   {models_data_sorted[-1][3]:.3f}")

print(f"\nWorst model: {models_data_sorted[0][0]}")
print(f"  RMSE: {models_data_sorted[0][1]:.1f} µg/m³")

improvement = models_data_sorted[0][1] - models_data_sorted[-1][1]
pct_improvement = 100 * improvement / models_data_sorted[0][1]
print(f"\nImprovement: {improvement:.1f} µg/m³ ({pct_improvement:.1f}%)")

print("\n" + "="*80)
print("✓ Complete!")
print("="*80)
