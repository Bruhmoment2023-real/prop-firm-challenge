"""Download free price history (no key, no login) from the public Yahoo Finance chart endpoint.

Usage:  python code/fetch_market_data.py
Writes data/market/<symbol>_<interval>.csv (columns: ts_utc, open, high, low, close) and data/market/fetch_log.csv.

Used only to build *standardised, de-meaned* return shapes for the bootstrap; no price level or drift from
these files enters any result (zero edge is imposed by construction).
Total download is a few megabytes.
"""
import csv, json, datetime, pathlib, urllib.request, urllib.parse

OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "market"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
JOBS = [  # (symbol, interval, range)
    ("EURUSD=X", "1h", "730d"), ("GBPUSD=X", "1h", "730d"), ("GC=F", "1h", "730d"), ("NQ=F", "1h", "730d"),
    ("EURUSD=X", "1d", "max"), ("GC=F", "1d", "max"), ("^GSPC", "1d", "max"), ("^NDX", "1d", "max"),
]


def fetch(symbol, interval, rng):
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol)
           + (f"?interval={interval}&period1=0&period2=9999999999" if rng == "max"
              else f"?interval={interval}&range={rng}"))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.load(r)["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    rows = []
    for i, t in enumerate(res["timestamp"]):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        rows.append((datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), o, h, l, c))
    return url, rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "fetch_log.csv").open("w", newline="") as lf:
        lw = csv.writer(lf)
        lw.writerow(["symbol", "interval", "range", "url", "accessed_utc", "rows", "first", "last"])
        for sym, itv, rng in JOBS:
            ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            try:
                url, rows = fetch(sym, itv, rng)
            except Exception as e:  # noqa: BLE001
                lw.writerow([sym, itv, rng, "", ts, f"FAIL {e}", "", ""])
                print(sym, itv, "FAIL", e)
                continue
            name = sym.replace("=X", "").replace("=F", "_F").replace("^", "") + f"_{itv}.csv"
            with (OUT / name).open("w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["ts_utc", "open", "high", "low", "close"])
                w.writerows(rows)
            lw.writerow([sym, itv, rng, url, ts, len(rows), rows[0][0], rows[-1][0]])
            print(sym, itv, len(rows), rows[0][0], rows[-1][0])


if __name__ == "__main__":
    main()
