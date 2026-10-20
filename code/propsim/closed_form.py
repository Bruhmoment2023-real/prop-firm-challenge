"""Closed-form benchmarks for prop-challenge pass probabilities.

Model: account profit X_t (as a fraction of the starting balance) is an arithmetic Brownian motion
    X_t = mu * t + sigma * W_t ,  X_0 = 0,
with profit target a > 0 and loss allowance b > 0 (static) or d > 0 (trailing drawdown).
Time is measured in trading days, so sigma is the DAILY standard deviation of account P&L and mu the daily drift.
For n trades per day, each with standard deviation r and mean q*r:  sigma = r*sqrt(n),  mu = q*r*n.

Every formula here is classical. Sources (see 01-prior-work.md for links):
  * two-barrier exit probability / gambler's ruin: Feller (1968) ch. XIV; Karlin & Taylor (1975) ch. 7
  * exit before a deadline: eigenfunction (Fourier sine) series for the heat equation on an interval,
    Darling & Siegert (1953); Borodin & Salminen, Handbook of Brownian Motion, formula 1.3.0.x family
  * maximum before a drawdown of size d: Taylor (1975), Lehoczky (1977); Hadjiliadis & Vecer (2006)
  * daily (discrete) monitoring correction: Broadie, Glasserman & Kou (1997), beta = -zeta(1/2)/sqrt(2*pi)
Nothing in this file is new mathematics; the contribution is applying it to published rule sets.
"""
from __future__ import annotations

import math

BGK_BETA = 0.5825971579390107  # -zeta(1/2)/sqrt(2*pi)


# ----------------------------------------------------------------------------- static barriers
def p_static(a: float, b: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """P(hit +a before -b), no deadline. Driftless value is b/(a+b), independent of sigma."""
    if abs(mu) < 1e-15:
        return b / (a + b)
    th = 2.0 * mu / sigma ** 2
    # scale function s(x) = exp(-th x):  (s(0)-s(-b)) / (s(a)-s(-b))
    return (1.0 - math.exp(th * b)) / (math.exp(-th * a) - math.exp(th * b)) if th * b < 700 else \
        1.0 - math.exp(-th * b)  # large positive drift: avoid overflow


def p_static_deadline(a: float, b: float, t: float, mu: float = 0.0, sigma: float = 1.0, terms: int = 400) -> float:
    """P(hit +a before -b AND before time t). Exponentially convergent sine series.

    P(t) = P(inf) - exp(mu*a/sigma^2) * (sigma^2*pi/L^2) * sum_{n>=1} (-1)^(n+1) n sin(n pi b/L)
                                                         * exp(-(lam_n+g) t) / (lam_n+g)
    with L = a+b, lam_n = n^2 pi^2 sigma^2 / (2 L^2), g = mu^2 / (2 sigma^2).
    """
    if t <= 0:
        return 0.0
    L = a + b
    g = mu * mu / (2.0 * sigma * sigma)
    pref = math.exp(mu * a / sigma ** 2) * sigma ** 2 * math.pi / L ** 2
    s = 0.0
    for n in range(1, terms + 1):
        lam = n * n * math.pi ** 2 * sigma ** 2 / (2.0 * L * L)
        term = (-1) ** (n + 1) * n * math.sin(n * math.pi * b / L) * math.exp(-(lam + g) * t) / (lam + g)
        s += term
        if (lam + g) * t > 60:
            break
    return max(0.0, p_static(a, b, mu, sigma) - pref * s)


def p_fail_static_deadline(a: float, b: float, t: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """P(hit -b before +a AND before time t), by reflection of the problem."""
    return p_static_deadline(b, a, t, -mu, sigma)


def expected_exit_time(a: float, b: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """E[first exit time from (-b, a)]. Driftless: a*b/sigma^2 (days)."""
    if abs(mu) < 1e-15:
        return a * b / sigma ** 2
    p = p_static(a, b, mu, sigma)
    return (p * a - (1 - p) * b) / mu  # Wald's identity


# ----------------------------------------------------------------------------- trailing drawdown
def p_trailing(a: float, d: float, mu: float = 0.0, sigma: float = 1.0, lock: bool = False) -> float:
    """P(profit reaches +a before the account falls d below its running peak), continuous trailing.

    Driftless, no lock:  exp(-a/d).   (The peak reached before a drawdown of d is exponential with mean d.)
    With drift: exp(-a*th/(exp(th*d)-1)), th = 2mu/sigma^2.   [Taylor 1975; Lehoczky 1977]
    lock=True: the floor stops rising once it reaches the starting balance (peak = d); from there the
    problem is a static two-barrier one from x=d with barriers at 0 and a.
    """
    th = 2.0 * mu / sigma ** 2

    def hazard() -> float:
        return 1.0 / d if abs(th * d) < 1e-12 else th / math.expm1(th * d)

    if not lock or a <= d:
        return math.exp(-a * hazard())
    return math.exp(-d * hazard()) * p_static(a - d, d, mu, sigma)


# ----------------------------------------------------------------------------- discrete monitoring
def p_static_discrete(a: float, b: float, step_sd: float) -> float:
    """Driftless Gaussian random walk observed only at steps of s.d. `step_sd` (e.g. end of day).

    Broadie-Glasserman-Kou continuity correction: each barrier is effectively beta*step_sd further away.
    As step_sd -> infinity this tends to 1/2: one huge step decides the account like a coin flip.
    """
    s = BGK_BETA * step_sd
    return (b + s) / (a + b + 2.0 * s)


# ----------------------------------------------------------------------------- lattice gambler's ruin
def p_gamblers_ruin(up_steps: int, down_steps: int, p_win: float = 0.5) -> float:
    """Simple random walk, +1 w.p. p_win, -1 otherwise: P(reach +up_steps before -down_steps). Exact."""
    if abs(p_win - 0.5) < 1e-15:
        return down_steps / (up_steps + down_steps)
    rho = (1.0 - p_win) / p_win
    return (rho ** down_steps - 1.0) / (rho ** (up_steps + down_steps) - 1.0)


# ----------------------------------------------------------------------------- bounds and economics
def zero_edge_ceiling(targets, loss) -> float:
    """Optional-stopping ceiling for ANY zero-edge strategy (any sizing), barriers hit without overshoot.

    One phase: E[X_tau] = 0 with X_tau = +a on a pass and X_tau >= -b on a fail  =>  p <= b/(a+b).
    The same inequality holds for a trailing floor because the floor is never below -b.
    Phases are independent restarts, so the ceilings multiply.
    """
    p = 1.0
    for a in targets:
        p *= loss / (a + loss)
    return p


def max_likelihood_ratio(targets, loss) -> float:
    """Largest possible positive likelihood ratio of 'passed' as a test of skill when unskilled = zero edge.

    P(pass | skilled) <= 1 and P(pass | zero edge) = ceiling  =>  LR+ <= 1/ceiling.
    """
    return 1.0 / zero_edge_ceiling(targets, loss)


def ppv(prior_skilled: float, p_pass_skilled: float, p_pass_unskilled: float) -> float:
    """Bayes: P(skilled | passed)."""
    num = prior_skilled * p_pass_skilled
    return num / (num + (1.0 - prior_skilled) * p_pass_unskilled)


def funded_first_payout_value(x: float, loss: float, split: float) -> float:
    """Zero-edge value (fraction of account) of 'trade the funded account until +x or bust, then withdraw'.

    P(reach +x before -loss) = loss/(loss+x); payout = split*x.  Tends to split*loss as x grows.
    The trader's downside in the funded stage is zero, so this is strictly positive: it is option value.
    """
    return split * x * loss / (loss + x)
