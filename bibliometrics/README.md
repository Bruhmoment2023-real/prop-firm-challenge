# Literature map (bibliometrics) - 01-prop-firm-challenge

Data-driven map of the literature around: *Zero-skill traders passing retail prop-firm trading challenges: first-passage and drawdown mathematics, retail trader performance, prop-firm incentives*

- **Corpus size:** 910 records (First-passage, barrier, ruin and drawdown mathematics: 520; Retail trader performance and day trading: 224; Prop firms, funded-trader programmes, contests and tournament incentives: 166)
- **Date of pull:** 2026-10-13
- **Sources:** discovery in Crossref, Semantic Scholar and arXiv; metadata from OpenAlex; forward citations from Semantic Scholar. No Scopus/WoS data (EMPTY - no Scopus/WoS export to merge; corpus is OpenAlex-only).
- **Made by:** an AI agent (Claude). It contains data, figures, tables and bullet-point analysis only - no manuscript prose.

## What is here

| Path | Contents |
|---|---|
| `search-protocol.md` | exact search strings, databases, inclusion/exclusion rules, PRISMA-style counts, coverage checks |
| `scopus-queries.md` | ready-to-paste Scopus and Web of Science advanced-search strings (not run: no login) |
| `gap-analysis.md` | what the map shows: dense and thin areas, where Sean's question sits, five papers to read first |
| `evidence-table.csv` | the most relevant papers with study type, setting, data, method, one-line finding (from the abstract), relation to this paper |
| `config.json` | every setting of the run: queries, rules, seeds, hand-screen exclusions |
| `data\raw\` | raw API responses per query (`crossref\`, `s2\`, `eric\`, `arxiv\`), all query hits (`all_hits.csv`), query log, raw OpenAlex records (`openalex\*.jsonl.gz`) |
| `data\clean\` | `master.csv` / `master.rds` (one row per corpus record), `bibliometrix_input.csv` / `bibliometrix_M.rds` (bibliometrix data frame), `citation_edges.csv`, `cited_references.csv`, screening logs, unresolved candidates |
| `figures\` | 74 figures (PNG at 220 dpi, SVG copies, interactive HTML) and `captions.md` |
| `tables\` | 90 CSV tables (every figure's numbers, PRISMA counts, clusters, logs) |
| `vosviewer\` | map + network files for VOSviewer (co-citation, co-authorship, keyword co-occurrence, bibliographic coupling, direct citation) and VOSviewer-computed layouts |
| `pdfs\` | 8 legally open-access PDFs of core papers and `download_log.csv` |
| `R\`, `python\` | the scripts that made everything |
| `scopus-drop\` | empty; put Scopus/WoS exports here |

## How to regenerate everything (PowerShell)

```powershell
$py = 'D:\Research-Publishing\_tools\biblio-venv\Scripts\python.exe'
$b  = 'D:\Research-Publishing\01-prop-firm-challenge\bibliometrics'
& $py "$b\python\pipeline.py" $b search enrich snowball refs master   # network; every response is cached in D:\Research-Publishing\_tools\biblio-cache
$env:R_LIBS_USER = 'D:\Research-Publishing\_tools\R-lib;C:\Users\seans\AppData\Local\R\win-library\4.5'   # this shell only
& 'C:\Program Files\R\R-4.5.3\bin\Rscript.exe' "$b\R\bibliometrix_analysis.R" $b                # tables + R figures + VOSviewer files
& $py "$b\python\figures.py" $b        # Python figures, VOSviewer layouts, captions.md
& $py "$b\python\pdfs.py" $b download  # open-access PDFs of the core papers
& $py "$b\python\pdfs.py" $b evidence  # rebuild evidence-table.csv from data\clean\evidence_notes.json
& $py "$b\python\docs.py" $b           # this README and search-protocol.md
```
Re-running `search` on a later date re-uses cached responses; delete the cache file to force a fresh pull. To hand-exclude a record, add its OpenAlex id and a reason under `manual_exclude` in `config.json` and re-run `master` onward.

## Analysis log

R / bibliometrix: 27 of 27 analyses completed.

Python figures:
- prisma: ok
- year_sub: ok
- timeline: ok
- db: ok
- geography: ok
- heatmap: ok
- citation_network: ok
- main_path: ok
- cocitation: ok
- vosviewer_cli: VOSviewer command line produced layouts for: py_cocitation_references, keyword_cooccurrence, coauthorship_authors. py_cocitation_references: VOSviewer command line timed out. keyword_cooccurrence: VOSviewer command line timed out. coauthorship_authors: VOSviewer command line timed out. 

## Limits (read before using any figure)

- Discovery ran through Crossref, Semantic Scholar and arXiv, not through an OpenAlex or Scopus topic search (see search-protocol.md section 1). Recall is unknown; the corpus is a map of the indexed literature, not a census.
- OpenAlex is broader but noisier than Scopus: it includes low-quality and predatory outlets, working-paper duplicates and occasional wrong metadata. Screening was by rules plus one AI hand pass over titles.
- OpenAlex is weak on Indian journals and books (missing abstracts, affiliations and reference lists) and on law. Country and collaboration figures only describe the records that carry affiliation data.
- Keywords are OpenAlex's machine-assigned keywords, not author keywords. Thematic maps and co-occurrence networks inherit OpenAlex's vocabulary.
- Citation links exist only where the publisher deposited a reference list. Books, reports, working papers and most law reviews appear isolated even when they are heavily used.
- Citation counts are as of the pull date and favour older papers and English-language journals.
- Evidence-table findings are taken from abstracts unless a row says 'full text read'. Check the paper before citing it.
- Paper 01 was built in two passes: an earlier agent ran discovery, screening, snowballing and the first R tables (python/pipeline.py, python/config.py); this pass re-used that corpus unchanged (python/adapt_to_kit.py), added any paper named in 01-prior-work.md that was missing, and ran the shared kit for the remaining analyses and figures. The older R figures are the files named R02_ ... R22_; the newer ones are R_xx / py_xx.

## Paper-01-specific notes (build history; read with the section above)
- Two passes. Pass 1 (earlier agent, stopped part-way) ran discovery, screening, snowballing and a first set of bibliometrix tables and figures with `python\pipeline.py` and `python\config.py` (search strings are in `python\config.py` and `data\raw\query_log.csv`). Its figures are the files named `R02_` ... `R22_` in `figures\` (kept; the thematic-evolution figure there failed in pass 1). Pass 2 re-used that corpus unchanged (`python\adapt_to_kit.py`), added the 14 papers named in `..\01-prior-work.md` that were missing (`tables\prior_work_added.csv`: SSRN prop-firm preprints and some mathematics papers), rebuilt the master table with the shared kit (`python\kit\`), and produced the newer files `R_NN_*` (bibliometrix) and `py_NN_*` (Python) plus VOSviewer files.
- So `figures\` holds two generations; prefer the `R_NN_` and `py_NN_` files and `figures\captions.md` (which covers those). Sub-literature letters: a = retail trader performance, b = barrier/ruin/drawdown mathematics, c = prop firms, contests, incentives.
- The regenerate block above does not apply as written: run `python\make_config.py`, `python\adapt_to_kit.py`, then `python\kit\pipeline.py <dir> master`, the R script, `python\kit\figures.py`, `python\kit\pdfs.py`, `python\kit\docs.py` (after `python\patch_docs_p01.py`, which adapts docs.py to this paper's rule scheme). `python\evidence_notes_p01.py` writes the hand notes behind `evidence-table.csv` (45 rows "abstract read", 13 "metadata only"; abstracts of the 2026 working papers come from Crossref).
- Known issues: bibliometrix `histNetwork` fails on documents with an empty reference field (patched in R by filling a placeholder; `R\rerun_historiograph.R`); VOSviewer command-line layouts hung for about 30 minutes on a loaded laptop and were killed, so only the layouts named `*_voslayout_map.txt` that exist were produced; the Chevalier and Ellison 1997 PDF is an unreadable scan; the Magdon-Ismail PDF is the 2003 conference version.
- PDFs: only 8 of about 50 attempted open copies downloaded (publisher, SSRN, Wiley, doi.org returned HTTP 403, not worked around). Hall (arXiv 2609.14859) was fetched by hand; see `pdfs\download_note.txt`. Open-copy hunt for three SSRN preprints: `..\depth\preprints.md`.
- Burst detection (Kleinberg) was added in the depth pass: `figures\py_burst_keywords.png`, `tables\py_burst_keywords.csv`. Main-path analysis: `figures\py_06_main_path.png`, `tables\py_main_path_documents.csv`.
