#!/usr/bin/env python3
"""Extract Hanoi/Lang IGRA sounding levels to a flat CSV."""

from __future__ import annotations

import csv
import zipfile
from datetime import datetime
from pathlib import Path


STATION = "VMM00048820"
START = (2015, 1, 1, 0)
END_EXCLUSIVE = (2026, 6, 1, 0)


def as_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    parsed = int(value)
    if parsed in {-8888, -9999}:
        return None
    return parsed


def scale(value: int | None, divisor: float) -> float | None:
    if value is None:
        return None
    return value / divisor


def fmt(value: float | int | str | None) -> float | int | str:
    if value is None:
        return ""
    return value


def parse_header(line: str) -> dict[str, int | str]:
    return {
        "station": line[1:12].strip(),
        "year": int(line[13:17]),
        "month": int(line[18:20]),
        "day": int(line[21:23]),
        "hour": int(line[24:26]),
        "release_time": line[27:31].strip(),
        "num_levels": int(line[32:36]),
        "pressure_source": line[37:45].strip(),
        "nonpressure_source": line[46:54].strip(),
        "latitude": int(line[55:62]) / 10000.0,
        "longitude": int(line[63:71]) / 10000.0,
    }


def parse_level(line: str) -> dict[str, int | str | None]:
    return {
        "lvltyp1": as_int(line[0:1]),
        "lvltyp2": as_int(line[1:2]),
        "etime": as_int(line[3:8]),
        "pressure": as_int(line[9:15]),
        "pflag": line[15:16].strip(),
        "height": as_int(line[16:21]),
        "zflag": line[21:22].strip(),
        "temp": as_int(line[22:27]),
        "tflag": line[27:28].strip(),
        "rh": as_int(line[28:33]),
        "dpdp": as_int(line[34:39]),
        "wdir": as_int(line[40:45]),
        "wspd": as_int(line[46:51]),
    }


def in_range(header: dict[str, int | str]) -> bool:
    hour = int(header["hour"])
    if hour == 99:
        hour = 0
    stamp = (int(header["year"]), int(header["month"]), int(header["day"]), hour)
    return START <= stamp < END_EXCLUSIVE


def valid_utc(header: dict[str, int | str]) -> str:
    hour = int(header["hour"])
    if hour == 99:
        return f"{header['year']:04d}-{header['month']:02d}-{header['day']:02d}T99:00:00Z"
    return datetime(
        int(header["year"]), int(header["month"]), int(header["day"]), hour
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    root = Path("data/igra_hanoi_lang")
    source = root / f"{STATION}-data.txt.zip"
    output = root / f"{STATION}_2015-01_2026-05_levels.csv"

    rows = 0
    soundings = 0
    current_header: dict[str, int | str] | None = None
    include_current = False

    with zipfile.ZipFile(source) as zf, zf.open(f"{STATION}-data.txt") as raw, output.open(
        "w", newline=""
    ) as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "station",
                "validUTC",
                "release_time_utc",
                "latitude",
                "longitude",
                "pressure_source",
                "nonpressure_source",
                "lvltyp1",
                "lvltyp2",
                "elapsed_time",
                "pressure_hpa",
                "pressure_qc",
                "height_m",
                "height_qc",
                "tmpc",
                "tmpc_qc",
                "rh_percent",
                "dewpoint_depression_c",
                "dwpc",
                "drct",
                "speed_mps",
                "speed_kts",
            ]
        )

        for raw_line in raw:
            line = raw_line.decode("ascii")
            if line.startswith("#"):
                current_header = parse_header(line)
                include_current = in_range(current_header)
                if include_current:
                    soundings += 1
                continue

            if not include_current or current_header is None:
                continue

            level = parse_level(line)
            temp_c = scale(level["temp"], 10.0)
            dewpoint_depression_c = scale(level["dpdp"], 10.0)
            dewpoint_c = None
            if temp_c is not None and dewpoint_depression_c is not None:
                dewpoint_c = temp_c - dewpoint_depression_c
            wind_mps = scale(level["wspd"], 10.0)
            wind_kts = None if wind_mps is None else wind_mps * 1.9438444924406

            writer.writerow(
                [
                    current_header["station"],
                    valid_utc(current_header),
                    current_header["release_time"],
                    current_header["latitude"],
                    current_header["longitude"],
                    current_header["pressure_source"],
                    current_header["nonpressure_source"],
                    fmt(level["lvltyp1"]),
                    fmt(level["lvltyp2"]),
                    fmt(level["etime"]),
                    fmt(scale(level["pressure"], 100.0)),
                    level["pflag"],
                    fmt(level["height"]),
                    level["zflag"],
                    fmt(temp_c),
                    level["tflag"],
                    fmt(scale(level["rh"], 10.0)),
                    fmt(dewpoint_depression_c),
                    fmt(dewpoint_c),
                    fmt(level["wdir"]),
                    fmt(wind_mps),
                    fmt(None if wind_kts is None else round(wind_kts, 3)),
                ]
            )
            rows += 1

    print(f"Wrote {rows} levels from {soundings} soundings to {output}")


if __name__ == "__main__":
    main()
