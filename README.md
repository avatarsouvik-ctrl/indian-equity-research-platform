# Indian Equity Research & Valuation Platform

An automated equity research and DCF valuation platform for Indian listed companies, built as a learning project.

## Status: Working MVP (Phase 1 complete)

## Features

- Automated financial data retrieval via `yfinance` — no manual data entry
- Currency detection and correction: some Indian companies report financials in USD (due to US ADR listings), and this is not always labeled correctly by the data provider. The platform cross-checks reported currency against market cap and auto-corrects when the label is implausible.
- FCFF (Free Cash Flow to Firm) calculation, verified by hand against the formula `EBIT(1-T) + D&A - CapEx - ΔNWC`
- Core fundamentals: Revenue, EBITDA, Net Income, EPS, P/E, Debt/Equity, EV/EBITDA, Profit Margin — Debt/Equity and EV/EBITDA are calculated from raw balance sheet data rather than using `yfinance`'s pre-built ratios, which were found to be unreliable (see Known Issues below)
- DCF valuation with Bear/Base/Bull scenarios, where growth assumptions are derived from each company's own historical revenue growth rather than arbitrary guesses
- WACC × Terminal Growth sensitivity grid, showing how much the valuation depends on unobservable assumptions
- Interactive Streamlit dashboard with a company selector, live market price comparison, and upside/downside per scenario

## Companies covered so far
TCS, Infosys, HCLTech, Wipro, Tech Mahindra

## Tech stack
Python, yfinance, pandas, Streamlit

## Known data-quality issues found and fixed during development

- **Currency mismatch (Infosys):** `yfinance` correctly labels Infosys's financials as USD (due to its NYSE ADR listing), but naive code could easily combine USD figures with INR figures (e.g. market cap) without converting first. Fixed by converting all monetary inputs to INR before any calculation.
- **Currency mislabeling (HCLTech):** `yfinance` labels HCLTech's financials as USD, but the underlying figures are actually in INR. Detected by cross-checking Market Cap ÷ Revenue against a plausible Price/Sales range, and auto-corrected.
- **Percentage/decimal mismatch:** `yfinance`'s `debtToEquity` field for TCS returned 10.211, which would imply TCS is heavily indebted — contradicted by its real-world near-debt-free reputation. Rebuilding the ratio from raw balance sheet data (Total Debt ÷ Stockholders Equity) gave 0.105, the correct figure. `yfinance`'s pre-calculated ratio fields (`debtToEquity`, `enterpriseToEbitda`) were found to be unreliable in general; this project calculates these ratios from raw statement data instead.
- **Missing historical data (NaN):** Some companies have an incomplete oldest year of revenue data, which produced invalid `NaN` growth rates that could silently corrupt scenario selection. Fixed by filtering out invalid values before selecting Bear/Base/Bull.

## Known limitations

- **WACC (12%) and terminal growth (4%) are placeholder assumptions**, not derived from each company's actual capital structure, beta, or risk profile. The sensitivity grid is provided specifically so the valuation isn't read as a single precise number.
- **The DCF model only projects revenue growth; it does not model margin expansion or contraction.** For Tech Mahindra, even the most optimistic assumptions in the sensitivity grid (10% WACC, 5% terminal growth) produce a valuation well below the current market price — suggesting the market may be pricing in a margin recovery this model cannot capture, since margins are held constant.
- **Growth scenarios are derived from only 3-4 years of historical data.** For some companies (e.g. Wipro), this produces a Bear and Base case that are nearly identical, since two of the few available historical growth rates happen to be close together.
- Data is sourced from `yfinance`, an unofficial Yahoo Finance wrapper, not an official NSE/BSE data feed. Occasional data-quality issues (see above) are a known trade-off of using a free data source.

## Roadmap

- Technical analysis (moving averages, RSI, MACD)
- News and sentiment analysis
- CAPM-based WACC calculation per company
- Multi-stage DCF (high growth → fade period → terminal growth)
- Additional companies and sectors