# Code - how to reproduce every table and figure

Python 3.12, packages pinned in `requirements.txt` (numpy, scipy, pandas, matplotlib, numba). Free software only. No account, key or login is used anywhere.

Run from the project folder `D:\Research-Publishing\01-prop-firm-challenge` with the project's own interpreter:

```
.venv\Scripts\python.exe code\fetch_pages.py name=URL ...        # archive a firm page (HTML + text + access time)
.venv\Scripts\python.exe code\build_rule_tables.py               # data\firm_rules_sourced.csv, rule_sets_model.csv, published_statistics.csv
.venv\Scripts\python.exe code\fetch_market_data.py               # data\market\*.csv from Yahoo's public chart endpoint (about 8 MB)
.venv\Scripts\python.exe code\01_validate.py                     # results\validation.csv   (about 4 min)
.venv\Scripts\python.exe code\02_run_experiments.py --only A --part 1of2
.venv\Scripts\python.exe code\02_run_experiments.py --only A --part 2of2
.venv\Scripts\python.exe code\02_run_experiments.py --only B
.venv\Scripts\python.exe code\02_run_experiments.py --only C
.venv\Scripts\python.exe code\02_run_experiments.py --only DE
.venv\Scripts\python.exe code\03_figures_and_tables.py           # figures and T1..T5 tables (seconds)
```

Measured wall time on the shared laptop, single thread, 13 Oct 2026: A part 1 took 738 s (398 s on an earlier, quieter run), A part 2 426 s, B 321 s, C 421 s, DE 149 s. To keep every run under 10 minutes on a busy machine use `--part 1of3`, `2of3`, `3of3` for block A. `--quick` runs blocks A-C at 2,000 paths in about 3 minutes as a smoke test and writes `results\QUICK_*.csv`, kept apart from the real tables.

## Files

| File | What it is |
|---|---|
| `propsim/closed_form.py` | The formulas: two-barrier exit, exit before a deadline, trailing drawdown with and without lock, discrete-monitoring correction, gambler's ruin, optional-stopping ceiling, Bayes posterior |
| `propsim/sim.py` | The Monte Carlo kernels (numba): `sim_challenge` for the evaluation, `sim_funded` for the funded stage. The module docstring lists every rule and option |
| `propsim/rules.py` | Loads `data/rule_sets_model.csv`, wraps the kernels, computes the economics |
| `01_validate.py` | 30 closed-form tests plus one illustration row |
| `02_run_experiments.py` | Blocks A-E described in its docstring |
| `03_figures_and_tables.py` | Figures 1-7 and summary tables |
| `build_rule_tables.py` | The rule numbers, each with URL, date and archived file |
| `fetch_pages.py`, `fetch_market_data.py`, `lit_search.py` | Small download helpers (firm pages, prices, Crossref title search) |

## Conventions

- All money is a fraction of the starting balance. 0.10 means 10%.
- `risk` is the stop size (fixed-stop model) or the standard deviation of one trade (other models).
- `edge` and `cost` are in units of `risk` per trade.
- Outcome codes: 1 pass, -1 maximum-loss breach, -2 daily-loss breach, -3 time limit, 0 unresolved at `max_days`.
- Seeds are fixed in each block, so tables reproduce exactly on the same numpy and numba versions.

## Known limits of the simulator

- Equity is checked after each trade, not inside a trade.
- Trades are independent draws. The bootstrap keeps 24-bar blocks of real hourly returns but removes their mean.
- Position size does not compound.
- The funded stage uses assumed payout timing (see `data/rule_sets_model.csv`, column `assumptions`).
- Not modelled: spreads beyond the flat per-trade `cost`, news and weekend rules, lot caps, prohibited-strategy clauses, refused payouts.
