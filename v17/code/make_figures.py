"""Figures from result CSVs, 600 dpi PNG (and TIFF copies for the journal). Reads results/*.csv only."""
import pathlib, glob
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).resolve().parents[1]; RES = ROOT / "results"; FIG = ROOT / "figures"; FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100})
DPI = 600


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=DPI, bbox_inches="tight"); fig.savefig(FIG / f"{name}.tif", dpi=DPI, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"}); plt.close(fig)


def grid():
    return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RES / "grid" / "E1_*.csv")))], ignore_index=True)


def fig_validation():
    v = pd.read_csv(RES / "validation_v3.csv")
    fig, ax = plt.subplots(figsize=(4.2, 4.2)); ax.plot([0, 1], [0, 1], "k-", lw=0.5)
    ax.errorbar(v.ref, v.sim, yerr=3 * v.se, fmt="o", ms=3, lw=0.8, color="C0")
    ax.set_xlabel("Reference (exact lattice, integral equation, closed form, or old simulator)"); ax.set_ylabel("New daily simulator"); ax.set_xlim(0, 0.6); ax.set_ylim(0, 0.6)
    save(fig, "figV_validation")


def fig_heat():
    d = grid(); d = d[(d.sigma_a == 0.01) & (d.h == 0.5) & (d.m == 1.0)]
    t = d.pivot_table(index="pid", columns=["asset", "process"], values="p_pass")
    fig, ax = plt.subplots(figsize=(9, 4.2)); im = ax.imshow(t.values * 100, aspect="auto", cmap="viridis")
    ax.set_yticks(range(len(t.index))); ax.set_yticklabels(t.index); ax.set_xticks(range(t.shape[1])); ax.set_xticklabels([f"{a}\n{p}" for a, p in t.columns], fontsize=5)
    for i in range(t.shape[0]):
        for j in range(t.shape[1]): ax.text(j, i, f"{t.values[i, j]*100:.0f}", ha="center", va="center", fontsize=4, color="w")
    fig.colorbar(im, label="zero-skill pass probability (%)"); save(fig, "fig2_heat_zero_skill")


def fig_skill():
    d = grid(); d = d[(d.sigma_a == 0.01) & (d.m == 1.0) & (d.asset == "ES") & (d.process == "P2")]
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    for pid, g in d.groupby("pid"): g = g.sort_values("h"); ax.plot(g.h, g.p_pass * 100, lw=0.9, label=pid)
    ax.set_xlabel("direction accuracy h"); ax.set_ylabel("pass probability (%)"); ax.legend(fontsize=4, ncol=2, frameon=False); save(fig, "fig3_pass_vs_skill")


def fig_drivers():
    d = pd.read_csv(RES / "E3b_drivers.csv").sort_values("drop_one_partial_R2")
    fig, ax = plt.subplots(figsize=(4.2, 3.2)); ax.barh(d.feature, d.drop_one_partial_R2); ax.set_xlabel("drop-one partial R$^2$ (logit zero-skill pass probability)"); save(fig, "fig4_rule_drivers")
    c = pd.read_csv(RES / "E3a_counterfactuals.csv"); c = c[(c.process == "P2") & (c.scenario != "baseline")]
    t = c.pivot_table(index="pid", columns="scenario", values="delta") * 100
    fig, ax = plt.subplots(figsize=(7, 4)); im = ax.imshow(t.values, aspect="auto", cmap="RdBu", vmin=-30, vmax=30)
    ax.set_yticks(range(len(t.index))); ax.set_yticklabels(t.index); ax.set_xticks(range(t.shape[1])); ax.set_xticklabels(t.columns, rotation=60, ha="right")
    for i in range(t.shape[0]):
        for j in range(t.shape[1]):
            if not np.isnan(t.values[i, j]): ax.text(j, i, f"{t.values[i, j]:.0f}", ha="center", va="center", fontsize=5)
    fig.colorbar(im, label="change in zero-skill pass probability (points)"); save(fig, "fig5_counterfactuals")


def fig_revenue():
    e = pd.read_csv(RES / "E4_firm_revenue.csv"); e = e[(e.asset == "ES") & (e.process == "P2") & (e.K == 3)]
    t = e.pivot_table(index="pid", columns="population", values="house_edge") * 100
    fig, ax = plt.subplots(figsize=(7, 3.4)); w = 0.16
    for j, c in enumerate(t.columns): ax.bar(np.arange(len(t)) + j * w, t[c], w, label=c)
    ax.set_xticks(np.arange(len(t)) + 2 * w); ax.set_xticklabels(t.index, rotation=45, ha="right"); ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("house edge = 1 - payouts / fees (%), axis clipped at -150"); ax.set_ylim(-150, 100); ax.legend(fontsize=5, frameon=False); save(fig, "fig6_house_edge")


def fig_calib():
    d = pd.read_csv(RES / "V6_oos_calibration.csv"); t = d.pivot_table(index=["asset", "metric"], columns="process", values="two_sided_p")
    fig, ax = plt.subplots(figsize=(4, 5)); im = ax.imshow(t.values, aspect="auto", cmap="RdYlGn", vmin=0, vmax=0.2)
    ax.set_yticks(range(len(t.index))); ax.set_yticklabels([f"{a} {m}" for a, m in t.index], fontsize=5); ax.set_xticks(range(t.shape[1])); ax.set_xticklabels(t.columns)
    fig.colorbar(im, label="two-sided p (capped at 0.2)"); save(fig, "fig1_oos_calibration")


if __name__ == "__main__":
    import sys
    for f in (sys.argv[1:] or ["fig_validation", "fig_calib", "fig_heat", "fig_skill", "fig_drivers", "fig_revenue"]):
        try: globals()[f](); print("ok", f)
        except Exception as ex: print("skip", f, ex)
