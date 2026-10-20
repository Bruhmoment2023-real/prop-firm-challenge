"""Write config.json for paper 01 (kit format) from the earlier run's python/config.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import config as K
B = os.path.dirname(HERE)
sub = {}
for k, s in K.SUBLITS.items():
    sub[k] = dict(label=s["label"], include=["|".join("(?:%s)" % p for p in s["strong"] + s["weak"]), s["context"]],
                  strong=s["strong"], weak=s["weak"], context=s["context"], exclude=s.get("exclude", []), exclude_soft=s.get("exclude_soft", []),
                  exclude_title=s.get("exclude_title", []), crossref=s["crossref"], s2=[q for q, _ in s["s2"]], arxiv=s["arxiv"], eric=[], openalex=[])
cfg = dict(paper_id=K.PAPER, paper_title="Zero-skill traders passing retail prop-firm trading challenges: first-passage and drawdown mathematics, retail trader performance, prop-firm incentives",
           year_min=1950, year_max=2026, sublits=sub, exclude="", n_per_query={"crossref": K.CROSSREF_ROWS}, snowball_n_central=K.N_CENTRAL,
           seed_titles=K.SEED_TITLES, seed_dois=K.SEED_DOIS, seed_arxiv=K.SEED_ARXIV, manual_exclude={},
           core_terms={r"prop(rietary)?[- ](firm|trad)|funded[- ]trader|trading (challenge|contest|competition)": 3,
                       r"day[- ]trad|retail (trader|investor|forex|fx)|individual investors?": 2,
                       r"drawdown|gambler|ruin|double[- ]barrier|first[- ]passage|hitting time|stop[- ]loss|kelly": 2,
                       r"tournament|high[- ]water|incentive|risk[- ]shifting|option compensation": 1},
           n_evidence_candidates=70,
           heatmap=dict(
               title="Methods against markets and data: what kind of evidence the trader-performance, barrier-mathematics and incentive literatures rest on (coded from title + abstract)",
               row_title="Method or evidence type named in title/abstract", col_title="Market or data named in title/abstract",
               caution="Mention is not design: a paper that names 'stocks' once in its motivation counts the same as one that tests only stocks, and only title and abstract are read (about 24% of records have no abstract). Cells are not exclusive.",
               rows={"Brokerage / transaction-account data": r"\b(brokerage|broker (data|accounts?)|account[- ]level|transaction (data|records)|trade[- ]level|household (accounts?|data)|administrative data|clearinghouse)\b",
                     "Performance / skill measurement": r"\b(performance|profitab\w+|skill|alpha|sharpe|losses|lose)\b",
                     "Behavioural biases": r"\b(overconfiden\w*|disposition effect|gambl\w+|lotter\w+|sensation[- ]seeking|behaviou?ral|biases?|herd\w*)\b",
                     "Experiments / games / contests": r"\b(experiments?|experimental|laboratory|trading (contest|competition|game)s?|investment (contest|competition|game)s?|tournaments?|contests?|simulation game)\b",
                     "Closed form / first passage / ruin": r"\b(first[- ]passage|hitting times?|gambler|ruin|closed[- ]form|barrier|double[- ]barrier|absorbing|optimal stopping|brownian)\b",
                     "Drawdown / stop-loss / goal reaching": r"\b(draw[- ]?downs?|stop[- ]loss|take[- ]profit|goal[- ]reaching|kelly|bold play)\b",
                     "Monte Carlo / simulation": r"\b(monte carlo|simulat\w+|bootstrap)\b",
                     "Incentives / compensation / tournaments": r"\b(incentives?|compensation|high[- ]water|fees?|risk[- ]shifting|risk[- ]taking|convex|option[- ]like|limited liability)\b",
                     "Prop firms / funded traders": r"\b(prop(rietary)?[- ](firm|trad\w+)|funded (trader|account)s?|evaluation (phase|challenge)|trading challenge)\b"},
               cols={"Stocks / equities": r"\b(stocks?|equit\w+|share prices?|common stock)\b",
                     "Foreign exchange / CFD": r"\b(foreign exchange|forex|\bfx\b|currenc\w+|contracts? for differences?|\bcfds?\b)\b",
                     "Futures": r"\b(futures)\b",
                     "Options / derivatives": r"\b(options?|derivatives?|warrants?|binary)\b",
                     "Cryptocurrency": r"\b(bitcoin|crypto\w*)\b",
                     "Mutual / hedge funds": r"\b(mutual funds?|hedge funds?|fund managers?|portfolio managers?|money managers?)\b",
                     "Retail / individual investors": r"\b(retail|individual investors?|household|day[- ]trad\w+|amateur)\b",
                     "Brownian / continuous-time models": r"\b(brownian|diffusion|continuous[- ]time|random walk|martingale|stochastic)\b"}),
           readme_limits=["Paper 01 was built in two passes: an earlier agent ran discovery, screening, snowballing and the first R tables (python/pipeline.py, python/config.py); this pass re-used that corpus unchanged (python/adapt_to_kit.py), added any paper named in 01-prior-work.md that was missing, and ran the shared kit for the remaining analyses and figures. The older R figures are the files named R02_ ... R22_; the newer ones are R_xx / py_xx."])
json.dump(cfg, open(os.path.join(B, "config.json"), "w", encoding="utf-8"), indent=1)
print("ok")
