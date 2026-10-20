# Search protocol - 01-prop-firm-challenge

- Paper question: Zero-skill traders passing retail prop-firm trading challenges: first-passage and drawdown mathematics, retail trader performance, prop-firm incentives
- Date of search and data pull: **2026-10-13**
- Years covered: 1950-2026; language: English (OpenAlex language field `en` or missing)
- Built by an AI agent (Claude) with the scripts in `python\` and `R\`; all numbers below are read from the run logs.

## 1. Databases

| Role | Database | Access | Note |
|---|---|---|---|
| Discovery | Crossref REST API | free, no key, `mailto` polite pool | relevance-ranked keyword search; top N per query |
| Discovery | Semantic Scholar Graph API (bulk search) | free, no key | boolean search on title/abstract; top N by citations per query |
| Discovery | arXiv API | free, no key | preprints |
| Enrichment (authors, institutions, countries, topics, keywords, abstracts, references, citation counts, OA links) | **OpenAlex** single-record lookups (`/works/doi:...`, `/works/mag:...`, `/works/W...`) | free, no key | see limit 1 below |
| Forward citations for snowballing | Semantic Scholar Graph API (citations endpoint) | free, no key | citing records, most with DOIs |
| Cross-check | Crossref (per-DOI), Semantic Scholar (batch) | free, no key | citation counts and reference-list coverage compared in `tables\coverage_crosscheck.csv` |
| Not used | Scopus, Web of Science, Lens, Dimensions | need accounts | equivalent strings are in `scopus-queries.md` |
| Not usable | RePEc/IDEAS | its API needs a registered access code; the public search page returned no parseable result list to a script | economics working papers still enter via Crossref, Semantic Scholar and snowballing |

**Why OpenAlex was not the search engine.** Since 2026 OpenAlex charges keyless list/search calls against a small daily budget shared by everyone on the same IP address ($0.10/day). On the day of the pull that budget was already exhausted by other work on this network, and an API key needs an account (ruled out). Single-record lookups remain free and unlimited, so records were *discovered* in Crossref / Semantic Scholar / ERIC / arXiv and then *enriched* one by one from OpenAlex. Consequence: a work that is in OpenAlex but not found by any of the four discovery databases is missed, except where snowballing caught it.

## 2. Exact search strings

### a: Retail trader performance and day trading

| database | query | hits in database | records retrieved | status |
|---|---|---|---|---|
| Crossref | day trading profitability | 346369 | 200 | ok |
| Crossref | day traders performance skill | 2590483 | 200 | ok |
| Crossref | retail investors trading performance losses | 2465591 | 200 | ok |
| Crossref | individual investors trading performance common stock | 3093771 | 200 | ok |
| Crossref | retail forex traders profitability | 95699 | 200 | ok |
| Crossref | retail foreign exchange traders leverage | 778134 | 200 | ok |
| Crossref | learning by trading individual investors | 2936423 | 200 | ok |
| Crossref | do day traders learn about their ability | 2745403 | 200 | ok |
| Crossref | retail traders derivatives losses | 480048 | 200 | ok |
| Crossref | gambling stock market individual investors | 881251 | 200 | ok |
| Crossref | contracts for difference retail investors | 319994 | 200 | ok |
| Crossref | retail options trading losses | 266360 | 200 | ok |
| Crossref | overconfidence trading volume individual investors | 1986354 | 200 | ok |
| Crossref | retail traders cryptocurrency performance | 2348579 | 200 | ok |
| Semantic Scholar (bulk) | "day trading" \| "day traders" \| "day trader" \| "retail traders" \| "retail trader" \| "retail trading"  [fieldsOfStudy=Economics,Business,Mathematics,Computer Science,Psychology] | 8374 | 1000 | ok |
| Semantic Scholar (bulk) | ("individual investors" \| "retail investors") + (performance \| profitability \| losses \| skill \| overconfidence \| gambling)  [fieldsOfStudy=Economics,Business] | 4001 | 1000 | ok |
| arXiv | all:"day trading" AND cat:q-fin.* | 8 | 8 | ok |
| arXiv | all:"retail traders" AND cat:q-fin.* | 10 | 10 | ok |
| arXiv | all:"retail investors" AND all:profitability | 5 | 5 | ok |

### b: First-passage, barrier, ruin and drawdown mathematics

| database | query | hits in database | records retrieved | status |
|---|---|---|---|---|
| Crossref | gambler's ruin trading | 67764 | 200 | ok |
| Crossref | risk of ruin trading strategy | 2308755 | 200 | ok |
| Crossref | double barrier first passage time Brownian motion | 3722489 | 200 | ok |
| Crossref | double barrier option pricing | 736155 | 200 | ok |
| Crossref | maximum drawdown Brownian motion distribution | 1316131 | 200 | ok |
| Crossref | drawdown constraint portfolio optimization | 1114899 | 200 | ok |
| Crossref | trailing drawdown trading | 69529 | 200 | ok |
| Crossref | stop-loss take-profit optimal trading | 1048082 | 200 | ok |
| Crossref | probability of reaching a goal before ruin | 466316 | 200 | ok |
| Crossref | Kelly criterion drawdown | 200822 | 200 | ok |
| Crossref | first passage time trading strategy finance | 3792458 | 200 | ok |
| Crossref | triple barrier method labeling | 2301771 | 200 | ok |
| Crossref | optimal stopping trading exit barrier | 678702 | 200 | ok |
| Crossref | bold play gambling reaching a goal | 226146 | 200 | ok |
| Crossref | drawdown probability trading strategy | 838511 | 200 | ok |
| Crossref | maximizing probability of reaching a goal portfolio | 326668 | 200 | ok |
| Crossref | stop-loss rules performance | 2855114 | 200 | ok |
| Semantic Scholar (bulk) | ("gambler's ruin" \| "risk of ruin") + (trading \| finance \| investor \| portfolio \| betting \| market) | 119 | 119 | ok |
| Semantic Scholar (bulk) | drawdown + (portfolio \| trading \| "Brownian motion" \| investment)  [fieldsOfStudy=Economics,Business,Mathematics,Computer Science,Psychology] | 1898 | 1000 | ok |
| Semantic Scholar (bulk) | "double barrier" + (option \| Brownian \| "first passage" \| trading) | 347 | 347 | ok |
| Semantic Scholar (bulk) | ("first passage" \| "hitting time" \| "first exit") + (trading \| "stock price" \| portfolio \| "trading strategy" \| investor)  [fieldsOfStudy=Economics,Business,Mathematics,Computer Science,Psychology] | 256 | 256 | ok |
| Semantic Scholar (bulk) | ("stop-loss" \| "take-profit" \| "stop loss") + (trading \| portfolio \| strategy)  [fieldsOfStudy=Economics,Business,Mathematics,Computer Science,Psychology] | 719 | 719 | ok |
| Semantic Scholar (bulk) | "Kelly criterion" \| "goal-reaching" \| "bold play"  [fieldsOfStudy=Economics,Business,Mathematics,Computer Science,Psychology] | 1124 | 1000 | ok |
| arXiv | all:drawdown AND cat:q-fin.* | 245 | 200 | ok |
| arXiv | all:"gambler's ruin" AND (cat:q-fin.* OR cat:math.PR) | 40 | 40 | ok |
| arXiv | all:"double barrier" AND cat:q-fin.* | 23 | 23 | ok |
| arXiv | all:"stop-loss" AND cat:q-fin.* | 35 | 35 | ok |
| arXiv | all:"Kelly criterion" AND cat:q-fin.* | 40 | 40 | ok |
| arXiv | all:"first passage" AND cat:q-fin.TR | 8 | 8 | ok |

### c: Prop firms, funded-trader programmes, contests and tournament incentives

| database | query | hits in database | records retrieved | status |
|---|---|---|---|---|
| Crossref | proprietary trading firm traders | 174454 | 200 | ok |
| Crossref | proprietary traders behavior risk taking | 3004177 | 200 | ok |
| Crossref | funded trader program evaluation | 2643161 | 200 | ok |
| Crossref | prop firm trading challenge | 370145 | 200 | ok |
| Crossref | trading competition participants performance | 2546824 | 200 | ok |
| Crossref | trading contest risk taking | 1834610 | 200 | ok |
| Crossref | investment competition risk taking tournament | 2117843 | 200 | ok |
| Crossref | tournament incentives risk taking fund managers | 1935250 | 200 | ok |
| Crossref | mutual fund tournament risk taking | 1903272 | 200 | ok |
| Crossref | high-water mark hedge fund risk taking | 6539749 | 200 | ok |
| Crossref | convex incentives risk taking traders | 1856729 | 200 | ok |
| Crossref | stock market simulation game students trading | 2823650 | 200 | ok |
| Crossref | option-like compensation risk shifting portfolio managers | 2483951 | 200 | ok |
| Crossref | limited liability traders risk taking experiment | 2169969 | 200 | ok |
| Crossref | professional traders behavioral biases | 800680 | 200 | ok |
| Crossref | social trading platform leaderboard | 3444975 | 200 | ok |
| Crossref | rank-order tournaments risk taking contest | 2325937 | 200 | ok |
| Semantic Scholar (bulk) | "proprietary trading" \| "proprietary traders" \| "prop firm" \| "prop trading" \| "funded trader" | 559 | 559 | ok |
| Semantic Scholar (bulk) | "trading competition" \| "trading contest" \| "investment competition" \| "investment contest" \| "stock market game" \| "trading tournament" \| "investment game" \| "trading competitions" \| "trading contests" | 2068 | 1000 | ok |
| Semantic Scholar (bulk) | tournament + ("risk taking" \| "risk-taking") + (fund \| traders \| managers \| investment)  [fieldsOfStudy=Economics,Business] | 84 | 84 | ok |
| Semantic Scholar (bulk) | "high-water mark" \| "convex incentives" \| "option-like compensation" \| "incentive fees" \| "risk shifting" + (fund \| trader \| portfolio)  [fieldsOfStudy=Economics,Business,Mathematics] | 552 | 552 | ok |
| arXiv | all:"proprietary trading" | 5 | 5 | ok |
| arXiv | all:"prop firm" OR all:"funded trader" OR all:"prop trading" | 0 | 0 | ok |
| arXiv | all:"trading competition" OR all:"trading contest" | 9 | 9 | ok |
| arXiv | all:"high-water mark" AND cat:q-fin.* | 7 | 7 | ok |

Per-query retrieval caps: crossref = 200. Crossref totals are large because its search is an OR-type relevance ranking; only the top-ranked records were taken. Raw responses for every query are in `data\raw\<database>\`.

Seed arXiv ids (from the PDFs the substance agent saved in the paper folder): 2607.20093

## 3. Inclusion and exclusion rules (applied identically to search hits and snowballed records)

A record is **included** if all of the following hold:
1. It resolves to an OpenAlex work record (by DOI, MAG id, or a Crossref title match of at least 93% similarity).
2. OpenAlex type is article, review, preprint, book chapter, book, dissertation, report or other (editorials, errata, paratext, datasets, peer reviews are dropped).
3. Publication year 1950-2026; language English or unrecorded.
4. It satisfies at least one sub-literature rule below: every `include` pattern must match in title + abstract, and every `title_must` pattern must match in the title.
5. Its title does not match the exclusion pattern.

Book-series and proceedings trap: a record whose abstract is a series/proceedings blurb (detected by wording such as 'this volume constitutes the refereed proceedings', or the same abstract shared by 3+ records) is screened on its title alone; whole-volume records (titles starting 'Proceedings of', 'Front matter', etc.) are dropped.

The patterns are case-insensitive regular expressions (`\b` = word boundary, `\w*` = any word ending, `.{0,80}` = within 80 characters).

These rules are those of the earlier pass (`python\config.py`, `classify()` in `python\pipeline.py`), applied identically to search hits and snowballed records.

A record is **included in sub-literature X** if (i) a *strong* pattern of X is in the title, or two distinct strong patterns are in the abstract, or a strong abstract pattern plus a weak title pattern, or a weak title pattern with at least three distinct X patterns overall; (ii) the finance (or trader/fund) *context* pattern matches title+abstract; (iii) no *exclude* pattern matches title+abstract, no *exclude_title* pattern matches the title, and (unless a strong term is in the title) no *exclude_soft* pattern matches. The sub-literature with the highest score (4 per strong title hit + 2 per strong abstract hit + 2 per weak title hit + 1 per weak abstract hit) is the primary label. Records were also dropped for: paratext/front-matter/spam titles, retraction, document types other than article/review/preprint/chapter/book/report/dissertation, non-English language, and OpenAlex domains that are clearly outside finance (unless the title carried a finance term).

**a - Retail trader performance and day trading**

- context (required): `\b(stock|equit|financ|trader|trading|investor|invest|market|portfolio|asset|currenc|exchange rate|foreign exchange|forex|futures|option|hedge fund|mutual fund|fund manager|return|price|bitcoin|crypto|wealth|gambl|betting)\w*`
- strong: `(?<![a-z]-)(?<!ex )(?<!first )(?<!dividend )(?<!announcement )(?<!sunday )\bday[- ]trad(er|ing)`
- strong: `trading is hazardous`
- strong: `retail (fx|forex|foreign exchange|cfd|currency|derivatives?|options?) (trad|invest|client|broker)`
- strong: `(individual|retail|household|amateur) (investors?|traders?|trading)'?.{0,80}(profit|perform|los[es]|lose|skill|learn|leverag|gambl|overconfiden|overtrad)`
- strong: `(profit|performance|loss|losses|skill|learning|leverage|gambling|overconfidence).{0,60}(individual|retail|household|amateur) (investors?|traders?)`
- strong: `learning by trading`
- strong: `speculator skill`
- strong: `contracts? for differences?`
- strong: `behaviou?r of individual investors`
- weak: `individual investors?`
- weak: `retail investors?`
- weak: `retail (traders?|trading)`
- weak: `overconfiden`
- weak: `gambl`
- weak: `lotter`
- weak: `leverage`
- weak: `binary options?`
- weak: `trading (performance|profit|loss|skill|experience)`
- weak: `disposition effect`
- weak: `sensation[- ]seeking`
- weak: `excessive trading|overtrad`
- weak: `robinhood`
- weak: `(social|copy)[- ]trading`
- weak: `learn(ing)? (from|by|about) (trading|experience|their ability)`
- weak: `lose money|losses`
- weak: `amateur|novice|inexperienced`
- exclude (title+abstract): `\b(electricity|energy|power|emission|carbon) (market|trading)`
- exclude (title+abstract): `retail (store|sector|industry|chain|price|sales|bank)|retailing|retailers?\b`
- exclude (title+abstract): `\bgst\b|shopkeep|street vend|wholesale|sunday trading|merchant`
- exclude (title): `(determinants?|factors?) (of|influencing|affecting|on)\b.*(investment|investor|decision)`
- exclude (title): `investment (decisions?|intentions?|behaviou?r)(?!.*(performance|profit|loss))`
- exclude (title): `herd`
- exclude (title): `\besg\b|socially responsible|sharia|conscience|corporate social|environmental`
- exclude (title): `financial literacy`
- exclude (title): `personality|big[- ]five|religio`
- exclude (title): `intention`
- exclude (title): `perception`
- exclude (title): `\bipo\b`
- exclude (title): `mutual funds?`
- exclude (title): `robo-?advis`
- exclude (title): `tax[- ](motivated|loss)`
- exclude (title): `reinforcement learning|deep learning|neural network|\blstm\b|transformer|machine learning|deep q`
- exclude_soft: `reinforcement learning|deep learning|neural network|\blstm\b|transformer|machine learning|deep q`
- exclude_soft: `\besg\b`
- exclude_soft: `\bipo\b`
- exclude_soft: `earnings announcement`
- exclude_soft: `disclosure`

**b - First-passage, barrier, ruin and drawdown mathematics**

- context (required): `\b(stock|equit|financ|trader|trading|investor|invest|market|portfolio|asset|currenc|exchange rate|foreign exchange|forex|futures|option|hedge fund|mutual fund|fund manager|return|price|bitcoin|crypto|wealth|gambl|betting)\w*`
- strong: `gambler'?s'? ruin`
- strong: `risk of ruin`
- strong: `probabilit(y|ies) of ruin|ruin probabilit`
- strong: `double[- ]barrier`
- strong: `two[- ]sided (exit|barrier)`
- strong: `two barriers`
- strong: `draw[- ]?downs?`
- strong: `triple[- ]barrier`
- strong: `take[- ]profit`
- strong: `bold play`
- strong: `how to gamble if you must`
- strong: `goal[- ]reaching|reach(ing)? (a |the )?(goal|target)s? (by|before)`
- strong: `kelly (criterion|betting|strateg|portfolio|gambl)`
- strong: `stop[- ]loss`
- weak: `first[- ]passage`
- weak: `hitting times?`
- weak: `first[- ]exit|exit times?`
- weak: `barrier options?`
- weak: `brownian motion`
- weak: `random walk`
- weak: `absorbing (barrier|boundar)`
- weak: `optimal stopping`
- weak: `survival`
- weak: `\bruin\b`
- weak: `barriers?`
- weak: `profit target`
- weak: `stopping (rule|time)`
- weak: `path[- ]dependent`
- weak: `exit (rule|strateg)`
- exclude (title+abstract): `insur`
- exclude (title+abstract): `reinsur`
- exclude (title+abstract): `actuar`
- exclude (title+abstract): `\bclaims?\b`
- exclude (title+abstract): `cram[eé]r|lundberg`
- exclude (title+abstract): `surplus process`
- exclude (title+abstract): `dividend (problem|payment|strateg|barrier|optimi)`
- exclude (title+abstract): `\b(neuron|cell|protein|molecul|epidemi|patient|clinical|polymer|groundwater|military|troop)\w*`
- exclude (title+abstract): `credit risk|default (risk|probabilit|time)|structural model`
- exclude (title+abstract): `stop[- ]loss (reinsurance|premium|order(ing)?s? of|transform|contract)`
- exclude (title+abstract): `consumption draw|drawdown constraints? on consumption`
- exclude (title+abstract): `robot|servoing|kinodynamic|resonant|tunnel(l)?ing|geofoam|waterway|reservoir|retirement|pension|income drawdown|longevity|annuit|credit line`
- exclude (title): `reinforcement learning|deep learning|neural network|\blstm\b|transformer|machine learning|deep q`
- exclude (title): `\blstm\b|deep |reinforcement|xgboost|genetic algorithm|fuzzy|ensemble learning|quantum`
- exclude_soft: `reinforcement learning|deep learning|neural network|\blstm\b|transformer|machine learning|deep q`

**c - Prop firms, funded-trader programmes, contests and tournament incentives**

- context (required): `\b(traders?|trading|hedge funds?|mutual funds?|fund managers?|portfolio managers?|money managers?|investors?|stock market|asset managers?|investment (contest|competition|game)s?|speculat\w+)\b`
- strong: `proprietary[- ]trad`
- strong: `\bprop(rietary)?[- ](firm|shop|desk|trading|trader)s?`
- strong: `funded[- ](trader|account)`
- strong: `trading (contest|competition|tournament|championship|game|challenge)s?`
- strong: `(stock[- ]market|stock|investing|portfolio) (simulation )?(contest|competition|game|tournament)s?`
- strong: `investment (contest|competition|challenge|tournament)s?`
- strong: `tournament (incentive|behavio|risk)`
- strong: `tournaments? and temptations?`
- strong: `rank[- ]order tournaments?`
- strong: `high[- ]water ?marks?`
- strong: `convex (incentive|compensation|payoff|reward)s?`
- strong: `option[- ]like (compensation|incentive|payoff|feature|contract)s?`
- strong: `incentive fees?`
- strong: `performance fees?`
- strong: `risk[- ]shifting`
- strong: `professional traders?`
- strong: `leaderboards?`
- strong: `(mutual|hedge) fund tournaments?`
- weak: `limited liability`
- weak: `risk[- ]taking`
- weak: `relative performance`
- weak: `tournaments?`
- weak: `delegated portfolio`
- weak: `contests?`
- weak: `rankings?`
- weak: `compensation`
- weak: `investment games?`
- weak: `floor traders?|market makers?`
- weak: `career concerns`
- weak: `fund flows?`
- exclude (title+abstract): `volcker`
- exclude (title+abstract): `sports?\b|football|soccer|tennis|golf|athlet|poker|chess`
- exclude (title+abstract): `\b(electricity|energy|power|emission|carbon) (market|trading)`
- exclude (title+abstract): `\bceos?\b|executive compensation|corporate tournament`
- exclude (title+abstract): `\bbanks?\b|banking`
- exclude (title+abstract): `merger|antitrust|\btax\b|\bvat\b|insur|farm|cournot|pension`
- exclude_soft: `reinforcement learning|deep learning|neural network|\blstm\b|transformer|machine learning|deep q`

**Seeds.** Landmark titles (accepted only on a near-exact Crossref title match), four DOIs from the hub's prior-work notes and, in the second pass, every DOI or arXiv id in `01-prior-work.md`: 14 of those were missing from the corpus and were added by one-by-one OpenAlex lookup (`tables\prior_work_added.csv`). Seeds bypass the keyword rules.

A record matching several sub-literatures keeps the highest-scoring one as `sublit`.

## 4. Snowballing (one round)

- Central papers: the 25 corpus records ranked highest on local citations + topical relevance + log(global citations) - listed in `data\clean\snowball_central_papers.csv`.
- Backward: every OpenAlex `referenced_works` entry of those papers not already in the corpus (664 candidates).
- Forward: citing records from Semantic Scholar for each central paper (6116 citing records, pre-screened on title/abstract and then screened with the rules in section 3).
- All candidates were looked up in OpenAlex and screened with the rules in section 3: 14 backward and 61 forward records were added.

## 5. PRISMA-style counts

| stage | n |
|---|---|
| Records identified through database searching (all query hits) | 17670 |
|    of which from arxiv | 390 |
|    of which from crossref | 9600 |
|    of which from s2 | 7636 |
|    of which from seed | 5 |
|    of which from seed_title | 39 |
| Duplicates removed (same DOI / id / title across queries and databases) | 2276 |
| Unique records screened on title (+ abstract where the database supplied one) | 15394 |
| Removed at title pre-screen (off-topic) | 13907 |
| Records looked up in OpenAlex | 1487 |
| Duplicates removed after OpenAlex matching (same work / same title) | 59 |
| Excluded at full screen: unresolved in OpenAlex (not in corpus) | 68 |
| Included after search screening | 1073 |
| Snowball: central papers used | 25 |
| Snowball: backward-reference candidates | 664 |
| Snowball: forward-citation candidates (OpenCitations) | 6116 |
| Snowball: duplicates of corpus records | 78 |
| Snowball: included (backward) | 14 |
| Snowball: included (forward) | 61 |
| Corpus before hand-screening | 910 |
| Removed at hand-screening (see tables/hand_screen_removed.csv) | 0 |
| FINAL CORPUS | 910 |
|    with abstract | 687 |
|    with DOI | 839 |
|    with a reference list in OpenAlex | 691 |
| Distinct cited references / resolved to metadata | 12048 / 2020 |

Figure: `figures\py_01_prisma_flow.png`.

## 6. Hand-screening

After rule screening and snowballing, the agent read the titles (with source and year) of the whole corpus and removed 0 records as off-topic or mis-matched; every removal and its reason is in `tables\hand_screen_removed.csv`. This is a single-screener pass by an AI agent on titles, not a two-person human screen; borderline records were kept.

## 7. Coverage and cross-checks

| item | value |
|---|---|
| corpus records | 910.0 |
| records with DOI | 839.0 |
| found in Crossref (DOI lookup) | 780.0 |
| found in Semantic Scholar (batch DOI lookup) | 685.0 |
| Spearman corr. OpenAlex vs Crossref cited-by | 0.949 |
| Spearman corr. OpenAlex vs Semantic Scholar cited-by | 0.929 |
| median cited-by: OpenAlex | 3.0 |
| median cited-by: Crossref | 3.0 |
| median cited-by: Semantic Scholar | 5.0 |
| records with no reference list in OpenAlex | 219.0 |
|   of which Crossref holds a reference list | 9.0 |
| records with no institution/country data | 207.0 |
| records without abstract | 223.0 |
| open-access records (OpenAlex) | 558.0 |
| origin: search | 798.0 |
| origin: snowball_forward | 61.0 |
| origin: seed | 37.0 |
| origin: snowball_backward | 14.0 |
| retrieved by: search | 798.0 |
| retrieved by: snowball_forward | 61.0 |
| retrieved by: seed | 23.0 |
| retrieved by: snowball_backward | 14.0 |
| retrieved by: prior-work note | 14.0 |

- Cited references: 12048 distinct works are cited by the corpus (22499 links); 2020 of the 2020 outside the corpus were resolved to metadata for the co-citation and RPYS analyses.


### Named prior work (seed list / the substance agent's saved papers) - is it in the corpus?

| id | kind | in_corpus | title |
|---|---|---|---|
| 10.1007/s11009-009-9139-1 | doi | 1 |  |
| 10.1016/j.finmar.2013.05.006 | doi | 1 |  |
| 10.1016/j.spa.2009.01.002 | doi | 1 |  |
| 10.1080/14697680600764227 | doi | 1 |  |
| 10.1093/rfs/hhm025 | doi | 1 |  |
| 10.1093/rfs/hhn046 | doi | 1 |  |
| 10.1111/0022-1082.00288 | doi | 1 |  |
| 10.1111/1467-9965.00035 | doi | 1 |  |
| 10.1111/1540-6261.00581 | doi | 1 |  |
| 10.1111/j.1467-9965.1993.tb00044.x | doi | 1 |  |
| 10.1111/j.1540-6261.1996.tb05203.x | doi | 1 |  |
| 10.1162/qjec.2006.121.2.505 | doi | 1 |  |
| 10.1214/aoms/1177728918 | doi | 1 |  |
| 10.1214/aop/1176995770 | doi | 1 |  |
| 10.1214/aop/1176996395 | doi | 1 |  |
| 10.1239/jap/1077134674 | doi | 1 |  |
| 10.21314/jor.2015.317 | doi | 1 |  |
| 10.2139/ssrn.3423101 | doi | 1 |  |
| 10.2139/ssrn.6573599 | doi | 1 |  |
| 10.2139/ssrn.6814738 | doi | 1 |  |
| 10.2139/ssrn.7178078 | doi | 1 |  |
| 10.2139/ssrn.7184138 | doi | 1 |  |
| 10.2139/ssrn.7260819 | doi | 1 |  |
| 10.2139/ssrn.7445798 | doi | 1 |  |
| 10.2139/ssrn.7453580 | doi | 1 |  |
| 10.2139/ssrn.7514219 | doi | 1 |  |
| 10.2139/ssrn.7550538 | doi | 1 |  |
| 10.2139/ssrn.7577238 | doi | 1 |  |
| 10.2139/ssrn.7579458 | doi | 1 |  |
| 10.2307/2282848 | doi | 1 |  |
| 10.34044/j.kjss.2026.47.3.23 | doi | 1 |  |
| arXiv:2607.20093 | arxiv | 1 | Retail Trader's Ruin: An Anatomy of Popular Signal Failure |
| arXiv:2609.14859 | arxiv | 1 | Gate Design and Stage-Dependent Incentives in Retail Proprietary-Trading Evaluations: Why Passing Is Not Standalone Evidence of Skill, and Why the Product Fails to Pay Under Measured Trading Constraints |

## 8. API failures during the run

- None logged beyond normal 'not found' (404) lookups.


## 9. Scopus / Web of Science exports
- `scopus-drop\`: EMPTY - no Scopus/WoS export to merge; corpus is OpenAlex-only.
- Ready-to-paste strings: `scopus-queries.md`.
