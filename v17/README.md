# v17/ : version 2 (November 2026) analysis

Everything the November paper ("Passing the prop-firm challenge: rules, calibrated return processes, skill inference and
the economics of evaluation fees") needs to be checked or rerun: the dated rule dataset, the daily-position simulator, the
calibration, the experiment grid, all result tables and figures, and the analysis plan. The October analysis lives in the
repository root (`code/`, `data/`, `results/`) and is untouched.

## What is not here, and why

- **Archived firm-page text and HTML** (106 page files read on 17 November 2026) are not redistributed. The pages are the
  firms' own text. The rule values were transcribed by the author and are in the rule dataset instead.
- **Market data** (Yahoo Finance daily files for ES, NQ, EURUSD, gold, Bitcoin and others) is not redistributed, under
  Yahoo's terms. `code/fetch_market_daily.py` downloads it again.

Pointers: every row of `data/rule_dataset_v3_long.csv` has the source `url`, the `access_date`, the `archived_file` name
and a `wayback_url` with `wayback_timestamp` (the closest snapshot found through the public Wayback availability
interface; the paper reports snapshots for 15 of the 17 products). The Wayback snapshot is the nearest public copy, not
necessarily the page exactly as read.

## File map

| Path | What it is |
|---|---|
| `PLAN.md` | Analysis plan written before any simulation, with Amendment 1 (reduced grid, fixed before any result was seen) |
| `Online_Resource_1_appendix.pdf` | Online Resource 1: supplementary tables and figures (validation, hypotheses, sensitivity) |
| `data/rule_dataset_v3_long.csv` | 106 rows, one per field, for 17 products at 12 firms: value as published, URL, access date, archived file name, Wayback link |
| `data/rule_sets_v3_model.csv` | The rules as modelled (one row per product), with the assumptions made where a page said nothing |
| `data/rule_changes_oct13_vs_nov17.csv` | What changed between the 13 October and 17 November reads |
| `code/v3sim.py` | Daily-position challenge simulator (numba) and the return-process banks |
| `code/calibrate.py`, `code/pars.py` | Calibrate the five return processes; out-of-sample test and range check; `pars.py` caches the fits |
| `code/validate_v3.py` | Validation tests against exact and closed-form references; writes `results/validation_v3.csv` |
| `code/run_grid.py` | Zero-skill and skill grid over assets, processes, products and costs; `headline` mode runs the 100,000-path headline cell |
| `code/summarise_e1.py` | Joins the grid files with the dataset ceilings into `results/E1_all_cells.csv.gz` |
| `code/rule_drivers.py` | Which rule drives failure: one-rule-removed counterfactuals (`a`), synthetic rule-set regression (`b`, then `analyse`) |
| `code/economics.py` | Firm revenue per buyer, house edge, populations of buyers, likelihood ratios |
| `code/sens_ambiguous.py` | Sensitivity rows for rule readings that stayed ambiguous |
| `code/make_figures.py` | Figures from the result CSVs |
| `code/build_rule_dataset.py` | Builds the rule dataset from archived pages (needs the page text, which is not redistributed) |
| `code/fetch_rule_pages.py`, `code/fetch_rule_tabs.py`, `code/html2text.py`, `code/urls*.csv` | How the firm pages were archived (headless browser, public pages only, no login, one request per page); URL lists |
| `code/fetch_market_daily.py` | Re-downloads the daily price files into `data/market/` |
| `code/format_refs.py`, `code/docx_helpers.py` | Reference formatting and manuscript-building helpers; not needed for the results |
| `code/chain.sh` | The shell chain the author used for the headline cell, rule-driver and economics runs (it has the author's absolute paths; read it as a record of the order) |
| `results/` | Every result table. `grid/` has one CSV per asset and process; `E1_all_cells.csv.gz` is the joined grid; `E1_headline_100k.csv`; `E3a`/`E3b` (rule drivers); `E4*` (economics); `E5_likelihood_ratios.csv`; `S1` to `S6`, `V5`, `V6` and `validation_v3.csv` (summaries, calibration, validation) |
| `figures/` | Figures 1 to 6 and the validation figure (PNG) |

## Run order

Python 3.12 or newer (the November run used 3.13). Install the root `requirements.txt` plus the packages the new code adds:

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # Windows; .venv/bin/python elsewhere
.venv/Scripts/python -m pip install arch psutil             # GARCH calibration and process priority
# only to re-archive firm pages: pip install playwright && playwright install chromium
```

Run from the repository root (the scripts find `v17/` from their own path):

```
python v17/code/fetch_market_daily.py              # 1. price files into v17/data/market/ (not shipped; Yahoo)
python v17/code/calibrate.py                       # 2. calibration, out-of-sample test, range check
python v17/code/validate_v3.py                     # 3. validation -> results/validation_v3.csv
python v17/code/run_grid.py ES NQ EURUSD GOLD BTC  # 4. the grid, one CSV per asset and process (resumable)
python v17/code/run_grid.py headline               # 5. 100,000-path headline cell
python v17/code/summarise_e1.py                    # 6. joined grid
python v17/code/rule_drivers.py a                  # 7. one-rule-removed counterfactuals
python v17/code/rule_drivers.py b
python v17/code/rule_drivers.py analyse
python v17/code/economics.py                       # 8. revenue, populations, likelihood ratios
python v17/code/sens_ambiguous.py                  # 9. sensitivity rows
python v17/code/make_figures.py                    # 10. figures
```

Notes:

- The calibration window ends on 14 November 2026 (`END` in `calibrate.py`), so a fresh download should give the same fit.
  Yahoo can revise old values slightly.
- `run_grid.py` pauses on weekdays 09:00 to 15:45 local time and runs at below-normal priority; it sets 3 numba threads.
- `validate_v3.py` also compares against the older trade-level simulator in the root `code/` folder, which is in this repository.
- The rule dataset (`data/rule_dataset_v3_long.csv`, `rule_sets_v3_model.csv`) is shipped and is the reference. Rebuilding it
  with `fetch_rule_pages.py` and `build_rule_dataset.py` re-reads live firm pages, which have changed since 17 November,
  and `build_rule_dataset.py` also needs the October page archive, which is not redistributed. Use the shipped files to
  reproduce the paper; use the fetch scripts to see how the data were collected.
- Seeds are fixed in the scripts, so a rerun on the same package versions should reproduce the shipped tables. This
  documentation update did not rerun the pipeline.
