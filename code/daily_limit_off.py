"""Rerun selected zero-edge cells with the daily loss limit switched off.

Uses sim_copy_nonumba.py, a copy of the pack's code/propsim/sim.py with the numba decorator replaced by a
no-op (numba is not installed here), so the kernels run as plain Python. Rule sets and market data are read
(read only) from the research pack. For each cell the script runs the simulator twice with the same seed,
once with the rule set's daily limit and once with daily_loss = 0 (no daily limit), and writes both results.

Usage: python -I daily_limit_off.py <pack_dir> <out_csv> [n_paths]
"""
import csv
import math
import pathlib
import sys
import time

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sim_copy_nonumba as sim  # noqa: E402

PACK = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
N = int(sys.argv[3]) if len(sys.argv) > 3 else 20_000
if OUT.exists():
    sys.exit(f"{OUT} exists; refusing to overwrite")

DD = {"static": sim.DD_STATIC, "trail_eod": sim.DD_TRAIL_EOD, "trail_intraday": sim.DD_TRAIL_INTRADAY}
DM = {"breach": sim.DAILY_BREACH, "pause": sim.DAILY_PAUSE}
DISTS = {"bernoulli_1to1": (sim.BERNOULLI, 1.0, 4.0, None),
         "gauss": (sim.GAUSS, 1.0, 4.0, None),
         "boot_EURUSD_1h": (sim.BOOTSTRAP, 1.0, 4.0, "EURUSD_1h.csv")}

rules = {r["key"]: r for r in csv.DictReader(open(PACK / "data" / "rule_sets_model.csv", newline=""))}


def boot_series(fname):
    px = np.array([float(r["close"]) for r in csv.DictReader(open(PACK / "data" / "market" / fname, newline=""))])
    ret = np.diff(np.log(px))
    ret = ret[np.isfinite(ret) & (ret != 0.0)]
    return sim.standardise(ret)


def run(key, dist, stop_k, daily_on, risk=0.01, n_trades=3, seed=101):
    rs = rules[key]
    code_, R, df, fname = DISTS[dist]
    boot = boot_series(fname) if fname else sim.EMPTY
    targets = np.array([float(x) for x in rs["targets"].split("|")])
    daily = float(rs["daily_loss"]) if daily_on else 0.0
    code, days, trades, _ = sim.sim_challenge(
        N, seed, targets, daily, DM[rs["daily_mode"]], float(rs["max_loss"]), DD[rs["dd_type"]],
        bool(int(rs["lock"])), int(rs["min_days"]), int(rs["min_profit_days"]), float(rs["profit_day_thr"]),
        float(rs["consistency"]), int(rs["time_limit"]), n_trades, risk, 0.0, 0.0, code_, R, df, boot, 24,
        stop_k, 750)
    p = float((code == 1).mean())
    return dict(rule_set=key, dist=dist, risk=risk, trades_per_day=n_trades,
                policy="rule_aware" if stop_k > 0 else "naive", daily_limit="on" if daily_on else "off",
                n_paths=N, p_pass=p, se=math.sqrt(max(p * (1 - p), 1e-12) / N),
                p_fail_maxloss=float((code == -1).mean()), p_fail_daily=float((code == -2).mean()),
                p_unresolved=float((code == 0).mean()), mean_trades=float(trades.mean()))


CELLS = [(k, d, s) for k in ("FTMO_2S", "FTMO_1S")
         for d, s in (("bernoulli_1to1", 0.0), ("bernoulli_1to1", 1.0), ("gauss", 1.0), ("boot_EURUSD_1h", 1.0))]
rows = []
for key, dist, stop_k in CELLS:
    for on in (True, False):
        t0 = time.time()
        rows.append(run(key, dist, stop_k, on))
        print(rows[-1], f"{time.time() - t0:.0f}s", flush=True)
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
