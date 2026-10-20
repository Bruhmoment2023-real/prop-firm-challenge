# Scopus and Web of Science queries - paper 01 (zero-skill traders and retail prop-firm challenges)

Status: **not run.** There is no Scopus or Web of Science login on this machine. `scopus-drop\` was empty on 2026-10-13.
The strings mirror the three sub-literatures in `search-protocol.md`; they are broader than the OpenAlex rules (which also needed a finance-context test), so expect more noise.

How to use
- Scopus: Advanced document search -> paste -> Search -> Export -> **CSV**; tick *Citation information, Bibliographical information, Abstract & keywords, Include references* (with references the cap is 2,000 records per file: export in year slices).
- Web of Science: Advanced Search (Core Collection) -> paste -> Export -> **BibTeX** or *Plain text file*, Record Content = **Full Record and Cited References** (500 per file).
- Save each export into `bibliometrics\scopus-drop\` (`.csv`, `.bib` or `.txt`); the R script merges whatever is there with `bibliometrix::convert2df()` + `mergeDbSources()`.
- Record the date, database and number of hits under each query.

## A. Retail trader performance and day-trading profitability

Scopus
```
TITLE-ABS-KEY ( ( "day trad*" OR "retail trader*" OR "retail trading" OR "individual investor*" OR "retail investor*" OR "household investor*" OR "amateur trader*" OR "speculator skill" OR "retail forex" OR "retail FX"
    OR "contracts for difference" OR "binary option*" OR "social trading" OR "copy trading" )
  AND ( profit* OR performance OR loss* OR lose OR skill OR learning OR leverage OR gambl* OR overconfiden* OR overtrad* OR "excessive trading" ) )
AND SUBJAREA ( econ OR busi OR soci OR math OR psyc )
AND NOT TITLE ( "retail store*" OR "retail sector" OR "retail bank*" OR "retail price*" OR electricity OR energy OR "deep learning" OR "neural network*" OR "reinforcement learning" )
AND PUBYEAR > 1963 AND LANGUAGE ( english )
```
Web of Science
```
TS=(("day trad*" OR "retail trader*" OR "retail trading" OR "individual investor*" OR "retail investor*" OR "household investor*" OR "amateur trader*" OR "speculator skill" OR "retail forex" OR "retail FX"
    OR "contracts for difference" OR "binary option*" OR "social trading" OR "copy trading")
  AND (profit* OR performance OR loss* OR lose OR skill OR learning OR leverage OR gambl* OR overconfiden* OR overtrad* OR "excessive trading"))
NOT TI=("retail store*" OR "retail sector" OR "retail bank*" OR "retail price*" OR electricity OR energy OR "deep learning" OR "neural network*" OR "reinforcement learning")
AND PY=(1964-2026) AND LA=(English)
```
Refine by Web of Science Categories: Business, Finance; Economics; Management; Mathematics, Interdisciplinary Applications; Psychology, Multidisciplinary.

## B. First-passage, double-barrier, gambler's-ruin and drawdown mathematics in finance

Scopus
```
TITLE-ABS-KEY ( ( "gambler* ruin" OR "risk of ruin" OR "ruin probabilit*" OR "double barrier*" OR "two-sided exit" OR "triple barrier" OR drawdown* OR "maximum drawdown" OR "bold play" OR "how to gamble if you must"
    OR "first passage" OR "first-passage" OR "hitting time*" OR "first exit" OR "kelly criterion" OR "goal-reaching" OR "stop-loss" OR "take-profit" )
  AND ( trading OR trader* OR portfolio OR "stock price*" OR investor* OR "Brownian motion" OR finance OR financial OR betting OR "trading strateg*" ) )
AND NOT TITLE ( insurance OR reinsurance OR actuarial OR "surplus process" OR "deep learning" OR lstm OR "reinforcement learning" OR pension OR annuit* OR retirement )
AND PUBYEAR > 1963 AND LANGUAGE ( english )
AND ( LIMIT-TO ( SUBJAREA , "ECON" ) OR LIMIT-TO ( SUBJAREA , "MATH" ) OR LIMIT-TO ( SUBJAREA , "BUSI" ) OR LIMIT-TO ( SUBJAREA , "DECI" ) )
```
Web of Science
```
TS=(("gambler* ruin" OR "risk of ruin" OR "ruin probabilit*" OR "double barrier*" OR "two-sided exit" OR "triple barrier" OR drawdown* OR "maximum drawdown" OR "bold play" OR "how to gamble if you must"
    OR "first passage" OR "first-passage" OR "hitting time*" OR "first exit" OR "kelly criterion" OR "goal-reaching" OR "stop-loss" OR "take-profit")
  AND (trading OR trader* OR portfolio OR "stock price*" OR investor* OR "Brownian motion" OR finance OR financial OR betting OR "trading strateg*"))
NOT TI=(insurance OR reinsurance OR actuarial OR "surplus process" OR "deep learning" OR lstm OR "reinforcement learning" OR pension OR annuit* OR retirement)
AND PY=(1964-2026) AND LA=(English)
```
Refine by Web of Science Categories: Business, Finance; Economics; Mathematics, Interdisciplinary Applications; Statistics & Probability; Operations Research & Management Science.

## C. Proprietary trading firms, funded-trader programmes, contests and tournament incentives

Scopus
```
TITLE-ABS-KEY ( ( "proprietary trad*" OR "prop firm*" OR "prop trad*" OR "funded trader*" OR "funded account*" OR "trading contest*" OR "trading competition*" OR "trading tournament*"
    OR "investment contest*" OR "investment competition*" OR "stock market game*" OR "tournament incentive*" OR "rank-order tournament*" OR "high-water mark*" OR "convex incentive*" OR "option-like compensation"
    OR "incentive fee*" OR "risk shifting" OR "risk-shifting" OR "mutual fund tournament*" OR "professional trader*" OR leaderboard* )
  AND ( trader* OR trading OR fund OR funds OR manager* OR portfolio OR investor* ) )
AND NOT TITLE ( volcker OR football OR soccer OR tennis OR golf OR athlet* OR poker OR chess OR "executive compensation" OR electricity OR "carbon market*" )
AND PUBYEAR > 1963 AND LANGUAGE ( english )
```
Web of Science
```
TS=(("proprietary trad*" OR "prop firm*" OR "prop trad*" OR "funded trader*" OR "funded account*" OR "trading contest*" OR "trading competition*" OR "trading tournament*"
    OR "investment contest*" OR "investment competition*" OR "stock market game*" OR "tournament incentive*" OR "rank-order tournament*" OR "high-water mark*" OR "convex incentive*" OR "option-like compensation"
    OR "incentive fee*" OR "risk shifting" OR "risk-shifting" OR "mutual fund tournament*" OR "professional trader*" OR leaderboard*)
  AND (trader* OR trading OR fund OR funds OR manager* OR portfolio OR investor*))
NOT TI=(volcker OR football OR soccer OR tennis OR golf OR athlet* OR poker OR chess OR "executive compensation" OR electricity OR "carbon market*")
AND PY=(1964-2026) AND LA=(English)
```

## D. Seed check (should all be returned by the combined searches)
Barber, Odean (2000) "Trading is hazardous to your wealth"; Barber, Lee, Liu, Odean (2014) "The cross-section of speculator skill: evidence from day trading"; Brown, Harlow, Starks (1996) "Of tournaments and temptations";
Grossman, Zhou (1993) "Optimal investment strategies for controlling drawdowns"; Magdon-Ismail et al. (2004) "On the maximum drawdown of a Brownian motion"; Hadjiliadis, Vecer (2006) "Drawdowns preceding rallies in the Brownian motion model".
Scopus will not index the 2026 SSRN working papers on prop-firm challenges (Hall, Villahermosa, Tomas Fernandez, Lim, Lutsak, Youngblood, Ruether, Tran, Ng); add them by hand from `01-prior-work.md`.
