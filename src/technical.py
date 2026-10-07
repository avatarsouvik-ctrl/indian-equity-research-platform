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


def add_macd(history, fast=12, slow=26, signal=9):
    history = history.copy()

    ema_fast = history["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = history["Close"].ewm(span=slow, adjust=False).mean()

    history["MACD"] = ema_fast - ema_slow
    history["MACD_Signal"] = history["MACD"].ewm(span=signal, adjust=False).mean()
    history["MACD_Histogram"] = history["MACD"] - history["MACD_Signal"]

    return history


if __name__ == "__main__":
    data = get_price_history("TCS.NS")
    data = add_moving_averages(data)
    data = add_rsi(data)
    data = add_macd(data)
    print(data[["Close", "MACD", "MACD_Signal", "MACD_Histogram"]].tail(10))