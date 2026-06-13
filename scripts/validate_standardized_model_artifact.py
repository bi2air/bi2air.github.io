#!/usr/bin/env python3
"""Validate an exported standardized PM2.5 forecasting artifact on its holdout block."""

import argparse
import copy
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_horizon_standardized import SPLIT_DATE, metrics


def load_payload(path: Path) -> dict:
    with path.open("rb") as fh:
        return pickle.load(fh)


def validate_supervised(payload: dict, df: pd.DataFrame) -> dict:
    feature_names = payload["feature_names"]
    holdout = df[df["DATE"] >= SPLIT_DATE].copy()
    holdout = holdout.dropna(subset=feature_names + ["target_pm25"]).copy()
    x_holdout = holdout[feature_names].replace([np.inf, -np.inf], np.nan)
    y_holdout = holdout["target_pm25"].astype(float).to_numpy()
    pred = payload["model"].predict(x_holdout)
    out = metrics(y_holdout, pred)
    out["holdout_size"] = int(len(holdout))
    return out


def validate_sarima(payload: dict, df: pd.DataFrame, horizon: int) -> dict:
    holdout = df[df["DATE"] >= SPLIT_DATE].dropna(subset=["pm25", "target_pm25"]).copy().sort_values("DATE")
    model = copy.deepcopy(payload["model"])
    preds = []
    for pm_now in holdout["pm25"].astype(float).to_numpy():
        forecast = model.forecast(steps=horizon)
        preds.append(float(forecast.iloc[-1]))
        model = model.extend([pm_now])

    out = metrics(holdout["target_pm25"].astype(float).to_numpy(), np.asarray(preds, dtype=float))
    out["holdout_size"] = int(len(holdout))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    args = parser.parse_args()

    payload = load_payload(args.artifact)
    metadata = payload["metadata"]
    dataset_path = Path(metadata["dataset"]["path"])
    horizon_text = metadata["forecast_horizon"]
    horizon = int(horizon_text.replace("T+", "").replace("h", ""))

    df = pd.read_csv(dataset_path, parse_dates=["DATE", "target_time"], low_memory=False)
    df = df[df["model_ready"]].copy()

    if metadata["add"]["model_key"] == "sarima_24h":
        out = validate_sarima(payload, df, horizon)
    else:
        out = validate_supervised(payload, df)

    print(
        {
            "artifact": str(args.artifact),
            "forecast_horizon": horizon_text,
            "model_key": metadata["add"]["model_key"],
            "revalidated_metrics": out,
            "saved_metrics": payload["metrics"],
        }
    )


if __name__ == "__main__":
    main()
