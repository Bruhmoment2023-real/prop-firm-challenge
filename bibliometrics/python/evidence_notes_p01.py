"""Hand-written evidence notes for paper 01 (one line per paper, taken from the abstract in data/clean/master.csv).
Rows marked 'metadata only' had no abstract in OpenAlex, Crossref or Semantic Scholar: nothing is claimed about their findings.
Run: python evidence_notes_p01.py  -> data/clean/evidence_notes.json"""
import json, os
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AR = "abstract read"
MO = "metadata only (no abstract available)"
N = []
def add(i, study, country, data, method, finding, rel, status=AR):
    N.append(dict(oa_id=i, study_type=study, country=country, data=data, method=method, finding=finding, relation=rel, read_status=status))

# ---- C. prop-firm challenges (2026 working papers) and incentives
add("W7213370519", "working paper (SSRN), theory + simulation", "US futures prop firms", "firm rule sets; published cohort pass rate 0.168 (as cited in the abstract)", "stage-by-stage incentive model, simulation",
    "Passing is a poor standalone signal of skill: position sizing alone gives a zero-skill pass probability near 0.40 against a measured cohort rate of 0.168, and a real edge and aggressive sizing move the pass probability by nearly the same amount.",
    "Closest prior work: same headline claim and zero-skill control; the paper must go beyond it (likelihood ratio, base rates, optimal-test benchmark).")
add("W7202269910", "working paper (SSRN), closed-form theory", "13 products of one account size", "official contract terms of 13 products", "chain of first-passage problems with six contract parameters; checked against simulation",
    "Success probability is derived in closed form (error below 1% against simulation); across 13 products with the same advertised target and buffer it varies by 62%, entirely from parameters published but not shown beside the price.",
    "Overlaps the mathematics of the trailing barrier; read in full before claiming any closed form.")
add("W7172549950", "working paper (SSRN), pricing model", "stylised two-step challenge", "none (model); illustrative population", "arithmetic Brownian motion, Monte Carlo first-passage pricing with profit sweeps and fee refund",
    "A zero-edge trader passes the frictionless benchmark with probability 0.50 but the baseline contract with probability 0.30; contract value concentrates on a narrow risk-sizing ridge near 2 per cent daily volatility; model-implied average value of a USD 500 challenge is USD 221.",
    "Time limit as the main zero-edge penalty; two-step CFD contract. Check against firms with no time limit.")
add("W7172508446", "working paper (SSRN), hand-collected rule dataset + valuation", "21 firms, 31 contracts", "rule sets and fees displayed 25-26 July 2026 with dated screenshots", "common benchmark population of skill and volatility, 300-day evaluation cap, one-year funded horizon",
    "At displayed list prices 29 of 31 contracts have negative benchmark expected value (before several restrictive terms are included, so estimates are upper bounds).",
    "Cross-firm rule table and expected value; benchmark for Sean's ten rule sets.")
add("W7221095952", "working paper (SSRN), coded dataset", "40 firms", "public rule pages observed 5 May 2026, eleven dimensions", "systematic coding of rules",
    "A 5% daily and 10% maximum loss limit, an 80% base profit split, no time limit and MetaTrader connectivity each appear at a majority of firms; automated strategies are permitted in some form at 39 firms.",
    "Supports 'time limits are gone' and the rule-table inputs; no probability modelling.")
add("W7214609362", "working paper (SSRN), mechanism-design framing", "industry-wide", "none (model)", "mechanism design under asymmetric information; simple firm-profit-per-participant model",
    "Separates trading-funded from fee-funded revenue models and argues the dominant contemporary form is fee-funded, with consequences for the alignment of firm and participant incentives.",
    "Framing for why firms tolerate low pass rates; no simulation.")
add("W7214126987", "working paper (SSRN), simulation", "US index futures (Topstep $50,000 model)", "about 10 years of 1-minute Nasdaq futures", "10,000 randomised long/short paths; fixed-size strategy with symmetric 100-tick barriers",
    "Gross performance is about break-even (49.98% win rate), yet mean payouts of $9,368.50 exceed mean account costs of $7,878.30 (net $1,490.19 per account); 39.70% of full-sample simulations lose money.",
    "Zero edge can have positive expected value under the contract: the converse of the 'passers are skilled' reading.")
add("W7220906257", "working paper (SSRN), closed-form theory", "hedged evaluation accounts, static drawdown", "none stated", "closed-form analysis (from the title)", "No abstract in OpenAlex, Crossref or Semantic Scholar; not summarised.",
    "Hedged evaluation accounts with a static drawdown (title); read before citing.", MO)
add("W7154941387", "working paper (SSRN), vendor-linked observational study", "1,000 prop traders of one vendor", "24-month exclusive observation, 490 manual and 510 AI-assisted traders", "observational comparison, non-randomised",
    "AI-assisted traders show lower drawdowns (4.3% vs 7.8%), fewer emotionally driven exits (37.2% vs 61.7%) and a lower rule-breach rate (12.2% vs 18.4%); the author proposes a proprietary bias index.",
    "Low weight: vendor-linked, non-randomised; shows what behavioural data a firm holds.")
add("W7212033909", "journal article, qualitative sociology", "Thailand", "retail traders on forex prop-firm platforms", "sociology of finance (interpretive)",
    "Retail traders aim to become professional by passing the evaluation, but only a few succeed; the firms' main income is evaluation fees from the many who fail, secondary income is trading data from the few who succeed.",
    "Only peer-reviewed item on prop-firm challenges found; no model.")
add("W4416309300", "working paper (SSRN), mixed methods", "one prop-firm programme (coupon campaign)", "internal enrolment and performance records, sentiment analysis", "benchmark comparison",
    "A 20% discount coupon is associated with higher enrolment and completion rates, modestly higher early-stage risk exposure and better medium-term retention.", "Price sensitivity of challenge buyers; single firm.")
add("W7170163211", "working paper (arXiv), multiple-testing study", "US equities", "NASDAQ-100/SPY daily, Russell 3000 (as described in the note)", "three predeclared gates, stationary bootstrap, Benjamini-Yekutieli, equivalence tests",
    "Four of six candidate retail signal families (oscillator, volume, calendar, candlestick) are refuted on statistical and/or economic materiality, trend and a momentum benchmark are inconclusive, none is supported.",
    "Methodological model (three-way verdict); also the nearest relative for paper 02.")
add("W2125585375", "journal article, empirical", "US", "334 growth-oriented mutual funds, 1976-1991", "volatility change between mid-year winners and losers",
    "Mid-year losers raise fund volatility in the later part of the assessment year more than winners, and the effect strengthens as industry growth and investor awareness rise.", "Tournament risk-shifting: the incentive logic behind a pass/fail threshold.")
add("W2133907450", "journal article, theory", "n/a", "none (model)", "dynamic investment problem of a manager paid with a call option",
    "Under the optimal policy the option ends deep in or deep out of the money, but option compensation does not strictly lead to greater risk seeking; more options can reduce volatility.", "Capped downside plus profit share is an option; challenge fees cap the trader's loss.")
add("W2033772453", "journal article, empirical", "US", "growth and growth-and-income funds 1982-92", "semiparametric flow-performance estimation",
    "The shape of the flow-performance relationship creates incentives for managers to raise or lower fund risk depending on year-to-date standing.", "Convex payoffs and risk-taking incentives.")
add("W3122418752", "journal article, empirical (replication-type)", "US", "mutual funds, daily returns", "daily versus monthly volatility estimates",
    "With daily returns the monthly-data pattern of year-to-date underperformers raising risk disappears, suggesting earlier results were an artefact of inefficient monthly volatility estimates.", "Caution on tournament results; data-frequency artefact.")
add("W3121909572", "journal article, theory", "n/a", "none (model)", "valuation of performance fees with high-water marks; closed-form cost of the mark",
    "Hedge-fund performance fees are valuable to managers and a claim on a significant share of investor wealth; high-water marks limit their value; a closed-form cost is derived under certain conditions.", "High-water-mark path dependence resembles the trailing drawdown.")
add("W1998402685", "journal article, empirical", "hedge funds", "hedge-fund manager incentive contracts", "regression of risk shifting on contract terms",
    "Risk shifting after poor performance is weaker when pay is tied to the high-water mark, when liquidation risk is low and when the manager has a large personal stake.", "How contract terms change risk-taking.")
add("W3123642420", "journal article, theory", "n/a", "none", "analysis of gaming of performance measures",
    "If a principal judges an agent with a performance measure, the agent has an incentive to game it (abstract truncated in the record).", "A pass rate is a measure that can be gamed by reshaping the return distribution.")

# ---- A. retail trader performance
add("W3122890729", "journal article, empirical", "US", "66,465 households at a large discount broker, 1991-96", "account-level returns by turnover",
    "Households that trade most earn 11.4% a year against 17.9% for the market; the average household earns 16.4% and turns over 75% of its portfolio; overconfidence can explain the heavy trading and poor performance.", "Base rate: active retail trading lowers wealth.")
add("W3123386791", "journal article, empirical", "Taiwan", "complete trading history of all investors", "aggregate portfolio performance",
    "The aggregate portfolio of individual investors suffers an annual performance penalty of 3.8 percentage points (2.2% of GDP); virtually all losses come from aggressive orders; institutions gain 1.5 points.", "Base rate: retail traders lose in aggregate.")
add("W2113604236", "journal article, empirical", "US", "sample of day traders", "two profitability methodologies",
    "About twice as many day traders lose money as make money; roughly 20 percent are more than marginally profitable; profitability relates to Nasdaq Composite movements.", "Share of day traders with positive results.")
add("W3123078299", "journal article, empirical", "Taiwan futures", "3,470 individual day traders", "natural experiment from a margin-reduction day-trading policy",
    "Day traders incur an average significant loss of NT$61,500 after transaction costs (NT$26,700 before costs) over the sample period.", "Day-trader losses with a clean identification of day traders.")
add("W3125339824", "journal article, empirical", "Taiwan", "day-trading records (from the title)", "not stated in the record", "No abstract in OpenAlex, Crossref or Semantic Scholar; not summarised.", "Source for the share of day traders with persistent skill; read before quoting.", MO)
add("W3125905545", "journal article, clinical study", "US", "day-traders (from the title)", "not stated in the record", "No abstract available; not summarised.", "Emotion and trading performance among day traders; read before citing.", MO)
add("W3121282282", "journal article, empirical", "unknown", "not stated", "not stated", "No abstract available; not summarised.", "Learning from trading experience; read before citing.", MO)
add("W2127665088", "journal article, empirical", "US", "individual investors 1964-70 (from the title)", "not stated", "No abstract available; not summarised.", "Early performance record of individual investors.", MO)
add("W2712733770", "handbook chapter, review", "global", "not stated", "review", "No abstract available; not summarised.", "Review of retail investor behaviour by two leading authors.", MO)
add("W1858758572", "journal article, empirical", "UK", "trading records of UK individual investors, 2006-2009", "account-level analysis of stop-loss use",
    "Stop losses used as part of investment decisions are an effective tool against the disposition effect; stop-loss users have less experience.", "Stop-losses and retail behaviour.")
add("W2603143682", "journal article, empirical", "UK", "over three years of trading data on 7,200 investors", "multivariable regression",
    "Frequent trading is positively associated with being male, younger, using stop losses and using multiple trading channels.", "Who overtrades.")
add("W3123986875", "journal article, empirical", "Taiwan", "lottery jackpots and individual-investor trading", "event-style analysis around large jackpots",
    "When jackpots exceed NT$500 million, trading volume falls 5.2% to 9.1% in stocks preferred by individuals, consistent with trading as a substitute for gambling.", "Trading as gambling; relevant to challenge buyers.")
add("W4410353577", "journal article, cross-sectional survey", "Spain", "1,429 adults; 28.6% engaged in non-professional trading", "weighted latent class analysis",
    "Three subgroups of retail investors are found, the largest being crypto-traders (52.4%); the paper compares involvement, impulsivity, cognitive biases and problem gambling across them.", "Gambling overlap in retail traders.")
add("W2565774457", "journal article, survey (from the title)", "Australia", "day traders (South Australia)", "not stated", "No abstract available; not summarised.", "Day traders compared with gamblers.", MO)
add("W2949665310", "case study", "Malaysia", "one proprietary day trader at Bursa Malaysia", "single-case study",
    "Contrasting with the literature on failed traders who trade actively and speculatively, the successful proprietary trader studied is described as highly attentive (abstract truncated in the record).", "A single success case, not evidence on base rates.")
add("W59574001", "working paper (SSRN), empirical", "Taiwan futures", "trade-by-trade records of retail, foreign institutional and proprietary traders", "new discipline measures, profitability regressions",
    "Constructs trade-level measures of trading discipline and examines whether more disciplined traders are more profitable (abstract truncated).", "Discipline and profit; includes proprietary traders.")
add("W2790252415", "journal article, empirical", "unknown", "day-trading strategy data", "comparison of leverage rules (Kelly, optimal fraction)",
    "Leverage can increase profit in a popular day-trading strategy; the article relates it to the Kelly criterion and the optimal fraction criterion.", "Sizing and leverage: the lever that drives pass probability.")
add("W3138835085", "journal article, empirical", "Bitcoin futures", "one-minute candlesticks", "out-of-sample test of take-profit and stop-loss exits",
    "Taking profit after three consecutive bullish (bearish) one-minute candlesticks yields a notable positive average profit per trade, robust out of sample in an upward trend.", "Take-profit/stop-loss exits in a retail setting; check for data-snooping.")
add("W4317506856", "journal article, empirical", "US ETFs", "four market and nine sector ETFs, 2001-2021", "trailing stop-loss rules with fixed and volatility-based thresholds",
    "Thresholds of 1.0 to 1.5 standard deviations give significantly higher excess returns; most trailing stop-loss strategies post positive excess returns after costs and risk.", "Trailing stops as a rule; Sean's trailing drawdown is the mirror image.")

# ---- B. barrier, ruin and drawdown mathematics
add("W2029633324", "journal article, theory", "n/a", "none", "Laplace-transform solution of two-sided first passage for a Markov process",
    "Solves the first passage problem for a continuous Markov process leaving an interval; from the distribution of the exit time it deduces the distribution of the maximum and the range.", "Classical double-barrier exit law underlying the challenge pass/fail.")
add("W1973164504", "journal article, theory", "n/a", "none", "drawdowns and rallies of Brownian motion",
    "Determines the probability that a drawdown of a units precedes a rally of b units and applies it to stock-market crashes and rallies in the geometric Brownian motion model.", "Closest published statement of the trailing-drawdown challenge.")
add("W2119657026", "journal article, theory", "n/a", "none", "distribution of the maximum drawdown of Brownian motion with drift",
    "Gives an infinite-series representation of the distribution of the maximum drawdown and its expectation; the limiting behaviour is logarithmic (positive drift), square root (zero drift) or linear.", "Survival in the funded stage.")
add("W2104089070", "journal article, theory", "n/a", "none", "stopped diffusions with drawdown/drawup stopping times", "No abstract available; not summarised.", "General-diffusion version of drawdown stopping results.", MO)
add("W1600138544", "journal article, theory", "n/a", "none", "drawdowns and rallies with a finite horizon", "No abstract available; not summarised.", "Same question as Hadjiliadis-Vecer with a deadline.", MO)
add("W2046913100", "journal article, theory", "n/a", "none", "optimal investment under a drawdown constraint",
    "For constant relative risk aversion, the optimal policy invests in risky assets in proportion to the surplus between wealth and a fraction alpha of its running maximum.", "Investing under a drawdown constraint (the skilled trader's side).")
add("W2111302854", "journal article, theory", "n/a", "none", "growth-optimal portfolio under non-linear drawdown constraints (semimartingale model)",
    "Solves the long-term growth problem under a drawdown constraint by showing it equals an unconstrained problem with a modified utility.", "Extends Grossman-Zhou.")
add("W3123675609", "journal article, methodology", "n/a", "single and multi-scenario paths", "Conditional Drawdown risk measure", "Introduces conditional drawdown (CDD), the mean of the worst (1-alpha) drawdowns, with Maximal and Average Drawdown as limits and efficient optimisation techniques.", "Drawdown as a risk measure.")
add("W2155847265", "journal article, theory", "n/a", "none", "sensitivities to running maximum and maximum drawdown",
    "Defines new Greeks for sensitivities to the running maximum and maximum drawdown, relevant to hedge-fund net asset value and performance fees.", "High-water-mark contracts as derivatives.")
add("W3125885723", "journal article, theory", "n/a", "none", "stop-outs under serial correlation",
    "On average the recovery from a maximum quantile loss spans three times the period of accumulating it (the triple penance rule); the framework is generalised to first-order autocorrelation.", "Stop-out thresholds for managers.")
add("W2168954579", "journal article, theory", "n/a", "none", "continuity correction for discrete barrier options",
    "Discrete barrier options can be priced with remarkable accuracy using continuous-barrier formulas after a simple shift of the barrier.", "Why end-of-day-only breach checks raise zero-edge pass rates.")
add("W3124756721", "journal article, theory", "n/a", "none", "maximise probability of reaching a wealth goal by a deadline",
    "Finds the policy that maximises the probability of reaching a given wealth level by a fixed terminal time with n risky assets and a riskless one (generalising Kulldorff and Heath).", "Bold play as the way to hit a profit target.")
add("W2943161183", "journal article, theory and simulation", "n/a", "none", "four stop-loss implementations with overnight gaps and flash-crash drops", "Analyses the performance of four popular stop-loss implementations for asset prices modelled with overnight gaps and momentary price drops (abstract truncated).", "Stop-loss efficacy under gaps; relevant to breach at the stop.")
add("W2171169470", "journal article, theory", "n/a", "none", "minimising the probability of ruin for a firm with random risk process", "Solves for investment strategies that minimise the risk of ruin when bankruptcy risk cannot be eliminated.", "Ruin-minimising investment.")
add("W2105364396", "journal article, theory", "n/a", "none", "Bayesian Kelly strategy", "For log utility with an unobserved drift, the optimal bet is a fraction of wealth linear in the posterior mean increment (a generalised Kelly strategy).", "Sizing under uncertainty about edge.")
add("W2472233234", "journal article, theory", "n/a", "none", "double barrier options by path counting", "Gives analytic valuation formulas for options with two barriers (including rebates) using only defining properties of Brownian paths.", "Double-barrier exit mathematics in the option-pricing literature.")
add("W2023970747", "journal article, theory", "n/a", "none", "double barrier options via Laplace transforms", "No abstract available; not summarised.", "Double-barrier option pricing.", MO)
add("W2163276114", "handbook chapter, review", "n/a", "none", "Kelly criterion in blackjack, sports betting and the stock market", "No abstract available; not summarised.", "Standard Kelly reference.", MO)
add("W3124187603", "journal article, theory", "n/a", "none", "stop-loss rules", "No abstract available; not summarised.", "Title asks when stop-loss rules stop losses; read before citing.", MO)
add("W1484091935", "book chapter, theory", "n/a", "none", "portfolio optimisation under drawdown constraints", "No abstract available; not summarised.", "Early drawdown-constraint result.", MO)

json.dump(N, open(os.path.join(B, "data", "clean", "evidence_notes.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(N), "notes;", sum(n["read_status"] == AR for n in N), "abstract read")
