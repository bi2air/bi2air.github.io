#!/usr/bin/env python3
"""
Generate forecast comparison charts for the 2026 forecasting experiments page.
Two panels: short-horizon (T+1, T+6, T+12) and medium-horizon (T+24, T+48, T+72).
Period: 2025-03-01 to 2025-03-12.
"""

import warnings
warnings.filterwarnings("ignore")

import os
os.environ['MPLCONFIGDIR'] = os.environ.get('TMPDIR', '/tmp')

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMRegressor
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

RANDOM_STATE = 20260607
DATA_ROOT = Path("tmp/air-quality-analysis-upstream/data")
OUT_DIR = Path("assets/images/research")

PLOT_START = "2025-03-01"
PLOT_END = "2025-03-08"

SHORT_HORIZONS = [1, 12]
MEDIUM_HORIZONS = [24, 72]


def load_data(horizon):
    path = DATA_ROOT / "forecast_ready" / f"hanoi_pm25_open_meteo_forecast_h{horizon}_2015_2025.csv"
    df = pd.read_csv(path, parse_dates=["DATE", "target_time"], low_memory=False)
    df = df[df["model_ready"]].copy()
    df["target_pm25"] = pd.to_numeric(df["target_pm25"], errors="coerce")
    return df


def get_features():
    roles = pd.read_csv(DATA_ROOT / "forecast_ready/forecast_supervised_columns.csv")
    role_map = roles.groupby("role")["column"].apply(list).to_dict()
    pm25_history = role_map["pm25_current_history_calendar"]
    forecast_weather = role_map["forecast_weather_proxy_at_target_time"]
    return pm25_history + forecast_weather


def get_model(horizon):
    if horizon in {1, 6, 12} and HAS_LGB:
        return LGBMRegressor(
            objective="regression", n_estimators=500, learning_rate=0.04,
            num_leaves=31, subsample=0.85, colsample_bytree=0.85,
            reg_lambda=1.0, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1,
        )
    if HAS_XGB:
        return XGBRegressor(
            objective="reg:squarederror", n_estimators=350, learning_rate=0.04,
            max_depth=5, subsample=0.85, colsample_bytree=0.85,
            reg_lambda=1.0, random_state=RANDOM_STATE, n_jobs=-1, tree_method="hist",
        )
    if HAS_LGB:
        return LGBMRegressor(
            objective="regression", n_estimators=500, learning_rate=0.04,
            num_leaves=31, subsample=0.85, colsample_bytree=0.85,
            reg_lambda=1.0, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1,
        )
    from sklearn.ensemble import HistGradientBoostingRegressor
    return HistGradientBoostingRegressor(
        learning_rate=0.06, max_iter=300, max_leaf_nodes=31,
        l2_regularization=0.05, early_stopping=True, random_state=RANDOM_STATE,
    )


def train_and_predict(horizon, features):
    print(f"  Training T+{horizon}h model...")
    df = load_data(horizon)
    subset = df.dropna(subset=["target_pm25"]).copy()
    X = subset[features].replace([np.inf, -np.inf], np.nan)
    mask = X.notna().all(axis=1)
    subset = subset.loc[mask].copy()
    X = X.loc[mask].copy()

    train_mask = subset["split"].eq("train").to_numpy()
    test_mask = subset["split"].isin(["test", "valid"]).to_numpy()

    model = get_model(horizon)
    model.fit(X.loc[train_mask], subset.loc[train_mask, "target_pm25"].to_numpy(float))

    test = subset.loc[test_mask].copy()
    test["pred_pm25"] = model.predict(X.loc[test_mask]).astype(float)

    # Filter to our plot window
    window = test[
        (test["target_time"] >= PLOT_START) & (test["target_time"] < PLOT_END)
    ].sort_values("target_time").copy()

    print(f"    T+{horizon}h: {len(window)} points in window")
    return window[["target_time", "target_pm25", "pred_pm25"]]


def plot_panel(results, horizons, title, filename):
    fig, (ax_main, ax_err) = plt.subplots(
        nrows=2, ncols=1, figsize=(12, 6), dpi=160,
        sharex=True, height_ratios=[2.5, 1],
        gridspec_kw={"hspace": 0.08}
    )

    # Top panel: actual vs predicted
    actual_h = min(horizons)
    actual = results[actual_h]
    ax_main.plot(actual["target_time"], actual["target_pm25"],
                 color="black", linewidth=0.6, marker="o", markersize=3,
                 label="Actual", zorder=10)

    colors = {1: "#2563eb", 12: "#059669", 24: "#2563eb", 72: "#dc2626"}
    markers = {1: "s", 12: "D", 24: "s", 72: "D"}

    for h in horizons:
        df = results[h]
        ax_main.plot(df["target_time"], df["pred_pm25"],
                     color=colors[h], linewidth=0.5, alpha=0.85,
                     marker=markers[h], markersize=2.5,
                     label=f"T+{h}h forecast")

    ax_main.set_title(title, fontsize=13, weight="bold")
    ax_main.set_ylabel(r"PM$_{2.5}$ ($\mu g/m^3$)")
    ax_main.legend(loc="upper right", frameon=True, fontsize=9)
    ax_main.grid(axis="y", color="#e5e7eb", alpha=0.7)
    ax_main.spines[["top", "right"]].set_visible(False)

    # Bottom panel: error bars (predicted - actual)
    bar_width = pd.Timedelta(hours=0.35)
    offsets = {h: i for i, h in enumerate(horizons)}
    n = len(horizons)

    for h in horizons:
        df = results[h].copy()
        df["error"] = df["pred_pm25"] - df["target_pm25"]
        offset = pd.Timedelta(hours=(offsets[h] - (n - 1) / 2) * 0.4)
        times = df["target_time"] + offset
        bar_colors = [colors[h] if e >= 0 else "#f87171" for e in df["error"]]
        ax_err.bar(times, df["error"], width=bar_width,
                   color=colors[h], alpha=0.6, label=f"T+{h}h error")

    ax_err.axhline(0, color="black", linewidth=0.5)
    ax_err.set_ylabel(r"Error ($\mu g/m^3$)")
    ax_err.set_xlabel("Date (March 2025)")
    ax_err.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax_err.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax_err.legend(loc="upper right", frameon=True, fontsize=8)
    ax_err.grid(axis="y", color="#e5e7eb", alpha=0.7)
    ax_err.spines[["top", "right"]].set_visible(False)
    ax_err.set_xlim(pd.Timestamp(PLOT_START), pd.Timestamp(PLOT_END))

    fig.tight_layout()
    out_path = OUT_DIR / filename
    fig.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path} ({out_path.stat().st_size:,} bytes)")


def main():
    print("=" * 60)
    print("Generating PM2.5 Forecast Comparison Charts")
    print(f"Period: {PLOT_START} to {PLOT_END}")
    print("=" * 60)

    features = get_features()
    print(f"Features: {len(features)}")

    all_horizons = SHORT_HORIZONS + MEDIUM_HORIZONS
    results = {}

    for h in all_horizons:
        results[h] = train_and_predict(h, features)

    print("\nGenerating short-horizon chart...")
    plot_panel(results, SHORT_HORIZONS,
              r"Hanoi PM$_{2.5}$ forecast: short horizons (T+1h, T+12h)",
              "2026-forecast-short-horizon.png")

    print("Generating medium-horizon chart...")
    plot_panel(results, MEDIUM_HORIZONS,
              r"Hanoi PM$_{2.5}$ forecast: medium horizons (T+24h, T+72h)",
              "2026-forecast-medium-horizon.png")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
