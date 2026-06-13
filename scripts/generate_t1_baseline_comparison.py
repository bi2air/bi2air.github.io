#!/usr/bin/env python3
"""Generate a T+1h baseline comparison chart for Hanoi PM2.5 forecasting."""

import os
os.environ["MPLCONFIGDIR"] = os.environ.get("TMPDIR", "/tmp")

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.statespace.sarimax import SARIMAX
from xgboost import XGBRegressor

DATA_PATH = Path("tmp/air-quality-analysis-upstream/data/forecast_ready/hanoi_pm25_open_meteo_forecast_h1_2015_2025.csv")
OUT_DIR = Path("assets/images/research")

PLOT_START = "2024-11-01"
PLOT_END = "2024-11-08"

AR_FEATURES = [
    "pm25",
    "pm25_lag_1h",
    "pm25_lag_2h",
    "pm25_lag_3h",
    "pm25_lag_6h",
    "pm25_lag_12h",
    "pm25_lag_24h",
    "pm25_lag_48h",
    "pm25_roll_mean_3h",
    "pm25_roll_mean_6h",
    "pm25_roll_mean_12h",
    "pm25_roll_mean_24h",
    "pm25_change_1h",
    "pm25_change_3h",
    "pm25_slope_6h",
]

PM_ONLY_FEATURES = [
    "pm25",
    "pm25_lag_1h",
    "pm25_lag_2h",
    "pm25_lag_3h",
    "pm25_lag_6h",
    "pm25_lag_12h",
    "pm25_lag_24h",
    "pm25_lag_48h",
    "pm25_lag_72h",
    "pm25_roll_mean_3h",
    "pm25_roll_max_3h",
    "pm25_roll_min_3h",
    "pm25_roll_mean_6h",
    "pm25_roll_max_6h",
    "pm25_roll_min_6h",
    "pm25_roll_mean_12h",
    "pm25_roll_max_12h",
    "pm25_roll_min_12h",
    "pm25_roll_mean_24h",
    "pm25_roll_max_24h",
    "pm25_roll_min_24h",
    "pm25_roll_mean_48h",
    "pm25_roll_max_48h",
    "pm25_roll_min_48h",
    "pm25_roll_mean_72h",
    "pm25_roll_max_72h",
    "pm25_roll_min_72h",
    "pm25_change_1h",
    "pm25_change_3h",
    "pm25_change_6h",
    "pm25_change_12h",
    "pm25_change_24h",
    "pm25_slope_6h",
    "pm25_slope_24h",
    "pm25_accel_6h",
]

NAIVE_BASELINE_SPECS = [
    ("Persistence", "pm25", "#6b7280"),
    ("Rolling mean 3h", "pm25_roll_mean_3h", "#2563eb"),
    ("Rolling mean 12h", "pm25_roll_mean_12h", "#60a5fa"),
    ("NowCast", "nowcast_pm25", "#059669"),
]

STAT_BASELINE_SPECS = [
    ("SARIMA(24h)", "pred_sarima", "#7c3aed"),
    ("Linear AR", "pred_ar", "#dc2626"),
    ("HGB PM-only", "pred_hgb_pm", "#d97706"),
    ("XGB PM-only", "pred_xgb_pm", "#0891b2"),
]


def load_frame() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["DATE", "target_time"], low_memory=False)
    df = df[df["model_ready"]].copy()

    numeric_cols = {
        "target_pm25",
        "pm25",
        "nowcast_pm25",
        "pm25_roll_mean_3h",
        "pm25_roll_mean_12h",
        "pm25_change_1h",
        "pm25_change_3h",
        "pm25_slope_6h",
        *PM_ONLY_FEATURES,
        *AR_FEATURES,
    }
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fit_ar_baseline(df: pd.DataFrame) -> pd.DataFrame:
    train = df[df["split"].eq("train")].dropna(subset=AR_FEATURES + ["target_pm25"]).copy()
    ready = df.dropna(subset=AR_FEATURES).copy()

    model = LinearRegression()
    model.fit(train[AR_FEATURES], train["target_pm25"])
    ready["pred_ar"] = model.predict(ready[AR_FEATURES]).astype(float)
    return ready


def fit_sarima_baseline(df: pd.DataFrame) -> pd.DataFrame:
    train = df[df["split"].eq("train")].dropna(subset=["target_pm25"]).copy()
    holdout = df[df["split"].isin(["valid", "test"])].dropna(subset=["target_pm25"]).copy()

    model = SARIMAX(
        train["target_pm25"].reset_index(drop=True),
        order=(2, 0, 0),
        seasonal_order=(1, 0, 0, 24),
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    result = model.fit(disp=False)
    pred_holdout = result.apply(
        holdout["target_pm25"].reset_index(drop=True),
        refit=False,
    ).fittedvalues.to_numpy(float)

    out = df.copy()
    out["pred_sarima"] = np.nan
    out.loc[holdout.index, "pred_sarima"] = pred_holdout
    return out


def fit_pm_only_tree_baselines(df: pd.DataFrame) -> pd.DataFrame:
    subset = df.dropna(subset=PM_ONLY_FEATURES + ["target_pm25"]).copy()
    train = subset[subset["split"].eq("train")].copy()
    ready = subset.copy()

    x_train = train[PM_ONLY_FEATURES]
    y_train = train["target_pm25"].astype(float)
    x_ready = ready[PM_ONLY_FEATURES]

    hgb = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_iter=500,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=0.05,
        early_stopping=True,
        random_state=20260611,
    )
    hgb.fit(x_train, y_train)

    xgb = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=500,
        learning_rate=0.04,
        max_depth=5,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.0,
        random_state=20260611,
        n_jobs=-1,
        tree_method="hist",
    )
    xgb.fit(x_train, y_train)

    out = df.copy()
    out["pred_hgb_pm"] = np.nan
    out["pred_xgb_pm"] = np.nan
    out.loc[ready.index, "pred_hgb_pm"] = hgb.predict(x_ready).astype(float)
    out.loc[ready.index, "pred_xgb_pm"] = xgb.predict(x_ready).astype(float)
    return out


def compute_metrics(df: pd.DataFrame, baseline_specs: list[tuple[str, str, str]]) -> pd.DataFrame:
    holdout = df[df["split"].isin(["valid", "test"])].dropna(subset=["target_pm25"]).copy()
    rows = []
    for label, col, color in baseline_specs:
        sub = holdout.dropna(subset=[col]).copy()
        err = sub[col] - sub["target_pm25"]
        rows.append(
            {
                "label": label,
                "column": col,
                "color": color,
                "rmse": float(np.sqrt(np.mean(np.square(err)))),
                "mae": float(np.mean(np.abs(err))),
                "count": int(len(sub)),
            }
        )
    return pd.DataFrame(rows).sort_values("rmse").reset_index(drop=True)


def plot(
    df: pd.DataFrame,
    metrics: pd.DataFrame,
    baseline_specs: list[tuple[str, str, str]],
    title: str,
    footer: str,
    out_path: Path,
    rmse_xlim: tuple[float, float] | None = None,
) -> None:
    window = df[
        df["split"].isin(["valid", "test"])
        & (df["target_time"] >= PLOT_START)
        & (df["target_time"] < PLOT_END)
    ].sort_values("target_time").copy()

    fig, (ax_top, ax_bottom) = plt.subplots(
        2,
        1,
        figsize=(12, 7.5),
        dpi=160,
        gridspec_kw={"height_ratios": [2.6, 1.2], "hspace": 0.2},
    )

    ax_top.plot(
        window["target_time"],
        window["target_pm25"],
        color="black",
        linewidth=1.0,
        marker="o",
        markersize=3.0,
        linestyle="-",
        label="Actual T+1 target",
        zorder=20,
    )

    for label, col, color in baseline_specs:
        ax_top.plot(
            window["target_time"],
            window[col],
            color=color,
            linewidth=1.0,
            linestyle="-",
            alpha=0.95 if label == "Linear AR" else 0.88,
            label=label,
        )

    ax_top.set_title(title, fontsize=13, weight="bold")
    ax_top.set_ylabel(r"PM$_{2.5}$ ($\mu g/m^3$)")
    ax_top.xaxis.set_major_formatter(mdates.DateFormatter("%b %d\n%H:%M"))
    ax_top.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))
    ax_top.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
    ax_top.grid(axis="y", color="#e5e7eb", alpha=0.85)
    ax_top.grid(axis="x", which="major", color="#f3f4f6", alpha=0.85)
    ax_top.spines[["top", "right"]].set_visible(False)
    ax_top.legend(loc="upper right", ncol=2, fontsize=8.5, frameon=True)
    ax_top.tick_params(axis="x", labelsize=8)

    ax_bottom.barh(metrics["label"], metrics["rmse"], color=metrics["color"], alpha=0.82)
    ax_bottom.invert_yaxis()
    ax_bottom.set_xlabel(r"Full holdout RMSE for T+1h ($\mu g/m^3$)")
    ax_bottom.grid(axis="x", color="#e5e7eb", alpha=0.85)
    ax_bottom.spines[["top", "right"]].set_visible(False)
    if rmse_xlim is not None:
        ax_bottom.set_xlim(*rmse_xlim)

    for _, row in metrics.iterrows():
        ax_bottom.text(
            row["rmse"] + 0.15,
            row["label"],
            f"RMSE {row['rmse']:.2f} | MAE {row['mae']:.2f}",
            va="center",
            fontsize=8.5,
        )

    fig.text(
        0.012,
        0.012,
        footer,
        fontsize=8.5,
        color="#374151",
    )

    fig.subplots_adjust(left=0.08, right=0.98, top=0.93, bottom=0.16, hspace=0.2)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = load_frame()
    df = fit_ar_baseline(df)
    df = fit_sarima_baseline(df)
    df = fit_pm_only_tree_baselines(df)

    naive_metrics = compute_metrics(df, NAIVE_BASELINE_SPECS)
    stat_metrics = compute_metrics(df, STAT_BASELINE_SPECS)

    naive_out = OUT_DIR / "2026-t1-baseline-naive.png"
    stat_out = OUT_DIR / "2026-t1-baseline-statistical.png"

    plot(
        df,
        naive_metrics,
        NAIVE_BASELINE_SPECS,
        r"Hanoi PM$_{2.5}$ T+1h naive baselines only (1-8 Nov 2024)",
        "Naive panel only: persistence, rolling means, and NowCast. No Linear AR or SARIMA is plotted here. All metrics are evaluated only on valid/test rows.",
        naive_out,
        rmse_xlim=(0, 22.5),
    )
    plot(
        df,
        stat_metrics,
        STAT_BASELINE_SPECS,
        r"Hanoi PM$_{2.5}$ T+1h statistical baselines only (1-8 Nov 2024)",
        "SARIMA(24h) is fit on train only and applied to valid/test with rolling one-step updates. Linear AR, HGB PM-only, and XGB PM-only are trained on train only using PM2.5-history-derived features only.",
        stat_out,
        rmse_xlim=(0, 22.5),
    )

    print("Naive baselines")
    print(naive_metrics[["label", "rmse", "mae", "count"]].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(f"Saved {naive_out}")
    print("\nStatistical baselines")
    print(stat_metrics[["label", "rmse", "mae", "count"]].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(f"Saved {stat_out}")


if __name__ == "__main__":
    main()
