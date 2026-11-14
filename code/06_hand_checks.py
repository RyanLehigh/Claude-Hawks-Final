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
    check(f"GPU change on Monday {mon.date()} (includes the weekend)",
          panel.loc[panel["date"] == mon, "dgpu"].iloc[0],
          np.log(p[mon.strftime("%Y-%m-%d")]) - np.log(p[fri.strftime("%Y-%m-%d")]),
          private=True)

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

    # Step 5: group average in group_summary equals the mean of firm betas.
    grp = pd.read_csv(C.OUTPUTS / "group_summary.csv").set_index("group")
    chip = betas.loc[betas["group"] == "Chipmaker", "compute_beta"]
    check("Chipmaker mean compute beta", grp.loc["Chipmaker", "mean_compute_beta"],
          chip.sum() / len(chip))

    # Sanity (Quick Reference ABCD): a beta near 0 for a big TECH stock usually means
    # misaligned dates. Control (staples) betas can truly be near 0, so they are only reported.
    tech = betas[betas["group"] != "Control"].set_index("ticker")["market_beta"]
    ok = (tech > 0.5).all()
    lines.append(f"{'PASS' if ok else 'FAIL'}  tech/AI market betas all > 0.5: "
                 + ", ".join(f"{t} {b:.2f}" for t, b in tech.items()))
    assert ok, lines[-1]
    ctrl = betas[betas["group"] == "Control"].set_index("ticker")["market_beta"]
    lines.append("INFO  control market betas (low in 2025-26, confirmed from raw prices): "
                 + ", ".join(f"{t} {b:.2f}" for t, b in ctrl.items()))

    (C.OUTPUTS / "hand_checks.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
