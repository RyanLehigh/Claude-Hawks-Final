"""Step 6: checks by hand. At least one number per pipeline step is recomputed
independently from the raw files and must match. Any mismatch stops run_all.py.

Output: outputs/hand_checks.txt
"""
import numpy as np
import pandas as pd

import config as C

lines = []


def check(name: str, ours: float, by_hand: float, tol: float = 1e-9, private: bool = False) -> None:
    """private=True: the numbers come from Ornn data, so with real data they are
    compared but NOT written to outputs/ (which is committed and public)."""
    ok = abs(ours - by_hand) <= tol
    if private and C.data_source() == "ORNN":
        detail = "values hidden (private Ornn data)"
    else:
        detail = f"pipeline={ours:.10g}  by_hand={by_hand:.10g}"
    lines.append(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    assert ok, lines[-1]


def main() -> None:
    panel = pd.read_csv(C.PROCESSED / "panel.csv", parse_dates=["date"])
    betas = pd.read_csv(C.OUTPUTS / "compute_betas.csv")
    long = pd.read_csv(C.OUTPUTS / "betas_long.csv")

    # Step 1/3: one NVDA return, from the raw price file with plain arithmetic.
    raw = pd.read_csv(C.RAW_STOCKS / "prices.csv")
    nv = raw[raw["ticker"] == "NVDA"].set_index("date")["adj_close"]
    d = panel.loc[panel["ticker"] == "NVDA", "date"].iloc[100].strftime("%Y-%m-%d")
    prev = nv.index[nv.index.get_loc(d) - 1]
    ours = panel.loc[(panel["ticker"] == "NVDA") & (panel["date"] == pd.Timestamp(d)), "ret"].item()
    check(f"NVDA return on {d}", ours, nv[d] / nv[prev] - 1)

    # Step 1: units and dates of the factors. SPY excess return should track Mkt-RF closely.
    spy = raw[raw["ticker"] == "SPY"].sort_values("date").copy()
    spy["ret"] = spy["adj_close"].pct_change()
    ff = pd.read_csv(C.RAW_FF / "ff3_daily.csv")
    m = spy.merge(ff, on="date", how="inner", validate="1:1").dropna()
    corr = np.corrcoef(m["ret"] - m["rf"], m["mkt_rf"])[0, 1]
    lines.append(f"{'PASS' if corr > 0.95 else 'FAIL'}  corr(SPY excess ret, Ken French Mkt-RF) "
                 f"= {corr:.4f} (want > 0.95: same units, same dates)")
    assert corr > 0.95, lines[-1]

    # Step 1/3: one QQQ excess return (S4 control), from the raw ETF file.
    etf = pd.read_csv(C.RAW_STOCKS / "etf_prices.csv")
    q = etf[etf["ticker"] == C.NASDAQ_PROXY].set_index("date")["adj_close"]
    qprev = q.index[q.index.get_loc(d) - 1]
    rf = ff.set_index("date").loc[d, "rf"]
    ours = panel.loc[(panel["ticker"] == "NVDA") & (panel["date"] == pd.Timestamp(d)), "qqq_rf"].item()
    check(f"{C.NASDAQ_PROXY} excess return on {d}", ours, q[d] / q[qprev] - 1 - rf)

    # Step 2: one GPU change on a Monday = ln P(Mon) - ln P(Fri), straight from the raw file.
    src = (pd.concat([pd.read_csv(f) for f in sorted(C.RAW_ORNN_PRIVATE.glob("*.csv"))])
           if C.data_source() == "ORNN" else pd.read_csv(C.ORNN_FAKE))
    p = (src[src[C.ORNN_SERIES_COL] == C.ORNN_SERIES]
         .set_index(C.ORNN_DATE_COL)[C.ORNN_PRICE_COL])
    # Pick a Monday whose Friday was also a trading day, so the check always runs.
    days = set(panel["date"])
    mon = next(d for d in sorted(days)[10:]
               if d.dayofweek == 0 and d - pd.Timedelta(days=3) in days)
    fri = mon - pd.Timedelta(days=3)
    check(f"GPU change on Monday {mon.date()}, same-day timing (Mon vs Fri price)",
          panel.loc[panel["date"] == mon, "dgpu_sd"].iloc[0],
          np.log(p[mon.strftime("%Y-%m-%d")]) - np.log(p[fri.strftime("%Y-%m-%d")]),
          private=True)
    # Same Monday, alternative timing (S5): the price is known one day after its date,
    # so Monday's level is Sunday's price and Friday's level is Thursday's.
    sun, thu = mon - pd.Timedelta(days=1), mon - pd.Timedelta(days=4)
    check(f"GPU change on Monday {mon.date()}, next-day timing (Sun vs Thu price)",
          panel.loc[panel["date"] == mon, "dgpu_nd"].iloc[0],
          np.log(p[sun.strftime("%Y-%m-%d")]) - np.log(p[thu.strftime("%Y-%m-%d")]),
          private=True)
    # The regressions use dgpu (main rule) and dgpu_alt (other rule): check they point
    # at the right columns, so a config switch can't silently flip the timing.
    rule_col = {"same_day": "dgpu_sd", "next_day": "dgpu_nd"}
    for col, rule in [("dgpu", C.GPU_TIMING_MAIN), ("dgpu_alt", C.GPU_TIMING_ALT)]:
        same = panel[col].equals(panel[rule_col[rule]])
        lines.append(f"{'PASS' if same else 'FAIL'}  {col} uses the {rule} rule ({rule_col[rule]})")
        assert same, lines[-1]

    # Step 3: unit of observation.
    lines.append(f"PASS  panel key (ticker, date) unique: {not panel.duplicated(['ticker', 'date']).any()}")
    assert not panel.duplicated(["ticker", "date"]).any()

    # Step 4: NVDA compute beta by plain least squares (numpy, no statsmodels).
    df = panel[panel["ticker"] == "NVDA"].dropna(subset=["ret_rf", "mkt_rf", "dgpu"])
    X = np.column_stack([np.ones(len(df)), df["mkt_rf"], df["dgpu"]])
    coef, *_ = np.linalg.lstsq(X, df["ret_rf"].to_numpy(), rcond=None)
    check("NVDA compute beta (S1)", betas.query("ticker == 'NVDA'")["compute_beta"].item(),
          coef[2], tol=1e-8)
    check("NVDA market beta (S1)", betas.query("ticker == 'NVDA'")["market_beta"].item(),
          coef[1], tol=1e-8)

    # Step 4: NVDA compute beta in S4 (Nasdaq control) and S5 (other timing), by numpy.
    nv_long = long[long["ticker"] == "NVDA"].set_index(["spec", "term"])["coef"]
    for spec, xcols, gpu_col in [("S4_nasdaq", ["mkt_rf", "qqq_rf"], "dgpu"),
                                 ("S5_alt_timing", ["mkt_rf"], "dgpu_alt")]:
        df = panel[panel["ticker"] == "NVDA"].dropna(subset=["ret_rf", gpu_col] + xcols)
        X = np.column_stack([np.ones(len(df))] + [df[c] for c in xcols] + [df[gpu_col]])
        coef, *_ = np.linalg.lstsq(X, df["ret_rf"].to_numpy(), rcond=None)
        check(f"NVDA compute beta ({spec})", nv_long[(spec, gpu_col)], coef[-1], tol=1e-8)

    # Step 5: group average in group_summary equals the mean of firm betas.
    grp = pd.read_csv(C.OUTPUTS / "group_summary.csv").set_index("group")
    chip = betas.loc[betas["group"] == "Chipmaker", "compute_beta"]
    check("Chipmaker mean compute beta", grp.loc["Chipmaker", "mean_compute_beta"],
          chip.sum() / len(chip))

    # Step 4: Benjamini-Hochberg p for the firm with the smallest p, by hand:
    # p_bh = min over j >= rank of (p_(j) * n / j), capped at 1.
    ps = betas["p"].sort_values().to_numpy()
    n = len(ps)
    bh_first = min(1.0, min(ps[j] * n / (j + 1) for j in range(n)))
    check("BH-adjusted p of the most significant firm",
          betas.loc[betas["p"].idxmin(), "p_bh"], bh_first, tol=1e-12)

    # Step 4: NVDA volatility-scaled beta = beta * sd(dgpu) / sd(ret_rf), by hand.
    df = panel[panel["ticker"] == "NVDA"].dropna(subset=["ret_rf", "mkt_rf", "dgpu"])
    nv = betas.query("ticker == 'NVDA'").iloc[0]
    check("NVDA volatility-scaled compute beta", nv["std_compute_beta"],
          nv["compute_beta"] * df["dgpu"].std() / df["ret_rf"].std(), tol=1e-12)

    # Step 4b: AI-heavy software minus Control portfolio, rebuilt with a plain loop over
    # dates and solved with numpy (no groupby/unstack, no statsmodels).
    gt = pd.read_csv(C.OUTPUTS / "group_tests.csv").set_index("group")
    ys, xs = [], []
    for d, day in panel.groupby("date"):
        a = day.loc[day["group"] == "AI-heavy software", "ret_rf"]
        c = day.loc[day["group"] == "Control", "ret_rf"]
        if len(a) and len(c):
            ys.append(a.sum() / len(a) - c.sum() / len(c))
            xs.append([1.0, day["mkt_rf"].iloc[0], day["dgpu"].iloc[0]])
    coef, *_ = np.linalg.lstsq(np.array(xs), np.array(ys), rcond=None)
    check("AI-heavy software minus Control compute beta (S6)",
          gt.loc["AI-heavy software", "diff_compute_beta"], coef[2], tol=1e-8)

    # Sanity (Quick Reference ABCD): a beta near 0 for a big TECH stock usually means
    # misaligned dates. Control (staples) betas can truly be near 0, so they are only reported.
    tech = betas[betas["group"] != "Control"].set_index("ticker")["market_beta"]
    ok = (tech > 0.5).all()
    lines.append(f"{'PASS' if ok else 'FAIL'}  tech/AI market betas all > 0.5: "
                 + ", ".join(f"{t} {b:.2f}" for t, b in tech.items()))
    assert ok, lines[-1]
    ctrl = betas[betas["group"] == "Control"].set_index("ticker")["market_beta"]
    lines.append("INFO  control market betas (near 0 in 2024-26: real, see README Threats): "
                 + ", ".join(f"{t} {b:.2f}" for t, b in ctrl.items()))

    (C.OUTPUTS / "hand_checks.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
