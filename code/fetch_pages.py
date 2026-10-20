"""Archive public firm / regulator pages (raw HTML + plain text) with an access timestamp.

Usage:  python code/fetch_pages.py name=URL [name=URL ...]
Writes data/raw/firm_pages/<name>.html, <name>.txt and appends to data/raw/firm_pages/fetch_log.csv.
No logins, no cookies, plain GET with a browser user-agent. If a page refuses (403/429) it is logged, not retried.
"""
import sys, re, html, csv, datetime, pathlib, urllib.request

OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw" / "firm_pages"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<(br|/p|/div|/li|/tr|/h[1-6]|/td|/th)[^>]*>", "\n", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
    return re.sub(r"\n\s*\n+", "\n", raw).strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / "fetch_log.csv"
    new = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["name", "url", "accessed_utc", "status", "bytes"])
        for arg in sys.argv[1:]:
            name, url = arg.split("=", 1)
            ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
                with urllib.request.urlopen(req, timeout=40) as r:
                    body = r.read()
                    status = r.status
                raw = body.decode("utf-8", "replace")
                (OUT / f"{name}.html").write_text(raw, encoding="utf-8")
                (OUT / f"{name}.txt").write_text(to_text(raw), encoding="utf-8")
                w.writerow([name, url, ts, status, len(body)])
                print(name, status, len(body))
            except Exception as e:  # noqa: BLE001 - we want every failure logged
                w.writerow([name, url, ts, f"FAIL {e}", 0])
                print(name, "FAIL", e)


if __name__ == "__main__":
    main()
