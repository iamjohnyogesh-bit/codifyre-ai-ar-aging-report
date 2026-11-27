"""Self-contained HTML dashboard (dark default, light toggle) for AR aging."""

import html


def esc(s):
    return html.escape(str(s))


def money(v):
    return f"${v:,.2f}"


CSS = """
:root{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#8b949e;--acc:#58a6ff;--bad:#f85149;--warn:#d29922;--ok:#3fb950;--bd:#30363d}
body.light{--bg:#f6f8fa;--card:#fff;--fg:#1f2328;--mut:#59636e;--acc:#0969da;--bad:#cf222e;--warn:#9a6700;--ok:#1a7f37;--bd:#d0d7de}
*{box-sizing:border-box}body{margin:0;font:14px system-ui,sans-serif;background:var(--bg);color:var(--fg)}
header{display:flex;justify-content:space-between;align-items:center;padding:18px 28px;border-bottom:1px solid var(--bd)}
h1{font-size:18px;margin:0}h2{font-size:13px;margin:0 0 12px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
button{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:6px;padding:6px 12px;cursor:pointer}
main{padding:24px 28px;display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(380px,1fr))}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px}.wide{grid-column:1/-1}
.kpis{grid-column:1/-1;display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}
.kpi b{display:block;font-size:24px;margin-top:4px}.muted{color:var(--mut)}
.col{display:flex;align-items:flex-end;gap:14px;height:190px;padding-top:10px}
.col div{flex:1;text-align:center;display:flex;flex-direction:column;justify-content:flex-end;height:100%}
.col i{display:block;border-radius:4px 4px 0 0;background:var(--acc)}.col .o i{background:var(--warn)}.col .r i{background:var(--bad)}
.col small{color:var(--mut)}
table{width:100%;border-collapse:collapse}td,th{padding:6px 6px;border-bottom:1px solid var(--bd);text-align:left;white-space:nowrap}
td.n,th.n{text-align:right}.bad{color:var(--bad)}.warn{color:var(--warn)}
.scroll{overflow-x:auto}footer{padding:18px 28px;color:var(--mut)}
"""

JS = """
const b=document.body,t=document.getElementById('theme-toggle');
function get(){try{return localStorage.getItem('codifyre-theme')}catch(e){return null}}
function put(v){try{localStorage.setItem('codifyre-theme',v)}catch(e){}}
function lbl(){t.textContent=b.classList.contains('light')?'\\u263E Dark':'\\u2600 Light'}
if(get()==='light')b.classList.add('light');
lbl();
t.addEventListener('click',function(){b.classList.toggle('light');put(b.classList.contains('light')?'light':'dark');lbl()});
"""


def render(data):
    s = data["summary"]
    kpis = [("Open claims", s["open_claims"]), ("Total AR", money(s["total_balance"])),
            ("Avg days in AR", s["avg_days_in_ar"]), ("Over 90 days", money(s["over_90_balance"])),
            ("% over 90", f"{s['pct_over_90']}%")]
    kpi_html = "".join(f"<div class='card kpi'><span class='muted'>{esc(k)}</span><b>{esc(v)}</b></div>" for k, v in kpis)
    top = max((b["balance"] for b in data["buckets"]), default=0) or 1
    cols = []
    for idx, b in enumerate(data["buckets"]):
        h = max(2, int(150 * b["balance"] / top))
        cls = "r" if idx == len(data["buckets"]) - 1 else "o" if idx == len(data["buckets"]) - 2 else ""
        cols.append(f"<div class='{cls}'><small>{money(b['balance'])}<br>{b['pct']}%</small>"
                    f"<i style='height:{h}px'></i><small>{esc(b['bucket'])}</small></div>")
    bucket_names = [b["bucket"] for b in data["buckets"]]
    head = "".join(f"<th class='n'>{esc(n)}</th>" for n in bucket_names)
    prow = "".join(
        f"<tr><td>{esc(p['payer'])}</td>" + "".join(f"<td class='n'>{money(p[n])}</td>" for n in bucket_names) +
        f"<td class='n'><b>{money(p['balance'])}</b></td><td class='n'>{p['avg_days']}</td>"
        f"<td class='n {'bad' if p['pct_over_90'] > 30 else 'warn' if p['pct_over_90'] > 15 else ''}'>{p['pct_over_90']}%</td></tr>"
        for p in data["payers"])
    wrow = "".join(
        f"<tr><td>{esc(w['claim_id'])}</td><td>{esc(w['payer'])}</td><td>{esc(w['patient'])}</td>"
        f"<td class='n'>{w['age_days']}</td><td>{esc(w['bucket'])}</td><td class='n'>{money(w['balance'])}</td>"
        f"<td>{esc(w['status'])}</td></tr>" for w in data["worklist"])
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Codifyre AI - AR Aging Report</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>{CSS}</style></head><body>
<header><h1>Codifyre AI &middot; AR Aging Report <span class="muted">as of {esc(data['as_of'])}</span></h1><button id="theme-toggle" type="button">Light</button></header>
<main><section class="kpis">{kpi_html}</section>
<section class="card wide"><h2>Balance by age bucket</h2><div class="col">{''.join(cols)}</div></section>
<section class="card wide"><h2>Aging by payer</h2><div class="scroll"><table><tr><th>Payer</th>{head}<th class="n">Total</th><th class="n">Avg days</th><th class="n">% &gt;90</th></tr>{prow}</table></div></section>
<section class="card wide"><h2>Collector worklist (highest priority first)</h2><div class="scroll"><table><tr><th>Claim</th><th>Payer</th><th>Patient</th><th class="n">Age</th><th>Bucket</th><th class="n">Balance</th><th>Status</th></tr>{wrow}</table></div></section>
</main><footer>Generated by Codifyre AI AR Aging Report. Synthetic sample data.</footer>
<script>{JS}</script></body></html>"""
