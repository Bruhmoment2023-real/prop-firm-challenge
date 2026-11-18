"""v3 daily-step prop-firm challenge simulator (new code, numba), plus return-process banks.

Units: fractions of the starting balance (1.0 = start balance of each phase). One step = one trading day.
A "bank" holds, for N paths and D days, the asset's close-to-close log return C, the intraday high H and low L relative to the
previous close (H >= max(C,0), L <= min(C,0)) and a uniform U used to draw the trader's direction.
Trader: direction s = sign(C) with probability h, else -sign(C)   (h = 0.5 is zero skill); position = lev * s, so the day's
account result is lev*s*C - cost, with intraday excursions lev*(H or -L) - cost.
Outcome codes: 1 pass, -1 max-loss breach, -2 daily-loss breach, -3 time limit, 0 unresolved at maxdays.
Rule vector rp (float64):
 0 n_targets, 1..3 targets, 4 max_loss, 5 dd_type (0 static, 1 EOD trail, 2 intraday trail), 6 lock, 7 daily_loss (0 none),
 8 daily_mode (0 breach, 1 pause), 9 min_days, 10 min_profit_days, 11 profit_day_threshold, 12 consistency (0 none),
 13 time_limit (0 none), 14 split, 15 payout cycle days, 16 funded min profit, 17 funded consistency
"""
from __future__ import annotations
import numpy as np
from numba import njit, prange

EPS = 1e-6   # tolerance: banks are float32, so ten steps of 0.01 sum to 0.0999999977


@njit(cache=True, inline="always")
def _day(c, hh, ll, u, lev, h, cst):
    pos = (c >= 0.0) == (u < h)            # True -> long
    if pos:
        pc = lev * c - cst
        fav = lev * hh - cst
        adv = lev * ll - cst
    else:
        pc = -lev * c - cst
        fav = -lev * ll - cst
        adv = -lev * hh - cst
    return pc, fav, adv


@njit(cache=True, inline="always")
def _floor(peak, ml, dd, lock):
    if dd == 0:
        return 1.0 - ml
    f = peak - ml
    if lock > 0.5 and f > 1.0:
        f = 1.0
    return f


@njit(parallel=True, cache=True)
def run_bank(Cb, Hb, Lb, Ub, lev, h, cst, rp, maxdays, hz, do_funded, code_o, days_o, pay_o):
    N = Cb.shape[0]
    D = Cb.shape[1]
    nt = int(rp[0])
    ml = rp[4]
    dd = int(rp[5])
    lock = rp[6]
    dl = rp[7]
    dlm = int(rp[8])
    mind = int(rp[9])
    minp = int(rp[10])
    pthr = rp[11]
    cons = rp[12]
    tl = int(rp[13])
    split = rp[14]
    cyc = int(rp[15])
    fmin = rp[16]
    fcons = rp[17]
    for i in prange(N):
        e = 1.0
        peak = 1.0
        ph = 0
        dph = 0
        best = 0.0
        pdays = 0
        code = 0
        t = 0
        while t < maxdays:
            pc, fav, adv = _day(Cb[i, t], Hb[i, t], Lb[i, t], Ub[i, t], lev, h, cst)
            e0 = e
            pk = peak
            if dd == 2:
                v = e0 + fav
                if v > pk:
                    pk = v
            fl = _floor(pk, ml, dd, lock)
            if e0 + adv <= fl + EPS:
                code = -1
                t += 1
                break
            if dl > 0.0 and adv <= -dl + EPS:
                if dlm == 0:
                    code = -2
                    t += 1
                    break
                pc = -dl
            e = e0 + pc
            if e <= fl + EPS:
                code = -1
                t += 1
                break
            if dd >= 1:
                if dd == 2 and pk > peak:
                    peak = pk
                if e > peak:
                    peak = e
            t += 1
            dph += 1
            if pc > best:
                best = pc
            if pc >= pthr and pc > 0.0:
                pdays += 1
            if e >= 1.0 + rp[1 + ph] - EPS and dph >= mind and pdays >= minp:
                prof = e - 1.0
                if cons <= 0.0 or best <= cons * prof + EPS:
                    ph += 1
                    if ph >= nt:
                        code = 1
                        break
                    e = 1.0
                    peak = 1.0
                    dph = 0
                    best = 0.0
                    pdays = 0
                    continue
            if tl > 0 and dph >= tl:
                code = -3
                break
        code_o[i] = code
        days_o[i] = t
        for k in range(3):
            pay_o[i, k] = 0.0
        if code == 1 and do_funded and t + hz[2] <= D:
            e = 1.0
            peak = 1.0
            tot = 0.0
            fb = 0.0
            alive = True
            k = 0
            for f in range(1, hz[2] + 1):
                if alive:
                    pc, fav, adv = _day(Cb[i, t + f - 1], Hb[i, t + f - 1], Lb[i, t + f - 1], Ub[i, t + f - 1], lev, h, cst)
                    e0 = e
                    pk = peak
                    if dd == 2:
                        v = e0 + fav
                        if v > pk:
                            pk = v
                    fl = _floor(pk, ml, dd, lock)
                    if e0 + adv <= fl + EPS:
                        alive = False
                    elif dl > 0.0 and adv <= -dl + EPS and dlm == 0:
                        alive = False
                    else:
                        if dl > 0.0 and adv <= -dl + EPS:
                            pc = -dl
                        e = e0 + pc
                        if e <= fl + EPS:
                            alive = False
                        else:
                            if dd >= 1:
                                if dd == 2 and pk > peak:
                                    peak = pk
                                if e > peak:
                                    peak = e
                            if pc > fb:
                                fb = pc
                            if cyc > 0 and f % cyc == 0:
                                prof = e - 1.0
                                if prof > fmin and (fcons <= 0.0 or fb <= fcons * prof + 1e-12):
                                    tot += split * prof
                                    e = 1.0
                                    peak = 1.0
                                    fb = 0.0
                while k < 3 and f == hz[k]:
                    pay_o[i, k] = tot
                    k += 1
        elif code == 1:
            pay_o[i, 0] = -1.0   # not enough bank left for the funded stage (flag)


def simulate(bank, lev, h, cst, rp, maxdays=1000, hz=(20, 60, 120), funded=False):
    C, H, L, U = bank
    N = C.shape[0]
    code = np.zeros(N, np.int8)
    days = np.zeros(N, np.int32)
    pay = np.zeros((N, 3), np.float64)
    run_bank(C, H, L, U, float(lev), float(h), float(cst), np.asarray(rp, np.float64), int(maxdays),
             np.asarray(hz, np.int64), bool(funded), code, days, pay)
    return code, days, pay


# ---------------------------------------------------------------- rule vectors
DDMAP = {"static": 0, "trail_eod": 1, "trail_intraday": 2}
DLMAP = {"breach": 0, "pause": 1}


def rule_vector(r: dict) -> np.ndarray:
    """r: dict with keys targets (list), max_loss, dd_type, lock, daily_loss, daily_mode, min_days, min_profit_days,
    profit_day_thr, consistency, time_limit, split, funded_cycle_days, funded_min_profit, funded_consistency."""
    t = list(r["targets"]) + [0.0, 0.0, 0.0]
    rp = np.zeros(18)
    rp[0] = len(r["targets"])
    rp[1:4] = t[:3]
    rp[4] = r["max_loss"]
    rp[5] = DDMAP[r["dd_type"]]
    rp[6] = float(r.get("lock", 0))
    rp[7] = r.get("daily_loss", 0.0) or 0.0
    rp[8] = DLMAP.get(r.get("daily_mode", "breach"), 0)
    rp[9] = r.get("min_days", 0)
    rp[10] = r.get("min_profit_days", 0)
    rp[11] = r.get("profit_day_thr", 0.0)
    rp[12] = r.get("consistency", 0.0)
    rp[13] = r.get("time_limit", 0)
    rp[14] = r.get("split", 0.8)
    rp[15] = r.get("funded_cycle_days", 10)
    rp[16] = r.get("funded_min_profit", 0.0)
    rp[17] = r.get("funded_consistency", 0.0)
    return rp


# ---------------------------------------------------------------- return processes
def _bridge_extremes(c, s, rng):
    """Brownian-bridge max and min of a day with close c and day sd s (arrays); independent draws."""
    u1 = rng.random(c.shape)
    u2 = rng.random(c.shape)
    s2 = np.maximum(s, 1e-9) ** 2
    M = 0.5 * (c + np.sqrt(c * c - 2.0 * s2 * np.log(np.maximum(u1, 1e-300))))
    m = 0.5 * (c - np.sqrt(c * c - 2.0 * s2 * np.log(np.maximum(u2, 1e-300))))
    return M, m


def adj_garch(g, sd, cap=0.995):
    om, al, ga, be, nu = g
    pers = al + 0.5 * ga + be
    if pers > cap:
        be = be - (pers - cap)
        pers = cap
    om = sd * sd * (1.0 - pers)
    return om, al, ga, be, nu


def make_bank(process: str, params: dict, N: int, D: int, seed: int, intraday: bool = True):
    """Return (C,H,L,U) float32 arrays. params from calibration: sd, df, garch (omega,alpha,gamma,beta,nu),
    std_resid (array), triples (n x 3 array of demeaned close/high/low log returns)."""
    rng = np.random.default_rng(seed)
    U = rng.random((N, D), dtype=np.float32)
    if process == "P4":
        tr = params["triples"]
        n = tr.shape[0]
        mb = 20.0
        pnew = 1.0 / mb
        idx = np.empty((N, D), np.int64)
        idx[:, 0] = rng.integers(0, n, N)
        newb = rng.random((N, D)) < pnew
        jump = rng.integers(0, n, (N, D))
        for t in range(1, D):
            nxt = (idx[:, t - 1] + 1) % n
            idx[:, t] = np.where(newb[:, t], jump[:, t], nxt)
        C = tr[idx, 0]
        H = tr[idx, 1]
        L = tr[idx, 2]
        return C.astype(np.float32), H.astype(np.float32), L.astype(np.float32), U
    sd = params["sd"]
    if process == "P0":
        C = rng.standard_normal((N, D)) * sd
        S = np.full((N, D), sd)
    elif process == "P1":
        nu = max(params["df"], 3.0)                      # df floored at 3 (finite kurtosis not needed, but finite variance is)
        C = rng.standard_t(nu, (N, D)) * np.sqrt((nu - 2.0) / nu) * sd
        S = np.full((N, D), sd)
    else:
        om, al, ga, be, nu = adj_garch(params["garch"], sd)   # persistence capped at 0.995, omega set so that unconditional sd = sample sd
        burn = 500
        T = D + burn
        if process == "P2":
            Z = rng.standard_t(nu, (N, T)) * np.sqrt((nu - 2.0) / nu)
        else:
            sr = params["std_resid"]
            Z = sr[rng.integers(0, sr.shape[0], (N, T))]
        s2 = np.full(N, om / (1.0 - al - 0.5 * ga - be))
        Cc = np.empty((N, T), np.float32)
        Ss = np.empty((N, T), np.float32)
        for t in range(T):
            sdt = np.sqrt(s2)
            eps = sdt * Z[:, t]
            Cc[:, t] = eps
            Ss[:, t] = sdt
            s2 = om + (al + ga * (eps < 0)) * eps * eps + be * s2
        C = Cc[:, burn:]
        S = Ss[:, burn:]
        C = C.astype(np.float64)
        S = S.astype(np.float64)
    if process in ("P1", "P2", "P3"):                     # rescale so the bank's overall sd equals the sample sd (comparable sigma_a across processes)
        f = sd / C.std()
        C = C * f; S = S * f
    if intraday:
        M, m = _bridge_extremes(C, S, rng)
    else:
        M = np.maximum(C, 0.0)
        m = np.minimum(C, 0.0)
    return C.astype(np.float32), M.astype(np.float32), m.astype(np.float32), U


def lattice_bank(step: float, N: int, D: int, seed: int):
    """Bank for exact-lattice validation: every day C = +step (direction random via U, h = 0.5 -> +-step), no excursions."""
    rng = np.random.default_rng(seed)
    C = np.full((N, D), step, np.float32)
    H = C.copy()
    L = np.zeros((N, D), np.float32)
    U = rng.random((N, D), dtype=np.float32)
    return C, H, L, U
