#!/usr/bin/env python3
"""
Complete automated pipeline: Run RF analysis → Generate chart → Stage for git
"""

import subprocess
import sys
import os
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).parent.parent
ANALYSIS_DIR = REPO_ROOT / "tmp" / "air-quality-analysis"
HTML_FILE = REPO_ROOT / "assets" / "images" / "research" / "generate_chart.html"
OUTPUT_FILE = REPO_ROOT / "assets" / "images" / "research" / "pm25-ai-assisted-modeling-2026.png"

print("="*60)
print("2018 PM2.5 Complete Automated Pipeline")
print("="*60)

# Step 1: Run RandomForest analysis
print("\n1. Running RandomForest analysis...")
os.chdir(ANALYSIS_DIR)
result = subprocess.run([sys.executable, "run_rf_analysis.py"], capture_output=True, text=True)
if result.returncode != 0:
    print(f"ERROR: RandomForest analysis failed:\n{result.stderr}")
    sys.exit(1)
print(result.stdout)

# Step 2: Generate chart using Chrome/Chromium
print("\n2. Generating chart with headless browser...")

# Try to find available browser
browsers = [
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/snap/bin/chromium",
]

browser_cmd = None
for browser in browsers:
    if os.path.exists(browser):
        browser_cmd = browser
        break

if not browser_cmd:
    print("ERROR: No Chrome/Chromium browser found")
    print("Please install Chrome or open the HTML file manually:")
    print(f"  file://{HTML_FILE}")
    sys.exit(1)

print(f"Using browser: {browser_cmd}")

# Generate screenshot with Chrome headless
try:
    # First try: new headless mode with longer wait for Plotly
    cmd = [
        browser_cmd,
        "--headless=new",
        "--disable-gpu",
        "--window-size=1200,850",  # Slightly taller
        "--force-device-scale-factor=2",
        f"--screenshot={OUTPUT_FILE}",
        "--hide-scrollbars",
        "--virtual-time-budget=15000",  # Wait 15s for Plotly to fully render
        f"file://{HTML_FILE}"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)

    if not OUTPUT_FILE.exists() or OUTPUT_FILE.stat().st_size < 1000:
        # Try alternative method
        print("Trying alternative headless method...")
        cmd[1] = "--headless"
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

except Exception as e:
    print(f"ERROR: Screenshot failed: {e}")
    print("\nAlternative: Open this file in browser and click 'Download PNG':")
    print(f"  file://{HTML_FILE}")
    sys.exit(1)

# Step 3: Verify output
if OUTPUT_FILE.exists() and OUTPUT_FILE.stat().st_size > 1000:
    size = OUTPUT_FILE.stat().st_size
    print(f"\n✓ Chart generated successfully!")
    print(f"  Output: {OUTPUT_FILE}")
    print(f"  Size: {size:,} bytes")

    # Step 4: Stage for git
    os.chdir(REPO_ROOT)
    subprocess.run(["git", "add", str(OUTPUT_FILE)])
    subprocess.run(["git", "add", "docs/research/hanoi-pm25-ai-assisted-modeling-2018.md"])

    print(f"\n✓ Files staged for commit")
    print("\n" + "="*60)
    print("Pipeline complete! Ready to commit:")
    print("  git commit -m 'Add 2018 RF metrics and worst-to-best chart'")
    print("="*60)
else:
    print("\nERROR: Chart not generated or file too small")
    print(f"Expected: {OUTPUT_FILE}")
    print("\nPlease open this file manually:")
    print(f"  file://{HTML_FILE}")
    sys.exit(1)
