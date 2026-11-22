"""Step 4b: does each exposed group differ from the control group? (spec S6)

For every trading day, take the equal-weighted average excess return of each
group's firms (firms enter when they have a return, e.g. CRWV from 2025-03).
For each exposed group G, the long-short return is

    ls_ret_t = mean excess return of G on t - mean excess return of Control on t

and we run   ls_ret ~ mkt_rf + dgpu   (OLS, Newey-West HAC SEs, same as step 4).

The dgpu coefficient is the gap between G's average compute beta and the
controls'. One portfolio regression gets the standard error right even though
every firm is regressed on the SAME GPU series (a t-test across firm betas
would treat them as independent and overstate significance).

Output: outputs/group_tests.csv   one row = exposed group
"""
import pandas as pd
import statsmodels.formula.api as smf

import config as C

GROUPS = ["Chipmaker", "Cloud provider", "AI-heavy software"]
CONTROL = "Control"


def group_portfolios(panel: pd.DataFrame) -> pd.DataFrame:
    """One row = trading day; one column per group (equal-weighted excess return)."""
    port = panel.groupby(["date", "group"])["ret_rf"].mean().unstack("group")
    days = panel.drop_duplicates("date").set_index("date")[["mkt_rf", "dgpu"]]
    out = port.join(days, how="inner", validate="1:1")
    assert out.index.is_unique
    return out


def main() -> None:
    panel = pd.read_csv(C.PROCESSED / "panel.csv", parse_dates=["date"])
    # Market and GPU columns are per-date, so they must be identical across firms.
    assert (panel.groupby("date")[["mkt_rf", "dgpu"]].nunique(dropna=False) <= 1).all().all()
    port = group_portfolios(panel)

    rows = []
    for g in GROUPS:
        df = pd.DataFrame({"ls_ret": port[g] - port[CONTROL],
                           "mkt_rf": port["mkt_rf"], "dgpu": port["dgpu"]}).dropna()
        res = smf.ols("ls_ret ~ mkt_rf + dgpu", data=df).fit(
            cov_type="HAC", cov_kwds={"maxlags": C.HAC_LAGS})
        lo, hi = res.conf_int().loc["dgpu"]
        rows.append({
            "spec": "S6_group_vs_control", "group": g, "vs": CONTROL,
            "diff_compute_beta": res.params["dgpu"], "se": res.bse["dgpu"],
            "t": res.tvalues["dgpu"], "p": res.pvalues["dgpu"], "ci_lo": lo, "ci_hi": hi,
            "nobs": int(res.nobs), "gpu_timing": C.GPU_TIMING_MAIN,
            "data_source": C.data_source(),
        })
    out = pd.DataFrame(rows)
    assert out["group"].is_unique
    out.to_csv(C.OUTPUTS / "group_tests.csv", index=False)
    print(out[["group", "diff_compute_beta", "se", "p", "nobs"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
