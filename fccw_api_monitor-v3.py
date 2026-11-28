#!/usr/bin/env python3
"""Import official LADBS permits into the FCCW pending review queue."""

import argparse
from contextlib import closing
from datetime import date, timedelta
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlencode
from urllib.request import urlopen

from fccw_watchdog import DEFAULT_BUFFER_DEG, DEFAULT_DB_PATH, SROLedgerEngine, ZoningAuditEngine

ENDPOINT = "https://data.lacity.org/resource/gwh9-jnip.json"
SOURCE = "LADBS"
PAGE_SIZE = 500
PERMIT_FIELDS = (
    "permit_nbr", "primary_address", "lat", "lon", "zone", "permit_type",
    "submitted_date", "status_desc", "status_date",
)


def fetch_permits(since):
    bounds = ZoningAuditEngine.SKID_ROW_BOUNDS
    buffer = DEFAULT_BUFFER_DEG
    where = (
        f"(submitted_date >= '{since}T00:00:00' OR status_date >= '{since}T00:00:00') "
        f"AND lat BETWEEN {bounds['lat_south'] - buffer:.6f} AND {bounds['lat_north'] + buffer:.6f} "
        f"AND lon BETWEEN {bounds['lon_west'] - buffer:.6f} AND {bounds['lon_east'] + buffer:.6f}"
    )
    offset = 0
    while True:
        query = urlencode({
            "$select": ",".join(PERMIT_FIELDS), "$where": where,
            "$order": "permit_nbr, :id", "$limit": PAGE_SIZE, "$offset": offset,
        })
        with urlopen(f"{ENDPOINT}?{query}", timeout=30) as response:
            page = json.load(response)
        if not isinstance(page, list):
            raise ValueError("Unexpected response from DataLA.")
        yield from page
        if len(page) < PAGE_SIZE:
            return
        offset += len(page)


def normalize_permit(row):
    case_id = row["permit_nbr"].strip()
    address = row["primary_address"].strip()
    lat, lon = float(row["lat"]), float(row["lon"])
    if not case_id or not address or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError(f"Incomplete permit record: {case_id!r}")
    return {
        "feed_source": SOURCE,
        "external_case_id": case_id,
        "project_name": address,
        "latitude": lat,
        "longitude": lon,
        "source_details": {
            key: row.get(key) for key in ("zone", "permit_type", "submitted_date", "status_desc", "status_date")
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--days", type=int, default=30, help="Submission and status-change lookback")
    args = parser.parse_args()
    if not 1 <= args.days <= 3650:
        parser.error("--days must be between 1 and 3650")
    try:
        since = date.today() - timedelta(days=args.days)
        permits = {}
        for raw in fetch_permits(since):
            permit = normalize_permit(raw)
            case_id = permit["external_case_id"]
            if case_id in permits and permits[case_id] != permit:
                raise ValueError(f"Conflicting rows for permit {case_id}.")
            permits[case_id] = permit
        ledger = SROLedgerEngine(args.db)
        with closing(ledger.conn), ledger.conn:
            ledger.conn.execute("BEGIN IMMEDIATE")
            for permit in permits.values():
                ledger.upsert_gis_feed_record(**permit)
            ledger.mark_feed_success(SOURCE)
        print(f"Checked {len(permits)} LADBS permits. New or changed permits are pending review.")
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        parser.exit(1, f"DataLA import failed: {exc}\n")


if __name__ == "__main__":
    main()
