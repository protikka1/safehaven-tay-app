#!/usr/bin/env python3
"""Export verified FCCW watchdog records as a PNG and GeoJSON."""

import argparse
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from fccw_watchdog import DEFAULT_BUFFER_DEG, DEFAULT_DB_PATH, SROLedgerEngine, ZoningAuditEngine

ASSETS = Path(__file__).resolve().parent / "docs" / "assets"
SKID_ROW_BOUNDS = ZoningAuditEngine.SKID_ROW_BOUNDS
BUFFER_DISTANCE_DEG = DEFAULT_BUFFER_DEG
PUBLIC_FIELDS = (
    "id", "feed_source", "external_case_id", "project_name", "proposed_units",
    "affordable_units", "zoning_requested", "audit_status", "verified_at",
)


def export_geojson(records, output_path, last_checked=None):
    features = []
    for row in records:
        if row["verification_status"] != "VERIFIED":
            continue
        properties = {key: row[key] for key in PUBLIC_FIELDS}
        if row["feed_source"] == "LADBS" and row.get("source_details"):
            details = json.loads(row["source_details"])
            properties["permit"] = {
                key: details.get(key)
                for key in ("zone", "permit_type", "submitted_date", "status_desc", "status_date")
            }
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"]],
            },
            "properties": properties,
        })
    document = json.dumps(
        {"type": "FeatureCollection", "features": features, "ladbs_last_checked": last_checked},
        indent=2, allow_nan=False,
    )
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=output_path.parent, delete=False) as tmp:
        temp_path = Path(tmp.name)
        try:
            tmp.write(document + "\n")
            tmp.close()
            temp_path.replace(output_path)
        finally:
            temp_path.unlink(missing_ok=True)


def render_map_png(records, output_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="white", palette="colorblind", font="DejaVu Sans")
    styles = {
        "CRITICAL VIOLATION": ("#dc2626", "X"),
        "BUFFER INVASION": ("#d97706", "o"),
        "WARNING": ("#d97706", "o"),
        "PASS": ("#16a34a", "^"),
    }
    cases = []
    for row in records:
        if row["verification_status"] != "VERIFIED":
            continue
        status = row["audit_status"]
        color, marker = styles.get(status, ("#2874a6", "o"))
        cases.append({
            "name": row["project_name"], "lat": row["latitude"], "lon": row["longitude"],
            "status": status, "color": color, "marker": marker, "size": 110,
            "units": f'{row["affordable_units"]}/{row["proposed_units"]} affordable units' if row["proposed_units"] else "",
            "ha": "left", "dx": 0.0003, "dy": 0.00015,
        })

    # Set up figure
    fig, ax = plt.subplots(figsize=(11, 9))

    # Plot street grid lines to give genuine GIS cartography feel
    # East-West streets
    ew_streets = {
        "3rd St": 34.0482,
        "4th St": 34.0464,
        "5th St": 34.0446,
        "6th St": 34.0428,
        "7th St": 34.0410
    }
    # North-South streets
    ns_streets = {
        "Main St": -118.2495,
        "Los Angeles St": -118.2460,
        "San Pedro St": -118.2440,
        "Central Ave": -118.2412,
        "Alameda St": -118.2360
    }

    # Drawing grid lines
    for street_name, lat in ew_streets.items():
        ax.plot([-118.2530, -118.2320], [lat, lat], color='#e2e8f0', linewidth=1.5, linestyle='-', zorder=1)
        ax.text(-118.2525, lat + 0.00015, street_name, fontsize=8, color='#64748b', fontweight='bold', zorder=2)

    for street_name, lon in ns_streets.items():
        ax.plot([lon, lon], [34.0385, 34.0505], color='#e2e8f0', linewidth=1.5, linestyle='-', zorder=1)
        ax.text(lon + 0.0001, 34.0390, street_name, fontsize=8, color='#64748b', fontweight='bold', rotation=90, zorder=2)

    # Shade the Skid Row containment zone (Historical Bounds)
    skid_row_rect = plt.Rectangle(
        (SKID_ROW_BOUNDS['lon_west'], SKID_ROW_BOUNDS['lat_south']),
        SKID_ROW_BOUNDS['lon_east'] - SKID_ROW_BOUNDS['lon_west'],
        SKID_ROW_BOUNDS['lat_north'] - SKID_ROW_BOUNDS['lat_south'],
        facecolor='#3b82f6', alpha=0.08, edgecolor='#3b82f6', linewidth=2.5, linestyle='-', label='Skid Row monitoring bounds', zorder=3
    )
    ax.add_patch(skid_row_rect)

    # Draw the buffer boundaries (Boundary + 0.005 degrees)
    buffer_rect = plt.Rectangle(
        (SKID_ROW_BOUNDS['lon_west'] - BUFFER_DISTANCE_DEG, SKID_ROW_BOUNDS['lat_south'] - BUFFER_DISTANCE_DEG),
        (SKID_ROW_BOUNDS['lon_east'] - SKID_ROW_BOUNDS['lon_west']) + 2*BUFFER_DISTANCE_DEG,
        (SKID_ROW_BOUNDS['lat_north'] - SKID_ROW_BOUNDS['lat_south']) + 2*BUFFER_DISTANCE_DEG,
        facecolor='none', edgecolor='#ef4444', linewidth=1.8, linestyle='--', label='Monitoring buffer (0.005°)', zorder=3
    )
    ax.add_patch(buffer_rect)

    # Plot cases with distinct markers and labels
    for case in cases:
        # Scatter point
        ax.scatter(case['lon'], case['lat'], c=case['color'], marker=case['marker'], s=case['size'], edgecolor='black', linewidths=1.2, zorder=5, label=f"{case['status']}: {case['name']}")
    
        # Label with box
        box_style = dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor=case['color'], alpha=0.9, linewidth=1.2)
        label_text = f"{case['name']}\nWatchdog flag: {case['status']}\n{case['units']}"
    
        ax.text(case['lon'] + case['dx'], case['lat'] + case['dy'], label_text, fontsize=8, color='#1e293b', fontweight='bold', bbox=box_style, zorder=6, ha=case['ha'])

    # Decorate map
    ax.set_xlim(-118.2550, -118.2300)
    ax.set_ylim(34.0380, 34.0510)

    # Set grid off and clean up axes
    ax.set_xticks([])
    ax.set_yticks([])
    sns.despine(left=True, bottom=True)

    # Add compass and scale bar indicators to make it look like a professional GIS product
    ax.text(-118.2320, 34.0495, "N\n▲", fontsize=15, color='#475569', ha='center', fontweight='bold', bbox=dict(boxstyle='circle,pad=0.2', facecolor='#f8fafc', edgecolor='#cbd5e1', alpha=0.9))

    # Scale bar (Approx 0.5 miles)
    ax.plot([-118.2350, -118.2350 + 0.0072], [34.0385, 34.0385], color='#475569', linewidth=3, zorder=4)
    ax.text(-118.2314, 34.0387, "0.5 Miles", fontsize=8, color='#475569', fontweight='bold')

    ax.set_title("Verified watchdog records", fontsize=12, fontweight="bold")
    fig.suptitle("Fourth & Central Community Watch")
    if not cases:
        ax.text(0.5, 0.5, "No verified records", transform=ax.transAxes, ha="center")

    # Customize Legend
    handles, labels = ax.get_legend_handles_labels()
    # Filter out duplicate handles
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='lower left', frameon=True, facecolor='#f8fafc', edgecolor='#cbd5e1', fontsize=8.5, shadow=False)

    plt.tight_layout(pad=2.0)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--png", type=Path, default=ASSETS / "fccw_zoning_audit_map.png")
    parser.add_argument("--geojson", type=Path, default=ASSETS / "verified_watchdog.geojson")
    parser.add_argument("--geojson-only", action="store_true")
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error(f"Database missing: {args.db}. Run fccw_watchdog.py list first.")
    if len({path.resolve() for path in (args.db, args.png, args.geojson)}) != 3:
        parser.error("The database, PNG and GeoJSON paths must be distinct.")
    ledger = SROLedgerEngine(args.db)
    try:
        records = ledger.list_gis_records("VERIFIED")
        last_checked = ledger.feed_last_success("LADBS")
    finally:
        ledger.conn.close()
    if not args.geojson_only:
        args.png.parent.mkdir(parents=True, exist_ok=True)
        render_map_png(records, args.png)
    args.geojson.parent.mkdir(parents=True, exist_ok=True)
    export_geojson(records, args.geojson, last_checked)
    print(f"Exported {len(records)} verified record(s).")


if __name__ == "__main__":
    main()
