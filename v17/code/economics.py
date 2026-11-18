"""E4 (firm revenue, house edge, populations) and E5 (likelihood ratios) from the Tier-1 grid. PLAN sections 6."""
import sys, pathlib, glob, math
import numpy as np, pandas as pd
from scipy.stats import norm
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent; RES = ROOT / "results"
HG = [0.46, 0.48, 0.50, 0.52, 0.54, 0.56, 0.60]
dw = norm.pdf(HG, 0.49, 0.02); dw = dw / dw.sum()
POPS = {"A_1pct_skilled": ({0.56: 0.01, 0.50: 0.99}, 1.0), "B_5pct_skilled": ({0.56: 0.05, 0.50: 0.95}, 1.0), "C_20pct_skilled": ({0.56: 0.20, 0.50: 0.80}, 1.0),
        "D_dispersed": (dict(zip(HG, dw)), 1.0), "E_dispersed_wide_cost": (dict(zip(HG, dw)), 4.0)}
KS = [1, 3, 10]


def load():
    d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RES / "grid" / "E1_*.csv")))], ignore_index=True)
    r = pd.read_csv(ROOT / "data" / "rule_sets_v3_model.csv")[["pid", "tier_usd", "fee_usd", "activation_usd", "refund"]]
    return d.merge(r, on="pid")


def journey(row, K, hz="60"):
    p = row.p_pass; fee = row.fee_usd; act = row.activation_usd; acc = row.tier_usd
    if p <= 0: return dict(n_att=K, pK=0.0, fees=fee * K, pay=0.0, refund=0.0, fail_fees=fee * K)
    pK = 1 - (1 - p) ** K; n_att = pK / p
    pay_pass = getattr(row, f"pay{hz}_mean_pass") * acc if not np.isnan(getattr(row, f"pay{hz}_mean_pass")) else 0.0
    pos = getattr(row, f"pay{hz}_pospass") if not np.isnan(getattr(row, f"pay{hz}_pospass")) else 0.0
    fees = fee * n_att + act * pK
    return dict(n_att=n_att, pK=pK, fees=fees, pay=pK * pay_pass, refund=pK * pos * row.refund * fee, fail_fees=fee * (n_att - pK))


def main(hz="60"):
    suf = "" if hz == "60" else f"_h{hz}"
    d = load(); d = d[(d.sigma_a == 0.01) & d.pay60_mean_pass.notna() | ((d.sigma_a == 0.01) & (d.p_pass == 0))]
    d = d[d.fee_usd.notna()]
    rows = []
    for (a, proc, pid), g in d.groupby(["asset", "process", "pid"]):
        lk = {(round(r.h, 2), r.m): r for r in g.itertuples()}
        for pop, (w, m) in POPS.items():
            for K in KS:
                tot = dict(fees=0, pay=0, refund=0, fail_fees=0, pK=0, n_att=0); ok = True
                for h, wt in w.items():
                    r = lk.get((round(h, 2), m))
                    if r is None: ok = False; break
                    j = journey(r, K, hz)
                    for k in tot: tot[k] += wt * j[k]
                if not ok: continue
                rev = tot["fees"] - tot["pay"] - tot["refund"]
                rows.append(dict(asset=a, process=proc, pid=pid, population=pop, K=K, fees_per_buyer=tot["fees"], payouts_per_buyer=tot["pay"], refunds_per_buyer=tot["refund"],
                                 revenue_per_buyer=rev, house_edge=rev / tot["fees"] if tot["fees"] > 0 else np.nan,
                                 fee_share_from_failed_attempts=tot["fail_fees"] / tot["fees"] if tot["fees"] > 0 else np.nan, share_buyers_passing=tot["pK"],
                                 haircut_breakeven=(tot["fees"] - tot["refund"]) / tot["pay"] if tot["pay"] > 0 else np.nan))
    e = pd.DataFrame(rows); e.to_csv(RES / f"E4_firm_revenue{suf}.csv", index=False)
    if hz != "60": return
    # frictionless zero-skill buyer (h=0.5, m=0), single attempt and K=3: sign of firm revenue
    z = []
    for (a, proc, pid), g in d.groupby(["asset", "process", "pid"]):
        r = g[(g.h == 0.5) & (g.m == 0.0)]
        if len(r) == 0: continue
        r = next(r.itertuples())
        for K in KS:
            j = journey(r, K); z.append(dict(asset=a, process=proc, pid=pid, K=K, revenue_per_buyer=j["fees"] - j["pay"] - j["refund"], p_pass=r.p_pass))
    pd.DataFrame(z).to_csv(RES / "E4b_frictionless_zero_skill.csv", index=False)
    # break-even skilled share (h=0.56 vs 0.50, m=1)
    be = []
    for (a, proc, pid, K), g in e.groupby(["asset", "process", "pid", "K"]):
        x = g.set_index("population").revenue_per_buyer
        r0 = (x["A_1pct_skilled"] - 0.01 * x["B_5pct_skilled"] / 0.05) if False else None
        # linear in pi: rev(pi) = rev0 + pi*(rev1-rev0); use A (1%) and C (20%) to recover both ends
        slope = (x["C_20pct_skilled"] - x["A_1pct_skilled"]) / 0.19; rev0 = x["A_1pct_skilled"] - 0.01 * slope
        pistar = -rev0 / slope if slope != 0 else np.nan
        be.append(dict(asset=a, process=proc, pid=pid, K=K, rev_all_unskilled=rev0, rev_all_skilled=rev0 + slope, breakeven_skilled_share=pistar))
    pd.DataFrame(be).to_csv(RES / "E4c_breakeven_skilled_share.csv", index=False)
    # E5 likelihood ratios
    l = []
    for (a, proc, pid), g in d.groupby(["asset", "process", "pid"]):
        s = g[(g.h == 0.56) & (g.m == 1.0)]; u = g[(g.h == 0.50) & (g.m == 1.0)]
        if len(s) == 0 or len(u) == 0: continue
        p1, p0 = float(s.p_pass.iloc[0]), float(u.p_pass.iloc[0])
        for K in (1, 3, 5):
            q1 = 1 - (1 - p1) ** K; q0 = 1 - (1 - p0) ** K
            row = dict(asset=a, process=proc, pid=pid, K=K, p_skilled=q1, p_unskilled=q0, LR=q1 / q0 if q0 > 0 else np.nan)
            for pr in (0.01, 0.05, 0.20):
                row[f"posterior_prior{int(pr*100)}"] = pr * q1 / (pr * q1 + (1 - pr) * q0) if q0 > 0 else np.nan
            l.append(row)
    pd.DataFrame(l).to_csv(RES / "E5_likelihood_ratios.csv", index=False)
    print("econ done", len(e), len(be), len(l))


def distribution_metrics():
    """Net-negative share and payout concentration for ES / P2 using stored path samples."""
    z = np.load(RES / "grid" / "samples_ES_P2.npz"); r = pd.read_csv(ROOT / "data" / "rule_sets_v3_model.csv").set_index("pid")
    rng = np.random.default_rng(99); rows = []
    for pid in r.index:
        if not r.loc[pid, "fee_usd"] == r.loc[pid, "fee_usd"]: continue
        fee, act, acc, ref = r.loc[pid, "fee_usd"], r.loc[pid, "activation_usd"], r.loc[pid, "tier_usd"], r.loc[pid, "refund"]
        for pop, (w, m) in POPS.items():
            for K in (3,):
                n = 100000; hs = list(w.keys()); ty = rng.choice(len(hs), n, p=np.array(list(w.values())) / sum(w.values()))
                net = np.zeros(n); pay_tot = np.zeros(n)
                for ti, h in enumerate(hs):
                    key = f"{pid}|{h}|{m}"
                    if key + "|pass" not in z: break
                    ps = z[key + "|pass"]; pp = z[key + "|pay60"]; idx = np.where(ty == ti)[0]
                    if len(idx) == 0: continue
                    draw = rng.integers(0, len(ps), (len(idx), K)); passed = ps[draw]
                    first = np.where(passed.any(axis=1), passed.argmax(axis=1), K)       # index of first pass, K = none
                    nat = np.minimum(first + 1, K); fees = fee * nat + act * (first < K)
                    payout = np.where(first < K, pp[draw[np.arange(len(idx)), np.minimum(first, K - 1)]] * acc, 0.0)
                    refund = np.where((first < K) & (payout > 0), ref * fee, 0.0)
                    net[idx] = payout + refund - fees; pay_tot[idx] = payout
                else:
                    top = np.sort(pay_tot)[::-1]; s = top.sum()
                    rows.append(dict(pid=pid, population=pop, K=K, share_net_negative=float((net < 0).mean()), mean_net=float(net.mean()),
                                     share_payouts_to_top10pct=float(top[: n // 10].sum() / s) if s > 0 else np.nan, share_buyers_with_any_payout=float((pay_tot > 0).mean())))
    pd.DataFrame(rows).to_csv(RES / "E4d_distribution_ES_P2.csv", index=False)


if __name__ == "__main__":
    main(); main('20'); main('120'); distribution_metrics()
