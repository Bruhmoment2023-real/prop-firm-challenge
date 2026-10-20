"""Search + screening configuration: Paper 01 - zero-skill traders passing retail prop-firm challenges."""
PAPER = "01-prop-firm-challenge"
PAPER_TITLE = "Zero-skill traders and retail prop-firm challenges"
SEARCH_DATE = "2026-10-13"
CROSSREF_ROWS = 200
N_CENTRAL = 25
REF_MIN_CITES = 2

FIN_CTX = (r"\b(stock|equit|financ|trader|trading|investor|invest|market|portfolio|asset|currenc|exchange rate|foreign exchange|forex|futures|"
           r"option|hedge fund|mutual fund|fund manager|return|price|bitcoin|crypto|wealth|gambl|betting)\w*")
TRADER_CTX = (r"\b(traders?|trading|hedge funds?|mutual funds?|fund managers?|portfolio managers?|money managers?|investors?|stock market|"
              r"asset managers?|investment (contest|competition|game)s?|speculat\w+)\b")
S2_FOS = "Economics,Business,Mathematics,Computer Science,Psychology"
ML = r"reinforcement learning|deep learning|neural network|\blstm\b|transformer|machine learning|deep q"

SUBLITS = {
    "a": dict(
        label="Retail trader performance and day trading",
        strong=[r"(?<![a-z]-)(?<!ex )(?<!first )(?<!dividend )(?<!announcement )(?<!sunday )\bday[- ]trad(er|ing)", r"trading is hazardous",
                r"retail (fx|forex|foreign exchange|cfd|currency|derivatives?|options?) (trad|invest|client|broker)",
                r"(individual|retail|household|amateur) (investors?|traders?|trading)'?.{0,80}(profit|perform|los[es]|lose|skill|learn|leverag|gambl|overconfiden|overtrad)",
                r"(profit|performance|loss|losses|skill|learning|leverage|gambling|overconfidence).{0,60}(individual|retail|household|amateur) (investors?|traders?)",
                r"learning by trading", r"speculator skill", r"contracts? for differences?", r"behaviou?r of individual investors"],
        weak=[r"individual investors?", r"retail investors?", r"retail (traders?|trading)", r"overconfiden", r"gambl", r"lotter", r"leverage", r"binary options?",
              r"trading (performance|profit|loss|skill|experience)", r"disposition effect", r"sensation[- ]seeking", r"excessive trading|overtrad",
              r"robinhood", r"(social|copy)[- ]trading", r"learn(ing)? (from|by|about) (trading|experience|their ability)", r"lose money|losses",
              r"amateur|novice|inexperienced"],
        context=FIN_CTX,
        exclude=[r"\b(electricity|energy|power|emission|carbon) (market|trading)", r"retail (store|sector|industry|chain|price|sales|bank)|retailing|retailers?\b",
                 r"\bgst\b|shopkeep|street vend|wholesale|sunday trading|merchant"],
        exclude_soft=[ML, r"\besg\b", r"\bipo\b", r"earnings announcement", r"disclosure"],
        exclude_title=[r"(determinants?|factors?) (of|influencing|affecting|on)\b.*(investment|investor|decision)", r"investment (decisions?|intentions?|behaviou?r)(?!.*(performance|profit|loss))",
                       r"herd", r"\besg\b|socially responsible|sharia|conscience|corporate social|environmental", r"financial literacy", r"personality|big[- ]five|religio",
                       r"intention", r"perception", r"\bipo\b", r"mutual funds?", r"robo-?advis", r"tax[- ](motivated|loss)", ML],
        crossref=["day trading profitability", "day traders performance skill", "retail investors trading performance losses", "individual investors trading performance common stock",
                  "retail forex traders profitability", "retail foreign exchange traders leverage", "learning by trading individual investors", "do day traders learn about their ability",
                  "retail traders derivatives losses", "gambling stock market individual investors", "contracts for difference retail investors", "retail options trading losses",
                  "overconfidence trading volume individual investors", "retail traders cryptocurrency performance"],
        s2=[('"day trading" | "day traders" | "day trader" | "retail traders" | "retail trader" | "retail trading"', S2_FOS),
            ('("individual investors" | "retail investors") + (performance | profitability | losses | skill | overconfidence | gambling)', "Economics,Business")],
        arxiv=['all:"day trading" AND cat:q-fin.*', 'all:"retail traders" AND cat:q-fin.*', 'all:"retail investors" AND all:profitability'],
    ),
    "b": dict(
        label="First-passage, barrier, ruin and drawdown mathematics",
        strong=[r"gambler'?s'? ruin", r"risk of ruin", r"probabilit(y|ies) of ruin|ruin probabilit", r"double[- ]barrier", r"two[- ]sided (exit|barrier)", r"two barriers",
                r"draw[- ]?downs?", r"triple[- ]barrier", r"take[- ]profit", r"bold play", r"how to gamble if you must",
                r"goal[- ]reaching|reach(ing)? (a |the )?(goal|target)s? (by|before)", r"kelly (criterion|betting|strateg|portfolio|gambl)", r"stop[- ]loss"],
        weak=[r"first[- ]passage", r"hitting times?", r"first[- ]exit|exit times?", r"barrier options?", r"brownian motion", r"random walk", r"absorbing (barrier|boundar)",
              r"optimal stopping", r"survival", r"\bruin\b", r"barriers?", r"profit target", r"stopping (rule|time)", r"path[- ]dependent", r"exit (rule|strateg)"],
        context=FIN_CTX,
        exclude=[r"insur", r"reinsur", r"actuar", r"\bclaims?\b", r"cram[eé]r|lundberg", r"surplus process", r"dividend (problem|payment|strateg|barrier|optimi)",
                 r"\b(neuron|cell|protein|molecul|epidemi|patient|clinical|polymer|groundwater|military|troop)\w*", r"credit risk|default (risk|probabilit|time)|structural model",
                 r"stop[- ]loss (reinsurance|premium|order(ing)?s? of|transform|contract)", r"consumption draw|drawdown constraints? on consumption",
                 r"robot|servoing|kinodynamic|resonant|tunnel(l)?ing|geofoam|waterway|reservoir|retirement|pension|income drawdown|longevity|annuit|credit line"],
        exclude_soft=[ML],
        exclude_title=[ML, r"\blstm\b|deep |reinforcement|xgboost|genetic algorithm|fuzzy|ensemble learning|quantum"],
        crossref=["gambler's ruin trading", "risk of ruin trading strategy", "double barrier first passage time Brownian motion", "double barrier option pricing",
                  "maximum drawdown Brownian motion distribution", "drawdown constraint portfolio optimization", "trailing drawdown trading", "stop-loss take-profit optimal trading",
                  "probability of reaching a goal before ruin", "Kelly criterion drawdown", "first passage time trading strategy finance", "triple barrier method labeling",
                  "optimal stopping trading exit barrier", "bold play gambling reaching a goal", "drawdown probability trading strategy", "maximizing probability of reaching a goal portfolio",
                  "stop-loss rules performance"],
        s2=[('("gambler\'s ruin" | "risk of ruin") + (trading | finance | investor | portfolio | betting | market)', None),
            ('drawdown + (portfolio | trading | "Brownian motion" | investment)', S2_FOS),
            ('"double barrier" + (option | Brownian | "first passage" | trading)', None),
            ('("first passage" | "hitting time" | "first exit") + (trading | "stock price" | portfolio | "trading strategy" | investor)', S2_FOS),
            ('("stop-loss" | "take-profit" | "stop loss") + (trading | portfolio | strategy)', S2_FOS),
            ('"Kelly criterion" | "goal-reaching" | "bold play"', S2_FOS)],
        arxiv=['all:drawdown AND cat:q-fin.*', 'all:"gambler\'s ruin" AND (cat:q-fin.* OR cat:math.PR)', 'all:"double barrier" AND cat:q-fin.*',
               'all:"stop-loss" AND cat:q-fin.*', 'all:"Kelly criterion" AND cat:q-fin.*', 'all:"first passage" AND cat:q-fin.TR'],
    ),
    "c": dict(
        label="Prop firms, funded-trader programmes, contests and tournament incentives",
        strong=[r"proprietary[- ]trad", r"\bprop(rietary)?[- ](firm|shop|desk|trading|trader)s?", r"funded[- ](trader|account)",
                r"trading (contest|competition|tournament|championship|game|challenge)s?", r"(stock[- ]market|stock|investing|portfolio) (simulation )?(contest|competition|game|tournament)s?",
                r"investment (contest|competition|challenge|tournament)s?", r"tournament (incentive|behavio|risk)", r"tournaments? and temptations?", r"rank[- ]order tournaments?",
                r"high[- ]water ?marks?", r"convex (incentive|compensation|payoff|reward)s?", r"option[- ]like (compensation|incentive|payoff|feature|contract)s?",
                r"incentive fees?", r"performance fees?", r"risk[- ]shifting", r"professional traders?", r"leaderboards?", r"(mutual|hedge) fund tournaments?"],
        weak=[r"limited liability", r"risk[- ]taking", r"relative performance", r"tournaments?", r"delegated portfolio", r"contests?", r"rankings?", r"compensation",
              r"investment games?", r"floor traders?|market makers?", r"career concerns", r"fund flows?"],
        context=TRADER_CTX, context_name="trader/fund",
        exclude=[r"volcker", r"sports?\b|football|soccer|tennis|golf|athlet|poker|chess", r"\b(electricity|energy|power|emission|carbon) (market|trading)",
                 r"\bceos?\b|executive compensation|corporate tournament", r"\bbanks?\b|banking", r"merger|antitrust|\btax\b|\bvat\b|insur|farm|cournot|pension"],
        exclude_soft=[ML],
        crossref=["proprietary trading firm traders", "proprietary traders behavior risk taking", "funded trader program evaluation", "prop firm trading challenge",
                  "trading competition participants performance", "trading contest risk taking", "investment competition risk taking tournament", "tournament incentives risk taking fund managers",
                  "mutual fund tournament risk taking", "high-water mark hedge fund risk taking", "convex incentives risk taking traders", "stock market simulation game students trading",
                  "option-like compensation risk shifting portfolio managers", "limited liability traders risk taking experiment", "professional traders behavioral biases",
                  "social trading platform leaderboard", "rank-order tournaments risk taking contest"],
        s2=[('"proprietary trading" | "proprietary traders" | "prop firm" | "prop trading" | "funded trader"', None),
            ('"trading competition" | "trading contest" | "investment competition" | "investment contest" | "stock market game" | "trading tournament" | "investment game" | "trading competitions" | "trading contests"', None),
            ('tournament + ("risk taking" | "risk-taking") + (fund | traders | managers | investment)', "Economics,Business"),
            ('"high-water mark" | "convex incentives" | "option-like compensation" | "incentive fees" | "risk shifting" + (fund | trader | portfolio)', "Economics,Business,Mathematics")],
        arxiv=['all:"proprietary trading"', 'all:"prop firm" OR all:"funded trader" OR all:"prop trading"', 'all:"trading competition" OR all:"trading contest"', 'all:"high-water mark" AND cat:q-fin.*'],
    ),
}

# Papers named in the hub's prior-work notes (track-A-quant-finance.md, entries C1, L3, L4, D1) - must all be in the corpus
SEED_DOIS = ["10.1016/B978-0-44-459406-8.00022-6", "10.1016/j.finmar.2013.05.006", "10.2139/ssrn.3423101", "10.2469/faj.v59.n6.2578"]
SEED_ARXIV = ["2607.20093"]
# Analyst-supplied landmark titles; each is accepted only if Crossref returns a near-exact title match
SEED_TITLES = [
    "Trading Is Hazardous to Your Wealth: The Common Stock Investment Performance of Individual Investors",
    "Do Day Traders Rationally Learn About Their Ability?",
    "The cross-section of speculator skill: Evidence from day trading",
    "Day trading for a living?",
    "Reaching goals by a deadline: digital options and continuous-time active portfolio management",
    "Of Tournaments and Temptations: An Analysis of Managerial Incentives in the Mutual Fund Industry",
    "Risk Taking by Mutual Funds as a Response to Incentives",
    "Does Option Compensation Increase Managerial Risk Appetite?",
    "High-Water Marks and Hedge Fund Management Contracts",
    "Do Behavioral Biases Affect Prices?",
    "On the maximum drawdown of a Brownian motion",
    "Optimal Investment Strategies for Controlling Drawdowns",
    "Peer Pressure: Social Interaction and the Disposition Effect",
    "Should Retail Investors' Leverage Be Limited?",
    "Rank-Order Tournaments as Optimum Labor Contracts",
    "Are Professional Traders Too Slow to Realize Their Losses?",
    "Professional trader discipline and trade disposition",
    "Survival and Growth with a Liability: Optimal Portfolio Strategies in Continuous Time",
    "When Do Stop-Loss Rules Stop Losses?",
    "The Behavior of Individual Investors",
]
SEED_DEFAULT_SUBLIT = {}
