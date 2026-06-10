#!/usr/bin/env python3
"""Analyze overlap and QC for DC1100, DC1700, and AirVisual."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median

FMT = "%Y-%m-%d %H:%M:%S"
SVG_NS = "http://www.w3.org/2000/svg"
SUSPECT_R_THRESHOLD = 0.2
PAIR_LABELS = [
    ("r_dc1100_dc1700", "DC1100 vs DC1700"),
    ("r_dc1100_airvisual", "DC1100 vs AirVisual"),
    ("r_dc1700_airvisual", "DC1700 vs AirVisual"),
]


def floor_bin(dt: datetime, minutes: int) -> datetime:
    minute = (dt.minute // minutes) * minutes
    return dt.replace(minute=minute, second=0, microsecond=0)


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    if denx == 0 or deny == 0:
        return float("nan")
    return num / (denx * deny)


def mean_abs_error(xs: list[float], ys: list[float]) -> float:
    return sum(abs(x - y) for x, y in zip(xs, ys)) / len(xs) if xs else float("nan")


def mean_bias(xs: list[float], ys: list[float]) -> float:
    return sum(x - y for x, y in zip(xs, ys)) / len(xs) if xs else float("nan")


def sample_points(points: list[tuple[float, float]], limit: int = 5000) -> list[tuple[float, float]]:
    if len(points) <= limit:
        return points
    step = len(points) / limit
    out = []
    idx = 0.0
    while int(idx) < len(points) and len(out) < limit:
        out.append(points[int(idx)])
        idx += step
    return out


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def quantile(values: list[float], p: float) -> float:
    vals = sorted(v for v in values if not math.isnan(v))
    if not vals:
        return float("nan")
    idx = min(len(vals) - 1, max(0, int(p * (len(vals) - 1))))
    return vals[idx]


def load_binned(root: Path, minutes: int) -> tuple[dict[str, dict[datetime, float]], dict[str, tuple[datetime, datetime, int]]]:
    specs = {
        "dylos.csv": "Dylos DC1100 Pro",
        "dc1700.csv": "Dylos DC1700",
        "airvisual.csv": "IQAir AirVisual",
    }
    raw_bins: dict[str, dict[datetime, list[float]]] = defaultdict(lambda: defaultdict(list))
    coverage = {}

    for filename, label in specs.items():
        start = end = None
        count = 0
        with (root / filename).open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                ts = datetime.strptime(row["time"], FMT)
                bucket = floor_bin(ts, minutes)
                if start is None or ts < start:
                    start = ts
                if end is None or ts > end:
                    end = ts
                count += 1
                if filename == "dylos.csv":
                    raw_bins["dc1100_simple"][bucket].append((float(row["fine"]) - float(row["large"])) / 100.0)
                    raw_bins["dc1100_fit"][bucket].append(float(row["pm2_5_f"]))
                elif filename == "dc1700.csv":
                    raw_bins["dc1700_simple"][bucket].append((float(row["small"]) - float(row["large"])) / 100.0)
                elif filename == "airvisual.csv":
                    raw_bins["airvisual_pm25"][bucket].append(float(row["pm25"]))
        coverage[label] = (start, end, count)

    binned = {key: {bucket: median(values) for bucket, values in series.items()} for key, series in raw_bins.items()}
    return binned, coverage


def build_common_rows(binned: dict[str, dict[datetime, float]]) -> list[tuple[datetime, float, float, float, float]]:
    common_bins = sorted(set(binned["dc1100_fit"]) & set(binned["dc1700_simple"]) & set(binned["airvisual_pm25"]))
    return [
        (
            bucket,
            binned["dc1100_simple"].get(bucket, float("nan")),
            binned["dc1100_fit"][bucket],
            binned["dc1700_simple"][bucket],
            binned["airvisual_pm25"][bucket],
        )
        for bucket in common_bins
    ]


def write_common_csv(path: Path, common_rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_bin", "dc1100_simple", "dc1100_fit", "dc1700_simple", "airvisual_pm25"])
        for row in common_rows:
            writer.writerow([row[0].strftime(FMT), *row[1:]])


def overall_corr(common_rows) -> dict[str, float]:
    dc1100_fit = [row[2] for row in common_rows]
    dc1700_simple = [row[3] for row in common_rows]
    airvisual_pm25 = [row[4] for row in common_rows]
    return {
        "DC1100 fit vs DC1700 proxy": pearson(dc1100_fit, dc1700_simple),
        "DC1100 fit vs AirVisual": pearson(dc1100_fit, airvisual_pm25),
        "DC1700 proxy vs AirVisual": pearson(dc1700_simple, airvisual_pm25),
    }


def monthly_metrics(common_rows):
    groups = defaultdict(list)
    for row in common_rows:
        groups[row[0].strftime("%Y-%m")].append(row)
    out = []
    for month in sorted(groups):
        rows = groups[month]
        dc1100 = [r[2] for r in rows]
        dc1700 = [r[3] for r in rows]
        air = [r[4] for r in rows]
        out.append({
            "month": month,
            "bins": len(rows),
            "r_dc1100_dc1700": pearson(dc1100, dc1700),
            "r_dc1100_airvisual": pearson(dc1100, air),
            "r_dc1700_airvisual": pearson(dc1700, air),
            "mae_dc1100_airvisual": mean_abs_error(dc1100, air),
            "bias_dc1100_airvisual": mean_bias(dc1100, air),
            "mae_dc1700_airvisual": mean_abs_error(dc1700, air),
            "bias_dc1700_airvisual": mean_bias(dc1700, air),
        })
    return out


def lag_scan(common_rows, base_key: int, other_key: int, label: str):
    values_base = [r[base_key] for r in common_rows]
    values_other = [r[other_key] for r in common_rows]
    out = []
    for lag in range(-8, 9):
        if lag < 0:
            xs = values_base[-lag:]
            ys = values_other[: len(values_other) + lag]
        elif lag > 0:
            xs = values_base[:-lag]
            ys = values_other[lag:]
        else:
            xs = values_base
            ys = values_other
        out.append({"pair": label, "lag_bins": lag, "lag_minutes": lag * 15, "r": pearson(xs, ys), "n": len(xs)})
    return out


def regime_metrics(common_rows):
    air = [r[4] for r in common_rows]
    q1 = quantile(air, 1 / 3)
    q2 = quantile(air, 2 / 3)
    regimes = [("low", lambda x: x <= q1), ("mid", lambda x: q1 < x <= q2), ("high", lambda x: x > q2)]
    out = []
    for name, pred in regimes:
        rows = [r for r in common_rows if pred(r[4])]
        dc1100 = [r[2] for r in rows]
        dc1700 = [r[3] for r in rows]
        airv = [r[4] for r in rows]
        out.append({
            "regime": name,
            "bins": len(rows),
            "airvisual_min": min(airv) if airv else float("nan"),
            "airvisual_max": max(airv) if airv else float("nan"),
            "r_dc1100_airvisual": pearson(dc1100, airv),
            "r_dc1700_airvisual": pearson(dc1700, airv),
            "r_dc1100_dc1700": pearson(dc1100, dc1700),
        })
    return out


def daily_qc_metrics(hourly_rows):
    groups = defaultdict(list)
    for row in hourly_rows:
        groups[row[0].strftime("%Y-%m-%d")].append(row)
    out = []
    for day in sorted(groups):
        rows = groups[day]
        if len(rows) < 18:
            continue
        dc1100 = [r[2] for r in rows]
        dc1700 = [r[3] for r in rows]
        air = [r[4] for r in rows]
        r12 = pearson(dc1100, dc1700)
        r13 = pearson(dc1100, air)
        r23 = pearson(dc1700, air)
        out.append({
            "day": day,
            "bins": len(rows),
            "r_dc1100_dc1700": r12,
            "r_dc1100_airvisual": r13,
            "r_dc1700_airvisual": r23,
            "min_r": min(v for v in [r12, r13, r23] if not math.isnan(v)),
        })
    return out


def hour_of_day_metrics(common_rows):
    groups = defaultdict(list)
    for row in common_rows:
        groups[row[0].hour].append(row)
    out = []
    for hour in range(24):
        rows = groups[hour]
        dc1100 = [r[2] for r in rows]
        dc1700 = [r[3] for r in rows]
        air = [r[4] for r in rows]
        r12 = pearson(dc1100, dc1700)
        r13 = pearson(dc1100, air)
        r23 = pearson(dc1700, air)
        min_r = min(v for v in [r12, r13, r23] if not math.isnan(v))
        out.append({
            "hour": hour,
            "bins": len(rows),
            "r_dc1100_dc1700": r12,
            "r_dc1100_airvisual": r13,
            "r_dc1700_airvisual": r23,
            "mae_dc1100_airvisual": mean_abs_error(dc1100, air),
            "mae_dc1700_airvisual": mean_abs_error(dc1700, air),
            "bias_dc1100_airvisual": mean_bias(dc1100, air),
            "bias_dc1700_airvisual": mean_bias(dc1700, air),
            "min_r": min_r,
            "status": "suspect" if min_r < SUSPECT_R_THRESHOLD else "keep",
        })
    return out


def flag_bad_days(daily_rows):
    thresholds = {key: quantile([row[key] for row in daily_rows], 0.05) for key, _ in PAIR_LABELS}
    enriched = []
    flagged = []
    for row in daily_rows:
        low_pairs = [key for key, _ in PAIR_LABELS if row[key] <= thresholds[key]]
        item = dict(row)
        item["low_pair_count"] = len(low_pairs)
        item["low_pairs"] = ";".join(low_pairs)
        item["flagged"] = len(low_pairs) >= 2
        item["abnormal_low_r"] = item["min_r"] < SUSPECT_R_THRESHOLD
        if item["flagged"]:
            flagged.append(item["day"])
        enriched.append(item)
    return thresholds, enriched, set(flagged)


def filtered_rows(common_rows, flagged_days):
    return [row for row in common_rows if row[0].strftime("%Y-%m-%d") not in flagged_days]


def build_labeled_rows(common_rows, daily_rows: list[dict], hour_rows: list[dict]):
    daily_map = {row["day"]: row for row in daily_rows}
    hour_map = {row["hour"]: row for row in hour_rows}
    labeled = []
    for row in common_rows:
        day_key = row[0].strftime("%Y-%m-%d")
        day_info = daily_map.get(day_key)
        hour_info = hour_map[row[0].hour]
        day_flagged = bool(day_info and day_info["flagged"])
        day_abnormal = bool(day_info and day_info["abnormal_low_r"])
        hour_suspect = hour_info["status"] == "suspect"
        if day_flagged:
            qc_status = "drop_day_flagged"
        elif day_abnormal or hour_suspect:
            qc_status = "suspect"
        else:
            qc_status = "keep"
        labeled.append({
            "time_bin": row[0].strftime(FMT),
            "date": day_key,
            "hour_of_day": row[0].hour,
            "dc1100_simple": row[1],
            "dc1100_fit": row[2],
            "dc1700_simple": row[3],
            "airvisual_pm25": row[4],
            "day_bins": day_info["bins"] if day_info else "",
            "day_r_dc1100_dc1700": day_info["r_dc1100_dc1700"] if day_info else "",
            "day_r_dc1100_airvisual": day_info["r_dc1100_airvisual"] if day_info else "",
            "day_r_dc1700_airvisual": day_info["r_dc1700_airvisual"] if day_info else "",
            "day_low_pair_count": day_info["low_pair_count"] if day_info else "",
            "day_low_pairs": day_info["low_pairs"] if day_info else "",
            "day_flagged": int(day_flagged),
            "day_abnormal_low_r": int(day_abnormal),
            "hour_r_dc1100_dc1700": hour_info["r_dc1100_dc1700"],
            "hour_r_dc1100_airvisual": hour_info["r_dc1100_airvisual"],
            "hour_r_dc1700_airvisual": hour_info["r_dc1700_airvisual"],
            "hour_status": hour_info["status"],
            "qc_status": qc_status,
        })
    return labeled


def write_metrics_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def value_color(v: float) -> str:
    if math.isnan(v):
        return "#eeeeee"
    v = max(-1.0, min(1.0, v))
    if v >= 0:
        red = int(255 - 70 * v)
        green = int(245 - 20 * v)
        blue = int(255 - 160 * v)
    else:
        red = int(255 - 120 * (-v))
        green = int(245 - 180 * (-v))
        blue = int(255 - 60 * (-v))
    return f"#{red:02x}{green:02x}{blue:02x}"


def write_coverage_svg(path: Path, coverage) -> None:
    labels = list(coverage.keys())
    starts = [coverage[label][0] for label in labels]
    ends = [coverage[label][1] for label in labels]
    min_t = min(starts)
    max_t = max(ends)
    total = (max_t - min_t).total_seconds() or 1
    width, height = 1000, 220
    left, right, top, row_h = 180, 40, 40, 48

    def x_pos(ts: datetime) -> float:
        return left + ((ts - min_t).total_seconds() / total) * (width - left - right)

    lines = [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;font-size:14px} .title{font-size:18px;font-weight:bold}</style>',
        f'<text x="{left}" y="24" class="title">Mid-Tier Sensor Time Coverage</text>',
    ]
    for idx, label in enumerate(labels):
        y = top + idx * row_h
        xs = x_pos(coverage[label][0])
        xe = x_pos(coverage[label][1])
        lines.append(f'<text x="10" y="{y+5}">{escape(label)}</text>')
        lines.append(f'<line x1="{xs:.1f}" y1="{y}" x2="{xe:.1f}" y2="{y}" stroke="#2b6cb0" stroke-width="8" stroke-linecap="round" />')
        lines.append(f'<circle cx="{xs:.1f}" cy="{y}" r="4" fill="#2b6cb0" />')
        lines.append(f'<circle cx="{xe:.1f}" cy="{y}" r="4" fill="#2b6cb0" />')
    lines.append(f'<text x="{left}" y="{height-12}">{min_t.strftime(FMT)}</text>')
    lines.append(f'<text x="{width-220}" y="{height-12}">{max_t.strftime(FMT)}</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def panel_svg(xvals, yvals, xlab, ylab, title, r, x0, y0, w, h):
    margin = 42
    xmin, xmax = min(xvals), max(xvals)
    ymin, ymax = min(yvals), max(yvals)
    if xmax == xmin:
        xmax += 1
    if ymax == ymin:
        ymax += 1

    def sx(x):
        return x0 + margin + (x - xmin) / (xmax - xmin) * (w - 2 * margin)

    def sy(y):
        return y0 + h - margin - (y - ymin) / (ymax - ymin) * (h - 2 * margin)

    points = sample_points(list(zip(xvals, yvals)))
    parts = [
        f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="white" stroke="#cccccc" />',
        f'<text x="{x0 + 10}" y="{y0 + 22}" font-size="16" font-weight="bold">{escape(title)}</text>',
        f'<text x="{x0 + 10}" y="{y0 + 40}">r = {r:.4f}</text>',
    ]
    for x, y in points:
        parts.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="1.8" fill="#1f4e79" fill-opacity="0.22" />')
    parts.append(f'<text x="{x0 + w/2:.1f}" y="{y0 + h - 8}" text-anchor="middle">{escape(xlab)}</text>')
    parts.append(f'<text x="{x0 + 12}" y="{y0 + h/2:.1f}" transform="rotate(-90 {x0 + 12},{y0 + h/2:.1f})" text-anchor="middle">{escape(ylab)}</text>')
    return parts


def write_correlation_svg(path: Path, common_rows, corr, title="Exploratory Mid-Tier Pairwise Correlation (15-minute bins)") -> None:
    dc1100_fit = [row[2] for row in common_rows]
    dc1700_simple = [row[3] for row in common_rows]
    airvisual_pm25 = [row[4] for row in common_rows]
    width, height = 1200, 420
    panel_w, panel_h = 360, 320
    parts = [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;font-size:14px}</style>',
        f'<text x="20" y="26" font-size="20" font-weight="bold">{escape(title)}</text>',
    ]
    parts += panel_svg(dc1100_fit, dc1700_simple, "DC1100 PM2.5 fit", "DC1700 PM2.5 proxy", "DC1100 vs DC1700", corr["DC1100 fit vs DC1700 proxy"], 20, 60, panel_w, panel_h)
    parts += panel_svg(dc1100_fit, airvisual_pm25, "DC1100 PM2.5 fit", "AirVisual PM2.5", "DC1100 vs AirVisual", corr["DC1100 fit vs AirVisual"], 410, 60, panel_w, panel_h)
    parts += panel_svg(dc1700_simple, airvisual_pm25, "DC1700 PM2.5 proxy", "AirVisual PM2.5", "DC1700 vs AirVisual", corr["DC1700 proxy vs AirVisual"], 800, 60, panel_w, panel_h)
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_monthly_heatmap_svg(path: Path, monthly: list[dict]) -> None:
    cols = ["r_dc1100_dc1700", "r_dc1100_airvisual", "r_dc1700_airvisual"]
    labels = ["DC1100 vs DC1700", "DC1100 vs AirVisual", "DC1700 vs AirVisual"]
    cell_w, cell_h = 120, 24
    left, top = 140, 60
    width = left + cell_w * len(cols) + 20
    height = top + cell_h * len(monthly) + 40
    parts = [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;font-size:13px} .title{font-size:18px;font-weight:bold}</style>',
        '<text x="20" y="24" class="title">Monthly Correlation Stability</text>',
    ]
    for j, label in enumerate(labels):
        x = left + j * cell_w + cell_w / 2
        parts.append(f'<text x="{x:.1f}" y="48" text-anchor="middle">{escape(label)}</text>')
    for i, row in enumerate(monthly):
        y = top + i * cell_h
        parts.append(f'<text x="20" y="{y+16}">{row["month"]}</text>')
        for j, col in enumerate(cols):
            x = left + j * cell_w
            value = row[col]
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{value_color(value)}" stroke="#ffffff" />')
            parts.append(f'<text x="{x + cell_w/2:.1f}" y="{y+16}" text-anchor="middle">{value:.3f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_lag_svg(path: Path, lag_rows: list[dict]) -> None:
    pairs = ["DC1100 vs DC1700", "DC1100 vs AirVisual", "DC1700 vs AirVisual"]
    grouped = {pair: [r for r in lag_rows if r["pair"] == pair] for pair in pairs}
    width, height = 1200, 360
    panel_w, panel_h = 360, 240
    parts = [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;font-size:13px}</style>',
        '<text x="20" y="24" font-size="20" font-weight="bold">Lag Scan Around 15-minute Bins</text>',
    ]
    for idx, pair in enumerate(pairs):
        rows = grouped[pair]
        x0 = 20 + idx * 390
        y0 = 60
        parts.append(f'<rect x="{x0}" y="{y0}" width="{panel_w}" height="{panel_h}" fill="white" stroke="#cccccc" />')
        parts.append(f'<text x="{x0+10}" y="{y0+22}" font-size="16" font-weight="bold">{escape(pair)}</text>')
        lags = [r["lag_minutes"] for r in rows]
        vals = [r["r"] for r in rows]
        xmin, xmax = min(lags), max(lags)
        ymin, ymax = min(vals), max(vals)
        if ymax == ymin:
            ymax += 0.01
        margin = 36

        def sx(x):
            return x0 + margin + (x - xmin) / (xmax - xmin) * (panel_w - 2 * margin)

        def sy(y):
            return y0 + panel_h - margin - (y - ymin) / (ymax - ymin) * (panel_h - 2 * margin)

        poly = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(lags, vals))
        parts.append(f'<polyline fill="none" stroke="#1f4e79" stroke-width="2" points="{poly}" />')
        best = max(rows, key=lambda r: r["r"])
        parts.append(f'<circle cx="{sx(best["lag_minutes"]):.1f}" cy="{sy(best["r"]):.1f}" r="4" fill="#c53030" />')
        parts.append(f'<text x="{x0+10}" y="{y0+42}">best lag = {best["lag_minutes"]} min, r = {best["r"]:.4f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_daily_qc_svg(path: Path, daily_rows: list[dict], thresholds: dict[str, float]) -> None:
    cols = [key for key, _ in PAIR_LABELS]
    labels = [label for _, label in PAIR_LABELS]
    cell_w, cell_h = 120, 10
    left, top = 170, 60
    width = left + cell_w * len(cols) + 20
    height = top + cell_h * len(daily_rows) + 40
    parts = [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;font-size:12px} .title{font-size:18px;font-weight:bold}</style>',
        '<text x="20" y="24" class="title">Daily QC Correlation Grid</text>',
        '<text x="20" y="42">Rows flagged when at least 2 pairwise daily correlations fall below their 5th-percentile thresholds.</text>',
    ]
    for j, label in enumerate(labels):
        x = left + j * cell_w + cell_w / 2
        parts.append(f'<text x="{x:.1f}" y="52" text-anchor="middle">{escape(label)}</text>')
    tick_every = max(1, len(daily_rows) // 18)
    for i, row in enumerate(daily_rows):
        y = top + i * cell_h
        if i % tick_every == 0:
            label = row["day"] + (" *" if row["flagged"] else "")
            parts.append(f'<text x="20" y="{y+8}">{label}</text>')
        for j, col in enumerate(cols):
            x = left + j * cell_w
            value = float(row[col])
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{value_color(value)}" stroke="#ffffff" />')
        if row["flagged"]:
            parts.append(f'<rect x="{left-2}" y="{y}" width="{cell_w * len(cols) + 4}" height="{cell_h}" fill="none" stroke="#c53030" stroke-width="1.5" />')
    legend_y = height - 14
    parts.append(f'<text x="20" y="{legend_y}">Thresholds: DC1100/DC1700 {thresholds["r_dc1100_dc1700"]:.3f}, DC1100/AirVisual {thresholds["r_dc1100_airvisual"]:.3f}, DC1700/AirVisual {thresholds["r_dc1700_airvisual"]:.3f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_hourly_stability_svg(path: Path, hour_rows: list[dict]) -> None:
    cols = [key for key, _ in PAIR_LABELS]
    labels = [label for _, label in PAIR_LABELS]
    cell_w, cell_h = 120, 20
    left, top = 120, 60
    width = left + cell_w * len(cols) + 20
    height = top + cell_h * len(hour_rows) + 60
    parts = [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:Arial,sans-serif;font-size:12px} .title{font-size:18px;font-weight:bold}</style>',
        '<text x="20" y="24" class="title">Hour-of-Day Stability</text>',
        f'<text x="20" y="42">Hours are labeled suspect only when any pair drops below r = {SUSPECT_R_THRESHOLD:.1f} across the full campaign.</text>',
    ]
    for j, label in enumerate(labels):
        x = left + j * cell_w + cell_w / 2
        parts.append(f'<text x="{x:.1f}" y="52" text-anchor="middle">{escape(label)}</text>')
    for i, row in enumerate(hour_rows):
        y = top + i * cell_h
        parts.append(f'<text x="20" y="{y+14}">{row["hour"]:02d}:00</text>')
        for j, col in enumerate(cols):
            x = left + j * cell_w
            value = row[col]
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{value_color(value)}" stroke="#ffffff" />')
            parts.append(f'<text x="{x + cell_w/2:.1f}" y="{y+14}" text-anchor="middle">{value:.3f}</text>')
        if row["status"] == "suspect":
            parts.append(f'<rect x="{left-2}" y="{y}" width="{cell_w * len(cols) + 4}" height="{cell_h}" fill="none" stroke="#c53030" stroke-width="1.5" />')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_summary(path: Path, coverage, common_rows, corr, monthly, lag_rows, regime_rows, thresholds, flagged_days, cleaned_corr, cleaned_rows, hour_rows, labeled_rows) -> None:
    common_start = common_rows[0][0]
    common_end = common_rows[-1][0]
    suspect_hours = [row["hour"] for row in hour_rows if row["status"] == "suspect"]
    suspect_rows = sum(1 for row in labeled_rows if row["qc_status"] == "suspect")
    keep_rows = sum(1 for row in labeled_rows if row["qc_status"] == "keep")
    dropped_rows = sum(1 for row in labeled_rows if row["qc_status"] == "drop_day_flagged")
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Mid-Tier Sensor Coverage and Correlation\n\n")
        handle.write("- Resampling bin: `15 minutes`\n")
        handle.write(f"- Common overlap window: `{common_start}` to `{common_end}`\n")
        handle.write(f"- Common aligned bins: `{len(common_rows)}`\n")
        handle.write(f"- Flagged low-agreement days: `{len(flagged_days)}`\n")
        hours_text = ", ".join(f"{hour:02d}:00" for hour in suspect_hours) if suspect_hours else "none"
        handle.write(f"- Hour-of-day suspect windows (r < {SUSPECT_R_THRESHOLD:.1f}): `{hours_text}`\n")
        handle.write(f"- Labeled rows: `keep={keep_rows}`, `suspect={suspect_rows}`, `drop_day_flagged={dropped_rows}`\n")
        handle.write(f"- Cleaned aligned bins after day-level trim: `{len(cleaned_rows)}`\n\n")
        handle.write("## Source coverage\n\n")
        for label, (start, end, rows) in coverage.items():
            handle.write(f"- `{label}`: `{start}` to `{end}` with `{rows}` raw rows\n")
        handle.write("\n## Pairwise Pearson correlation\n\n")
        handle.write("| Pair | Raw r | Cleaned r |\n| --- | ---: | ---: |\n")
        for pair, value in corr.items():
            handle.write(f"| {pair} | {value:.4f} | {cleaned_corr[pair]:.4f} |\n")
        handle.write("\n## Day-level QC thresholds\n\n")
        handle.write("| Pair | 5th-percentile daily r threshold |\n| --- | ---: |\n")
        handle.write(f"| DC1100 vs DC1700 | {thresholds['r_dc1100_dc1700']:.4f} |\n")
        handle.write(f"| DC1100 vs AirVisual | {thresholds['r_dc1100_airvisual']:.4f} |\n")
        handle.write(f"| DC1700 vs AirVisual | {thresholds['r_dc1700_airvisual']:.4f} |\n")
        handle.write("\n## Hour-of-day stability\n\n")
        handle.write("| Hour | Bins | DC1100 vs DC1700 | DC1100 vs AirVisual | DC1700 vs AirVisual | Status |\n")
        handle.write("| --- | ---: | ---: | ---: | ---: | --- |\n")
        for row in hour_rows:
            handle.write(f"| {row['hour']:02d}:00 | {row['bins']} | {row['r_dc1100_dc1700']:.4f} | {row['r_dc1100_airvisual']:.4f} | {row['r_dc1700_airvisual']:.4f} | {row['status']} |\n")
        handle.write("\n## Monthly stability\n\n")
        handle.write("| Month | Bins | DC1100 vs DC1700 | DC1100 vs AirVisual | DC1700 vs AirVisual | MAE DC1100-AirVisual | MAE DC1700-AirVisual |\n")
        handle.write("| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        for row in monthly:
            handle.write(f"| {row['month']} | {row['bins']} | {row['r_dc1100_dc1700']:.4f} | {row['r_dc1100_airvisual']:.4f} | {row['r_dc1700_airvisual']:.4f} | {row['mae_dc1100_airvisual']:.2f} | {row['mae_dc1700_airvisual']:.2f} |\n")
        handle.write("\n## Lag scan best offsets\n\n")
        handle.write("| Pair | Best lag (minutes) | r |\n| --- | ---: | ---: |\n")
        for pair in sorted(set(r["pair"] for r in lag_rows)):
            rows = [r for r in lag_rows if r["pair"] == pair]
            best = max(rows, key=lambda r: r["r"])
            handle.write(f"| {pair} | {best['lag_minutes']} | {best['r']:.4f} |\n")
        handle.write("\n## Concentration regimes by AirVisual PM2.5 tertiles\n\n")
        handle.write("| Regime | Bins | AirVisual min | AirVisual max | DC1100 vs AirVisual | DC1700 vs AirVisual | DC1100 vs DC1700 |\n")
        handle.write("| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        for row in regime_rows:
            handle.write(f"| {row['regime']} | {row['bins']} | {row['airvisual_min']:.1f} | {row['airvisual_max']:.1f} | {row['r_dc1100_airvisual']:.4f} | {row['r_dc1700_airvisual']:.4f} | {row['r_dc1100_dc1700']:.4f} |\n")
        handle.write("\n## Clean-data outputs\n\n")
        handle.write("- `mid_tier_15min_with_qc.csv`: full aligned dataset with day-level and hour-of-day QC labels\n")
        handle.write("- `mid_tier_15min_analysis_clean.csv`: rows retained for downstream analysis after dropping day-flagged periods only\n")
        handle.write("- `mid_tier_daily_qc.csv`: daily diagnostic table\n")
        handle.write("- `mid_tier_hour_of_day.csv`: hour-of-day stability table\n")


def main() -> int:
    src_root = Path("/home/abc/working/bioinfo/airdb/csv_output")
    out_root = Path("/home/abc/working/gitpage/tmp/mid_tier_correlation")
    asset_root = Path("/home/abc/working/gitpage/assets/images/research/collocation")
    out_root.mkdir(parents=True, exist_ok=True)
    asset_root.mkdir(parents=True, exist_ok=True)

    binned_15, coverage = load_binned(src_root, 15)
    common_rows = build_common_rows(binned_15)
    write_common_csv(out_root / "mid_tier_15min_common.csv", common_rows)
    corr = overall_corr(common_rows)
    monthly = monthly_metrics(common_rows)
    lag_rows = []
    lag_rows.extend(lag_scan(common_rows, 2, 3, "DC1100 vs DC1700"))
    lag_rows.extend(lag_scan(common_rows, 2, 4, "DC1100 vs AirVisual"))
    lag_rows.extend(lag_scan(common_rows, 3, 4, "DC1700 vs AirVisual"))
    regime_rows = regime_metrics(common_rows)
    hour_rows = hour_of_day_metrics(common_rows)

    binned_60, _ = load_binned(src_root, 60)
    hourly_rows = build_common_rows(binned_60)
    daily_rows = daily_qc_metrics(hourly_rows)
    thresholds, daily_enriched, flagged_days = flag_bad_days(daily_rows)
    cleaned_rows = filtered_rows(common_rows, flagged_days)
    cleaned_corr = overall_corr(cleaned_rows)
    labeled_rows = build_labeled_rows(common_rows, daily_enriched, hour_rows)

    write_common_csv(out_root / "mid_tier_15min_common_cleaned.csv", cleaned_rows)
    write_common_csv(out_root / "mid_tier_15min_analysis_clean.csv", cleaned_rows)
    write_metrics_csv(out_root / "mid_tier_monthly.csv", monthly)
    write_metrics_csv(out_root / "mid_tier_lag.csv", lag_rows)
    write_metrics_csv(out_root / "mid_tier_regimes.csv", regime_rows)
    write_metrics_csv(out_root / "mid_tier_daily_qc.csv", daily_enriched)
    write_metrics_csv(out_root / "mid_tier_hour_of_day.csv", hour_rows)
    write_metrics_csv(out_root / "mid_tier_15min_with_qc.csv", labeled_rows)
    write_summary(out_root / "summary.md", coverage, common_rows, corr, monthly, lag_rows, regime_rows, thresholds, flagged_days, cleaned_corr, cleaned_rows, hour_rows, labeled_rows)

    write_coverage_svg(asset_root / "mid_tier_coverage.svg", coverage)
    write_correlation_svg(asset_root / "mid_tier_correlation.svg", common_rows, corr)
    write_correlation_svg(asset_root / "mid_tier_correlation_cleaned.svg", cleaned_rows, cleaned_corr, title="Mid-Tier Pairwise Correlation After Day-Level QC Trim")
    write_monthly_heatmap_svg(asset_root / "mid_tier_monthly_heatmap.svg", monthly)
    write_lag_svg(asset_root / "mid_tier_lag.svg", lag_rows)
    write_daily_qc_svg(asset_root / "mid_tier_daily_qc.svg", daily_enriched, thresholds)
    write_hourly_stability_svg(asset_root / "mid_tier_hourly_stability.svg", hour_rows)

    suspect_hours = [row["hour"] for row in hour_rows if row["status"] == "suspect"]
    suspect_rows = sum(1 for row in labeled_rows if row["qc_status"] == "suspect")
    print("common_bins", len(common_rows))
    print("flagged_days", len(flagged_days))
    print("cleaned_bins", len(cleaned_rows))
    print("suspect_hours", ",".join(f"{hour:02d}" for hour in suspect_hours) if suspect_hours else "none")
    print("suspect_rows", suspect_rows)
    print("overall_corr")
    for key, value in corr.items():
        print(key, f"{value:.6f}")
    print("cleaned_corr")
    for key, value in cleaned_corr.items():
        print(key, f"{value:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
