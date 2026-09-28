import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from fundamentals import calculate_fcff, get_fundamentals, get_historical_growth_rates, calculate_dcf

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

st.header(f"{ticker}")

fundamentals = get_fundamentals(ticker)

st.subheader("Fundamentals")
st.write(f"Revenue: {fundamentals['revenue']:,.0f} {fundamentals['currency']}")
st.write(f"EBITDA: {fundamentals['ebitda']:,.0f} {fundamentals['currency']}")
st.write(f"Net Income: {fundamentals['net_income']:,.0f} {fundamentals['currency']}")
st.write(f"P/E Ratio: {fundamentals['pe_ratio']}")
st.write(f"Debt/Equity: {fundamentals['debt_to_equity']:.3f}")
st.write(f"EV/EBITDA: {fundamentals['ev_to_ebitda']:.2f}")

st.subheader("DCF Valuation")

growth_rates = get_historical_growth_rates(ticker)

for scenario in ["bear", "base", "bull"]:
    result = calculate_dcf(ticker, growth_rate=growth_rates[scenario])
    st.write(f"{scenario.capitalize()}: ₹{result['intrinsic_value_per_share']:,.2f} per share")