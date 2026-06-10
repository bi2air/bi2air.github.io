#!/usr/bin/env python3
"""Collect Hanoi public air-quality data from moitruongthudo.vn and CEM.

Stage 1 stores a raw-ish latest-24h snapshot grouped by source and station.
Stage 2 derives hourly PM2.5 and VN AQI records, preferring moitruongthudo.vn
and using CEM PM2.5 AQI as an estimated fallback where stations overlap.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


HANOI_TZ = timezone(timedelta(hours=7))
DEFAULT_DATA_ROOT = Path("data")
RAW_SOURCE_SLUG = "public-air-quality"
RAW_ROOT_REL = Path("external/raw/hanoi") / RAW_SOURCE_SLUG
PROCESSED_ROOT_REL = Path("external/processed/hanoi") / RAW_SOURCE_SLUG

MOIT_BASE = "https://moitruongthudo.vn"
MOIT_SITES_URL = f"{MOIT_BASE}/api/site"
MOIT_DAILYSTAT_URL = f"{MOIT_BASE}/public/dailystat"
MOIT_DAILYAQI_URL = f"{MOIT_BASE}/public/dailyaqi"

CEM_BASE = "https://envisoft.gov.vn/eos/services/call/json"
CEM_STATIONS_URL = f"{CEM_BASE}/get_stations"
CEM_QI_DETAIL_URL = f"{CEM_BASE}/qi_detail"

VN_AQI_PM25_BREAKPOINTS = (
    (0.0, 25.0, 0, 50),
    (25.0, 50.0, 50, 100),
    (50.0, 80.0, 100, 150),
    (80.0, 150.0, 150, 200),
    (150.0, 250.0, 200, 300),
    (250.0, 350.0, 300, 400),
    (350.0, 500.0, 400, 500),
)


@dataclass
class SourceHourlyRow:
    source_slug: str
    station_code: str
    station_name: str
    station_index: str
    observation_hour_local: str
    pm25_ugm3: str
    vn_aqi_pm25: str
    pm25_status: str
    vn_aqi_status: str
    pm25_method: str
    vn_aqi_method: str
    raw_sample_count: str
    raw_time_resolution_minutes: str
    backup_station_code: str
    snapshot_time_utc: str


@dataclass
class CanonicalHourlyRow:
    station_code: str
    station_name: str
    observation_hour_local: str
    pm25_ugm3: str
    vn_aqi_pm25: str
    pm25_source_used: str
    vn_aqi_source_used: str
    pm25_status: str
    vn_aqi_status: str
    pm25_method: str
    vn_aqi_method: str
    backup_station_code: str
    snapshot_time_utc: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("stage1", "stage2", "all"),
        default="all",
        help="run only stage1, only stage2 from an existing snapshot, or both",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help="project data root; raw and processed outputs are written under this directory",
    )
    parser.add_argument(
        "--stage1-input",
        type=Path,
        help="use an existing stage1 snapshot JSON for stage2",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds",
    )
    return parser.parse_args()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc_compact(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def parse_moit_timestamp(value: str) -> datetime | None:
    cleaned = (value or "").strip()
    if not cleaned:
        return None
    return datetime.strptime(cleaned, "%Y-%m-%d %H:%M").replace(tzinfo=HANOI_TZ)


def parse_cem_timestamp(value: str) -> datetime | None:
    cleaned = (value or "").strip()
    if not cleaned:
        return None
    return datetime.strptime(cleaned, "%d/%m/%Y %H:%M").replace(tzinfo=HANOI_TZ)


def normalize_hour_local(value: datetime) -> str:
    return value.astimezone(HANOI_TZ).strftime("%Y-%m-%d %H:00")


def make_request(
    url: str,
    *,
    timeout: float,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    form: dict[str, str] | None = None,
) -> Any:
    payload = None
    request_headers = dict(headers or {})
    if form is not None:
        payload = urllib.parse.urlencode(form).encode("utf-8")
        request_headers.setdefault("content-type", "application/x-www-form-urlencoded; charset=UTF-8")
        request_headers.setdefault("accept", "application/json, text/javascript, */*; q=0.01")
    request = urllib.request.Request(url, data=payload, headers=request_headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset))


def trim_series_last_24h(
    series: list[dict[str, Any]],
    *,
    parse_time,
    time_key: str = "time",
) -> list[dict[str, Any]]:
    dated = []
    for item in series:
        timestamp = parse_time(str(item.get(time_key, "")))
        if timestamp is None:
            continue
        dated.append((timestamp, item))
    if not dated:
        return []
    latest = max(timestamp for timestamp, _ in dated)
    cutoff = latest - timedelta(hours=24)
    trimmed = [item for timestamp, item in dated if timestamp > cutoff]
    trimmed.sort(key=lambda item: str(item.get(time_key, "")))
    return trimmed


def trim_cem_pm25_values(values: list[dict[str, str]]) -> list[dict[str, str]]:
    dated = []
    for item in values:
        if not item:
            continue
        value_str, time_str = next(iter(item.items()))
        timestamp = parse_cem_timestamp(time_str)
        if timestamp is None:
            continue
        dated.append((timestamp, {value_str: time_str}))
    if not dated:
        return []
    latest = max(timestamp for timestamp, _ in dated)
    cutoff = latest - timedelta(hours=24)
    trimmed = [item for timestamp, item in dated if timestamp > cutoff]
    trimmed.sort(key=lambda item: next(iter(item.values())))
    return trimmed


def stringify_number(value: float | int | None, *, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def to_float(value: Any) -> float | None:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def infer_resolution_minutes(points: list[dict[str, Any]], parse_time) -> int | None:
    timestamps = [parse_time(str(point.get("time", ""))) for point in points]
    timestamps = [value for value in timestamps if value is not None]
    if len(timestamps) < 2:
        return None
    deltas = []
    for earlier, later in zip(timestamps, timestamps[1:]):
        delta_minutes = int((later - earlier).total_seconds() // 60)
        if delta_minutes > 0:
            deltas.append(delta_minutes)
    if not deltas:
        return None
    counts: dict[int, int] = defaultdict(int)
    for delta in deltas:
        counts[delta] += 1
    return max(sorted(counts), key=lambda key: counts[key])


def invert_vn_aqi_pm25(aqi: float) -> float | None:
    if aqi < 0:
        return None
    clipped = min(aqi, 500.0)
    for bp_low, bp_high, idx_low, idx_high in VN_AQI_PM25_BREAKPOINTS:
        if clipped <= idx_high:
            if idx_high == idx_low:
                return bp_low
            ratio = (clipped - idx_low) / (idx_high - idx_low)
            return bp_low + ratio * (bp_high - bp_low)
    return VN_AQI_PM25_BREAKPOINTS[-1][1]


def fetch_moit_stage1(timeout: float) -> dict[str, Any]:
    sites = make_request(MOIT_SITES_URL, timeout=timeout)
    stations = []
    for site in sites:
        site_id = int(site["id"])
        raw_stat = make_request(f"{MOIT_DAILYSTAT_URL}/{site_id}", timeout=timeout)
        raw_aqi = make_request(f"{MOIT_DAILYAQI_URL}/{site_id}", timeout=timeout)
        pm25_stat = trim_series_last_24h(raw_stat.get("PM2.5", []), parse_time=parse_moit_timestamp)
        pm25_aqi = trim_series_last_24h(raw_aqi.get("PM2.5", []), parse_time=parse_moit_timestamp)
        stations.append(
            {
                "site_id": site_id,
                "site_code": site.get("code", ""),
                "site_name": site.get("name", ""),
                "site_type": site.get("type", ""),
                "current_overall_aqi": site.get("aqi"),
                "current_overall_aqi_text": site.get("aqiText", ""),
                "latest_site_aqi_date": site.get("aqi_time", ""),
                "endpoints": {
                    "site": MOIT_SITES_URL,
                    "dailystat": f"{MOIT_DAILYSTAT_URL}/{site_id}",
                    "dailyaqi": f"{MOIT_DAILYAQI_URL}/{site_id}",
                },
                "pm25_raw_last24h": pm25_stat,
                "pm25_vn_aqi_last24h": pm25_aqi,
            }
        )
    return {
        "source_slug": "moitruongthudo",
        "source_url": MOIT_BASE,
        "site_catalog_endpoint": MOIT_SITES_URL,
        "station_count": len(stations),
        "stations": stations,
    }


def is_hanoi_cem_station(station: dict[str, Any]) -> bool:
    name = str(station.get("station_name", ""))
    address = str(station.get("address", ""))
    return name.startswith("Hà Nội:") or "Hà Nội" in address


def fetch_cem_stage1(timeout: float) -> dict[str, Any]:
    stations_response = make_request(
        CEM_STATIONS_URL,
        timeout=timeout,
        method="POST",
        form={"is_qi": "true", "is_public": "true", "qi_type": "aqi"},
    )
    hanoi_stations = [station for station in stations_response.get("stations", []) if is_hanoi_cem_station(station)]
    stations = []
    for station in hanoi_stations:
        station_id = str(station["id"])
        detail = make_request(
            CEM_QI_DETAIL_URL,
            timeout=timeout,
            method="POST",
            form={"station_id": station_id},
        )
        pm25 = detail.get("res", {}).get("PM-2-5", {})
        stations.append(
            {
                "station_id": station_id,
                "station_name": station.get("station_name", ""),
                "address": station.get("address", ""),
                "latitude": station.get("latitude"),
                "longitude": station.get("longitude"),
                "station_qi": station.get("qi"),
                "station_qi_time": station.get("qi_time", ""),
                "endpoints": {
                    "get_stations": CEM_STATIONS_URL,
                    "qi_detail": CEM_QI_DETAIL_URL,
                },
                "pm25_vn_aqi_current": pm25.get("current"),
                "pm25_vn_aqi_last24h_raw": trim_cem_pm25_values(pm25.get("values", [])),
                "qi_value_current": detail.get("qi_value"),
                "qi_detail_time": detail.get("qi_time_2", ""),
            }
        )
    return {
        "source_slug": "cem",
        "source_url": "https://cem.gov.vn/",
        "station_count": len(stations),
        "stations": stations,
    }


def raw_root(data_root: Path) -> Path:
    return data_root / RAW_ROOT_REL


def processed_root(data_root: Path) -> Path:
    return data_root / PROCESSED_ROOT_REL


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_stage1(data_root: Path, timeout: float) -> tuple[dict[str, Any], Path]:
    snapshot_time = now_utc()
    payload = {
        "snapshot_time_utc": snapshot_time.isoformat(),
        "city": "hanoi",
        "sources": {
            "moitruongthudo": fetch_moit_stage1(timeout),
            "cem": fetch_cem_stage1(timeout),
        },
    }
    stage1_dir = raw_root(data_root) / "stage1"
    latest_path = stage1_dir / "latest.json"
    snapshot_path = stage1_dir / "snapshots" / f"{iso_utc_compact(snapshot_time)}.json"
    write_json(latest_path, payload)
    write_json(snapshot_path, payload)
    return payload, snapshot_path


def derive_moit_hourly_rows(snapshot_time_utc: str, source: dict[str, Any]) -> list[SourceHourlyRow]:
    rows: list[SourceHourlyRow] = []
    for station in source.get("stations", []):
        station_code = str(station.get("site_code") or f"moit-site-{station['site_id']}")
        pm25_points = station.get("pm25_raw_last24h", [])
        aqi_points = station.get("pm25_vn_aqi_last24h", [])
        resolution = infer_resolution_minutes(pm25_points, parse_moit_timestamp)
        grouped: dict[str, list[float]] = defaultdict(list)
        for point in pm25_points:
            timestamp = parse_moit_timestamp(str(point.get("time", "")))
            if timestamp is None:
                continue
            value = to_float(point.get("value"))
            if value is not None:
                grouped[normalize_hour_local(timestamp)].append(value)

        aqi_by_hour: dict[str, dict[str, Any]] = {}
        for point in aqi_points:
            timestamp = parse_moit_timestamp(str(point.get("time", "")))
            if timestamp is None:
                continue
            aqi_by_hour[normalize_hour_local(timestamp)] = point

        all_hours = sorted(set(grouped) | set(aqi_by_hour))
        for hour in all_hours:
            values = grouped.get(hour, [])
            pm25_value = sum(values) / len(values) if values else None
            aqi_point = aqi_by_hour.get(hour, {})
            aqi_value = to_float(aqi_point.get("value"))
            rows.append(
                SourceHourlyRow(
                    source_slug="moitruongthudo",
                    station_code=station_code,
                    station_name=str(station.get("site_name", "")),
                    station_index=str(station.get("site_id", "")),
                    observation_hour_local=hour,
                    pm25_ugm3=stringify_number(pm25_value, digits=2),
                    vn_aqi_pm25=stringify_number(aqi_value, digits=0),
                    pm25_status="observed" if pm25_value is not None else "missing",
                    vn_aqi_status="reported" if aqi_value is not None else "missing",
                    pm25_method="hourly_mean" if values else "",
                    vn_aqi_method="reported_hourly_pm25_aqi" if aqi_value is not None else "",
                    raw_sample_count=str(len(values)) if values else "0",
                    raw_time_resolution_minutes=str(resolution or ""),
                    backup_station_code=station_code if station.get("site_type") == "envisoft" else "",
                    snapshot_time_utc=snapshot_time_utc,
                )
            )
    return rows


def derive_cem_hourly_rows(snapshot_time_utc: str, source: dict[str, Any]) -> list[SourceHourlyRow]:
    rows: list[SourceHourlyRow] = []
    for station in source.get("stations", []):
        station_code = str(station.get("station_id", ""))
        for item in station.get("pm25_vn_aqi_last24h_raw", []):
            aqi_str, time_str = next(iter(item.items()))
            timestamp = parse_cem_timestamp(time_str)
            if timestamp is None:
                continue
            aqi_value = to_float(aqi_str)
            rows.append(
                SourceHourlyRow(
                    source_slug="cem",
                    station_code=station_code,
                    station_name=str(station.get("station_name", "")),
                    station_index=station_code,
                    observation_hour_local=normalize_hour_local(timestamp),
                    pm25_ugm3="",
                    vn_aqi_pm25=stringify_number(aqi_value, digits=0),
                    pm25_status="missing",
                    vn_aqi_status="reported" if aqi_value is not None else "missing",
                    pm25_method="",
                    vn_aqi_method="reported_hourly_pm25_aqi_nowcast",
                    raw_sample_count="1",
                    raw_time_resolution_minutes="60",
                    backup_station_code=station_code,
                    snapshot_time_utc=snapshot_time_utc,
                )
            )
    return rows


def source_rows_to_dicts(rows: list[SourceHourlyRow]) -> list[dict[str, str]]:
    return [row.__dict__ for row in rows]


def canonical_rows_to_dicts(rows: list[CanonicalHourlyRow]) -> list[dict[str, str]]:
    return [row.__dict__ for row in rows]


def dedupe_rows(rows: list[dict[str, str]], key_fields: tuple[str, ...]) -> list[dict[str, str]]:
    keyed: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = tuple(row.get(field, "") for field in key_fields)
        keyed[key] = row
    return [keyed[key] for key in sorted(keyed)]


def load_existing_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_canonical_rows(source_rows: list[SourceHourlyRow], snapshot_time_utc: str) -> list[CanonicalHourlyRow]:
    grouped: dict[tuple[str, str], dict[str, SourceHourlyRow]] = defaultdict(dict)
    station_names: dict[str, str] = {}
    for row in source_rows:
        grouped[(row.station_code, row.observation_hour_local)][row.source_slug] = row
        station_names[row.station_code] = row.station_name

    canonical_rows: list[CanonicalHourlyRow] = []
    for (station_code, hour), by_source in sorted(grouped.items()):
        moit = by_source.get("moitruongthudo")
        cem = by_source.get("cem")

        pm25_value = moit.pm25_ugm3 if moit and moit.pm25_ugm3 else ""
        pm25_source_used = "moitruongthudo" if pm25_value else ""
        pm25_status = moit.pm25_status if pm25_value and moit else "missing"
        pm25_method = moit.pm25_method if pm25_value and moit else ""

        vn_aqi_value = moit.vn_aqi_pm25 if moit and moit.vn_aqi_pm25 else ""
        vn_aqi_source_used = "moitruongthudo" if vn_aqi_value else ""
        vn_aqi_status = moit.vn_aqi_status if vn_aqi_value and moit else "missing"
        vn_aqi_method = moit.vn_aqi_method if vn_aqi_value and moit else ""

        if cem and cem.vn_aqi_pm25:
            if not vn_aqi_value:
                vn_aqi_value = cem.vn_aqi_pm25
                vn_aqi_source_used = "cem"
                vn_aqi_status = cem.vn_aqi_status
                vn_aqi_method = cem.vn_aqi_method
            if not pm25_value:
                estimated_pm25 = invert_vn_aqi_pm25(float(cem.vn_aqi_pm25))
                pm25_value = stringify_number(estimated_pm25, digits=2)
                pm25_source_used = "cem"
                pm25_status = "estimated_from_cem_vn_aqi"
                pm25_method = "inverse_vn_aqi_nowcast_breakpoints"

        canonical_rows.append(
            CanonicalHourlyRow(
                station_code=station_code,
                station_name=station_names.get(station_code, ""),
                observation_hour_local=hour,
                pm25_ugm3=pm25_value,
                vn_aqi_pm25=vn_aqi_value,
                pm25_source_used=pm25_source_used,
                vn_aqi_source_used=vn_aqi_source_used,
                pm25_status=pm25_status,
                vn_aqi_status=vn_aqi_status,
                pm25_method=pm25_method,
                vn_aqi_method=vn_aqi_method,
                backup_station_code=station_code if cem else "",
                snapshot_time_utc=snapshot_time_utc,
            )
        )
    return canonical_rows


def build_stage2(snapshot: dict[str, Any], data_root: Path) -> dict[str, Any]:
    snapshot_time_utc = str(snapshot.get("snapshot_time_utc", ""))
    source_rows = []
    source_rows.extend(derive_moit_hourly_rows(snapshot_time_utc, snapshot["sources"]["moitruongthudo"]))
    source_rows.extend(derive_cem_hourly_rows(snapshot_time_utc, snapshot["sources"]["cem"]))
    canonical_rows = build_canonical_rows(source_rows, snapshot_time_utc)

    source_dicts = source_rows_to_dicts(source_rows)
    canonical_dicts = canonical_rows_to_dicts(canonical_rows)

    processed_dir = processed_root(data_root)
    source_csv = processed_dir / "hourly_source_records.csv"
    canonical_csv = processed_dir / "hourly_canonical_records.csv"

    merged_source = dedupe_rows(
        load_existing_csv(source_csv) + source_dicts,
        ("source_slug", "station_code", "observation_hour_local"),
    )
    merged_canonical = dedupe_rows(
        load_existing_csv(canonical_csv) + canonical_dicts,
        ("station_code", "observation_hour_local"),
    )

    source_fieldnames = list(SourceHourlyRow.__dataclass_fields__)
    canonical_fieldnames = list(CanonicalHourlyRow.__dataclass_fields__)
    write_csv(source_csv, merged_source, source_fieldnames)
    write_csv(canonical_csv, merged_canonical, canonical_fieldnames)

    summary = {
        "snapshot_time_utc": snapshot_time_utc,
        "source_rows_added": len(source_dicts),
        "canonical_rows_added": len(canonical_dicts),
        "source_rows_total": len(merged_source),
        "canonical_rows_total": len(merged_canonical),
        "pm25_estimated_from_cem_rows": sum(
            1 for row in canonical_dicts if row.get("pm25_status") == "estimated_from_cem_vn_aqi"
        ),
        "paths": {
            "hourly_source_records_csv": str(source_csv),
            "hourly_canonical_records_csv": str(canonical_csv),
        },
    }
    write_json(processed_dir / "latest-stage2-summary.json", summary)
    return summary


def resolve_stage1_snapshot(args: argparse.Namespace) -> tuple[dict[str, Any], Path | None]:
    if args.stage1_input:
        return read_json(args.stage1_input), args.stage1_input
    latest_path = raw_root(args.data_root) / "stage1" / "latest.json"
    if not latest_path.exists():
        raise SystemExit("No stage1 snapshot found. Run with --stage all or --stage stage1 first.")
    return read_json(latest_path), latest_path


def main() -> None:
    args = parse_args()
    stage1_snapshot = None
    stage1_path = None

    if args.stage in {"stage1", "all"}:
        stage1_snapshot, stage1_path = run_stage1(args.data_root, args.timeout)
        print(f"Wrote stage1 snapshot: {stage1_path}")

    if args.stage in {"stage2", "all"}:
        if stage1_snapshot is None:
            stage1_snapshot, stage1_path = resolve_stage1_snapshot(args)
        summary = build_stage2(stage1_snapshot, args.data_root)
        print(f"Wrote stage2 source rows: {summary['paths']['hourly_source_records_csv']}")
        print(f"Wrote stage2 canonical rows: {summary['paths']['hourly_canonical_records_csv']}")
        print(f"CEM-estimated PM2.5 rows in this run: {summary['pm25_estimated_from_cem_rows']}")


if __name__ == "__main__":
    main()
