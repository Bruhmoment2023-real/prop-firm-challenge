"""Run every experiment of the study and write CSV tables to results/.

Usage:
    python code/02_run_experiments.py            # full run, 20,000 paths per cell (about 6-9 CPU-minutes)
    python code/02_run_experiments.py --quick    # 2,000 paths per cell, smoke test (under 1 minute)
    python code/02_run_experiments.py --only A   # run one block (A, B, C, D or E)
    python code/02_run_experiments.py --only A --part 1of2   # first half of the rule sets (keeps a run under 10 min)

Runs used for the tables in results/ (each under 10 CPU-minutes, single thread):
    --only A --part 1of2 ; --only A --part 2of2 ; --only B ; --only C ; --only DE
Blocks A-C write one CSV per part (results/parts/) and then merge all parts found into results/<block>.csv.

Blocks
  A  zero-edge pass probability: rule set x return model x risk per trade x trades per day x sizing policy
  B  economics at zero edge: expected attempts, fees and expected value per attempt (funded stage simulated)
  C  edge sensitivity: pass probability against per-trade edge, by rule set and risk per trade
  D  the challenge as a test of skill: likelihood ratios, posterior probability of skill, and the
     Neyman-Pearson benchmark (best possible test using the same number of trades)
  E  time-limit sensitivity (a rule most firms have now dropped): closed form and simulation

Seeds are fixed, so the tables are reproducible on the same numpy/numba versions.
"""
import argparse
import math
import pathlib
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from propsim import closed_form as cf          # noqa: E402
from propsim import rules as R                 # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
RISKS = [0.0025, 0.005, 0.01, 0.02, 0.03, 0.05]
TRADES = [1, 3, 10]
POLICIES = {"naive": 0.0, "rule_aware": 1.0}
EDGES = [-0.10, -0.05, -0.02, 0.0, 0.02, 0.05, 0.10, 0.15, 0.20]


def save(rows, name, part):
    """Write this part, then merge every part on disk into results/<name>.csv.

    --quick runs are kept apart (results/parts_quick/, results/QUICK_<name>.csv) so they never mix with real runs.
    """
    quick = part.startswith("quick_")
    pdir = OUT / ("parts_quick" if quick else "parts")
    pdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(pdir / f"{name}__{part}.csv", index=False)
    parts = sorted(pdir.glob(f"{name}__*.csv"))
    merged = pd.concat([pd.read_csv(f) for f in parts]).drop_duplicates()
    merged.to_csv(OUT / (("QUICK_" if quick else "") + f"{name}.csv"), index=False)


def block_a(rs_all, n, part="all"):
    rows = []
    for key, rs in rs_all.items():
        ceil = cf.zero_edge_ceiling(rs["targets"], rs["max_loss"])
        for dist in R.DISTS:
            for risk in RISKS:
                for nt in TRADES:
                    for pol, k in POLICIES.items():
                        r = R.challenge(rs, risk, nt, dist, stop_k=k, n_paths=n, seed=101)
                        rows.append(dict(rule_set=key, dist=dist, risk=risk, trades_per_day=nt, policy=pol,
                                         ceiling=ceil, **r))
        print("A", key, flush=True)
    save(rows, "A_zero_edge_grid", part)


def block_b(rs_all, n, part="all"):
    rows = []
    for key, rs in rs_all.items():
        for dist in ("bernoulli_1to1", "gauss", "boot_EURUSD_1h"):
            for risk in RISKS:
                for nt in (1, 3):
                    for cost in (0.0, 0.05):
                        for horizon in (20, 60, 120):
                            if horizon != 60 and (dist != "bernoulli_1to1" or nt != 3 or cost != 0.0):
                                continue
                            ch = R.challenge(rs, risk, nt, dist, cost=cost, stop_k=1.0, n_paths=n, seed=202)
                            fu = R.funded(rs, risk, nt, dist, cost=cost, stop_k=1.0, n_paths=n, seed=203,
                                          horizon=horizon)
                            rows.append(dict(rule_set=key, dist=dist, risk=risk, trades_per_day=nt,
                                             cost_per_trade_R=cost, funded_horizon_days=horizon,
                                             fee_usd=rs["fee_usd"], account_usd=rs["account_usd"],
                                             p_pass=ch["p_pass"], p_unresolved=ch["p_unresolved"],
                                             mean_days_challenge=ch["mean_days"],
                                             funded_mean_paid_frac=fu["mean_paid"],
                                             funded_p_any_payout=fu["p_any_payout"],
                                             funded_median_paid_frac=fu["median_paid"], **R.economics(rs, ch, fu)))
        print("B", key, flush=True)
    save(rows, "B_economics", part)


def block_c(rs_all, n, part="all"):
    rows = []
    for key, rs in rs_all.items():
        for dist in ("bernoulli_1to1", "gauss"):
            for risk in (0.0025, 0.005, 0.01, 0.02, 0.03):
                for edge in EDGES:
                    r = R.challenge(rs, risk, 3, dist, edge=edge, stop_k=1.0, n_paths=n, seed=303)
                    rows.append(dict(rule_set=key, dist=dist, risk=risk, trades_per_day=3, edge=edge,
                                     p_pass=r["p_pass"], se=r["se"], p_unresolved=r["p_unresolved"],
                                     mean_trades=r["mean_trades"], mean_days=r["mean_days"]))
        print("C", key, flush=True)
    save(rows, "C_edge_sensitivity", part)


def block_d():
    """Likelihood ratios etc. computed from block C (so C must have been run)."""
    c = pd.read_csv(OUT / "C_edge_sensitivity.csv")
    c = c[c.dist == "bernoulli_1to1"]
    rs_all = R.load_rule_sets()
    rows = []
    for (key, risk), g in c.groupby(["rule_set", "risk"]):
        g = g.set_index("edge")
        for q1, q0 in ((0.10, 0.0), (0.10, -0.05), (0.05, 0.0), (0.05, -0.05), (0.20, 0.0)):
            p1, p0 = g.loc[q1, "p_pass"], g.loc[q0, "p_pass"]
            if p0 <= 0 or g.loc[q1, "p_unresolved"] > 0.02 or g.loc[q0, "p_unresolved"] > 0.02:
                continue
            # Neyman-Pearson benchmark: a fixed-sample test on N trades (N = average trades the challenge used),
            # run at the same false-positive rate p0. For unit-variance trades the test statistic is the mean.
            n_tr = 0.5 * (g.loc[q1, "mean_trades"] + g.loc[q0, "mean_trades"])
            tpr_np = float(norm.cdf(norm.ppf(p0) + (q1 - q0) * math.sqrt(n_tr)))
            auc_np = float(norm.cdf((q1 - q0) * math.sqrt(n_tr) / math.sqrt(2)))
            row = dict(rule_set=key, risk=risk, edge_skilled=q1, edge_unskilled=q0, tpr=p1, fpr=p0,
                       lr_plus=p1 / p0, lr_minus=(1 - p1) / (1 - p0), youden_j=p1 - p0,
                       auc_single_point=0.5 * (1 + p1 - p0), mean_trades=n_tr, tpr_neyman_pearson_same_fpr=tpr_np,
                       auc_neyman_pearson=auc_np,
                       lr_plus_ceiling_zero_edge=cf.max_likelihood_ratio(rs_all[key]["targets"],
                                                                        rs_all[key]["max_loss"]))
            for prior in (0.01, 0.05, 0.10, 0.20):
                row[f"ppv_prior_{prior:.2f}"] = cf.ppv(prior, p1, p0)
            rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "D_skill_test.csv", index=False)
    print("D done", flush=True)


def block_e(rs_all, n):
    """Static 10% target / 10% loss phase with a deadline (30 and 60 trading days), against daily volatility."""
    rs = dict(rs_all["FTMO_2S"])
    rs["targets"] = np.array([0.10])
    rs["daily_loss"] = 0.0
    rs["min_days"] = 0
    rows = []
    for sig in (0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.03, 0.05):
        for T in (30, 60, 0):
            nt = 20
            risk = sig / math.sqrt(nt)
            sh = cf.BGK_BETA * risk
            exact = cf.p_static_deadline(0.10, 0.10, T, 0.0, sig) if T else 0.5
            exact_d = cf.p_static_deadline(0.10 + sh, 0.10 + sh, T, 0.0, sig) if T else 0.5
            r = R.challenge(rs, risk, nt, "gauss", n_paths=n, seed=505, time_limit=T, max_days=5000)
            rows.append(dict(daily_vol=sig, deadline_days=T, closed_form_continuous=exact,
                             closed_form_discrete_shift=exact_d, mc=r["p_pass"], se=r["se"],
                             p_fail_time=r["p_fail_time"], p_fail_maxloss=r["p_fail_maxloss"]))
    pd.DataFrame(rows).to_csv(OUT / "E_time_limit.csv", index=False)
    print("E done", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", default="ABCDE")
    ap.add_argument("--part", default="1of1", help="e.g. 1of2: run only the first half of the rule sets")
    a = ap.parse_args()
    n = 2_000 if a.quick else 20_000
    OUT.mkdir(exist_ok=True)
    rs_full = R.load_rule_sets()
    i, k = (int(x) for x in a.part.split("of"))
    keys = list(rs_full)
    rs_all = {key: rs_full[key] for j, key in enumerate(keys) if j * k // len(keys) == i - 1}
    part = ("quick_" if a.quick else "") + a.part
    t0 = time.time()
    if "A" in a.only:
        block_a(rs_all, n, part)
    if "B" in a.only:
        block_b(rs_all, n, part)
    if "C" in a.only:
        block_c(rs_all, n, part)
    if "D" in a.only and not a.quick:      # D and E write unprefixed files, so they are skipped in --quick mode
        block_d()
    if "E" in a.only and not a.quick:
        block_e(rs_full, n)
    print(f"finished in {time.time() - t0:.0f} s, {n} paths per cell")


if __name__ == "__main__":
    main()
