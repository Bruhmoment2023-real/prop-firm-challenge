import pickle, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import calibrate as cal
ROOT = HERE.parent
def get_pars(asset):
    f = ROOT / "results" / f"_pars_{asset}.pkl"
    if f.exists(): return pickle.load(open(f, "rb"))
    d = cal.load(asset); m = cal.log_ohlc(d, asset == "EURUSD"); P = cal.fit_all(m)
    pars = dict(sd=P["sd"], df=P["df"], garch=P["garch"], std_resid=P["std_resid"], triples=P["triples"])
    pickle.dump(pars, open(f, "wb")); return pars
