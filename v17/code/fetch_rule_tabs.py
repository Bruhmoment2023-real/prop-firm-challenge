"""Second pass on archived rule pages: on a public page, click the account-size selector that reads 100K (or 50K) and save the
rendered text and HTML again (suffix _100k / _50k). Only same-page tab buttons are clicked; no forms, no logins, no navigation away."""
import sys, csv, datetime, pathlib, time, re
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT/"data"/"raw"/"firm_pages_2026-11-17"
UA = "academic-research-script/1.0 (public pages only; polite rate; no login)"
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
sizes = sys.argv[2].split(",") if len(sys.argv) > 2 else ["100K"]
log = OUT/"fetch_log_tabs.csv"; new = not log.exists()
with sync_playwright() as p, log.open("a", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    if new: w.writerow(["name","url","size","accessed_utc","clicked","chars_text"])
    b = p.chromium.launch(headless=True); ctx = b.new_context(user_agent=UA, locale="en-US")
    for r in rows:
        for sz in sizes:
            ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            pg = ctx.new_page(); clicked = 0
            try:
                pg.goto(r["url"], wait_until="domcontentloaded", timeout=45000)
                try: pg.wait_for_load_state("networkidle", timeout=12000)
                except Exception: pass
                pg.wait_for_timeout(2000)
                pat = re.compile(r"^\s*\$?\s*%s\s*$|^\s*\$?\s*%s\s*$" % (re.escape(sz), re.escape(sz.replace("K", ",000"))), re.I)
                loc = pg.get_by_text(pat)
                n = loc.count()
                for k in range(min(n, 6)):
                    try:
                        el = loc.nth(k)
                        if el.is_visible():
                            el.click(timeout=3000); clicked += 1; pg.wait_for_timeout(800); break
                    except Exception: pass
                txt = pg.inner_text("body")
                (OUT/f"{r['name']}_{sz.lower()}.txt").write_text(txt, encoding="utf-8")
                (OUT/f"{r['name']}_{sz.lower()}.html").write_text(pg.content(), encoding="utf-8")
                w.writerow([r["name"], r["url"], sz, ts, clicked, len(txt)]); print(r["name"], sz, clicked, len(txt), flush=True)
            except Exception as e:
                w.writerow([r["name"], r["url"], sz, ts, "FAIL", str(e)[:100]]); print(r["name"], "FAIL", str(e)[:80], flush=True)
            pg.close(); fh.flush(); time.sleep(4)
    b.close()
