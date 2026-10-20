"""Adapt python/kit/docs.py to paper 01's own screening rules (strong/weak/context patterns) and sources. Idempotent."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "kit", "docs.py")
L = open(p, encoding="utf-8").read().split("\n")
if any("PAPER01-PATCHED" in l for l in L):
    raise SystemExit("already patched")
out = []
i = 0
rules_new = '''o.append("These rules are those of the earlier pass (`python\\\\config.py`, `classify()` in `python\\\\pipeline.py`), applied identically to search hits and snowballed records.\\n\\n"
         "A record is **included in sub-literature X** if (i) a *strong* pattern of X is in the title, or two distinct strong patterns are in the abstract, or a strong abstract pattern plus a weak title pattern, or a weak title pattern with at least three distinct X patterns overall; "
         "(ii) the finance (or trader/fund) *context* pattern matches title+abstract; (iii) no *exclude* pattern matches title+abstract, no *exclude_title* pattern matches the title, and (unless a strong term is in the title) no *exclude_soft* pattern matches. "
         "The sub-literature with the highest score (4 per strong title hit + 2 per strong abstract hit + 2 per weak title hit + 1 per weak abstract hit) is the primary label. "
         "Records were also dropped for: paratext/front-matter/spam titles, retraction, document types other than article/review/preprint/chapter/book/report/dissertation, non-English language, and OpenAlex domains that are clearly outside finance (unless the title carried a finance term).\\n")
for sk, sl in cfg["sublits"].items():
    o.append(f"**{sk} - {sl['label']}**\\n")
    o.append(f"- context (required): `{sl['context']}`")
    for g in sl["strong"]:
        o.append(f"- strong: `{g}`")
    for g in sl["weak"]:
        o.append(f"- weak: `{g}`")
    for g in sl.get("exclude", []):
        o.append(f"- exclude (title+abstract): `{g}`")
    for g in sl.get("exclude_title", []):
        o.append(f"- exclude (title): `{g}`")
    for g in sl.get("exclude_soft", []):
        o.append(f"- exclude_soft: `{g}`")
    o.append("")
o.append("**Seeds.** Landmark titles (accepted only on a near-exact Crossref title match), four DOIs from the hub's prior-work notes and, in the second pass, every DOI or arXiv id in `01-prior-work.md`: 14 of those were missing from the corpus and were added by one-by-one OpenAlex lookup (`tables\\\\prior_work_added.csv`). Seeds bypass the keyword rules.\\n")
o.append("A record matching several sub-literatures keeps the highest-scoring one as `sublit`.\\n")'''.split("\n")
while i < len(L):
    l = L[i]
    if "ERIC API | free, no key | education topics only" in l:
        i += 1; continue
    if "OpenCitations Index API v2" in l:
        l = l.replace("OpenCitations Index API v2 | free, no key | DOI-to-DOI citations only", "Semantic Scholar Graph API (citations endpoint) | free, no key | citing records, most with DOIs")
    if l.startswith("for sk, sl in cfg[\"sublits\"].items():") and i > 80 and "o.append(f\"**{sk} - " in L[i + 1]:
        # skip old rule loop until the 'Exclusion pattern' and 'A record matching' lines
        j = i
        while not L[j].startswith("o.append(\"## 4. Snowballing"):
            j += 1
        out.extend(rules_new)
        i = j
        continue
    if "Forward: citing DOIs from OpenCitations" in l:
        l = ('         f"- Forward: citing records from Semantic Scholar for each central paper ({p2.get(\'forward_candidates\')} citing records, pre-screened on title/abstract and then screened with the rules in section 3).\\n"')
        out.append(l); i += 1
        # drop the following continuation line about OpenCitations if it begins with f"- All candidates
        continue
    l = l.replace("Crossref, Semantic Scholar, ERIC and arXiv", "Crossref, Semantic Scholar and arXiv").replace("forward citations from OpenCitations", "forward citations from Semantic Scholar")
    out.append(l); i += 1
out.append("# PAPER01-PATCHED")
open(p, "w", encoding="utf-8").write("\n".join(out))
print("patched")
