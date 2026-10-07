import yfinance as yf


def get_price_history(ticker_symbol, period="1y"):
    stock = yf.Ticker(ticker_symbol)
    # auto_adjust=False: we want actual traded prices for technical
    # analysis (moving averages, RSI), not dividend/split-adjusted prices
    history = stock.history(period=period, auto_adjust=False)

    missing_price = history[history["Close"].isna()]
    if len(missing_price) > 0:
        print(f"{ticker_symbol}: {len(missing_price)} row(s) with missing Close -> {missing_price.index.tolist()}")

    history = history.dropna(subset=["Close"])
    return history


def add_moving_averages(history):
    history = history.copy()
    history["MA20"] = history["Close"].rolling(window=20).mean()
    history["MA50"] = history["Close"].rolling(window=50).mean()
    history["MA200"] = history["Close"].rolling(window=200).mean()
    return history


def add_rsi(history, period=14):
    history = history.copy()
    delta = history["Close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    history["RSI"] = 100 - (100 / (1 + rs))

    return history


if __name__ == "__main__":
    data = get_price_history("TCS.NS")
    data = add_moving_averages(data)
    data = add_rsi(data)
    print(data[["Close", "RSI"]].tail(10))