#!/usr/bin/env python3
"""Batch-check pending LADBS permits and record a reviewer's explicit approvals."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from fccw_watchdog import DEFAULT_DB_PATH, SROLedgerEngine

LADBS = "https://data.lacity.org/resource/gwh9-jnip.json"
PARCELS = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0"
ZONING = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Zoning/FeatureServer/15"
ZIMAS = "https://zimas.lacity.org/"
DETAIL_FIELDS = ("zone", "permit_type", "submitted_date", "status_desc", "status_date")
REPORT_MAX_AGE = timedelta(days=1)


def request_json(endpoint, params):
    with urlopen(f"{endpoint}?{urlencode(params)}", timeout=12) as response:
        return json.load(response)


def get_ladbs_records(rows):
    records = {}
    for start in range(0, len(rows), 50):
        ids = [row["external_case_id"] for row in rows[start:start + 50]]
        literals = ", ".join("'" + case_id.replace("'", "''") + "'" for case_id in ids)
        page = request_json(LADBS, {
            "$where": f"permit_nbr IN ({literals})",
            "$select": ",".join(("permit_nbr", "primary_address", "apn", "lat", "lon", *DETAIL_FIELDS)),
            "$limit": 5000,
        })
        if not isinstance(page, list) or len(page) >= 5000:
            raise ValueError("DataLA response was invalid or incomplete.")
        for record in page:
            records.setdefault(record["permit_nbr"], []).append(record)
    return records


def lookup_point(endpoint, field, point):
    lon, lat = point
    response = request_json(f"{endpoint}/query", {
        "f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
        "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
        "outFields": field, "returnGeometry": "false",
    })
    if response.get("error") or response.get("exceededTransferLimit") or not isinstance(response.get("features"), list):
        raise ValueError(f"GIS lookup was incomplete for {field}.")
    return [feature["attributes"].get(field) for feature in response["features"]]


def at_point(point):
    try:
        return {
            "parcel_ids": lookup_point(PARCELS, "AIN", point),
            "city_zones": lookup_point(ZONING, "Zoning", point),
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"lookup_error": str(exc)}


def normalized(value):
    return "".join((value or "").split()).upper()


def parcel_id(value):
    return normalized(value).replace("-", "")


def fingerprint(row):
    data = json.dumps(row, sort_keys=True, separators=(",", ":"))
    return sha256(data.encode()).hexdigest()


def precheck(row, live_rows, evidence):
    result = {
        "id": row["id"], "permit_id": row["external_case_id"],
        "address": row["project_name"], "fingerprint": fingerprint(row),
        "status": "MANUAL_REVIEW", **evidence,
    }
    reasons = []
    if len(live_rows) != 1:
        reasons.append("DataLA returned zero or multiple rows for this permit.")
    else:
        live = live_rows[0]
        stored_details = json.loads(row["source_details"] or "{}")
        result["ladbs_apn"] = live.get("apn")
        result["ladbs_zone"] = live.get("zone")
        try:
            same_point = (
                float(live["lat"]) == row["latitude"]
                and float(live["lon"]) == row["longitude"]
            )
        except (ValueError, KeyError, TypeError):
            same_point = False
        if (
            not same_point
            or " ".join((live.get("primary_address") or "").upper().split())
            != " ".join(row["project_name"].upper().split())
            or any(live.get(field) != stored_details.get(field) for field in DETAIL_FIELDS)
        ):
            reasons.append("DataLA differs from the stored permit. Run the importer again.")
        if evidence.get("lookup_error"):
            reasons.append("Official parcel or zoning lookup failed.")
        else:
            apn = parcel_id(live.get("apn"))
            found = {parcel_id(value) for value in evidence["parcel_ids"]}
            if not (apn.isdigit() and len(apn) == 10 and found == {apn}):
                reasons.append("No unambiguous County parcel match to the DataLA APN.")
            zone = normalized(live.get("zone"))
            if not zone or {normalized(value) for value in evidence["city_zones"]} != {zone}:
                reasons.append("No unambiguous City zoning match to the DataLA zone.")
    result["reasons"] = reasons
    if not reasons:
        result["status"] = "CANDIDATE"
    return result


def build_report(ledger):
    rows = [r for r in ledger.list_gis_records("PENDING_REVIEW") if r["feed_source"] == "LADBS"]
    if not rows:
        return []
    live = get_ladbs_records(rows)
    points = list(dict.fromkeys((row["longitude"], row["latitude"]) for row in rows))
    with ThreadPoolExecutor(max_workers=4) as pool:
        evidence_by_point = dict(zip(points, pool.map(at_point, points)))
    return [
        precheck(row, live.get(row["external_case_id"], []), evidence_by_point[(row["longitude"], row["latitude"])])
        for row in rows
    ]


def approve(ledger, report, reviewer, ids):
    checked = datetime.fromisoformat(report["checked_at"])
    if not timedelta(0) <= datetime.now(timezone.utc) - checked <= REPORT_MAX_AGE:
        raise ValueError("Report is older than 24 hours or has an invalid timestamp. Run check again.")
    candidates = {row["id"]: row for row in report["records"] if row["status"] == "CANDIDATE"}
    selected = candidates.keys() if ids is None else dict.fromkeys(ids)
    with ledger.conn:
        ledger.conn.execute("BEGIN IMMEDIATE")
        pending = {row["id"]: row for row in ledger.list_gis_records("PENDING_REVIEW")}
        for record_id in selected:
            candidate = candidates.get(record_id)
            current = pending.get(record_id)
            if not candidate or not current or current["feed_source"] != "LADBS" or candidate["fingerprint"] != fingerprint(current):
                raise ValueError(f"{record_id} is no longer an unchanged pending candidate. Run check again.")
            ledger.verify_gis_record(
                record_id, reviewer, notes=f"Reviewer approved batch comparison dated {report['checked_at']} "
                "(DataLA permit, LA County parcel and LA City Planning zoning).",
            )
    return len(selected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check")
    check.add_argument("--report", type=Path, required=True)
    decision = commands.add_parser("approve")
    decision.add_argument("--report", type=Path, required=True)
    decision.add_argument("--reviewer", required=True)
    selection = decision.add_mutually_exclusive_group(required=True)
    selection.add_argument("--id", action="append", help="Repeat for each candidate UUID")
    selection.add_argument("--all-matches", action="store_true", help="Explicitly approve every candidate in this report")
    args = parser.parse_args()
    if not args.db.is_file() or args.report.resolve() == args.db.resolve():
        parser.error("Use an existing database and a separate report path.")
    try:
        ledger = SROLedgerEngine(args.db)
        with closing(ledger.conn):
            if args.command == "check":
                records = build_report(ledger)
                document = {"checked_at": datetime.now(timezone.utc).isoformat(),
                            "sources": {"permits": LADBS, "parcels": PARCELS, "zoning": ZONING, "manual_zimas": ZIMAS},
                            "records": records}
                with args.report.open("x", encoding="utf-8") as output:
                    json.dump(document, output, indent=2)
                    output.write("\n")
                for row in records:
                    print(row["status"], row["id"], row["permit_id"], row["address"])
                print(f"{sum(row['status'] == 'CANDIDATE' for row in records)} candidates out of {len(records)} permits.")
            else:
                document = json.loads(args.report.read_text(encoding="utf-8"))
                print(f"Approved {approve(ledger, document, args.reviewer, args.id)} permits.")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Batch review failed: {exc}\n")


if __name__ == "__main__":
    main()
