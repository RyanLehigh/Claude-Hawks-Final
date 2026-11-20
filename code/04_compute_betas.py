"""Step 4: estimate compute betas, firm by firm.

Specifications (every one is also listed in specs_tried.md). dgpu uses the
MAIN GPU timing rule and dgpu_alt the other one (config.GPU_TIMING_*; v1 main =
next_day). v0 called these S1_same_day ... S5_next_day, when same-day was main.
  S1 main         ret_rf ~ mkt_rf + dgpu
  S2 ff3          ret_rf ~ mkt_rf + smb + hml + dgpu
  S3 lead_lag     ret_rf ~ mkt_rf + dgpu_lag2 + dgpu_lag1 + dgpu + dgpu_lead1 + dgpu_lead2
  S4 nasdaq       ret_rf ~ mkt_rf + qqq_rf + dgpu       (audit A2: Nasdaq/tech control)
  S5 alt_timing   ret_rf ~ mkt_rf + dgpu_alt            (audit A3: the other GPU timing)

OLS with Newey-West (HAC) standard errors. Every firm is reported, whatever
its estimate.

Outputs:
  outputs/betas_long.csv          one row = firm x spec x term
  outputs/compute_betas.csv       one row = firm (S1 compute beta + CI), the main result
  outputs/robustness_betas.csv    one row = firm x spec: the compute beta in every
                                  same-day-style spec (S1, S2, S4, S5), side by side
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

import config as C

lags = [f"dgpu_lag{k}" for k in range(C.LEADLAG_K, 0, -1)]
leads = [f"dgpu_lead{k}" for k in range(1, C.LEADLAG_K + 1)]
SPECS = {
    "S1_main": "ret_rf ~ mkt_rf + dgpu",
    "S2_ff3": "ret_rf ~ mkt_rf + smb + hml + dgpu",
    "S3_lead_lag": "ret_rf ~ mkt_rf + " + " + ".join(lags + ["dgpu"] + leads),
    "S4_nasdaq": "ret_rf ~ mkt_rf + qqq_rf + dgpu",
    "S5_alt_timing": "ret_rf ~ mkt_rf + dgpu_alt",
}
# The compute-beta term in each single-coefficient spec (S3 has a whole profile instead).
COMPUTE_TERM = {"S1_main": "dgpu", "S2_ff3": "dgpu",
                "S4_nasdaq": "dgpu", "S5_alt_timing": "dgpu_alt"}
# GPU timing rule behind each spec (see config.py)
TIMING = {s: (C.GPU_TIMING_ALT if s == "S5_alt_timing" else C.GPU_TIMING_MAIN) for s in SPECS}
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
    long["gpu_timing"] = long["spec"].map(TIMING)
    long["data_source"] = source
    long["sample_start"] = panel["date"].min().date().isoformat()
    long["sample_end"] = panel["date"].max().date().isoformat()

    assert not long.duplicated(["ticker", "spec", "term"]).any()
    C.OUTPUTS.mkdir(exist_ok=True)
    long.to_csv(C.OUTPUTS / "betas_long.csv", index=False)

    # Main result: S1 compute beta, one row per firm.
    main_tbl = (long.query("spec == 'S1_main' and term == 'dgpu'")
                [["ticker", "group", "coef", "se", "t", "p", "ci_lo", "ci_hi", "nobs", "r2",
                  "data_source", "sample_start", "sample_end"]]
                .rename(columns={"coef": "compute_beta"}))
    main_tbl["gpu_timing"] = C.GPU_TIMING_MAIN
    mkt = (long.query("spec == 'S1_main' and term == 'mkt_rf'")
           [["ticker", "coef"]].rename(columns={"coef": "market_beta"}))
    main_tbl = main_tbl.merge(mkt, on="ticker", how="left", validate="1:1")
    # Magnitude: stock return response to a 10% rise in the GPU price, in basis points.
    main_tbl["bps_per_10pct_gpu_move"] = main_tbl["compute_beta"] * np.log(1.10) * 1e4
    # Volatility-scaled beta: a 1-sd GPU move, in sd's of the stock's excess return.
    # Makes low-volatility controls comparable to high-volatility chipmakers.
    used = panel.dropna(subset=["ret_rf", "mkt_rf", "dgpu"])
    sds = (used.groupby("ticker")
           .agg(sd_ret=("ret_rf", "std"), sd_gpu=("dgpu", "std")).reset_index())
    main_tbl = main_tbl.merge(sds, on="ticker", how="left", validate="1:1")
    main_tbl["std_compute_beta"] = main_tbl["compute_beta"] * main_tbl["sd_gpu"] / main_tbl["sd_ret"]
    main_tbl = main_tbl.drop(columns=["sd_ret", "sd_gpu"])   # sd_gpu would describe Ornn data
    # Multiple testing across the firms: Benjamini-Hochberg false discovery rate.
    main_tbl["p_bh"] = multipletests(main_tbl["p"], method="fdr_bh")[1]
    main_tbl = main_tbl.sort_values("compute_beta", ascending=False).reset_index(drop=True)

    assert main_tbl["ticker"].is_unique and len(main_tbl) == len(C.FIRMS)
    main_tbl.to_csv(C.OUTPUTS / "compute_betas.csv", index=False)

    # Robustness: the compute beta from every single-coefficient spec, one row per firm x spec.
    is_compute = long["term"] == long["spec"].map(COMPUTE_TERM)
    rob = (long[is_compute]
           [["ticker", "group", "spec", "gpu_timing", "term", "coef", "se", "p",
             "ci_lo", "ci_hi", "nobs", "data_source"]]
           .rename(columns={"coef": "compute_beta"})
           .sort_values(["group", "ticker", "spec"]).reset_index(drop=True))
    assert len(rob) == len(C.FIRMS) * len(COMPUTE_TERM), "a firm x spec is missing"
    rob.to_csv(C.OUTPUTS / "robustness_betas.csv", index=False)

    n_reg = long.groupby(["ticker", "spec"]).ngroups
    print(f"ran {n_reg} regressions ({len(SPECS)} specs x {panel['ticker'].nunique()} firms), "
          f"data_source={source}")
    print(main_tbl[["ticker", "group", "market_beta", "compute_beta", "std_compute_beta",
                    "se", "p", "p_bh"]]
          .round(3).to_string(index=False))
    print("\ncompute beta by spec:")
    print(rob.pivot(index="ticker", columns="spec", values="compute_beta").round(3).to_string())


if __name__ == "__main__":
    main()
