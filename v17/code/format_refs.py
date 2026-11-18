import json, urllib.request, urllib.parse, re, pathlib, pandas as pd, time, html
ROOT = pathlib.Path(__file__).resolve().parents[1]
v = pd.read_csv(ROOT / "results" / "lit_verification.csv")
out = []
for r in v.itertuples():
    m = json.load(urllib.request.urlopen(urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(r.doi, safe="/()<>:;"), headers={"User-Agent": "academic-research-script/1.0"}), timeout=40))["message"]
    au = []
    for a in m.get("author", []):
        g = "".join(w[0] for w in re.split(r"[\s\-]+", a.get("given", "")) if w)
        au.append(f"{a.get('family','')} {g}")
    t = re.sub(r"<[^>]+>", "", html.unescape((m.get("title") or [""])[0])).replace("\n", " ").strip(); t = re.sub(r"\s+", " ", t).rstrip(":")
    if t.isupper(): t = t.capitalize()
    y = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    j = html.unescape((m.get("container-title") or [""])[0]); vol = m.get("volume", ""); iss = m.get("issue", ""); pg = m.get("page", "").replace("-", "-")
    s = f"{', '.join(au)} ({y}) {t}. {j} {vol}" + (f"({iss})" if iss else "") + (f":{pg}" if pg else "") + f". https://doi.org/{r.doi}"
    out.append(dict(short=r.short, ref=s, year=y)); time.sleep(0.3)
pd.DataFrame(out).to_csv(ROOT / "results" / "new_refs_formatted.csv", index=False)
for o in out: print(o["ref"])
