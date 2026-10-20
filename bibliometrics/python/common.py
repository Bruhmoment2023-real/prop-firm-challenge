"""Shared helpers for the bibliometrics pipeline (HTTP cache, API wrappers, text utils).

Every HTTP response is cached in one SQLite file so nothing is fetched twice:
    D:\\Research-Publishing\\_tools\\biblio-cache\\http_cache.sqlite
Raw per-paper copies are exported to <paper>\\bibliometrics\\data\\raw by pipeline.py.
"""
import json, os, re, sqlite3, sys, time, zlib, threading, unicodedata, hashlib
from concurrent.futures import ThreadPoolExecutor
import requests

MAILTO = "research-contact-withheld@example.invalid"
UA = f"SeanResearchBibliometrics/1.0 (mailto:{MAILTO})"
CACHE_DIR = r"D:\Research-Publishing\_tools\biblio-cache"
CACHE_DB = os.path.join(CACHE_DIR, "http_cache.sqlite")

_lock = threading.Lock()
_conn = None
_sess = threading.local()


def _db():
    global _conn
    if _conn is None:
        if not os.path.exists("D:\\"):
            sys.exit("D: is missing - stopping (nothing is written to C:).")
        os.makedirs(CACHE_DIR, exist_ok=True)
        _conn = sqlite3.connect(CACHE_DB, check_same_thread=False, timeout=60)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("CREATE TABLE IF NOT EXISTS http (k TEXT PRIMARY KEY, url TEXT, status INT, body BLOB, ts REAL)")
        _conn.commit()
    return _conn


def _session():
    if not hasattr(_sess, "s"):
        _sess.s = requests.Session()
        _sess.s.headers["User-Agent"] = UA
    return _sess.s


def cache_get(key):
    with _lock:
        r = _db().execute("SELECT status, body FROM http WHERE k=?", (key,)).fetchone()
    if r is None:
        return None
    return r[0], zlib.decompress(r[1]).decode("utf-8", "replace")


def cache_put(key, url, status, text):
    with _lock:
        _db().execute("INSERT OR REPLACE INTO http VALUES (?,?,?,?,?)",
                      (key, url, status, zlib.compress(text.encode("utf-8")), time.time()))
        _db().commit()


def fetch(url, method="GET", body=None, min_interval=0.0, retries=6, ok_status=(200, 404), headers=None, timeout=60):
    """Cached fetch. Returns (status, text). 404 is cached (means 'not in this database')."""
    key = hashlib.sha1((method + url + (json.dumps(body, sort_keys=True) if body else "")).encode()).hexdigest()
    hit = cache_get(key)
    if hit is not None:
        return hit
    delay = 2.0
    last = (0, "")
    for attempt in range(retries):
        try:
            if min_interval:
                time.sleep(min_interval)
            if method == "GET":
                r = _session().get(url, timeout=timeout, headers=headers)
            else:
                r = _session().post(url, json=body, timeout=timeout, headers=headers)
            last = (r.status_code, r.text)
            if r.status_code in ok_status:
                cache_put(key, url, r.status_code, r.text)
                return last
            if r.status_code in (429, 500, 502, 503, 504):
                ra = r.headers.get("Retry-After")
                wait = min(float(ra), 60) if ra and ra.replace(".", "").isdigit() else delay
                if ra and ra.isdigit() and float(ra) > 600:   # daily budget exhausted: do not hammer
                    return last
                time.sleep(wait)
                delay = min(delay * 2, 60)
                continue
            return last
        except requests.RequestException as e:
            last = (0, str(e))
            time.sleep(delay)
            delay = min(delay * 2, 60)
    return last


# ---------- OpenAlex (single-record lookups are free; list/search calls cost daily credits) ----------
OA_SELECT_FULL = ("id,doi,title,display_name,publication_year,publication_date,language,type,authorships,"
                  "primary_location,best_oa_location,open_access,cited_by_count,counts_by_year,biblio,is_retracted,"
                  "is_paratext,primary_topic,topics,keywords,concepts,referenced_works,abstract_inverted_index,ids,"
                  "fwci,corresponding_author_ids,corresponding_institution_ids,locations_count,referenced_works_count")
OA_SELECT_REF = "id,doi,display_name,publication_year,type,authorships,primary_location,biblio,cited_by_count"


def oa_single(ident, select=OA_SELECT_FULL):
    """ident: 'W123', 'doi:10.x/y'. Returns dict or None."""
    url = f"https://api.openalex.org/works/{ident}?select={select}&mailto={MAILTO}"
    st, tx = fetch(url, min_interval=0.05)
    if st != 200:
        return None
    try:
        return json.loads(tx)
    except Exception:
        return None


def pmap(fn, items, workers=6, label="", every=250):
    out = [None] * len(items)
    t0 = time.time()
    done = [0]

    def run(i):
        out[i] = fn(items[i])
        done[0] += 1
        if every and done[0] % every == 0:
            print(f"  {label} {done[0]}/{len(items)} ({time.time()-t0:.0f}s)", flush=True)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(run, range(len(items))))
    return out


def abstract_from_inverted(inv):
    if not inv:
        return ""
    pos = []
    for w, idxs in inv.items():
        for i in idxs:
            pos.append((i, w))
    pos.sort()
    return " ".join(w for _, w in pos)


def norm_doi(d):
    if not d:
        return ""
    d = d.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d


def norm_title(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def strip_tags(t):
    if not t:
        return ""
    import html
    t = html.unescape(html.unescape(t))
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def ascii_up(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).upper().strip()


def wid(x):
    return x.rsplit("/", 1)[-1] if x else ""


def jdump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def jload(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)
