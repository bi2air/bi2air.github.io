#!/usr/bin/env python3
"""Collect upper-air soundings from NOAA IGRA into the project data layout.

Default output:
  data/external/raw/<site>/igra-raob/

The current site catalog contains Hanoi/Lang. Add new sites to SITE_CATALOG
when their IGRA station identifiers are known.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import urllib.request
import zipfile
from datetime import date, datetime
from pathlib import Path


DEFAULT_START = date(2015, 1, 1)
DEFAULT_END = date(2026, 5, 31)
DEFAULT_DATA_ROOT = Path("data")
SOURCE_SLUG = "igra-raob"
IGRA_BASE = "https://www.ncei.noaa.gov/pub/data/igra"
STATION_LIST_URL = f"{IGRA_BASE}/igra2-station-list.txt"
IEM_RAOB_URL = "https://mesonet.agron.iastate.edu/archive/raob/"

SITE_CATALOG = {
    "hanoi": {
        "slug": "hanoi",
        "name": "Hanoi",
        "country": "Vietnam",
        "timezone": "Asia/Ho_Chi_Minh",
        "station": "VMM00048820",
        "station_name": "HA NOI",
        "aliases": {"ha-noi", "ha noi", "lang", "hanoi lang", "hanoi-lang"},
    },
    "ho-chi-minh-city": {
        "slug": "ho-chi-minh-city",
        "name": "Ho Chi Minh City",
        "country": "Vietnam",
        "timezone": "Asia/Ho_Chi_Minh",
        "station": "VMM00048900",
        "station_name": "TAN SON HOA",
        "aliases": {
            "hcmc", "ho chi minh", "ho chi minh city", "saigon",
            "sai gon", "tan son hoa", "tan-son-hoa"
        },
    },
}


def normalize_site(value: str) -> dict[str, object]:
    key = value.strip().lower().replace("_", "-")
    for site_key, site in SITE_CATALOG.items():
        aliases = set(site.get("aliases", set()))
        if key == site_key or key == site["slug"] or key in aliases:
            return site
    choices = ", ".join(sorted(SITE_CATALOG))
    raise SystemExit(f"Unknown site {value!r}. Known sites: {choices}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and flatten IGRA sounding data for a configured site."
    )
    parser.add_argument("site", help="site/city name, e.g. hanoi")
    parser.add_argument("--start", default=DEFAULT_START.isoformat())
    parser.add_argument("--end", default=DEFAULT_END.isoformat())
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help="project data root; output goes under data-root/external/raw/<site>/igra-raob",
    )
    parser.add_argument("--output-dir", type=Path, help="override full source output directory")
    parser.add_argument("--force", action="store_true", help="redownload raw inputs")
    return parser.parse_args()


def source_output_dir(args: argparse.Namespace, site: dict[str, object]) -> Path:
    if args.output_dir:
        return args.output_dir
    return args.data_root / "external" / "raw" / str(site["slug"]) / SOURCE_SLUG


def download(url: str, dest: Path, force: bool = False) -> None:
    if dest.exists() and not force:
        return
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with urllib.request.urlopen(url) as response, tmp.open("wb") as fh:
        shutil.copyfileobj(response, fh)
    tmp.replace(dest)


def as_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    parsed = int(value)
    if parsed in {-8888, -9999}:
        return None
    return parsed


def scale(value: int | None, divisor: float) -> float | None:
    return None if value is None else value / divisor


def blank_none(value: float | int | str | None) -> float | int | str:
    return "" if value is None else value


def parse_header(line: str) -> dict[str, int | str | float]:
    return {
        "station": line[1:12].strip(),
        "year": int(line[13:17]),
        "month": int(line[18:20]),
        "day": int(line[21:23]),
        "hour": int(line[24:26]),
        "release_time": line[27:31].strip(),
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


def header_date(header: dict[str, int | str | float]) -> date:
    return date(int(header["year"]), int(header["month"]), int(header["day"]))


def valid_utc(header: dict[str, int | str | float]) -> str:
    hour = int(header["hour"])
    if hour == 99:
        return f"{header['year']:04d}-{header['month']:02d}-{header['day']:02d}T99:00:00Z"
    return datetime(
        int(header["year"]), int(header["month"]), int(header["day"]), hour
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def flatten_igra(
    station: str, source_zip: Path, output_csv: Path, start: date, end: date
) -> dict[str, int | str | None]:
    rows = 0
    soundings = 0
    first_time: str | None = None
    last_time: str | None = None
    current_header: dict[str, int | str | float] | None = None
    include_current = False

    with zipfile.ZipFile(source_zip) as zf, zf.open(f"{station}-data.txt") as raw:
        with output_csv.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow([
                "station", "validUTC", "release_time_utc", "latitude", "longitude",
                "pressure_source", "nonpressure_source", "lvltyp1", "lvltyp2",
                "elapsed_time", "pressure_hpa", "pressure_qc", "height_m",
                "height_qc", "tmpc", "tmpc_qc", "rh_percent",
                "dewpoint_depression_c", "dwpc", "drct", "speed_mps", "speed_kts",
            ])

            for raw_line in raw:
                line = raw_line.decode("ascii")
                if line.startswith("#"):
                    current_header = parse_header(line)
                    include_current = start <= header_date(current_header) <= end
                    if include_current:
                        soundings += 1
                    continue

                if not include_current or current_header is None:
                    continue

                level = parse_level(line)
                temp_c = scale(level["temp"], 10.0)
                dpdp_c = scale(level["dpdp"], 10.0)
                dewpoint_c = temp_c - dpdp_c if temp_c is not None and dpdp_c is not None else None
                wind_mps = scale(level["wspd"], 10.0)
                wind_kts = None if wind_mps is None else round(wind_mps * 1.9438444924406, 3)
                timestamp = valid_utc(current_header)

                writer.writerow([
                    current_header["station"], timestamp, current_header["release_time"],
                    current_header["latitude"], current_header["longitude"],
                    current_header["pressure_source"], current_header["nonpressure_source"],
                    blank_none(level["lvltyp1"]), blank_none(level["lvltyp2"]),
                    blank_none(level["etime"]), blank_none(scale(level["pressure"], 100.0)),
                    level["pflag"], blank_none(level["height"]), level["zflag"],
                    blank_none(temp_c), level["tflag"], blank_none(scale(level["rh"], 10.0)),
                    blank_none(dpdp_c), blank_none(dewpoint_c), blank_none(level["wdir"]),
                    blank_none(wind_mps), blank_none(wind_kts),
                ])
                rows += 1
                first_time = timestamp if first_time is None or timestamp < first_time else first_time
                last_time = timestamp if last_time is None or timestamp > last_time else last_time

    return {"rows": rows, "soundings": soundings, "first_time": first_time, "last_time": last_time}


def station_metadata(station_list: Path, station: str) -> str:
    for line in station_list.read_text(encoding="utf-8").splitlines():
        if line.startswith(station):
            return line
    return ""


def write_site_registry(data_root: Path) -> None:
    external = data_root / "external"
    external.mkdir(parents=True, exist_ok=True)
    registry_path = external / "sites.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    else:
        registry = {}

    for site in SITE_CATALOG.values():
        slug = str(site["slug"])
        entry = registry.setdefault(slug, {})
        for key in ["slug", "name", "country", "timezone"]:
            entry[key] = site[key]
        stations = entry.setdefault("stations", {})
        station_names = entry.setdefault("station_names", {})
        stations[SOURCE_SLUG] = site["station"]
        station_names[SOURCE_SLUG] = site["station_name"]

    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    site = normalize_site(args.site)
    station = str(site["station"])
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    if end < start:
        raise SystemExit("--end must be on or after --start")

    output_dir = source_output_dir(args, site)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.output_dir:
        write_site_registry(args.data_root)

    data_url = f"{IGRA_BASE}/data/data-por/{station}-data.txt.zip"
    source_zip = output_dir / f"{station}-data.txt.zip"
    station_list = output_dir / "igra2-station-list.txt"
    output_csv = output_dir / f"{station}_{start:%Y-%m-%d}_{end:%Y-%m-%d}_levels.csv"
    metadata_json = output_dir / "collection-metadata.json"
    readme = output_dir / "README.md"

    download(data_url, source_zip, args.force)
    download(STATION_LIST_URL, station_list, args.force)
    stats = flatten_igra(station, source_zip, output_csv, start, end)
    metadata = {
        "source": "NOAA NCEI IGRA",
        "source_slug": SOURCE_SLUG,
        "iem_raob_page": IEM_RAOB_URL,
        "reason_for_igra": "Hanoi/Lang is not exposed by the IEM RAOB station list; IEM documents NCEI IGRA as a backfill source.",
        "site": site["slug"],
        "site_name": site["name"],
        "station": station,
        "station_name": site["station_name"],
        "station_metadata": station_metadata(station_list, station),
        "requested_start": start.isoformat(),
        "requested_end": end.isoformat(),
        "data_url": data_url,
        "output_csv": str(output_csv),
        **stats,
    }
    metadata_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    readme.write_text("\n".join([
        f"# {site['name']} IGRA Sounding Data", "",
        f"Site: `{site['slug']}`",
        f"Station: `{station}` (`{site['station_name']}`)",
        f"Requested period: `{start.isoformat()}` through `{end.isoformat()}`",
        f"Rows: `{stats['rows']}`",
        f"Soundings: `{stats['soundings']}`",
        f"First timestamp: `{stats['first_time']}`",
        f"Last timestamp: `{stats['last_time']}`", "",
        "Files:",
        f"- `{source_zip.name}`: raw IGRA period-of-record ZIP",
        f"- `{output_csv.name}`: flattened level-by-level CSV",
        "- `collection-metadata.json`: collection metadata",
        "- `igra2-station-list.txt`: IGRA station list snapshot", "",
        f"IEM RAOB page: {IEM_RAOB_URL}",
        f"IGRA data URL: {data_url}", "",
    ]), encoding="utf-8")
    print(f"Wrote {output_csv}")
    print(f"Rows: {stats['rows']}; soundings: {stats['soundings']}")
    print(f"Date bounds: {stats['first_time']} to {stats['last_time']}")


if __name__ == "__main__":
    main()
