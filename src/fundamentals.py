import yfinance as yf

def get_usd_to_inr_rate():
    fx = yf.Ticker("USDINR=X")
    rate = fx.info.get("regularMarketPrice")
    return rate


def convert_to_inr(value, currency):
    if currency == "INR":
        return value
    elif currency == "USD":
        rate = get_usd_to_inr_rate()
        return value * rate
    else:
        raise ValueError(f"Unsupported currency: {currency}")


def detect_actual_currency(revenue, market_cap, stated_currency):
    """
    Cross-checks the stated currency against market cap using the
    Price/Sales ratio (Market Cap / Revenue). Real companies usually
    fall somewhere between roughly 0.5 and 20 on this ratio.
    If the stated currency produces an implausible ratio, but the
    other currency would produce a sane one, we override it.
    """
    if revenue is None or market_cap is None:
        return stated_currency, False  # can't check, trust the label

    fx_rate = get_usd_to_inr_rate()

    if stated_currency == "USD":
        ratio_as_stated = market_cap / (revenue * fx_rate)
        ratio_if_actually_inr = market_cap / revenue
    else:  # stated_currency == "INR"
        ratio_as_stated = market_cap / revenue
        ratio_if_actually_inr = None

    sane_low, sane_high = 0.5, 20

    stated_is_sane = sane_low <= ratio_as_stated <= sane_high

    if stated_is_sane:
        return stated_currency, False  # label looks fine, no override

    # Stated currency gives a nonsense ratio — check the alternative
    if stated_currency == "USD" and sane_low <= ratio_if_actually_inr <= sane_high:
        return "INR", True  # override: it's actually INR

    # Neither assumption is sane, or INR was already sane and still isn't — 
    # we can't confidently fix it, so return the original with no override
    return stated_currency, False


def calculate_fcff(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    financials = stock.financials
    cashflow = stock.cashflow
    info = stock.info

    stated_currency = info.get("financialCurrency")
    revenue = financials.loc["Total Revenue"].iloc[0]
    market_cap = info.get("marketCap")

    actual_currency, was_overridden = detect_actual_currency(
        revenue, market_cap, stated_currency
    )

    ebit = financials.loc["EBIT"].iloc[0]
    tax_rate = financials.loc["Tax Rate For Calcs"].iloc[0]
    depreciation = financials.loc["Reconciled Depreciation"].iloc[0]
    capex = cashflow.loc["Capital Expenditure"].iloc[0]
    change_in_nwc = cashflow.loc["Change In Working Capital"].iloc[0]

    fcff = ebit * (1 - tax_rate) + depreciation + capex + change_in_nwc

    return {
        "ticker": ticker_symbol,
        "fcff": fcff,
        "currency": actual_currency,
        "stated_currency": stated_currency,
        "currency_overridden": was_overridden
    }


if __name__ == "__main__":
    tickers = ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"]

    for ticker in tickers:
        result = calculate_fcff(ticker)
        fcff_inr = convert_to_inr(result["fcff"], result["currency"])

        note = ""
        if result["currency_overridden"]:
            note = f"  (currency auto-corrected: yfinance said {result['stated_currency']}, actually {result['currency']})"
        elif result["currency"] != "INR":
            note = "  (converted using today's spot FX rate — approximate)"

        print(f"{result['ticker']}: FCFF = {result['fcff']:,.0f} {result['currency']}  →  {fcff_inr:,.0f} INR{note}")