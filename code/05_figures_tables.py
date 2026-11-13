"""Step 5: tables and figures for the dashboard and slides.

Reads only outputs/ (results) and data/processed/panel.csv (for sample counts).
Never writes GPU prices or GPU changes to outputs/.

Outputs:
  outputs/table_compute_betas.md   main table (S1), markdown
  outputs/group_summary.csv        average compute beta by group
  outputs/sample_summary.csv       sample facts for the methodology page
  outputs/fig_compute_betas.png    compute beta with 95% CI, by firm
  outputs/fig_lead_lag.png         lead-lag profile by firm
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config as C

GROUP_ORDER = ["Chipmaker", "Cloud provider", "AI-heavy software", "Control"]
GROUP_COLOR = {"Chipmaker": "#2a6fdb", "Cloud provider": "#1f9e89",
               "AI-heavy software": "#e07b39", "Control": "#8a8a8a"}


def main() -> None:
    betas = pd.read_csv(C.OUTPUTS / "compute_betas.csv")
    long = pd.read_csv(C.OUTPUTS / "betas_long.csv")
    panel = pd.read_csv(C.PROCESSED / "panel.csv", parse_dates=["date"])
    source = betas["data_source"].iloc[0]
    tag = " [FAKE GPU DATA: true beta = 0]" if source == "FAKE" else ""

    # ---- table ---------------------------------------------------------------
    tbl = betas[["ticker", "group", "market_beta", "compute_beta", "se", "ci_lo", "ci_hi",
                 "p", "bps_per_10pct_gpu_move", "nobs"]].copy()
    with open(C.OUTPUTS / "table_compute_betas.md", "w", encoding="utf-8") as f:
        f.write(f"Same-day compute betas (S1), data source: {source}, "
                f"{betas['sample_start'].iloc[0]} to {betas['sample_end'].iloc[0]}\n\n")
        f.write(tbl.round(3).to_markdown(index=False))
        f.write("\n")

    # ---- group summary (equal-weight average of firm betas) ------------------
    grp = (betas.groupby("group")
           .agg(n_firms=("ticker", "count"), mean_compute_beta=("compute_beta", "mean"),
                mean_market_beta=("market_beta", "mean"))
           .reindex(GROUP_ORDER).reset_index())
    grp["data_source"] = source
    grp.to_csv(C.OUTPUTS / "group_summary.csv", index=False)

    # ---- sample summary --------------------------------------------------------
    pd.DataFrame([{
        "data_source": source,
        "n_firms": panel["ticker"].nunique(),
        "n_trading_days": panel["date"].nunique(),
        "n_firm_days": len(panel),
        "start": panel["date"].min().date(),
        "end": panel["date"].max().date(),
        "n_regressions": long.groupby(["ticker", "spec"]).ngroups,
        "n_specs": long["spec"].nunique(),
    }]).to_csv(C.OUTPUTS / "sample_summary.csv", index=False)

    # ---- figure 1: compute betas with CI ---------------------------------------
    b = betas.sort_values("compute_beta")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = b["group"].map(GROUP_COLOR)
    ax.errorbar(b["compute_beta"], b["ticker"],
                xerr=[b["compute_beta"] - b["ci_lo"], b["ci_hi"] - b["compute_beta"]],
                fmt="none", ecolor="#bbbbbb", elinewidth=2)
    ax.scatter(b["compute_beta"], b["ticker"], c=colors, s=60, zorder=3)
    ax.axvline(0, color="black", lw=0.8)
    for g in GROUP_ORDER:
        ax.scatter([], [], c=GROUP_COLOR[g], label=g)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_xlabel("Compute beta (stock excess return on daily log change in GPU price)")
    ax.set_title(f"Same-day compute beta, 95% CI (HAC){tag}", fontsize=10)
    fig.tight_layout()
    fig.savefig(C.OUTPUTS / "fig_compute_betas.png", dpi=150)
    plt.close(fig)

    # ---- figure 2: lead-lag profiles ---------------------------------------------
    ll = long.query("spec == 'S3_lead_lag' and k == k").copy()
    tickers = betas.sort_values(["group", "ticker"])["ticker"].tolist()
    fig, axes = plt.subplots(2, 4, figsize=(11, 5), sharex=True, sharey=True)
    for ax, t in zip(axes.flat, tickers):
        d = ll[ll["ticker"] == t].sort_values("k")
        g = d["group"].iloc[0]
        ax.fill_between(d["k"], d["ci_lo"], d["ci_hi"], color=GROUP_COLOR[g], alpha=0.2)
        ax.plot(d["k"], d["coef"], marker="o", color=GROUP_COLOR[g])
        ax.axhline(0, color="black", lw=0.6)
        ax.set_title(f"{t} ({g})", fontsize=9)
    for ax in axes[-1]:
        ax.set_xlabel("k (negative = GPU moved first)")
    fig.suptitle(f"Lead-lag profile: coefficient on GPU change at t+k{tag}", fontsize=10)
    fig.tight_layout()
    fig.savefig(C.OUTPUTS / "fig_lead_lag.png", dpi=150)
    plt.close(fig)

    print("wrote table_compute_betas.md, group_summary.csv, sample_summary.csv, "
          "fig_compute_betas.png, fig_lead_lag.png")


if __name__ == "__main__":
    main()
