#!/usr/bin/env python3
"""Train and export standardized PM2.5 forecasting model artifacts."""

import argparse
import copy
import pickle
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
import statsmodels
import xgboost
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from statsmodels.tsa.statespace.sarimax import SARIMAX
from xgboost import XGBRegressor

from evaluate_horizon_standardized import (
    DATA_ROOT,
    SPLIT_DATE,
    full_feature_columns,
    linear_ar_columns,
    load_horizon_frame,
    metrics,
    pm_only_columns,
)


MODEL_SPECS = {
    "xgb_full": {
        "display_name": "XGB full baseline",
        "feature_scope": "Full baseline",
        "lib": "xgboost",
        "note": "Open-Meteo full baseline with PM2.5 history, temporal features, current weather, and target-time forecast weather.",
    },
    "hgb_full": {
        "display_name": "HGB full baseline",
        "feature_scope": "Full baseline",
        "lib": "sklearn",
        "note": "HistGradientBoosting full baseline on the same Open-Meteo feature family as the XGB full baseline.",
    },
    "xgb_pm_only": {
        "display_name": "XGB PM-only",
        "feature_scope": "PM2.5-only",
        "lib": "xgboost",
        "note": "PM-history-only gradient boosting baseline without weather features.",
    },
    "hgb_pm_only": {
        "display_name": "HGB PM-only",
        "feature_scope": "PM2.5-only",
        "lib": "sklearn",
        "note": "PM-history-only histogram gradient boosting baseline without weather features.",
    },
    "linear_ar": {
        "display_name": "Linear AR",
        "feature_scope": "Linear AR subset",
        "lib": "sklearn",
        "note": "Linear autoregressive baseline over a compact PM2.5 lag and rolling-stat subset.",
    },
    "sarima_24h": {
        "display_name": "SARIMA(24h)",
        "feature_scope": "PM2.5 series only",
        "lib": "statsmodels",
        "note": "Corrected multi-step SARIMA evaluation. Forecasts h steps ahead from the issuance-time PM2.5 series only.",
    },
}


def train_valid_split(df):
    train = df[df["DATE"] < SPLIT_DATE].copy()
    valid = df[df["DATE"] >= SPLIT_DATE].copy()
    return train, valid


def feature_columns_for_model(df, model_key: str) -> list[str]:
    if model_key in {"xgb_full", "hgb_full"}:
        return full_feature_columns(df)
    if model_key in {"xgb_pm_only", "hgb_pm_only"}:
        return pm_only_columns(df)
    if model_key == "linear_ar":
        return linear_ar_columns(df)
    if model_key == "sarima_24h":
        return ["pm25"]
    raise ValueError(f"unknown model key: {model_key}")


def build_estimator(model_key: str):
    if model_key == "xgb_full":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "estimator",
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
                ),
            ]
        )
    if model_key == "hgb_full":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "estimator",
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
                ),
            ]
        )
    if model_key == "xgb_pm_only":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "estimator",
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
                ),
            ]
        )
    if model_key == "hgb_pm_only":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "estimator",
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
                ),
            ]
        )
    if model_key == "linear_ar":
        return LinearRegression()
    if model_key == "sarima_24h":
        return None
    raise ValueError(f"unknown model key: {model_key}")


def train_supervised_artifact(df, model_key: str) -> dict:
    feature_names = feature_columns_for_model(df, model_key)
    train, valid = train_valid_split(df)
    train = train.dropna(subset=feature_names + ["target_pm25"]).copy()
    valid = valid.dropna(subset=feature_names + ["target_pm25"]).copy()

    x_train = train[feature_names].replace([np.inf, -np.inf], np.nan)
    y_train = train["target_pm25"].astype(float).to_numpy()
    x_valid = valid[feature_names].replace([np.inf, -np.inf], np.nan)
    y_valid = valid["target_pm25"].astype(float).to_numpy()

    estimator = build_estimator(model_key)
    estimator.fit(x_train, y_train)
    pred = estimator.predict(x_valid)
    fit_metrics = metrics(y_valid, pred)

    return {
        "model": estimator,
        "feature_names": feature_names,
        "metrics": fit_metrics,
        "n_train": int(len(train)),
        "n_valid": int(len(valid)),
        "train_dates": (train["DATE"].min(), train["DATE"].max()),
        "valid_dates": (valid["DATE"].min(), valid["DATE"].max()),
    }


def train_sarima_artifact(df, horizon: int) -> dict:
    train, valid = train_valid_split(df)
    train = train.dropna(subset=["pm25"]).copy().sort_values("DATE")
    valid = valid.dropna(subset=["pm25", "target_pm25"]).copy().sort_values("DATE")
    series_train = train["pm25"].astype(float).reset_index(drop=True)

    fitted = SARIMAX(
        series_train,
        order=(2, 0, 0),
        seasonal_order=(1, 0, 0, 24),
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False)

    rolling_model = copy.deepcopy(fitted)
    preds = []
    for pm_now in valid["pm25"].astype(float).to_numpy():
        forecast = rolling_model.forecast(steps=horizon)
        preds.append(float(forecast.iloc[-1]))
        rolling_model = rolling_model.extend([pm_now])

    fit_metrics = metrics(valid["target_pm25"].astype(float).to_numpy(), np.asarray(preds, dtype=float))
    return {
        "model": fitted,
        "feature_names": ["pm25"],
        "metrics": fit_metrics,
        "n_train": int(len(train)),
        "n_valid": int(len(valid)),
        "train_dates": (train["DATE"].min(), train["DATE"].max()),
        "valid_dates": (valid["DATE"].min(), valid["DATE"].max()),
    }


def build_metadata(df, artifact_data: dict, horizon: int, model_key: str, export_note: str) -> dict:
    dataset_path = DATA_ROOT / f"hanoi_pm25_open_meteo_forecast_h{horizon}_2015_2025.csv"
    dataset_start = df["DATE"].min()
    dataset_end = df["DATE"].max()
    model_spec = MODEL_SPECS[model_key]

    library_version = {
        "xgboost": xgboost.__version__,
        "sklearn": sklearn.__version__,
        "statsmodels": statsmodels.__version__,
    }[model_spec["lib"]]

    return {
        "lib": {
            "name": model_spec["lib"],
            "version": library_version,
        },
        "dataset": {
            "path": str(dataset_path),
            "split_rule": "DATE < 2024-01-01 train, DATE >= 2024-01-01 holdout",
            "train_size": artifact_data["n_train"],
            "holdout_size": artifact_data["n_valid"],
            "target_column": "target_pm25",
            "time_column": "DATE",
            "target_time_column": "target_time",
            "model_ready_filter": True,
        },
        "time_cover": {
            "dataset_start": dataset_start.isoformat(),
            "dataset_end": dataset_end.isoformat(),
            "train_start": artifact_data["train_dates"][0].isoformat(),
            "train_end": artifact_data["train_dates"][1].isoformat(),
            "holdout_start": artifact_data["valid_dates"][0].isoformat(),
            "holdout_end": artifact_data["valid_dates"][1].isoformat(),
        },
        "forecast_horizon": f"T+{horizon}h",
        "note": export_note or model_spec["note"],
        "add": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "artifact_schema": "standardized_holdout_model_v1",
            "model_key": model_key,
            "display_name": model_spec["display_name"],
            "feature_scope": model_spec["feature_scope"],
            "holdout_label": "post-2024 holdout",
            "training_script": "scripts/export_standardized_model_artifact.py",
            "validation_script": "scripts/validate_standardized_model_artifact.py",
            "evaluator_script": "scripts/evaluate_horizon_standardized.py",
            "feature_names_ordered": True,
            "feature_imputation": "median imputer inside pipeline" if model_key != "linear_ar" and model_key != "sarima_24h" else "none",
            "training_parameters": str(artifact_data["model"].get_params()) if model_key != "sarima_24h" else {
                "order": [2, 0, 0],
                "seasonal_order": [1, 0, 0, 24],
                "trend": "c",
                "enforce_stationarity": False,
                "enforce_invertibility": False,
            },
        },
    }


def export_artifact(horizon: int, model_key: str, output_dir: Path, export_note: str) -> Path:
    df = load_horizon_frame(horizon)
    artifact_data = train_sarima_artifact(df, horizon) if model_key == "sarima_24h" else train_supervised_artifact(df, model_key)

    payload = {
        "model": artifact_data["model"],
        "n_features": len(artifact_data["feature_names"]),
        "feature_names": artifact_data["feature_names"],
        "metrics": artifact_data["metrics"],
        "metadata": build_metadata(df, artifact_data, horizon, model_key, export_note),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"hanoi_pm25_t{horizon:02d}h_{model_key}.pkl"
    with out_path.open("wb") as fh:
        pickle.dump(payload, fh)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, required=True)
    parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        choices=sorted(MODEL_SPECS.keys()),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    for model_key in args.models:
        print(export_artifact(args.horizon, model_key, args.output_dir, args.note))


if __name__ == "__main__":
    main()
