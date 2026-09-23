# Indian Equity Research & Valuation Platform

An automated equity research and DCF valuation platform for Indian listed companies, built as a learning project.

## Status: Early development (Phase 1)

Currently supports:
- Automated financial data retrieval via yfinance
- FCFF (Free Cash Flow to Firm) calculation
- Currency detection and correction (some Indian companies report financials in USD due to US ADR listings, and this is not always labeled correctly by data providers)

## Companies covered so far
TCS, Infosys, HCLTech, Wipro, Tech Mahindra

## Tech stack
Python, yfinance, pandas

## Data source note
Uses yfinance (unofficial Yahoo Finance wrapper), which is free but occasionally has data-quality quirks — see currency handling logic in `src/fundamentals.py` for one real example encountered and fixed during development.