#!/bin/sh
# Build Firebase Hosting output and publish the current verified snapshot.
set -eu
repo_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
cd "$repo_dir/website"
case "${1:-}" in
    ""|--build-only) ;;
    *) echo "Usage: $0 [--build-only]" >&2; exit 2 ;;
esac
npm run build
python3 "$repo_dir/fccw_spatial_map.py" \
    --db "${FCCW_DB_PATH:-$repo_dir/civic_watchdog.db}" \
    --geojson-only --geojson "$PWD/dist/verified_watchdog.geojson"
if [ "${1:-}" != "--build-only" ]; then
    ./node_modules/.bin/firebase deploy --only hosting --project safehaven-tay --non-interactive
fi
