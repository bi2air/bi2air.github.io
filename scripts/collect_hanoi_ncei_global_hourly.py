#!/usr/bin/env python3
"""Collect NOAA NCEI Global Hourly observations into the project data layout.

Default output:
  data/external/raw/<site>/ncei-global-hourly/

The current site catalog contains Hanoi/Noibai. Add new sites to SITE_CATALOG
when their NCEI Global Hourly station identifiers are known.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path


DEFAULT_START = date(2015, 1, 1)
DEFAULT_END = date(2026, 5, 31)
DEFAULT_DATA_ROOT = Path("data")
SOURCE_SLUG = "ncei-global-hourly"
SEARCH_URL = "https://www.ncei.noaa.gov/access/services/search/v1/data"
DATA_URL = "https://www.ncei.noaa.gov/access/services/data/v1"
GLOBAL_HOURLY_PAGE = "https://www.ncei.noaa.gov/access/search/data-search/global-hourly"

SITE_CATALOG = {
    "hanoi": {
        "slug": "hanoi",
        "name": "Hanoi",
        "country": "Vietnam",
        "timezone": "Asia/Ho_Chi_Minh",
        "station": "48820099999",
        "station_name": "NOIBAI INTERNATIONAL, VM",
        "aliases": {"ha-noi", "ha noi", "noibai", "noi bai", "hanoi noibai"},
    },
    "ho-chi-minh-city": {
        "slug": "ho-chi-minh-city",
        "name": "Ho Chi Minh City",
        "country": "Vietnam",
        "timezone": "Asia/Ho_Chi_Minh",
        "station": "48900099999",
        "station_name": "TANSONNHAT INTERNATIONAL, VM",
        "aliases": {
            "hcmc", "ho chi minh", "ho chi minh city", "saigon",
            "sai gon", "tan son nhat", "tansonnhat", "tan-son-nhat"
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
        description="Download NCEI Global Hourly CSV for a configured site."
    )
    parser.add_argument("site", help="site/city name, e.g. hanoi")
    parser.add_argument("--start", default=DEFAULT_START.isoformat())
    parser.add_argument("--end", default=DEFAULT_END.isoformat())
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help="project data root; output goes under data-root/external/raw/<site>/ncei-global-hourly",
    )
    parser.add_argument("--output-dir", type=Path, help="override full source output directory")
    parser.add_argument("--force", action="store_true", help="redownload existing files")
    return parser.parse_args()


def source_output_dir(args: argparse.Namespace, site: dict[str, object]) -> Path:
    if args.output_dir:
        return args.output_dir
    return args.data_root / "external" / "raw" / str(site["slug"]) / SOURCE_SLUG


def build_url(base: str, params: dict[str, str | int]) -> str:
    return f"{base}?{urllib.parse.urlencode(params)}"


def download(url: str, dest: Path, force: bool = False) -> None:
    if dest.exists() and not force:
        return
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with urllib.request.urlopen(url) as response, tmp.open("wb") as fh:
        shutil.copyfileobj(response, fh)
    tmp.replace(dest)


def validate_csv(path: Path) -> dict[str, object]:
    rows = 0
    first_date: str | None = None
    last_date: str | None = None
    names: set[str] = set()
    locations: set[tuple[str, str, str]] = set()

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows += 1
            timestamp = row["DATE"]
            first_date = timestamp if first_date is None or timestamp < first_date else first_date
            last_date = timestamp if last_date is None or timestamp > last_date else last_date
            names.add(row.get("NAME", ""))
            locations.add((row.get("LATITUDE", ""), row.get("LONGITUDE", ""), row.get("ELEVATION", "")))

    return {
        "rows": rows,
        "first_date": first_date,
        "last_date": last_date,
        "station_names": sorted(names),
        "locations": [list(location) for location in sorted(locations)],
    }


def metadata_summary(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as fh:
        metadata = json.load(fh)
    return {
        "search_count": metadata.get("count"),
        "search_startDate": metadata.get("startDate"),
        "search_endDate": metadata.get("endDate"),
        "stations": metadata.get("stations", {}).get("buckets", []),
    }


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

    prefix = f"{station}_global-hourly_{start:%Y-%m-%d}_{end:%Y-%m-%d}"
    output_csv = output_dir / f"{prefix}.csv"
    search_json = output_dir / "search-metadata.json"
    collection_json = output_dir / "collection-metadata.json"
    readme = output_dir / "README.md"

    search_url = build_url(SEARCH_URL, {
        "dataset": "global-hourly",
        "stations": station,
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "limit": 1,
    })
    data_url = build_url(DATA_URL, {
        "dataset": "global-hourly",
        "stations": station,
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "format": "csv",
        "units": "metric",
        "includeStationName": "true",
        "includeStationLocation": "true",
    })

    download(search_url, search_json, args.force)
    download(data_url, output_csv, args.force)
    stats = validate_csv(output_csv)
    search_stats = metadata_summary(search_json)
    collection = {
        "source": "NOAA NCEI Global Hourly",
        "source_slug": SOURCE_SLUG,
        "source_page": GLOBAL_HOURLY_PAGE,
        "site": site["slug"],
        "site_name": site["name"],
        "station": station,
        "station_name": site["station_name"],
        "requested_start": start.isoformat(),
        "requested_end": end.isoformat(),
        "search_url": search_url,
        "data_url": data_url,
        "output_csv": str(output_csv),
        **stats,
        **search_stats,
    }
    collection_json.write_text(json.dumps(collection, indent=2) + "\n", encoding="utf-8")
    readme.write_text("\n".join([
        f"# {site['name']} NCEI Global Hourly", "",
        f"Site: `{site['slug']}`",
        f"Station: `{station}` (`{site['station_name']}`)",
        f"Requested period: `{start.isoformat()}` through `{end.isoformat()}`",
        f"Rows: `{stats['rows']}`",
        f"First DATE: `{stats['first_date']}`",
        f"Last DATE: `{stats['last_date']}`", "",
        "Files:",
        f"- `{output_csv.name}`: NCEI Global Hourly CSV",
        "- `search-metadata.json`: NCEI search metadata",
        "- `collection-metadata.json`: collection metadata and validation summary", "",
        f"Source page: {GLOBAL_HOURLY_PAGE}", "",
    ]), encoding="utf-8")
    print(f"Wrote {output_csv}")
    print(f"Rows: {stats['rows']}")
    print(f"Date bounds: {stats['first_date']} to {stats['last_date']}")


if __name__ == "__main__":
    main()
