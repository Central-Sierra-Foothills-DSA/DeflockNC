#!/usr/bin/env python3
"""
Analyze Flock Safety Network Audit CSV files for NC PD.
Reads base64-encoded JSON files saved from the Google Drive MCP tool.
"""

import base64
import csv
import io
import json
import os
import glob
from collections import defaultdict

# ─── helpers ────────────────────────────────────────────────────────────────

CALIFORNIA_KEYWORDS = [
    " CA ", " CA,", " CA.", "(CA)", "California", " CA$"
]

# Agencies that are clearly NOT California even if they contain "CA"
NON_CA_OVERRIDES = []  # filled by context

FEDERAL_KEYWORDS = [
    "ATF", "FBI", "HSI", "CBP", "Border Patrol", "ICE ", " ICE",
    "DEA", "NCIS", "Air Force", "Army", "Navy", "Marines",
    "National Park", "Postal Inspection", "GSA", "Secret Service",
    "U.S. Marshals", "US Marshals", "Marshal", "Homeland Security",
    "Department of Justice", "DOJ", "DHS", "USBP", "Customs",
    "Immigration", "Drug Enforcement", "Alcohol Tobacco",
    "Federal Bureau", "Fugitive"
]

IMMIGRATION_KEYWORDS = [
    "HSI", "CBP", "Border Patrol", "ICE", "USBP", "Fugitive",
    "Immigration", "Customs and Border", "Homeland Security Investigations"
]

def is_california(org_name):
    """Return True if org appears to be a California agency."""
    org = org_name.strip()
    # Check for explicit CA state abbreviation patterns
    if " CA " in org or org.endswith(" CA") or " CA," in org or "(CA)" in org:
        return True
    if "California" in org:
        return True
    return False

def is_federal(org_name):
    org = org_name.strip().upper()
    for kw in FEDERAL_KEYWORDS:
        if kw.upper() in org:
            return True
    return False

def is_immigration(org_name):
    org = org_name.strip().upper()
    for kw in IMMIGRATION_KEYWORDS:
        if kw.upper() in org:
            return True
    return False

def parse_csv_content(csv_text, file_label):
    """Parse the CSV text (with multi-line Time Frame rows) and return list of row dicts."""
    reader = csv.reader(io.StringIO(csv_text))
    rows = []
    headers = None
    for row in reader:
        if headers is None:
            headers = [h.strip() for h in row]
            continue
        if len(row) == 0:
            continue
        # Map to dict; if row is shorter than headers, pad with empty strings
        while len(row) < len(headers):
            row.append("")
        row_dict = {headers[i]: row[i].strip() for i in range(len(headers))}
        rows.append(row_dict)
    return rows

def analyze_rows(rows, file_label):
    """Analyze a list of row dicts and return a results dict."""
    total = len(rows)
    orgs = defaultdict(int)
    out_of_state = defaultdict(int)
    federal = defaultdict(int)
    immigration = defaultdict(int)
    reasons = defaultdict(int)
    protest_rows = []
    search_times = []

    for row in rows:
        org = row.get("Org Name", "").strip()
        reason = row.get("Reason", "").strip()
        search_time = row.get("Search Time", "").strip()

        if org:
            orgs[org] += 1

        # Out of state = not California
        if org and not is_california(org):
            out_of_state[org] += 1

        if org and is_federal(org):
            federal[org] += 1

        if org and is_immigration(org):
            immigration[org] += 1

        if reason:
            reasons[reason] += 1

        if reason and "protest" in reason.lower():
            protest_rows.append({
                "org": org,
                "reason": reason,
                "time": search_time,
                "plate": row.get("License Plate", "").strip(),
                "case": row.get("Case #", "").strip(),
            })

        if search_time:
            search_times.append(search_time)

    return {
        "file": file_label,
        "total_searches": total,
        "unique_orgs": dict(orgs),
        "out_of_state": dict(out_of_state),
        "federal": dict(federal),
        "immigration": dict(immigration),
        "reasons": dict(reasons),
        "protest_rows": protest_rows,
        "search_times": search_times,
    }


def process_json_file(path, file_label):
    """Load a saved MCP tool-result JSON file and parse the CSV inside."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        content_b64 = data.get("content", "")
        if not content_b64:
            print(f"  [WARN] No content field in {path}")
            return None
        csv_bytes = base64.b64decode(content_b64)
        csv_text = csv_bytes.decode("utf-8", errors="replace")
        rows = parse_csv_content(csv_text, file_label)
        print(f"  Parsed {len(rows)} rows from {file_label}")
        return analyze_rows(rows, file_label)
    except Exception as e:
        print(f"  [ERROR] Failed to process {file_label}: {e}")
        return None


# ─── main ───────────────────────────────────────────────────────────────────

def main():
    tool_results_dir = "/Users/maxwellpingeon/.claude/projects/-Users-maxwellpingeon-Documents-DeflockNC/95626d8a-a0f4-49db-8816-8e5ab569624a/tool-results"

    # Map each file_id to a label
    file_map = {
        "mcp-d2869d70-7153-4569-adac-6649591a78a9-download_file_content-1782251772747.txt": "Feb 2024",
    }

    # Find all download_file_content result files
    pattern = os.path.join(tool_results_dir, "mcp-d2869d70-7153-4569-adac-6649591a78a9-download_file_content-*.txt")
    found_files = sorted(glob.glob(pattern))
    print(f"Found {len(found_files)} tool-result files in {tool_results_dir}")
    for f in found_files:
        print(f"  {os.path.basename(f)}")

    results_by_label = {}

    for path in found_files:
        basename = os.path.basename(path)
        label = file_map.get(basename, basename)
        print(f"\nProcessing: {label} ({basename})")
        result = process_json_file(path, label)
        if result:
            results_by_label[label] = result

    # ─── Aggregate ───────────────────────────────────────────────────────────
    print("\n" + "="*80)
    print("PER-FILE RESULTS")
    print("="*80)

    all_orgs = defaultdict(int)
    all_out_of_state = defaultdict(int)
    all_federal = defaultdict(int)
    all_immigration = defaultdict(int)
    all_reasons = defaultdict(int)
    all_protest_rows = []
    grand_total_searches = 0
    all_search_times = []

    for label, r in sorted(results_by_label.items()):
        print(f"\n{'─'*60}")
        print(f"FILE: {label}")
        print(f"  Total searches: {r['total_searches']:,}")
        print(f"  Unique orgs: {len(r['unique_orgs'])}")
        print(f"  Out-of-state orgs: {len(r['out_of_state'])}")
        print(f"  Federal agencies: {len(r['federal'])}")
        print(f"  Immigration-related agencies: {len(r['immigration'])}")
        print(f"  Protest searches: {len(r['protest_rows'])}")

        if r['out_of_state']:
            print(f"  Out-of-state agencies:")
            for org, cnt in sorted(r['out_of_state'].items(), key=lambda x: -x[1]):
                fed_flag = " [FEDERAL]" if is_federal(org) else ""
                imm_flag = " [IMMIGRATION]" if is_immigration(org) else ""
                print(f"    {cnt:>5}  {org}{fed_flag}{imm_flag}")

        if r['federal']:
            print(f"  Federal agencies:")
            for org, cnt in sorted(r['federal'].items(), key=lambda x: -x[1]):
                print(f"    {cnt:>5}  {org}")

        if r['protest_rows']:
            print(f"  Protest searches:")
            for p in r['protest_rows']:
                print(f"    Org: {p['org']} | Reason: {p['reason']} | Time: {p['time']} | Case: {p['case']}")

        print(f"  Reasons:")
        for reason, cnt in sorted(r['reasons'].items(), key=lambda x: -x[1]):
            print(f"    {cnt:>5}  {reason}")

        # Accumulate
        grand_total_searches += r['total_searches']
        for org, cnt in r['unique_orgs'].items():
            all_orgs[org] += cnt
        for org, cnt in r['out_of_state'].items():
            all_out_of_state[org] += cnt
        for org, cnt in r['federal'].items():
            all_federal[org] += cnt
        for org, cnt in r['immigration'].items():
            all_immigration[org] += cnt
        for reason, cnt in r['reasons'].items():
            all_reasons[reason] += cnt
        all_protest_rows.extend(r['protest_rows'])
        all_search_times.extend(r['search_times'])

    # ─── Grand Summary ───────────────────────────────────────────────────────
    print("\n" + "="*80)
    print("GRAND SUMMARY — ALL FILES COMBINED")
    print("="*80)
    print(f"\nFiles processed: {len(results_by_label)}")
    print(f"Grand total searches: {grand_total_searches:,}")
    print(f"Grand unique agencies: {len(all_orgs)}")
    print(f"Out-of-state agencies: {len(all_out_of_state)}")
    print(f"Federal agencies: {len(all_federal)}")
    print(f"Immigration agencies: {len(all_immigration)}")

    print(f"\n{'─'*60}")
    print("ALL OUT-OF-STATE AGENCIES (sorted by search count):")
    for org, cnt in sorted(all_out_of_state.items(), key=lambda x: -x[1]):
        fed_flag = " [FEDERAL]" if is_federal(org) else ""
        imm_flag = " [IMMIGRATION]" if is_immigration(org) else ""
        print(f"  {cnt:>5}  {org}{fed_flag}{imm_flag}")

    print(f"\n{'─'*60}")
    print("ALL FEDERAL AGENCIES (sorted by search count):")
    for org, cnt in sorted(all_federal.items(), key=lambda x: -x[1]):
        imm_flag = " [IMMIGRATION]" if is_immigration(org) else ""
        print(f"  {cnt:>5}  {org}{imm_flag}")

    print(f"\n{'─'*60}")
    print("ALL IMMIGRATION ENFORCEMENT AGENCIES:")
    total_immigration = sum(all_immigration.values())
    for org, cnt in sorted(all_immigration.items(), key=lambda x: -x[1]):
        print(f"  {cnt:>5}  {org}")
    print(f"  TOTAL IMMIGRATION SEARCHES: {total_immigration:,}")

    print(f"\n{'─'*60}")
    print("ALL UNIQUE REASON VALUES:")
    for reason, cnt in sorted(all_reasons.items(), key=lambda x: -x[1]):
        print(f"  {cnt:>5}  {reason}")

    print(f"\n{'─'*60}")
    print("ALL PROTEST-RELATED SEARCHES:")
    if all_protest_rows:
        for p in all_protest_rows:
            print(f"  Org: {p['org']} | Reason: {p['reason']} | Time: {p['time']} | Case: {p['case']}")
    else:
        print("  None found.")

    print(f"\n{'─'*60}")
    print("ALL AGENCIES (complete list, sorted by search count):")
    for org, cnt in sorted(all_orgs.items(), key=lambda x: -x[1]):
        flags = []
        if not is_california(org):
            flags.append("OUT-OF-STATE")
        if is_federal(org):
            flags.append("FEDERAL")
        if is_immigration(org):
            flags.append("IMMIGRATION")
        flag_str = f"  [{', '.join(flags)}]" if flags else ""
        print(f"  {cnt:>5}  {org}{flag_str}")

    if all_search_times:
        sorted_times = sorted(all_search_times)
        print(f"\n{'─'*60}")
        print(f"Date range: {sorted_times[0]} → {sorted_times[-1]}")


if __name__ == "__main__":
    main()
