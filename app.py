"""Dashboard (v0 skeleton). Run locally:  streamlit run app.py

Reads ONLY files in outputs/. No downloads, no models, and never any raw or
changed Ornn GPU prices: only regression results.
"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

OUT = Path(__file__).resolve().parent / "outputs"
GROUP_ORDER = ["Chipmaker", "Cloud provider", "AI-heavy software", "Control"]
GROUP_COLORS = ["#2a6fdb", "#1f9e89", "#e07b39", "#8a8a8a"]
color = alt.Color("group:N", scale=alt.Scale(domain=GROUP_ORDER, range=GROUP_COLORS),
                  legend=alt.Legend(title="Group", orient="bottom"))

st.set_page_config(page_title="Compute Beta", layout="wide")


@st.cache_data
def load():
    return (pd.read_csv(OUT / "compute_betas.csv"),
            pd.read_csv(OUT / "betas_long.csv"),
            pd.read_csv(OUT / "group_summary.csv"),
            pd.read_csv(OUT / "sample_summary.csv").iloc[0])


betas, long, groups, sample = load()

st.title("Which stocks are exposed to GPU prices?")
st.caption("FIN 377 final project · Claude-Hawks · data partner: Ornn · v0 skeleton")
if sample["data_source"] == "FAKE":
    st.warning("**These results use FAKE GPU prices** (a random walk unrelated to any stock), "
               "so every true compute beta is zero. Any estimate that looks significant here is "
               "noise. Real results need Ornn's private data, which is never published.")

intro, method, results, explore = st.tabs(["Intro", "Methodology", "Results", "Explore"])

# ---------------------------------------------------------------- Intro
with intro:
    st.header("The question")
    st.markdown(
        "When the price of renting a GPU moves, whose share price moves with it?\n\n"
        "We estimate a **compute beta** for each company: how much its stock return "
        "moves with the daily change in a GPU rental price, after controlling for the "
        "market. We compare chipmakers, cloud providers, AI-heavy software firms, and a "
        "control group with no compute exposure.\n\n"
        "*Placeholder: the team's motivation and who would use this goes here.*")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Firms", int(sample["n_firms"]))
    c2.metric("Trading days", int(sample["n_trading_days"]))
    c3.metric("Sample", f"{sample['start']} → {sample['end']}")
    c4.metric("Regressions run", int(sample["n_regressions"]))

# ---------------------------------------------------------------- Methodology
with method:
    st.header("Data")
    st.markdown(
        "| Input | Source | Notes |\n|---|---|---|\n"
        "| GPU rental price (H100) | Ornn, via the professor | **Private**, never published |\n"
        "| Stock prices | yfinance (adjusted close) | Daily |\n"
        "| Market and factors | Ken French Data Library | Daily, converted from percent |\n")
    st.header("Recipe")
    st.markdown(
        "1. **Changes, not levels.** Daily log change in the GPU price.\n"
        "2. **Timing.** A GPU price dated *d* counts as known by the 4 pm close on *d*. "
        "Weekend and holiday moves roll into the next trading day.\n"
        "3. **Same-day compute beta (S1):**")
    st.latex(r"r_{it}-r_{f,t} = \alpha_i + \beta_i^{MKT}(MKT_t - r_{f,t}) "
             r"+ \beta_i^{GPU}\,\Delta \ln P^{GPU}_t + \varepsilon_{it}")
    st.markdown(
        "4. **Robustness (S2):** add the size and value factors (SMB, HML).\n"
        "5. **Leads and lags (S3):** GPU changes from *t−2* to *t+2*.\n"
        "6. Newey-West (HAC) standard errors, 5 lags. Every firm and every specification is "
        "reported (see `specs_tried.md`).")

# ---------------------------------------------------------------- Results
with results:
    st.header("Same-day compute betas")
    b = betas.copy()
    base = alt.Chart(b).encode(y=alt.Y("ticker:N", sort="-x", title=None))
    bars = base.mark_rule(strokeWidth=3, color="#bbbbbb").encode(
        x=alt.X("ci_lo:Q", title="Compute beta (95% CI)"), x2="ci_hi:Q")
    dots = base.mark_circle(size=120).encode(
        x="compute_beta:Q", color=color,
        tooltip=["ticker", "group", alt.Tooltip("compute_beta:Q", format=".3f"),
                 alt.Tooltip("se:Q", format=".3f"), alt.Tooltip("p:Q", format=".3f")])
    zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="black").encode(x="x:Q")
    st.altair_chart((bars + dots + zero).properties(height=320), width="stretch")

    st.subheader("Table")
    st.dataframe(
        b[["ticker", "group", "market_beta", "compute_beta", "se", "p",
           "bps_per_10pct_gpu_move", "nobs"]].round(3),
        hide_index=True, width="stretch")
    st.caption("`bps_per_10pct_gpu_move`: the stock's same-day return, in basis points, "
               "associated with a 10% rise in the GPU price.")

    st.subheader("By group (equal-weighted average of firm betas)")
    st.dataframe(groups.round(3), hide_index=True, width="stretch")

# ---------------------------------------------------------------- Explore
with explore:
    st.header("Pick a firm")
    c1, c2 = st.columns([1, 2])
    with c1:
        firm = st.selectbox("Firm", betas.sort_values(["group", "ticker"])["ticker"])
        spec = st.radio("Specification", ["S1_same_day", "S2_same_day_ff3"])
        row = long.query("ticker == @firm and spec == @spec and term == 'dgpu'").iloc[0]
        st.metric("Compute beta", f"{row['coef']:.3f}",
                  help="Coefficient on the daily log change in the GPU price")
        st.write(f"95% CI: [{row['ci_lo']:.3f}, {row['ci_hi']:.3f}]  \n"
                 f"p-value: {row['p']:.3f}  \nGroup: {row['group']}  \nDays: {int(row['nobs'])}")
    with c2:
        ll = long.query("ticker == @firm and spec == 'S3_lead_lag' and k == k")
        band = alt.Chart(ll).mark_area(opacity=0.2).encode(
            x=alt.X("k:Q", title="k (negative = GPU price moved first)",
                    scale=alt.Scale(domain=[-2, 2])),
            y=alt.Y("ci_lo:Q", title="Coefficient"), y2="ci_hi:Q")
        line = alt.Chart(ll).mark_line(point=True).encode(x="k:Q", y="coef:Q")
        st.altair_chart((band + line + alt.Chart(pd.DataFrame({"y": [0]}))
                         .mark_rule(color="black").encode(y="y:Q"))
                        .properties(title=f"{firm}: lead-lag profile (S3)", height=300),
                        width="stretch")

    st.subheader("Ranking")
    pick = st.multiselect("Groups", GROUP_ORDER, default=GROUP_ORDER)
    rank = betas[betas["group"].isin(pick)].sort_values("compute_beta", ascending=False)
    st.altair_chart(
        alt.Chart(rank).mark_bar().encode(
            x=alt.X("compute_beta:Q", title="Compute beta (S1)"),
            y=alt.Y("ticker:N", sort="-x", title=None), color=color,
            tooltip=["ticker", "group", alt.Tooltip("compute_beta:Q", format=".3f")])
        .properties(height=280), width="stretch")
