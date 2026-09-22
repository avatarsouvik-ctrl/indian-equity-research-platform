import yfinance as yf

infy = yf.Ticker("INFY.NS")

print("--- Infosys Annual Financials ---")
print(infy.financials.index.tolist())

print("\n--- Infosys Cash Flow rows ---")
print(infy.cashflow.index.tolist())