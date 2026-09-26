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
        return stated_currency, False

    fx_rate = get_usd_to_inr_rate()

    if stated_currency == "USD":
        ratio_as_stated = market_cap / (revenue * fx_rate)
        ratio_if_actually_inr = market_cap / revenue
    else:
        ratio_as_stated = market_cap / revenue
        ratio_if_actually_inr = None

    sane_low, sane_high = 0.5, 20
    stated_is_sane = sane_low <= ratio_as_stated <= sane_high

    if stated_is_sane:
        return stated_currency, False

    if stated_currency == "USD" and sane_low <= ratio_if_actually_inr <= sane_high:
        return "INR", True

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


def get_fundamentals(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    info = stock.info
    financials = stock.financials
    balance_sheet = stock.balance_sheet

    stated_currency = info.get("financialCurrency")
    revenue = financials.loc["Total Revenue"].iloc[0]
    market_cap = info.get("marketCap")

    actual_currency, was_overridden = detect_actual_currency(
        revenue, market_cap, stated_currency
    )

    total_debt = balance_sheet.loc["Total Debt"].iloc[0]
    stockholders_equity = balance_sheet.loc["Stockholders Equity"].iloc[0]
    cash = balance_sheet.loc["Cash And Cash Equivalents"].iloc[0]
    ebitda = financials.loc["EBITDA"].iloc[0]

    # Bring debt/cash/ebitda/equity into the same currency as market_cap
    # (INR) before combining them in any formula.
    total_debt_inr = convert_to_inr(total_debt, actual_currency)
    cash_inr = convert_to_inr(cash, actual_currency)
    ebitda_inr = convert_to_inr(ebitda, actual_currency)
    stockholders_equity_inr = convert_to_inr(stockholders_equity, actual_currency)

    debt_to_equity = total_debt_inr / stockholders_equity_inr
    enterprise_value = market_cap + total_debt_inr - cash_inr
    ev_to_ebitda = enterprise_value / ebitda_inr

    return {
        "ticker": ticker_symbol,
        "revenue": revenue,
        "ebitda": ebitda,
        "net_income": financials.loc["Net Income"].iloc[0],
        "eps": financials.loc["Diluted EPS"].iloc[0],
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": debt_to_equity,
        "pe_ratio": info.get("trailingPE"),
        "ev_to_ebitda": ev_to_ebitda,
        "profit_margin": info.get("profitMargins"),
        "currency": actual_currency,
        "currency_overridden": was_overridden
    }


if __name__ == "__main__":
    tickers = ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"]

    for ticker in tickers:
        data = get_fundamentals(ticker)
        flag = "  [auto-corrected]" if data["currency_overridden"] else ""
        print(f"\n{data['ticker']} ({data['currency']}{flag})")
        print(f"  Revenue: {data['revenue']:,.0f}")
        print(f"  EBITDA: {data['ebitda']:,.0f}")
        print(f"  Net Income: {data['net_income']:,.0f}")
        print(f"  EPS: {data['eps']}")
        print(f"  ROE: {data['roe']}")
        print(f"  Debt/Equity: {data['debt_to_equity']:.3f}")
        print(f"  P/E: {data['pe_ratio']}")
        print(f"  EV/EBITDA: {data['ev_to_ebitda']:.2f}")
        print(f"  Profit Margin: {data['profit_margin']}")