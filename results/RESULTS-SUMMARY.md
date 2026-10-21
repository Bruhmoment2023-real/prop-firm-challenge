# Results summary (plain bullets)

Run of 13 Oct 2026. 20,000 simulated paths per cell, fixed seeds, Monte Carlo standard error about 0.3 percentage points. All numbers are model outputs under the assumptions in `02-design.md`. They are not forecasts and not advice to buy any product.

Vocabulary: R = the amount risked on one trade. "Zero edge" = every trade has zero expected profit. "Rule-aware" = the trader never opens a trade whose stop would break a rule. "Naive" = fixed trade size regardless of the rules. "Ceiling" = product over phases of loss/(target + loss).

## 0. Validation (`validation.csv`, `fig1_validation.png`)

- 30 of 30 tests pass: lattice gambler's ruin (fair and biased), two-phase product, Brownian limit with and without drift, 10/30/60-day deadline against the sine series, trailing floor with and without lock and with drift, end-of-day-only monitoring against the Broadie-Glasserman-Kou correction, rule-aware sizing against the ceiling, and three funded-stage checks.
- A check over 8 independent seeds (2 million paths) found no bias: 0.4003 against 0.4000 and 0.4999 against 0.5000.
- One bug was found and fixed during the work (rule-aware sizing could still break the daily limit by floating-point rounding when the trade equalled the room left). All tables were rerun after the fix.

## 1. What the rules alone imply (`T1_closed_form_benchmarks.csv`)

| Rule set | Targets | Max loss | Floor type | Ceiling (any sizing) | Continuous-trailing value | Fee (USD) |
|---|---|---|---|---|---|---|
| FTMO 2-Step 100K | 10% then 5% | 10% | static | 0.333 | 0.333 | 605 |
| FTMO 1-Step 100K | 10% | 10% | end-of-day trailing | 0.500 | 0.368 | 559 |
| FundedNext Stellar 2-Step 100K | 8% then 5% | 10% | static | 0.370 | 0.370 | 550 |
| The5ers High Stakes 2.5K | 10% then 5% | 10% | static (assumed) | 0.333 | 0.333 | 19 |
| Topstep Combine 50K | 6% | 4% | end-of-day trailing, locks at start | 0.400 | 0.245 | 49 + 149 on passing |
| E8 One 100K | 9% | 6% | trailing (assumed intraday) | 0.400 | 0.223 | 488 |
| Alpha Pro 10% 100K | 10% then 5% | 10% | static | 0.333 | 0.333 | 497 |
| Alpha One 10% 100K | 10% | 6% | trailing (assumed intraday) | 0.375 | 0.189 | 477 |
| FunderPro Classic 100K | 10% then 5% | 10% | static | 0.333 | 0.333 | 539 |
| BrightFunded Classic 100K | 8% then 5% | 8% | static (assumed) | 0.308 | 0.308 | 534 |

- The ceiling is a theorem (optional stopping): no zero-edge strategy can pass more often if limits are hit without overshoot. It depends only on the rulebook, not on volatility or bet size.

## 2. Zero-edge pass probability (`A_zero_edge_grid.csv`, `T2*.csv`, `fig2`, `fig3`)

- Grid: 2,160 cells (10 rule sets x 6 return models x 6 risk levels x 3 trade frequencies x 2 sizing policies). 1,903 cells resolve (under 2% of paths unfinished after 750 trading days per phase); the rest are very small trade sizes and are excluded.
- Across the 1,903 resolved cells the zero-edge pass probability has median 23.6%, 5th-95th percentile 10.3%-34.9%, maximum 44.3%. 95% of cells are at or above 10%; 67% are at or above 20%.
- Headline cell (1% risk, 3 trades a day, 1:1 fixed-stop trades, rule-aware): FTMO 2-Step 33.7%, FTMO 1-Step 40.5%, FundedNext 37.5%, The5ers 33.7%, Topstep 30.2%, E8 One 25.6%, Alpha Pro 33.7%, Alpha One 22.0%, FunderPro 33.7%, BrightFunded 31.3%.
- Median trading days to pass at that cell: 41 for the 10%/5% two-step sets, 34 FundedNext, 21 FTMO 1-Step, 6 Topstep, 12 E8 One, 14 Alpha One.
- Sean's earlier project runs (14-38% for zero-edge twins) sit inside this range.

Hypotheses (see `02-design.md`):

- **H1 confirmed.** Static rule sets, fixed-stop trades, rule-aware sizing: 157 cells, mean deviation from the ceiling +0.07 points, largest 1.1 points, 156 of 157 within 3 standard errors. The pass rate does not move with risk per trade or trades per day.
- **H2 confirmed for pure trailing rules, not for the two with extra rules.** E8 One rises from 22.4% to 36.1% and Alpha One from 19.0% to 31.6% as risk per trade goes from 0.25% to 5% (one trade a day), always between the continuous-trailing value and the ceiling. FTMO 1-Step and Topstep fall below the continuous-trailing value in about a third of fixed-stop, rule-aware cells (12 of 33 and 14 of 36; across all resolved rule-aware cells 75% and 43%), because their best-day rule and daily limit bind at large sizes.
- **H3 partly confirmed.** For fixed-stop trades, rule-aware sizing beats naive sizing by 7-8 points on average and by up to 35 points in a single cell. Example: FTMO 1-Step at 1% risk, 3 trades a day passes 12.6% naive and 40.5% rule-aware (28 points). For Gaussian, Student-t and bootstrapped trades the two policies differ by under 1 point on average, because a trade without a stop cannot be made safe. In a few cells naive sizing does better (Topstep, 3% risk, 1 trade a day: 44.3% against 32.4%); this happens when a loss is allowed to jump past the floor, which real-time liquidation would prevent, so treat those cells as an artefact.
- **H4 confirmed.** No rule-aware fixed-stop cell exceeds its ceiling by more than 3 standard errors. Two naive cells do (the artefact above).
- **H7 rejected.** The return model matters more than predicted. At the headline cell the spread across the six return models is 10-13 points for the static two-step sets and 22 points for FTMO 1-Step (FTMO 2-Step: 33.7% fixed 1:1 trades, 33.3% fixed 1:2, 30.1% Gaussian, 27.5% Student-t(3), 23.5% bootstrapped EURUSD hourly, 23.1% bootstrapped Nasdaq-futures hourly). The cause is the daily loss limit: with bootstrapped returns 34-37% of attempts in resolved cells end on the daily limit, against 9% with fixed stops.

## 3. Deadlines (`E_time_limit.csv`, `fig7_time_limit.png`)

- One 10% target / 10% loss phase: no deadline gives 0.50 at any volatility. With a 30-trading-day deadline the zero-edge pass probability is 0.07 at 1% daily volatility, 0.22 at 1.5%, 0.36 at 2%, 0.48 at 3%. With 60 days: 0.20, 0.38, 0.47, 0.50. Simulation agrees with the sine-series formula once the discrete-step correction is applied.
- This is the one place where "pass probability depends on volatility" is strongly true. Seven of the eight firms read on 13 Oct 2026 state that there is no time limit (the E8 page read did not mention one either way), so this is now a historical or sensitivity result.

## 4. Economics at zero edge (`B_economics.csv`, `T3*.csv`, `fig4_expected_value.png`)

Assumptions that drive these numbers: rule-aware sizing; funded stage of 60 trading days; a payout every 10 trading days whenever the account is in profit; nothing is ever refused; list-price fees; one fee per attempt.

- Expected attempts to pass at the headline cell: 3.0 for the 10%/5% two-step sets, 2.7 FundedNext, 2.5 FTMO 1-Step, 3.3 BrightFunded, 3.4 Topstep, 4.1 E8 One, 4.8 Alpha One.
- Expected fees to reach a first funded account: about USD 1,820 FTMO 2-Step, 1,395 FTMO 1-Step, 1,483 FundedNext, 1,494 Alpha Pro, 1,620 FunderPro, 1,745 BrightFunded, 1,979 E8 One, 2,270 Alpha One, 315 Topstep 50K, 57 The5ers 2.5K.
- **With zero trading costs, expected value per purchase is positive in 67% of resolved cells** (H6 confirmed). At the headline cell: FTMO 2-Step +1,425, FTMO 1-Step +1,636, FundedNext +1,698, Alpha Pro +1,380, FunderPro +1,474, BrightFunded +1,477, Topstep +133, E8 One +93, Alpha One +18, The5ers +33 (USD). Reason: the buyer's loss is capped at the fee while a funded account gives a share of the upside with none of the downside.
- **A cost of 0.05 R per trade removes it.** Only 16% of cells stay positive. Headline cell: FTMO 2-Step -138, FTMO 1-Step -485, Alpha Pro -80, FunderPro -78, E8 One -303, Alpha One -326, The5ers -7; FundedNext +31, BrightFunded +38, Topstep +19. The same cost cuts the FTMO 2-Step pass probability from 33.3% to 13.2% at 1% risk and to 4.0% at 0.5% risk.
- The value is very sensitive to the funded horizon (FTMO 2-Step: +465 for 20 days, +1,425 for 60, +1,987 for 120) and to the return model (FTMO 2-Step: +1,425 fixed-stop, +1,270 Gaussian, +664 bootstrapped EURUSD; FTMO 1-Step: +1,636, +210, -17).
- These are upper-end figures. Firms' terms forbid gambling-style trading and allow payouts to be refused; those terms are not modelled.

## 5. How much edge changes the pass rate (`C_edge_sensitivity.csv`, `T4`, `fig5`)

- FTMO 2-Step, 1% risk, 3 trades a day, 1:1 trades: pass probability 3.9% at -0.10 R per trade, 13.2% at -0.05 R, 24.2% at -0.02 R, 33.6% at zero, 44.0% at +0.02 R, 59.6% at +0.05 R, 80.4% at +0.10 R (a 55% win rate), 97.1% at +0.20 R.
- Trade size decides how visible the edge is. Same rule set, edge +0.10 R: 99.9% at 0.25% risk, 96.6% at 0.5%, 80.4% at 1%, 60.4% at 2%, 52.6% at 3%. The zero-edge trader passes 33-34% at every size.
- Trailing one-step rules are flatter: at +0.10 R Topstep passes 49.8%, E8 One 51.2%, Alpha One 47.6% (against 30.2%, 25.4%, 21.8% at zero edge).

## 6. The pass as a test of skill (`D_skill_test.csv`, `T5`, `fig6_roc_view.png`)

"Skilled" = +0.10 R per trade. Two definitions of "unskilled": exactly zero edge, and -0.05 R (zero edge plus costs). 1% risk, 3 trades a day unless stated.

- Against a zero-edge unskilled trader the positive likelihood ratio of a pass is 2.4 for the 10%/5% two-step sets, 2.2 FundedNext, 2.3 BrightFunded, 1.9 FTMO 1-Step, 2.0 E8 One, 2.2 Alpha One, 1.6 Topstep. It can never exceed 1 / P(pass | unskilled), which is 3.0 for the common two-step design (H5 partly confirmed: 2.94 is reached at 0.5% risk on static floors, but on trailing floors the 1/ceiling cap does not hold, e.g. 3.35 for Alpha One at +0.20 R against 2.67).
- If 5% of buyers are skilled, the share of passers who are skilled is 8-11% across the ten rule sets (10% prior: 16-21%; 20% prior: 29-38%).
- Against a cost-paying unskilled trader (-0.05 R) the test is stronger and depends heavily on trade size. FTMO 2-Step likelihood ratio: 2.1 at 3% risk, 2.8 at 2%, 6.1 at 1%, 24 at 0.5%, about 465 at 0.25%. Posterior with a 5% prior: 10%, 13%, 24%, 56%, 96%.
- The firm does not choose the trade size; the trader does. A pass achieved with large trades carries little information, a pass achieved with small trades carries a lot, and the certificate does not say which it was.
- Compared with the best fixed-sample test using the same average number of trades and the same false-positive rate, the challenge is not worse (FTMO 2-Step: 80.4% true-positive rate against 74.4%). A two-barrier rule is a sequential test of the kind Wald studied, and sequential tests are efficient with data. The weakness is the operating point: a false-positive rate of 22-40% against zero-edge traders.

## What these results do not show

- They do not show what real traders do. Published cohort pass rates (7.35% FunderPro, 16.8% Topstep per account, 17.7% E8, 36.2% Take Profit Trader per test) use different denominators and are not a test of this model.
- They do not show that any firm acts unfairly.
- They do not include spreads, slippage, news rules, prohibited-strategy clauses or refused payouts, all of which lower real outcomes.
