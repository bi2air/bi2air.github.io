#!/usr/bin/env python3
"""Evaluate standardized model families for a given forecast horizon."""

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from statsmodels.tsa.statespace.sarimax import SARIMAX
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")

DATA_ROOT = Path("tmp/air-quality-analysis-upstream/data/forecast_ready")
SPLIT_DATE = pd.Timestamp("2024-01-01")

FULL_BASE = [
    "pm25_now",
    "nowcast_pm25",
    "dist_to_boundary",
    "dist_to_next_up",
    "dist_to_next_down",
    "current_bin_run_hours",
]
TEMPORAL = ["hour", "month", "dayofyear", "dow", "sin_hour", "cos_hour", "sin_doy", "cos_doy"]


def load_horizon_frame(horizon: int) -> pd.DataFrame:
    path = DATA_ROOT / f"hanoi_pm25_open_meteo_forecast_h{horizon}_2015_2025.csv"
    df = pd.read_csv(path, parse_dates=["DATE", "target_time"], low_memory=False)
    return df[df["model_ready"]].copy()


def full_feature_columns(df: pd.DataFrame) -> list[str]:
    pm25 = [
        col
        for col in df.columns
        if col.startswith("pm25_lag_")
        or col.startswith("pm25_roll_")
        or col.startswith("pm25_change_")
        or col.startswith("pm25_slope_")
        or col.startswith("pm25_accel_")
    ]
    current_weather = [
        col
        for col in df.columns
        if col.startswith("current_") and col not in FULL_BASE and col not in ["current_bin", "current_bin_code"]
    ]
    forecast_weather = [col for col in df.columns if col.startswith("fcst_")]
    return [f for f in (FULL_BASE + pm25 + TEMPORAL + current_weather + forecast_weather) if f in df.columns]


def pm_only_columns(df: pd.DataFrame) -> list[str]:
    return [
        col
        for col in [
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
        if col in df.columns
    ]


def linear_ar_columns(df: pd.DataFrame) -> list[str]:
    return [
        col
        for col in [
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
        if col in df.columns
    ]


def metrics(y_true: np.ndarray, pred: np.ndarray) -> dict:
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, pred))),
        "mae": float(mean_absolute_error(y_true, pred)),
        "r2": float(r2_score(y_true, pred)),
    }


def fit_tree_model(df: pd.DataFrame, feature_cols: list[str], model) -> dict:
    train = df[df["DATE"] < SPLIT_DATE].copy()
    valid = df[df["DATE"] >= SPLIT_DATE].copy()
    train = train.dropna(subset=feature_cols + ["target_pm25"]).copy()
    valid = valid.dropna(subset=feature_cols + ["target_pm25"]).copy()

    x_train = train[feature_cols].replace([np.inf, -np.inf], np.nan)
    y_train = train["target_pm25"].astype(float).to_numpy()
    x_valid = valid[feature_cols].replace([np.inf, -np.inf], np.nan)
    y_valid = valid["target_pm25"].astype(float).to_numpy()

    imputer = SimpleImputer(strategy="median")
    x_train = imputer.fit_transform(x_train)
    x_valid = imputer.transform(x_valid)

    model.fit(x_train, y_train)
    pred = model.predict(x_valid)
    out = metrics(y_valid, pred)
    out.update({"n_train": int(len(train)), "n_valid": int(len(valid)), "n_features": int(len(feature_cols))})
    return out


def fit_linear_ar(df: pd.DataFrame, feature_cols: list[str]) -> dict:
    train = df[df["DATE"] < SPLIT_DATE].copy()
    valid = df[df["DATE"] >= SPLIT_DATE].copy()
    train = train.dropna(subset=feature_cols + ["target_pm25"]).copy()
    valid = valid.dropna(subset=feature_cols + ["target_pm25"]).copy()

    model = LinearRegression().fit(train[feature_cols], train["target_pm25"].astype(float))
    pred = model.predict(valid[feature_cols])
    out = metrics(valid["target_pm25"].astype(float).to_numpy(), pred)
    out.update({"n_train": int(len(train)), "n_valid": int(len(valid)), "n_features": int(len(feature_cols))})
    return out


def fit_sarima(df: pd.DataFrame, horizon: int) -> dict:
    train = df[df["DATE"] < SPLIT_DATE].dropna(subset=["pm25"]).copy().sort_values("DATE")
    valid = df[df["DATE"] >= SPLIT_DATE].dropna(subset=["pm25", "target_pm25"]).copy().sort_values("DATE")
    series_train = train["pm25"].astype(float).reset_index(drop=True)

    # Forecast from the issuance-time PM2.5 series, not the future target series.
    # For each validation row at time t, predict t+h using only observations available up to t.
    model = SARIMAX(
        series_train,
        order=(2, 0, 0),
        seasonal_order=(1, 0, 0, 24),
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False)

    preds = []
    for pm_now in valid["pm25"].astype(float).to_numpy():
        forecast = model.forecast(steps=horizon)
        preds.append(float(forecast.iloc[-1]))
        # `extend` updates the filtered state without rebuilding the full result object.
        model = model.extend([pm_now])

    y_valid = valid["target_pm25"].astype(float).to_numpy()
    out = metrics(y_valid, np.asarray(preds, dtype=float))
    out.update({"n_train": int(len(train)), "n_valid": int(len(valid)), "n_features": None})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--models",
        nargs="+",
        choices=["xgb_full", "hgb_full", "xgb_pm_only", "hgb_pm_only", "linear_ar", "sarima_24h"],
        default=["xgb_full", "hgb_full", "xgb_pm_only", "hgb_pm_only", "linear_ar", "sarima_24h"],
        help="Subset of standardized model families to evaluate.",
    )
    args = parser.parse_args()

    df = load_horizon_frame(args.horizon)
    full_cols = full_feature_columns(df)
    pm_cols = pm_only_columns(df)
    ar_cols = linear_ar_columns(df)

    result = {
        "horizon": args.horizon,
        "dataset": str(DATA_ROOT / f"hanoi_pm25_open_meteo_forecast_h{args.horizon}_2015_2025.csv"),
        "split_rule": "DATE < 2024-01-01 train, DATE >= 2024-01-01 valid",
        "feature_groups": {
            "full_baseline": full_cols,
            "pm_only": pm_cols,
            "linear_ar": ar_cols,
        },
        "models": {},
    }

    selected_models = set(args.models)

    if "xgb_full" in selected_models:
        result["models"]["xgb_full"] = fit_tree_model(
            df,
            full_cols,
            XGBRegressor(
                objective="reg:squarederror",
                random_state=20260607,
                n_estimators=500,
                max_depth=5,
                learning_rate=0.02,
                tree_method="hist",
                subsample=0.9,
                colsample_bytree=0.85,
                reg_lambda=1.0,
                n_jobs=-1,
            ),
        )
    if "hgb_full" in selected_models:
        result["models"]["hgb_full"] = fit_tree_model(
            df,
            full_cols,
            HistGradientBoostingRegressor(
                learning_rate=0.04,
                max_iter=500,
                max_leaf_nodes=31,
                min_samples_leaf=20,
                l2_regularization=0.05,
                early_stopping=True,
                validation_fraction=0.1,
                random_state=20260611,
            ),
        )
    if "xgb_pm_only" in selected_models:
        result["models"]["xgb_pm_only"] = fit_tree_model(
            df,
            pm_cols,
            XGBRegressor(
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
            ),
        )
    if "hgb_pm_only" in selected_models:
        result["models"]["hgb_pm_only"] = fit_tree_model(
            df,
            pm_cols,
            HistGradientBoostingRegressor(
                learning_rate=0.05,
                max_iter=500,
                max_leaf_nodes=31,
                min_samples_leaf=20,
                l2_regularization=0.05,
                early_stopping=True,
                validation_fraction=0.1,
                random_state=20260611,
            ),
        )
    if "linear_ar" in selected_models:
        result["models"]["linear_ar"] = fit_linear_ar(df, ar_cols)
    if "sarima_24h" in selected_models:
        result["models"]["sarima_24h"] = fit_sarima(df, args.horizon)

    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
