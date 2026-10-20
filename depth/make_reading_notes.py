"""Write depth/reading-notes/*.md for paper 01 from the extracted PDF text (depth/raw/*.txt).
Every verbatim quotation is looked up in the text with whitespace ignored; its page number is taken from the text, and a quotation that is not found aborts the run."""
import os, re, glob, sys
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "reading-notes"); os.makedirs(OUT, exist_ok=True)
strip = lambda s: re.sub(r"\s+", "", s)

def page_of(txt, q):
    flat, idx = [], []
    for i, ch in enumerate(txt):
        if not ch.isspace():
            flat.append(ch); idx.append(i)
    flat = "".join(flat); k = flat.find(strip(q))
    if k < 0:
        sys.exit("QUOTE NOT FOUND: " + q)
    pos = idx[k]; pg = txt.rfind("[[p", 0, pos)
    return re.match(r"\[\[p(\d+)\]\]", txt[pg:pg + 12]).group(1) if pg >= 0 else "?"

NOTES = [
 dict(key="Hall", file="Hall_2026_Gate-Design-arXiv-2609.14859.txt", name="hall-2026-gate-design",
  cite="Hall, N. (2026). Gate Design and Stage-Dependent Incentives in Retail Proprietary-Trading Evaluations: Why Passing Is Not Standalone Evidence of Skill. arXiv:2609.14859 (v1, working paper, 'version 23 draft' dated 13 Sep 2026), 40 pp. https://arxiv.org/abs/2609.14859",
  status="Full text available and extracted (40 pages); text searched by keyword in full, abstract, introduction, section 5.4 (skill gradient), section 9.5 and appendix B.2 read closely. Other sections were not read end to end.",
  rq="Does the geometry of a two-stage retail prop-firm contract (evaluation, then funded account with payout gates) make passing informative about skill, and is the product positive-expected-value for the participant?",
  data="Futures strategy universe measured by the author at bar level, with a trade-level cost model (round-turn friction about 1.12 points / $2.24 on the micro contract per the introduction); three accounts studied in detail; published firm pass and payout rates (cohort rate 0.168); simulation (path counts not extracted).",
  method="Stage-by-stage model of the contract; simulation of P(pass | skill) across per-trade edges q = mu/sigma and sizing rules (Table 7); zero-edge control run through the identical pipeline for every account-level result; seller contribution-margin model (Proposition 5, shrouded-attributes analogy); pre-specified research protocol with in-sample selection and one out-of-sample validation.",
  results="Zero-skill pass probability near 0.40 from sizing alone against a measured cohort rate of 0.168. Table 7: at 5 trades a day, zero skill passes 0.434 with optimised sizing versus 0.101 with fixed sizing; real edge q = 0.05 at fixed sizing gives 0.394. Break-even lies between a 40.5% and 41.5% win rate at 1:1.5 net of costs against a driftless 40.0%. No measured strategy configuration clears break-even on any account structure sourced. Two firm families with inverted rule architectures differ by a factor of 1.7 in pass rate.",
  limits="Authors state: the payout rate is 'the paper's thinnest empirical footing' (four values, range over two to one, transparency bias runs towards the conclusion); the belief gap behind Proposition 5 is unmeasured and would need a survey; a full deflated-Sharpe treatment of two near-survivors is left undone; the claim of a conserved joint rate across firms from an earlier draft was withdrawn.",
  quotes=["make passing a poor standalone signal of skill", "The pass rate confounds skill with sizing at roughly equal weight.", "The evaluation is a filter. The question is how strong a filter, and against what.", "Every account-level result is reported against a zero-edge control through the identical pipeline"],
  bears="CONTRADICTS the novelty of 'a pass is weak evidence of skill' and SUPPORTS the zero-edge pass probability (about 0.40 with sizing). LEAVES A GAP: P(pass | skill) is given, but no likelihood ratio, no posterior for a passer under stated base rates, no optimal-test benchmark (keyword search of the full text finds none). Method to borrow: zero-edge control through the identical pipeline."),
 dict(key="Darmanin", file="Darmanin_2026_Retail-Trader-s-Ruin-An-Anatomy-of-Popular-Signal-Failu.txt", name="darmanin-2026-retail-ruin",
  cite="Darmanin, A. (2026). Retail Trader's Ruin: An Anatomy of Popular Signal Failure. arXiv:2607.20093 [q-fin.ST], v1, 22 Jul 2026, 12 pp. https://arxiv.org/abs/2607.20093",
  status="Full text extracted (12 pages); abstract, introduction and section 8 (limitations) read; results sections skimmed only.",
  rq="Do five widely promoted retail signal families (trend, oscillator, candlestick, volume, calendar) deliver a positive, net-of-cost, survivable edge?",
  data="Index-level series (trend, oscillator, calendar) and point-in-time cross-sectional equity panels (volume, candlestick, momentum benchmark); an EU CFD leverage/margin arm; FINRA- and ESMA-anchored leverage scenarios.",
  method="Three predeclared family-level gates (statistical edge after multiplicity correction, economic viability after costs, finite-bankroll survival under leverage); exposure-matched benchmarks; stationary-bootstrap intervals; hierarchical Benjamini-Yekutieli control; one-sided claim-exclusion and equivalence tests; verdicts REFUTED / INCONCLUSIVE / SUPPORTED.",
  results="Four of six candidates (oscillator, volume, calendar, candlestick) refuted; trend and a momentum benchmark inconclusive; none supported. Survival is not the binding constraint at the US headline leverage scenario but becomes discriminating for trend and oscillator in the higher-leverage EU CFD scenario.",
  limits="No pristine holdout (data and rules examined in earlier repository work); families run on different universes; candlestick excluded from the survival gate; no margin or liquidity dataset, costs are a fixed-bps convention; no external peer review; AI-assisted (Claude Code disclosure on page 10).",
  quotes=["No existing study composes all three conditions into one joint falsification test", "has not undergone external peer review"],
  bears="METHOD TO BORROW: three-way verdict with equivalence tests and bankroll-survival gate. Also the nearest relative of paper 02 (retail signal families with multiplicity control). No prop-firm contract is modelled, so it does not overlap the pass-probability question."),
 dict(key="Ketmanee", file="Ketmanee_2026_The-process-of-becoming-a-digital-labor-of-retail-trade.txt", name="ketmanee-2026-digital-labor",
  cite="Ketmanee, T. (2026). The process of becoming a digital labor of retail traders on the forex proprietary firms' trading platform. Kasetsart Journal of Social Sciences 47, 470323. https://doi.org/10.34044/j.kjss.2026.47.3.23 (CC BY-NC-ND)",
  status="Full text extracted (11 pages); abstract, methodology and conclusion read.",
  rq="How do Thai retail traders become 'digital labor' on forex prop-firm platforms (sociology of finance)?",
  data="Articles, books, research and online media on retail traders and prop firms; participant observation by the author taking part in an evaluation; face-to-face ethnographic interviews with successful and failed Thai retail traders (number of interviewees not extracted).",
  method="Qualitative: documentary analysis, participant observation, ethnographic interviews.",
  results="Retail traders aspire to become professional funded traders; only a few succeed; per the abstract the firms' main income is evaluation fees from the many who fail and the secondary income is use of the trading data of the few who succeed; both groups are framed as exploited digital labor.",
  limits="Qualitative, one country, no quantitative pass-rate data in the extracted text; not checked for stated limitations section.",
  quotes=["Forex prop firms’ main income comes from charging fees in the trading evaluation of most failed retail traders", "taking part in the trading evaluation to become a Forex prop trader like other retail traders"],
  bears="Context only: the only peer-reviewed paper on prop-firm challenges found; supports the 'fees from failures' revenue description but offers no probability model. Cite as the social-science view."),
 dict(key="Carpenter", file="Carpenter_2000_Does-Option-Compensation-Increase-Managerial-Risk-Appet.txt", name="carpenter-2000-option-compensation",
  cite="Carpenter, J. N. (2000). Does Option Compensation Increase Managerial Risk Appetite? Journal of Finance 55(5), Oct 2000; first page 2311 as printed on the saved copy.",
  status="Full text extracted (22 pages); abstract, introduction, Proposition 1 and conclusion read; proofs not checked.",
  rq="How does a risk-averse manager paid with a call option on the assets he controls choose portfolio volatility dynamically?",
  data="None (theory).", method="Dynamic investment problem solved by concavifying the objective function; examples with CRRA and HARA utility.",
  results="The option ends up either deep in or deep out of the money; volatility goes to infinity as asset value goes to zero; but option compensation does not strictly increase risk seeking: volatility is moderated as asset value grows and can be below own-account volatility; more options make the manager reduce volatility for constant or decreasing absolute risk aversion.",
  limits="Theory with a single manager and unhedgeable option; equilibrium not modelled (the paper says the solution could serve in one).",
  quotes=["the option ends up either deep in or deep out of the money", "giving the manager more options causes him to reduce volatility", "can lead to dramatic increases in volatility"],
  bears="SUPPORTS the framing of a capped-downside, profit-share contract as an option; WARNS that convexity does not mechanically imply more risk taking, so predictions about funded-trader behaviour need care."),
 dict(key="Ivkovi", file="Ivkovi_2008_Portfolio-Concentration-and-the-Performance-of-Individu.txt", name="ivkovic-2008-concentration",
  cite="Ivkovic, Z., Sialm, C. and Weisbenner, S. (2004/2008). Portfolio Concentration and the Performance of Individual Investors. NBER Working Paper 10675 (Aug 2004); published in the Journal of Financial and Quantitative Analysis (2008, per the OpenAlex record). Working-paper version read.",
  status="Full text extracted (52 pages, working-paper version); abstract and selected descriptive and results passages read.",
  rq="Do individual investors with concentrated stock portfolios earn better returns on their trades than diversified investors?",
  data="Positions, trades and demographics of a large number of households at a US discount broker, 1991-1996.", method="Cross-sectional regressions of excess returns on trades by concentration; portfolio analysis of positions; robustness to turnover, inside information, concentration measures.",
  results="Stocks bought by concentrated households outperform those bought by diversified households; a portfolio-based estimate of 2.8 percentage points annualised is printed beside 4.8 for the cross-sectional regression (p. 31; units of the 4.8 not verified); stronger for large accounts, non-S&P 500 and local stocks; essentially all of the differential comes from purchases, not sales.",
  limits="Single broker, single period (1991-96), US only; authors interpret the result as information advantage, not proved to be skill.",
  quotes=["the stock trades by households with concentrated portfolios outperform those with diversified portfolios", "suggesting that some of these concentrated households have superior information processing skills"],
  bears="Evidence that SOME individual investors have skill-like outcomes (a prior for the share of skilled traders), but not about day traders or leveraged FX; use with caution in a base-rate argument."),
 dict(key="Cherny", file="Cherny_2013_Portfolio-optimisation-under-non-linear-drawdown-constr.txt", name="cherny-2013-drawdown",
  cite="Cherny, V. and Obloj, J. (2013). Portfolio optimisation under non-linear drawdown constraints in a semimartingale financial model. Finance and Stochastics (per the OpenAlex record; volume and pages not verified). arXiv:1110.6289v3.",
  status="arXiv version, full text extracted (31 pages); abstract and introduction read, proofs not checked.",
  rq="Maximise the long-run growth rate of expected utility of wealth when wealth must stay above a function of its running maximum.",
  data="None (theory).", method="Show the drawdown problem is equivalent to an unconstrained problem with a modified utility function; explicit value function and policy; Azema-Yor processes; extends Grossman and Zhou (1993) and Cvitanic and Karatzas.",
  results="Both the value function and the optimal policy for the drawdown problem are given explicitly in terms of those of the unconstrained problem, for a general semimartingale market, utility class and drawdown function.",
  limits="Asymptotic growth-rate criterion; no empirical content.",
  quotes=["equivalent to an unconstrained problem", "typically many investors have a stop-loss provision"],
  bears="Background for the funded-stage side (a trader investing under a trailing floor); not needed for the pass-probability result."),
 dict(key="MagdonIsmail", file="MagdonIsmail_2004_On-the-maximum-drawdown-of-a-Brownian-motion.txt", name="magdon-ismail-2003-max-drawdown",
  cite="Magdon-Ismail, M., Atiya, A., Pratap, A. and Abu-Mostafa, Y. (2003). The Maximum Drawdown of the Brownian Motion. CIFEr'03, Hong Kong (IEEE), 5 pp. NOTE: the open PDF in pdfs\\ is this conference version, not the Journal of Applied Probability 41(1), 2004 article of the same group that the evidence table lists.",
  status="Full text extracted (5 pages) and read.",
  rq="Expected maximum drawdown of a trading system that follows Brownian motion with drift, and its relation to the Sharpe ratio.",
  data="None (theory).", method="Drawdown process shown equivalent to Brownian motion with drift -mu and one absorbing and one reflecting barrier; first-passage formulas; continuous case as the limit of the discrete case; universal functions Qp and Qn.",
  results="Cases mu > 0, mu = 0 and mu < 0 give qualitatively different formulas; expected MDD for mu > 0 relates to Sharpe^2 T through a universal function; formulas give a baseline against which an observed drawdown can be judged.",
  limits="Assumes a plain Brownian-motion equity curve with no reinvestment; the authors say other process models could differ.",
  quotes=["The maximum drawdown MDD is the most widespread risk measure among money managers and hedge funds.", "the drawdown process is equivalent to a Brownian motion with drift -p and one absorbing barrier and one reflecting barrier"],
  bears="METHOD TO BORROW for funded-stage survival and for the expected drawdown of a zero-edge account; confirm numbers against the 2004 journal version before citing."),
 dict(key="Chevalier", file="Chevalier_1997_Risk-Taking-by-Mutual-Funds-as-a-Response-to-Incentives.txt", name="chevalier-1997-mutual-fund-risk",
  cite="Chevalier, J. and Ellison, G. (1997). Risk Taking by Mutual Funds as a Response to Incentives. Journal of Political Economy (1997, per the OpenAlex record; volume and pages not verified).",
  status="ABSTRACT ONLY. The downloaded 55-page PDF is a scan whose text layer is unreadable (rotated pages; extraction returns garbage), so no full-text note could be made. The abstract below is the one held in OpenAlex.",
  rq="Do mutual-fund companies take risk in response to the shape of the flow-performance relationship?", data="Growth and growth-and-income funds, 1982-92 (abstract).", method="Semiparametric estimate of the flow-performance relationship (abstract).",
  results="From the abstract: the shape of the flow-performance relationship creates incentives for managers to raise or lower fund risk depending on the fund's year-to-date performance. No numbers were read.",
  limits="Not read.", quotes=[], bears="Background on tournament-style risk shifting; needs a proper read of the scan (OCR) before any citation of its numbers."),
]
idx = ["# Reading notes - index (paper 01)\n", "Notes are built from the extracted PDF text in `depth\\raw\\`. Quotation page numbers are PDF page numbers of the saved copy (looked up by script, not typed). Only 8 open-access PDFs could be downloaded (see `bibliometrics\\pdfs\\download_log.csv`); most core papers sit behind publisher or SSRN blocks (HTTP 403, not worked around).\n",
       "| File | Paper | Status | One-line takeaway |", "|---|---|---|---|"]
take = {"hall-2026-gate-design": "Pass probability rises with skill but sizing moves it as much: pass rate confounds skill and sizing; no likelihood ratio or base-rate step.",
        "darmanin-2026-retail-ruin": "Three-gate falsification of retail signal families; 4 of 6 refuted, none supported.",
        "ketmanee-2026-digital-labor": "Only peer-reviewed prop-firm paper; qualitative, firms earn mainly from failed evaluations.",
        "carpenter-2000-option-compensation": "Option pay does not strictly raise risk seeking; payoffs end deep in or out of the money.",
        "ivkovic-2008-concentration": "Concentrated households' purchases outperform: some individual investors look skilled.",
        "cherny-2013-drawdown": "Drawdown-constrained growth problem reduces to an unconstrained one.",
        "magdon-ismail-2003-max-drawdown": "Expected maximum drawdown of Brownian motion with drift, linked to Sharpe ratio (conference version).",
        "chevalier-1997-mutual-fund-risk": "Abstract only (scan unreadable): flow-performance shape drives fund risk-taking."}
for n in NOTES:
    txt = open(os.path.join(D, "raw", n["file"]), encoding="utf-8").read()
    q = [f"- \"{s}\" (p. {page_of(txt, s)})" for s in n["quotes"]]
    body = [f"# {n['cite'].split('. ')[0]} - {n['name']}\n", f"**Citation.** {n['cite']}\n", f"**Read status.** {n['status']}\n", f"**Research question.** {n['rq']}\n", f"**Data and sample.** {n['data']}\n",
            f"**Method and identification.** {n['method']}\n", f"**Main results.** {n['results']}\n", f"**Limitations stated by the authors.** {n['limits']}\n",
            "**Verbatim quotations (PDF page numbers).**\n" + ("\n".join(q) if q else "- none (no readable text)") + "\n", f"**How it bears on Sean's paper.** {n['bears']}\n"]
    open(os.path.join(OUT, n["name"] + ".md"), "w", encoding="utf-8").write("\n".join(body))
    idx.append(f"| [{n['name']}.md]({n['name']}.md) | {n['cite'].split('(')[0].strip()} ({n['cite'].split('(')[1].split(')')[0]}) | {n['status'].split(';')[0].split('.')[0]} | {take[n['name']]} |")
open(os.path.join(OUT, "00-index.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")
print(len(NOTES), "notes written")
