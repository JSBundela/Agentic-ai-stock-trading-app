# Agent Tool Validation Report

**Test Date:** 2026-01-26 09:50:55

## Summary

| Tool | Tests | Passed | Failed | Success Rate |
|------|-------|--------|--------|--------------|
| ✅ getIndexQuotes | 3 | 3 | 0 | 100.0% |
| ❌ getQuotes | 3 | 0 | 3 | 0.0% |
| ✅ getMarketDepth | 1 | 1 | 0 | 100.0% |
| ✅ searchNews | 3 | 3 | 0 | 100.0% |
| ✅ getLimits | 3 | 3 | 0 | 100.0% |
| ✅ getPositions | 2 | 2 | 0 | 100.0% |
| ✅ getWebSocketStatus | 2 | 2 | 0 | 100.0% |
| ❌ navigateTo | 3 | 0 | 3 | 0.0% |
| **TOTAL** | **20** | **14** | **6** | **70.0%** |

---

## Detailed Validation Results

### getIndexQuotes

#### ✅ Query: "Why is NIFTY 50 down today?"

- ✅ Tool 'getIndexQuotes' was called correctly
- ✅ Response has meaningful content (418 chars)

#### ✅ Query: "What happened to SENSEX?"

- ✅ Tool 'getIndexQuotes' was called correctly
- ✅ Response has meaningful content (393 chars)

#### ✅ Query: "Show me NIFTY BANK price"

- ✅ Tool 'getIndexQuotes' was called correctly
- ✅ Response has meaningful content (368 chars)

---

### getQuotes

#### ❌ Query: "Tell me about RELIANCE stock"

- ❌ Expected tool 'getQuotes' was not called. Tools called: []
- ✅ Response has meaningful content (715 chars)

#### ❌ Query: "What's HDFC price?"

- ❌ Expected tool 'getQuotes' was not called. Tools called: ['getIndexQuotes']
- ✅ Response has meaningful content (598 chars)

#### ❌ Query: "Show me INFY details"

- ❌ Expected tool 'getQuotes' was not called. Tools called: []
- ✅ Response has meaningful content (541 chars)

---

### getMarketDepth

#### ✅ Query: "What is the market depth for NIFTY 50?"

- ✅ Tool 'getMarketDepth' was called correctly
- ✅ Response has meaningful content (657 chars)

---

### searchNews

#### ✅ Query: "Latest news on Reliance"

- ✅ Tool 'searchNews' was called correctly
- ✅ Response has meaningful content (724 chars)

#### ✅ Query: "Tell me recent updates about Indian stock market"

- ✅ Tool 'searchNews' was called correctly
- ✅ Response has meaningful content (47 chars)

#### ✅ Query: "Any news on Tata Motors?"

- ✅ Tool 'searchNews' was called correctly
- ✅ Response has meaningful content (587 chars)

---

### getLimits

#### ✅ Query: "What's my available margin?"

- ✅ Tool 'getLimits' was called correctly
- ✅ Response has meaningful content (516 chars)

#### ✅ Query: "Show me my account balance"

- ✅ Tool 'getLimits' was called correctly
- ✅ Response has meaningful content (73 chars)

#### ✅ Query: "How much cash do I have?"

- ✅ Tool 'getLimits' was called correctly
- ✅ Response has meaningful content (31 chars)

---

### getPositions

#### ✅ Query: "Show me my current positions"

- ✅ Tool 'getPositions' was called correctly
- ✅ Response has meaningful content (27 chars)

#### ✅ Query: "What are my open positions?"

- ✅ Tool 'getPositions' was called correctly
- ✅ Response has meaningful content (27 chars)

---

### getWebSocketStatus

#### ✅ Query: "Is the market data connection working?"

- ✅ Tool 'getWebSocketStatus' was called correctly
- ✅ Response has meaningful content (125 chars)

#### ✅ Query: "Check WebSocket status"

- ✅ Tool 'getWebSocketStatus' was called correctly
- ✅ Response has meaningful content (70 chars)

---

### navigateTo

#### ❌ Query: "Take me to the funds page"

- ❌ Expected tool 'navigateTo' was not called. Tools called: ['getLimits']
- ✅ Response has meaningful content (212 chars)

#### ❌ Query: "Go to orders section"

- ❌ Expected tool 'navigateTo' was not called. Tools called: []
- ✅ Response has meaningful content (52 chars)
- ⚠️  Error reported: getOrders requires arguments

#### ❌ Query: "Navigate to dashboard"

- ❌ Expected tool 'navigateTo' was not called. Tools called: []
- ✅ Response has meaningful content (193 chars)

---

