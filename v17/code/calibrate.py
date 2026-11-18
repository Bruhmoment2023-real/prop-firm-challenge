"""Calibrate return processes P0-P4 to free daily data (PLAN section 2) and run the out-of-sample test (V6) and the range check (V5).
Outputs: results/calibration_params.json, results/V6_oos_calibration.csv, results/V5_bridge_range.csv, results/calibration_fit_table.csv
"""
import json, pathlib, sys, warnings
import numpy as np, pandas as pd
from scipy import stats
from arch import arch_model
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import v3sim as v
warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parents[1]
RES = ROOT / "results"; RES.mkdir(exist_ok=True)
ASSETS = {"ES": "ES_F", "NQ": "NQ_F", "EURUSD": "EURUSD", "GOLD": "GC_F", "BTC": "BTCUSD"}
CLEAN_FX = True
END = "2026-11-14"; TRAIN_END = "2022-12-31"


def load(asset, end=END):
    d = pd.read_csv(ROOT / "data" / "market" / f"{ASSETS[asset]}_1d.csv", parse_dates=["date"])
    d = d[d["date"] <= end].reset_index(drop=True)
    return d


def log_ohlc(d, fx=False):
    pc = d["close"].shift(1)
    r = np.log(d["close"] / pc)
    hh = np.log(d["high"] / pc); ll = np.log(d["low"] / pc)
    m = pd.DataFrame({"c": r, "h": hh, "l": ll}).dropna()
    m = m[np.isfinite(m).all(axis=1)]
    if fx:   # Yahoo FX daily series has erroneous prints (e.g. EURUSD 2008-12-08 close 1.4918 between ~1.27 neighbours): drop |r|>5% days and the next day, and ranges > 6%
        bad = (m["c"].abs() > 0.05) | ((m["h"] - m["l"]) > 0.06)
        bad = bad | bad.shift(1, fill_value=False)
        m = m[~bad]
    return m


def fit_all(m):
    r = m["c"].to_numpy()
    mu = r.mean(); x = r - mu; sd = x.std(ddof=1)
    df, loc, sc = stats.t.fit(x / sd, floc=0.0)
    df = float(max(df, 2.2))
    am = arch_model(x * 100.0, mean="Zero", vol="GARCH", p=1, o=1, q=1, dist="t")
    res = am.fit(disp="off", options={"maxiter": 1000})
    p = res.params
    om, al, ga, be, nu = p["omega"] / 1e4, p["alpha[1]"], p["gamma[1]"], p["beta[1]"], p["nu"]
    persist = al + 0.5 * ga + be
    z = np.asarray(res.resid) / np.asarray(res.conditional_volatility)
    z = (z - z.mean()) / z.std()
    trip = np.column_stack([x, (m["h"].to_numpy() - mu), (m["l"].to_numpy() - mu)])
    trip[:, 1] = np.maximum(trip[:, 1], np.maximum(trip[:, 0], 0.0)); trip[:, 2] = np.minimum(trip[:, 2], np.minimum(trip[:, 0], 0.0))
    return dict(mu=mu, sd=sd, df=df, garch=(om, al, ga, be, nu), persist=persist, loglik=float(res.loglikelihood), std_resid=z, triples=trip, n=len(r))


def metrics(x, sd_ref):
    x = np.asarray(x)
    k = stats.kurtosis(x)
    tail = np.mean(np.abs(x) > 3 * sd_ref)
    a = np.abs(x)
    ac = np.corrcoef(a[:-1], a[1:])[0, 1]
    return k, tail, ac


def kupiec(n, x, p):
    if x == 0:
        return -2 * (n * np.log(1 - p)), 1.0 - 0
    ph = x / n
    lr = -2 * ((n - x) * np.log(1 - p) + x * np.log(p) - (n - x) * np.log(1 - ph) - x * np.log(ph))
    return lr, 1 - stats.chi2.cdf(lr, 1)


def main():
    out_params = {}; fit_rows = []; oos = []; rng_rows = []
    for a in ASSETS:
        d = load(a); m = log_ohlc(d, a == "EURUSD")
        P = fit_all(m)
        out_params[a] = dict(mu=P["mu"], sd=P["sd"], df=P["df"], garch=list(P["garch"]), persist=P["persist"], n=P["n"],
                             first=str(d["date"].iloc[0].date()), last=str(d["date"].iloc[-1].date()))
        fit_rows.append(dict(asset=a, n=P["n"], first=out_params[a]["first"], last=out_params[a]["last"], daily_sd_pct=100 * P["sd"],
                             ann_vol_pct=100 * P["sd"] * np.sqrt(252), excess_kurt=stats.kurtosis(m["c"]), t_df=P["df"], garch_omega=P["garch"][0],
                             alpha=P["garch"][1], gamma=P["garch"][2], beta=P["garch"][3], nu=P["garch"][4], persistence=P["persist"]))
        # V5 range device: real mean (H-L)/sd(C) vs bank
        real_ratio = float((P["triples"][:, 1] - P["triples"][:, 2]).mean() / P["sd"])
        pars = dict(sd=P["sd"], df=P["df"], garch=P["garch"], std_resid=P["std_resid"], triples=P["triples"])
        row = dict(asset=a, real_range_over_sd=real_ratio)
        for proc in ["P0", "P1", "P2", "P3"]:
            C, H, L, U = v.make_bank(proc, pars, 4000, 1000, 11)
            row[proc] = float((H.astype(float) - L.astype(float)).mean() / C.astype(float).std())
        rng_rows.append(row)
        # V6 out-of-sample: fit on <= TRAIN_END, compare with later data
        d1 = d[d["date"] <= TRAIN_END]; d2 = d[d["date"] > TRAIN_END]
        m1 = log_ohlc(d1, a == "EURUSD"); m2 = log_ohlc(d2, a == "EURUSD")
        P1_ = fit_all(m1)
        x2 = (m2["c"].to_numpy() - P1_["mu"]); n2 = len(x2); sd1 = P1_["sd"]
        real = dict(zip(["kurt", "tail3sd", "acf_abs"], metrics(x2, sd1)))
        # simulated distributions of the same metrics, n2 days
        for proc in ["P0", "P1", "P2", "P3"]:
            pars1 = dict(sd=sd1, df=P1_["df"], garch=P1_["garch"], std_resid=P1_["std_resid"])
            C, H, L, U = v.make_bank(proc, pars1, 3000, n2, 21, intraday=False)
            sims = np.array([metrics(C[i].astype(float), sd1) for i in range(C.shape[0])])
            for j, name in enumerate(["kurt", "tail3sd", "acf_abs"]):
                pct = float((sims[:, j] < real[name]).mean() + 0.5 * (sims[:, j] == real[name]).mean())
                oos.append(dict(asset=a, process=proc, metric=name, realised=real[name], sim_median=float(np.median(sims[:, j])),
                                sim_p5=float(np.percentile(sims[:, j], 5)), sim_p95=float(np.percentile(sims[:, j], 95)),
                                realised_percentile=pct, two_sided_p=2 * min(pct, 1 - pct), n_test=n2, train_end=TRAIN_END))
            # VaR exceedances with filtered volatility (GARCH) or unconditional quantiles
            for pr in (0.01, 0.05):
                if proc == "P0":
                    q = stats.norm.ppf(pr) * sd1 * np.ones(n2)
                elif proc == "P1":
                    q = stats.t.ppf(pr, P1_["df"]) * np.sqrt((P1_["df"] - 2) / P1_["df"]) * sd1 * np.ones(n2)
                else:
                    om, al, ga, be, nu = P1_["garch"]
                    s2 = np.empty(n2); prev = m1["c"].to_numpy()[-1] - P1_["mu"]
                    # last train conditional variance approximated by unconditional start then filtered over last 250 train days
                    xs = np.concatenate([m1["c"].to_numpy()[-250:] - P1_["mu"], x2])
                    sv = om / (1 - al - 0.5 * ga - be); sig = []
                    for t in range(len(xs)):
                        sig.append(sv); sv = om + (al + ga * (xs[t] < 0)) * xs[t] ** 2 + be * sv
                    sig = np.sqrt(np.array(sig[250:]))
                    if proc == "P2":
                        zq = stats.t.ppf(pr, nu) * np.sqrt((nu - 2) / nu)
                    else:
                        zq = np.quantile(P1_["std_resid"], pr)
                    q = zq * sig
                xcount = int((x2 < q).sum()); lr, pv = kupiec(n2, xcount, pr)
                oos.append(dict(asset=a, process=proc, metric=f"VaR{int(pr*100)}_exceed", realised=xcount, sim_median=pr * n2,
                                sim_p5=np.nan, sim_p95=np.nan, realised_percentile=np.nan, two_sided_p=pv, n_test=n2, train_end=TRAIN_END))
        print(a, "done", flush=True)
    json.dump(out_params, open(RES / "calibration_params.json", "w"), indent=1)
    pd.DataFrame(fit_rows).to_csv(RES / "calibration_fit_table.csv", index=False)
    pd.DataFrame(oos).to_csv(RES / "V6_oos_calibration.csv", index=False)
    pd.DataFrame(rng_rows).to_csv(RES / "V5_bridge_range.csv", index=False)


if __name__ == "__main__":
    main()
