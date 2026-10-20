"""Monte Carlo simulator for prop-firm challenges (evaluation stage and funded stage).

All money quantities are FRACTIONS OF THE STARTING BALANCE (0.10 = 10%).  A path is a sequence of
trading days, each with `n_trades` trades.  Equity is checked after every trade (so n_trades also sets
how finely the loss limits are monitored).

Per-trade P&L models (`dist`):
  0 GAUSS      r * (edge + Z),               Z ~ N(0,1)
  1 STUDENT_T  r * (edge + T*sqrt((df-2)/df)), T ~ t(df)       (fat tails, unit variance)
  2 BERNOULLI  +R*r with prob (1+edge)/(1+R), else -r           (fixed stop / fixed target trade)
  3 BOOTSTRAP  r * (edge + B),  B = block-resampled standardised real returns (mean 0, s.d. 1)
`risk` r is the per-trade standard deviation (models 0,1,3) or the per-trade stop loss (model 2).
`edge` is the expected profit per trade in units of r.  edge = 0 is the zero-skill trader.
`cost` is a per-trade cost in units of r (spread/commission); it is simply subtracted from every trade.

Sizing policies (`stop_k`):
  0   naive: always trade size r until a rule is broken.
  >0  rule-aware: never open a trade whose stop would break a rule. The trade's r is cut to the room left
      above the maximum-loss floor, and to 99% of the room left under today's daily loss limit; trading
      stops for the day once that room is below a tenth of r.  For the Bernoulli (fixed stop/target) model the
      trade is also cut so that a win lands on the profit target instead of beyond it.  With that model this
      removes overshoot at both ends: the floor and the target are hit exactly and the daily limit is never hit.

Rules handled: several phases; static, end-of-day-trailing and intraday-trailing maximum loss, with or
without a lock at the starting balance; daily loss limit as a hard breach or as a pause; minimum trading
days; minimum profitable days; best-day consistency rule; time limit per phase.

Outcome codes: 1 pass, -1 max-loss breach, -2 daily-loss breach, -3 time limit, 0 unresolved at max_days.
"""
from __future__ import annotations

import numpy as np
from numba import njit

GAUSS, STUDENT_T, BERNOULLI, BOOTSTRAP = 0, 1, 2, 3
DD_STATIC, DD_TRAIL_EOD, DD_TRAIL_INTRADAY = 0, 1, 2
DAILY_BREACH, DAILY_PAUSE = 0, 1
EPS = 1e-12   # tolerance so that e.g. ten wins of 0.01 count as reaching a 0.10 target


@njit(cache=True)
def _draw(dist, edge, R, df, boot, state):
    """One standardised trade outcome in units of r. `state` = [boot index, draws left in block, block]."""
    if dist == 0:
        return edge + np.random.standard_normal()
    if dist == 1:
        return edge + np.random.standard_t(df) * np.sqrt((df - 2.0) / df)
    if dist == 2:
        p = (1.0 + edge) / (1.0 + R)
        return R if np.random.random() < p else -1.0
    if state[1] <= 0:
        state[0] = np.random.randint(0, boot.shape[0])
        state[1] = state[2]
    v = boot[state[0] % boot.shape[0]]
    state[0] += 1
    state[1] -= 1
    return edge + v


@njit(cache=True)
def _one_phase(target, daily, daily_mode, maxloss, dd_type, lock, min_days, min_pdays, pday_thr, consist,
               time_limit, n_trades, risk, edge, cost, dist, R, df, boot, state, stop_k, max_days):
    """Simulate one phase. Returns (code, days_used, trades_used)."""
    bal = 0.0
    floor = -maxloss
    peak = 0.0
    days = 0
    trades = 0
    tdays = 0          # days with at least one trade
    pdays = 0          # days with profit >= pday_thr
    best_day = 0.0
    idle = False       # target met, only waiting for minimum trading days
    while True:
        days += 1
        if time_limit > 0 and days > time_limit:
            return -3, days - 1, trades
        if days > max_days:
            return 0, days - 1, trades
        sod = bal
        traded = False
        paused = False
        if idle:
            tdays += 1                       # a token trade of negligible size
            if tdays >= min_days:
                return 1, days, trades
            continue
        for _ in range(n_trades):
            if paused:
                break
            r = risk
            if stop_k > 0.0:
                room = bal - floor
                if room < r:
                    r = room                 # never risk more than the room to the max-loss floor
                if daily > 0.0:
                    droom = bal - (sod - daily)
                    if droom < 0.1 * risk:
                        break                # today's allowance is used up: stop for today
                    if r > 0.99 * droom:
                        r = 0.99 * droom     # never risk more than 99% of today's remaining allowance
                if dist == 2:                # fixed stop/target trade: do not aim past the profit target
                    day_run = bal - sod
                    bd0 = best_day if best_day > day_run else day_run
                    need0 = target
                    if consist > 0.0 and bd0 / consist > need0:
                        need0 = bd0 / consist
                    gap = need0 - bal
                    if gap > EPS and R * r > gap:
                        r = gap / R
            x = (_draw(dist, edge, R, df, boot, state) - cost) * r
            bal += x
            trades += 1
            traded = True
            if dd_type == 2 and bal > peak:  # intraday trailing on closed balance
                peak = bal
                floor = peak - maxloss
                if lock and floor > 0.0:
                    floor = 0.0
            if bal <= floor + EPS:
                return -1, days, trades
            if daily > 0.0 and bal <= sod - daily + EPS:
                if daily_mode == 0:
                    return -2, days, trades
                paused = True
                continue
            # pass check (best day includes today's running profit)
            day_pl = bal - sod
            bd = best_day if best_day > day_pl else day_pl
            need = target
            if consist > 0.0 and bd / consist > need:
                need = bd / consist
            if bal >= need - EPS and pdays + (1 if day_pl >= pday_thr and min_pdays > 0 else 0) >= min_pdays:
                if tdays + 1 >= min_days:
                    return 1, days, trades
                idle = True
                break
        # ---- end of day
        if traded:
            tdays += 1
        day_pl = bal - sod
        if day_pl > best_day:
            best_day = day_pl
        if min_pdays > 0 and day_pl >= pday_thr:
            pdays += 1
        if dd_type == 1 and bal > peak:      # end-of-day trailing
            peak = bal
            floor = peak - maxloss
            if lock and floor > 0.0:
                floor = 0.0


@njit(cache=True)
def sim_challenge(n_paths, seed, targets, daily, daily_mode, maxloss, dd_type, lock, min_days, min_pdays,
                  pday_thr, consist, time_limit, n_trades, risk, edge, cost, dist, R, df, boot, block,
                  stop_k, max_days):
    """Simulate `n_paths` full challenges. Returns (code, days, trades, failed_phase) arrays."""
    np.random.seed(seed)
    code = np.zeros(n_paths, np.int8)
    days = np.zeros(n_paths, np.int32)
    trades = np.zeros(n_paths, np.int64)
    fphase = np.zeros(n_paths, np.int8)
    state = np.zeros(3, np.int64)
    state[2] = block
    for i in range(n_paths):
        state[1] = 0
        dsum = 0
        tsum = 0
        c = 1
        for k in range(targets.shape[0]):
            c, d, t = _one_phase(targets[k], daily, daily_mode, maxloss, dd_type, lock, min_days, min_pdays,
                                 pday_thr, consist, time_limit, n_trades, risk, edge, cost, dist, R, df, boot,
                                 state, stop_k, max_days)
            dsum += d
            tsum += t
            if c != 1:
                fphase[i] = k + 1
                break
        code[i] = c
        days[i] = dsum
        trades[i] = tsum
    return code, days, trades, fphase


@njit(cache=True)
def sim_funded(n_paths, seed, daily, daily_mode, maxloss, dd_type, lock, n_trades, risk, edge, cost, dist, R,
               df, boot, block, stop_k, horizon, cycle, min_profit, split, payout_mode, win_days_needed,
               win_day_thr, payout_frac, payout_cap, consist):
    """Funded stage for `horizon` trading days. Returns (total payout to trader, number of payouts) per path.

    payout_mode 0 (CFD style): every `cycle` trading days, if profit >= min_profit (and the best-day rule,
        if any, is met) the trader withdraws ALL profit, receives split*profit, and the balance and the
        loss floor reset to their starting values.
    payout_mode 1 (futures style, e.g. Topstep XFA): balance starts at 0 with a trailing floor that locks at
        0; after `win_days_needed` days each with profit >= win_day_thr the trader may withdraw
        min(payout_frac*balance, payout_cap); the floor is then fixed at 0 and the day count restarts.
    The trader's own loss in this stage is zero by construction (the firm bears it).
    """
    np.random.seed(seed)
    paid = np.zeros(n_paths)
    npay = np.zeros(n_paths, np.int32)
    state = np.zeros(3, np.int64)
    state[2] = block
    for i in range(n_paths):
        state[1] = 0
        bal = 0.0
        floor = -maxloss
        peak = 0.0
        lk = lock          # per-path copy: payout_mode 1 switches the lock on after the first payout
        since = 0
        wins = 0
        best_day = 0.0
        dead = False
        for _day in range(horizon):
            sod = bal
            paused = False
            for _ in range(n_trades):
                if paused:
                    break
                r = risk
                if stop_k > 0.0:
                    room = bal - floor
                    if room < r:
                        r = room
                    if daily > 0.0:
                        droom = bal - (sod - daily)
                        if droom < 0.1 * risk:
                            break
                        if r > 0.99 * droom:
                            r = 0.99 * droom
                    if r <= 0.0:
                        break
                bal += (_draw(dist, edge, R, df, boot, state) - cost) * r
                if dd_type == 2 and bal > peak:
                    peak = bal
                    floor = peak - maxloss
                    if lk and floor > 0.0:
                        floor = 0.0
                if bal <= floor + EPS:
                    dead = True
                    break
                if daily > 0.0 and bal <= sod - daily + EPS:
                    if daily_mode == 0:
                        dead = True
                        break
                    paused = True
            if dead:
                break
            day_pl = bal - sod
            if day_pl > best_day:
                best_day = day_pl
            if dd_type == 1 and bal > peak:
                peak = bal
                floor = peak - maxloss
                if lk and floor > 0.0:
                    floor = 0.0
            since += 1
            if day_pl >= win_day_thr:
                wins += 1
            if payout_mode == 0:
                if since >= cycle and bal >= min_profit and bal > 0.0 and \
                        (consist <= 0.0 or best_day <= consist * bal):
                    paid[i] += split * bal
                    npay[i] += 1
                    bal = 0.0
                    floor = -maxloss
                    peak = 0.0
                    since = 0
                    best_day = 0.0
            else:
                if wins >= win_days_needed and bal > 0.0 and (consist <= 0.0 or best_day <= consist * bal):
                    w = payout_frac * bal
                    if w > payout_cap:
                        w = payout_cap
                    paid[i] += split * w
                    npay[i] += 1
                    bal -= w
                    floor = 0.0
                    lk = True
                    wins = 0
                    best_day = 0.0
    return paid, npay


def standardise(returns: np.ndarray) -> np.ndarray:
    """De-mean and scale to unit variance (imposes zero edge on a real return series)."""
    r = np.asarray(returns, float)
    r = r[np.isfinite(r)]
    return (r - r.mean()) / r.std()


EMPTY = np.zeros(1)
