#!/usr/bin/env python3
"""
Generate PNG chart using PIL/Pillow (minimal dependencies)
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    print("✓ PIL available")
except ImportError:
    print("ERROR: PIL/Pillow not available")
    sys.exit(1)

# Setup
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = REPO_ROOT / "assets" / "images" / "research" / "pm25-ai-assisted-modeling-2026.png"

print("="*60)
print("Generating PNG Chart with PIL")
print("="*60)

# Data
models = [
    ('Mean baseline', 32.0),
    ('Linear weather', 25.9),
    ('Random Forest', 20.0),
    ('HGB weather', 19.5),
    ('HGB weather+time', 14.6),
    ('HGB rich lags (chrono)', 14.5),
    ('HGB rich lags', 10.8),
    ('Blend rich lags', 10.7),
]

# Image settings
width, height = 1200, 700
bg_color = (255, 255, 255)
img = Image.new('RGB', (width, height), bg_color)
draw = ImageDraw.Draw(img)

# Try to load font
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    value_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
except:
    title_font = label_font = value_font = ImageFont.load_default()

# Layout
margin_left = 220
margin_right = 80
margin_top = 100
margin_bottom = 80
chart_width = width - margin_left - margin_right
chart_height = height - margin_top - margin_bottom

# Title
title = "Hanoi PM2.5 Model Comparison (2018)"
subtitle = "Ordered by RMSE: Worst to Best"
draw.text((width//2, 30), title, fill=(0, 0, 0), font=title_font, anchor="mm")
draw.text((width//2, 55), subtitle, fill=(0, 0, 0), font=label_font, anchor="mm")

# Colors (red to green gradient)
def get_color(idx, total):
    ratio = idx / (total - 1)
    if ratio < 0.5:
        r = 255
        g = int(255 * ratio * 2)
        b = 0
    else:
        r = int(255 * (1 - (ratio - 0.5) * 2))
        g = 255
        b = 0
    return (r, g, b)

# Draw bars
max_rmse = max(m[1] for m in models)
bar_height = chart_height // len(models) - 10
y_start = margin_top

for idx, (model, rmse) in enumerate(models):
    y = y_start + idx * (bar_height + 10)

    # Bar width proportional to RMSE
    bar_width = int((rmse / max_rmse) * chart_width * 0.85)
    x = margin_left

    # Draw bar
    color = get_color(idx, len(models))
    draw.rectangle([x, y, x + bar_width, y + bar_height],
                   fill=color, outline=(0, 0, 0), width=2)

    # Model label (left)
    draw.text((margin_left - 10, y + bar_height//2), model,
              fill=(0, 0, 0), font=label_font, anchor="rm")

    # RMSE value (on bar)
    draw.text((x + bar_width + 10, y + bar_height//2), f"{rmse:.1f}",
              fill=(0, 0, 0), font=value_font, anchor="lm")

# X-axis label
draw.text((margin_left + chart_width//2, height - 30),
          "RMSE (µg/m³)", fill=(0, 0, 0), font=label_font, anchor="mm")

# Y-axis label
draw.text((30, margin_top + chart_height//2),
          "Model", fill=(0, 0, 0), font=label_font, anchor="mm")

# Improvement annotation
baseline_rmse = models[0][1]
best_rmse = models[-1][1]
improvement = 100 * (baseline_rmse - best_rmse) / baseline_rmse
draw.rectangle([width - 200, height - 70, width - 20, height - 30],
               fill=(245, 222, 179), outline=(0, 0, 0))
draw.text((width - 110, height - 50), f"Improvement: {improvement:.1f}%",
          fill=(0, 0, 0), font=value_font, anchor="mm")

# Save
img.save(OUTPUT_FILE, 'PNG', dpi=(300, 300))
print(f"\n✓ Chart saved: {OUTPUT_FILE}")
print(f"  Size: {OUTPUT_FILE.stat().st_size:,} bytes")
print("\n" + "="*60)
print("Chart generation complete!")
print("="*60)
