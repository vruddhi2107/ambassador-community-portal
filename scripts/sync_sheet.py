#!/usr/bin/env python3
"""
On2Cook Ambassador Portal — Google Sheet sync
------------------------------------------------
Pulls the ambassador roster from a published Google Sheet (CSV export)
and regenerates the two data files the portal reads from:

    data/ambassadors.json        -> used when the site is served over http(s)
    js/ambassadors-data.js       -> same data, inlined as a JS global, used as
                                     an automatic offline fallback so the site
                                     also works when someone just double-clicks
                                     index.html (no server, fetch() unavailable)

How to point this at your sheet
--------------------------------
1. In Google Sheets: File -> Share -> Publish to web.
2. Choose the correct tab, select "Comma-separated values (.csv)", click Publish.
3. Copy the generated URL (looks like:
   https://docs.google.com/spreadsheets/d/e/2PACX-.../pub?gid=0&single=true&output=csv)
4. Set it as the GOOGLE_SHEET_CSV_URL secret/variable in the GitHub repo running
   the sync workflow (see .github/workflows/sync-sheet.yml), or export it as an
   env var when running this script locally.

Privacy note
------------
Contact Number and E-mail are personal data. This portal includes them by
default (set here per your instructions), so anyone with the site's URL can
read whatever ends up in data/ambassadors.json. If this ever gets deployed
somewhere fully public and you'd rather not publish phone/email, set
INCLUDE_CONTACT_INFO=false when running this script.
"""

import csv
import io
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config (env vars, all optional except the sheet URL)
# ---------------------------------------------------------------------------
SHEET_CSV_URL = os.environ.get("GOOGLE_SHEET_CSV_URL", "").strip()
INCLUDE_CONTACT_INFO = os.environ.get("INCLUDE_CONTACT_INFO", "true").strip().lower() == "true"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_OUT = os.path.join(REPO_ROOT, "data", "ambassadors.json")
JS_OUT = os.path.join(REPO_ROOT, "js", "ambassadors-data.js")

# ---------------------------------------------------------------------------
# Header normalisation — tolerant of the exact wording/whitespace used in the
# source sheet ("City " with a trailing space, "Profile." with a period, etc.)
# ---------------------------------------------------------------------------
HEADER_MAP = {
    "sr no": "srNo",
    "sr. no": "srNo",
    "sr.no": "srNo",
    "srno": "srNo",
    "name": "name",
    "brand name": "brandName",
    "billing name": "billingName",
    "ambassador code": "code",
    "city": "city",
    "state": "state",
    "contact number": "phone",
    "phone": "phone",
    "phone number": "phone",
    "e-mail": "email",
    "email": "email",
    "e mail": "email",
    "profile": "profile",

    # --- Optional extra columns -------------------------------------------
    # None of these are required. Add any of them to your sheet (spelled
    # roughly as below — matching is case/whitespace/punctuation tolerant)
    # and the portal will automatically start showing that section on the
    # ambassador's profile. Leave a column out entirely and that section
    # just doesn't render — nothing is ever faked.
    "instagram": "instagram",
    "facebook": "facebook",
    "whatsapp": "whatsapp",
    "whatsapp number": "whatsapp",
    "kitchen type": "kitchenType",
    "operational since": "operationalSince",
    "services offered": "servicesOffered",
    "coverage areas": "coverageAreas",
    "specialties": "specialties",
    "specialities": "specialties",
    "happy customers": "happyCustomers",
    "dishes served": "dishesServed",
    "rating": "rating",
    "customer rating": "rating",
    "profile url": "profileUrl",
    "profile link": "profileUrl",
    "photo url": "photoUrl",
    "photo": "photoUrl",
}


def normalise_header(h):
    h = h.strip().lower()
    h = h.rstrip(".")
    h = re.sub(r"\s+", " ", h)
    return h


def fetch_csv(url):
    req = urllib.request.Request(url, headers={"User-Agent": "on2cook-ambassador-sync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    return raw.decode("utf-8-sig")


def parse_records(csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    field_lookup = {}
    for raw_header in reader.fieldnames or []:
        key = normalise_header(raw_header)
        if key in HEADER_MAP:
            field_lookup[raw_header] = HEADER_MAP[key]

    missing = {"name", "city", "state", "code"} - set(field_lookup.values())
    if missing:
        print(f"WARNING: sheet is missing expected column(s): {sorted(missing)}", file=sys.stderr)

    records = []
    sr_fallback = 0
    for row in reader:
        sr_fallback += 1
        record = {}
        for raw_header, field in field_lookup.items():
            value = (row.get(raw_header) or "").strip()
            record[field] = value

        # Skip fully blank rows
        if not any(record.values()):
            continue
        if not record.get("name") and not record.get("code"):
            continue

        record.setdefault("srNo", sr_fallback)
        if record.get("srNo"):
            try:
                record["srNo"] = int(str(record["srNo"]).strip())
            except ValueError:
                record["srNo"] = sr_fallback

        if not INCLUDE_CONTACT_INFO:
            record.pop("phone", None)
            record.pop("email", None)

        base_fields = ("name", "brandName", "billingName", "code", "city", "state", "profile")
        optional_fields = (
            "instagram", "facebook", "whatsapp", "kitchenType", "operationalSince",
            "servicesOffered", "coverageAreas", "specialties", "happyCustomers",
            "dishesServed", "rating", "profileUrl", "photoUrl",
        )
        for field in base_fields + optional_fields:
            record.setdefault(field, "")

        records.append(record)

    records.sort(key=lambda r: r.get("srNo", 0))
    return records


def write_outputs(records):
    os.makedirs(os.path.dirname(JSON_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(JS_OUT), exist_ok=True)

    payload = {
        "_meta": {
            "syncedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "Google Sheets",
            "count": len(records),
            "includesContactInfo": INCLUDE_CONTACT_INFO,
        },
        "ambassadors": records,
    }

    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(JS_OUT, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by scripts/sync_sheet.py — do not edit by hand.\n")
        f.write("// Loaded as a fallback so the portal also works without a web server.\n")
        f.write("window.AMBASSADORS_FALLBACK = ")
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    print(f"Wrote {len(records)} ambassador records to:")
    print(f"  {JSON_OUT}")
    print(f"  {JS_OUT}")


def main():
    if not SHEET_CSV_URL:
        print(
            "ERROR: GOOGLE_SHEET_CSV_URL is not set.\n"
            "Publish your Google Sheet tab to the web as CSV and set the URL as an\n"
            "env var / GitHub Actions secret. See the docstring at the top of this file.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Fetching sheet CSV from: {SHEET_CSV_URL}")
    csv_text = fetch_csv(SHEET_CSV_URL)
    records = parse_records(csv_text)
    if not records:
        print("ERROR: parsed 0 ambassador records — check the sheet URL/headers.", file=sys.stderr)
        sys.exit(1)
    write_outputs(records)


if __name__ == "__main__":
    main()
