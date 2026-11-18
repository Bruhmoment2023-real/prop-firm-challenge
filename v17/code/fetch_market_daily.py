"""Download free daily OHLC history from Yahoo's public chart endpoint (no key, no login).
Writes data/market/<name>_1d.csv (date, open, high, low, close) and data/market/fetch_log_v3.csv.
Data end at the access date; nothing after the access date exists, so there is no look-ahead in the file itself."""
import csv, json, datetime, pathlib, urllib.request, urllib.parse, time
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "market"
UA = "academic-research-script/1.0 (public free-data download, polite rate)"
JOBS = [("ES=F","ES_F"),("NQ=F","NQ_F"),("^GSPC","GSPC"),("^NDX","NDX"),("EURUSD=X","EURUSD"),("GBPUSD=X","GBPUSD"),("GC=F","GC_F"),("BTC-USD","BTCUSD"),("CL=F","CL_F")]
def fetch(sym):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%s?interval=1d&period1=0&period2=9999999999" % urllib.parse.quote(sym)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.load(r)["chart"]["result"][0]
    q = res["indicators"]["quote"][0]; rows=[]
    for i,t in enumerate(res["timestamp"]):
        o,h,l,c = q["open"][i],q["high"][i],q["low"][i],q["close"][i]
        if None in (o,h,l,c) or min(o,h,l,c)<=0: continue
        rows.append((datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime("%Y-%m-%d"),o,h,l,c))
    return url, rows
OUT.mkdir(parents=True, exist_ok=True)
with (OUT/"fetch_log_v3.csv").open("w",newline="") as lf:
    lw=csv.writer(lf); lw.writerow(["symbol","url","accessed_utc","rows","first","last"])
    for sym,name in JOBS:
        ts=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try: url,rows=fetch(sym)
        except Exception as e:
            lw.writerow([sym,"",ts,"FAIL %s"%e,"",""]); print(sym,"FAIL",e); continue
        with (OUT/(name+"_1d.csv")).open("w",newline="") as fh:
            w=csv.writer(fh); w.writerow(["date","open","high","low","close"]); w.writerows(rows)
        lw.writerow([sym,url,ts,len(rows),rows[0][0],rows[-1][0]]); print(sym,len(rows),rows[0][0],rows[-1][0]); time.sleep(2)
