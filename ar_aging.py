"""Core AR aging logic: load open-claim balances, bucket by age, summarize, prioritize."""

import csv
from dataclasses import dataclass
from datetime import date, datetime

BUCKETS = [("0-30", 0, 30), ("31-60", 31, 60), ("61-90", 61, 90),
           ("91-120", 91, 120), ("120+", 121, 10**6)]
REQUIRED = ["claim_id", "payer", "patient", "dos", "billed", "balance"]


@dataclass
class ArItem:
    claim_id: str
    payer: str
    patient: str
    dos: date
    billed: float
    balance: float
    status: str = ""
    last_action: str = ""

    def age(self, as_of):
        return (as_of - self.dos).days


def bucket_for(age):
    for name, lo, hi in BUCKETS:
        if lo <= age <= hi:
            return name
    return BUCKETS[0][0]  # negative age (future DOS) treated as current


def parse_date(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def load_items(path):
    """Read a CSV; raises ValueError listing bad rows rather than skipping silently."""
    items, errors = [], []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("CSV is missing required column(s): " + ", ".join(missing))
        for n, row in enumerate(reader, start=2):
            try:
                items.append(ArItem(
                    claim_id=row["claim_id"].strip(), payer=row["payer"].strip() or "Unknown",
                    patient=row["patient"].strip(), dos=parse_date(row["dos"]),
                    billed=float(row["billed"]), balance=float(row["balance"]),
                    status=(row.get("status") or "").strip(),
                    last_action=(row.get("last_action") or "").strip()))
            except (ValueError, KeyError) as exc:
                errors.append(f"row {n}: {exc}")
    if errors:
        raise ValueError("Bad rows:\n  " + "\n  ".join(errors))
    return items


def aging(items, as_of):
    """Return the full analysis dict."""
    open_items = [i for i in items if i.balance > 0.005]
    totals = {b[0]: {"bucket": b[0], "count": 0, "balance": 0.0} for b in BUCKETS}
    payers = {}
    for it in open_items:
        b = bucket_for(it.age(as_of))
        totals[b]["count"] += 1
        totals[b]["balance"] += it.balance
        p = payers.setdefault(it.payer, {"payer": it.payer, "count": 0, "balance": 0.0,
                                         "weighted_age": 0.0,
                                         **{x[0]: 0.0 for x in BUCKETS}})
        p["count"] += 1
        p["balance"] += it.balance
        p["weighted_age"] += it.balance * it.age(as_of)
        p[b] += it.balance
    total_bal = sum(i.balance for i in open_items)
    over90 = sum(i.balance for i in open_items if i.age(as_of) > 90)
    for p in payers.values():
        p["avg_days"] = round(p["weighted_age"] / p["balance"], 1) if p["balance"] else 0.0
        p["pct_over_90"] = round(100 * (p["91-120"] + p["120+"]) / p["balance"], 1) if p["balance"] else 0.0
        del p["weighted_age"]
        for k in [x[0] for x in BUCKETS] + ["balance"]:
            p[k] = round(p[k], 2)
    buckets = []
    for b in BUCKETS:
        row = totals[b[0]]
        row["balance"] = round(row["balance"], 2)
        row["pct"] = round(100 * row["balance"] / total_bal, 1) if total_bal else 0.0
        buckets.append(row)
    avg_days = (sum(i.balance * i.age(as_of) for i in open_items) / total_bal) if total_bal else 0.0
    return {
        "as_of": as_of.isoformat(),
        "summary": {
            "open_claims": len(open_items),
            "total_balance": round(total_bal, 2),
            "over_90_balance": round(over90, 2),
            "pct_over_90": round(100 * over90 / total_bal, 1) if total_bal else 0.0,
            "avg_days_in_ar": round(avg_days, 1),
            "closed_or_zero": len(items) - len(open_items),
        },
        "buckets": buckets,
        "payers": sorted(payers.values(), key=lambda p: -p["balance"]),
        "worklist": worklist(open_items, as_of),
    }


def priority(item, as_of):
    """Higher = work first: dollars weighted by age, boosted past 90 days."""
    age = item.age(as_of)
    boost = 2.0 if age > 120 else 1.5 if age > 90 else 1.0
    return round(item.balance * (1 + age / 90.0) * boost, 2)


def worklist(open_items, as_of, limit=15):
    ranked = sorted(open_items, key=lambda i: -priority(i, as_of))[:limit]
    return [{"claim_id": i.claim_id, "payer": i.payer, "patient": i.patient,
             "age_days": i.age(as_of), "bucket": bucket_for(i.age(as_of)),
             "balance": round(i.balance, 2), "status": i.status,
             "priority": priority(i, as_of)} for i in ranked]
