import streamlit as st
import sys
import os
import math
import yfinance as yf

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from fundamentals import get_fundamentals, get_historical_growth_rates, calculate_dcf


# ---------- Cached data loaders ----------
# st.cache_data remembers a function's result for a while, so Streamlit
# doesn't re-download the same data every time you touch the dropdown.

@st.cache_data(ttl=3600)
def load_fundamentals(ticker):
    return get_fundamentals(ticker)


@st.cache_data(ttl=3600)
def load_valuation(ticker):
    growth_rates = get_historical_growth_rates(ticker)
    results = {}
    for scenario in ["bear", "base", "bull"]:
        results[scenario] = calculate_dcf(ticker, growth_rate=growth_rates[scenario])
    return growth_rates, results


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
growth_rates, dcf_results = load_valuation(ticker)

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

# ---------- Assumptions shown next to the valuation ----------

st.subheader("Assumptions behind these values")

base = dcf_results["base"]
st.write(
    f"- **WACC:** {base['wacc'] * 100:.1f}%  (placeholder assumption, not derived from the company)\n"
    f"- **Terminal growth:** {base['terminal_growth'] * 100:.1f}%\n"
    f"- **Projection period:** 5 years\n"
    f"- **Bear growth:** {growth_rates['bear'] * 100:.2f}%  (lowest valid historical revenue growth)\n"
    f"- **Base growth:** {growth_rates['base'] * 100:.2f}%  (middle historical revenue growth)\n"
    f"- **Bull growth:** {growth_rates['bull'] * 100:.2f}%  (highest historical revenue growth)"
)

st.caption(
    "Data source: yfinance (unofficial Yahoo Finance wrapper). "
    "Scenario growth rates come from only 3-4 years of history, so Bear and Base "
    "can sit very close together for some companies."
)