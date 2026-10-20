"""Make the figures (PNG) and the compact summary tables (CSV) from the raw result tables.

Usage:  python code/03_figures_and_tables.py        (a few seconds; needs results/A..E CSVs)
Outputs in results/:  fig1_validation.png ... fig7_time_limit.png,  T1..T5 summary tables.
"""
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from propsim import closed_form as cf   # noqa: E402
from propsim import rules as R          # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[1] / "results"
plt.rcParams.update({"figure.dpi": 130, "font.size": 9, "axes.grid": True, "grid.alpha": 0.3})
RS = R.load_rule_sets()
ORDER = list(RS)
LABEL = {k: f'{v["firm"]} - {v["product"]}' for k, v in RS.items()}


def closed_form_benchmarks():
    """T1: per rule set, the zero-edge ceiling and the continuous-trailing value, from the rules alone."""
    rows = []
    for k, rs in RS.items():
        t, d = rs["targets"], float(rs["max_loss"])
        ceil = cf.zero_edge_ceiling(t, d)
        if rs["dd_type"] == "static":
            cont = ceil
            form = " x ".join(f"{d:g}/({a:g}+{d:g})" for a in t)
        else:
            cont = float(np.prod([cf.p_trailing(a, d, lock=bool(rs["lock"])) for a in t]))
            form = "exp(-a/d)" + (" with lock at start balance" if rs["lock"] else "")
        rows.append(dict(rule_set=k, firm=rs["firm"], product=rs["product"],
                         targets="|".join(f"{a:g}" for a in t), max_loss=d, dd_type=rs["dd_type"],
                         zero_edge_ceiling_any_sizing=ceil, continuous_monitoring_value=cont, formula=form,
                         max_likelihood_ratio_of_a_pass=1 / ceil, fee_usd=rs["fee_usd"],
                         account_usd=rs["account_usd"], fee_pct_of_account=100 * rs["fee_usd"] / rs["account_usd"]))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T1_closed_form_benchmarks.csv", index=False)
    return df


def fig_validation():
    v = pd.read_csv(OUT / "validation.csv")
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.errorbar(v.exact, v.mc, yerr=3 * v.se, fmt="o", ms=4, capsize=2)
    ax.plot([0, 1], [0, 1], "k--", lw=0.8)
    ax.set_xlabel("closed-form probability")
    ax.set_ylabel("Monte Carlo estimate (bars = 3 standard errors)")
    ax.set_title(f"Simulator against closed forms ({len(v)} tests)")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_validation.png")
    plt.close(fig)


def fig_zero_edge(a, t1):
    sub = a[(a.dist == "bernoulli_1to1") & (a.trades_per_day == 3)]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), sharey=True)
    for ax, pol in zip(axes, ("naive", "rule_aware")):
        for k in ORDER:
            g = sub[(sub.rule_set == k) & (sub.policy == pol) & (sub.p_unresolved < 0.02)].sort_values("risk")
            ax.plot(100 * g.risk, g.p_pass, marker="o", ms=3, label=LABEL[k])
        ax.set_xscale("log")
        ax.set_xticks([0.25, 0.5, 1, 2, 3, 5])
        ax.set_xticklabels(["0.25", "0.5", "1", "2", "3", "5"])
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel("risk per trade (% of account), 3 trades per day, 1:1 stop/target trades")
        ax.set_title(f"zero edge, {pol.replace('_', '-')} sizing")
    axes[0].set_ylabel("pass probability")
    h, l = axes[1].get_legend_handles_labels()
    fig.suptitle("Zero-skill pass probability by rule set (cells with >2% unresolved paths omitted)")
    fig.tight_layout(rect=(0, 0, 0.78, 1))
    fig.legend(h, l, fontsize=7, loc="center right")
    fig.savefig(OUT / "fig2_zero_edge_by_risk.png")
    plt.close(fig)

    # T2: one line per rule set: range across the whole grid and the headline cell
    rows = []
    for k in ORDER:
        g = a[(a.rule_set == k) & (a.p_unresolved < 0.02)]
        h = g[(g.dist == "bernoulli_1to1") & (g.trades_per_day == 3) & (g.risk == 0.01)].set_index("policy")
        rows.append(dict(rule_set=k, ceiling=float(t1.set_index("rule_set").loc[k, "zero_edge_ceiling_any_sizing"]),
                         continuous_value=float(t1.set_index("rule_set").loc[k, "continuous_monitoring_value"]),
                         headline_naive_1pct_3trades=h.loc["naive", "p_pass"] if "naive" in h.index else np.nan,
                         headline_rule_aware_1pct_3trades=h.loc["rule_aware", "p_pass"] if "rule_aware" in h.index else np.nan,
                         min_naive=g[g.policy == "naive"].p_pass.min(), max_naive=g[g.policy == "naive"].p_pass.max(),
                         min_rule_aware=g[g.policy == "rule_aware"].p_pass.min(),
                         max_rule_aware=g[g.policy == "rule_aware"].p_pass.max(),
                         median_all_cells=g.p_pass.median(), n_cells=len(g)))
    pd.DataFrame(rows).to_csv(OUT / "T2_zero_edge_summary.csv", index=False)

    # T2b: effect of the return model at the headline cell
    piv = a[(a.trades_per_day == 3) & (a.risk == 0.01)].pivot_table(index=["rule_set", "policy"], columns="dist",
                                                                    values="p_pass")
    piv.to_csv(OUT / "T2b_zero_edge_by_return_model.csv")


def fig_heatmaps(a):
    fig, axes = plt.subplots(2, 4, figsize=(13, 5.6))
    for row, pol in enumerate(("naive", "rule_aware")):
        for col, k in enumerate(("FTMO_2S", "FTMO_1S", "TOPSTEP_50K", "E8_ONE")):
            g = a[(a.rule_set == k) & (a.policy == pol) & (a.dist == "gauss")]
            p = g.pivot_table(index="trades_per_day", columns="risk", values="p_pass")
            u = g.pivot_table(index="trades_per_day", columns="risk", values="p_unresolved")
            ax = axes[row, col]
            im = ax.imshow(p.values, vmin=0, vmax=0.5, cmap="viridis", aspect="auto")
            ax.set_xticks(range(p.shape[1]))
            ax.set_xticklabels([f"{100 * x:g}" for x in p.columns])
            ax.set_yticks(range(p.shape[0]))
            ax.set_yticklabels(p.index)
            ax.grid(False)
            for i in range(p.shape[0]):
                for j in range(p.shape[1]):
                    txt = f"{p.values[i, j]:.2f}" + ("*" if u.values[i, j] > 0.02 else "")
                    ax.text(j, i, txt, ha="center", va="center", color="w", fontsize=7)
            ax.set_title(f"{k} ({pol})", fontsize=8)
            if row == 1:
                ax.set_xlabel("per-trade s.d. (% of account)")
            if col == 0:
                ax.set_ylabel("trades per day")
    fig.suptitle("Zero-edge pass probability, Gaussian trades (* = more than 2% of paths unresolved after 750 days per phase)")
    fig.tight_layout()
    fig.savefig(OUT / "fig3_heatmaps.png")
    plt.close(fig)


def fig_economics(b):
    sub = b[(b.dist == "bernoulli_1to1") & (b.trades_per_day == 3) & (b.funded_horizon_days == 60)]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), sharey=True)
    for ax, cost in zip(axes, (0.0, 0.05)):
        for k in ORDER:
            g = sub[(sub.rule_set == k) & (sub.cost_per_trade_R == cost) & (sub.p_unresolved < 0.02)].sort_values("risk")
            ax.plot(100 * g.risk, 100 * g.ev_per_attempt_usd / g.fee_usd, marker="o", ms=3, label=LABEL[k])
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xscale("log")
        ax.set_xticks([0.25, 0.5, 1, 2, 3, 5])
        ax.set_xticklabels(["0.25", "0.5", "1", "2", "3", "5"])
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel("risk per trade (% of account)")
        ax.set_title(f"cost per trade = {cost:g} R")
    axes[0].set_ylabel("expected value per attempt, % of fee")
    h, l = axes[1].get_legend_handles_labels()
    fig.suptitle("Zero-edge expected value per challenge bought (rule-aware sizing, 60-day funded horizon, no payout denial)")
    fig.tight_layout(rect=(0, 0, 0.78, 1))
    fig.legend(h, l, fontsize=7, loc="center right")
    fig.savefig(OUT / "fig4_expected_value.png")
    plt.close(fig)

    h = sub[(sub.risk == 0.01)].copy()
    cols = ["rule_set", "cost_per_trade_R", "fee_usd", "account_usd", "p_pass", "exp_attempts_to_pass",
            "exp_fees_to_first_funded_usd", "funded_p_any_payout", "p_paid_per_attempt", "exp_payout_given_pass_usd",
            "ev_per_attempt_usd"]
    h[cols].sort_values(["cost_per_trade_R", "rule_set"]).to_csv(OUT / "T3_economics_headline.csv", index=False)
    # best and worst zero-cost sizing per rule set
    z = b[(b.cost_per_trade_R == 0.0) & (b.funded_horizon_days == 60) & (b.p_unresolved < 0.02)]
    idx = z.groupby("rule_set").ev_per_attempt_usd.idxmax()
    z.loc[idx, ["rule_set", "dist", "risk", "trades_per_day", "p_pass", "funded_p_any_payout",
                "ev_per_attempt_usd", "fee_usd"]].to_csv(OUT / "T3b_best_zero_edge_sizing.csv", index=False)
    hz = b[(b.dist == "bernoulli_1to1") & (b.trades_per_day == 3) & (b.cost_per_trade_R == 0.0) & (b.risk == 0.01)]
    hz.pivot_table(index="rule_set", columns="funded_horizon_days", values="ev_per_attempt_usd").to_csv(
        OUT / "T3c_ev_by_funded_horizon.csv")


def fig_edge(c):
    sub = c[(c.dist == "bernoulli_1to1") & (c.risk == 0.01)]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for k in ORDER:
        g = sub[(sub.rule_set == k) & (sub.p_unresolved < 0.02)].sort_values("edge")
        ax.plot(g.edge, g.p_pass, marker="o", ms=3, label=LABEL[k])
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("edge per trade (expected profit in units of risk R); 0 = zero skill")
    ax.set_ylabel("pass probability")
    ax.set_title("Pass probability against edge (1% risk, 3 trades/day, rule-aware)")
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_edge_sensitivity.png")
    plt.close(fig)
    sub.pivot_table(index="rule_set", columns="edge", values="p_pass").to_csv(OUT / "T4_pass_by_edge_1pct.csv")


def fig_roc(d):
    g = d[(d.edge_skilled == 0.10) & (d.risk == 0.01)]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    cmap = plt.get_cmap("tab10")
    for ax, q0 in zip(axes, (0.0, -0.05)):
        s = g[g.edge_unskilled == q0].set_index("rule_set")
        ax.plot([0, 1], [0, 1], "k--", lw=0.8)
        for i, k in enumerate(ORDER):
            if k not in s.index:
                continue
            r = s.loc[k]
            ax.plot(r.fpr, r.tpr, "o", ms=6, color=cmap(i), label=LABEL[k])
            ax.plot(r.fpr, r.tpr_neyman_pearson_same_fpr, "^", ms=5, color=cmap(i), mfc="none")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.set_xlabel("P(pass | unskilled)  = false-positive rate")
        ax.set_ylabel("P(pass | skilled)  = true-positive rate")
        ax.set_title(f"skilled edge +0.10 R vs unskilled {q0:+.2f} R")
    h, l = axes[0].get_legend_handles_labels()
    fig.suptitle("The challenge as a diagnostic test (filled circles). Open triangles: best fixed-sample test with the "
                 "same average number of trades and the same false-positive rate. Dashed: no information.", fontsize=8)
    fig.tight_layout(rect=(0, 0, 0.78, 0.97))
    fig.legend(h, l, fontsize=7, loc="center right")
    fig.savefig(OUT / "fig6_roc_view.png")
    plt.close(fig)
    cols = ["rule_set", "risk", "edge_skilled", "edge_unskilled", "tpr", "fpr", "lr_plus", "lr_minus",
            "lr_plus_ceiling_zero_edge", "ppv_prior_0.05", "ppv_prior_0.10", "ppv_prior_0.20", "mean_trades",
            "tpr_neyman_pearson_same_fpr"]
    d[(d.risk == 0.01)][cols].to_csv(OUT / "T5_skill_test_1pct.csv", index=False)


def fig_time_limit(e):
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    xs = np.linspace(0.002, 0.05, 120)
    for T, c in ((30, "C0"), (60, "C1")):
        ax.plot(100 * xs, [cf.p_static_deadline(0.10, 0.10, T, 0.0, s) for s in xs], c, label=f"closed form, {T}-day limit")
        g = e[e.deadline_days == T]
        ax.errorbar(100 * g.daily_vol, g.mc, yerr=3 * g.se, fmt="o", color=c, ms=3, capsize=2)
    ax.axhline(0.5, color="k", ls="--", lw=0.8, label="no time limit: b/(a+b) = 0.5")
    ax.set_xlabel("daily volatility of account P&L (%)")
    ax.set_ylabel("zero-edge pass probability")
    ax.set_title("One 10% target / 10% loss phase with a time limit")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig7_time_limit.png")
    plt.close(fig)


def main():
    t1 = closed_form_benchmarks()
    fig_validation()
    a = pd.read_csv(OUT / "A_zero_edge_grid.csv")
    fig_zero_edge(a, t1)
    fig_heatmaps(a)
    fig_economics(pd.read_csv(OUT / "B_economics.csv"))
    fig_edge(pd.read_csv(OUT / "C_edge_sensitivity.csv"))
    fig_roc(pd.read_csv(OUT / "D_skill_test.csv"))
    fig_time_limit(pd.read_csv(OUT / "E_time_limit.csv"))
    print("figures and tables written to", OUT)


if __name__ == "__main__":
    main()
