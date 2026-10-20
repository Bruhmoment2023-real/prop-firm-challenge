# Is passing a prop-firm challenge evidence of skill? Zero-edge pass rates and the diagnostic value of a pass under ten published rule sets

**Sean Solano Paul**, Independent researcher, Bengaluru, India. Funding: none. Competing interests: none.

## Summary

Retail proprietary trading firms sell evaluations ("challenges") in which a trader must reach a profit target before hitting a loss limit; a pass is presented as a sign that the trader can trade. This repository holds what is needed to reproduce the paper's results: the sourced rule tables for ten products from eight firms (read 13 October 2026), a numba Monte Carlo simulator (`code/propsim`) checked against 30 closed-form results, the experiment scripts (blocks A-E), all result tables and figures, and a bibliometric map of the surrounding literature. A trader whose every trade has zero expected profit passes a static two-step challenge with probability 1/3 at any trade size; across 1,903 resolved settings the zero-edge pass rate had a median of 23.6% and a maximum of 44.3%, and as a screening test at 1% risk a pass had a likelihood ratio of 1.1 to 3.4 against a zero-edge trader.

## Repository layout

| Path | Contents |
|---|---|
| `code/` | `propsim/` (closed forms, simulator kernels, rules and economics), `01_validate.py`, `02_run_experiments.py`, `03_figures_and_tables.py`, `build_rule_tables.py`, download helpers (`fetch_pages.py`, `fetch_market_data.py`, `lit_search.py`), `code/README.md` (detailed run notes and conventions) |
| `data/` | `firm_rules_sourced.csv` (each rule with source URL and date), `rule_sets_model.csv` (rules as modelled), `published_statistics.csv` (pass rates etc. published by firms) |
| `results/` | `A_`..`E_` experiment tables, `T1`..`T5` summary tables, `validation.csv`, figures `fig1`..`fig7`, `RESULTS-SUMMARY.md`, run logs |
| `bibliometrics/` | Literature map: search protocol, OpenAlex-based corpus, tables, figures, VOSviewer files, R and Python scripts (see `bibliometrics/README.md`) |
| `depth/` | Citation files (BibTeX/RIS), data dictionary, rerun script and its recorded result |
| `01-prior-work.md`, `02-design.md` | Prior-work review and the experiment design |
| `requirements.txt` | Pinned Python packages |

## How to reproduce

Python 3.12. Install:

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # Windows; use .venv/bin/python elsewhere
```

Run from the repository root, in this order (timings are from a shared laptop, single thread; see `code/README.md`):

```
python code/build_rule_tables.py                  # rule tables (already provided in data/)
python code/fetch_market_data.py                  # OPTIONAL: re-download price series into data/market/ (needed only for the bootstrap return models)
python code/01_validate.py                        # results/validation.csv (about 4 min)
python code/02_run_experiments.py --only A --part 1of2
python code/02_run_experiments.py --only A --part 2of2
python code/02_run_experiments.py --only B
python code/02_run_experiments.py --only C
python code/02_run_experiments.py --only DE
python code/03_figures_and_tables.py              # figures and T1..T5 (seconds)
```

`--quick` runs blocks A-C at 2,000 paths as a smoke test and writes `results/QUICK_*.csv`. Some scripts and notes contain the original absolute project path (`D:\Research-Publishing\01-prop-firm-challenge`); run from the repository root and adjust that path if a script reports a missing file. The literature-map steps need R 4.5 with `bibliometrix` and are described in `bibliometrics/README.md`.

## Data sources and licences

| Data | Source | Terms |
|---|---|---|
| Firm rules and published statistics (`data/firm_rules_sourced.csv`, `published_statistics.csv`) | Public pages of the firms, each with URL and access date | Facts transcribed by the author; the firms' page text is not redistributed |
| Hourly/daily price series used by the bootstrap return models | Yahoo Finance public chart endpoint, downloaded by `code/fetch_market_data.py` | Yahoo terms; **not included** |
| Literature metadata | OpenAlex (CC0), Crossref (open metadata), arXiv API, Semantic Scholar API (discovery and counts) | Open metadata; Semantic Scholar citation-context text is **not included** |
| Derived results, tables, figures | This work | CC BY 4.0 (`LICENSE-DATA.md`) |
| Code | This work | MIT (`LICENSE`) |

Third-party email addresses that appeared in copied abstracts were replaced by `[email-redacted]`.

## Not included and why

- Abstract text of third-party papers (the `abstract`/`AB` columns and abstract-derived quote columns of the bibliographic tables, and abstract fields in the OpenAlex JSON). Identifiers, titles, years, venues, keywords and citation data are kept; re-fetch abstracts with the bibliometrics pipeline if needed.
- Per-paper reading notes on the literature (they contain quotations from copyrighted papers) and the literature gap-analysis note (scoping). The scripts that built the notes are kept; run them on your own copies of the papers.
- `data/market/*.csv`: raw vendor price bars (Yahoo Finance). Regenerate with `code/fetch_market_data.py` (about 8 MB).
- `data/raw/firm_pages/`: archived HTML and text copies of firms' web pages (copyrighted, scraped). Regenerate with `code/fetch_pages.py name=URL`; the URLs and access dates are in `data/firm_rules_sourced.csv`.
- `data/raw/papers/`, `data/raw/regulators/`, `depth/raw/`, `bibliometrics/pdfs/`: full-text copies of third-party papers and web or court-docket downloads. Obtain via the DOIs and links in `depth/citations/references.bib`; `bibliometrics/python/pdfs.py` re-downloads open-access PDFs.
- `bibliometrics/data/clean/citation_contexts_s2.csv`: Semantic Scholar citation-context text (API terms). Regenerate with the pipeline in `bibliometrics/python/`.
- `bibliometrics/figures/html_libs`, `R21_lib`, `R21_thematic_evolution_files`: bundled JavaScript libraries for interactive HTML figures; regenerated by the R script.
- Virtual environments, caches, model weights and credentials: none were needed (no account, key or login is used anywhere).

## Citation

Solano Paul, S. (2026). *Is passing a prop-firm challenge evidence of skill? Zero-edge pass rates and the diagnostic value of a pass under ten published rule sets* [Research code and data]. https://github.com/Bruhmoment2023-real/prop-firm-challenge (Zenodo DOI to be added).

A machine-readable record is in `CITATION.cff`.
