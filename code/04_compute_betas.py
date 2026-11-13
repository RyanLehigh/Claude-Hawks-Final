"""Step 4: estimate compute betas, firm by firm.

Specifications (every one is also listed in specs_tried.md):
  S1 same_day     ret_rf ~ mkt_rf + dgpu
  S2 same_day_ff3 ret_rf ~ mkt_rf + smb + hml + dgpu
  S3 lead_lag     ret_rf ~ mkt_rf + dgpu_lag2 + dgpu_lag1 + dgpu + dgpu_lead1 + dgpu_lead2

OLS with Newey-West (HAC) standard errors. Every firm is reported, whatever
its estimate.

Outputs:
  outputs/betas_long.csv   one row = firm x spec x term
  outputs/compute_betas.csv one row = firm (S1 compute beta + CI), the main result
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import config as C

lags = [f"dgpu_lag{k}" for k in range(C.LEADLAG_K, 0, -1)]
leads = [f"dgpu_lead{k}" for k in range(1, C.LEADLAG_K + 1)]
SPECS = {
    "S1_same_day": "ret_rf ~ mkt_rf + dgpu",
    "S2_same_day_ff3": "ret_rf ~ mkt_rf + smb + hml + dgpu",
    "S3_lead_lag": "ret_rf ~ mkt_rf + " + " + ".join(lags + ["dgpu"] + leads),
}
# k = days the GPU move is shifted relative to the stock return (negative = GPU moved first)
K_OF_TERM = {"dgpu": 0,
             **{f"dgpu_lag{k}": -k for k in range(1, C.LEADLAG_K + 1)},
             **{f"dgpu_lead{k}": k for k in range(1, C.LEADLAG_K + 1)}}


def fit_one(df: pd.DataFrame, formula: str) -> pd.DataFrame | None:
    needed = [v.strip() for v in formula.replace("~", "+").split("+")]
    df = df.dropna(subset=needed)
    if len(df) < C.MIN_OBS:
        return None
    res = smf.ols(formula, data=df).fit(cov_type="HAC", cov_kwds={"maxlags": C.HAC_LAGS})
    ci = res.conf_int()
    return pd.DataFrame({
        "term": res.params.index,
        "coef": res.params.values,
        "se": res.bse.values,
        "t": res.tvalues.values,
        "p": res.pvalues.values,
        "ci_lo": ci[0].values,
        "ci_hi": ci[1].values,
        "nobs": int(res.nobs),
        "r2": res.rsquared,
    })


def main() -> None:
    panel = pd.read_csv(C.PROCESSED / "panel.csv", parse_dates=["date"])
    source = C.data_source()

    rows = []
    for (ticker, group), df in panel.groupby(["ticker", "group"]):
        for spec, formula in SPECS.items():
            out = fit_one(df, formula)
            if out is None:
                print(f"  {ticker} {spec}: too few obs, skipped")
                continue
            out.insert(0, "spec", spec)
            out.insert(0, "group", group)
            out.insert(0, "ticker", ticker)
            rows.append(out)
    long = pd.concat(rows, ignore_index=True)
    long["k"] = long["term"].map(K_OF_TERM)
    long["data_source"] = source
    long["sample_start"] = panel["date"].min().date().isoformat()
    long["sample_end"] = panel["date"].max().date().isoformat()

    assert not long.duplicated(["ticker", "spec", "term"]).any()
    C.OUTPUTS.mkdir(exist_ok=True)
    long.to_csv(C.OUTPUTS / "betas_long.csv", index=False)

    # Main result: S1 compute beta, one row per firm.
    main_tbl = (long.query("spec == 'S1_same_day' and term == 'dgpu'")
                [["ticker", "group", "coef", "se", "t", "p", "ci_lo", "ci_hi", "nobs", "r2",
                  "data_source", "sample_start", "sample_end"]]
                .rename(columns={"coef": "compute_beta"}))
    mkt = (long.query("spec == 'S1_same_day' and term == 'mkt_rf'")
           [["ticker", "coef"]].rename(columns={"coef": "market_beta"}))
    main_tbl = main_tbl.merge(mkt, on="ticker", how="left", validate="1:1")
    # Magnitude: stock return response to a 10% rise in the GPU price, in basis points.
    main_tbl["bps_per_10pct_gpu_move"] = main_tbl["compute_beta"] * np.log(1.10) * 1e4
    main_tbl = main_tbl.sort_values("compute_beta", ascending=False).reset_index(drop=True)

    assert main_tbl["ticker"].is_unique and len(main_tbl) == len(C.FIRMS)
    main_tbl.to_csv(C.OUTPUTS / "compute_betas.csv", index=False)

    n_reg = long.groupby(["ticker", "spec"]).ngroups
    print(f"ran {n_reg} regressions ({len(SPECS)} specs x {panel['ticker'].nunique()} firms), "
          f"data_source={source}")
    print(main_tbl[["ticker", "group", "market_beta", "compute_beta", "se", "p"]]
          .round(3).to_string(index=False))


if __name__ == "__main__":
    main()
