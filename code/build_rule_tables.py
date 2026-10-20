"""Write the three data tables used by the study.

data/firm_rules_sourced.csv    one row per published number, with URL, access date and the archived file it was read from
data/rule_sets_model.csv       one row per product: the parameters the simulator uses, incl. flagged assumptions
data/published_statistics.csv  pass-rate / payout statistics published by firms, with URL and access date

Every value below was read on 2026-10-13 from the firm's own public page (archived under data/raw/firm_pages/).
"NOT STATED" means the page did not say; nothing has been filled in from memory or third-party sites.

Usage:  python code/build_rule_tables.py
"""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
D = "2026-10-13"
U = dict(
    ftmo_home="https://ftmo.com/en/", ftmo_obj="https://ftmo.com/en/trading-objectives/",
    fn="https://fundednext.com/stellar-model", f5="https://the5ers.com/high-stakes/",
    ts_home="https://www.topstep.com/",
    ts_mll="https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit",
    ts_price="https://help.topstep.com/en/articles/14289835-topstep-pricing-and-payment-questions",
    ts_cons="https://help.topstep.com/en/articles/8284208-what-is-the-consistency-target",
    ts_par="https://help.topstep.com/en/articles/8284197-trading-combine-parameters",
    ts_dll="https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account",
    ts_xfa="https://help.topstep.com/en/articles/8284215-express-funded-account-parameters",
    ts_pay="https://help.topstep.com/en/articles/8284233-topstep-payout-policy",
    ts_subs="https://help.topstep.com/en/articles/8284121-trading-combine-subscriptions",
    e8="https://e8markets.com/", a_pro="https://alphacapitalgroup.uk/product/alpha-pro",
    a_one="https://alphacapitalgroup.uk/product/alpha-one",
    a_px="https://alphacapitalgroup.uk/resources/alpha-capital-2026-plan-pricing-update",
    fp="https://funderpro.com/", bf="https://brightfunded.com/", tpt="https://takeprofittrader.com/",
)
A = dict(ftmo_home="ftmo_home", ftmo_obj="ftmo_objectives", fn="fundednext_stellar", f5="the5ers_highstakes",
         ts_home="topstep_home", ts_mll="topstep_mll", ts_price="topstep_pricing", ts_cons="topstep_consistency",
         ts_par="topstep_params", ts_dll="topstep_dll", ts_xfa="topstep_xfa", ts_pay="topstep_payout",
         ts_subs="topstep_subs", e8="e8_home", a_pro="alpha_pro", a_one="alpha_one", a_px="alpha_pricing_update",
         fp="funderpro_home", bf="brightfunded_home", tpt="tpt_home")

R = []


def add(firm, product, account, src, **fields):
    """Append one row per field. A tuple value is (value, note)."""
    for k, v in fields.items():
        note = ""
        if isinstance(v, tuple):
            v, note = v
        R.append([firm, product, account, k, v, U[src], D, A[src] + ".html", note])


add("FTMO", "2-Step Challenge", "USD 100,000", "ftmo_home",
    fee=("EUR 540", "list price; a EUR 439 first-account deal was also shown"),
    profit_target_phase1="10%", profit_target_phase2="5%", max_daily_loss="5% of initial balance",
    max_loss="10% of initial balance", min_trading_days="4 per phase", time_limit="Unlimited",
    fee_refund="100%, with the first Reward",
    profit_split=("80%, up to 90% with Scaling Plan", "base 80% modelled"),
    published_average_reward=("USD 5,957", "field average_reward in the page pricing data; definition not given"))
add("FTMO", "2-Step Challenge", "USD 100,000", "ftmo_obj", max_loss_type="static",
    daily_loss_basis="balance at 00:00 CE(S)T minus 5% of initial; equity monitored",
    payout_frequency=("NOT STATED on the pages read", "10 trading days assumed in the model"))
add("FTMO", "1-Step Challenge", "USD 100,000", "ftmo_home",
    fee=("EUR 499", "list price; EUR 399 deal also shown"),
    profit_target_phase1="10%", max_daily_loss="3% of initial balance", max_loss="10% of initial balance",
    time_limit="Unlimited", consistency_best_day="50% of total profit", profit_split="90%",
    fee_refund=("NOT STATED for 1-Step", "modelled as no refund"))
add("FTMO", "1-Step Challenge", "USD 100,000", "ftmo_obj",
    max_loss_type="end-of-day trailing: highest balance at 00:00 of any preceding day (or initial) minus 10%",
    rule_change_note=("Consistency rule differs for orders on/after 12 Oct 2026 versus Legacy accounts",
                      "the rules changed the day before access"))
add("FundedNext", "Stellar 2-Step", "USD 100,000", "fn", fee="USD 549.99", profit_target_phase1="8%",
    profit_target_phase2="5%", max_daily_loss="5%", max_loss="10%", max_loss_type="Static",
    min_trading_days="5", time_limit="No time limit",
    profit_split=("80% (headline says up to 95%)", "80% modelled"),
    fee_refund="Refundable with the first reward",
    payout_frequency="first after 21 days, then every 14 days",
    daily_loss_basis=("NOT STATED on the page read", "start-of-day balance assumed"))
add("The5ers", "High Stakes (2-step)", "USD 2,500", "f5",
    fee=("USD 19", "only the $2.5K price was in the static page; the $100K price was NOT RETRIEVED"),
    profit_target_phase1="10%", profit_target_phase2="5%", max_daily_loss="5%", max_loss="10%",
    max_loss_type=("NOT STATED on the page read", "static assumed"), time_limit="Unlimited",
    min_profitable_days="3 per step (profitable day = at least 0.5% of initial balance)",
    profit_split="80%-100% by scaling level",
    fee_refund=("Refund listed; conditions not stated", "refund with first payout assumed"),
    payout_frequency=("NOT STATED on the page read", "10 trading days assumed"))
TS = ("Topstep", "Trading Combine 50K (Standard path)", "USD 50,000")
add(*TS, "ts_price", fee="USD 49 per month", activation_fee="USD 149 once per Express Funded Account",
    fee_no_activation_path="USD 95 per month", back2funded_reactivation="USD 599 (50K)")
add(*TS, "ts_cons", profit_target="USD 3,000",
    consistency_best_day=("best day below 55% of profit target, else the target rises to best day / 0.55",
                          "example on page: best day $2,200 gives target $4,000"))
add(*TS, "ts_mll", max_loss="USD 2,000",
    max_loss_type="trailing on end-of-day balance; locks at the starting balance; monitored in real time on unrealized P&L",
    funded_max_loss="XFA balance starts at $0, MLL -$2,000 trailing, locks at $0; MLL set to $0 after first payout")
add(*TS, "ts_dll",
    max_daily_loss=("USD 1,000, optional; a hit pauses trading until the next session",
                    "not an account breach; modelled as off in the baseline"))
add(*TS, "ts_par", min_trading_days="can pass in as few as two days")
add(*TS, "ts_subs", time_limit="No time limit (monthly rebill until pass or cancel)")
add(*TS, "ts_xfa", profit_split="90/10",
    payout_conditions="5 winning days of $150+; request 50% of balance up to $5,000 (or 3 days traded with 40% consistency, up to $6,000)")
add("E8 Markets", "E8 One", "USD 100,000", "e8",
    fee=("USD 488", "list price; USD 342 with a 30%-off code shown"),
    profit_target_phase1="USD 9,000",
    max_loss=("USD 6,000 Dynamic Drawdown (Drawdown 6% Max)",
              "trailing mechanics NOT STATED on the page read; intraday trailing without lock assumed"),
    max_daily_loss="USD 4,000 Daily drawdown", min_trading_days="Pass in as little as 1 Day",
    profit_split="80%", funded_consistency="40%", fee_refund=("NOT STATED", "modelled as no refund"))
add("Alpha Capital", "Alpha Pro 10% (2-step)", "USD 100,000", "a_px",
    fee="USD 497 bi-weekly / USD 447 on-demand", profit_target_phase1="10%", profit_target_phase2="5%",
    max_daily_loss="5%", max_loss="10% static", min_trading_days="3 per phase",
    profit_split="80% standard, optional 90% add-on")
add("Alpha Capital", "Alpha Pro 10% (2-step)", "USD 100,000", "a_pro",
    daily_loss_basis="balance-based on Pro 10%", time_limit="no maximum trading-day cap",
    payout_conditions="bi-weekly: $100 minimum and 5 trading days for first request; on-demand: 40% best-day rule and 2% minimum profit",
    fee_refund=("NOT STATED", "modelled as no refund"))
add("Alpha Capital", "Alpha One 10% (1-step)", "USD 100,000", "a_px", fee="USD 477",
    profit_target_phase1="10%", max_daily_loss="4%",
    max_loss="6% trailing max loss based on high-water mark",
    profit_split="80% standard, optional 90% add-on")
add("Alpha Capital", "Alpha One 10% (1-step)", "USD 100,000", "a_one", min_trading_days="at least 1 trading day",
    payout_conditions="on-demand; 40% Best Day Rule and 2% minimum profit",
    max_loss_type=("trailing max loss based on the high-water mark", "intraday trailing, no lock assumed"))
add("FunderPro", "Classic 2-Phase", "USD 100,000", "fp",
    fee=("USD 539", "page says: Price (will be processed with 1st reward) - read here as refunded with the first reward; ambiguous"),
    profit_target_phase1="10%", profit_target_phase2="5%",
    max_daily_loss="5% (balance based, set at start of day 5 pm EST)", max_loss="10%",
    max_loss_type="No Trailing Drawdown", min_trading_days="4", time_limit="Unlimited",
    profit_split=("Up to 90%", "base NOT STATED; 80% assumed"))
add("BrightFunded", "Classic 2-Step", "USD 100,000", "bf",
    fee=("EUR 477", "list; EUR 357.75 with a -25% promotion shown"),
    profit_target_phase1="8%", profit_target_phase2="5%", max_daily_loss="4%", max_loss="8%",
    max_loss_type=("NOT STATED on the page read", "static assumed"), min_trading_days="5",
    time_limit="Unlimited", profit_split=("Up to 90%", "base NOT STATED; 80% assumed"),
    evaluation_profit_reward=("15% of evaluation profit = USD 1,950",
                              "included in the model as a one-off on the first payout"),
    fee_refund=("offered as a paid add-on only", "modelled as no refund"),
    published_average_reward=("USD 2,422", "Avg. reward shown next to the 100K plan; definition not given"))
for firm, url, code in (("Apex Trader Funding", "https://apextraderfunding.com/", 403),
                        ("FundingPips", "https://fundingpips.com/", 429)):
    R.append([firm, "-", "-", "ALL", "NOT RETRIEVED", url, D, "",
              f"page refused automated access (HTTP {code}) on repeated attempts; not modelled"])

with (ROOT / "data" / "firm_rules_sourced.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["firm", "product", "account_size", "field", "value_as_published", "source_url", "access_date",
                "archived_file_in_data_raw_firm_pages", "note"])
    w.writerows(R)

# ------------------------------------------------------------------ model parameters (fractions of account)
EURUSD = 1.12  # Yahoo EURUSD=X close on 2026-10-13 was 1.1198; used only to express EUR fees in USD
H = ["key", "firm", "product", "account_usd", "targets", "daily_loss", "daily_mode", "max_loss", "dd_type", "lock",
     "min_days", "min_profit_days", "profit_day_thr", "consistency", "time_limit", "fee_usd", "activation_usd",
     "refund", "split", "funded_cycle_days", "funded_min_profit", "funded_consistency", "funded_mode", "bonus_frac",
     "assumptions"]
M = [
    ["FTMO_2S", "FTMO", "2-Step Challenge", 100000, "0.10|0.05", 0.05, "breach", 0.10, "static", 0, 4, 0, 0, 0, 0,
     round(540 * EURUSD, 2), 0, 1, 0.80, 10, 0, 0, "cfd", 0,
     "payout every 10 trading days assumed; EUR fee converted at 1.12"],
    ["FTMO_1S", "FTMO", "1-Step Challenge", 100000, "0.10", 0.03, "breach", 0.10, "trail_eod", 0, 0, 0, 0, 0.50, 0,
     round(499 * EURUSD, 2), 0, 0, 0.90, 10, 0, 0.50, "cfd", 0,
     "no refund assumed; payout every 10 trading days assumed"],
    ["FN_ST2", "FundedNext", "Stellar 2-Step", 100000, "0.08|0.05", 0.05, "breach", 0.10, "static", 0, 5, 0, 0, 0, 0,
     549.99, 0, 1, 0.80, 10, 0, 0, "cfd", 0,
     "daily loss on start-of-day balance assumed; payout timing simplified to 10-trading-day cycles"],
    ["5ERS_HS", "The5ers", "High Stakes (2-step)", 2500, "0.10|0.05", 0.05, "breach", 0.10, "static", 0, 0, 3, 0.005,
     0, 0, 19.0, 0, 1, 0.80, 10, 0, 0, "cfd", 0,
     "$2.5K tier (only price retrieved); static max loss assumed; refund with first payout assumed"],
    ["TOPSTEP_50K", "Topstep", "Trading Combine 50K", 50000, "0.06", 0.0, "pause", 0.04, "trail_eod", 1, 2, 0, 0, 0.55,
     0, 49.0, 149.0, 0, 0.90, 0, 0, 0, "futures", 0,
     "one monthly fee per attempt assumed; optional daily loss limit off; payout after 5 winning days of 0.3%, 50% of balance capped at 10% of account"],
    ["E8_ONE", "E8 Markets", "E8 One", 100000, "0.09", 0.04, "breach", 0.06, "trail_intraday", 0, 1, 0, 0, 0, 0,
     488.0, 0, 0, 0.80, 10, 0, 0.40, "cfd", 0,
     "dynamic drawdown modelled as intraday trailing, no lock (NOT STATED on page); no refund assumed"],
    ["ALPHA_PRO10", "Alpha Capital", "Alpha Pro 10% (2-step)", 100000, "0.10|0.05", 0.05, "breach", 0.10, "static", 0,
     3, 0, 0, 0, 0, 497.0, 0, 0, 0.80, 10, 0, 0, "cfd", 0, "bi-weekly price; no refund assumed"],
    ["ALPHA_ONE10", "Alpha Capital", "Alpha One 10% (1-step)", 100000, "0.10", 0.04, "breach", 0.06, "trail_intraday",
     0, 1, 0, 0, 0, 0, 477.0, 0, 0, 0.80, 10, 0.02, 0.40, "cfd", 0,
     "high-water-mark trailing modelled as intraday, no lock; no refund assumed"],
    ["FUNDERPRO_CL", "FunderPro", "Classic 2-Phase", 100000, "0.10|0.05", 0.05, "breach", 0.10, "static", 0, 4, 0, 0,
     0, 0, 539.0, 0, 1, 0.80, 10, 0, 0, "cfd", 0,
     "refund with first reward assumed from ambiguous wording; base split 80% assumed"],
    ["BRIGHT_CL2", "BrightFunded", "Classic 2-Step", 100000, "0.08|0.05", 0.04, "breach", 0.08, "static", 0, 5, 0, 0,
     0, 0, round(477 * EURUSD, 2), 0, 0, 0.80, 10, 0, 0, "cfd", 0.0195,
     "static max loss assumed; base split 80% assumed; 15% of evaluation profit paid with first payout"],
]
with (ROOT / "data" / "rule_sets_model.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(H)
    w.writerows(M)

S = [
    ["Topstep", "Trading Combines initiated that were completed (per account)", "16.8%", "Jan-Dec 2025", U["ts_home"], D, "topstep_home.html"],
    ["Topstep", "individual participants who reached the Funded Level at least once", "51.8%", "Jan-Dec 2025", U["ts_home"], D, "topstep_home.html"],
    ["Topstep", "individual participants at the Funded Level who received a payout", "33.3%", "Jan-Dec 2025", U["ts_home"], D, "topstep_home.html"],
    ["Topstep", "Express Funded Account participants called up to a Live Funded Account", "0.71%", "Jan-Dec 2025", U["ts_home"], D, "topstep_home.html"],
    ["Topstep", "traders who lost their Combine / account in a single day (wording differs between two help pages)", "63%", "not dated", U["ts_dll"], D, "topstep_dll.html; topstep_payout.html"],
    ["E8 Markets", "evaluation customer pass rate, customers who traded at least once", "17.7%", "1 Jan 2023 - 1 Mar 2024", U["e8"], D, "e8_home.html"],
    ["FunderPro", "traders who purchase a challenge and pass to the funded phase", "7.35%", "company inception to present", U["fp"], D, "funderpro_home.html"],
    ["Take Profit Trader", "currently registered users who have passed a trading test", "20.37%", "1 Jan - 31 Aug 2023", U["tpt"], D, "tpt_home.html"],
    ["Take Profit Trader", "Trading Tests successfully passed (per test)", "36.22%", "1 Jan - 31 Dec 2025", U["tpt"], D, "tpt_home.html"],
    ["FTMO", "average_reward for the USD 100,000 2-Step account (definition not given)", "USD 5,957", "not dated", U["ftmo_home"], D, "ftmo_home.html"],
    ["BrightFunded", "Avg. reward shown for the USD 100,000 Classic plan (definition not given)", "USD 2,422", "not dated", U["bf"], D, "brightfunded_home.html"],
]
with (ROOT / "data" / "published_statistics.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["firm", "statistic_as_described_by_firm", "value", "period", "source_url", "access_date", "archived_file"])
    w.writerows(S)
print(len(R), "sourced rows;", len(M), "model rule sets;", len(S), "statistics")
