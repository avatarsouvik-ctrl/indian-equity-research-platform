import yfinance as yf
import math

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
    ebit = financials.loc["EBIT"].iloc[0]
    total_assets = balance_sheet.loc["Total Assets"].iloc[0]
    current_liabilities = balance_sheet.loc["Current Liabilities"].iloc[0]

    total_debt_inr = convert_to_inr(total_debt, actual_currency)
    cash_inr = convert_to_inr(cash, actual_currency)
    ebitda_inr = convert_to_inr(ebitda, actual_currency)
    stockholders_equity_inr = convert_to_inr(stockholders_equity, actual_currency)
    ebit_inr = convert_to_inr(ebit, actual_currency)
    total_assets_inr = convert_to_inr(total_assets, actual_currency)
    current_liabilities_inr = convert_to_inr(current_liabilities, actual_currency)

    debt_to_equity = total_debt_inr / stockholders_equity_inr
    enterprise_value = market_cap + total_debt_inr - cash_inr
    ev_to_ebitda = enterprise_value / ebitda_inr

    capital_employed = total_assets_inr - current_liabilities_inr
    roce = ebit_inr / capital_employed

    return {
        "ticker": ticker_symbol,
        "revenue": revenue,
        "ebitda": ebitda,
        "net_income": financials.loc["Net Income"].iloc[0],
        "eps": financials.loc["Diluted EPS"].iloc[0],
        "roe": info.get("returnOnEquity"),
        "roce": roce,
        "debt_to_equity": debt_to_equity,
        "pe_ratio": info.get("trailingPE"),
        "ev_to_ebitda": ev_to_ebitda,
        "profit_margin": info.get("profitMargins"),
        "currency": actual_currency,
        "currency_overridden": was_overridden
    }


def get_historical_growth_rates(ticker_symbol):
    """
    Calculates year-over-year revenue growth rates from the available
    historical data. Some companies have missing (NaN) revenue for
    their oldest available year, which would produce an invalid NaN
    growth rate -- we filter those out before picking bear/base/bull.
      bear = lowest (most conservative) valid growth rate
      bull = highest valid growth rate
      base = the middle valid value
    """
    stock = yf.Ticker(ticker_symbol)
    financials = stock.financials
    revenue_row = financials.loc["Total Revenue"]

    revenues = revenue_row.iloc[::-1].tolist()

    growth_rates = []
    for i in range(1, len(revenues)):
        previous = revenues[i - 1]
        current = revenues[i]
        growth = (current - previous) / previous
        growth_rates.append(growth)

    valid_rates = [rate for rate in growth_rates if not math.isnan(rate)]
    sorted_rates = sorted(valid_rates)

    return {
        "all_growth_rates": growth_rates,
        "bear": sorted_rates[0],
        "base": sorted_rates[len(sorted_rates) // 2],
        "bull": sorted_rates[-1]
    }


def get_dcf_inputs(ticker_symbol):
    """
    Fetches everything a DCF needs from the data source, ONCE, and
    puts it all in INR. No assumptions are applied here.
    """
    stock = yf.Ticker(ticker_symbol)
    balance_sheet = stock.balance_sheet
    financials = stock.financials

    fcff_result = calculate_fcff(ticker_symbol)
    currency = fcff_result["currency"]

    return {
        "ticker": ticker_symbol,
        "currency": currency,
        "fcff_year_0": convert_to_inr(fcff_result["fcff"], currency),
        "total_debt": convert_to_inr(balance_sheet.loc["Total Debt"].iloc[0], currency),
        "cash": convert_to_inr(balance_sheet.loc["Cash And Cash Equivalents"].iloc[0], currency),
        "shares_outstanding": financials.loc["Diluted Average Shares"].iloc[0],
    }


def run_dcf_math(inputs, growth_rate, wacc, terminal_growth, projection_years=5):
    """
    Pure calculation: no downloading. Takes the inputs from
    get_dcf_inputs() plus the assumptions, and returns the valuation.
    Returns None if the assumptions are mathematically invalid
    (WACC must be greater than terminal growth).
    """
    if wacc <= terminal_growth:
        return None

    pv_of_explicit_fcff = 0
    fcff_current = inputs["fcff_year_0"]

    for year in range(1, projection_years + 1):
        fcff_current = fcff_current * (1 + growth_rate)
        discount_factor = (1 + wacc) ** year
        pv_of_explicit_fcff += fcff_current / discount_factor

    fcff_year_after_projection = fcff_current * (1 + terminal_growth)
    terminal_value = fcff_year_after_projection / (wacc - terminal_growth)
    pv_of_terminal_value = terminal_value / ((1 + wacc) ** projection_years)

    enterprise_value = pv_of_explicit_fcff + pv_of_terminal_value
    equity_value = enterprise_value - inputs["total_debt"] + inputs["cash"]
    intrinsic_value_per_share = equity_value / inputs["shares_outstanding"]

    return {
        "growth_rate": growth_rate,
        "wacc": wacc,
        "terminal_growth": terminal_growth,
        "pv_of_explicit_fcff": pv_of_explicit_fcff,
        "pv_of_terminal_value": pv_of_terminal_value,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "intrinsic_value_per_share": intrinsic_value_per_share
    }


def build_sensitivity_grid(inputs, growth_rate, wacc_values, terminal_growth_values, projection_years=5):
    """
    Runs the DCF for every WACC x terminal-growth combination.
    Returns a list of rows (one per WACC), each row a list of
    intrinsic values per share (one per terminal growth value).
    A cell is None if that combination is invalid.
    """
    grid = []
    for wacc in wacc_values:
        row = []
        for terminal_growth in terminal_growth_values:
            result = run_dcf_math(inputs, growth_rate, wacc, terminal_growth, projection_years)
            row.append(None if result is None else result["intrinsic_value_per_share"])
        grid.append(row)
    return grid


def calculate_dcf(ticker_symbol, growth_rate, wacc=0.12, terminal_growth=0.04, projection_years=5):
    """
    Convenience wrapper: fetch inputs, then run the math once.
    """
    inputs = get_dcf_inputs(ticker_symbol)
    result = run_dcf_math(inputs, growth_rate, wacc, terminal_growth, projection_years)
    result["ticker"] = ticker_symbol
    return result


if __name__ == "__main__":
    for ticker in ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"]:
        data = get_fundamentals(ticker)
        print(f"{data['ticker']}: ROCE = {data['roce']*100:.1f}%")