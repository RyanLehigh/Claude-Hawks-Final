"""Dashboard and final presentation. Run locally:  streamlit run app.py

The tabs are ordered as a talk: question -> method -> results -> robustness ->
explore -> limits. Written for an audience that has never seen the project.

Reads ONLY files in outputs/. No downloads, no models, and never any raw or
changed Ornn GPU prices: only regression results. Every number shown is read
or computed from those files, so nothing here is typed in by hand.
"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

OUT = Path(__file__).resolve().parent / "outputs"
REPO = "https://github.com/RyanLehigh/Claude-Hawks-Final"
GROUP_ORDER = ["Chipmaker", "Cloud provider", "AI-heavy software", "Control"]
GROUP_COLORS = ["#2a6fdb", "#1f9e89", "#e07b39", "#8a8a8a"]
GROUP_PLAIN = {
    "Chipmaker": "Make the chips (they sell the GPUs)",
    "Cloud provider": "Rent out computing power (they own the GPUs)",
    "AI-heavy software": "Build AI products (they pay to use GPUs)",
    "Control": "No real link to GPUs (the comparison group)",
}
NAMES = {  # display labels only
    "NVDA": "Nvidia", "AMD": "AMD", "AVGO": "Broadcom", "TSM": "TSMC", "INTC": "Intel",
    "MU": "Micron", "MRVL": "Marvell", "ARM": "Arm", "AMZN": "Amazon", "MSFT": "Microsoft",
    "GOOGL": "Alphabet", "ORCL": "Oracle", "CRWV": "CoreWeave", "META": "Meta",
    "PLTR": "Palantir", "CRM": "Salesforce", "NOW": "ServiceNow", "SNOW": "Snowflake",
    "ADBE": "Adobe", "AI": "C3.ai", "KO": "Coca-Cola", "PG": "Procter & Gamble",
    "JNJ": "Johnson & Johnson", "WMT": "Walmart", "PEP": "PepsiCo", "MCD": "McDonald's",
    "XOM": "ExxonMobil", "DUK": "Duke Energy",
}
SPEC_LABEL = {
    "S1_main": "Main estimate",
    "S2_ff3": "+ size & value factors",
    "S4_nasdaq": "+ Nasdaq (tech) control",
    "S5_alt_timing": "Same-day timing (check)",
}
NEUTRAL = "#8a8a8a"  # reference lines; readable in light and dark themes
color = alt.Color("group:N", scale=alt.Scale(domain=GROUP_ORDER, range=GROUP_COLORS),
                  legend=alt.Legend(title="Group", orient="bottom"))

st.set_page_config(page_title="Compute Beta", page_icon="📈", layout="wide")
st.markdown("""<style>
.big {font-size:1.35rem; line-height:1.55;}
.callout {border-left:6px solid #e07b39; padding:0.8rem 1.1rem; margin:0.6rem 0 1.2rem 0;
          background:rgba(224,123,57,0.08); border-radius:4px; font-size:1.15rem;}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load():
    return (pd.read_csv(OUT / "compute_betas.csv"),
            pd.read_csv(OUT / "betas_long.csv"),
            pd.read_csv(OUT / "group_summary.csv"),
            pd.read_csv(OUT / "sample_summary.csv").iloc[0],
            pd.read_csv(OUT / "robustness_betas.csv"),
            pd.read_csv(OUT / "group_tests.csv"))


betas, long, groups, sample, robust, gtests = load()
betas["name"] = betas["ticker"].map(NAMES).fillna(betas["ticker"])
betas["label"] = betas["name"] + " (" + betas["ticker"] + ")"

# Headline numbers, all computed from outputs/
N = len(betas)
n_sig = int((betas["p"] < 0.05).sum())
n_expected = 0.05 * N
min_pbh = betas["p_bh"].min()
sig_names = ", ".join(betas.loc[betas["p"] < 0.05, "name"])
top = betas.sort_values("compute_beta", ascending=False).iloc[0]
gt = gtests.set_index("group")
sw = gt.loc["AI-heavy software"] if "AI-heavy software" in gt.index else None
ll = long.query("spec == 'S3_lead_lag' and term.str.startswith('dgpu')", engine="python")
n_ll, n_ll_sig = len(ll), int((ll["p"] < 0.05).sum())
n_regs = int(sample["n_regressions"]) + len(gtests)


def callout(text):
    st.markdown(f'<div class="callout">{text}</div>', unsafe_allow_html=True)


st.title("Do GPU prices move stock prices?")
st.caption(f"FIN 331 final project · Claude-Hawks · GPU price data from Ornn (private, never shown) · "
           f"{sample['start']} to {sample['end']}")
if sample["data_source"] == "FAKE":
    st.warning("**These results use FAKE GPU prices** (a random walk unrelated to any stock), "
               "so every true compute beta is zero. Any estimate that looks significant here is "
               "noise. Real results need Ornn's private data, which is never published.")

tabs = st.tabs(["1 · The question", "2 · How we measured it", "3 · What we found",
                "4 · Does it hold up?", "5 · Explore a firm", "6 · Takeaways & limits"])

# ======================================================================= 1. Question
with tabs[0]:
    st.header("When renting a GPU gets more expensive, whose stock moves?")
    st.markdown(
        '<p class="big">AI runs on <b>GPUs</b>, specialised chips that companies rent by the hour '
        "from cloud providers. The rental price changes every day, a bit like a commodity "
        "price. <b>Ornn</b> builds a daily price index for renting an Nvidia H100, the "
        "workhorse AI chip.</p>"
        '<p class="big">We asked: <b>which companies\' share prices are exposed to that '
        "price?</b> If GPU rent jumps, do chipmakers gain, do AI software firms lose, or does "
        "nobody notice?</p>", unsafe_allow_html=True)

    st.subheader("Who would care")
    c1, c2, c3 = st.columns(3)
    c1.markdown("**A portfolio manager**  \nHow much hidden AI-compute risk is in my stocks?")
    c2.markdown("**A CFO**  \nWill my company's shares react when compute costs rise?")
    c3.markdown("**Ornn and its customers**  \nCan GPU prices be used to hedge, like oil or power?")

    st.subheader("The short answer")
    if sw is not None:
        callout(
            f"<b>Barely.</b> Across {N} companies and {int(sample['n_trading_days'])} trading days, "
            f"day-to-day GPU rental prices explain very little of daily stock returns. The only "
            f"hint is in <b>AI-heavy software</b> stocks, which tend to rise slightly when GPU rent "
            f"rises, and even that is not strong enough to rule out luck (p = {sw['p']:.2f}).")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Companies studied", N)
    c2.metric("Trading days", int(sample["n_trading_days"]))
    c3.metric("Firms with a reliable link", f"0 of {N}" if min_pbh >= 0.05 else
              f"{int((betas['p_bh'] < 0.05).sum())} of {N}",
              help="After correcting for testing many firms at once (Benjamini-Hochberg)")
    c4.metric("Regressions run (all reported)", n_regs)

# ======================================================================= 2. Method
with tabs[1]:
    st.header("How we measured it")
    st.markdown(
        '<p class="big">For each company we estimate one number, its <b>compute beta</b>: '
        "how much the stock moves on a day the GPU rental price moves, <i>after taking out "
        "whatever the whole stock market did that day</i>.</p>", unsafe_allow_html=True)
    callout(f"<b>How to read it:</b> {top['name']} has the largest compute beta, "
            f"{top['compute_beta']:.3f}. That means on a day when GPU rent rises 10%, "
            f"{top['name']}'s stock tends to beat the market by about "
            f"{top['bps_per_10pct_gpu_move'] / 100:.2f}%. A compute beta of 0 means no link.")

    st.subheader("Four steps")
    s1, s2, s3, s4 = st.columns(4)
    s1.markdown("**① Collect**  \nDaily H100 rental index from Ornn, daily stock prices "
                "(Yahoo Finance), daily market returns (Ken French library).")
    s2.markdown("**② Use changes, not levels**  \nTwo things that both trend upward always look "
                "related. So we compare daily *changes* in price, not price levels.")
    s3.markdown("**③ Line up the timing**  \nOrnn's daily price averages the whole day, "
                "including hours after the stock market closes at 4 pm. So we match it to the "
                "*next* trading day, so we never use information stocks couldn't have seen.")
    s4.markdown("**④ Run a regression per firm**  \nStock return on market return and GPU "
                "price change. The GPU coefficient is the compute beta.")

    st.subheader(f"The {N} companies, in four groups chosen before seeing any results")
    gcols = st.columns(4)
    for col, g in zip(gcols, GROUP_ORDER):
        firms = betas.query("group == @g").sort_values("ticker")
        col.markdown(f"**{g}**  \n*{GROUP_PLAIN[g]}*")
        col.markdown("\n".join(f"- {r.name} ({r.ticker})" for r in firms.itertuples()))

    with st.expander("Technical details (for the curious)"):
        st.latex(r"r_{it}-r_{f,t} = \alpha_i + \beta_i^{MKT}(MKT_t - r_{f,t}) "
                 r"+ \beta_i^{GPU}\,\Delta \ln P^{GPU}_t + \varepsilon_{it}")
        st.markdown(
            "- Daily data; GPU price is the Ornn H100 SXM index (a price every day, weekends "
            "included; weekend moves roll into Monday).\n"
            "- Newey-West (HAC) standard errors with 5 lags.\n"
            "- Robustness: add size and value factors; add the Nasdaq-100 (QQQ) return; leads "
            "and lags of the GPU change (t−2 … t+2); same-day timing as a check.\n"
            "- Group test: daily return of each group's equal-weighted portfolio minus the "
            "control portfolio, regressed on the market and the GPU change.\n"
            "- Multiple testing: Benjamini-Hochberg adjusted p-values across firms.\n"
            f"- Every specification is logged in [`specs_tried.md`]({REPO}/blob/main/specs_tried.md); "
            f"code and outputs are in the [repo]({REPO}).")

# ======================================================================= 3. Results
with tabs[2]:
    st.header("What we found")
    st.subheader("Every company's compute beta")
    st.markdown("Each dot is a company's estimate; the line is its 95% confidence range. "
                "**If the line crosses the grey zero line, we can't tell the effect apart from "
                "no effect.**")
    base = alt.Chart(betas).encode(y=alt.Y(
        "label:N", title=None,
        sort=alt.EncodingSortField("compute_beta", order="descending")))
    bars = base.mark_rule(strokeWidth=3, color="#bbbbbb").encode(
        x=alt.X("ci_lo:Q", title="Compute beta (95% confidence range)",
                axis=alt.Axis(tickCount=10)), x2="ci_hi:Q")
    dots = base.mark_circle(size=140).encode(
        x="compute_beta:Q", color=color,
        tooltip=["name", "group", alt.Tooltip("compute_beta:Q", format=".3f"),
                 alt.Tooltip("p:Q", format=".3f", title="p-value")])
    zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=NEUTRAL).encode(x="x:Q")
    st.altair_chart((bars + dots + zero).properties(height=26 * N), width="stretch",
                    height=26 * N + 90)
    callout(f"Almost every line crosses zero. Only {n_sig} of {N} ({sig_names}) clear the usual "
            f"5% bar, and with {N} firms you'd expect about {n_expected:.1f} to do that "
            f"<b>by pure chance</b>. After correcting for that, no firm comes close "
            f"(smallest adjusted p-value: {min_pbh:.2f}).")

    st.subheader("Do the groups differ from companies with no GPU link?")
    st.markdown("For each group, we compare a portfolio of its stocks against the control "
                "group (Coca-Cola, Walmart, etc.). A bar above zero means the group rises more "
                "than the controls when GPU rent rises.")
    gt_plot = gtests.assign(sig=lambda d: d["p"].map(lambda p: f"p = {p:.2f}"))
    gbase = alt.Chart(gt_plot).encode(x=alt.X("group:N", sort=GROUP_ORDER, title=None,
                                              axis=alt.Axis(labelAngle=0)))
    gchart = (gbase.mark_bar(size=60).encode(
                  y=alt.Y("diff_compute_beta:Q", title="Compute beta vs control group"),
                  color=alt.Color("group:N", legend=None,
                                  scale=alt.Scale(domain=GROUP_ORDER, range=GROUP_COLORS)),
                  tooltip=["group", alt.Tooltip("diff_compute_beta:Q", format=".3f"),
                                        alt.Tooltip("p:Q", format=".3f")])
              + gbase.mark_rule(strokeWidth=2, color=NEUTRAL).encode(y="ci_lo:Q", y2="ci_hi:Q")
              + gbase.mark_text(dy=-12, fontSize=15, color=NEUTRAL).encode(y="ci_hi:Q", text="sig:N")
              + alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=NEUTRAL).encode(y="y:Q"))
    st.altair_chart(gchart.properties(height=360), width="stretch")
    if sw is not None and "Chipmaker" in gt.index:
        callout(f"AI-heavy software is the only group with a hint of exposure "
                f"(+{sw['diff_compute_beta']:.3f}, p = {sw['p']:.2f}), short of the usual 5% bar. "
                f"Surprisingly, <b>chipmakers show nothing</b> "
                f"({gt.loc['Chipmaker', 'diff_compute_beta']:+.3f}), even though they're who you'd "
                f"expect to benefit from pricier GPUs.")

    with st.expander("Full results table"):
        st.dataframe(
            betas[["ticker", "name", "group", "market_beta", "compute_beta", "se", "p", "p_bh",
                   "std_compute_beta", "bps_per_10pct_gpu_move", "nobs"]]
            .sort_values("compute_beta", ascending=False).round(3),
            hide_index=True, width="stretch")
        st.caption("`p_bh`: p-value adjusted for testing many firms at once (Benjamini-Hochberg). "
                   "`std_compute_beta`: effect of a typical GPU move, in units of the stock's "
                   "typical daily move. `bps_per_10pct_gpu_move`: the stock's return in basis "
                   "points (1/100 of a percent) on the day a 10% GPU price rise becomes known. "
                   "`nobs`: trading days (CoreWeave listed in March 2025).")
        st.dataframe(groups.drop(columns="data_source").round(3), hide_index=True,
                     width="stretch")

# ======================================================================= 4. Robustness
with tabs[3]:
    st.header("Does it hold up?")
    st.markdown("A good skeptic asks three questions. Here's what each check shows.")

    wide = robust.pivot(index=["ticker", "group"], columns="spec",
                        values="compute_beta").reset_index()
    wide["name"] = wide["ticker"].map(NAMES).fillna(wide["ticker"])
    lim = float(wide[["S1_main", "S4_nasdaq", "S5_alt_timing"]].abs().max().max()) * 1.1
    diag = alt.Chart(pd.DataFrame({"a": [-lim, lim]})).mark_line(
        color="gray", strokeDash=[4, 4]).encode(x="a:Q", y="a:Q")

    def scatter(ycol, ytitle):
        pts = alt.Chart(wide).mark_circle(size=110).encode(
            x=alt.X("S1_main:Q", title="Main estimate", scale=alt.Scale(domain=[-lim, lim])),
            y=alt.Y(f"{ycol}:Q", title=ytitle, scale=alt.Scale(domain=[-lim, lim])),
            color=color, tooltip=["name", "group", alt.Tooltip("S1_main:Q", format=".3f"),
                                  alt.Tooltip(f"{ycol}:Q", format=".3f")])
        return (diag + pts).properties(height=360)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Is it just tech stocks moving together?")
        st.markdown("We add the Nasdaq-100 as a second control. If dots stay on the dashed "
                    "line, the compute beta isn't just a tech-market effect in disguise.")
        st.altair_chart(scatter("S4_nasdaq", "With Nasdaq control"), width="stretch")
    with c2:
        st.subheader("Does the timing choice matter?")
        st.markdown("Same estimate, but matching the GPU price to the *same* day (which peeks "
                    "at after-close hours). Dots far from the line mean timing drives the result.")
        st.altair_chart(scatter("S5_alt_timing", "Same-day timing"), width="stretch")
    corr_nq = wide["S1_main"].corr(wide["S4_nasdaq"])
    corr_t = wide["S1_main"].corr(wide["S5_alt_timing"])
    callout(f"The Nasdaq control barely changes anything (correlation {corr_nq:.2f} with the main "
            f"estimates), so the weak signal isn't a tech factor in disguise. Timing, though, "
            f"matters a lot (correlation {corr_t:.2f}): firm-level estimates are fragile.")

    st.subheader("Do GPU prices move first, or stocks?")
    st.markdown("We also checked GPU price changes from two days before to two days after "
                "each stock return. Below is the average across firms in each group.")
    ll_avg = (ll.groupby(["group", "k"], as_index=False)["coef"].mean())
    st.altair_chart(
        alt.Chart(ll_avg).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X("k:Q", title="Day of GPU price change relative to the stock return "
                                 "(negative = GPU moved first)",
                    scale=alt.Scale(domain=[-2, 2]), axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("coef:Q", title="Average coefficient"), color=color,
            tooltip=["group", "k", alt.Tooltip("coef:Q", format=".3f")])
        + alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=NEUTRAL).encode(y="y:Q"),
        width="stretch")
    callout(f"No pattern. Of {n_ll} lead and lag coefficients, {n_ll_sig} pass the 5% bar, "
            f"about the {0.05 * n_ll:.0f} you'd expect by chance. GPU prices don't predict "
            f"stocks, and stocks don't predict GPU prices.")

    with st.expander("Every firm in every specification"):
        tbl = wide.rename(columns=SPEC_LABEL)[["ticker", "name", "group"] +
                                             list(SPEC_LABEL.values())].round(3)
        st.dataframe(tbl, hide_index=True, width="stretch")

# ======================================================================= 5. Explore
with tabs[4]:
    st.header("Explore a firm")
    c1, c2 = st.columns([1, 2])
    with c1:
        order = betas.sort_values(["group", "ticker"])
        firm = st.selectbox("Company", order["ticker"],
                            format_func=lambda t: f"{NAMES.get(t, t)} ({t})")
        spec = st.radio("Version of the estimate", list(SPEC_LABEL), format_func=SPEC_LABEL.get)
        row = robust.query("ticker == @firm and spec == @spec").iloc[0]
        st.metric("Compute beta", f"{row['compute_beta']:.3f}")
        st.markdown(f"**Group:** {row['group']}  \n"
                    f"**95% range:** {row['ci_lo']:.3f} to {row['ci_hi']:.3f}  \n"
                    f"**p-value:** {row['p']:.3f}  \n**Trading days:** {int(row['nobs'])}")
        crosses = row["ci_lo"] < 0 < row["ci_hi"]
        st.info("The range includes zero: no detectable link to GPU prices." if crosses else
                "The range excludes zero, but remember: with many firms, a few will by chance.")
    with c2:
        fl = long.query("ticker == @firm and spec == 'S3_lead_lag' and k == k")
        band = alt.Chart(fl).mark_area(opacity=0.2).encode(
            x=alt.X("k:Q", title="Day of GPU price change (negative = GPU moved first)",
                    scale=alt.Scale(domain=[-2, 2]), axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("ci_lo:Q", title="Coefficient"), y2="ci_hi:Q")
        line = alt.Chart(fl).mark_line(point=True).encode(x="k:Q", y="coef:Q")
        st.altair_chart((band + line + alt.Chart(pd.DataFrame({"y": [0]}))
                         .mark_rule(color=NEUTRAL).encode(y="y:Q"))
                        .properties(title=f"{NAMES.get(firm, firm)}: does the GPU price lead or "
                                          f"lag the stock?", height=320), width="stretch")
        st.caption("Shaded band = 95% confidence range. A band covering zero at every point "
                   "means no lead or lag.")

    st.subheader("Ranking")
    pick = st.multiselect("Groups", GROUP_ORDER, default=GROUP_ORDER)
    rank = betas[betas["group"].isin(pick)].sort_values("compute_beta", ascending=False)
    st.altair_chart(
        alt.Chart(rank).mark_bar().encode(
            x=alt.X("compute_beta:Q", title="Compute beta (main estimate)"),
            y=alt.Y("label:N", sort="-x", title=None), color=color,
            tooltip=["name", "group", alt.Tooltip("compute_beta:Q", format=".3f")])
        .properties(height=26 * max(len(rank), 1)), width="stretch",
        height=26 * max(len(rank), 1) + 60)

# ======================================================================= 6. Takeaways
with tabs[5]:
    st.header("Takeaways")
    st.markdown(
        '<p class="big">1. <b>Daily GPU rental prices are not (yet) a stock-market risk factor.</b> '
        "No company's stock reliably moves with them once we account for chance.</p>"
        '<p class="big">2. <b>The faint signal is in AI software, not chips.</b> One possible '
        "reading (not proven by our data): investors see pricier GPUs as a sign of strong AI "
        "demand rather than as a cost.</p>"
        '<p class="big">3. <b>For hedging:</b> stocks are a poor proxy for compute costs, so '
        "anyone exposed to GPU prices would need a direct instrument tied to the GPU price itself, "
        "such as a GPU futures contract.</p>", unsafe_allow_html=True)

    st.header("What could be wrong (and what we did about it)")
    st.markdown(
        "| Concern | What we did |\n|---|---|\n"
        "| **Timing**: when is Ornn's daily price known? | Inferred from Ornn's timestamps it "
        "includes after-close hours, so we use next-day timing. This may blur real effects "
        "toward zero; it can't create fake ones. |\n"
        "| **Luck**: test enough firms and some look exposed | All firms and specifications "
        "reported; p-values corrected for multiple testing. |\n"
        "| **Hidden tech factor** | Nasdaq control added; results barely change. |\n"
        f"| **Short sample** ({sample['start'][:4]}–{sample['end'][:4]}) | One market regime; "
        "results may differ in a GPU glut or shortage. |\n"
        "| **Hindsight in picking 'AI stocks'** | Firm list and groups fixed before any real data "
        "was run, but chosen with today's knowledge. |\n"
        "| **Quiet control group** | Defensive stocks barely tracked the market in this period; "
        "we also report volatility-scaled betas, with the same conclusions. |")

    st.header("Data and reproducibility")
    st.markdown(
        "- GPU prices: **Ornn** H100 SXM daily index, via the course. Private: never shown here "
        "or in the repo; this site shows only regression results.\n"
        "- Stocks: Yahoo Finance. Market and factors: Ken French Data Library.\n"
        f"- Code, outputs, specification log and self-audits: [GitHub repo]({REPO}). "
        "`python run_all.py` rebuilds every number on this page.")
