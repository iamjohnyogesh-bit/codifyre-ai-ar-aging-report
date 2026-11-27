# Codifyre AI - AR Aging Report

> Turn a list of open claim balances into an accounts receivable aging report, payer breakdown and a prioritized collector worklist. Zero dependencies.

**Codifyre AI** builds practical open-source tooling. Day 4 of the daily build series, after [denial analytics](https://github.com/iamjohnyogesh-bit/codifyre-ai-denial-management-analytics), the [claim scrubber](https://github.com/iamjohnyogesh-bit/codifyre-ai-clean-claim-scrubber) and the [ERA 835 parser](https://github.com/iamjohnyogesh-bit/codifyre-ai-era-835-parser). Day 4 answers: how much money is stuck, with whom, and what should we chase first?

## What it does

`ar_cli.py` reads a CSV of claims with open balances and produces:

- **KPIs**: open claims, total AR, average days in AR (balance-weighted), dollars and share over 90 days
- **Aging buckets**: 0-30, 31-60, 61-90, 91-120, 120+ days from date of service
- **Payer breakdown**: balance per bucket, average age and % over 90 days per payer
- **Collector worklist**: top 15 claims ranked by priority (balance x age, boosted past 90 and 120 days)
- Console report, `aging_by_payer.csv`, `worklist.csv`, JSON, and an HTML dashboard (dark default, light toggle remembered per visitor)

Zero-balance rows are excluded and counted. Bad rows (invalid dates, non-numeric amounts, missing columns) raise a clear error listing the row numbers instead of being skipped silently.

## Quickstart

```bash
python3 gen_sample_ar.py        # writes data/sample_ar.csv (120 rows, as-of 2026-11-27)
python3 ar_cli.py data/sample_ar.csv --as-of 2026-11-27 --out out --json out/aging.json --html out/dashboard.html
python3 -m unittest discover -s tests -v   # 11 tests
```

Run it on your own data with `python3 ar_cli.py my_open_claims.csv` (as-of defaults to today).

## Input format

Required columns: `claim_id, payer, patient, dos, billed, balance` (`dos` as YYYY-MM-DD). Optional: `status, last_action`.

## Priority score

`priority = balance x (1 + age_days / 90) x boost`, where boost is 1.0 up to 90 days, 1.5 from 91 to 120 and 2.0 beyond 120. Big old balances rise to the top.

## Sample output

```
Open claims      : 113 (7 zero-balance excluded)
Total AR         : $60,790.00
Avg days in AR   : 70.5
Over 90 days     : $14,560.00 (24.0%)

  0-30      19  $   6,232.00   10.3%
  31-60     35  $  23,196.00   38.2%
  61-90     31  $  16,802.00   27.6%
  91-120    12  $   7,704.00   12.7%
  120+      16  $   6,856.00   11.3%
```

## Layout

```
ar_aging.py       loading, bucketing, summaries, priority ranking
ar_cli.py         CLI, CSV/JSON exports
ar_dashboard.py   HTML dashboard with dark/light toggle
gen_sample_ar.py  deterministic synthetic AR generator
tests/            11 unit tests
data/sample_ar.csv
```

Sample data is synthetic. No real patient information.

## License

MIT, see [LICENSE](LICENSE). Built by **Codifyre AI**.
