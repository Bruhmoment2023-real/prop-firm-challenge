import glob, pandas as pd, numpy as np, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]; RES = ROOT / "results"
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RES / "grid" / "E1_*.csv")))], ignore_index=True)
ceil = pd.read_csv(RES / "T_dataset_ceilings.csv").set_index("pid")
d["ceiling"] = d.pid.map(ceil.ceiling)
d.to_csv(RES / "E1_all_cells.csv.gz", index=False)
z = d[(d.sigma_a == 0.01) & (d.h == 0.5) & (d.m == 1.0)]
out = []
# S1: zero-skill pass by rule set, across the 25 asset x process banks
s1 = z.groupby("pid").p_pass.agg(["min", "median", "max"]).join(ceil[["ceiling"]]); s1.to_csv(RES / "S1_zero_skill_by_rule.csv")
# S2: by process (mean over rule sets) and by asset
s2 = z.pivot_table(index="asset", columns="process", values="p_pass", aggfunc="mean"); s2.to_csv(RES / "S2_zero_skill_by_asset_process.csv")
# S3: process effect relative to P0 per rule set (mean over assets)
t = z.pivot_table(index=["pid", "asset"], columns="process", values="p_pass")
for p in ["P1", "P2", "P3", "P4"]: t[p + "-P0"] = t[p] - t["P0"]
s3 = t.groupby("pid")[[c for c in t.columns if c.endswith("-P0")]].mean(); s3.to_csv(RES / "S3_process_effect_vs_P0.csv")
# S4 H1: static rule sets, zero skill, deviation from ceiling
stat = ceil[ceil.dd == "static"].index.tolist()
h1 = d[d.pid.isin(stat) & (d.h == 0.5) & (d.unresolved <= 0.02)].copy(); h1["dev_pts"] = 100 * (h1.p_pass - h1.ceiling)
s4 = h1.groupby(["sigma_a", "m"]).dev_pts.agg(["count", "mean", "min", "max"]); s4.to_csv(RES / "S4_H1_static_vs_ceiling.csv")
# S5 unresolved flags
s5 = d.groupby("sigma_a").apply(lambda g: pd.Series(dict(cells=len(g), flagged=(g.unresolved > 0.02).sum())))
s5.to_csv(RES / "S5_unresolved_flags.csv")
# S6 failure attribution at headline-style cell (ES, P2)
s6 = z[(z.asset == "ES")].groupby(["process", "pid"])[["p_pass", "f_maxloss", "f_daily", "f_time", "unresolved"]].mean()
s6.to_csv(RES / "S6_failure_attribution_ES.csv")
print(s1.round(3).to_string()); print(s2.round(3).to_string()); print(s3.round(3).to_string()); print(s4.round(2).to_string()); print(s5)
