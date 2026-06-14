# Manual Chart Generation Instructions

## Why Automation Failed

The automated pipeline failed because:
1. **Chrome headless screenshots** capture before Plotly finishes rendering (blank page)
2. **Playwright MCP** has a read-only file system lock issue
3. **Virtual time budget** doesn't work reliably with Plotly's async rendering

The chart HTML is correct (verified - all 8 models with RMSE=20.0), but the PNG screenshot needs manual generation.

## Solution: Manual Chart Generation (2 minutes)

### Step 1: Open the Chart in Browser

```bash
google-chrome file:///home/uno/working/gitpage/assets/images/research/generate_chart.html
```

Or use Firefox:
```bash
firefox file:///home/uno/working/gitpage/assets/images/research/generate_chart.html
```

### Step 2: Wait for Chart to Render

You should see a horizontal bar chart with 8 bars showing:
- **Mean baseline** (32.0) - RED/orange at top
- **Linear weather** (25.9)
- **Random Forest** (20.0) ← THIS SHOULD BE VISIBLE
- **HGB weather** (19.5)
- **HGB weather+time** (14.6)
- **HGB rich lags (chronological)** (14.5)
- **HGB rich lags** (10.8)
- **Blend rich lags** (10.7) - GREEN at bottom

### Step 3: Download the Chart

**Method A: Use built-in download button**
- Click the **"Download PNG (1200x700)"** button at the top
- Or click the camera icon in the Plotly toolbar (top-right of chart)
- File saves as: `pm25-ai-assisted-modeling-2026.png`

**Method B: Use browser screenshot**
- Right-click on the chart → "Save image as..."
- Save as: `pm25-ai-assisted-modeling-2026.png`

### Step 4: Move File to Correct Location

```bash
mv ~/Downloads/pm25-ai-assisted-modeling-2026.png \
   /home/uno/working/gitpage/assets/images/research/pm25-ai-assisted-modeling-2026.png
```

### Step 5: Verify and Commit

```bash
cd /home/uno/working/gitpage

# Verify the file
ls -lh assets/images/research/pm25-ai-assisted-modeling-2026.png

# Stage and commit
git add assets/images/research/pm25-ai-assisted-modeling-2026.png
git commit -m "Add chart with all 8 models including RandomForest (RMSE=20.0)"
```

## Verification

After generating, verify RandomForest is visible:
1. Open the PNG: `xdg-open assets/images/research/pm25-ai-assisted-modeling-2026.png`
2. Check that bar #3 says "Random Forest 20.0"
3. Confirm 8 bars total (not 7)

## Alternative: Use Plotly's Built-in Download

The HTML file has been configured to auto-trigger download after 3 seconds. If you open:
```bash
google-chrome file:///home/uno/working/gitpage/scripts/generate_chart_with_delay.html
```

It will automatically download after rendering (3 second delay).

## What Was Fixed

✅ **Parent year:** Changed from 2018 → 2021 (committed: 130df3e)
✅ **RMSE consistency:** All instances now show 20.0 (committed: ac511f6)
✅ **Chart HTML:** Contains all 8 models with correct RMSE values (verified)
❌ **Chart PNG:** Needs manual generation (automation failed due to render timing)

## Root Cause

Chrome's `--virtual-time-budget` flag doesn't wait for:
- External script loading (Plotly from CDN)
- Plotly's internal rendering pipeline
- Canvas/SVG drawing operations

This is a known limitation of headless Chrome with dynamic JavaScript charts.

---

**Once you manually generate the chart, everything will be complete!**

The chart HTML is perfect - it just needs to be captured after Plotly finishes rendering, which requires a real browser session.
