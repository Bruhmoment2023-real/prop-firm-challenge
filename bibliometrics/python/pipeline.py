"""Bibliometric data pipeline. Usage (from <paper>\\bibliometrics\\python):
    python pipeline.py discover   # Crossref + Semantic Scholar + arXiv searches, seeds, title pre-screen
    python pipeline.py resolve    # OpenAlex single-record lookups for every pre-screened candidate
    python pipeline.py screen     # rule screen + manual lists -> corpus
    python pipeline.py snowball   # one round backward + forward from the most central papers, then re-screen
    python pipeline.py refs       # resolve cited references (cited >=2x), S2 + Crossref enrichment
    python pipeline.py master     # master table + bibliometrix input + PRISMA counts
Everything is cached (see common.py); re-running never re-fetches.
"""
import csv, gzip, json, os, re, sys, time, collections, urllib.parse as up
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C
import config as CFG

BASE = os.path.dirname(HERE)                     # ...\bibliometrics
RAW = os.path.join(BASE, "data", "raw")
CLEAN = os.path.join(BASE, "data", "clean")
for d in (RAW, CLEAN, os.path.join(BASE, "tables")):
    os.makedirs(d, exist_ok=True)

CROSSREF_TYPES = "type:journal-article,type:posted-content,type:book-chapter,type:proceedings-article,type:report,type:monograph,type:book,type:dissertation"
S2_FIELDS = "title,abstract,year,externalIds,citationCount,influentialCitationCount,venue,publicationTypes"

# ------------------------------------------------------------------ screening rules
_comp = {}


def rx(p):
    if p not in _comp:
        _comp[p] = re.compile(p, re.I)
    return _comp[p]


GLOBAL_EXCL_TITLE = r"^(front ?matter|back ?matter|table of contents|contents|index|editorial board|preface|foreword|erratum|corrigendum|correction( to)?:?|book reviews?|masthead|issue information|author index|subject index|list of (figures|tables|contributors)|acknowledg|copyright|title page|announcements?)\b|(coupon|discount|promo) code"


def classify(title, abstract):
    """Return dict(best sublit or None, score, hits). Same function is used for pre-screen, screen and snowball."""
    title = C.strip_tags(title or "")
    abstract = C.strip_tags(abstract or "")
    both = title + " . " + abstract
    if rx(GLOBAL_EXCL_TITLE).search(title.strip()):
        return dict(sublit=None, score=0, reason="paratext, front-matter or promotional-spam title", hits="")
    best = None
    reasons = []
    for key, s in CFG.SUBLITS.items():
        ts = {p for p in s["strong"] if rx(p).search(title)}
        as_ = {p for p in s["strong"] if rx(p).search(abstract)} - ts
        tw = {p for p in s.get("weak", []) if rx(p).search(title)}
        aw = {p for p in s.get("weak", []) if rx(p).search(abstract)} - tw
        if not (ts or as_ or tw or aw):
            continue
        ctx = s.get("context")
        ctx_ok = True if not ctx else bool(rx(ctx).search(both))
        excl = next((p for p in s.get("exclude", []) if rx(p).search(both)), None)
        if not excl:                 # title-only excludes (off-target study designs)
            excl = next((p for p in s.get("exclude_title", []) if rx(p).search(title)), None)
        if not excl and not ts:      # soft excludes only bite when the topic term is not in the title
            excl = next((p for p in s.get("exclude_soft", []) if rx(p).search(both)), None)
        n_all = len(ts | as_ | tw | aw)
        # include if: a strong term in the title; or two strong terms in the abstract; or a strong abstract term plus a
        # weak title term; or a weak title term with at least three distinct topic terms overall
        ok = bool(ts) or len(as_) >= 2 or (bool(as_) and bool(tw)) or (bool(tw) and n_all >= 3)
        score = 4 * len(ts) + 2 * len(as_) + 2 * len(tw) + len(aw)
        if not ctx_ok:
            reasons.append(f"{key}: no {s.get('context_name','finance')} context"); continue
        if excl:
            reasons.append(f"{key}: excluded term /{excl}/"); continue
        if not ok:
            reasons.append(f"{key}: too few topic terms"); continue
        if best is None or score > best["score"]:
            best = dict(sublit=key, score=score, hits="|".join(sorted(ts | as_ | tw | aw))[:300])
    if best:
        best["reason"] = ""
        return best
    return dict(sublit=None, score=0, reason="; ".join(reasons) or "no topic term in title/abstract", hits="")


# ------------------------------------------------------------------ discovery
def crossref_search(q, rows):
    url = ("https://api.crossref.org/works?query.bibliographic=" + up.quote(q) + f"&rows={rows}&filter={CROSSREF_TYPES}"
           "&select=DOI,title,issued,container-title,type,is-referenced-by-count,author,abstract&mailto=" + C.MAILTO)
    st, tx = C.fetch(url, min_interval=0.4)
    if st != 200:
        print("  crossref FAIL", st, q); return None, []
    js = json.loads(tx)
    out = []
    for it in js["message"]["items"]:
        yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
        out.append(dict(src="crossref", doi=C.norm_doi(it.get("DOI")), title=C.strip_tags((it.get("title") or [""])[0]),
                        year=yr, abstract=C.strip_tags(it.get("abstract", "")), cites=it.get("is-referenced-by-count", 0)))
    return js["message"].get("total-results"), out


def s2_bulk(q, fos, max_n=1000):
    url = ("https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=" + up.quote(q) + "&fields=" + S2_FIELDS +
           "&sort=citationCount:desc" + ("&fieldsOfStudy=" + up.quote(fos) if fos else ""))
    st, tx = C.fetch(url, min_interval=1.5, retries=8)
    if st != 200:
        print("  s2 FAIL", st, q); return None, []
    js = json.loads(tx)
    out = []
    for it in (js.get("data") or [])[:max_n]:
        ex = it.get("externalIds") or {}
        out.append(dict(src="s2", doi=C.norm_doi(ex.get("DOI")), title=it.get("title") or "", year=it.get("year"),
                        abstract=it.get("abstract") or "", cites=it.get("citationCount") or 0, mag=str(ex.get("MAG") or ""),
                        arxiv=ex.get("ArXiv") or "", s2id=it.get("paperId")))
    return js.get("total"), out


def arxiv_search(q, max_n=200):
    url = "https://export.arxiv.org/api/query?search_query=" + up.quote(q) + f"&max_results={max_n}&sortBy=relevance"
    st, tx = C.fetch(url, min_interval=3.2)
    if st != 200:
        print("  arxiv FAIL", st, q); return None, []
    ns = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/", "x": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(tx)
    tot = root.find("o:totalResults", ns)
    out = []
    for e in root.findall("a:entry", ns):
        aid = re.sub(r"v\d+$", "", e.find("a:id", ns).text.rsplit("/abs/", 1)[-1])
        doi = e.find("x:doi", ns)
        out.append(dict(src="arxiv", doi=C.norm_doi(doi.text) if doi is not None else "", arxiv=aid,
                        title=re.sub(r"\s+", " ", e.find("a:title", ns).text or "").strip(),
                        abstract=re.sub(r"\s+", " ", e.find("a:summary", ns).text or "").strip(),
                        year=int(e.find("a:published", ns).text[:4]), cites=0,
                        authors="; ".join(a.find("a:name", ns).text for a in e.findall("a:author", ns))))
    return int(tot.text) if tot is not None else None, out


def title_seed(t):
    """Resolve a seed title to DOIs through Crossref; accept only near-exact title matches (all versions returned)."""
    url = ("https://api.crossref.org/works?query.bibliographic=" + up.quote(t) + "&rows=10&select=DOI,title,issued,type,is-referenced-by-count&mailto=" + C.MAILTO)
    st, tx = C.fetch(url, min_interval=0.4)
    if st != 200:
        return []
    nt = C.norm_title(t)
    out = []
    for it in json.loads(tx)["message"]["items"]:
        ct = C.norm_title((it.get("title") or [""])[0])
        if ct == nt or (len(nt) > 25 and len(ct) > 25 and (ct.startswith(nt) or nt.startswith(ct))):
            out.append((it.get("is-referenced-by-count") or 0, C.norm_doi(it["DOI"])))
    return [d for _, d in sorted(out, reverse=True)][:3]


def cmd_discover():
    cands, qlog = [], []
    for key, s in CFG.SUBLITS.items():
        for q in s["crossref"]:
            tot, rows = crossref_search(q, CFG.CROSSREF_ROWS)
            for r in rows: r.update(sublit_q=key, query=q)
            cands += rows; qlog.append(dict(db="Crossref", sublit=key, query=q, total_hits=tot, retrieved=len(rows)))
        for q, fos in s["s2"]:
            tot, rows = s2_bulk(q, fos)
            for r in rows: r.update(sublit_q=key, query=q)
            cands += rows; qlog.append(dict(db="Semantic Scholar (bulk)", sublit=key, query=q + (f"  [fieldsOfStudy={fos}]" if fos else ""), total_hits=tot, retrieved=len(rows)))
        for q in s["arxiv"]:
            tot, rows = arxiv_search(q)
            for r in rows: r.update(sublit_q=key, query=q)
            cands += rows; qlog.append(dict(db="arXiv", sublit=key, query=q, total_hits=tot, retrieved=len(rows)))
        print(key, "queries done; candidates so far", len(cands), flush=True)
    seeds = []
    for d in CFG.SEED_DOIS:
        seeds.append(dict(src="seed", doi=C.norm_doi(d), title="", abstract="", year=None, cites=0, sublit_q="seed", query="named prior work"))
    for a in CFG.SEED_ARXIV:
        seeds.append(dict(src="seed", doi="", arxiv=a, title="", abstract="", year=None, cites=0, sublit_q="seed", query="named prior work"))
    seedlog = []
    for t in CFG.SEED_TITLES:
        ds = title_seed(t)
        seedlog.append(dict(title=t, doi="; ".join(ds), resolved=bool(ds)))
        for d in ds:
            seeds.append(dict(src="seed_title", doi=d, title=t, abstract="", year=None, cites=0, sublit_q="seed", query="analyst seed title (verified in Crossref)"))
    with gzip.open(os.path.join(RAW, "discovery_candidates_all.jsonl.gz"), "wt", encoding="utf-8") as f:
        for r in cands + seeds: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    wcsv(os.path.join(BASE, "tables", "search_query_log.csv"), qlog)
    wcsv(os.path.join(BASE, "tables", "seed_title_resolution.csv"), seedlog)
    # de-duplicate, pre-screen
    uniq = {}
    for r in cands + seeds:
        k = r.get("doi") or ("arxiv:" + r["arxiv"] if r.get("arxiv") else "") or ("t:" + C.norm_title(r["title"]))
        if not k or k == "t:": continue
        if k in uniq:
            u = uniq[k]; u["srcs"].add(r["src"]); u["sublits_q"].add(r["sublit_q"])
            for f_ in ("abstract", "mag", "arxiv", "s2id", "title", "authors"):
                if not u.get(f_) and r.get(f_): u[f_] = r[f_]
        else:
            u = dict(r); u["srcs"] = {r["src"]}; u["sublits_q"] = {r["sublit_q"]}; uniq[k] = u
    passed = []
    for k, u in uniq.items():
        is_seed = bool(u["srcs"] & {"seed", "seed_title"})
        c = classify(u.get("title"), u.get("abstract"))
        u["pre_sublit"], u["pre_reason"] = c["sublit"], c["reason"]
        if is_seed or c["sublit"]:
            passed.append(u)
    for u in uniq.values():
        u["srcs"] = sorted(u["srcs"]); u["sublits_q"] = sorted(u["sublits_q"])
    C.jdump(passed, os.path.join(RAW, "candidates_prescreened.json"))
    stats = dict(records_found=len(cands) + len(seeds), by_db=dict(collections.Counter(r["src"] for r in cands + seeds)),
                 unique_after_dedup=len(uniq), duplicates_removed=len(cands) + len(seeds) - len(uniq),
                 prescreen_removed=len(uniq) - len(passed), prescreen_passed=len(passed))
    C.jdump(stats, os.path.join(CLEAN, "stats_discover.json"))
    print(json.dumps(stats, indent=1))


# ------------------------------------------------------------------ OpenAlex resolution
def resolve_one(u):
    idents = []
    if u.get("doi"): idents.append("doi:" + u["doi"])
    if u.get("arxiv"): idents.append("doi:10.48550/arxiv." + u["arxiv"])
    if u.get("mag"): idents.append("W" + u["mag"])
    for i in idents:
        w = C.oa_single(i)
        if w and w.get("id"):
            return w
    return None


STORE = os.path.join(RAW, "openalex_works.jsonl.gz")


def load_store():
    recs = {}
    if os.path.exists(STORE):
        with gzip.open(STORE, "rt", encoding="utf-8") as f:
            for line in f:
                w = json.loads(line); recs[C.wid(w["id"])] = w
    return recs


def save_store(recs):
    with gzip.open(STORE, "wt", encoding="utf-8") as f:
        for w in recs.values(): f.write(json.dumps(w, ensure_ascii=False) + "\n")


def cmd_resolve():
    cands = C.jload(os.path.join(RAW, "candidates_prescreened.json"))
    res = C.pmap(resolve_one, cands, workers=6, label="openalex")
    recs = load_store(); unresolved = []; origin = C.jload(os.path.join(CLEAN, "origin.json"), {})
    for u, w in zip(cands, res):
        if w is None:
            unresolved.append({k: (u.get(k) if not isinstance(u.get(k), list) else ";".join(u[k])) for k in ("doi", "arxiv", "title", "year", "srcs", "authors", "abstract", "cites")})
            continue
        i = C.wid(w["id"]); recs[i] = w
        o = "seed" if set(u["srcs"]) & {"seed", "seed_title"} else "search"
        if origin.get(i) != "seed": origin[i] = o
    save_store(recs); C.jdump(origin, os.path.join(CLEAN, "origin.json"))
    wcsv(os.path.join(CLEAN, "unresolved_in_openalex.csv"), unresolved)
    st = dict(candidates=len(cands), resolved=len(cands) - len(unresolved), unresolved=len(unresolved), unique_openalex_records=len(recs))
    C.jdump(st, os.path.join(CLEAN, "stats_resolve.json")); print(st)


# ------------------------------------------------------------------ screening
BAD_DOMAINS = {"Health Sciences", "Life Sciences"}
OK_TYPES = {"conference-paper", "article", "preprint", "book-chapter", "review", "book", "dissertation", "report", "posted-content", "other", "letter"}


def screen_record(w):
    title = w.get("title") or w.get("display_name") or ""
    ab = C.abstract_from_inverted(w.get("abstract_inverted_index"))
    if w.get("is_paratext"): return None, "paratext flag", 0, ""
    if w.get("is_retracted"): return None, "retracted", 0, ""
    if (w.get("type") or "") not in OK_TYPES: return None, f"document type {w.get('type')}", 0, ""
    if not title.strip(): return None, "no title", 0, ""
    if w.get("language") not in (None, "en"): return None, f"language {w.get('language')}", 0, ""
    c = classify(title, ab)
    if not c["sublit"]: return None, c["reason"], 0, ""
    dom = ((w.get("primary_topic") or {}).get("domain") or {}).get("display_name")
    if dom in BAD_DOMAINS and not rx(CFG.FIN_CTX).search(title):
        return None, f"off-domain ({dom}) with no finance term in title", 0, ""
    return c["sublit"], "", c["score"], c["hits"]


def read_manual(name):
    p = os.path.join(BASE, "data", "manual", name)
    d = {}
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f): d[r["id"].strip()] = r
    return d


def do_screen(recs):
    man_ex, man_in = read_manual("manual_exclude.csv"), read_manual("manual_include.csv")
    origin = C.jload(os.path.join(CLEAN, "origin.json"), {})
    log, inc = [], {}
    # duplicated abstracts = proceedings / book-series blurb attached to many records (known OpenAlex trap)
    abcount = collections.Counter()
    for w in recs.values():
        a = C.norm_title(C.abstract_from_inverted(w.get("abstract_inverted_index")))[:300]
        if len(a) > 120: abcount[a] += 1
    for i, w in recs.items():
        sub, reason, score, hits = screen_record(w)
        a = C.norm_title(C.abstract_from_inverted(w.get("abstract_inverted_index")))[:300]
        if sub and len(a) > 120 and abcount[a] >= 3:
            sub, reason = None, f"abstract shared by {abcount[a]} records (series/proceedings blurb)"
        if i in man_in:
            sub, reason = man_in[i].get("sublit") or sub or "a", ""
            score = max(score, 4)
        elif origin.get(i) == "seed" and not sub:
            sub = CFG.SEED_DEFAULT_SUBLIT.get(i, None) or guess_sub(w); reason = ""; score = max(score, 4)
        if i in man_ex:
            sub, reason = None, "hand screen: " + man_ex[i].get("reason", "")
        log.append(dict(id=i, year=w.get("publication_year"), type=w.get("type"), cited_by=w.get("cited_by_count"),
                        decision="include" if sub else "exclude", sublit=sub or "", score=score, reason=reason,
                        origin=origin.get(i, ""), title=(w.get("title") or "")[:200], hits=hits))
        if sub: inc[i] = dict(sublit=sub, score=score)
    # version duplicates (preprint + journal): same normalised title -> keep most cited
    bytitle = collections.defaultdict(list)
    for i in inc: bytitle[C.norm_title(recs[i].get("title"))].append(i)
    ndup = 0
    for t, ids in bytitle.items():
        if len(ids) > 1 and len(t) > 20:
            ids.sort(key=lambda i: (-(recs[i].get("cited_by_count") or 0), -(recs[i].get("referenced_works_count") or 0)))
            for j in ids[1:]:
                inc.pop(j); ndup += 1
                for r in log:
                    if r["id"] == j: r["decision"], r["reason"], r["sublit"] = "exclude", f"duplicate version of {ids[0]}", ""
    return inc, log, ndup


def guess_sub(w):
    c = classify(w.get("title"), C.abstract_from_inverted(w.get("abstract_inverted_index")))
    return c["sublit"] or "a"


def cmd_screen():
    recs = load_store()
    inc, log, ndup = do_screen(recs)
    C.jdump(inc, os.path.join(CLEAN, "included.json"))
    wcsv(os.path.join(CLEAN, "screen_log.csv"), sorted(log, key=lambda r: (r["decision"], r["sublit"], -(r["cited_by"] or 0))))
    cnt = collections.Counter(v["sublit"] for v in inc.values())
    rs = collections.Counter(re.sub(r"/.*?/", "/../", r["reason"]).split(" of W")[0][:60] for r in log if r["decision"] == "exclude")
    st = dict(records=len(recs), included=len(inc), by_sublit=dict(cnt), version_duplicates=ndup, exclusion_reasons=dict(rs.most_common(40)))
    C.jdump(st, os.path.join(CLEAN, "stats_screen.json")); print(json.dumps(st, indent=1))


# ------------------------------------------------------------------ snowball
def local_cites(recs, inc):
    lc = collections.Counter()
    for i in inc:
        for r in recs[i].get("referenced_works") or []:
            r = C.wid(r)
            if r in inc and r != i: lc[r] += 1
    return lc


def s2_citations(doi):
    url = (f"https://api.semanticscholar.org/graph/v1/paper/DOI:{up.quote(doi)}/citations?fields=contexts,isInfluential,intents,"
           "externalIds,title,year,abstract,citationCount&limit=1000")
    st, tx = C.fetch(url, min_interval=1.5, retries=8)
    if st != 200: return None
    return json.loads(tx).get("data") or []


def cmd_snowball():
    recs = load_store(); inc = C.jload(os.path.join(CLEAN, "included.json")); origin = C.jload(os.path.join(CLEAN, "origin.json"), {})
    if os.path.exists(os.path.join(CLEAN, "snowball_central.json")):
        central = C.jload(os.path.join(CLEAN, "snowball_central.json"))
    else:
        lc = local_cites(recs, inc)
        central = [i for i, _ in sorted(lc.items(), key=lambda kv: (-kv[1], -(recs[kv[0]].get("cited_by_count") or 0)))][:CFG.N_CENTRAL]
        C.jdump(central, os.path.join(CLEAN, "snowball_central.json"))
    # backward
    back = set()
    for i in central:
        for r in recs[i].get("referenced_works") or []:
            r = C.wid(r)
            if r not in recs: back.add(r)
    back = sorted(back)
    print("backward refs to fetch:", len(back), flush=True)
    res = C.pmap(lambda w: C.oa_single(w), back, workers=6, label="backward")
    nb = 0
    for w in res:
        if w and w.get("id"):
            i = C.wid(w["id"])
            if i not in recs: recs[i] = w; origin.setdefault(i, "snowball_backward"); nb += 1
    # forward via Semantic Scholar (also keeps citation contexts + influential flags)
    ctx_rows, fwd, nfail, nfwd_total = [], {}, 0, 0
    for i in central:
        doi = C.norm_doi(recs[i].get("doi"))
        if not doi: nfail += 1; continue
        data = s2_citations(doi)
        if data is None: nfail += 1; print("  s2 citations FAIL", doi); continue
        nfwd_total += len(data)
        for d in data:
            cp = d.get("citingPaper") or {}
            ex = cp.get("externalIds") or {}
            for cx in (d.get("contexts") or [])[:3]:
                ctx_rows.append(dict(cited_id=i, cited_title=recs[i].get("title"), citing_title=cp.get("title"), citing_year=cp.get("year"),
                                     citing_doi=C.norm_doi(ex.get("DOI")), influential=d.get("isInfluential"), intents="|".join(d.get("intents") or []), context=cx))
            c = classify(cp.get("title"), cp.get("abstract"))
            if c["sublit"]:
                k = C.norm_doi(ex.get("DOI")) or "arxiv:" + (ex.get("ArXiv") or "") or "mag:" + str(ex.get("MAG") or "")
                fwd[k] = dict(doi=C.norm_doi(ex.get("DOI")), arxiv=ex.get("ArXiv") or "", mag=str(ex.get("MAG") or ""), title=cp.get("title"), srcs=["s2fwd"])
    fl = list(fwd.values())
    print("forward: S2 citing records", nfwd_total, "pre-screen passed", len(fl), flush=True)
    res = C.pmap(resolve_one, fl, workers=6, label="forward")
    nf = 0
    for w in res:
        if w and w.get("id"):
            i = C.wid(w["id"])
            if i not in recs: recs[i] = w; origin.setdefault(i, "snowball_forward"); nf += 1
    save_store(recs); C.jdump(origin, os.path.join(CLEAN, "origin.json"))
    wcsv(os.path.join(CLEAN, "citation_contexts_s2.csv"), ctx_rows)
    before = len(inc)
    inc2, log, ndup = do_screen(recs)
    C.jdump(inc2, os.path.join(CLEAN, "included.json"))
    wcsv(os.path.join(CLEAN, "screen_log.csv"), sorted(log, key=lambda r: (r["decision"], r["sublit"], -(r["cited_by"] or 0))))
    st = dict(central=len(central), backward_new_records=nb, forward_s2_citing_records=nfwd_total, forward_prescreen_passed=len(fl),
              forward_new_records=nf, s2_forward_failures=nfail, included_before=before, included_after=len(inc2),
              added_by_snowball=sum(1 for i in inc2 if origin.get(i, "").startswith("snowball")), version_duplicates=ndup,
              by_sublit=dict(collections.Counter(v["sublit"] for v in inc2.values())))
    C.jdump(st, os.path.join(CLEAN, "stats_snowball.json")); print(json.dumps(st, indent=1))


# ------------------------------------------------------------------ references + enrichment
def cmd_refs():
    recs = load_store(); inc = C.jload(os.path.join(CLEAN, "included.json"))
    rc = collections.Counter()
    for i in inc:
        for r in set(recs[i].get("referenced_works") or []): rc[C.wid(r)] += 1
    need = sorted(r for r, n in rc.items() if n >= CFG.REF_MIN_CITES and r not in recs)
    print("unique refs", len(rc), "cited>=%d" % CFG.REF_MIN_CITES, sum(1 for n in rc.values() if n >= CFG.REF_MIN_CITES), "to fetch", len(need), flush=True)
    res = C.pmap(lambda w: C.oa_single(w, C.OA_SELECT_REF), need, workers=6, label="refs", every=500)
    refs = {C.wid(w["id"]): w for w in res if w and w.get("id")}
    with gzip.open(os.path.join(RAW, "openalex_reference_records.jsonl.gz"), "wt", encoding="utf-8") as f:
        for w in refs.values(): f.write(json.dumps(w, ensure_ascii=False) + "\n")
    # Semantic Scholar batch (citation + influential-citation counts)
    dois = [C.norm_doi(recs[i].get("doi")) for i in inc if recs[i].get("doi")]
    s2 = {}
    for k in range(0, len(dois), 400):
        chunk = dois[k:k + 400]
        st, tx = C.fetch("https://api.semanticscholar.org/graph/v1/paper/batch?fields=externalIds,citationCount,influentialCitationCount,abstract,tldr",
                         method="POST", body={"ids": ["DOI:" + d for d in chunk]}, min_interval=2.0, retries=8)
        if st != 200: print("  s2 batch FAIL", st); continue
        for d, it in zip(chunk, json.loads(tx)):
            if it: s2[d] = dict(s2_citations=it.get("citationCount"), s2_influential=it.get("influentialCitationCount"), abstract=it.get("abstract") or "", tldr=(it.get("tldr") or {}).get("text") or "")
    C.jdump(s2, os.path.join(RAW, "s2_batch_counts.json"))
    cr = {}
    for k in range(0, len(dois), 40):
        chunk = [d for d in dois[k:k + 40] if "," not in d]
        url = ("https://api.crossref.org/works?filter=" + ",".join("doi:" + up.quote(d, safe="/") for d in chunk) +
               f"&rows={len(chunk)}&select=DOI,is-referenced-by-count,references-count,type,publisher&mailto=" + C.MAILTO)
        st, tx = C.fetch(url, min_interval=0.4)
        if st != 200: print("  crossref batch FAIL", st); continue
        for it in json.loads(tx)["message"]["items"]:
            cr[C.norm_doi(it["DOI"])] = dict(crossref_cited_by=it.get("is-referenced-by-count"), crossref_refs=it.get("references-count"), publisher=it.get("publisher"))
    C.jdump(cr, os.path.join(RAW, "crossref_batch_counts.json"))
    st = dict(unique_references=len(rc), references_cited_min=sum(1 for n in rc.values() if n >= CFG.REF_MIN_CITES), fetched=len(refs),
              not_found=len(need) - len(refs), corpus_dois=len(dois), s2_matched=len(s2), crossref_matched=len(cr))
    C.jdump(st, os.path.join(CLEAN, "stats_refs.json")); print(st)


# ------------------------------------------------------------------ master table
ISO = None


def country_name(cc):
    global ISO
    if ISO is None:
        ISO = C.jload(os.path.join(HERE, "iso2_names.json"))
    return ISO.get(cc, cc)


def au_wos(name):
    name = C.ascii_up(re.sub(r"[;,]", " ", name or ""))
    name = re.sub(r"\b(JR|SR|II|III|IV)\.?$", "", name).strip()
    parts = [p for p in re.split(r"[\s]+", name) if p]
    if not parts: return ""
    if len(parts) == 1: return parts[0]
    sur = parts[-1].replace(".", "")
    ini = "".join(p[0] for p in parts[:-1] if p[0].isalpha())
    return f"{sur} {ini}".strip()


def so_abbr(w):
    s = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    s = re.sub(r"[^A-Z0-9& ]+", " ", C.ascii_up(s))
    return re.sub(r"\s+", " ", s).strip()


def cr_string(w):
    au = (w.get("authorships") or [{}])
    a1 = au_wos(((au[0] if au else {}).get("author") or {}).get("display_name") or "") or "ANONYMOUS"
    so = so_abbr(w) or re.sub(r"[^A-Z0-9 ]+", " ", C.ascii_up(w.get("display_name") or ""))[:60].strip() or "NO SOURCE"
    b = w.get("biblio") or {}
    s = f"{a1}, {w.get('publication_year') or ''}, {so}"
    if b.get("volume"): s += f", V{re.sub('[;,]', '', str(b['volume']))}"
    if b.get("first_page"): s += f", P{re.sub('[;,]', '', str(b['first_page']))}"
    d = C.norm_doi(w.get("doi"))
    if d: s += f", DOI {d.upper().replace(';', '').replace(',', '')}"
    return s


def cmd_master():
    recs = load_store(); inc = C.jload(os.path.join(CLEAN, "included.json")); origin = C.jload(os.path.join(CLEAN, "origin.json"), {})
    refs = {}
    p = os.path.join(RAW, "openalex_reference_records.jsonl.gz")
    if os.path.exists(p):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                w = json.loads(line); refs[C.wid(w["id"])] = w
    s2 = C.jload(os.path.join(RAW, "s2_batch_counts.json"), {}); cr = C.jload(os.path.join(RAW, "crossref_batch_counts.json"), {})
    lc = local_cites(recs, inc)
    disc = {}   # abstract fallbacks from the discovery pulls (Semantic Scholar / Crossref / arXiv), keyed by DOI
    with gzip.open(os.path.join(RAW, "discovery_candidates_all.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("doi") and len(r.get("abstract") or "") > len(disc.get(r["doi"], ("", ""))[0]):
                disc[r["doi"]] = (r["abstract"], r["src"])
    named = {C.norm_doi(d) for d in CFG.SEED_DOIS}
    rows, bib, refrows = [], [], {}
    for i, meta in inc.items():
        w = recs[i]
        aus = w.get("authorships") or []
        names = [(a.get("author") or {}).get("display_name") or a.get("raw_author_name") or "" for a in aus]
        insts = [[x.get("display_name") for x in a.get("institutions") or []] for a in aus]
        ccs = [a.get("countries") or [] for a in aus]
        corr = next((k for k, a in enumerate(aus) if a.get("is_corresponding")), 0 if aus else None)
        src = (w.get("primary_location") or {}).get("source") or {}
        boa = w.get("best_oa_location") or {}
        oa = w.get("open_access") or {}
        pt = w.get("primary_topic") or {}
        ab = C.abstract_from_inverted(w.get("abstract_inverted_index"))
        doi = C.norm_doi(w.get("doi"))
        ab_src = "openalex" if ab else ""
        if not ab and (s2.get(doi) or {}).get("abstract"):
            ab, ab_src = s2[doi]["abstract"], "semantic scholar"
        if not ab and doi in disc:
            ab, ab_src = C.strip_tags(disc[doi][0]), {"s2": "semantic scholar"}.get(disc[doi][1], disc[doi][1])
        rlist = [C.wid(r) for r in w.get("referenced_works") or []]
        kws = [k.get("display_name") for k in w.get("keywords") or []]
        concepts = [c.get("display_name") for c in (w.get("concepts") or []) if (c.get("level") or 0) >= 2 and (c.get("score") or 0) >= 0.3]
        b = w.get("biblio") or {}
        rows.append(dict(
            id=i, doi=doi, title=C.strip_tags(w.get("title") or ""), year=w.get("publication_year"), date=w.get("publication_date"), type=w.get("type"),
            authors="; ".join(names), first_author=names[0] if names else "", n_authors=len(names),
            institutions="; ".join(sorted({x for l in insts for x in l if x})), countries="; ".join(sorted({c for l in ccs for c in l})),
            corr_country=(ccs[corr][0] if corr is not None and ccs[corr] else ""),
            source=src.get("display_name") or "", source_type=src.get("type") or "", issn_l=src.get("issn_l") or "", volume=b.get("volume") or "", issue=b.get("issue") or "",
            first_page=b.get("first_page") or "", last_page=b.get("last_page") or "",
            cited_by_openalex=w.get("cited_by_count"), fwci=w.get("fwci"), local_citations=lc.get(i, 0),
            s2_citations=(s2.get(doi) or {}).get("s2_citations"), s2_influential=(s2.get(doi) or {}).get("s2_influential"),
            crossref_cited_by=(cr.get(doi) or {}).get("crossref_cited_by"), publisher=(cr.get(doi) or {}).get("publisher") or "",
            is_oa=oa.get("is_oa"), oa_status=oa.get("oa_status"), oa_url=oa.get("oa_url") or "", pdf_url=boa.get("pdf_url") or "", oa_landing=boa.get("landing_page_url") or "",
            oa_host=((boa.get("source") or {}).get("display_name") or ""), oa_license=boa.get("license") or "",
            primary_topic=pt.get("display_name") or "", subfield=(pt.get("subfield") or {}).get("display_name") or "", field=(pt.get("field") or {}).get("display_name") or "",
            domain=(pt.get("domain") or {}).get("display_name") or "",
            keywords="; ".join(kws), concepts="; ".join(concepts), n_refs=len(rlist), has_abstract=bool(ab), abstract_source=ab_src, s2_tldr=(s2.get(doi) or {}).get("tldr") or "", abstract=ab,
            sublit=meta["sublit"], sublit_label=CFG.SUBLITS[meta["sublit"]]["label"], relevance_score=meta["score"], origin=origin.get(i, ""),
            named_prior_work=doi in named, refs="; ".join(rlist)))
        # bibliometrix (WoS-tag) record
        crs = []
        for r in rlist:
            rw = recs.get(r) if r in inc else None
            rw = rw or refs.get(r) or (recs.get(r) if r in recs else None)
            if rw is None: continue
            s = cr_string(rw); crs.append(s)
            if r not in refrows:
                refrows[r] = dict(ref_id=r, cr_string=s, title=rw.get("display_name") or rw.get("title"), year=rw.get("publication_year"), doi=C.norm_doi(rw.get("doi")),
                                  source=((rw.get("primary_location") or {}).get("source") or {}).get("display_name") or "", in_corpus=r in inc, cited_by_openalex=rw.get("cited_by_count"))
        c1 = []
        for a, il, cl in zip(aus, insts, ccs):
            for k, ins in enumerate(il or []):
                cc = (a.get("institutions") or [])[k].get("country_code") if k < len(a.get("institutions") or []) else None
                if ins: c1.append(f"{C.ascii_up(ins).replace(',', ' ').replace(';', ' ')}, {country_name(cc) if cc else 'NA'}")
        au_co = [country_name(c) for l in ccs for c in l]
        dt = {"article": "ARTICLE", "preprint": "PREPRINT", "book-chapter": "BOOK CHAPTER", "review": "REVIEW", "book": "BOOK", "dissertation": "THESIS", "report": "REPORT"}.get(w.get("type"), "OTHER")
        bib.append(dict(
            AU=";".join(au_wos(n) for n in names) or "ANONYMOUS", AF=";".join(C.ascii_up(n) for n in names) or "ANONYMOUS",
            TI=C.ascii_up(C.strip_tags(w.get("title") or "")), SO=C.ascii_up(src.get("display_name") or "") or "NO SOURCE (PREPRINT OR BOOK)",
            J9=so_abbr(w) or "NO SOURCE", JI=so_abbr(w) or "NO SOURCE", DT=dt, DE=";".join(C.ascii_up(k) for k in kws), ID=";".join(C.ascii_up(k) for k in concepts),
            AB=C.ascii_up(ab), C1=";".join(c1), RP=(c1[0] if c1 else ""), CR=";".join(crs), TC=w.get("cited_by_count") or 0, PY=w.get("publication_year"),
            DI=doi, LA="ENGLISH", DB="ISI", UT=i, VL=b.get("volume") or "", PG=b.get("first_page") or "",
            AU_UN=";".join(C.ascii_up(x).replace(";", " ") for l in insts for x in l if x), AU_CO=";".join(au_co),
            AU1_CO=(country_name(ccs[corr][0]) if corr is not None and ccs[corr] else ""), id_oa=i, SUBLIT=meta["sublit"], SUBLIT_LABEL=CFG.SUBLITS[meta["sublit"]]["label"],
            LCS_EXACT=lc.get(i, 0), ORIGIN=origin.get(i, "")))
    rows.sort(key=lambda r: (-(r["local_citations"] or 0), -(r["cited_by_openalex"] or 0)))
    wcsv(os.path.join(CLEAN, "master.csv"), rows)
    wcsv(os.path.join(CLEAN, "bibliometrix_input.csv"), bib)
    # reference table with exact corpus citation counts
    rc = collections.Counter()
    for r in rows:
        for x in set(r["refs"].split("; ")) if r["refs"] else []: rc[x] += 1
    rr = []
    for r, d in refrows.items():
        d["cited_by_corpus_docs"] = rc[r]; rr.append(d)
    rr.sort(key=lambda d: -d["cited_by_corpus_docs"])
    wcsv(os.path.join(CLEAN, "cited_references.csv"), rr)
    # exact direct-citation edge list (citing -> cited, both in corpus)
    edges = [dict(citing=r["id"], cited=x) for r in rows for x in (r["refs"].split("; ") if r["refs"] else []) if x in inc and x != r["id"]]
    wcsv(os.path.join(CLEAN, "direct_citation_edges.csv"), edges)
    # raw export of the corpus records only
    with gzip.open(os.path.join(RAW, "openalex_corpus_records.jsonl.gz"), "wt", encoding="utf-8") as f:
        for i in inc: f.write(json.dumps(recs[i], ensure_ascii=False) + "\n")
    st = dict(corpus=len(rows), with_abstract=sum(r["has_abstract"] for r in rows), with_doi=sum(bool(r["doi"]) for r in rows),
              with_refs=sum(r["n_refs"] > 0 for r in rows), with_country=sum(bool(r["countries"]) for r in rows), open_access=sum(bool(r["is_oa"]) for r in rows),
              direct_citation_edges=len(edges), by_sublit=dict(collections.Counter(r["sublit"] for r in rows)), by_origin=dict(collections.Counter(r["origin"] for r in rows)),
              year_min=min(r["year"] for r in rows if r["year"]), year_max=max(r["year"] for r in rows if r["year"]),
              named_prior_work_in_corpus=sum(r["named_prior_work"] for r in rows), named_prior_work_expected=len(named))
    C.jdump(st, os.path.join(CLEAN, "stats_master.json")); print(json.dumps(st, indent=1))
    missing = named - {r["doi"] for r in rows}
    if missing: print("NAMED PRIOR WORK NOT IN CORPUS:", missing)


def wcsv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=keys or ["empty"]); wr.writeheader(); wr.writerows(rows)


if __name__ == "__main__":
    if not os.path.exists("D:\\"): sys.exit("D: missing")
    {"discover": cmd_discover, "resolve": cmd_resolve, "screen": cmd_screen, "snowball": cmd_snowball, "refs": cmd_refs, "master": cmd_master}[sys.argv[1]]()
