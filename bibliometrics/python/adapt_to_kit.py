"""Convert the earlier agent's paper-01 data into the inputs of the shared kit (python/kit/pipeline.py `master` stage).

Nothing is re-searched. Reads data/raw/*.jsonl.gz and data/clean/*.json|csv, writes
data/clean/corpus_final.jsonl.gz, data/raw/openalex/refs_resolved.jsonl.gz, prisma_*.json, refs_stats.json,
data/raw/query_log.csv, tables/..., and adds any paper named in ../01-prior-work.md that is missing from the corpus
(looked up one by one in OpenAlex, free).  Usage: python adapt_to_kit.py
"""
import json, os, re, sys, gzip
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "kit"))
import common as C

B = os.path.dirname(HERE)
P = lambda *a: os.path.join(B, *a)
M = pd.read_csv(P("data", "clean", "master.csv"), encoding="utf-8-sig", keep_default_na=False)
origin = C.jload(P("data", "clean", "origin.json"), {})
recs = {C.wid(w["id"]): w for w in C.jsonl_gz_read(P("data", "raw", "openalex_corpus_records.jsonl.gz"))}
Mi = M.set_index("id")
works = []
for i, r in Mi.iterrows():
    w = recs.get(i)
    if w is None:
        continue
    if not w.get("abstract_inverted_index") and r["abstract"]:
        w["_abs_extra"] = r["abstract"]
    if r["pdf_url"] and not (w.get("best_oa_location") or {}).get("pdf_url"):
        w["best_oa_location"] = dict(w.get("best_oa_location") or {}, pdf_url=r["pdf_url"])
    w["_sublits"] = [r["sublit"]]
    w["_origin"] = r["origin"]
    w["_dbs"] = [r["origin"]]
    works.append(w)
print("corpus from earlier run:", len(works), "of", len(M))

# ---- papers named in the prior-work note that are missing: look up one by one in OpenAlex
txt = open(os.path.join(os.path.dirname(B), "01-prior-work.md"), encoding="utf-8").read()
dois = sorted({d.rstrip(".,;:)").lower() for d in re.findall(r"10\.\d{4,9}/[^\s\"<>\)\]]+", txt)})
arx = sorted(set(re.findall(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", txt)))
SUB_A = {"10.1016/j.finmar.2013.05.006", "10.2139/ssrn.3423101", "10.1093/rfs/hhn046"}
SUB_B = {"10.1007/s11009-009-9139-1", "10.1016/j.spa.2009.01.002", "10.1080/14697680600764227", "10.1111/1467-9965.00035", "10.1111/j.1467-9965.1993.tb00044.x",
         "10.1214/aoms/1177728918", "10.1214/aop/1176995770", "10.1214/aop/1176996395", "10.1239/jap/1077134674", "10.21314/jor.2015.317", "10.2307/2282848"}
have_doi = {C.norm_doi(w.get("doi")) for w in works}
have_id = {C.wid(w["id"]) for w in works}
have_title = {C.norm_title(w.get("title")) for w in works}
added = []
for d in dois + ["10.48550/arxiv." + a for a in arx]:
    if d in have_doi:
        continue
    w = C.oa_single("doi:" + d)
    if not w or not w.get("id"):
        added.append(dict(id=d, status="NOT FOUND in OpenAlex"))
        continue
    if C.wid(w["id"]) in have_id or C.norm_title(w.get("title")) in have_title:
        continue
    w["_sublits"] = ["a" if d in SUB_A else "b" if d in SUB_B else "c"]
    w["_origin"] = "seed"
    w["_dbs"] = ["prior-work note"]
    works.append(w)
    added.append(dict(id=d, status="added " + C.wid(w["id"]) + " | " + (w.get("title") or "")[:80]))
pd.DataFrame(added).to_csv(P("tables", "prior_work_added.csv"), index=False)
print("added from prior-work note:", sum(a["status"].startswith("added") for a in added), "| not found:", sum("NOT FOUND" in a["status"] for a in added))
C.jsonl_gz_write(P("data", "clean", "corpus_final.jsonl.gz"), works)
refs = C.jsonl_gz_read(P("data", "raw", "openalex_reference_records.jsonl.gz"))
C.jsonl_gz_write(P("data", "raw", "openalex", "refs_resolved.jsonl.gz"), refs)

# ---- PRISMA inputs from the earlier run's logs
sd, sres, ssn, sscr, srf = [C.jload(P("data", "clean", f"stats_{n}.json"), {}) for n in ("discover", "resolve", "snowball", "screen", "refs")]
rs = {k: v for k, v in sscr.get("exclusion_reasons", {}).items()}
C.jdump(dict(date="2026-10-13", records_identified=sd.get("records_found"), by_db=sd.get("by_db", {}), duplicates_removed_identifiers=sd.get("duplicates_removed"),
             unique_records=sd.get("unique_after_dedup"), removed_title_prescreen=sd.get("prescreen_removed"), sent_to_openalex=sres.get("candidates"),
             duplicates_removed_openalex=sres.get("candidates", 0) - sres.get("unique_openalex_records", 0) - sres.get("unresolved", 0),
             excluded_reasons={"unresolved in OpenAlex (not in corpus)": sres.get("unresolved")}, included_after_search_screen=ssn.get("included_before")),
        P("data", "clean", "prisma_search.json"), indent=1)
C.jdump(dict(central_papers=ssn.get("central"), backward_candidates=ssn.get("backward_new_records"), forward_candidates=ssn.get("forward_s2_citing_records"),
             snowball_duplicates=ssn.get("version_duplicates"), snowball_excluded_reasons={}, backward_included=int((M.origin == "snowball_backward").sum()),
             forward_included=int((M.origin == "snowball_forward").sum())), P("data", "clean", "prisma_snowball.json"), indent=1)
C.jdump(dict(distinct_cited_works=srf.get("unique_references"), resolved=len(refs), attempted=srf.get("fetched"),
             total_reference_links=sum(len(w.get("referenced_works") or []) for w in works)), P("data", "clean", "refs_stats.json"), indent=1)
# query log in the kit's layout
ql = pd.read_csv(P("tables", "search_query_log.csv"), keep_default_na=False)
print("query-log columns:", list(ql.columns))
ql.to_csv(P("data", "raw", "query_log_earlier_run.csv"), index=False)
print("done; screen reasons recorded:", len(rs))
