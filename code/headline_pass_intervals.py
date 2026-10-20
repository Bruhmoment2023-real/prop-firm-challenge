"""95% Wilson score intervals for the zero-edge pass probability at the headline cell of each rule set.

Headline cell: fixed 1:1 trades, 1% risk, 3 trades a day, rule-aware sizing. Reads results/A_zero_edge_grid.csv
from the research pack (read only); every cell there used 20,000 paths.

Usage: python -I headline_pass_intervals.py <pack_dir> <out_csv>
"""
import csv
import math
import pathlib
import sys

PACK, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
if OUT.exists():
    sys.exit(f"{OUT} exists; refusing to overwrite")
N, Z = 20_000, 1.959964


def wilson(p, n, z=Z):
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


rows = []
for r in csv.DictReader(open(PACK / "results" / "A_zero_edge_grid.csv", newline="")):
    if (r["dist"], r["risk"], r["trades_per_day"], r["policy"]) == ("bernoulli_1to1", "0.01", "3", "rule_aware"):
        p = float(r["p_pass"])
        lo, hi = wilson(p, N)
        rows.append(dict(rule_set=r["rule_set"], p_pass=p, passes=round(p * N), n_paths=N, wilson_lo=lo, wilson_hi=hi))
        print(f"{r['rule_set']:13s} {100*p:5.1f}%  ({100*lo:.1f}% to {100*hi:.1f}%)")
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
