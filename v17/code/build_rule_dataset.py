"""Build the dated rule dataset (long provenance table + wide model table) from the pages archived on 2026-11-17 (and, where a page
could not be re-read, the 2026-10-13 archive, flagged as such). Every value was typed in by reading the archived page text named
in the row; nothing is scraped by pattern. Also looks up Wayback snapshots via the public availability API (read-only).
"""
import csv, json, pathlib, time, urllib.request, urllib.parse, datetime
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
D17 = "data/raw/firm_pages_2026-11-17/"
D13 = "../data/raw/firm_pages/"          # relative to rework-v3 (2026-10-13 archive)
EUR = 1.0993    # EURUSD close 2026-11-17 (Yahoo), used only to convert EUR list prices
ACC = "2026-11-17"

# model fields: targets, max_loss, dd_type, lock, daily_loss, daily_mode, min_days, min_profit_days, profit_day_thr, consistency,
# time_limit (trading days per phase, 0 none), split, fee_usd, activation_usd, refund (1 = fee refunded with first payout)
P = []


def prod(pid, firm, name, tier, url, date, files, model, rows, status="re-read 2026-11-17", assumed=""):
    P.append(dict(pid=pid, firm=firm, product=name, tier=tier, url=url, date=date, files=files, model=model, rows=rows, status=status, assumed=assumed))


prod("FTMO_2S", "FTMO", "2-Step Challenge", 100000, "https://ftmo.com/en/trading-objectives/ ; https://ftmo.com/en/", ACC, "ftmo_objectives.txt; ftmo_home.txt",
     dict(targets=[0.10, 0.05], max_loss=0.10, dd_type="static", lock=0, daily_loss=0.05, daily_mode="breach", min_days=4, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.90, fee_usd=round(540 * EUR, 2), activation_usd=0, refund=1),
     [("fee", "EUR 540 list (EUR 439 shown as offer)", "ftmo_home.txt"), ("profit_target", "Phase 1 10%, Phase 2 5%", "ftmo_objectives.txt"),
      ("max_daily_loss", "5% of Initial Simulated Capital, from balance at 00:00 CE(S)T, equity-based", "ftmo_objectives.txt"),
      ("max_loss", "10%, static", "ftmo_objectives.txt"), ("min_trading_days", "4", "ftmo_objectives.txt"),
      ("time_limit", "Unlimited", "ftmo_home.txt"), ("refund", "Yes 100%", "ftmo_home.txt"), ("split", "Rewards up to 90%", "ftmo_home.txt")],
     assumed="split 0.90 = published maximum")
prod("FTMO_1S", "FTMO", "1-Step Challenge", 100000, "https://ftmo.com/en/trading-objectives/", ACC, "ftmo_objectives.txt",
     dict(targets=[0.10], max_loss=0.10, dd_type="trail_eod", lock=0, daily_loss=0.03, daily_mode="breach", min_days=0, min_profit_days=0,
          profit_day_thr=0, consistency=0.50, time_limit=0, split=0.90, fee_usd=558.88, activation_usd=0, refund=0),
     [("profit_target", "10%", "ftmo_objectives.txt"), ("max_daily_loss", "3%", "ftmo_objectives.txt"),
      ("max_loss", "10% end-of-day trailing (highest 00:00 balance minus 10%), never decreases", "ftmo_objectives.txt"),
      ("consistency", "Best Day not more than 50% of total profit (orders on or after 12 Oct 2026; legacy: 50% of positive days' profit)", "ftmo_objectives.txt"),
      ("fee", "NOT STATED on the 2026-11-17 pages read; USD 558.88 from the 2026-10-13 archive (EUR 499 x 1.12)", "../firm_pages/ftmo_home.txt")],
     assumed="fee from 13 Oct; no refund assumed; split published max")
prod("FN_ST2", "FundedNext", "Stellar 2-Step", 100000, "https://fundednext.com/stellar-model", ACC, "fundednext_stellar_100k.txt",
     dict(targets=[0.08, 0.05], max_loss=0.10, dd_type="static", lock=0, daily_loss=0.05, daily_mode="breach", min_days=5, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.80, fee_usd=549.99, activation_usd=0, refund=1),
     [("fee", "$549.99 (100K tab)", "fundednext_stellar_100k.txt"), ("profit_target", "Phase 1 8%, Phase 2 5%", "fundednext_stellar_100k.txt"),
      ("max_daily_loss", "5%", "fundednext_stellar_100k.txt"), ("max_loss", "10%, Drawdown Type Static", "fundednext_stellar_100k.txt"),
      ("min_trading_days", "5 Days", "fundednext_stellar_100k.txt"), ("split", "Reward Share 80%", "fundednext_stellar_100k.txt"),
      ("refund", "Refundable Fee: With 1st Reward", "fundednext_stellar_100k.txt"), ("reset", "Reset Applicable: Yes", "fundednext_stellar_100k.txt")])
prod("FN_ST1", "FundedNext", "Stellar 1-Step", 6000, "https://fundednext.com/cfds/stellar-1-step", ACC, "fundednext_1step.txt",
     dict(targets=[0.10], max_loss=0.06, dd_type="static", lock=0, daily_loss=0.03, daily_mode="breach", min_days=2, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.80, fee_usd=float("nan"), activation_usd=0, refund=0),
     [("profit_target", "10%", "fundednext_1step.txt"), ("max_daily_loss", "3%", "fundednext_1step.txt"), ("max_loss", "6%, Static", "fundednext_1step.txt"),
      ("min_trading_days", "2", "fundednext_1step.txt"), ("time_limit", "None", "fundednext_1step.txt"),
      ("fee", "NOT STATED for the 100K tier (page shows entry price 'from $44.99' for the smallest tier)", "fundednext_1step.txt"),
      ("refund", "Challenge fee refunded at 3rd reward", "fundednext_1step.txt")],
     assumed="fee unknown at 100K -> economics excluded; refund at 3rd reward not modelled")
prod("T5_HS", "The5ers", "High Stakes", 100000, "https://the5ers.com/high-stakes/", ACC, "the5ers_highstakes_100k.txt",
     dict(targets=[0.10, 0.05], max_loss=0.08, dd_type="static", lock=0, daily_loss=0.04, daily_mode="breach", min_days=0, min_profit_days=3,
          profit_day_thr=0.005, consistency=0, time_limit=0, split=0.80, fee_usd=405, activation_usd=0, refund=0),
     [("fee", "Cost $405 after clicking the 100K tab (smallest tier showed $19)", "the5ers_highstakes_100k.txt"),
      ("profit_target", "Step 1 10%, Step 2 5%", "the5ers_highstakes_100k.txt"), ("max_daily_loss", "4%", "the5ers_highstakes_100k.txt"),
      ("max_loss", "8%", "the5ers_highstakes_100k.txt"), ("min_profitable_days", "3 (a profitable day = at least 0.5% of initial balance)", "the5ers_highstakes_100k.txt"),
      ("time_limit", "Max Trading Period Unlimited", "the5ers_highstakes_100k.txt"), ("split", "Profit share 80%-100% (80/20 in the scaling table)", "the5ers_highstakes_100k.txt")],
     assumed="drawdown type NOT STATED (static assumed); refund of fee not clear from page (none assumed). Changed since 13 Oct (was 5% daily, 10% max)")
prod("E8_ONE", "E8 Markets", "E8 One", 100000, "https://e8markets.com/", ACC, "e8_home_100k.txt",
     dict(targets=[0.09], max_loss=0.06, dd_type="trail_intraday", lock=0, daily_loss=0.04, daily_mode="breach", min_days=1, min_profit_days=0,
          profit_day_thr=0, consistency=0.40, time_limit=0, split=0.80, fee_usd=488, activation_usd=0, refund=0),
     [("fee", "$488 list ($415 with code E8)", "e8_home_100k.txt"), ("profit_target", "$9,000 (9%)", "e8_home_100k.txt"),
      ("max_loss", "Dynamic Drawdown $6,000 (6% Max)", "e8_home_100k.txt"), ("max_daily_loss", "Daily drawdown $4,000", "e8_home_100k.txt"),
      ("consistency", "Consistency rule 40% is listed under PERFORMANCE RULES (funded stage), not under CHALLENGE RULES, and the same page says 'pass in as little as 1 day', which a 40% best-day rule would forbid; the help-centre article that defines it was collapsed and not readable. UNRESOLVED: applied in the evaluation in the main results (the more restrictive reading); sensitivity: not applied", "e8_home_100k.txt"), ("split", "Payout 80%", "e8_home_100k.txt"),
      ("activation", "No Activation Fee", "e8_home_100k.txt"), ("min_days", "Pass in as little as 1 Day", "e8_home_100k.txt")],
     assumed="'dynamic' drawdown assumed intraday-trailing without lock; consistency 40% applied in the evaluation as the restrictive reading (page lists it under performance rules only; sensitivity row without it)")
prod("BF_2S", "BrightFunded", "2-Step Bright", 100000, "https://brightfunded.com/cfds/2-step-bright", ACC, "brightfunded_2step.txt",
     dict(targets=[0.08, 0.05], max_loss=0.08, dd_type="static", lock=0, daily_loss=0.04, daily_mode="breach", min_days=0, min_profit_days=3,
          profit_day_thr=0.005, consistency=0, time_limit=0, split=0.90, fee_usd=round(477 * EUR, 2), activation_usd=0, refund=0),
     [("fee", "EUR 477 list at 100K (EUR 333.90 after -30% promotion)", "brightfunded_2step.txt"), ("profit_target", "Phase 1 8%, Phase 2 5%", "brightfunded_2step.txt"),
      ("max_daily_loss", "4%", "brightfunded_2step.txt"), ("max_loss", "8% (Static)", "brightfunded_2step.txt"),
      ("min_profitable_days", "Min. Trading Days 3 Days, 0.5%+ each", "brightfunded_2step.txt"), ("split", "Payout Ratio up to 90%", "brightfunded_2step.txt"),
      ("time_limit", "Unlimited Trading Period", "brightfunded_2step.txt")], assumed="split published max; fee refund add-on not modelled")
prod("BF_1S", "BrightFunded", "1-Step Daily", 100000, "https://brightfunded.com/cfds/1-step-daily", ACC, "brightfunded_1step.txt",
     dict(targets=[0.10], max_loss=0.06, dd_type="static", lock=0, daily_loss=0.03, daily_mode="breach", min_days=0, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.90, fee_usd=round(497 * EUR, 2), activation_usd=0, refund=0),
     [("fee", "EUR 497 list at 100K (EUR 347.90 after -30%)", "brightfunded_1step.txt"), ("profit_target", "10%", "brightfunded_1step.txt"),
      ("max_daily_loss", "3%", "brightfunded_1step.txt"), ("max_loss", "6%", "brightfunded_1step.txt"), ("min_trading_days", "No Minimum", "brightfunded_1step.txt"),
      ("split", "up to 90%, payouts daily", "brightfunded_1step.txt")], assumed="drawdown type NOT STATED (static assumed)")
prod("FP_CL", "FunderPro", "Classic 2-Phase", 100000, "https://funderpro.com/", ACC, "funderpro_home_100k.txt",
     dict(targets=[0.10, 0.05], max_loss=0.10, dd_type="static", lock=0, daily_loss=0.05, daily_mode="breach", min_days=4, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.80, fee_usd=539, activation_usd=0, refund=1),
     [("fee", "Price $539 (processed with 1st reward)", "funderpro_home_100k.txt"), ("profit_target", "$10k (10%), 5%", "funderpro_home_100k.txt"),
      ("max_daily_loss", "$5k (5%), balance based, from 5pm EST", "funderpro_home_100k.txt"), ("max_loss", "$10k (10%)", "funderpro_home_100k.txt"),
      ("min_trading_days", "4", "funderpro_home_100k.txt"), ("split", "80%", "funderpro_home_100k.txt"), ("time_limit", "Unlimited", "funderpro_home_100k.txt")],
     assumed="'Price (will be processed with 1st reward)' read as the fee being returned with the first reward")
prod("ALPHA_PRO", "Alpha Capital", "Alpha Pro 10%", 100000, "https://alphacapitalgroup.uk/product/alpha-pro", "2026-10-13", "../firm_pages/alpha_pro.txt",
     dict(targets=[0.10, 0.05], max_loss=0.10, dd_type="static", lock=0, daily_loss=0.05, daily_mode="breach", min_days=3, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.80, fee_usd=497, activation_usd=0, refund=0),
     [("all", "see data/firm_rules_sourced.csv rows for Alpha Capital (13 Oct); the 17 Nov page shows only a checkout configurator that was not rendered", "../firm_pages/alpha_pro.txt")],
     status="2026-10-13 only (17 Nov page configurator not readable)")
prod("ALPHA_ONE", "Alpha Capital", "Alpha One 10%", 100000, "https://alphacapitalgroup.uk/product/alpha-one", "2026-10-13", "../firm_pages/alpha_one.txt",
     dict(targets=[0.10], max_loss=0.06, dd_type="trail_intraday", lock=0, daily_loss=0.04, daily_mode="breach", min_days=1, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.80, fee_usd=477, activation_usd=0, refund=0),
     [("all", "see data/firm_rules_sourced.csv rows for Alpha Capital (13 Oct)", "../firm_pages/alpha_one.txt")],
     status="2026-10-13 only (17 Nov page configurator not readable)", assumed="trailing assumed intraday")
prod("TS_50K", "Topstep", "Trading Combine 50K", 50000, "https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit", ACC,
     "topstep_params.txt; topstep_mll.txt; topstep_consistency.txt; topstep_subs.txt",
     dict(targets=[0.06], max_loss=0.04, dd_type="trail_eod", lock=1, daily_loss=0.0, daily_mode="pause", min_days=0, min_profit_days=0,
          profit_day_thr=0, consistency=0.55, time_limit=0, split=0.90, fee_usd=49, activation_usd=149, refund=0),
     [("profit_target", "$3,000 on 50K", "topstep_consistency.txt"), ("max_loss", "MLL $2,000, trails end-of-day balance, locks at starting balance, breach checked intraday on unrealised P&L", "topstep_mll.txt"),
      ("consistency", "best single day at or below 55% of total profit, else target rises", "topstep_consistency.txt"),
      ("daily_loss", "Combine has one rule (MLL); a Daily Loss Limit is an optional add-on at checkout (payout-page note)", "topstep_params.txt; topstep_payout.txt"),
      ("time_limit", "No time limit for passing; monthly subscription rebills every 30 days", "topstep_subs.txt"),
      ("fee", "USD 49 per month (13 Oct archive; the 17 Nov article hides the amount in a collapsed FAQ); USD 149 activation", "../firm_pages/topstep_subs.txt"),
      ("split", "90/10", "topstep_payout.txt")],
     assumed="fee from 13 Oct; one monthly fee counted per attempt; funded stage simplified")
prod("TRD_50K", "Tradeify", "1-step Evaluation 50K", 50000, "https://tradeify.co/", ACC, "tradeify_home.txt",
     dict(targets=[0.07], max_loss=0.03, dd_type="static", lock=0, daily_loss=0.018, daily_mode="pause", min_days=0, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.80, fee_usd=376, activation_usd=0, refund=0),
     [("fee", "$376 list per evaluation ($263 with code NOV)", "tradeify_home.txt"), ("profit_target", "$3,500", "tradeify_home.txt"),
      ("max_loss", "Static Drawdown $1,500", "tradeify_home.txt"), ("daily_loss", "DLL type Soft, Daily Loss Limit $900", "tradeify_home.txt"),
      ("min_trading_days", "None", "tradeify_home.txt"), ("consistency", "None", "tradeify_home.txt"), ("split", "80% profit split + 10% to Live Funds", "tradeify_home.txt")],
     assumed="'Soft' DLL read as pause-for-the-day; the 50K card is read from the home page listing")
prod("BUL_50K", "Bulenox", "Qualification 50K (trailing option)", 50000, "https://bulenox.com/accounts-pricing", ACC, "bulenox_pricing.txt",
     dict(targets=[0.06], max_loss=0.05, dd_type="trail_intraday", lock=0, daily_loss=0.0, daily_mode="pause", min_days=0, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=21, split=0.90, fee_usd=175, activation_usd=0, refund=0),
     [("fee", "$175 one-time, access valid for 30 days", "bulenox_pricing.txt"), ("time_limit", "AMBIGUOUS: FAQ answer 'As long as you need. There is no minimum and no maximum number of trading days'; but the FAQ also says qualification accounts have no recurring payment and 'access simply expires at the end of the subscription cycle', and the pricing page says 'Access valid for 30 days'. Main results: 21-trading-day limit; sensitivity: no limit", "bulenox_faq.html"), ("profit_target", "$3,000", "bulenox_pricing.txt"),
      ("max_loss", "Drawdown up to $2,500; option 1 trailing follows highest point including open positions", "bulenox_pricing.txt"),
      ("daily_loss", "No daily loss limit (option 1)", "bulenox_pricing.txt"), ("min_trading_days", "None", "bulenox_pricing.txt"), ("split", "up to 90% (home page)", "bulenox_home.txt")],
     assumed="UNRESOLVED: 30 calendar days of access modelled as a 21-trading-day deadline in the main results; no-deadline version is the sensitivity row (Table S11); split published max")
prod("MF_RAPID", "My Funded Futures", "Rapid 50K", 50000, "https://myfundedfutures.com/plans/rapid", ACC, "mffu_rapid.txt",
     dict(targets=[0.06], max_loss=0.04, dd_type="trail_intraday", lock=1, daily_loss=0.0, daily_mode="pause", min_days=2, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.90, fee_usd=209, activation_usd=0, refund=0),
     [("fee", "$209 (50K), 'starting at $125' promotion shown for the smallest tier", "mffu_rapid.txt"), ("profit_target", "$3,000 for 50K", "mffu_rapid.txt"),
      ("max_loss", "$2,000 intraday trailing, stops trailing once balance is start+$100", "mffu_rapid.txt"), ("daily_loss", "None", "mffu_rapid.txt"),
      ("min_trading_days", "min 2 days", "mffu_rapid.txt"), ("split", "90/10", "mffu_rapid.txt"), ("activation", "$0", "mffu_rapid.txt")],
     assumed="lock at start balance approximates the +$100 buffer lock")
prod("MF_BUILD", "My Funded Futures", "Builder 50K", 50000, "https://myfundedfutures.com/plans/builder", ACC, "mffu_builder.txt",
     dict(targets=[0.06], max_loss=0.04, dd_type="trail_eod", lock=0, daily_loss=0.02, daily_mode="pause", min_days=1, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.80, fee_usd=153, activation_usd=0, refund=0),
     [("fee", "$153 beside the button 'Start builder Evaluation at $50K'; the first figure '$92 (STARTING AT, based on current promotions)' stands to $153 as $125 to $209 (Rapid) and $165 to $275 (Rapid EOD), a constant 0.60 ratio, so $92 is the promotion and $153 the list price. Largely settled; $92 kept as sensitivity", "mffu_builder.txt"), ("profit_target", "$3,000", "mffu_builder.txt"),
      ("max_loss", "EOD trailing, $2,000 drawdown (home page lists 1.5k or 2k)", "mffu_builder.txt"), ("daily_loss", "$1K soft pause (account survives)", "mffu_builder.txt"),
      ("min_trading_days", "1-day minimum (another line says min 2 days)", "mffu_builder.txt"), ("split", "80/20", "mffu_builder.txt")],
     assumed="list/promotion reading inferred from a constant 0.60 price ratio across three plans; consistency not applied in the evaluation")
prod("ETF_LT50", "Elite Trader Funding", "50K Live Trailing Eval", 50000, "https://elitetraderfunding.com/evaluations", ACC, "elitetf_evals.txt",
     dict(targets=[0.06], max_loss=0.04, dd_type="trail_intraday", lock=0, daily_loss=0.0, daily_mode="pause", min_days=5, min_profit_days=0,
          profit_day_thr=0, consistency=0, time_limit=0, split=0.90, fee_usd=207, activation_usd=177, refund=0),
     [("fee", "$207 per 30 days: the page's own price table (17 Nov) lists '50K Live Trailing Eval $207, billing every 30 days, activation $87 monthly or $177 once, reset $47' as list price; the $20.70 shown on the card is a promotion (the page says list prices are shown in the table and promotions apply at checkout). SETTLED: $207 list; $20.70 kept as sensitivity", "elitetf_evals.txt"),
      ("profit_target", "$3,000", "elitetf_evals.txt"), ("max_loss", "$2,000, Live Trailing on open and realised profit", "elitetf_evals.txt"),
      ("daily_loss", "None", "elitetf_evals.txt"), ("min_trading_days", "5", "elitetf_evals.txt"), ("reset", "$47 reset fee", "elitetf_evals.txt"),
      ("activation", "$177 one-time or $87 monthly", "elitetf_evals.txt")],
     assumed="split not stated on the page read (0.90 assumed, typical); 30-day billing counted as one fee per attempt (a longer attempt would renew); $20.70 promotion = sensitivity")


def wayback(url):
    u = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url.split(" ; ")[0])
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "academic-research-script/1.0"})
        with urllib.request.urlopen(req, timeout=40) as r:
            j = json.load(r)
        s = j.get("archived_snapshots", {}).get("closest")
        return (s["url"], s["timestamp"]) if s else ("none found", "")
    except Exception as e:
        return ("lookup failed: " + str(e)[:50], "")


def main():
    out = ROOT / "data"
    long_rows, wide = [], []
    wb = {}
    for p in P:
        url0 = p["url"].split(" ; ")[0]
        if url0 not in wb:
            wb[url0] = wayback(url0); time.sleep(1.5)
        for f, val, src in p["rows"]:
            long_rows.append(dict(pid=p["pid"], firm=p["firm"], product=p["product"], tier_usd=p["tier"], field=f, value_as_published=val,
                                  url=p["url"], access_date=p["date"], archived_file=src, wayback_url=wb[url0][0], wayback_timestamp=wb[url0][1]))
        m = dict(p["model"])
        m["targets"] = "|".join(str(x) for x in m["targets"])
        wide.append(dict(pid=p["pid"], firm=p["firm"], product=p["product"], tier_usd=p["tier"], read_status=p["status"], **m,
                         fee_pct_of_account=(m["fee_usd"] / p["tier"] if m["fee_usd"] == m["fee_usd"] else float("nan")),
                         assumed_fields=p["assumed"], sources=p["files"], source_url=p["url"], access_date=p["date"]))
    pd.DataFrame(long_rows).to_csv(out / "rule_dataset_v3_long.csv", index=False)
    pd.DataFrame(wide).to_csv(out / "rule_sets_v3_model.csv", index=False)
    print(len(P), "products,", len(long_rows), "rows")


if __name__ == "__main__":
    main()
