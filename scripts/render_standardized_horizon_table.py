#!/usr/bin/env python3
"""Render a per-horizon markdown summary table from standardized run JSON files."""

import argparse
import json
from pathlib import Path


MODEL_META = {
    "xgb_full": {
        "display": "XGB full baseline",
        "estimator": "XGBRegressor",
        "feature_scope": "Full baseline",
    },
    "hgb_full": {
        "display": "HGB full baseline",
        "estimator": "HistGradientBoostingRegressor",
        "feature_scope": "Full baseline",
    },
    "xgb_pm_only": {
        "display": "XGB PM-only",
        "estimator": "XGBRegressor",
        "feature_scope": "PM2.5-only",
    },
    "hgb_pm_only": {
        "display": "HGB PM-only",
        "estimator": "HistGradientBoostingRegressor",
        "feature_scope": "PM2.5-only",
    },
    "linear_ar": {
        "display": "Linear AR",
        "estimator": "LinearRegression",
        "feature_scope": "Linear AR subset",
    },
    "sarima_24h": {
        "display": "SARIMA(24h)",
        "estimator": "SARIMAX(2,0,0)x(1,0,0,24)",
        "feature_scope": "PM2.5 series only",
    },
}

MODEL_ORDER = [
    "xgb_full",
    "hgb_full",
    "xgb_pm_only",
    "hgb_pm_only",
    "linear_ar",
    "sarima_24h",
]


def load_results(paths: list[Path]) -> dict:
    merged: dict = {"models": {}}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "horizon" not in merged:
            merged["horizon"] = payload["horizon"]
            merged["dataset"] = payload["dataset"]
            merged["split_rule"] = payload["split_rule"]
        else:
            if payload["horizon"] != merged["horizon"]:
                raise ValueError(f"mixed horizons in inputs: {path}")
            if payload["dataset"] != merged["dataset"]:
                raise ValueError(f"mixed datasets in inputs: {path}")
            if payload["split_rule"] != merged["split_rule"]:
                raise ValueError(f"mixed split rules in inputs: {path}")
        merged["models"].update(payload.get("models", {}))
    return merged


def format_feature_count(value) -> str:
    if value is None:
        return "series-only"
    return str(value)


def format_metric(value: float) -> str:
    return f"{value:.3f}"


def build_table(data: dict) -> str:
    horizon = data["horizon"]
    lines = [
        f"## T+{horizon}h Summary Table",
        "",
        f"**Dataset:** `{data['dataset']}`  ",
        f"**Holdout split:** `{data['split_rule']}`",
        "",
        "> Note: the current standardized framework uses a single post-2024 holdout block. This table reports holdout-set metrics, not a separate validation-plus-test protocol.",
        "",
        "| Method | Fitting Method | Feature Scope | Features | Train N | Holdout N | RMSE | MAE | R² |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for model_key in MODEL_ORDER:
        result = data["models"].get(model_key)
        if result is None:
            continue
        meta = MODEL_META[model_key]
        lines.append(
            "| "
            + " | ".join(
                [
                    meta["display"],
                    meta["estimator"],
                    meta["feature_scope"],
                    format_feature_count(result["n_features"]),
                    str(result["n_train"]),
                    str(result["n_valid"]),
                    format_metric(result["rmse"]),
                    format_metric(result["mae"]),
                    format_metric(result["r2"]),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    table = build_table(load_results(args.inputs))
    if args.out:
        args.out.write_text(table + "\n", encoding="utf-8")
        print(args.out)
    else:
        print(table)


if __name__ == "__main__":
    main()
