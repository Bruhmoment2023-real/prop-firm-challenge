#!/bin/bash
cd /d/Research-Publishing/01-prop-firm-challenge/rework-v3
PY=/c/Users/seans/AppData/Local/Programs/Python/Python313/python.exe
until grep -q "BTC P4" logs/grid.log; do sleep 20; done
export NUMBA_NUM_THREADS=3 PYTHONUNBUFFERED=1
$PY -u code/run_grid.py headline > logs/headline.log 2>&1
$PY -u code/rule_drivers.py a > logs/e3a.log 2>&1
$PY -u code/rule_drivers.py b > logs/e3b.log 2>&1
$PY -u code/rule_drivers.py analyse > logs/e3b_analyse.log 2>&1
$PY -u code/economics.py > logs/econ.log 2>&1
echo CHAIN DONE > logs/chain.done
