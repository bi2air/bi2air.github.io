#!/usr/bin/env python3
"""
Create 2018 model comparison chart ordered from worst to best RMSE
Uses existing results from the analysis
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Results from the 2018 analysis (RMSE in µg/m³)
models_data = [
    ('Mean baseline', 32.0),
    ('Linear weather', 25.9),
    ('Random Forest', 19.9),  # From original notebook
    ('HGB weather', 19.5),
    ('HGB weather+time', 14.6),
    ('HGB rich lags\n(chronological)', 14.5),
    ('HGB rich lags', 10.8),
    ('Blend rich lags', 10.7),
]

# Sort from worst to best (descending RMSE)
models_data_sorted = sorted(models_data, key=lambda x: x[1], reverse=True)

models = [m[0] for m in models_data_sorted]
rmse_values = [m[1] for m in models_data_sorted]

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

# Create color gradient (red for worst, green for best)
colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.9, len(models)))

# Create horizontal bar chart
bars = ax.barh(models, rmse_values, color=colors, edgecolor='black', linewidth=0.8)

# Add RMSE values on the bars
for i, (model, rmse) in enumerate(zip(models, rmse_values)):
    ax.text(rmse + 0.7, i, f"{rmse:.1f}",
            va='center', ha='left', fontsize=10, fontweight='bold')

# Styling
ax.set_xlabel('RMSE (µg/m³)', fontsize=12, fontweight='bold')
ax.set_ylabel('Model', fontsize=12, fontweight='bold')
ax.set_title('Hanoi PM2.5 Model Comparison (2018)\nOrdered by RMSE: Worst to Best',
             fontsize=14, fontweight='bold', pad=20)
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.set_xlim(0, max(rmse_values) * 1.15)

# Adjust layout and save
plt.tight_layout()
output_path = '/home/uno/working/gitpage/assets/images/research/2018_model_comparison_worst_to_best.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✓ Chart saved to: {output_path}")

# Print summary
print("\n" + "="*60)
print("Model Performance (sorted worst to best by RMSE):")
print("="*60)
for model, rmse in models_data_sorted:
    print(f"{model:35s} {rmse:6.1f} µg/m³")
print("="*60)
print(f"\nBest model: {models_data_sorted[-1][0]}")
print(f"  RMSE: {models_data_sorted[-1][1]:.1f} µg/m³")
print(f"\nWorst model: {models_data_sorted[0][0]}")
print(f"  RMSE: {models_data_sorted[0][1]:.1f} µg/m³")
improvement = models_data_sorted[0][1] - models_data_sorted[-1][1]
pct_improvement = 100 * improvement / models_data_sorted[0][1]
print(f"\nImprovement: {improvement:.1f} µg/m³ ({pct_improvement:.1f}%)")
print(f"\nDataset: Hanoi 2018 (weather features)")
print(f"Note: Random Forest RMSE = 19.9 µg/m³ from original analysis")
print("="*60)
