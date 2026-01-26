# Agent Robustness Test Report

**Date**: 2026-01-25 20:03:13
**Total Questions**: 34
**Passed**: 31
**Failed**: 3
**Success Rate**: 91.2%

## detailed Results

| ID | Question | Status | Agent Used | Tools Used | Latency |
|----|----------|--------|------------|------------|---------|
| 1 | What is the current price of RELIANCE-EQ? | PASS | DataInterpreter | None | 7.23s |
| 2 | Show me the market depth for TCS. | FAIL | UINavigation | None | 0.67s |
| 3 | Get me the quote for HDFCBANK. | PASS | DataInterpreter | None | 7.62s |
| 4 | How is NIFTY 50 performing right now? | PASS | DataInterpreter | None | 8.61s |
| 5 | Check the price of INFIBEAM. | PASS | DataInterpreter | None | 9.31s |
| 6 | What is the volume for TATAMOTORS? | PASS | DataInterpreter | None | 5.56s |
| 7 | Is SENSEX up or down today? | PASS | DataInterpreter | None | 14.19s |
| 8 | Get detailed quote for SBIN. | PASS | DataInterpreter | None | 26.44s |
| 9 | What is the latest news on Adani Enterprises? | PASS | TrendNews | searchNews | 4.91s |
| 10 | Find recent news about the IT sector. | PASS | TrendNews | searchNews | 6.16s |
| 11 | Any updates on RBI monetary policy? | PASS | TrendNews | searchNews | 6.66s |
| 12 | Search for news regarding electric vehicles in India. | PASS | TrendNews | searchNews | 8.58s |
| 13 | What is the news sentiment for Banking stocks? | PASS | TrendNews | searchNews | 4.08s |
| 14 | Latest announcements for Infosys. | PASS | TrendNews | searchNews | 6.13s |
| 15 | What is happening with Gold prices? | PASS | DataInterpreter | None | 14.97s |
| 16 | Take me to the dashboard. | PASS | UINavigation | navigateTo | 1.09s |
| 17 | Go to the order book. | PASS | UINavigation | navigateTo | 0.51s |
| 18 | I want to see my open positions. | PASS | UINavigation | navigateTo | 1.14s |
| 19 | Show me my funds and limits. | PASS | UINavigation | navigateTo | 0.82s |
| 20 | Navigate to the option chain. | FAIL | UINavigation | None | 0.68s |
| 21 | Open the profile settings. | FAIL | UINavigation | None | 0.54s |
| 22 | I want to place a new order. | PASS | DataInterpreter | None | 10.33s |
| 23 | Go back to the home page. | PASS | UINavigation | navigateTo | 0.70s |
| 24 | What is the difference between CNC and MIS? | PASS | DataInterpreter | None | 20.13s |
| 25 | Explain what a limit order is. | PASS | DataInterpreter | None | 9.66s |
| 26 | How is margin calculated? | PASS | DataInterpreter | None | 11.79s |
| 27 | What does market depth mean? | PASS | DataInterpreter | None | 14.42s |
| 28 | Why would an order be rejected? | PASS | DataInterpreter | None | 4.39s |
| 29 | What is a stop-loss order? | PASS | DataInterpreter | None | 14.55s |
| 30 | How much cash do I have available? | PASS | DataInterpreter | None | 12.27s |
| 31 | Show me my rejected orders. | PASS | UINavigation | navigateTo | 1.57s |
| 32 | What is my total P&L for today? | PASS | DataInterpreter | None | 7.29s |
| 33 | List all my executed orders. | PASS | UINavigation | navigateTo | 1.10s |
| 34 | Do I have any open buy orders? | PASS | UINavigation | navigateTo | 0.64s |

## Tool Utilization Strategy
The following tools were exercised during this test suite:
- None
- navigateTo
- searchNews
