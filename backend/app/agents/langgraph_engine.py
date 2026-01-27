"""
LangGraph Engine - Deterministic state graph for agent orchestration.

Replaces ad-hoc orchestration with a structured multi-agent workflow.

Graph Structure:
    UserInput → IntentClassifier → [Agent Nodes] → ResponseAssembler → Persistence
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.mcp import mcp_server
from app.agents.core import llm_client, AgentModels, format_as_bullets
from app.database.memory_repository import MemoryRepository
from app.core.logger import logger

# Initialize memory repository
memory_repository = MemoryRepository()


# ==========================
# State Schema
# ==========================

class AgentState(TypedDict):
    """
    State shared across all nodes in the graph.
    
    Each node reads from and writes to this state.
    """
    # Input
    user_query: str
    session_id: str
    chat_history: List[Dict[str, Any]]
    
    # Intent classification
    # Intent classification
    intent: Optional[str]  # Kept for backward compat
    intents: List[str]
    parameters: Dict[str, Any]
    
    # Agent execution
    mcp_tool_calls: List[Dict[str, Any]]
    agent_response: str
    agent_responses: Dict[str, str] # Store results from multiple agents
    agent_name: Optional[str]
    
    # Debug/observability
    debug_info: Optional[Dict[str, Any]]
    error: Optional[str]
    visited_intents: List[str]


# ==========================
# Node Implementations
# ==========================

async def intent_classifier_node(state: AgentState) -> AgentState:
    """
    Classify user intent and extract parameters.
    
    Uses Claude Sonnet for reasoning.
    """
    logger.info(f"[IntentClassifier] Processing query: {state['user_query']}")
    
    # Build system prompt with explicit examples
    system_prompt = """
    You are an intent classifier for a stock trading application.
    
    Classify the user's query into ONE of these intents:
    
    1. **market_explainer** - Questions about price movements, market data, or explaining WHY something happened
       Keywords: "why", "explain", "price", "up", "down", "movement", "NIFTY", "SENSEX", stock names
       Examples:
       - "Why is NIFTY down today?"
       - "Explain NIFTY 50 price movement"
       - "What happened to Reliance stock?"
       - "Why did Infosys go up?"
    
    2. **trend_news** - Requests for news, latest updates, or market trends
       Keywords: "news", "latest", "updates", "trends", "reports", "headlines"
       Examples:
       - "Latest news on HDFC Bank"
       - "Show me news about IT sector"
       - "What are the trending stocks?"
       - "Recent updates on Tata Motors"
    
    3. **data_interpreter** - Questions about trading concepts, terms, definitions, or calculations
       Keywords: "what is", "define", "meaning", "calculate", "how to", "margin", "order status"
       Examples:
       - "What is margin in trading?"
       - "Explain limit order"
       - "What does MTM mean?"
       - "How is P&L calculated?"
    
    4. **ui_navigation** - Commands to navigate or perform UI actions
       Keywords: "go to", "show", "take me", "open", "navigate", "page", "funds", "orders"
       Examples:
       - "Go to funds page"
       - "Show me my orders"
       - "Take me to dashboard"
       - "Open positions page"
    
    5. **debug** - Internal debugging (rarely triggered by users)
       Only use if query explicitly mentions debugging or system diagnostics
    
    **Decision Rules**:
    - If query asks "WHY" or "EXPLAIN" market movement → market_explainer
    - If query asks for "NEWS" or "LATEST" → trend_news
    - If query asks "WHAT IS" a concept → data_interpreter
    - If query says "GO TO" or names a page → ui_navigation
    - When in doubt between market_explainer and data_interpreter, choose market_explainer if query mentions specific stocks/indices
    
    Return JSON format:
    {
      "intents": ["market_explainer", "trend_news"],
      "parameters": {"symbol": "NIFTY 50", "query": "NIFTY 50 news"}
    }
    
    Examples:
    {"role": "user", "content": "Show me a chart of NIFTY and tell me news"},
    {"role": "assistant", "content": '{"intents": ["market_explainer", "trend_news"], "parameters": {"symbol": "NIFTY 50", "query": "NIFTY news"}}'},
    {"role": "user", "content": "Go to funds page"},
    {"role": "assistant", "content": '{"intents": ["ui_navigation"], "parameters": {"route": "/funds"}}'},
    
    Extract stock symbols, index names (NIFTY 50, SENSEX, etc.), or route names into parameters.
    For market_explainer: extract "symbol"
    For trend_news: extract "query" (search terms)
    For ui_navigation: extract "route" (/funds, /orders, etc.)
    """
    
    # 1. Build message list starting with System Prompt
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # 2. Add Chat History (limited to last 4 for context)
    if state.get("chat_history"):
        for msg in state["chat_history"][-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    # 3. Add current query
    messages.append({"role": "user", "content": state["user_query"]})
    
    try:
        response = await llm_client.chat_completion(
            messages=messages,
            model=AgentModels.ORCHESTRATOR,  # Claude Sonnet
            max_tokens=900,
            json_mode=True
        )
        
        result = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        
        # Debug: Log raw classifier output
        logger.info(f"[IntentClassifier] Raw LLM output: {result}")
        
        import json
        classification = json.loads(result)
        
        # 2. Extract initial intents from LLM output
        intents = classification.get("intents", [])
        if not intents and "intent" in classification:
            intents = [classification["intent"]]
        
        # Fallback to data_interpreter if nothing found
        if not intents:
            intents = ["data_interpreter"]
        
        intents = set(intents) # Use set for uniqueness during overrides
        
        parameters = classification.get("parameters", {})
        
        # HYBRID APPROACH: Keyword-based fallback override
        query_lower = state["user_query"].lower()
        
        # Market-related keywords
        market_keywords = [
            "nifty", "sensex", "stock", "price", "down", "up", "movement", 
            "increase", "decrease", "rally", "fall", "market", "share", 
            "bull", "bear", "crash", "correction", "high", "low", "red", "green",
            "reliance", "tata", "hdfc", "infosys", "icici", "sbi", "wipro", 
            "bajaj", "kotak", "mahindra", "adan"
        ]
        market_questions = ["why", "explain", "what happened", "how come", "analysis", "forecast", "view", "outlook", "what is", "show", "get", "check", "price", "movement", "quote", "about", "tell", "details"]
        
        # Individual stock symbols (not indices)
        stock_symbols = ["reliance", "tata", "hdfc", "infosys", "infy", "icici", "sbi", "wipro", "bajaj", "kotak", "mahindra", "adani"]
        
        # Calculate market term and question presence
        has_market_term = any(keyword in query_lower for keyword in market_keywords)
        has_question = any(q in query_lower for q in market_questions)
        
        # Check for individual stock queries (RELIANCE, HDFC, INFY etc.)
        has_stock_symbol = any(stock in query_lower for stock in stock_symbols)
        if has_stock_symbol:
            logger.info(f"[IntentClassifier] OVERRIDE: Stock symbol detected, add market_explainer")
            intents.add("market_explainer")
            if "data_interpreter" in intents and len(intents) > 1:
                intents.remove("data_interpreter")
        # Otherwise check for general market queries
        elif has_market_term and (has_question or len(state["user_query"].split()) <= 2):
            logger.info(f"[IntentClassifier] OVERRIDE: Market match detected (term + question/short query), add market_explainer")
            intents.add("market_explainer")
            if "data_interpreter" in intents and len(intents) > 1:
                intents.remove("data_interpreter")
        
        # Data related overrides (Orders/Status/Filter)
        data_keywords = ["rejected", "status", "working", "connected", "filter", "mis", "cnc", "nrml"]
        if any(k in query_lower for k in data_keywords):
            logger.info(f"[IntentClassifier] OVERRIDE: Data keyword detected, add data_interpreter")
            intents.add("data_interpreter")

        # Extract symbol from query
        if "market_explainer" in intents:
            if "nifty 50" in query_lower or ("nifty" in query_lower and "bank" not in query_lower):
                parameters["symbol"] = "NIFTY 50"
            elif "nifty bank" in query_lower:
                parameters["symbol"] = "NIFTY BANK"
            elif "sensex" in query_lower:
                parameters["symbol"] = "SENSEX"
            elif "reliance" in query_lower:
                parameters["symbol"] = "RELIANCE"
            elif "hdfc" in query_lower:
                parameters["symbol"] = "HDFCBANK"
            elif "tata" in query_lower:
                parameters["symbol"] = "TATAMOTORS"
            elif "infy" in query_lower or "infosys" in query_lower:
                parameters["symbol"] = "INFY"
            elif "icici" in query_lower:
                parameters["symbol"] = "ICICIBANK"
            elif "sbi" in query_lower:
                parameters["symbol"] = "SBIN"
        
        # News keywords
        news_keywords = ["news", "latest", "updates", "headlines", "reports", "trending", "current affairs"]
        has_news_keyword = any(keyword in query_lower for keyword in news_keywords)
        
        # News contexts (added news contexts if missing in previous content)
        news_contexts = ["market", "stocks", "economy", "india", "finance"]

        # Don't force news if it's just a symbol (like "RELIANCE news" vs "RELIANCE")
        if has_news_keyword and len(query_lower.split()) > 1:
            logger.info(f"[IntentClassifier] OVERRIDE: News keyword detected, add trend_news")
            intents.add("trend_news")
            if "data_interpreter" in intents and len(intents) > 1:
                intents.remove("data_interpreter")
            # Extract search query - use everything after "about" if present, else use full query
            if " about " in query_lower:
                search_term = state["user_query"].split(" about ", 1)[1].strip()
            else:
                # Use generic "stock market" as search term
                search_term = "Indian stock market" if any(ctx in query_lower for ctx in news_contexts) else state["user_query"]
            parameters["query"] = search_term
        
        
        # Navigation keywords - HIGH PRIORITY (check before checking destinations)
        nav_keywords = ["go to", "goto", "navigate", "take me to", "open", "show me the"]
        has_nav_keyword = any(keyword in query_lower for keyword in nav_keywords)
        
        if has_nav_keyword:
            logger.info(f"[IntentClassifier] OVERRIDE: Navigation keyword detected, add ui_navigation")
            intents.add("ui_navigation")
            if "data_interpreter" in intents and len(intents) > 1:
                intents.remove("data_interpreter")
        
        # Navigation destinations (expanded to match ALL sidebar tabs)
        nav_dest = [
            "portfolio", "orders", "order book", "orderbook", "order entry", 
            "funds", "dashboard", "home", "holdings", "positions", 
            "market watch", "marketwatch", "place order", "trading"
        ] 
        
        # Map destinations to routes (MUST match actual React Router paths)
        route_map = {
            "portfolio": "/portfolio",       # Portfolio page
            "holdings": "/portfolio",        # Alias for portfolio
            "positions": "/portfolio",       # Alias for portfolio
            "orders": "/order-book",         # Order Book page
            "order book": "/order-book",     # Order Book
            "orderbook": "/order-book",      # Order Book (no space)
            "order entry": "/order-entry",   # Place Order page
            "place order": "/order-entry",   # Alias for order entry
            "trading": "/order-entry",       # Alias for order entry
            "funds": "/funds",               # Funds & Limits
            "dashboard": "/dashboard",       # Main Dashboard
            "home": "/dashboard",            # Alias for dashboard
            "market watch": "/market-watch", # Market Watch (if exists)
            "marketwatch": "/market-watch"   # Market Watch (no space)
        }
        
        # Check for navigation intent
        has_nav_keyword = any(keyword in query_lower for keyword in nav_keywords)
        has_destination = any(dest in query_lower for dest in nav_dest)
        
        # Guard: Don't navigate if user is asking for specific data or filters
        is_data_query = any(k in query_lower for k in ["rejected", "filter", "mis", "position", "p&l", "profit", "loss", "mtm"])
        
        if (has_nav_keyword or has_destination) and not is_data_query:
            logger.info(f"[IntentClassifier] OVERRIDE: Navigation detected, forcing ui_navigation")
            intent = "ui_navigation"
            # Find which destination
            for dest, route in route_map.items():
                if dest in query_lower:
                    parameters["route"] = route
                    break
            if "route" not in parameters:
                parameters["route"] = "/"
        
        state["intents"] = list(intents)
        state["parameters"] = parameters
        state["visited_intents"] = []
        state["agent_responses"] = {}
        
        logger.info(f"[IntentClassifier] Final Intents: {state['intents']}, Parameters: {state['parameters']}")
        
    except Exception as e:
        logger.error(f"[IntentClassifier] Failed: {e}")
        state["intent"] = "data_interpreter"  # Fallback
        state["parameters"] = {}
        state["error"] = str(e)
    
    return state


async def market_explainer_node(state: AgentState) -> AgentState:
    """
    Explain market movements using live data.
    
    Uses MCP getQuotes/getIndexQuotes tools.
    """
    logger.info(f"[MarketExplainer] Processing query with params: {state['parameters']}")
    state["agent_name"] = "MarketExplainer"
    
    try:
        # Extract symbol from parameters
        symbol = state["parameters"].get("symbol", "NIFTY 50")
        
        # Call MCP tool
        # Check for Market Depth intent
        if any(k in state['user_query'].lower() for k in ["depth", "bids", "asks", "orderbook", "order book"]):
            tool_result = await mcp_server.call_tool("getMarketDepth", {"symbol": symbol})
            state["mcp_tool_calls"].append({
                "tool": "getMarketDepth",
                "args": {"symbol": symbol},
                "result": tool_result
            })
        # Removed chart generation to reduce tokens

        
        # Route to appropriate quote tool
        if symbol.upper() in ["NIFTY 50", "NIFTY BANK", "SENSEX", "NIFTY IT"]:
            tool_result = await mcp_server.call_tool("getIndexQuotes", {"index": symbol})
            state["mcp_tool_calls"].append({
                "tool": "getIndexQuotes",
                "args": {"index": symbol},
                "result": tool_result
            })
        else:
            tool_result = await mcp_server.call_tool("getQuotes", {"symbols": [symbol]})
            state["mcp_tool_calls"].append({
                "tool": "getQuotes",
                "args": {"symbols": [symbol]},
                "result": tool_result
            })
        
        # Extract data
        if tool_result.get("success") and tool_result.get("data") and (isinstance(tool_result["data"], dict) or len(tool_result["data"]) > 0):
            data = tool_result.get("data", {})
            
            # Build context for LLM
            ltp = data.get('ltp') if isinstance(data, dict) else (data[0].get('ltp') if data else 'Unknown')
            change = data.get('change') if isinstance(data, dict) else (data[0].get('change') if data else 'Unknown')
            p_change = data.get('percent_change') if isinstance(data, dict) else (data[0].get('percent_change') if data else 'Unknown')

            context = f"""
            Market Data for {symbol}:
            - Last Price: {ltp}
            - Change: {change}
            - % Change: {p_change}
            """
            
            # Generate explanation with safety constraints
            safety_prompt = """
            You are a market data analyst. Explain WHAT happened in the market.
            
            STRICT RULES:
            - Explain price movements descriptively
            - Use phrases like "Price increased by X%", "Market showed..."
            - NEVER say "good time to buy" or "sell now"
            - NO trading advice or recommendations
            - Be factual and objective
            - IMPORTANT: You ARE able to show charts and graphs via your tools. NEVER tell the user you are a "text-based model" or "cannot show images".
            """
            
            messages = [
                {"role": "system", "content": safety_prompt},
            ]
            
            # Add context from history
            if state.get("chat_history"):
                for msg in state["chat_history"][-2:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            messages.append({"role": "user", "content": f"Query: {state['user_query']}\n\nData: {context}"})
            
            response = await llm_client.chat_completion(
                messages=messages,
                model=AgentModels.MARKET_EXPLAINER,
                max_tokens=900
            )
            
            state["agent_responses"]["market_explainer"] = response.get("choices", [{}])[0].get("message", {}).get("content", "Data unavailable")
        else:
            state["agent_responses"]["market_explainer"] = f"Unable to fetch data for {symbol}. {tool_result.get('errors', [''])}"
            
    except Exception as e:
        logger.error(f"[MarketExplainer] Failed: {e}")
        state["agent_responses"]["market_explainer"] = f"Error processing market data: {str(e)}"
        state["error"] = str(e)
    
    state["visited_intents"].append("market_explainer")
    return state


async def trend_news_node(state: AgentState) -> AgentState:
    """
    Summarize news and market trends.
    
    Uses MCP searchNews tool.
    """
    logger.info(f"[TrendNews] Processing query with params: {state['parameters']}")
    state["agent_name"] = "TrendNews"
    
    try:
        # Build search query
        query = state["parameters"].get("query", state["user_query"])
        
        # Call MCP tool
        tool_result = await mcp_server.call_tool("searchNews", {
            "query": query,
            "max_results": 5
        })
        
        state["mcp_tool_calls"].append({
            "tool": "searchNews",
            "args": {"query": query},
            "result": tool_result
        })
        
        # Extract news articles
        if tool_result.get("success") and tool_result.get("count") > 0:
            articles = tool_result.get("data", [])
            
            # Format news for LLM
            news_context = "\n\n".join([
                f"**{art['title']}**\n{art['snippet']}\nSource: {art['source']}"
                for art in articles[:3]
            ])
            
            # Generate summary with safety constraints
            safety_prompt = """
            You are a financial news analyst. Summarize news objectively.
            
            STRICT RULES:
            - Summarize what happened (facts only)
            - NO predictions or forecasts
            - NO recommendations
            - Use phrases like "Reports indicate...", "News suggests..."
            - Be neutral and factual
            - IMPORTANT: You ARE able to show news summaries and headlines. NEVER tell the user you "cannot search the internet".
            """
            
            messages = [
                {"role": "system", "content": safety_prompt},
            ]
            
            # Add context from history
            if state.get("chat_history"):
                for msg in state["chat_history"][-2:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                    
            messages.append({"role": "user", "content": f"Query: {state['user_query']}\n\nNews Articles:\n{news_context}"})
            
            response = await llm_client.chat_completion(
                messages=messages,
                model=AgentModels.TREND_ANALYSIS,
                max_tokens=900
            )
            
            state["agent_responses"]["trend_news"] = response.get("choices", [{}])[0].get("message", {}).get("content", "No news available")
        else:
            state["agent_responses"]["trend_news"] = f"No recent news found for '{query}'."
            
    except Exception as e:
        logger.error(f"[TrendNews] Failed: {e}")
        state["agent_responses"]["trend_news"] = f"Error fetching news: {str(e)}"
        state["error"] = str(e)
    
    state["visited_intents"].append("trend_news")
    return state


async def data_interpreter_node(state: AgentState) -> AgentState:
    """
    Explain trading terms, order statuses, and calculations.
    
    Uses MCP getOrders/getLimits for context if needed.
    """
    logger.info(f"[DataInterpreter] Processing query: {state['user_query']}")
    state["agent_name"] = "DataInterpreter"
    
    try:
        query_lower = state['user_query'].lower()
        tool_results = {}
        tool_context = ""

        # 1. Check for Portfolio/Funds Intent
        if any(k in query_lower for k in ["funds", "cash", "limit", "margin", "balance", "available"]):
            res = await mcp_server.call_tool("getLimits", {})
            state["mcp_tool_calls"].append({"tool": "getLimits", "args": {}, "result": res})
            if res.get("success"):
                d = res.get("data", {})
                tool_context += f"\nFunds/Limits Data:\n- Cash Available: {d.get('cash_available')}\n- Margin Used: {d.get('margin_used')}\n"
        # 2. Check for Orders Intent
        if any(k in query_lower for k in ["orders", "rejected", "bids", "history", "executed", "open order", "buy order", "sell order"]):
            status = None
            if "rejected" in query_lower: status = "REJECTED"
            elif "executed" in query_lower or "completed" in query_lower: status = "COMPLETE"
            elif "open" in query_lower: status = "PENDING"
                
            res = await mcp_server.call_tool("getOrders", {"status": status} if status else None)
            state["mcp_tool_calls"].append({"tool": "getOrders", "args": {"status": status}, "result": res})
            
            if res.get("success"):
                orders = res.get("data", [])
                order_summary = "\n".join([
                    f"- {o.get('symbol')} ({o.get('status')}) {o.get('quantity')} qty @ {o.get('price')}"
                    for o in orders[:5]
                ])
                tool_context += f"\nRecent Orders:\n{order_summary if order_summary else 'No recent orders found matching criteria.'}\n"

        # 3. Check for Positions Intent
        if any(k in query_lower for k in ["positions", "holdings", "profit", "loss", "p&l", "mtm", "portfolio"]):
            res = await mcp_server.call_tool("getPositions", {})
            state["mcp_tool_calls"].append({"tool": "getPositions", "args": {}, "result": res})
            
            if res.get("success"):
                positions = res.get("data", [])
                pos_summary = "\n".join([
                    f"- {p.get('symbol')}: {p.get('quantity')} qty, P&L: {p.get('pnl')}"
                    for p in positions
                ])
                tool_context += f"\nOpen Positions:\n{pos_summary if pos_summary else 'No open positions.'}\n"

        # 4. Check for WebSocket Status Intent
        if any(k in query_lower for k in ["feed", "websocket", "connected", "working", "status", "connection"]):
            res = await mcp_server.call_tool("getWebSocketStatus", {})
            state["mcp_tool_calls"].append({"tool": "getWebSocketStatus", "args": {}, "result": res})
            if res.get("success"):
                d = res.get("data", {})
                tool_context += f"\nWebSocket Status:\n- Connected: {d.get('connected')}\n- Active Subscriptions: {d.get('active_subscriptions')}\n"

        # 5. Check for Apply Filter Intent
        if any(k in query_lower for k in ["filter", "only", "mis", "rejected orders"]):
            # Simulate filter params
            params = {}
            if "mis" in query_lower: params["product"] = "MIS"
            if "rejected" in query_lower: params["status"] = "REJECTED"
            
            if params:
                res = await mcp_server.call_tool("applyFilter", {"params": params})
                state["mcp_tool_calls"].append({"tool": "applyFilter", "args": {"params": params}, "result": res})
                if res.get("success"):
                    tool_context += f"\nApplied Filter: Successfully applied filter for {params}\n"

        # Build educational/analytical prompt with Data
        educational_prompt = f"""
        You are a trading assistant. 
        If specific data is provided below, answer the user's question FACTUALLY using that data.
        If NO data is provided, explain the concept generally (educational mode).
        
        DATA CONTEXT:
        {tool_context}
        
        STRICT RULES:
        - If data exists, cite it directly (e.g. "You have 2500 cash available").
        - If user asks about specific orders/positions and you see them, list them.
        - If explaining terms, be concise.
        """
        
        messages = [
            {"role": "system", "content": educational_prompt},
            {"role": "user", "content": state["user_query"]}
        ]
        
        response = await llm_client.chat_completion(
            messages=messages,
            model=AgentModels.MARKET_EXPLAINER,
            max_tokens=900
        )
        
        state["agent_responses"]["data_interpreter"] = response.get("choices", [{}])[0].get("message", {}).get("content", "Unable to explain")
        
    except Exception as e:
        logger.error(f"[DataInterpreter] Failed: {e}")
        state["agent_responses"]["data_interpreter"] = f"Error processing query: {str(e)}"
        state["error"] = str(e)
    
    state["visited_intents"].append("data_interpreter")
    return state


async def ui_navigation_node(state: AgentState) -> AgentState:
    """
    Handle UI navigation requests.
    
    Uses MCP navigateTo/applyFilter tools.
    """
    logger.info(f"[UINavigation] Processing query: {state['user_query']}")
    state["agent_name"] = "UINavigation"
    
    try:
        # Extract route from parameters
        route = state["parameters"].get("route", "/dashboard")
        
        # Call MCP tool
        tool_result = await mcp_server.call_tool("navigateTo", {"route": route})
        
        state["mcp_tool_calls"].append({
            "tool": "navigateTo",
            "args": {"route": route},
            "result": tool_result
        })
        
        if tool_result.get("success"):
            state["agent_responses"]["ui_navigation"] = f"Navigating to {route}"
        else:
            state["agent_responses"]["ui_navigation"] = "Unable to navigate"
            
    except Exception as e:
        logger.error(f"[UINavigation] Failed: {e}")
        state["agent_responses"]["ui_navigation"] = f"Navigation error: {str(e)}"
        state["error"] = str(e)
    
    state["visited_intents"].append("ui_navigation")
    return state


async def debug_agent_node(state: AgentState) -> AgentState:
    """
    Internal debugging node (not user-facing).
    
    Detects API ↔ UI mismatches.
    """
    logger.info(f"[DebugAgent] Running diagnostics")
    state["agent_name"] = "DebugAgent"
    
    # Placeholder: actual implementation would analyze API responses
    state["agent_response"] = "Debug mode not implemented for user queries"
    state["debug_info"] = {
        "mcp_tool_calls": len(state.get("mcp_tool_calls", [])),
        "intent": state.get("intent")
    }
    
    return state


async def response_assembler_node(state: AgentState) -> AgentState:
    """
    Assemble final response for user by combining results from multiple agents.
    """
    logger.info(f"[ResponseAssembler] Combining responses from {state.get('visited_intents')}")
    
    all_responses = []
    for intent_name in state.get("visited_intents", []):
        resp = state["agent_responses"].get(intent_name)
        if resp:
            all_responses.append(resp)
    
    if not all_responses:
        state["agent_response"] = "I processed your request but couldn't generate a specific response."
    else:
        state["agent_response"] = "\n\n---\n\n".join(all_responses)
    
    # Use first one as primary name
    state["agent_name"] = state["visited_intents"][0] if state["visited_intents"] else "Orchestrator"
    
    return state


async def persistence_node(state: AgentState) -> AgentState:
    """
    Save conversation to database.
    
    Persists user query and agent response.
    """
    logger.info(f"[Persistence] Saving to session: {state['session_id']}")
    
    try:
        # Save agent response
        await memory_repository.add_message(
            session_id=state["session_id"],
            role="assistant",
            content=state.get("agent_response", ""),
            agent_name=state.get("agent_name")
        )
    except Exception as e:
        logger.error(f"[Persistence] Failed to save: {e}")
    
    return state


def route_after_agent(state: AgentState) -> str:
    """
    Determine next intent or go to assembler.
    """
    pending = [i for i in state.get("intents", []) if i not in state.get("visited_intents", [])]
    
    if not pending:
        return "response_assembler"
    
    return pending[0]

def route_after_intent(state: AgentState) -> str:
    """
    Route to first agent.
    """
    if not state.get("intents"):
        return "data_interpreter"
    
    return state["intents"][0]


# ==========================
# Graph Construction
# ==========================

def build_agent_graph() -> StateGraph:
    """
    Build the LangGraph state machine.
    
    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("intent_classifier", intent_classifier_node)
    graph.add_node("market_explainer", market_explainer_node)
    graph.add_node("trend_news", trend_news_node)
    graph.add_node("data_interpreter", data_interpreter_node)
    graph.add_node("ui_navigation", ui_navigation_node)
    graph.add_node("debug_agent", debug_agent_node)
    graph.add_node("response_assembler", response_assembler_node)
    graph.add_node("persistence", persistence_node)
    
    # Set entry point
    graph.set_entry_point("intent_classifier")
    
    # Intent → First Agent
    graph.add_conditional_edges(
        "intent_classifier",
        route_after_intent,
        {
            "market_explainer": "market_explainer",
            "trend_news": "trend_news",
            "data_interpreter": "data_interpreter",
            "ui_navigation": "ui_navigation",
            "debug_agent": "debug_agent"
        }
    )
    
    # Agent → Next Agent or Response Assembler
    for agent in ["market_explainer", "trend_news", "data_interpreter", "ui_navigation", "debug_agent"]:
        graph.add_conditional_edges(
            agent,
            route_after_agent,
            {
                "market_explainer": "market_explainer",
                "trend_news": "trend_news",
                "data_interpreter": "data_interpreter",
                "ui_navigation": "ui_navigation",
                "debug_agent": "debug_agent",
                "response_assembler": "response_assembler"
            }
        )
    
    # Response assembler → Persistence → END
    graph.add_edge("response_assembler", "persistence")
    graph.add_edge("persistence", END)
    
    return graph.compile()


# Export compiled graph
agent_graph = build_agent_graph()
