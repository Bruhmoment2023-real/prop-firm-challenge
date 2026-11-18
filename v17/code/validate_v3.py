"""V1-V4 validation of the v3 daily simulator (PLAN section 5). Writes results/validation_v3.csv. Each test: sim, reference, SE, z, pass."""
import os, sys, pathlib, math, itertools
import numpy as np, pandas as pd
os.environ.setdefault("NUMBA_NUM_THREADS", "3")
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
OLD = ROOT.parent / "code"
import v3sim as v
import psutil
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
rows = []
N = 20000


def add(test, sim, ref, se, tol=None, note=""):
    z = (sim - ref) / se if se > 0 else float("nan")
    ok = (abs(z) <= 3.0) if tol is None else (abs(sim - ref) <= tol)
    rows.append(dict(test=test, sim=sim, ref=ref, se=se, z=z, tol=tol, passed=bool(ok), note=note))
    print(("PASS " if ok else "FAIL ") + test, round(sim, 4), round(ref, 4), round(z, 2), flush=True)


# ---------------------------------------------------------------- V1 exact lattice DP
def dp_pass(T, L, phases, maxdays, dd="static", lock=False, tl=0):
    """T list of target steps per phase, L max-loss steps, +-1 step per day, p=0.5. Returns P(pass within maxdays)."""
    from collections import defaultdict
    cur = defaultdict(float); cur[(0, 0, 0, 0)] = 1.0     # (phase, e, peak, days_in_phase)
    tot = 0.0
    for day in range(1, maxdays + 1):
        nxt = defaultdict(float)
        for (ph, e, pk, dph), pr in cur.items():
            for s in (1, -1):
                e2 = e + s
                fl = -L if dd == "static" else pk - L
                if lock and fl > 0:
                    fl = 0
                if e2 <= fl:
                    continue
                pk2 = max(pk, e2) if dd != "static" else pk
                dph2 = dph + 1 if tl else 0
                if e2 >= T[ph]:
                    if ph + 1 == len(T):
                        tot += pr * 0.5
                        continue
                    nxt[(ph + 1, 0, 0, 0)] += pr * 0.5
                    continue
                if tl and dph2 >= tl:
                    continue
                nxt[(ph, e2, pk2, dph2)] += pr * 0.5
        cur = nxt
    return tot


def v1():
    q = 0.01
    cases = [
        ("V1a static single 10/10 steps, cap 1000d", dict(targets=[0.10], max_loss=0.10, dd_type="static"), dict(T=[10], L=10, dd="static")),
        ("V1b static two-phase 10/5, ML 10, cap 1000d", dict(targets=[0.10, 0.05], max_loss=0.10, dd_type="static"), dict(T=[10, 5], L=10, dd="static")),
        ("V1c static 8/5, ML 8, deadline 30d per phase", dict(targets=[0.08, 0.05], max_loss=0.08, dd_type="static", time_limit=30), dict(T=[8, 5], L=8, dd="static", tl=30)),
        ("V1d EOD trail no lock, T 9 ML 6", dict(targets=[0.09], max_loss=0.06, dd_type="trail_eod", lock=0), dict(T=[9], L=6, dd="trail", lock=False)),
        ("V1e EOD trail with lock, T 6 ML 4", dict(targets=[0.06], max_loss=0.04, dd_type="trail_eod", lock=1), dict(T=[6], L=4, dd="trail", lock=True)),
        ("V1f EOD trail with lock, T 6 ML 4, deadline 40d", dict(targets=[0.06], max_loss=0.04, dd_type="trail_eod", lock=1, time_limit=40), dict(T=[6], L=4, dd="trail", lock=True, tl=40)),
    ]
    bank = v.lattice_bank(q, N, 1200, 7)
    for name, r, d in cases:
        code, days, pay = v.simulate(bank, 1.0, 0.5, 0.0, v.rule_vector(r), maxdays=1000)
        p = float((code == 1).mean()); se = math.sqrt(p * (1 - p) / N)
        ref = dp_pass(d["T"], d["L"], len(d["T"]), 1000, dd=d["dd"], lock=d.get("lock", False), tl=d.get("tl", 0))
        add(name, p, ref, se)


# ---------------------------------------------------------------- V2 Nystrom (Gaussian, close-only, static)
def nystrom_pass(T, L, sd, n=3000):
    from numpy.polynomial.legendre import leggauss
    from scipy.stats import norm
    a, b = -L, T
    # composite Gauss-Legendre
    m = 60; k = n // m
    edges = np.linspace(a, b, k + 1)
    xg, wg = leggauss(m)
    x = np.concatenate([(edges[i] + edges[i + 1]) / 2 + (edges[i + 1] - edges[i]) / 2 * xg for i in range(k)])
    w = np.concatenate([(edges[i + 1] - edges[i]) / 2 * wg for i in range(k)])
    K = norm.pdf(x[None, :] - x[:, None], scale=sd) * w[None, :]
    rhs = 1.0 - norm.cdf((T - x) / sd)
    u = np.linalg.solve(np.eye(len(x)) - K, rhs)
    return float(np.interp(0.0, x, u))


def v2():
    r = dict(targets=[0.10], max_loss=0.06, dd_type="static")
    for sd_a in (0.01, 0.02):
        bank = v.make_bank("P0", dict(sd=0.01), N, 1200, 5, intraday=False)
        # bank sd = 1% close; lev scales the account sd
        code, days, pay = v.simulate(bank, sd_a / 0.01, 0.5, 0.0, v.rule_vector(r), maxdays=1000)
        p = float((code == 1).mean()); se = math.sqrt(p * (1 - p) / N)
        unres = float((code == 0).mean())
        ref = nystrom_pass(0.10, 0.06, sd_a)
        add(f"V2 Gaussian close-only static T10 L6 sd_a={sd_a}", p, ref, se, note=f"unresolved {unres:.4f}")


# ---------------------------------------------------------------- V3 old vs new simulator
def v3():
    sys.path.insert(0, str(OLD))
    from propsim import rules as old
    rs = old.load_rule_sets()
    bank = v.lattice_bank(0.01, N, 1200, 11)
    for key, r in rs.items():
        res = old.challenge(r, risk=0.01, n_trades=1, dist="bernoulli_1to1", edge=0.0, cost=0.0, stop_k=0.0, n_paths=N, seed=3, max_days=750)
        rr = dict(targets=list(r["targets"]), max_loss=r["max_loss"], dd_type=r["dd_type"], lock=r["lock"], daily_loss=r["daily_loss"],
                  daily_mode=r["daily_mode"], min_days=r["min_days"], min_profit_days=r["min_profit_days"], profit_day_thr=r["profit_day_thr"],
                  consistency=r["consistency"], time_limit=r["time_limit"])
        code, days, pay = v.simulate(bank, 1.0, 0.5, 0.0, v.rule_vector(rr), maxdays=750)
        p = float((code == 1).mean()); po = res["p_pass"]
        se = math.sqrt(p * (1 - p) / N + po * (1 - po) / N)
        add(f"V3 old vs new {key}", p, po, se, note="1 trade/day +-1% steps")


# ---------------------------------------------------------------- V4 continuous limits
def v4():
    sys.path.insert(0, str(OLD))
    from propsim import closed_form as cf
    # small-sigma limit with intraday monitoring (bridge extremes); the target is still checked at the close, so shift it by 0.5826 sd
    sd_a = 0.003
    bank = v.make_bank("P0", dict(sd=0.01), N, 1200, 9, intraday=True)
    lev = sd_a / 0.01
    cases = [
        ("V4a intraday trail no lock T3 d2", dict(targets=[0.03], max_loss=0.02, dd_type="trail_intraday", lock=0), lambda a, d: cf.p_trailing(a, d, 0.0, 1.0, False)),
        ("V4b intraday trail lock T3 d2", dict(targets=[0.03], max_loss=0.02, dd_type="trail_intraday", lock=1), lambda a, d: cf.p_trailing(a, d, 0.0, 1.0, True)),
        ("V4c static (intraday floor) T3 L2", dict(targets=[0.03], max_loss=0.02, dd_type="static"), lambda a, d: d / (a + d)),
    ]
    for name, r, f in cases:
        code, days, pay = v.simulate(bank, lev, 0.5, 0.0, v.rule_vector(r), maxdays=1000)
        p = float((code == 1).mean()); unres = float((code == 0).mean())
        a = r["targets"][0] + 0.5826 * sd_a
        ref = f(a, r["max_loss"])
        add(name, p, ref, math.sqrt(p * (1 - p) / N), tol=0.02, note=f"target shifted +0.5826 sd; unresolved {unres:.3f}")


if __name__ == "__main__":
    which = sys.argv[1:] or ["v1", "v2", "v4", "v3"]
    for w in which:
        globals()[w]()
        pd.DataFrame(rows).to_csv(ROOT / "results" / "validation_v3.csv", index=False)
