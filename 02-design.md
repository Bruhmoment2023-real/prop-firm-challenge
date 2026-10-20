# 02 - Study design

Working title (Sean to choose his own): *Is passing a prop-firm challenge evidence of skill? Zero-edge pass rates and the diagnostic value of a pass under ten published rule sets.*

Honesty note on timing: the hypotheses below were written by the research assistant on 13 Oct 2026 **before** the 20,000-path result tables in `results/` were produced, but **after** (a) reading the prior preprints, which already report zero-edge pass rates of 0.30-0.47, (b) Sean's own earlier runs (14-38%), and (c) one 2,000-path smoke test of the zero-edge grid for fixed 1:1 trades, whose pass rates were seen. H1, H2 and H4 are consequences of theorems. H3 was visible in the smoke test. H5, H6 and H7 were written without seeing any output for them. The first full run then exposed a bug in the rule-aware sizing rule (a trade exactly equal to the room left under the daily limit could still break it through floating-point rounding); the rule was corrected, the take-profit was aligned to the target, three validation tests were added, and everything was rerun. The hypotheses were not edited after any results were seen; H7 is reported as rejected. This is not blind pre-registration and the paper must not call it that. If Sean wants hypotheses of his own, he should write them down before opening `results/`.

## Research questions

- RQ1. Under each firm's published rules, how often does a trader with exactly zero edge pass the evaluation, and how much of that number is fixed by the rulebook rather than by the trader?
- RQ2. Which rule features (deadline, daily loss limit, trailing floor, monitoring frequency, consistency rule) and which trader choices (risk per trade, trades per day, rule-aware sizing) move the zero-edge pass rate, and by how much?
- RQ3. What is the expected cost per funded account and the expected value of one purchase for a zero-edge trader, under stated payout assumptions?
- RQ4. How much edge does it take to change the pass rate, and how good is "passed" as a test that separates skilled from unskilled traders (likelihood ratio, posterior probability of skill, comparison with the best possible test on the same number of trades)?

## Hypotheses (fixed before the results were run)

- H1. For rule sets with a static loss limit and no deadline, the zero-edge pass probability under rule-aware sizing equals the product over phases of loss/(target+loss) to within Monte Carlo error, whatever the risk per trade or trades per day, as long as the paths resolve. Predicted values: 0.333 for 10%/5% targets with a 10% limit; 0.370 for 8%/5% with 10%; 0.308 for 8%/5% with 8%.
- H2. For trailing-floor rule sets the zero-edge pass probability lies between the continuous-trailing value (exp(-a/d), adjusted for a lock) and the static ceiling d/(a+d), and rises towards the ceiling as trades get larger and fewer.
- H3. Naive sizing (ignoring the daily loss limit) passes strictly less often than rule-aware sizing whenever one day's trades can exceed the daily limit, and the gap grows with risk per trade.
- H4. No zero-edge cell exceeds the optional-stopping ceiling by more than Monte Carlo error when limits are hit without overshoot (fixed-stop trades, rule-aware sizing). Cells with Gaussian or fat-tailed increments may exceed it, because losses can jump past the floor.
- H5. When the unskilled trader has exactly zero edge, the likelihood ratio of a pass cannot exceed 1/ceiling (3.0 for the common two-step design). When the unskilled trader pays a per-trade cost, the likelihood ratio can be much larger, and it grows as risk per trade falls.
- H6. At zero edge and zero cost, expected value per purchase is positive for at least some rule sets and sizings (capped downside, shared upside), and a per-trade cost of 0.05 R is enough to make it negative for most.
- H7. The return model (Gaussian, Student-t with 3 degrees of freedom, fixed 1:1 and 1:2 trades, block-bootstrapped hourly EURUSD and Nasdaq-futures returns) changes zero-edge pass rates by less than 5 percentage points at the headline cell (1% risk, 3 trades per day, rule-aware sizing).

What would count against the design: H1 failing (it is a theorem, so failure means a simulator bug); H4 failing for fixed-stop trades (same).

## Method

1. **Rules.** Ten products from eight firms, each number read from the firm's own public page on 13 Oct 2026, pages archived in `data/raw/firm_pages/`, one row per number in `data/firm_rules_sourced.csv`. Where a page did not state something the table says NOT STATED and the model assumption is listed in `data/rule_sets_model.csv`. Two requested firms (Apex Trader Funding, FundingPips) refused automated access and are not modelled.
2. **Closed forms** (`code/propsim/closed_form.py`): two-barrier exit probability with and without drift; exit before a deadline (sine series); maximum-before-drawdown law for trailing floors with and without a lock; discrete-monitoring correction; lattice gambler's ruin; optional-stopping ceiling; Bayes posterior.
3. **Simulator** (`code/propsim/sim.py`): path-by-path Monte Carlo in units of account fraction. Equity is checked after every trade. Handles multi-phase challenges, static / end-of-day-trailing / intraday-trailing floors with optional lock, daily loss limit as breach or pause, minimum trading days, minimum profitable days, best-day consistency, per-phase deadline, per-trade cost, per-trade edge. Four return models. Two sizing policies. A funded-stage simulator for payouts.
4. **Validation** (`code/01_validate.py`, `results/validation.csv`): 25 tests against closed forms, 40,000-100,000 paths each. Pass criterion: within 3 standard errors for exact results, within 0.01 for the continuous-limit approximations.
5. **Experiments** (`code/02_run_experiments.py`), 20,000 paths per cell, fixed seeds:
   - A: zero-edge grid: 10 rule sets x 6 return models x 6 risk levels (0.25% to 5% per trade) x 3 trade frequencies (1, 3, 10 per day) x 2 sizing policies.
   - B: economics: pass probability, expected attempts, expected fees to a first funded account, funded-stage payouts over 60 trading days (also 20 and 120), expected value per purchase, with and without a 0.05 R per-trade cost.
   - C: pass probability against per-trade edge from -0.10 R to +0.20 R.
   - D: likelihood ratios, posterior probability of skill for priors of 1-20%, and the Neyman-Pearson benchmark.
   - E: deadline sensitivity (30 and 60 trading days) against daily volatility, closed form and simulation.
6. **Reporting.** Every probability is reported with its Monte Carlo standard error (about 0.3 percentage points at 20,000 paths). Cells in which more than 2% of paths are still unresolved after 750 trading days per phase are flagged and left out of summaries.

## Definitions the paper must state

- **Zero edge**: expected profit of every trade is zero before costs. It is a mathematical baseline, not a description of real beginners, who also pay spreads and break rules.
- **Risk per trade r**: the stop-loss size for the fixed-stop model; the standard deviation of a trade's result for the Gaussian, Student-t and bootstrap models. Always a fraction of the starting balance (no compounding).
- **Edge q**: expected profit per trade in units of r. For 1:1 trades q = 2 x (win rate) - 1, so q = 0.10 is a 55% win rate.
- **Rule-aware sizing**: never open a trade whose stop would break a rule (cut the trade to the room left above the floor; use at most 99% of the room left under today's daily limit; stop for the day when that room is under a tenth of r).
- **Pass**: all phases completed. **Payout**: at least one withdrawal in the funded stage.

## Assumptions (each is a limitation to state)

- Trades are independent and identically distributed; no skill at timing, no regime dependence in the trader's behaviour. The bootstrap keeps the volatility clustering of real hourly returns in blocks of 24 bars but imposes zero mean.
- Equity is observed after each trade only. A fixed-stop trade cannot lose more than r, so this is exact for that model. For the other models it ignores intratrade swings (optimistic for the trader).
- No spreads, commissions, swaps, slippage or gaps unless the per-trade cost is switched on.
- Position size is a fixed fraction of the starting balance.
- Rules not modelled: news and weekend restrictions, maximum lot or leverage caps, "prohibited strategies" clauses (including bans on all-or-nothing trading), inactivity expiry, payout denial at the firm's discretion, KYC failure, firm insolvency. All of these lower real pass and payout rates.
- Funded stage: payout every 10 trading days if in profit, all profit withdrawn, balance and floor reset; 60-day horizon; the futures-style account follows the published Topstep Express Funded Account rules in simplified form. These are assumptions, not published facts, and the expected values depend on them heavily.
- EUR fees converted at 1.12 USD per EUR (Yahoo close, 13 Oct 2026). List prices, not promotional prices.
- One attempt costs one fee. Topstep's monthly subscription is counted as one month per attempt.

## Threats to validity

- **Construct**: "zero-skill trader" is an idealisation. Real unskilled traders have negative edge after costs and poor rule discipline, so real pass rates should be below the simulated ones. The published cohort rates (7-36%, mixed denominators) are consistent with that but are not a test of the model.
- **Internal**: simulator bugs (mitigated by 25 closed-form tests and by H1/H4 being theorems); Monte Carlo noise (standard errors reported); discretisation (trade-level monitoring; quantified by the Broadie-Glasserman-Kou correction).
- **External**: rules change monthly (FTMO changed one rule on 12 Oct 2026); eight firms are a convenience sample of well-known names, not a random sample; two requested firms could not be read; several parameters were not stated on the pages read and were assumed.
- **Statistical conclusion**: firm-published statistics use different denominators (per account, per person, per registered user) and periods; they must not be pooled or multiplied.
- **Selection of results**: every cell of the grid is in the CSVs; summaries quote ranges, not best cases.
- **Priority**: at least eleven 2026 preprints precede this work (see `01-prior-work.md`). The paper must position itself as replication plus the diagnostic-test analysis.
