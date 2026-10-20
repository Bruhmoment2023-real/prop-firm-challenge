"""Load data/rule_sets_model.csv and run the simulator for one rule set.

`challenge(rs, ...)` and `funded(rs, ...)` are thin, readable wrappers around the numba kernels in sim.py.
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

from . import sim

ROOT = pathlib.Path(__file__).resolve().parents[2]
DD = {"static": sim.DD_STATIC, "trail_eod": sim.DD_TRAIL_EOD, "trail_intraday": sim.DD_TRAIL_INTRADAY}
DM = {"breach": sim.DAILY_BREACH, "pause": sim.DAILY_PAUSE}
DISTS = {  # name -> (dist code, R, df, bootstrap file or None)
    "gauss": (sim.GAUSS, 1.0, 4.0, None),
    "student_t3": (sim.STUDENT_T, 1.0, 3.0, None),
    "bernoulli_1to1": (sim.BERNOULLI, 1.0, 4.0, None),
    "bernoulli_1to2": (sim.BERNOULLI, 2.0, 4.0, None),
    "boot_EURUSD_1h": (sim.BOOTSTRAP, 1.0, 4.0, "EURUSD_1h.csv"),
    "boot_NQ_1h": (sim.BOOTSTRAP, 1.0, 4.0, "NQ_F_1h.csv"),
}
_boot_cache: dict = {}


def load_rule_sets() -> dict:
    df = pd.read_csv(ROOT / "data" / "rule_sets_model.csv")
    out = {}
    for _, r in df.iterrows():
        d = r.to_dict()
        d["targets"] = np.array([float(x) for x in str(r["targets"]).split("|")])
        out[r["key"]] = d
    return out


def boot_series(fname: str) -> np.ndarray:
    """Standardised (mean 0, s.d. 1) close-to-close log returns of a price file in data/market/."""
    if fname not in _boot_cache:
        px = pd.read_csv(ROOT / "data" / "market" / fname)["close"].to_numpy(float)
        ret = np.diff(np.log(px))
        ret = ret[np.isfinite(ret) & (ret != 0.0)]       # drop stale (flat) bars
        _boot_cache[fname] = sim.standardise(ret)
    return _boot_cache[fname]


def _dist(dist: str):
    code, R, df, fname = DISTS[dist]
    boot = boot_series(fname) if fname else sim.EMPTY
    return code, R, df, boot


def challenge(rs: dict, risk: float, n_trades: int, dist: str = "bernoulli_1to1", edge: float = 0.0,
              cost: float = 0.0, stop_k: float = 0.0, n_paths: int = 20_000, seed: int = 1,
              max_days: int = 750, block: int = 24, time_limit: int | None = None) -> dict:
    """Simulate the evaluation stage. Returns a dict of summary statistics."""
    code_, R, df, boot = _dist(dist)
    tl = int(rs["time_limit"]) if time_limit is None else int(time_limit)
    code, days, trades, fphase = sim.sim_challenge(
        n_paths, seed, rs["targets"], float(rs["daily_loss"]), DM[rs["daily_mode"]], float(rs["max_loss"]),
        DD[rs["dd_type"]], bool(rs["lock"]), int(rs["min_days"]), int(rs["min_profit_days"]),
        float(rs["profit_day_thr"]), float(rs["consistency"]), tl, int(n_trades), float(risk), float(edge),
        float(cost), code_, R, df, boot, int(block), float(stop_k), int(max_days))
    p = float((code == 1).mean())
    return dict(p_pass=p, se=float(np.sqrt(max(p * (1 - p), 1e-12) / n_paths)),
                p_fail_maxloss=float((code == -1).mean()), p_fail_daily=float((code == -2).mean()),
                p_fail_time=float((code == -3).mean()), p_unresolved=float((code == 0).mean()),
                mean_days=float(days.mean()), median_days_pass=float(np.median(days[code == 1])) if p > 0 else np.nan,
                mean_trades=float(trades.mean()), mean_trades_pass=float(trades[code == 1].mean()) if p > 0 else np.nan)


def funded(rs: dict, risk: float, n_trades: int, dist: str = "bernoulli_1to1", edge: float = 0.0,
           cost: float = 0.0, stop_k: float = 0.0, n_paths: int = 20_000, seed: int = 2, horizon: int = 60,
           block: int = 24) -> dict:
    """Simulate the funded stage for `horizon` trading days. Payouts are fractions of the account."""
    code_, R, df, boot = _dist(dist)
    fut = rs["funded_mode"] == "futures"
    paid, npay = sim.sim_funded(
        n_paths, seed, float(rs["daily_loss"]), DM[rs["daily_mode"]], float(rs["max_loss"]),
        sim.DD_TRAIL_EOD if fut else DD[rs["dd_type"]], True if fut else bool(rs["lock"]), int(n_trades),
        float(risk), float(edge), float(cost), code_, R, df, boot, int(block), float(stop_k), int(horizon),
        int(rs["funded_cycle_days"]), float(rs["funded_min_profit"]), float(rs["split"]), 1 if fut else 0,
        5, 0.003, 0.5, 0.10, float(rs["funded_consistency"]))
    return dict(mean_paid=float(paid.mean()), p_any_payout=float((npay > 0).mean()),
                median_paid=float(np.median(paid)), p90_paid=float(np.quantile(paid, 0.9)),
                mean_n_payouts=float(npay.mean()))


def economics(rs: dict, ch: dict, fu: dict) -> dict:
    """Expected value per challenge purchased, in USD, under the stated payout assumptions."""
    acct, fee, act = float(rs["account_usd"]), float(rs["fee_usd"]), float(rs["activation_usd"])
    p = ch["p_pass"]
    payout = fu["mean_paid"] * acct + fu["p_any_payout"] * (float(rs["refund"]) * fee + float(rs["bonus_frac"]) * acct)
    ev = p * (payout - act) - fee
    return dict(ev_per_attempt_usd=ev, exp_attempts_to_pass=(1 / p if p > 0 else np.inf),
                exp_fees_to_first_funded_usd=(fee / p + act if p > 0 else np.inf),
                exp_payout_given_pass_usd=payout, p_paid_per_attempt=p * fu["p_any_payout"],
                breakeven_payout_given_pass_usd=(fee / p + act if p > 0 else np.inf))
