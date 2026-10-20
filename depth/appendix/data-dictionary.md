# Data dictionary - paper 01 (prop-firm challenges)

Row counts are lines of the file minus the header (checked 2026-10-17). "R" = amount risked on one trade; money in the simulation tables is a fraction of the starting balance unless a column name ends in `_usd`. Column meanings for simulation outputs come from `code\README.md` (conventions) and the module docstrings; where a meaning is inferred from the column name it is marked (inferred).

## A. Inputs gathered from the web (`data\`)
| File | Source and access date | Rows x cols | Contents and known problems |
|---|---|---|---|
| `data\firm_rules_sourced.csv` | firm websites listed in column `source_url`, all accessed 2026-10-13 | 110 x 9 | One published rule per row. `firm`, `product`, `account_size` (text, USD), `field` (rule name, e.g. fee, profit_target_phase1, max_daily_loss), `value_as_published` (verbatim text), `source_url`, `access_date`, `archived_file_in_data_raw_firm_pages` (local HTML/text copy), `note`. Text values, not parsed; some prices were shown in EUR or as promotions. Pages change: only the dated copy is evidence. |
| `data\published_statistics.csv` | firm pages (Topstep, E8, FunderPro, Take Profit Trader, ...), 2026-10-13 | 11 x 7 | Pass or payout statistics exactly as described by each firm: `statistic_as_described_by_firm`, `value` (text, %), `period`, `source_url`, `access_date`, `archived_file`. Denominators differ across firms (per account, per individual, per registered user), so values are not comparable. |
| `data\rule_sets_model.csv` | built by `code\build_rule_tables.py` from the two files above plus assumptions | 10 x 25 | Ten modelled rule sets. `key`, `firm`, `product`, `account_usd`; `targets` (profit targets per phase, fraction of balance, `\|`-separated); `daily_loss`, `daily_mode` (breach or pause), `max_loss`, `dd_type` (static / trail_eod / trail intraday), `lock` (level at which the trailing floor stops); `min_days`, `min_profit_days`, `profit_day_thr`, `consistency`; `time_limit` (days, 0 = none); `fee_usd`, `activation_usd`, `refund`, `split`; funded-stage terms `funded_cycle_days`, `funded_min_profit`, `funded_consistency`, `funded_mode`, `bonus_frac`; `assumptions` (free text on assumed payout timing and EUR conversion at 1.12). Several funded-stage terms are assumptions, not published rules. |
| `data\market\*_1d.csv`, `*_1h.csv` | Yahoo Finance public chart endpoint (`fetch_log.csv` has URL, access time, rows) 2026-10-13 | EURUSD_1d 5,932; EURUSD_1h 17,245; GBPUSD_1h 17,247; GC_F_1d 6,555; GC_F_1h 13,736; GSPC_1d 14,317; NDX_1d 10,338; NQ_F_1h 13,697 | `ts_utc` (timestamp, UTC), `open`, `high`, `low`, `close` (price units of the instrument). Used only to bootstrap return blocks. Problems: unofficial endpoint, adjusted/continuous futures, no volume, hourly history limited to 730 days, index daily bars stamped at the exchange open. Licence: see checklist. |
| `data\market\fetch_log.csv` | same | 8 x 8 | `symbol, interval, range, url, accessed_utc, rows, first, last`. |
| `data\raw\firm_pages\` | firm pages, 2026-10-13 | 18+ firms x (html, txt) + `fetch_log.csv`, 11 MB | Archived page copies. Third-party copyright: do not redistribute. |
| `data\raw\papers\` | Crossref metadata text, Hall (2026) html/pdf/txt | 4 files | `crossref_metadata_2026-10-13.txt`: DOI, year, authors, title, journal, volume, issue, pages (pipe-separated); Hall preprint copies (arXiv 2609.14859). |
| `data\raw\regulators\` | CourtListener search result | 24 KB | Regulator docket evidence (not redistributed here; see README). |
aw
egulators` | CourtListener search result | 24 KB | Regulator docket evidence (not redistributed here; see README). |

## B. Simulation outputs (`results\`; 20,000 paths per cell, fixed seeds, Monte Carlo SE about 0.3 percentage points)
| File | Rows | Columns (meaning) |
|---|---|---|
| `A_zero_edge_grid.csv` | 2,160 | `rule_set` key; `dist` return model (bernoulli_1to1, bernoulli_1to2, boot_EURUSD_1h, boot_NQ_1h, gauss, student_t3); `risk` stop size or per-trade sd (fraction of balance); `trades_per_day`; `policy` naive vs rule-aware; `ceiling` zero-edge ceiling of the rule set; `p_pass` pass probability; `se` its MC standard error; `p_fail_maxloss`, `p_fail_daily`, `p_fail_time` failure probabilities by cause; `p_unresolved`; `mean_days`, `median_days_pass`, `mean_trades`, `mean_trades_pass`. |
| `B_economics.csv` | 840 | adds `cost_per_trade_R` (flat cost in R), `funded_horizon_days`, `fee_usd`, `account_usd`; funded-stage `funded_mean_paid_frac`, `funded_p_any_payout`, `funded_median_paid_frac`; `ev_per_attempt_usd`, `exp_attempts_to_pass`, `exp_fees_to_first_funded_usd`, `exp_payout_given_pass_usd`, `p_paid_per_attempt`, `breakeven_payout_given_pass_usd`. |
| `C_edge_sensitivity.csv` | 900 | pass probability as a function of per-trade `edge` (units of risk): `rule_set, dist, risk, trades_per_day, edge, p_pass, se, p_unresolved, mean_trades, mean_days`. |
| `D_skill_test.csv` | 225 | the pass as a diagnostic test: `edge_skilled`, `edge_unskilled`, `tpr` (pass rate of skilled), `fpr` (pass rate of unskilled), `lr_plus` = tpr/fpr, `lr_minus`, `youden_j`, `auc_single_point`, `mean_trades`, `tpr_neyman_pearson_same_fpr` (best possible test at the same false-positive rate, inferred from name), `auc_neyman_pearson`, `lr_plus_ceiling_zero_edge` (upper bound 1/ceiling), `ppv_prior_0.01 ... 0.20` (posterior probability a passer is skilled for stated base rates). |
| `E_time_limit.csv` | 24 | `daily_vol`, `deadline_days`, `closed_form_continuous`, `closed_form_discrete_shift` (Broadie-Glasserman-Kou-type shift), `mc`, `se`, `p_fail_time`, `p_fail_maxloss`. |
| `T1`-`T5*.csv` | 10-50 | summary tables built by `03_figures_and_tables.py` from A-E (closed-form benchmarks, zero-edge summary, headline economics, best zero-edge sizing, EV by funded horizon, pass by edge, skill test at 1% risk per trade (inferred from the file names)). Columns as in the source blocks. |
| `validation.csv` | 31 | 30 closed-form tests: `test`, `exact` (formula), `mc`, `se`, `z`, `approx` (formula is an approximation), `ok`, `n` (paths), `mean_days`, `secs`, `note`. Some `z` values are large (e.g. 5.92 for daily-close sd 0.1 with the BGK approximation): those rows are approximations, flagged in `approx`/`note`. |
| `parts\*.csv`, `run_log.txt`, `validation_log.txt` | - | per-part outputs and wall-time logs. |
| `RESULTS-SUMMARY.md`, `fig1-7*.png` | - | plain-bullet summary and figures. |

## C. Literature map (`bibliometrics\`)
| File | Source and date | Size | Contents and problems |
|---|---|---|---|
| `data\raw\*.jsonl.gz`, `data\raw\*.json` | OpenAlex single-record lookups, Crossref, Semantic Scholar, arXiv; 2026-10-13 | 2,119 works; 2,020 reference records; 17,670 search hits | Raw API payloads (OpenAlex schema). Abstract text is an inverted index. |
| `data\clean\master.csv` | built by `python\kit\pipeline.py master` | 910 x 52 | One row per corpus record: `oa_id`, `doi`, `title`, `year`, authors, institutions, countries, `cited_by_count` (OpenAlex citations at pull), `local_citations` (citations from other corpus records), `n_refs`, OA fields, `sublit` (a/b/c), `origin` (search / seed / snowball), `relevance` (keyword score), `abstract`, cross-check counts (`crossref_cited_by`, `s2_citation_count`). Problems: 24% no abstract; OpenAlex keywords are machine-assigned; country data missing for roughly a fifth of records. |
| `data\clean\bibliometrix_input.csv`, `*.rds` | same | 910 rows | WoS-style fields (`AU, TI, SO, DE, ID, AB, C1, CR, TC, PY, DI, ...`) for bibliometrix; `CR` strings are synthesised from OpenAlex references. |
| `data\clean\citation_edges.csv` | same | about 2,079 edges | `citing`, `cited` OpenAlex ids, within corpus. |
| `data\clean\cited_references.csv` | same | one row per distinct cited work | `oa_id, local_citations, in_corpus, first_author, year, title, source, doi, global_citations, cr_label`. |
| `data\clean\evidence_notes.json`, `evidence_candidates.json` | hand notes / ranking | 58 / 70 | Notes behind `evidence-table.csv`. |
| `tables\*.csv`, `figures\`, `vosviewer\` | derived | 90 tables, about 74 figures | Every figure's numbers; two figure generations (see README). |

## D. Depth layer (`depth\`)
`depth\raw\` holds extracted PDF text and fetched search pages (Google Scholar result pages, Crossref JSON); `depth\citations\` the BibTeX/RIS library; `depth\reading-notes\` the notes; `depth\preprints.md` the open-copy hunt.
