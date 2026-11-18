"""E3: (a) one-rule-removed counterfactuals with common random numbers; (b) synthetic rule space regression. PLAN section 6."""
import os, sys, math, pathlib, copy
os.environ.setdefault("NUMBA_NUM_THREADS", "3")
import numpy as np, pandas as pd, psutil
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import v3sim as v
from pars import get_pars
from run_grid import rules, guard, SPREAD_BP
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
RES = ROOT / "results"


def mods(r):
    out = {"baseline": r}
    def m(name, **kw):
        x = copy.deepcopy(r); x.update(kw); out[name] = x
    if r["daily_loss"] > 0: m("no_daily_limit", daily_loss=0.0)
    if r["dd_type"] != "static": m("trailing_to_static", dd_type="static", lock=0)
    if r["dd_type"] != "static" and not r["lock"]: m("add_lock", lock=1)
    if r["dd_type"] != "static" and r["lock"]: m("remove_lock", lock=0)
    if r["time_limit"] > 0: m("no_deadline", time_limit=0)
    if r["consistency"] > 0: m("no_consistency", consistency=0.0)
    if r["min_days"] > 0 or r["min_profit_days"] > 0: m("no_min_days", min_days=0, min_profit_days=0)
    m("target_x0.5", targets=[t * 0.5 for t in r["targets"]])
    m("max_loss_x1.5", max_loss=r["max_loss"] * 1.5, daily_loss=r["daily_loss"])
    m("intraday_monitoring_off", dd_type=r["dd_type"])  # placeholder replaced below by close-only bank
    del out["intraday_monitoring_off"]
    m("all_soft_rules_off", daily_loss=0.0, consistency=0.0, min_days=0, min_profit_days=0, time_limit=0)
    return out


def part_a():
    R = rules(); a = "ES"; pars = get_pars(a); sd = pars["sd"]; rows = []
    for proc in ("P0", "P2", "P4"):
        guard()
        bank = v.make_bank(proc, pars, 20000, 1200, 555)
        closeonly = (bank[0], np.maximum(bank[0], 0), np.minimum(bank[0], 0), bank[3])
        lev = 0.01 / sd; cst = lev * SPREAD_BP[a] * 1e-4
        for pid, r in R.items():
            base = None
            for name, x in mods(r).items():
                code, days, pay = v.simulate(bank, lev, 0.5, cst, v.rule_vector(x), maxdays=1000)
                ps = (code == 1).astype(float)
                if name == "baseline": base = ps; p0 = ps.mean()
                p = ps.mean(); se = (ps - base).std(ddof=1) / math.sqrt(len(ps)) if name != "baseline" else math.sqrt(p * (1 - p) / len(ps))
                rows.append(dict(process=proc, pid=pid, scenario=name, p_pass=p, delta=p - p0, se_delta=se))
            code, days, pay = v.simulate(closeonly, lev, 0.5, cst, v.rule_vector(r), maxdays=1000)
            ps = (code == 1).astype(float)
            rows.append(dict(process=proc, pid=pid, scenario="close_only_monitoring", p_pass=ps.mean(), delta=ps.mean() - p0, se_delta=(ps - base).std(ddof=1) / math.sqrt(len(ps))))
        print("A", proc, flush=True)
    pd.DataFrame(rows).to_csv(RES / "E3a_counterfactuals.csv", index=False)


def part_b(n_sets=2000):
    R = rules(); rl = list(R.values()); rng = np.random.default_rng(2026)
    a = "ES"; pars = get_pars(a); sd = pars["sd"]
    bank = v.make_bank("P2", pars, 10000, 1200, 777); lev = 0.01 / sd; cst = lev * SPREAD_BP[a] * 1e-4
    rows = []
    pick = lambda k: rl[rng.integers(len(rl))][k]
    for i in range(n_sets):
        if i % 200 == 0: guard()
        r = dict(targets=[pick("targets")[0]] if rng.random() < 0.5 else [rl[rng.integers(len(rl))]["targets"][0], 0.05],
                 max_loss=pick("max_loss"), dd_type=pick("dd_type"), lock=0, daily_loss=pick("daily_loss"), daily_mode=pick("daily_mode"),
                 min_days=pick("min_days"), min_profit_days=pick("min_profit_days"), profit_day_thr=0.005, consistency=pick("consistency"),
                 time_limit=pick("time_limit"))
        r["lock"] = pick("lock") if r["dd_type"] != "static" else 0
        code, days, pay = v.simulate(bank, lev, 0.5, cst, v.rule_vector(r), maxdays=1000)
        p = float((code == 1).mean())
        rows.append(dict(i=i, p_pass=p, unresolved=float((code == 0).mean()), n_phases=len(r["targets"]), target_total=sum(r["targets"]), t1=r["targets"][0],
                         max_loss=r["max_loss"], dd_type=r["dd_type"], lock=r["lock"], daily_loss=r["daily_loss"], daily_mode=r["daily_mode"], min_days=r["min_days"],
                         min_profit_days=r["min_profit_days"], consistency=r["consistency"], time_limit=r["time_limit"]))
    d = pd.DataFrame(rows); d.to_csv(RES / "E3b_synthetic_rules.csv", index=False)
    print("B done", flush=True)


def analyse_b():
    import statsmodels.api as sm
    d = pd.read_csv(RES / "E3b_synthetic_rules.csv"); d = d[d.unresolved <= 0.02].copy()
    pc = d.p_pass.clip(0.002, 0.998); y = np.log(pc / (1 - pc))
    X = pd.DataFrame({"log_target_to_loss": np.log(d.target_total / d.max_loss), "two_phase": (d.n_phases == 2).astype(float),
                      "trail_eod": (d.dd_type == "trail_eod").astype(float), "trail_intraday": (d.dd_type == "trail_intraday").astype(float),
                      "lock": d.lock.astype(float), "daily_limit_tightness": np.where(d.daily_loss > 0, d.max_loss / d.daily_loss.replace(0, np.nan), 0.0),
                      "has_daily_limit": (d.daily_loss > 0).astype(float), "daily_pause": (d.daily_mode == "pause").astype(float) * (d.daily_loss > 0),
                      "consistency": d.consistency, "min_days": d.min_days, "min_profit_days": d.min_profit_days, "deadline": (d.time_limit > 0).astype(float)})
    Xs = (X - X.mean()) / X.std().replace(0, 1); Xs = sm.add_constant(Xs)
    full = sm.OLS(y, Xs).fit(); rows = []
    for c in X.columns:
        red = sm.OLS(y, Xs.drop(columns=[c])).fit()
        rows.append(dict(feature=c, std_coef=full.params[c], t=full.tvalues[c], drop_one_partial_R2=full.rsquared - red.rsquared))
    out = pd.DataFrame(rows).sort_values("drop_one_partial_R2", ascending=False); out["R2_full"] = full.rsquared; out["n"] = len(d)
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.inspection import permutation_importance
        g = GradientBoostingRegressor(random_state=0, n_estimators=300, max_depth=3).fit(X.fillna(0), y)
        pi = permutation_importance(g, X.fillna(0), y, n_repeats=10, random_state=0)
        out["gbr_perm_importance"] = out.feature.map(dict(zip(X.columns, pi.importances_mean)))
    except Exception as e:
        out["gbr_perm_importance"] = np.nan; print("sklearn unavailable", e)
    out.to_csv(RES / "E3b_drivers.csv", index=False); print(out.to_string())


if __name__ == "__main__":
    w = sys.argv[1]
    {"a": part_a, "b": part_b, "analyse": analyse_b}[w]()
