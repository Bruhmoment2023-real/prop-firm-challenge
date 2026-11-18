"""Archive public prop-firm rule pages (rendered text + HTML) with an access date. No logins, no forms, no CAPTCHA solving.
Each page is fetched once with a headless browser (own instance, no remote-debugging ports), 4 s apart.
A refusal (HTTP 4xx/5xx, bot wall) is logged and not retried or circumvented.
Usage: python fetch_rule_pages.py urls.csv   (columns: name,url)"""
import sys, csv, datetime, pathlib, time
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT/"data"/"raw"/"firm_pages_2026-11-17"
UA = "academic-research-script/1.0 (public pages only; polite rate; no login)"
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
done = set()
log = OUT/"fetch_log.csv"
if log.exists(): done = {r["name"] for r in csv.DictReader(open(log, encoding="utf-8")) if r["status"].startswith("200")}
new = not log.exists()
with sync_playwright() as p, log.open("a", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    if new: w.writerow(["name","url","accessed_utc","status","final_url","chars_text","note"])
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(user_agent=UA, locale="en-US")
    for r in rows:
        if r["name"] in done: continue
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        pg = ctx.new_page(); note=""
        try:
            resp = pg.goto(r["url"], wait_until="domcontentloaded", timeout=45000)
            try: pg.wait_for_load_state("networkidle", timeout=15000)
            except Exception: note="networkidle timeout"
            # expand obvious accordions would require clicking; we do not click
            pg.wait_for_timeout(2500)
            st = resp.status if resp else 0
            txt = pg.inner_text("body")
            (OUT/(r["name"]+".txt")).write_text(txt, encoding="utf-8")
            (OUT/(r["name"]+".html")).write_text(pg.content(), encoding="utf-8")
            w.writerow([r["name"], r["url"], ts, st, pg.url, len(txt), note]); print(r["name"], st, len(txt), note)
        except Exception as e:
            w.writerow([r["name"], r["url"], ts, "FAIL", "", 0, str(e)[:120]]); print(r["name"], "FAIL", str(e)[:100])
        pg.close(); fh.flush(); time.sleep(4)
    b.close()
