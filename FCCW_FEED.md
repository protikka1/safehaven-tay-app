# FCCW daily permit feed

The importer reads LADBS building permit submissions from [DataLA dataset gwh9-jnip](https://data.lacity.org/d/gwh9-jnip).
It checks permit submissions and status changes from the past 30 days inside the watchdog bounds and buffer.
For a longer catch-up window, run the importer with `--days N`. Use [ZIMAS](https://planning.lacity.gov/zoning/zoning-search) to review parcel and zoning information.
The LADBS permit feed does not establish affordability or SRO replacement obligations.

## First run

From the repository root, using Python 3 and the website's supported Node version:

```sh
python3 fccw_api_monitor-v3.py
python3 fccw_watchdog.py list
npm --prefix website ci
sh fccw_publish.sh --build-only
```

The migration opens or creates `civic_watchdog.db` beside the scripts. Use `--db` to override
the importer and review CLI path, and set `FCCW_DB_PATH` to the same absolute path when publishing.
Keep the database and reviewer notes on the review machine. Firebase receives the build and verified GeoJSON.

## Review and publish

```sh
python3 fccw_watchdog.py verify RECORD_UUID --decision VERIFIED --reviewer "Reviewer name"
./website/node_modules/.bin/firebase login
sh fccw_publish.sh
```

Repeat the publish command after review to update the live cards immediately. The deploy command
targets Hosting only for project `safehaven-tay`.

## Daily job

On the Mac or other always-on review machine, set up the following in `crontab -e`.
Replace the example checkout path and set `PATH` to include the directories containing your Python, Node and npm binaries.
This example fetches every day at 6 a.m. in the machine's local time and refreshes Hosting
after a successful import using that machine's Firebase credentials.

```cron
PATH=/usr/local/bin:/usr/bin:/bin
0 6 * * * cd /absolute/path/to/safehaven-tay-app && python3 fccw_api_monitor-v3.py && sh fccw_publish.sh
```

For Termux, run the same commands from a Termux scheduler job script, using the same database
file as the reviewer. A failed import exits with an error and skips deployment in the command
chain above. Freshly imported or changed permits stay pending until a reviewer approves them.

## Batch review

Generate a dated local report from the pending LADBS queue:

```sh
FCCW_REPORT="fccw-review-$(date +%Y%m%d-%H%M%S).json"
python3 fccw_review.py check --report "$FCCW_REPORT"
```

The report checks the current DataLA permit against the stored permit, the DataLA APN against
LA County parcel polygons at the permit coordinates, and the DataLA zoning text against the
LA City Planning public zoning layer. `CANDIDATE` means those comparisons agreed. It remains
pending in SQLite until a reviewer acts. Open ZIMAS for zoning differences, missing data and
ambiguous parcels. The zoning layer is a cross-check and the report does not decide legal
compliance.

After reading the report, approve selected UUIDs or explicitly approve all candidates in that report:

```sh
python3 fccw_review.py approve --report "$FCCW_REPORT" --reviewer "Reviewer name" --id RECORD_UUID
python3 fccw_review.py approve --report "$FCCW_REPORT" --reviewer "Reviewer name" --all-matches
```

Use one approval command per selection. Repeat `--id` to approve several selected UUIDs.
Approvals are rejected if the report is older than 24 hours or a selected record changed.
Publish with `sh fccw_publish.sh` after approval.
