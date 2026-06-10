#!/usr/bin/env python3
"""Build lightweight metadata for a directory of CSV exports."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


TIMESTAMP_HINTS = (
    "time",
    "date",
    "datetime",
    "timestamp",
    "created",
    "recorded",
)

DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%fZ",
)


@dataclass
class FileMetadata:
    filename: str
    relative_path: str
    size_bytes: int
    row_count: int
    column_count: int
    columns_json: str
    timestamp_column: str
    timestamp_non_null: int
    time_start: str
    time_end: str
    parse_note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="Directory containing CSV files")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tmp/airdb-csv-metadata"),
        help="Directory for metadata outputs",
    )
    return parser.parse_args()


def looks_like_timestamp(name: str) -> bool:
    lowered = name.strip().lower()
    return any(hint in lowered for hint in TIMESTAMP_HINTS)


def parse_datetime(value: str) -> datetime | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def choose_timestamp_column(fieldnames: list[str], sample_rows: list[dict[str, str]]) -> tuple[str, str]:
    candidates = [name for name in fieldnames if looks_like_timestamp(name)]
    if not candidates:
        return "", "no timestamp-like column"

    best_name = ""
    best_count = -1
    for name in candidates:
        parsed_values = [
            parsed
            for parsed in (parse_datetime(row.get(name, "")) for row in sample_rows)
            if parsed is not None
        ]
        if len(parsed_values) > best_count:
            best_name = name
            best_count = len(parsed_values)

    note = "timestamp inferred from sampled rows"
    if best_count == 0:
        note = "timestamp-like column present but sample values did not parse"
    return best_name, note


def scan_file(path: Path, root: Path) -> FileMetadata:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        sample_rows = []
        sample_limit = 5000
        for row in reader:
            if len(sample_rows) < sample_limit:
                sample_rows.append(row)

    timestamp_name, note = choose_timestamp_column(fieldnames, sample_rows)
    row_count = 0
    timestamp_count = 0
    time_start = None
    time_end = None

    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_count += 1
            if not timestamp_name:
                continue
            parsed = parse_datetime(row.get(timestamp_name, ""))
            if parsed is None:
                continue
            timestamp_count += 1
            if time_start is None or parsed < time_start:
                time_start = parsed
            if time_end is None or parsed > time_end:
                time_end = parsed

    return FileMetadata(
        filename=path.name,
        relative_path=str(path.relative_to(root)),
        size_bytes=path.stat().st_size,
        row_count=row_count,
        column_count=len(fieldnames),
        columns_json=json.dumps(fieldnames),
        timestamp_column=timestamp_name,
        timestamp_non_null=timestamp_count,
        time_start=time_start.isoformat(sep=" ") if time_start else "",
        time_end=time_end.isoformat(sep=" ") if time_end else "",
        parse_note=note,
    )


def iter_csv_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.csv")):
        if path.name.startswith("._"):
            continue
        yield path


def write_metadata_csv(output_path: Path, rows: list[FileMetadata]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "filename",
                "relative_path",
                "size_bytes",
                "row_count",
                "column_count",
                "columns_json",
                "timestamp_column",
                "timestamp_non_null",
                "time_start",
                "time_end",
                "parse_note",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_summary(output_path: Path, input_dir: Path, rows: list[FileMetadata]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    for row in rows:
        counts["files"] += 1
        counts["rows"] += row.row_count
        if row.timestamp_column:
            counts["timestamp_files"] += 1

    dated_rows = [row for row in rows if row.time_start and row.time_end]
    global_start = min((row.time_start for row in dated_rows), default="")
    global_end = max((row.time_end for row in dated_rows), default="")

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("# CSV Output Metadata\n\n")
        handle.write(f"- Source directory: `{input_dir}`\n")
        handle.write(f"- CSV files scanned: `{counts['files']}`\n")
        handle.write(f"- Total data rows: `{counts['rows']}`\n")
        handle.write(f"- Files with inferred timestamp column: `{counts['timestamp_files']}`\n")
        if global_start and global_end:
            handle.write(f"- Overall full-file time span: `{global_start}` to `{global_end}`\n")
        handle.write("\n## Files\n\n")
        handle.write("| File | Rows | Cols | Timestamp | Time span |\n")
        handle.write("| --- | ---: | ---: | --- | --- |\n")
        for row in rows:
            if row.time_start and row.time_end:
                span = f"{row.time_start} to {row.time_end}"
            elif row.timestamp_column:
                span = row.parse_note
            else:
                span = "n/a"
            handle.write(
                f"| `{row.filename}` | {row.row_count} | {row.column_count} | "
                f"`{row.timestamp_column or 'n/a'}` | {span} |\n"
            )


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    rows = [scan_file(path, input_dir) for path in iter_csv_files(input_dir)]
    rows.sort(key=lambda item: item.filename.lower())
    write_metadata_csv(args.output_dir / "metadata.csv", rows)
    write_summary(args.output_dir / "summary.md", input_dir, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
