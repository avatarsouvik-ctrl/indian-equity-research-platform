import streamlit as st
import sys
import os
import math
import pandas as pd
import yfinance as yf

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from fundamentals import (
    get_fundamentals,
    get_historical_growth_rates,
    get_dcf_inputs,
    run_dcf_math,
    build_sensitivity_grid,
)

# Assumptions used for the Bear/Base/Bull cards
WACC = 0.12
TERMINAL_GROWTH = 0.04
PROJECTION_YEARS = 5


# ---------- Cached data loaders ----------

@st.cache_data(ttl=3600)
def load_fundamentals(ticker):
    return get_fundamentals(ticker)


@st.cache_data(ttl=3600)
def load_growth_rates(ticker):
    return get_historical_growth_rates(ticker)


@st.cache_data(ttl=3600)
def load_dcf_inputs(ticker):
    return get_dcf_inputs(ticker)


@st.cache_data(ttl=300)
def load_current_price(ticker):
    info = yf.Ticker(ticker).info
    price = info.get("currentPrice")
    if price is None:
        price = info.get("regularMarketPrice")
    return price


def fmt(value, decimals=2):
    """Show N/A instead of crashing or faking a zero when data is missing."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    return f"{value:,.{decimals}f}"


# ---------- Page ----------

st.title("Indian Equity Research & Valuation Platform")

companies = {
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HCLTech": "HCLTECH.NS",
    "Wipro": "WIPRO.NS",
    "Tech Mahindra": "TECHM.NS"
}

selected_company = st.selectbox("Select a company", list(companies.keys()))
ticker = companies[selected_company]

st.header(f"{selected_company} ({ticker})")

fundamentals = load_fundamentals(ticker)
current_price = load_current_price(ticker)
growth_rates = load_growth_rates(ticker)
dcf_inputs = load_dcf_inputs(ticker)

dcf_results = {
    scenario: run_dcf_math(
        dcf_inputs, growth_rates[scenario], WACC, TERMINAL_GROWTH, PROJECTION_YEARS
    )
    for scenario in ["bear", "base", "bull"]
}

# ---------- Current price ----------

st.metric("Current Market Price", f"₹{fmt(current_price)}")

# ---------- Fundamentals ----------

st.subheader("Fundamentals")
st.caption(f"Reported figures are in {fundamentals['currency']}")

col1, col2, col3 = st.columns(3)
col1.metric("Revenue", fmt(fundamentals["revenue"], 0))
col2.metric("EBITDA", fmt(fundamentals["ebitda"], 0))
col3.metric("Net Income", fmt(fundamentals["net_income"], 0))

col4, col5, col6 = st.columns(3)
col4.metric("P/E Ratio", fmt(fundamentals["pe_ratio"]))
col5.metric("Debt/Equity", fmt(fundamentals["debt_to_equity"], 3))
col6.metric("EV/EBITDA", fmt(fundamentals["ev_to_ebitda"]))

# ---------- DCF valuation ----------

st.subheader("DCF Valuation (per share)")

cols = st.columns(3)
for col, scenario in zip(cols, ["bear", "base", "bull"]):
    value = dcf_results[scenario]["intrinsic_value_per_share"]
    if current_price:
        upside = (value / current_price - 1) * 100
        delta_text = f"{upside:+.1f}% vs market"
    else:
        delta_text = None
    col.metric(scenario.capitalize(), f"₹{fmt(value)}", delta_text)

# ---------- Assumptions ----------

st.subheader("Assumptions behind these values")

st.write(
    f"- **WACC:** {WACC * 100:.1f}%  (placeholder assumption, not derived from the company)\n"
    f"- **Terminal growth:** {TERMINAL_GROWTH * 100:.1f}%\n"
    f"- **Projection period:** {PROJECTION_YEARS} years\n"
    f"- **Bear growth:** {growth_rates['bear'] * 100:.2f}%  (lowest valid historical revenue growth)\n"
    f"- **Base growth:** {growth_rates['base'] * 100:.2f}%  (middle historical revenue growth)\n"
    f"- **Bull growth:** {growth_rates['bull'] * 100:.2f}%  (highest historical revenue growth)"
)

# ---------- Sensitivity analysis ----------

st.subheader("Sensitivity: WACC × Terminal Growth")

scenario_choice = st.selectbox("Growth scenario", ["Bear", "Base", "Bull"], index=1)
view = st.radio("Show", ["Value per share (₹)", "% vs market price"], horizontal=True)

wacc_values = [0.10, 0.11, 0.12, 0.13, 0.14]
tg_values = [0.03, 0.035, 0.04, 0.045, 0.05]

grid = build_sensitivity_grid(
    dcf_inputs,
    growth_rates[scenario_choice.lower()],
    wacc_values,
    tg_values,
    PROJECTION_YEARS,
)

rows = []
for row in grid:
    formatted_row = []
    for value in row:
        if value is None:
            formatted_row.append("N/A")
        elif view == "Value per share (₹)":
            formatted_row.append(f"₹{value:,.0f}")
        elif current_price:
            formatted_row.append(f"{(value / current_price - 1) * 100:+.0f}%")
        else:
            formatted_row.append("N/A")
    rows.append(formatted_row)

df = pd.DataFrame(
    rows,
    index=[f"WACC {w * 100:.1f}%" for w in wacc_values],
    columns=[f"TG {g * 100:.1f}%" for g in tg_values],
)
st.dataframe(df)

st.caption(
    "Each cell re-runs the full DCF with a different discount rate (WACC, rows) and "
    "terminal growth rate (TG, columns). The centre cell (12.0% / 4.0%) equals the "
    "value in the DCF cards above, which is a built-in consistency check. "
    "Notice how far the values move: most of a DCF's value sits in the terminal value."
)

st.caption(
    "Data source: yfinance (unofficial Yahoo Finance wrapper). "
    "Scenario growth rates come from only 3-4 years of history, so Bear and Base "
    "can sit very close together for some companies."
)