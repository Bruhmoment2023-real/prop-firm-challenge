# Passing the prop-firm challenge: rules, calibrated return processes, skill inference and the economics of evaluation fees

Archived on Zenodo: https://doi.org/10.5281/zenodo.23537728 (this DOI always points to the latest version). Version 2.0 is https://doi.org/10.5281/zenodo.24332377.

**Sean Solano Paul**, Independent researcher, Bengaluru, India. ORCID: https://orcid.org/0009-0002-8465-4468. Funding: none. Competing interests: none.

## Version 2 (November 2026)

The November paper extends the October study from ten products at eight firms to 17 products at 12 firms, with the public rules read between 13 October and 17 November 2026. It is under peer review. This repository holds its code, rule dataset, result tables, figures and analysis plan in `v17/`.

### What the paper does

Retail proprietary trading firms sell evaluations ("challenges") that a trader passes by reaching a profit target before a loss limit, and they sell a pass as a sign of ability. The paper asks how often a trader with no skill passes, which rules drive failure, how much a pass says about skill, and what the rules imply for the firm's revenue. It uses a dated rule dataset, a daily-position simulator, return processes calibrated to five markets (GARCH, filtered historical simulation and block bootstrap among them) and intraday monitoring.

### Headline results

- **Dataset:** 17 products at 12 firms, 106 sourced rule values, rules read 13 October to 17 November 2026. Two firms refused automated access and were not worked around.
- **Zero-skill pass rate:** median 20.4% across 409 resolved settings (range 2.0% to 33.2%). On a static two-step product the rulebook alone fixes the rate at one third, and the simulated rates sit below that ceiling.
- **Calibration:** the GARCH process passed an out-of-sample calibration test that Gaussian processes failed.
- **What drives failure:** the target-to-loss ratio, any deadline and a trailing floor. The daily loss limit matters mainly for one-step products.
- **Skill inference:** a pass has a likelihood ratio of about 2 to 3.4 for a trader with a 56% hit rate against zero skill (1.8 to 3.4 across 16 products, median 2.6), and less when buyers may retry.
- **Economics:** under generous payout assumptions, firm revenue per buyer was positive for 5 of 16 products when 1% of buyers are skilled and for 15 of 16 when buyers pay wide spreads.
- **Limits:** these are simulations of an idealised trader, with rules read on stated dates and the paper's own funded-stage assumptions.

### Where everything is

All of it is in [`v17/`](v17/); [`v17/README.md`](v17/README.md) has the full file map and run order. In short: `v17/data/` (rule dataset, modelled rules, rule changes between the two reads), `v17/code/` (simulator, calibration, validation, grid, rule drivers, economics, figures, data-collection scripts), `v17/results/` (every result table), `v17/figures/`, `v17/PLAN.md` (analysis plan with its one amendment) and `v17/Online_Resource_1_appendix.pdf`.

### How to rerun

Python 3.12 or newer. Install `requirements.txt` plus `arch` and `psutil`, then run from the repository root:

```
python v17/code/fetch_market_daily.py              # price files (not shipped)
python v17/code/calibrate.py
python v17/code/validate_v3.py
python v17/code/run_grid.py ES NQ EURUSD GOLD BTC
python v17/code/run_grid.py headline
python v17/code/summarise_e1.py
python v17/code/rule_drivers.py a                  # then: b, analyse
python v17/code/economics.py
python v17/code/sens_ambiguous.py
python v17/code/make_figures.py
```

Details and caveats are in `v17/README.md`.

### What is not redistributed, and why

- **Archived firm-page text and HTML are not included.** The rule pages are the firms' own text, so this repository does not republish them. The rule values were transcribed by the author and are in `v17/data/rule_dataset_v3_long.csv`. Every row there carries the source URL, the access date, the archived file name and a Wayback Machine link (`wayback_url`, `wayback_timestamp`) to the nearest public snapshot. The Wayback copy is the closest public record, not necessarily the page exactly as read.
- **Market data is not included.** The daily price files come from Yahoo Finance and are not redistributed under its terms. `v17/code/fetch_market_daily.py` downloads them again; the calibration window ends on 14 November 2026, so the fit can be reproduced.

### Licences

Code: MIT (`LICENSE`). Results, derived tables and figures: CC BY 4.0 (`LICENSE-DATA.md`). Third-party source data keep their own terms.

---

## Version 1 (October 2026)

The description below is of the October paper and the root `code/`, `data/` and `results/` folders. It is unchanged except for this heading and the title line that follows.

**October paper:** Is passing a prop-firm challenge evidence of skill? Zero-edge pass rates and the diagnostic value of a pass under ten published rule sets

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

Two later checks (standard library plus numpy, run from the repository root with the root as `<repo>`): `python -I code/headline_pass_intervals.py <repo> <out.csv>` gives the 95% Wilson intervals in Table 2 (saved output `results/headline_pass_intervals.csv`), and `python -I code/daily_limit_off.py <repo> <out.csv>` reruns the FTMO headline cells of Section 3.3 with the daily loss limit on and off (saved output `results/daily_limit_off_results.csv`, log `results/daily_limit_off_log.txt`). The second uses `code/sim_copy_nonumba.py`, a copy of `code/propsim/sim.py` whose numba decorator is a no-op so it runs without numba; its bootstrap cells need `data/market/` (see `fetch_market_data.py`).

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

## Version 2 (November 2026)

The `v17/` folder holds the code, rule tables, results and figures for the revised study. The version 1 files above are unchanged.

- `v17/PLAN.md`: the analysis plan, fixed before the new data were collected.
- `v17/code/`: simulator and analysis scripts.
- `v17/data/`: the rule dataset, the coded rule sets and the log of rule changes.
- `v17/results/` and `v17/figures/`: outputs used in the paper.
- `v17/Online_Resource_1_appendix.pdf`: the online appendix.

Not included, for the same reasons as version 1: archived firm web pages (`data/raw/`) and vendor price bars (`data/market/`). The fetch scripts regenerate them.

## Citation

Solano Paul, S. (2026). *Is passing a prop-firm challenge evidence of skill? Zero-edge pass rates and the diagnostic value of a pass under ten published rule sets* [Research code and data]. https://github.com/Bruhmoment2023-real/prop-firm-challenge https://doi.org/10.5281/zenodo.23537728 (concept DOI; resolves to the latest version).

A machine-readable record is in `CITATION.cff`.
