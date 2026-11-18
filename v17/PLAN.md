# PLAN-v3 for paper 01 (prop-firm challenge pass probabilities)

Written 2026-11-17 20:14 IST, BEFORE any v3 simulation, calibration or economics run. Before this file only two things had been done:
(a) free daily price files were downloaded (data/market/*_1d.csv, no analysis run on them yet); (b) rule pages were being archived
(data collection, no analysis). Everything below is fixed in advance. Deviations are reported in the paper.
Nothing is tuned to find a positive result. All cells are reported, nulls included.

## 0. Constraints modelled
Prop-firm challenges allow short positions, so no long-only constraint applies to this paper (the Wharton competition rules do not apply).
Research only: no orders, no accounts, no logins. CPU at most 4 processes, BelowNormal; heavy compute paused 09:00-15:45 IST on weekdays.
All work on D:.

## 1. Rule dataset (D1)
Public pages only; no login, no form, no CAPTCHA, one fetch per page, 4 s apart, generic research User-Agent. Rendered text and HTML
are saved to data/raw/firm_pages_2026-11-17/ with the access time in fetch_log.csv. For every product there is one row per field in
data/rule_dataset_v3_long.csv: firm, product, account size, field, value as published, URL, access date, archived file, Wayback URL
or "none found". Wayback lookups use only the public availability API (read-only; no "save page" requests).
Fields: fee, profit targets, max loss (size; static, EOD-trailing or intraday-trailing; lock), daily loss (size, basis), minimum days,
minimum profitable days, consistency rule, time limit, profit split, payout cycle, reset/retry fee, fee refund.
A value the page does not state is recorded NOT STATED; modelling assumptions are stored separately (data/rule_sets_v3_model.csv,
column assumed_fields). Firms that refuse access are listed as refused and not worked around. A product enters the simulations only if
fee, targets, max loss and daily loss (or "none") are all read from its pages.

## 2. Return processes, calibrated to free daily data
Assets: ES futures (ES=F), Nasdaq-100 futures (NQ=F), EURUSD, gold futures (GC=F), Bitcoin (BTC-USD). Daily OHLC from Yahoo's public
chart endpoint, accessed 2026-11-17. Production calibration window: all data up to 2026-11-14 (last complete day before access).
Close-to-close log returns with the mean set to zero (direction is the trader's choice, so the underlying drift is irrelevant to skill).
Five processes:
- P0 iid Gaussian, sd = sample sd.
- P1 iid Student-t, degrees of freedom by maximum likelihood, scaled to the sample sd.
- P2 GJR-GARCH(1,1) with Student-t innovations (arch package, zero mean, quasi-ML), simulated from the unconditional variance with
  a 500-day burn-in.
- P3 Filtered historical simulation: the same GARCH recursion with bootstrapped standardised residuals.
- P4 Stationary block bootstrap of actual (close, high, low) day triples, mean block 20 days, drift removed.
Intraday: P0-P3 give closes only; each day's intraday high and low are drawn from the Brownian-bridge extremes given the close and that
day's conditional sd (max and min drawn independently, which slightly overstates the joint range). P4 uses the real highs and lows.
The device is checked against real OHLC (ratio of mean ln(H/L), per asset).
Look-ahead guard (out-of-sample calibration test): fit P0-P3 on data up to 2022-12-31 only and compare with realised 2023-01-01 to
2026-11-14 on excess kurtosis, share of |r| above 3 training sd, lag-1 autocorrelation of |r|, and 1% and 5% VaR exceedance counts
(Kupiec test). Report all of them whichever way they go. Production runs then use the full window.

## 3. Trader model ("daily-position trader")
Each trading day the trader holds one directional position (long or short), sized so that the account's unconditional daily sd is
sigma_a in {0.5%, 1%, 2%} of the starting balance (leverage = sigma_a / asset daily sd; fixed, no compounding, no resizing as the
account moves). Rule-aware sizing is not used here (it was studied in the old trade-level model).
Direction accuracy h = P(position sign = sign of the day's return). Zero skill is h = 0.5 exactly. Grid h in
{0.46, 0.48, 0.50, 0.52, 0.54, 0.56, 0.60}; h below 0.5 stands for cost-and-mistake losers.
Round-trip cost per day as account fraction = leverage x spread (bp) x multiplier. Base spreads (assumptions, typical quoted retail
spreads, not data): ES 0.5 bp, NQ 0.5 bp, EURUSD 1.0 bp, gold 1.5 bp, BTC 6.0 bp. Multiplier m in {0, 1, 4}.
The implied annualised gross Sharpe ratio for each h is reported so readers can judge how strong a skill level is.

## 4. Challenge simulator (daily steps, new code in numba)
Per rule set from the dataset: up to 3 phases with targets; max loss static, EOD-trailing or intraday-trailing with optional lock at
the start balance; daily loss limit (breach, or "pause" meaning the loss is capped at the limit that day), measured from start-of-day
equity and checked against the day's intraday low; minimum trading days (the trader trades every day so every day counts); minimum
profitable days; best-day consistency rule at the moment the target is first reached (the trader keeps trading until it is met);
time limit per phase; cap of 1,000 days (unresolved paths reported; cells above 2% unresolved are flagged). For trailing floors the
intraday order is worst case for the trader (high first, then low).
Paths: 20,000 per cell in grids; 100,000 for headline cells (ES, P2, sigma_a 1%, h 0.5, m 1). Common random numbers: one return and
uniform bank per (asset, process) shared by all rule sets, skills and costs.
Funded stage (economics): payout every 10 trading days when profit is positive, profit split from the page, all profit withdrawn,
a breach of the loss rules ends the account, horizon 60 trading days (20 and 120 as sensitivity). Same assumptions as paper v16 so
numbers stay comparable; they are assumptions, labelled as such.

## 5. Validation (each reported as pass or fail)
- V1 Exact dynamic programme on the plus/minus-step lattice (static; EOD-trail with and without lock; with and without deadline) against
  the simulator, within 3 standard errors.
- V2 Gaussian close-only static single phase against an independent Nystrom integral-equation solution, within 3 SE.
- V3 Old trade-level simulator (propsim) against the new daily simulator on the old ten rule sets, one trade per day, plus/minus-r
  steps, zero edge, within 3 SE.
- V4 Small-sigma limit of intraday-trailing against continuous closed forms exp(-a/d) (and lock-corrected form), tolerance 0.02;
  static against L/(T+L).
- V5 Brownian-bridge range device against real OHLC (ratio reported per asset; no tolerance pre-set).
- V6 Out-of-sample calibration test of section 2.

## 6. Experiments (all cells reported)
- E1 Pass probability, expected attempts, expected fee to a first funded account, funded payouts and buyer expected value for every
  modelled rule set x 5 assets x 5 processes x 3 sigma_a x 7 h x 3 m. Headline cell: ES, P2, sigma_a 1%, h 0.5, m 1.
- E2 Failure attribution: share of failed attempts ending on max loss, daily loss, time limit, unresolved.
- E3 Rule drivers. (a) Counterfactual "remove one rule" per rule set at the headline cell with common random numbers: daily limit off;
  trailing to static; lock added or removed; deadline off; consistency off; minimum days 0; target x0.5; max loss x1.5.
  (b) Synthetic rule space: 2,000 rule sets with each feature drawn independently from the empirical distribution of the dataset
  (support only, fixed seeds), zero skill, headline process; OLS on logit(pass) with standardised features, drop-one partial R2, plus
  permutation importance from a gradient-boosted regressor.
- E4 Skill populations, fixed before any E1 result is seen: Pop A 1% skilled (h = 0.56), rest h = 0.50, m = 1. Pop B 5% skilled.
  Pop C 20% skilled. Pop D h ~ N(0.49, 0.02^2) discretised onto the h grid, m = 1. Pop E as D with m = 4.
  Buyer behaviour: buys a new attempt after each failure up to K attempts, K in {1, 3, 10}; mixing at buyer level.
  Outputs per rule set: firm revenue per buyer = fees minus payouts minus refunds; "house edge" = 1 - payouts/fees; share of fee revenue
  from failed attempts; share of buyers ending net-negative; share of payouts going to the top 10% of buyers; break-even skilled share
  pi* (revenue zero) by interpolation. Firm-side trading P&L on funded accounts is NOT modelled (A-book or B-book unknown): a stated limitation.
- E5 Skill inference: likelihood ratio and posterior (priors 1%, 5%, 20%) of a pass, h = 0.56 against h = 0.50 at m = 1, calibrated processes.
- E6 Cross-check against the v16 trade-level grid: headline cells quoted side by side.

## 7. Hypotheses (directional, fixed now)
- H1 For static-floor rule sets with no deadline, the zero-skill pass probability of the daily-position trader at sigma_a <= 1% stays
  within 3 percentage points of the ceiling (product of L/(T+L)) in every process, while fat tails and clustering move trailing-floor
  and daily-limit sets by more than 3 points at sigma_a = 2%.
- H2 Over the synthetic rule space the order of drop-one partial R2 for zero-skill pass probability is: target-to-loss ratio, then
  trailing-floor indicator, then daily loss limit size, then consistency rule, then minimum days.
- H3 Under Pop A and Pop D with K = 3, firm revenue per buyer is positive for at least 90% of modelled rule sets; under frictionless
  zero-skill buyers (h = 0.5, m = 0) it is negative for a majority of the static two-step sets (the v16 sign of buyer expected value).
- H4 The share of fee revenue from failed attempts exceeds 80% for every rule set under Pops A-E.
- H5 GARCH-t, FHS and bootstrap processes lower zero-skill pass rates relative to P0 by 2 to 10 points for sets with a daily limit of
  5% or less, and change static sets with no daily limit by no more than 2 points.
If any of H1-H5 fails it is reported as failed.

## Amendment 1 (2026-11-17 20:55 IST, before any E1 run, no result seen)
Measured throughput on the loaded laptop (CPU at 100% from other jobs; kernel compile alone took 318 s) makes the full E1 grid of
section 6 (about 47,000 cells) infeasible. E1 is therefore run in two tiers, fixed now:
- Tier 1 (sigma_a = 1%): every modelled rule set x 5 assets x 5 processes x [h in the 7-point grid at m = 1; plus m in {0, 4} at
  h = 0.50 and h = 0.56]. 20,000 paths.
- Tier 2 (sigma_a in {0.5%, 2%}): h in {0.50, 0.56} at m = 1 only. 10,000 paths.
- Headline cells (ES, P2, sigma_a 1%, h 0.50, m 1): 100,000 paths (five banks of 20,000, seeds 101-105).
Funded-stage payouts are simulated for every passing path in Tier 1 only (horizon 20, 60, 120 days); Tier 2 reports pass
probabilities and failure attribution only. E3b, E4 and E5 use Tier 1 outputs.
