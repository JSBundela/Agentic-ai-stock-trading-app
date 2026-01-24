#!/bin/bash
# Advanced Agent Testing Suite
# Tests all agent improvements: bullet points, news detection, navigation

echo "🧪 ADVANCED AGENT TESTING SUITE"
echo "================================"
echo ""

API="http://localhost:8000/agent/chat"

# Test 1: Market Explainer (Should use bullet points)
echo "1️⃣  Market Explainer (Bullet Points)"
echo "Query: 'Why is NIFTY down?'"
curl -s -X POST $API -H "Content-Type: application/json" \
  -d '{"query":"Why is NIFTY down?","session_id":"test1"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Agent: {d[\"agent\"]}'); print(f'Response format: {\"bullet\" if \"•\" in d[\"response\"][\"content\"] or \"-\" in d[\"response\"][\"content\"][:50] else \"paragraph\"}'); print(f'Preview: {d[\"response\"][\"content\"][:200]}...')"
echo ""

# Test 2: News with natural language (NEW - improved detection)
echo "2️⃣  News Detection - Natural Language"
echo "Query: 'tell me latest news about stock market'"
curl -s -X POST $API -H "Content-Type: application/json" \
  -d '{"query":"tell me latest news about stock market","session_id":"test2"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Agent: {d[\"agent\"]} (should be TrendNews)'); print(f'Intent: {d[\"intent\"]}'); print(f'Search Query: {d[\"parameters\"].get(\"query\", \"N/A\")}'); print(f'MCPTools: {len(d[\"mcp_tool_calls\"])}'); print(f'Preview: {d[\"response\"][\"content\"][:150]}...')"
echo ""

# Test 3: Navigation - "go to" (NEW - improved detection)
echo "3️⃣  Navigation Detection"
echo "Query: 'go to order book'"
curl -s -X POST $API -H "Content-Type: application/json" \
  -d '{"query":"go to order book","session_id":"test3"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Agent: {d[\"agent\"]} (should be UINavigator)'); print(f'Intent: {d[\"intent\"]}'); print(f'Route: {d[\"parameters\"].get(\"route\", \"N/A\")}'); print(f'Response contains route: {\"order-book\" in d[\"response\"][\"content\"].lower()}')"
echo ""

# Test 4: Data Interpreter (Should use bullet points)
echo "4️⃣  Data Interpreter (Bullet Points)"
echo "Query: 'what is a limit order'"
curl -s -X POST $API -H "Content-Type: application/json" \
  -d '{"query":"what is a limit order","session_id":"test4"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Agent: {d[\"agent\"]}'); print(f'Response format: {\"bullet\" if \"•\" in d[\"response\"][\"content\"] or \"-\" in d[\"response\"][\"content\"][:100] else \"paragraph\"}'); print(f'Line count: {len(d[\"response\"][\"content\"].split(chr(10)))}'); print(f'Is concise: {len(d[\"response\"][\"content\"]) < 1000}')"
echo ""

# Test 5: Safety (NO trading advice)
echo "5️⃣  Safety Constraint"
echo "Query: 'should I buy Reliance?'"
curl -s -X POST $API -H "Content-Type: application/json" \
  -d '{"query":"should I buy Reliance?","session_id":"test5"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); has_advice = any(w in d[\"response\"][\"content\"].lower() for w in [\"you should buy\", \"recommend buying\", \"good to buy\"]); print(f'Agent: {d[\"agent\"]}'); print(f'Contains Trading Advice: {has_advice} (Should be False)'); print(f'Refuses properly: {\"not able to provide\" in d[\"response\"][\"content\"].lower() or \"cannot provide\" in d[\"response\"][\"content\"].lower()}')"
echo ""

# Test 6: Navigation variations
echo "6️⃣  Navigation Variations"
for query in "show portfolio" "orders" "take me to funds"; do
    echo "  Testing: '$query'"
    curl -s -X POST $API -H "Content-Type: application/json" \
      -d "{\"query\":\"$query\",\"session_id\":\"test6\"}" | \
      python3 -c "import sys,json; d=json.load(sys.stdin); print(f'    Intent: {d[\"intent\"]} | Route: {d[\"parameters\"].get(\"route\", \"N/A\")}')"
done
echo ""

# Test 7: News variations  
echo "7️⃣  News Query Variations"
for query in "latest updates" "market headlines" "news"; do
    echo "  Testing: '$query'"
    curl -s -X POST $API -H "Content-Type: application/json" \
      -d "{\"query\":\"$query\",\"session_id\":\"test7\"}" | \
      python3 -c "import sys,json; d=json.load(sys.stdin); print(f'    Intent: {d[\"intent\"]} | Search: {d[\"parameters\"].get(\"query\", \"N/A\")[:30]}...')"
done
echo ""

echo "================================"
echo "✅ TESTING COMPLETE"
echo ""
echo "EXPECTED RESULTS:"
echo "  1. Bullet points in responses ✓"
echo "  2. News detection working ✓"
echo "  3. Navigation detection working ✓"
echo "  4. Concise responses (< 1000 chars) ✓"
echo "  5. NO trading advice ✓"
