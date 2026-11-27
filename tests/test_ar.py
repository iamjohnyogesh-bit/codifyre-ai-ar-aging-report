import csv
import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gen_sample_ar
from ar_aging import ArItem, aging, bucket_for, load_items, priority
from ar_cli import main
from ar_dashboard import render

AS_OF = gen_sample_ar.AS_OF


def write_rows(rows, path):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


class ArTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.path = os.path.join(cls.tmp, "ar.csv")
        write_rows(gen_sample_ar.generate(), cls.path)
        cls.items = load_items(cls.path)
        cls.data = aging(cls.items, AS_OF)

    def test_bucket_edges(self):
        for age, name in [(0, "0-30"), (30, "0-30"), (31, "31-60"), (60, "31-60"), (61, "61-90"),
                          (90, "61-90"), (91, "91-120"), (120, "91-120"), (121, "120+"), (-5, "0-30")]:
            self.assertEqual(bucket_for(age), name, age)

    def test_zero_balance_excluded(self):
        self.assertEqual(self.data["summary"]["open_claims"] + self.data["summary"]["closed_or_zero"], 120)
        self.assertGreater(self.data["summary"]["closed_or_zero"], 0)

    def test_bucket_totals_match(self):
        s = self.data["summary"]
        self.assertAlmostEqual(sum(b["balance"] for b in self.data["buckets"]), s["total_balance"], places=1)
        self.assertEqual(sum(b["count"] for b in self.data["buckets"]), s["open_claims"])
        self.assertAlmostEqual(sum(b["pct"] for b in self.data["buckets"]), 100.0, delta=0.5)

    def test_payer_totals_match(self):
        self.assertAlmostEqual(sum(p["balance"] for p in self.data["payers"]),
                               self.data["summary"]["total_balance"], places=1)

    def test_over_90(self):
        expect = sum(i.balance for i in self.items if i.balance > 0.005 and i.age(AS_OF) > 90)
        self.assertAlmostEqual(self.data["summary"]["over_90_balance"], expect, places=2)

    def test_hand_computed_example(self):
        items = [ArItem("A", "P1", "x", date(2026, 11, 17), 100, 100),   # age 10
                 ArItem("B", "P1", "y", date(2026, 7, 29), 300, 300),    # age 121
                 ArItem("C", "P2", "z", date(2026, 11, 1), 50, 0)]       # zero balance
        d = aging(items, AS_OF)
        self.assertEqual(d["summary"]["open_claims"], 2)
        self.assertEqual(d["summary"]["total_balance"], 400.0)
        self.assertEqual(d["summary"]["over_90_balance"], 300.0)
        self.assertEqual(d["summary"]["pct_over_90"], 75.0)
        self.assertEqual(d["summary"]["avg_days_in_ar"], round((100 * 10 + 300 * 121) / 400, 1))
        self.assertEqual(d["buckets"][4]["balance"], 300.0)

    def test_priority_prefers_old_and_large(self):
        old = ArItem("o", "p", "n", date(2026, 6, 1), 500, 500)
        new = ArItem("n", "p", "n", date(2026, 11, 20), 500, 500)
        big = ArItem("b", "p", "n", date(2026, 11, 20), 5000, 5000)
        self.assertGreater(priority(old, AS_OF), priority(new, AS_OF))
        self.assertGreater(priority(big, AS_OF), priority(old, AS_OF))

    def test_worklist_sorted(self):
        w = [x["priority"] for x in self.data["worklist"]]
        self.assertEqual(w, sorted(w, reverse=True))
        self.assertLessEqual(len(w), 15)

    def test_bad_input(self):
        bad = os.path.join(self.tmp, "bad.csv")
        write_rows([{"claim_id": "1", "payer": "A", "patient": "p", "dos": "not-a-date", "billed": "1", "balance": "1"}], bad)
        with self.assertRaises(ValueError):
            load_items(bad)
        miss = os.path.join(self.tmp, "miss.csv")
        write_rows([{"claim_id": "1"}], miss)
        with self.assertRaises(ValueError):
            load_items(miss)

    def test_dashboard(self):
        page = render(self.data)
        for m in ("Codifyre AI", 'id="theme-toggle"', "body.light", "Collector worklist", "try{localStorage"):
            self.assertIn(m, page)

    def test_cli_end_to_end(self):
        out = os.path.join(self.tmp, "o")
        rc = main([self.path, "--as-of", "2026-11-27", "--out", out,
                   "--json", os.path.join(out, "a.json"), "--html", os.path.join(out, "d.html")])
        self.assertEqual(rc, 0)
        for f in ("aging_by_payer.csv", "worklist.csv", "a.json", "d.html"):
            self.assertGreater(os.path.getsize(os.path.join(out, f)), 0, f)
        self.assertEqual(main([os.path.join(self.tmp, "nope.csv")]), 1)


if __name__ == "__main__":
    unittest.main()
