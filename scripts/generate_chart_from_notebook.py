#!/usr/bin/env python3
"""
Generate chart based on 3.3 notebook code, updated with 8 models worst-to-best order
"""

import warnings
warnings.filterwarnings("ignore")

import os
os.environ['MPLCONFIGDIR'] = os.environ.get('TMPDIR', '/tmp')

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Output path
OUTPUT = Path("/home/uno/working/gitpage/assets/images/research/pm25-ai-assisted-modeling-2026.png")

print("="*60)
print("Generating Chart from Notebook Code")
print("="*60)

# Model results - ordered worst to best
results_data = [
    {"model": "mean_baseline", "rmse": 32.0, "mae": 23.3, "r2": -0.001},
    {"model": "linear_weather", "rmse": 25.9, "mae": 18.2, "r2": 0.345},
    {"model": "random_forest", "rmse": 20.0, "mae": 13.3, "r2": 0.610},
    {"model": "hgb_weather", "rmse": 19.5, "mae": 13.0, "r2": 0.629},
    {"model": "hgb_weather_time", "rmse": 14.6, "mae": 9.1, "r2": 0.793},
    {"model": "hgb_rich_lags_chrono", "rmse": 14.5, "mae": 8.5, "r2": 0.814},
    {"model": "hgb_rich_lags", "rmse": 10.8, "mae": 6.8, "r2": 0.883},
    {"model": "blend_rich_lags", "rmse": 10.7, "mae": 6.7, "r2": 0.886},
]

plot_df = pd.DataFrame(results_data)

# Labels for display (worst to best)
plot_df["label"] = [
    "Mean\\nbaseline",
    "Linear\\nweather",
    "Random\\nForest",
    "HGB\\nweather",
    "HGB\\nweather+time",
    "HGB rich lags\\nchronological",
    "HGB\\nrich lags",
    "Blend\\nrich lags",
]

# Colors: red to green gradient (worst to best)
colors = ["#dc2626", "#ea580c", "#f59e0b", "#eab308", "#84cc16", "#22c55e", "#10b981", "#059669"]

print("\\nModels (worst to best):")
for i, row in plot_df.iterrows():
    print(f"  {i+1}. {row['model']:<25} RMSE={row['rmse']:.1f}")

# Create figure (adapted from notebook)
fig, ax = plt.subplots(figsize=(11.5, 5.8), dpi=160)
x = np.arange(len(plot_df))
bars = ax.bar(x, plot_df["rmse"], color=colors, width=0.68)
ax.plot(x, plot_df["mae"], color="#111827", marker="o", linewidth=2, label="MAE")

ax.set_title("AI-assisted PM2.5 modeling update, Hanoi 2018", fontsize=15, weight="bold")
ax.set_ylabel("Error, µg/m³")
ax.set_xticks(x)
ax.set_xticklabels(plot_df["label"], fontsize=8.5)
ax.set_ylim(0, 36)
ax.grid(axis="y", color="#e5e7eb")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False)

# Add RMSE values on bars
for rect, val in zip(bars, plot_df["rmse"]):
    ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 0.6,
            f"{val:.1f}", ha="center", fontsize=8.5, weight="bold")

fig.text(0.01, 0.01,
         "Models ordered worst to best by RMSE. Rich-lag models use recent observed PM2.5; chronological split is the more realistic future-period check.",
         fontsize=8, color="#4b5563")

fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUTPUT, bbox_inches="tight")
print(f"\\n✓ Chart saved: {OUTPUT}")
print(f"  Size: {OUTPUT.stat().st_size:,} bytes")

plt.close()

print("\\n" + "="*60)
print("Chart generation complete!")
print("="*60)
