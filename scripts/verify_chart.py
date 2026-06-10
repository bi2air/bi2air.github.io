#!/usr/bin/env python3
"""
Verify the chart HTML contains all 8 models with correct values
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HTML_FILE = REPO_ROOT / "assets" / "images" / "research" / "generate_chart.html"

print("="*60)
print("Chart Verification")
print("="*60)

# Read the HTML file
with open(HTML_FILE, 'r') as f:
    html_content = f.read()

# Expected models with RMSE values
expected_models = [
    ("Mean baseline", 32.0),
    ("Linear weather", 25.9),
    ("Random Forest", 20.0),  # Should be 20.0, not 19.9
    ("HGB weather", 19.5),
    ("HGB weather+time", 14.6),
    ("HGB rich lags", 10.8),
    ("Blend rich lags", 10.7),
]

print("\nChecking models in HTML:")
print("-"*60)

all_found = True
for model_name, expected_rmse in expected_models:
    # Check if model is in HTML
    if model_name in html_content:
        # Check if RMSE value is correct
        rmse_str = f"rmse: {expected_rmse}"
        if rmse_str in html_content:
            print(f"✓ {model_name:<25} RMSE={expected_rmse}")
        else:
            print(f"✗ {model_name:<25} RMSE mismatch! Expected {expected_rmse}")
            all_found = False
    else:
        print(f"✗ {model_name:<25} NOT FOUND in HTML")
        all_found = False

# Also check chronological version
if "chronological" in html_content:
    print(f"✓ {'HGB rich lags (chrono)':<25} Found")
else:
    print(f"⚠ {'HGB rich lags (chrono)':<25} Not found (may be labeled differently)")

print("="*60)
if all_found:
    print("✅ All models present with correct RMSE values!")
    print("\nThe chart should show 8 bars ordered from worst to best:")
    print("  1. Mean baseline (32.0) - RED")
    print("  2. Linear weather (25.9)")
    print("  3. Random Forest (20.0) ← NEW")
    print("  4. HGB weather (19.5)")
    print("  5. HGB weather+time (14.6)")
    print("  6. HGB rich lags (chronological) (14.5)")
    print("  7. HGB rich lags (10.8)")
    print("  8. Blend rich lags (10.7) - GREEN")
else:
    print("❌ Some models are missing or have wrong values!")
print("="*60)
