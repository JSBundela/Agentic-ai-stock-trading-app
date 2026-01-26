# Agent Robustness Audit Report

| Query | Target Agent | Actual Agent | Target Tool | Status |
| :--- | :--- | :--- | :--- | :--- |
| What is the current price of RELIANCE? | MarketExplainer | MarketExplainer | getQuotes (getQuotes) | ✅ PASS |
| Show me the market depth for TCS. | MarketExplainer | MarketExplainer | getMarketDepth (getMarketDepth) | ✅ PASS |
| What is the latest news on HDFC Bank? | TrendNews | TrendNews | searchNews (searchNews) | ✅ PASS |
| How much cash do I have available? | DataInterpreter | DataInterpreter | getLimits (getLimits) | ✅ PASS |
| What are my current open positions? | DataInterpreter | DataInterpreter | getPositions (getPositions) | ✅ PASS |
| Go to the order book. | UINavigation | UINavigation | navigateTo (navigateTo) | ✅ PASS |
| Show me a chart of NIFTY 50. | MarketExplainer | MarketExplainer | generateChart (generateChart) | ✅ PASS |
