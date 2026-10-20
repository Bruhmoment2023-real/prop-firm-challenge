"""Validate the Monte Carlo simulator against closed-form results.

Usage:  python code/01_validate.py            (about 1-2 minutes of CPU on a laptop)
Writes results/validation.csv.  A row passes if |MC - exact| <= 3 standard errors (z column),
or, for the two approximations (flagged approx), if the absolute gap is below 0.01.
"""
import sys, pathlib, math, time
import numpy as np, pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from propsim import closed_form as cf
from propsim.sim import sim_challenge, EMPTY, GAUSS, BERNOULLI, DD_STATIC, DD_TRAIL_INTRADAY, DD_TRAIL_EOD

ROOT = pathlib.Path(__file__).resolve().parents[1]
N = 100_000
rows = []


def run(name, exact, approx=False, n=N, **kw):
    d = dict(targets=np.array([0.10]), daily=0.0, daily_mode=0, maxloss=0.10, dd_type=DD_STATIC, lock=False,
             min_days=0, min_pdays=0, pday_thr=0.0, consist=0.0, time_limit=0, n_trades=1, risk=0.01, edge=0.0,
             cost=0.0, dist=GAUSS, R=1.0, df=4.0, boot=EMPTY, block=1, stop_k=0.0, max_days=10 ** 7)
    d.update(kw)
    t0 = time.time()
    code, days, trades, _ = sim_challenge(n, 12345, d["targets"], d["daily"], d["daily_mode"], d["maxloss"],
                                          d["dd_type"], d["lock"], d["min_days"], d["min_pdays"], d["pday_thr"],
                                          d["consist"], d["time_limit"], d["n_trades"], d["risk"], d["edge"],
                                          d["cost"], d["dist"], d["R"], d["df"], d["boot"], d["block"],
                                          d["stop_k"], d["max_days"])
    p = float((code == 1).mean())
    se = math.sqrt(max(exact * (1 - exact), 1e-12) / n)
    z = (p - exact) / se
    ok = abs(p - exact) < 0.01 if approx else abs(z) <= 3.0
    rows.append(dict(test=name, exact=round(exact, 5), mc=round(p, 5), se=round(se, 5), z=round(z, 2),
                     approx=approx, ok=ok, n=n, mean_days=round(float(days.mean()), 1), secs=round(time.time() - t0, 1)))
    print(rows[-1], flush=True)


# 1. Exact lattice gambler's ruin (Bernoulli 1:1 trades, 1% stop): b/(a+b) for several rule geometries
for a, b in [(0.10, 0.10), (0.05, 0.10), (0.08, 0.10), (0.06, 0.04), (0.10, 0.06)]:
    run(f"lattice fair a={a} b={b}", cf.p_gamblers_ruin(round(a / 0.01), round(b / 0.01)), targets=np.array([a]),
        maxloss=b, dist=BERNOULLI)
# 2. Lattice with edge (win prob 0.55 and 0.45)
for e in (0.10, -0.10):
    run(f"lattice edge={e}", cf.p_gamblers_ruin(10, 10, (1 + e) / 2), edge=e, dist=BERNOULLI)
# 3. Two phases multiply: FTMO-style 10% then 5% with 10% loss -> 1/2 * 2/3 = 1/3
run("two-phase lattice 10%/5% loss 10%", cf.zero_edge_ceiling([0.10, 0.05], 0.10), targets=np.array([0.10, 0.05]),
    dist=BERNOULLI)
# 4. Brownian limit, static barriers: small Gaussian steps (r=0.1%, 20 per day) vs b/(a+b); BGK shows the tiny bias
run("gauss fine steps a=.10 b=.10 (exact=BGK)", cf.p_static_discrete(0.10, 0.10, 0.001), risk=0.001, n_trades=20, n=40_000)
run("gauss fine steps a=.05 b=.10 (exact=BGK)", cf.p_static_discrete(0.05, 0.10, 0.001), targets=np.array([0.05]),
    risk=0.001, n_trades=20, n=40_000, approx=True)
# 5. Drift: per-trade edge q -> mu = q r n, sigma = r sqrt(n)
for q in (0.02, -0.02):
    r, n = 0.002, 10
    run(f"gauss drift q={q}", cf.p_static(0.10, 0.10, q * r * n, r * math.sqrt(n)), risk=r, n_trades=n, edge=q,
        approx=True, n=40_000)
# 6. Deadline: 30 trading days, sigma_daily = 1.5% (r=0.3354%, 20 trades/day)
r, n = 0.015 / math.sqrt(20), 20
#    The walk moves in discrete steps of s.d. r, so both barriers are shifted out by BGK_BETA*r before the series is used.
sh = cf.BGK_BETA * r
for T in (10, 30, 60):
    run(f"gauss deadline T={T}d sigma=1.5%/d (series + BGK shift)", cf.p_static_deadline(0.10 + sh, 0.10 + sh, T, 0.0, 0.015),
        risk=r, n_trades=n, time_limit=T, n=60_000)
    rows[-1]["note"] = f"unshifted continuous value {cf.p_static_deadline(0.10, 0.10, T, 0.0, 0.015):.5f}"
# 7. Intraday trailing drawdown: exp(-a/d), and with lock at the starting balance
run("trailing a=.06 d=.04", cf.p_trailing(0.06, 0.04), targets=np.array([0.06]), maxloss=0.04,
    dd_type=DD_TRAIL_INTRADAY, risk=0.0005, n_trades=20, approx=True, n=40_000)
run("trailing+lock a=.06 d=.04", cf.p_trailing(0.06, 0.04, lock=True), targets=np.array([0.06]), maxloss=0.04,
    dd_type=DD_TRAIL_INTRADAY, lock=True, risk=0.0005, n_trades=20, approx=True, n=40_000)
run("trailing a=.10 d=.06", cf.p_trailing(0.10, 0.06), targets=np.array([0.10]), maxloss=0.06,
    dd_type=DD_TRAIL_INTRADAY, risk=0.0005, n_trades=20, approx=True, n=40_000)
run("trailing drift q=.02 a=.06 d=.04", cf.p_trailing(0.06, 0.04, 0.02 * 0.0005 * 20, 0.0005 * math.sqrt(20)),
    targets=np.array([0.06]), maxloss=0.04, dd_type=DD_TRAIL_INTRADAY, risk=0.0005, n_trades=20, edge=0.02,
    approx=True, n=40_000)
# 8. Daily-close-only monitoring (1 Gaussian step per day): BGK correction, incl. the coin-flip limit
for sd in (0.01, 0.03, 0.10, 1.0):
    run(f"daily-close gauss sd={sd} a=.06 b=.04 (BGK approx)", cf.p_static_discrete(0.06, 0.04, sd),
        targets=np.array([0.06]), maxloss=0.04, risk=sd, n_trades=1, approx=True)
# 9. Rule-aware sizing with fixed-stop trades: no overshoot at the floor or at the target, so the optional-stopping
#    ceiling is attained for ANY trade size, including sizes that do not divide the barriers, and with a daily limit.
run("rule-aware Bernoulli r=3% a=.10 b=.10", 0.5, dist=BERNOULLI, risk=0.03, stop_k=1.0)
run("rule-aware Bernoulli 1:2 r=1.7% a=.08 b=.10", 10 / 18, targets=np.array([0.08]), dist=BERNOULLI, R=2.0, risk=0.017,
    stop_k=1.0)
run("rule-aware Bernoulli two-phase 10%/5%, daily 5%, r=1%, 10 trades/day", 1 / 3, targets=np.array([0.10, 0.05]),
    daily=0.05, dist=BERNOULLI, risk=0.01, n_trades=10, stop_k=1.0)
run("rule-aware Bernoulli two-phase 10%/5%, daily 5%, r=3%, 3 trades/day", 1 / 3, targets=np.array([0.10, 0.05]),
    daily=0.05, dist=BERNOULLI, risk=0.03, n_trades=3, stop_k=1.0)
#    Naive sizing with the same rules: three 3% losses in a day break the 5% daily limit, so the pass rate is lower.
run("naive Bernoulli two-phase 10%/5%, daily 5%, r=3%, 3 trades/day (reported, no exact value)", 1 / 3,
    targets=np.array([0.10, 0.05]), daily=0.05, dist=BERNOULLI, risk=0.03, n_trades=3, approx=True)
rows[-1]["ok"] = True
rows[-1]["note"] = "illustration only: exact column is the rule-aware ceiling, not a prediction for naive sizing"
# 10. Funded-stage simulator: 1:1 trades of 1%, one per day, 10% loss limit, withdraw whenever profit >= 5%
#     (then the balance resets). P(at least one payout) = 10/15; payouts are geometric with mean 2;
#     mean total paid = split * 5% * 2 = 0.08 of the account.
from propsim.sim import sim_funded  # noqa: E402
paid, npay = sim_funded(100_000, 7, 0.0, 0, 0.10, DD_STATIC, False, 1, 0.01, 0.0, 0.0, BERNOULLI, 1.0, 4.0, EMPTY, 1, 0.0,
                        20000, 1, 0.05, 0.8, 0, 5, 0.003, 0.5, 0.10, 0.0)
for name, exact, got, sd in (("funded: P(any payout)", 10 / 15, float((npay > 0).mean()), math.sqrt(2 / 9)),
                             ("funded: mean number of payouts", 2.0, float(npay.mean()), float(npay.std())),
                             ("funded: mean paid (fraction of account)", 0.08, float(paid.mean()), float(paid.std()))):
    se = sd / math.sqrt(len(paid))
    rows.append(dict(test=name, exact=round(exact, 5), mc=round(got, 5), se=round(se, 5), z=round((got - exact) / se, 2),
                     approx=False, ok=abs(got - exact) <= 3 * se, n=len(paid), mean_days=np.nan, secs=np.nan))
    print(rows[-1], flush=True)

df = pd.DataFrame(rows)
(ROOT / "results").mkdir(exist_ok=True)
df.to_csv(ROOT / "results" / "validation.csv", index=False)
print(df.to_string())
tests = df[~df.test.str.contains("reported, no exact value")]
print("ALL TESTS PASS" if tests.ok.all() else "SOME TESTS FAILED", int(tests.ok.sum()), "/", len(tests),
      "(plus", len(df) - len(tests), "illustration row)")
