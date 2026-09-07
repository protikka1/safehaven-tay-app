from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

OUTPUT_PATH = (
    Path(__file__).resolve().parent / "docs" / "assets" / "fccw_zoning_audit_map.png"
)
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Set Seaborn theme
sns.set_theme(style='white', palette='colorblind', font='DejaVu Sans')

# Coordinates
SKID_ROW_BOUNDS = {
    'lat_north': 34.0482,   # 3rd St
    'lat_south': 34.0410,   # 7th St
    'lon_west': -118.2495,  # Main St
    'lon_east': -118.2360   # Alameda St
}
BUFFER_DISTANCE_DEG = 0.005

# Project Locations and details
cases = [
    {
        "name": "Fourth & Central Megabuild",
        "lat": 34.0458,
        "lon": -118.2390,
        "status": "BUFFER WATCH",
        "color": "#d97706",  # Deep Yellow/Gold
        "marker": "o",
        "size": 180,
        "units": "1,600 units (15.6% Affordable)",
        "ha": "left",
        "dx": 0.0006,
        "dy": -0.00035
    },
    {
        "name": "Winston Street Luxury Lofts",
        "lat": 34.0442,
        "lon": -118.2438,
        "status": "CRITICAL VIOLATION",
        "color": "#dc2626",  # Crimson Red
        "marker": "X",
        "size": 220,
        "units": "200 units (5% Affordable - Fails 80% IX1 Mandate)",
        "ha": "left",
        "dx": 0.0006,
        "dy": -0.00035
    },
    {
        "name": "Central Avenue Brewery & Bar",
        "lat": 34.0465,
        "lon": -118.2412,
        "status": "COMPATIBLE USE EXCLUSION",
        "color": "#ea580c",  # Vivid Orange
        "marker": "s",
        "size": 160,
        "units": "CUB Alcohol Permit near Recovery Space",
        "ha": "right",
        "dx": -0.0006,
        "dy": 0.0004
    },
    {
        "name": "Renato Apartments Phase II",
        "lat": 34.0435,
        "lon": -118.2449,
        "status": "PASS",
        "color": "#16a34a",  # Forest Green
        "marker": "^",
        "size": 160,
        "units": "100 units (100% Affordable SRO Upgrade)",
        "ha": "right",
        "dx": -0.0006,
        "dy": -0.0005
    }
]

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
    facecolor='#3b82f6', alpha=0.08, edgecolor='#3b82f6', linewidth=2.5, linestyle='-', label='Skid Row Containment Area (IX1)', zorder=3
)
ax.add_patch(skid_row_rect)

# Draw the buffer boundaries (Boundary + 0.005 degrees)
buffer_rect = plt.Rectangle(
    (SKID_ROW_BOUNDS['lon_west'] - BUFFER_DISTANCE_DEG, SKID_ROW_BOUNDS['lat_south'] - BUFFER_DISTANCE_DEG),
    (SKID_ROW_BOUNDS['lon_east'] - SKID_ROW_BOUNDS['lon_west']) + 2*BUFFER_DISTANCE_DEG,
    (SKID_ROW_BOUNDS['lat_north'] - SKID_ROW_BOUNDS['lat_south']) + 2*BUFFER_DISTANCE_DEG,
    facecolor='none', edgecolor='#ef4444', linewidth=1.8, linestyle='--', label='Gentrification Peripheral Buffer Zone (0.3 Mi)', zorder=3
)
ax.add_patch(buffer_rect)

# Plot cases with distinct markers and labels
for case in cases:
    # Scatter point
    ax.scatter(case['lon'], case['lat'], c=case['color'], marker=case['marker'], s=case['size'], edgecolor='black', linewidths=1.2, zorder=5, label=f"{case['status']}: {case['name']}")
    
    # Label with box
    box_style = dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor=case['color'], alpha=0.9, linewidth=1.2)
    label_text = f"{case['name']}\nStatus: {case['status']}\n{case['units']}"
    
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

# Title-as-takeaway (Data Craft Standard)
ax.set_title("Winston St Luxury Build Triggers Critical IX1 Boundary Breach Inside Containment Area", fontsize=12, fontweight='bold', pad=20, color='#0f172a')
fig.suptitle("FCCW GIS LAND-USE AUDIT ENGINE - SPATIAL MONITORING DASHBOARD", fontsize=14, fontweight='bold', y=0.96, color='#1e293b')

# Source citation at bottom left
ax.text(-118.2545, 34.0371, "Source: LA City Planning Open Data API (CPC-2025-1600-GPA-VZC-HD-MCUP-SPR / DIR-2026-8941-TOC-SPP-WDI)", fontsize=7, color='#64748b', style='italic')

# Customize Legend
handles, labels = ax.get_legend_handles_labels()
# Filter out duplicate handles
by_label = dict(zip(labels, handles))
ax.legend(by_label.values(), by_label.keys(), loc='lower left', frameon=True, facecolor='#f8fafc', edgecolor='#cbd5e1', fontsize=8.5, shadow=False)

plt.tight_layout(pad=2.0)
fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight')
plt.close()
print("Spatial map visualization generated successfully in scratch with optimized label offsets.")
