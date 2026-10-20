"""Tiny Crossref title search used for the novelty check (free API, no key).
Usage: python code/lit_search.py "query one" "query two" ...   -> prints year | title | authors | venue | DOI
"""
import sys, json, time, urllib.request, urllib.parse

for q in sys.argv[1:]:
    u = "https://api.crossref.org/works?" + urllib.parse.urlencode(
        {"query.bibliographic": q, "rows": 6, "select": "title,author,issued,DOI,container-title,type"})
    try:
        d = json.load(urllib.request.urlopen(u, timeout=40))
    except Exception as e:  # noqa: BLE001
        print("ERR", q, e)
        continue
    print("===", q)
    for r in d["message"]["items"]:
        a = ", ".join((x.get("family") or "") for x in r.get("author", [])[:4])
        y = (r.get("issued", {}).get("date-parts") or [[None]])[0][0]
        print("-", y, "|", (r.get("title") or [""])[0][:110], "|", a, "|", (r.get("container-title") or [""])[0][:45], "|", r["DOI"])
    time.sleep(1)
