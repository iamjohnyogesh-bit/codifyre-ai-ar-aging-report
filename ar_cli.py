#!/usr/bin/env python3
"""Codifyre AI - AR Aging Report CLI.

    python3 ar_cli.py data/sample_ar.csv --as-of 2026-11-27 --out out --json out/aging.json --html out/dashboard.html
"""

import argparse
import csv
import json
import os
import sys
from datetime import date

from ar_aging import aging, load_items, parse_date


def write_csv(path, rows):
    rows = list(rows)
    if not rows:
        return 0
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def console(data):
    s = data["summary"]
    print("=" * 66)
    print(f"AR AGING REPORT - as of {data['as_of']}")
    print("=" * 66)
    print(f"Open claims      : {s['open_claims']} ({s['closed_or_zero']} zero-balance excluded)")
    print(f"Total AR         : ${s['total_balance']:,.2f}")
    print(f"Avg days in AR   : {s['avg_days_in_ar']}")
    print(f"Over 90 days     : ${s['over_90_balance']:,.2f} ({s['pct_over_90']}%)")
    print("\n-- By age bucket " + "-" * 49)
    for b in data["buckets"]:
        bar = "#" * int(b["pct"] / 2)
        print(f"  {b['bucket']:<7} {b['count']:>4}  ${b['balance']:>11,.2f}  {b['pct']:>5}%  {bar}")
    print("\n-- By payer " + "-" * 54)
    for p in data["payers"]:
        print(f"  {p['payer'][:18]:<18} ${p['balance']:>11,.2f}  avg {p['avg_days']:>5}d  >90: {p['pct_over_90']}%")
    print("\n-- Top 5 worklist " + "-" * 48)
    for w in data["worklist"][:5]:
        print(f"  {w['claim_id']}  {w['payer'][:14]:<14} {w['age_days']:>4}d  ${w['balance']:>9,.2f}  {w['status']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="AR aging report")
    ap.add_argument("file")
    ap.add_argument("--as-of", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--out", help="directory for payer/worklist CSVs")
    ap.add_argument("--json")
    ap.add_argument("--html")
    args = ap.parse_args(argv)
    try:
        as_of = parse_date(args.as_of) if args.as_of else date.today()
        items = load_items(args.file)
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    data = aging(items, as_of)
    console(data)
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        write_csv(os.path.join(args.out, "aging_by_payer.csv"), data["payers"])
        write_csv(os.path.join(args.out, "worklist.csv"), data["worklist"])
        print(f"\nCSV written to {args.out}/")
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    if args.html:
        from ar_dashboard import render
        os.makedirs(os.path.dirname(os.path.abspath(args.html)), exist_ok=True)
        with open(args.html, "w", encoding="utf-8") as fh:
            fh.write(render(data))
        print(f"Dashboard written to {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
