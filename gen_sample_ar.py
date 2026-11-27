#!/usr/bin/env python3
"""Deterministic synthetic open-AR file (as-of 2026-11-27)."""

import csv
import random
from datetime import date, timedelta

AS_OF = date(2026, 11, 27)
PAYERS = {"Medicare": (45, 25), "Aetna": (55, 35), "UnitedHealthcare": (70, 40),
          "BCBS": (50, 30), "Cigna": (80, 45), "Medicaid": (95, 50), "Self-pay": (110, 60)}
STATUSES = ["Submitted", "In process", "Pended - info needed", "Denied - appeal",
            "Patient statement sent", "Awaiting payer response"]
FIRST = ["Anita", "Ravi", "Meera", "John", "Priya", "Karan", "Divya", "Sam", "Neha", "Arjun"]
LAST = ["Rao", "Nair", "Smith", "Shah", "Iyer", "Menon", "Gupta", "Verma", "Das", "Pillai"]


def generate(n=120):
    rng = random.Random(20261127)
    rows = []
    names = list(PAYERS)
    for i in range(1, n + 1):
        payer = rng.choices(names, weights=[5, 4, 4, 4, 3, 3, 2])[0]
        mean, sd = PAYERS[payer]
        age = max(1, int(rng.gauss(mean, sd)))
        billed = rng.choice([120, 180, 260, 340, 480, 720, 950, 1400, 2200])
        balance = round(billed * rng.choice([1, 1, 0.8, 0.6, 0.2]), 2)
        if i % 17 == 0:
            balance = 0.0  # paid in full, must be excluded
        rows.append({
            "claim_id": f"AR{50000 + i}", "payer": payer,
            "patient": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            "dos": (AS_OF - timedelta(days=age)).isoformat(),
            "billed": f"{billed:.2f}", "balance": f"{balance:.2f}",
            "status": rng.choice(STATUSES), "last_action": (AS_OF - timedelta(days=rng.randint(1, min(age, 40)))).isoformat(),
        })
    return rows


def main():
    rows = generate()
    with open("data/sample_ar.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} AR rows to data/sample_ar.csv (as-of {AS_OF})")


if __name__ == "__main__":
    main()
