"""E1/E2 (Tier 1, Tier 2, headline 100k). Resumable: one CSV per (asset, process). Pauses on weekdays 09:00-15:45 IST.
Usage: python run_grid.py ES NQ ...   (assets in the order given)"""
import os, sys, time, datetime, pathlib, math
os.environ.setdefault("NUMBA_NUM_THREADS", "3")
import numpy as np, pandas as pd, psutil
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import v3sim as v
from pars import get_pars
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
SPREAD_BP = dict(ES=0.5, NQ=0.5, EURUSD=1.0, GOLD=1.5, BTC=6.0)
HGRID = [0.46, 0.48, 0.50, 0.52, 0.54, 0.56, 0.60]
OUT = ROOT / "results" / "grid"; OUT.mkdir(parents=True, exist_ok=True)
PROCS = ["P0", "P1", "P2", "P3", "P4"]


def guard():
    while True:
        n = datetime.datetime.now()
        if n.weekday() < 5 and datetime.time(9, 0) <= n.time() < datetime.time(15, 45):
            time.sleep(300)
        else:
            return


def rules():
    df = pd.read_csv(ROOT / "data" / "rule_sets_v3_model.csv")
    out = {}
    for _, r in df.iterrows():
        d = r.to_dict(); d["targets"] = [float(x) for x in str(r["targets"]).split("|")]
        d["funded_cycle_days"] = 10; d["funded_min_profit"] = 0.0; d["funded_consistency"] = 0.0
        out[r["pid"]] = d
    return out


def cell(bank, n, lev, h, cst, rp, funded):
    sub = tuple(a[:n] for a in bank)
    code, days, pay = v.simulate(sub, lev, h, cst, rp, maxdays=1000, funded=funded)
    ps = code == 1
    p = float(ps.mean())
    r = dict(p_pass=p, se=math.sqrt(max(p * (1 - p), 1e-12) / n), f_maxloss=float((code == -1).mean()), f_daily=float((code == -2).mean()),
             f_time=float((code == -3).mean()), unresolved=float((code == 0).mean()), median_days_pass=float(np.median(days[ps])) if ps.any() else np.nan)
    if funded and ps.any():
        for k, hz in enumerate((20, 60, 120)):
            r[f"pay{hz}_mean_all"] = float(pay[:, k].mean())            # E[payout fraction per attempt]
            r[f"pay{hz}_mean_pass"] = float(pay[ps, k].mean())
            r[f"pay{hz}_pospass"] = float((pay[ps, k] > 0).mean())
    return r, (ps, pay[:, 1])


def main(assets):
    R = rules(); sig_main = 0.01
    for a in assets:
        pars = get_pars(a); sd = pars["sd"]
        for proc in PROCS:
            f = OUT / f"E1_{a}_{proc}.csv"
            if f.exists(): continue
            guard(); t0 = time.time()
            bank = v.make_bank(proc, pars, 20000, 1200, 1000 + 7 * PROCS.index(proc) + len(a))
            rows = []; samples = {}
            for pid, r in R.items():
                rp = v.rule_vector(r)
                combos = [(h, 1.0, 0.01, True) for h in HGRID] + [(h, 4.0, 0.01, True) for h in HGRID] + [(h, 0.0, 0.01, True) for h in (0.50, 0.56)]
                combos += [(h, 1.0, s, False) for s in (0.005, 0.02) for h in (0.50, 0.56)]
                for h, m, s, fd in combos:
                    lev = s / sd; cst = lev * SPREAD_BP[a] * 1e-4 * m
                    n = 20000 if s == 0.01 else 10000
                    res, smp = cell(bank, n, lev, h, cst, rp, fd)
                    res.update(asset=a, process=proc, pid=pid, h=h, m=m, sigma_a=s, n_paths=n)
                    rows.append(res)
                    if a == "ES" and proc == "P2" and s == 0.01 and m in (1.0, 4.0) and fd:
                        samples[f"{pid}|{h}|{m}"] = (smp[0], smp[1].astype(np.float32))
            pd.DataFrame(rows).to_csv(f, index=False)
            if samples:
                np.savez_compressed(OUT / "samples_ES_P2.npz", **{k + "|pass": s[0] for k, s in samples.items()}, **{k + "|pay60": s[1] for k, s in samples.items()})
            print(a, proc, len(rows), "cells", round(time.time() - t0), "s", flush=True)


def headline():
    """100,000 paths (5 banks x 20,000, seeds 101-105): ES, P2, sigma_a 1%, h 0.50, m 1, funded stage."""
    R = rules(); a = "ES"; pars = get_pars(a); sd = pars["sd"]; rows = []
    for pid, r in R.items():
        tot = dict(p=0.0, pay60=0.0, n=0)
        rp = v.rule_vector(r); ps_all = []
        for seed in range(101, 106):
            pass
    for seed in range(101, 106):
        guard()
        bank = v.make_bank("P2", pars, 20000, 1200, seed)
        for pid, r in R.items():
            rp = v.rule_vector(r); lev = 0.01 / sd; cst = lev * SPREAD_BP[a] * 1e-4
            res, _ = cell(bank, 20000, lev, 0.5, cst, rp, True); res.update(pid=pid, seed=seed); rows.append(res)
    d = pd.DataFrame(rows)
    g = d.groupby("pid").agg(p_pass=("p_pass", "mean"), pay60_mean_all=("pay60_mean_all", "mean"), f_maxloss=("f_maxloss", "mean"),
                              f_daily=("f_daily", "mean"), f_time=("f_time", "mean"), unresolved=("unresolved", "mean")).reset_index()
    g["se"] = d.groupby("pid").p_pass.std(ddof=1).values / math.sqrt(5)
    g["n_paths"] = 100000
    g.to_csv(ROOT / "results" / "E1_headline_100k.csv", index=False)


if __name__ == "__main__":
    if sys.argv[1] == "headline": headline()
    else: main(sys.argv[1:])
