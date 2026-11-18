"""Sensitivity rows for readings that stayed ambiguous (ES, GARCH-t bank, 1% volatility, K=3):
BUL_50K without the 21-day limit; E8_ONE without the consistency rule; ETF_LT50 at the USD 20.70 promotion fee; MF_BUILD at the USD 92 promotion fee."""
import os, sys, pathlib, math, copy
os.environ.setdefault("NUMBA_NUM_THREADS", "3")
import numpy as np, pandas as pd, psutil
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent; RES = ROOT / "results"
sys.path.insert(0, str(HERE))
import v3sim as v
from pars import get_pars
from run_grid import rules, cell, SPREAD_BP, HGRID, guard
import economics as eco
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
guard()
R = rules(); pars = get_pars("ES"); sd = pars["sd"]
bank = v.make_bank("P2", pars, 20000, 1200, 1000 + 7 * 2 + 2)       # the same seed as the grid's ES P2 bank
rows = []
scen = [("BUL_50K", "main (21-day limit)", {}), ("BUL_50K", "no deadline", {"time_limit": 0}),
        ("E8_ONE", "main (consistency 40%)", {}), ("E8_ONE", "no consistency rule", {"consistency": 0.0}),
        ("ETF_LT50", "main (fee 207)", {}), ("ETF_LT50", "promotion fee 20.70", {"fee_usd": 20.70}),
        ("MF_BUILD", "main (fee 153)", {}), ("MF_BUILD", "promotion fee 92", {"fee_usd": 92.0})]
cache = {}
for pid, name, mod in scen:
    r = copy.deepcopy(R[pid]); r.update({k: v_ for k, v_ in mod.items() if k != "fee_usd"})
    key = (pid, tuple(sorted((k, v_) for k, v_ in mod.items() if k != "fee_usd")))
    if key not in cache:
        rp = v.rule_vector(r); lev = 0.01 / sd; cells = {}
        for h in HGRID:
            for m in (1.0, 4.0):
                res, _ = cell(bank, 20000, lev, h, lev * SPREAD_BP["ES"] * 1e-4 * m, rp, True)
                cells[(round(h, 2), m)] = res
        cache[key] = cells
    cells = cache[key]; fee = mod.get("fee_usd", r["fee_usd"])
    out = dict(product=pid, scenario=name, fee_usd=fee, p_pass_zero_skill=cells[(0.5, 1.0)]["p_pass"])
    for pop, (w, m) in eco.POPS.items():
        if pop not in ("A_1pct_skilled", "D_dispersed", "E_dispersed_wide_cost"): continue
        tot = 0.0
        for h, wt in w.items():
            c = cells[(round(h, 2), m)]; row = pd.Series(dict(p_pass=c["p_pass"], fee_usd=fee, activation_usd=r["activation_usd"], tier_usd=r["tier_usd"], refund=r["refund"],
                                                              pay60_mean_pass=c.get("pay60_mean_pass", np.nan), pay60_pospass=c.get("pay60_pospass", np.nan)))
            j = eco.journey(row.rename(None).to_frame().T.itertuples().__next__(), 3)
            tot += wt * (j["fees"] - j["pay"] - j["refund"])
        out[f"revenue_{pop}"] = tot
    rows.append(out)
pd.DataFrame(rows).to_csv(RES / "E4_ambiguity_sensitivity.csv", index=False)
print(pd.DataFrame(rows).round(3).to_string())
