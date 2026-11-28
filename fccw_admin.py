#!/usr/bin/env python3
"""Review watchdog records in a browser on the review machine."""

import argparse
from contextlib import closing
import json
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import secrets
import sqlite3
from urllib.parse import parse_qs

from fccw_watchdog import DEFAULT_DB_PATH, SROLedgerEngine
from fccw_review import fingerprint


def review_card(row, token):
    warnings = json.loads(row["audit_warnings"] or "[]")
    warning_html = "".join(f"<li>{escape(str(warning))}</li>" for warning in warnings)
    return f"""
    <article>
      <h2>{escape(row["project_name"])}</h2>
      <p>{escape(row["external_case_id"])} · {escape(row["feed_source"])}
        · {escape(row["audit_status"])}</p>
      <p>Record ID: <code>{escape(row["id"])}</code></p>
      <ul>{warning_html}</ul>
      <form method="post" action="/admin/">
        <input type="hidden" name="token" value="{token.decode()}">
        <input type="hidden" name="id" value="{escape(row["id"])}">
        <input type="hidden" name="version" value="{fingerprint(row)}">
        <label>Verification notes
          <textarea name="notes" required maxlength="2000"
            placeholder="Official source and case or permit number"></textarea>
        </label>
        <button name="decision" value="VERIFIED">Verify</button>
        <button name="decision" value="DISMISSED">Dismiss</button>
      </form>
    </article>"""


class ReviewHandler(BaseHTTPRequestHandler):
    def check_route(self):
        if self.headers.get("Host") != self.server.host_header:
            self.send_error(HTTPStatus.FORBIDDEN)
            return False
        if self.path != "/admin/":
            self.send_error(HTTPStatus.NOT_FOUND)
            return False
        return True

    def do_GET(self):
        if not self.check_route():
            return
        with closing(SROLedgerEngine(self.server.db).conn) as conn:
            rows = conn.execute("""
                SELECT * FROM gis_live_feeds WHERE verification_status = 'PENDING_REVIEW'
                ORDER BY ingested_at DESC, id
            """).fetchall()
        content = "".join(review_card(dict(row), self.server.token) for row in rows)
        content = content or "<p>No pending GIS records.</p>"
        page = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SafeHaven Community | Housing Watch Admin</title>
<style>
  body {{ font: 1rem system-ui, sans-serif; color: #102f37; background: #f3f6f5;
    max-width: 50rem; padding: 1rem; margin: auto; }}
  article {{ background: white; border: 1px solid #acbdbd; border-radius: .5rem;
    padding: 1rem; margin-block: 1rem; overflow-wrap: anywhere; }}
  h2 {{ margin-top: 0; }}
  textarea {{ box-sizing: border-box; display: block; width: 100%; min-height: 5rem;
    font: inherit; margin-block: .5rem; }}
  button {{ font: inherit; padding: .5rem 1rem; margin: .25rem; cursor: pointer; }}
</style>
<main>
<h1>Housing Watch Admin</h1>
<p>Reviewer: {escape(self.server.reviewer)}</p>
<p>Compare each record with its official source before saving a decision.
  Run the Hosting publish script to update the public map after review.</p>
<h2>Pending review ({len(rows)})</h2>
{content}
</main>
</html>""".encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; style-src 'unsafe-inline'; "
                         "form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        if not self.check_route():
            return
        if self.headers.get("Origin") != f"http://{self.server.host_header}":
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if self.headers.get_content_type() != "application/x-www-form-urlencoded":
            self.send_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 32_768:
                raise ValueError
            data = parse_qs(self.rfile.read(length).decode(), max_num_fields=5)
            token, record_id, version, decision, notes = (
                data[key][0] for key in ("token", "id", "version", "decision", "notes")
            )
            notes = notes.strip()
            if decision not in ("VERIFIED", "DISMISSED") or not 0 < len(notes) <= 2000:
                raise ValueError
        except (KeyError, ValueError):
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid review")
            return
        if not secrets.compare_digest(self.server.token, token.encode()):
            self.send_error(HTTPStatus.FORBIDDEN)
            return

        try:
            ledger = SROLedgerEngine(self.server.db)
            with closing(ledger.conn), ledger.conn:
                ledger.conn.execute("BEGIN IMMEDIATE")
                current = ledger.conn.execute(
                    "SELECT * FROM gis_live_feeds WHERE id = ?", (record_id,)
                ).fetchone()
                if (current is None or current["verification_status"] != "PENDING_REVIEW"
                        or fingerprint(dict(current)) != version):
                    self.send_error(HTTPStatus.CONFLICT, "Record changed. Reload the queue.")
                    return
                ledger.verify_gis_record(record_id, self.server.reviewer, decision, notes)
        except sqlite3.Error:
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Unable to save review. Try again.")
            return
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/admin/")
        self.end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not args.db.is_file() or not args.reviewer.strip():
        parser.error("Use an existing database and provide a reviewer name.")
    with HTTPServer(("127.0.0.1", args.port), ReviewHandler) as server:
        server.db = args.db.resolve()
        server.reviewer = args.reviewer.strip()
        server.token = secrets.token_hex(32).encode()
        server.host_header = f"127.0.0.1:{server.server_port}"
        print(f"Open http://{server.host_header}/admin/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
