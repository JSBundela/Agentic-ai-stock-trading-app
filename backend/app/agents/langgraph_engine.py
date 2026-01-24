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
from app.agents.core import llm_client, AgentModels
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
    intent: Optional[Literal["market_explainer", "trend_news", "data_interpreter", "ui_navigation", "debug"]]
    parameters: Dict[str, Any]
    
    # Agent execution
    mcp_tool_calls: List[Dict[str, Any]]
    agent_response: str
    agent_name: Optional[str]
    
    # Debug/observability
    debug_info: Optional[Dict[str, Any]]
    error: Optional[str]


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
      "intent": "market_explainer",
      "parameters": {"symbol": "NIFTY 50"}
    }
    
    Extract stock symbols, index names (NIFTY 50, SENSEX, etc.), or route names into parameters.
    For market_explainer: extract "symbol"
    For trend_news: extract "query" (search terms)
    For ui_navigation: extract "route" (/funds, /orders, etc.)
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        # Few-shot examples
        {"role": "user", "content": "Why is NIFTY down?"},
        {"role": "assistant", "content": '{"intent": "market_explainer", "parameters": {"symbol": "NIFTY 50"}}'},
        {"role": "user", "content": "Latest news on Reliance"},
        {"role": "assistant", "content": '{"intent": "trend_news", "parameters": {"query": "Reliance news"}}'},
        {"role": "user", "content": "What is margin?"},
        {"role": "assistant", "content": '{"intent": "data_interpreter", "parameters": {}}'},
        {"role": "user", "content": "Go to funds page"},
        {"role": "assistant", "content": '{"intent": "ui_navigation", "parameters": {"route": "/funds"}}'},
        # Actual user query
        {"role": "user", "content": state["user_query"]}
    ]
    
    try:
        response = await llm_client.chat_completion(
            messages=messages,
            model=AgentModels.ORCHESTRATOR,  # Claude Sonnet
            max_tokens=300,
            json_mode=True
        )
        
        result = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        
        # Debug: Log raw classifier output
        logger.info(f"[IntentClassifier] Raw LLM output: {result}")
        
        import json
        classification = json.loads(result)
        
        intent = classification.get("intent", "data_interpreter")
        parameters = classification.get("parameters", {})
        
        # HYBRID APPROACH: Keyword-based fallback override
        query_lower = state["user_query"].lower()
        
        # Market-related keywords
        market_keywords = ["nifty", "sensex", "stock", "price", "down", "up", "movement", "increase", "decrease", "rally", "fall"]
        market_questions = ["why", "explain", "what happened", "how come"]
        
        # If query asks "why/explain" + mentions market terms → force market_explainer
        has_market_term = any(keyword in query_lower for keyword in market_keywords)
        has_question = any(q in query_lower for q in market_questions)
        
        if has_market_term and has_question and intent == "data_interpreter":
            logger.info(f"[IntentClassifier] OVERRIDE: Keyword match detected, forcing market_explainer")
            intent = "market_explainer"
            # Extract symbol from query
            if "nifty" in query_lower:
                parameters["symbol"] = "NIFTY 50"
            elif "sensex" in query_lower:
                parameters["symbol"] = "SENSEX"
        
        # News keywords - improved to catch more variations
        news_keywords = ["news", "latest", "updates", "headlines", "reports", "trending"]
        news_contexts = ["stock market", "market", "trading", "stocks", "indices"]
        
        # Check if query asks for news (even with "tell me" or "about")
        has_news_keyword = any(keyword in query_lower for keyword in news_keywords)
        if has_news_keyword:
            logger.info(f"[IntentClassifier] OVERRIDE: News keyword detected, forcing trend_news")
            intent = "trend_news"
            # Extract search query - use everything after "about" if present, else use full query
            if " about " in query_lower:
                search_term = state["user_query"].split(" about ", 1)[1].strip()
            else:
                # Use generic "stock market" as search term
                search_term = "Indian stock market" if any(ctx in query_lower for ctx in news_contexts) else state["user_query"]
            parameters["query"] = search_term
        
        # Navigation keywords
        nav_keywords = ["go to", "goto", "navigate", "show", "open", "take me to"]
        nav_dest = ["portfolio", "orders", "order book", "orderbook", "funds", "dashboard", "home", "holdings", "positions"]
        
        # Map destinations to routes
        route_map = {
            "portfolio": "/portfolio",
            "orders": "/order-book",
            "order book": "/order-book",
            "orderbook": "/order-book",
            "funds": "/funds",
            "dashboard": "/",
            "home": "/",
            "holdings": "/portfolio",
            "positions": "/portfolio"
        }
        
        # Check for navigation intent
        has_nav_keyword = any(keyword in query_lower for keyword in nav_keywords)
        has_destination = any(dest in query_lower for dest in nav_dest)
        
        if has_nav_keyword or has_destination:
            logger.info(f"[IntentClassifier] OVERRIDE: Navigation detected, forcing ui_navigation")
            intent = "ui_navigation"
            # Find which destination
            for dest, route in route_map.items():
                if dest in query_lower:
                    parameters["route"] = route
                    break
            if "route" not in parameters:
                parameters["route"] = "/"
        
        state["intent"] = intent
        state["parameters"] = parameters
        
        logger.info(f"[IntentClassifier] Final Intent: {state['intent']}, Parameters: {state['parameters']}")
        
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
        if "NIFTY" in symbol.upper() or "SENSEX" in symbol.upper():
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
        if tool_result.get("success"):
            data = tool_result.get("data", {})
            
            # Build context for LLM
            context = f"""
            Market Data for {symbol}:
            - Last Price: {data.get('ltp') if isinstance(data, dict) else data[0].get('ltp')}
            - Change: {data.get('change') if isinstance(data, dict) else data[0].get('change')}
            - % Change: {data.get('percent_change') if isinstance(data, dict) else data[0].get('percent_change')}
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
            """
            
            messages = [
                {"role": "system", "content": safety_prompt},
                {"role": "user", "content": f"Query: {state['user_query']}\n\nData: {context}"}
            ]
            
            response = await llm_client.chat_completion(
                messages=messages,
                model=AgentModels.MARKET_EXPLAINER,
                max_tokens=500
            )
            
            state["agent_response"] = response.get("choices", [{}])[0].get("message", {}).get("content", "Data unavailable")
        else:
            state["agent_response"] = f"Unable to fetch data for {symbol}. {tool_result.get('errors', [''])}"
            
    except Exception as e:
        logger.error(f"[MarketExplainer] Failed: {e}")
        state["agent_response"] = f"Error processing market data: {str(e)}"
        state["error"] = str(e)
    
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
            """
            
            messages = [
                {"role": "system", "content": safety_prompt},
                {"role": "user", "content": f"Query: {state['user_query']}\n\nNews Articles:\n{news_context}"}
            ]
            
            response = await llm_client.chat_completion(
                messages=messages,
                model=AgentModels.TREND_ANALYSIS,
                max_tokens=500
            )
            
            state["agent_response"] = response.get("choices", [{}])[0].get("message", {}).get("content", "No news available")
        else:
            state["agent_response"] = f"No recent news found for '{query}'."
            
    except Exception as e:
        logger.error(f"[TrendNews] Failed: {e}")
        state["agent_response"] = f"Error fetching news: {str(e)}"
        state["error"] = str(e)
    
    return state


async def data_interpreter_node(state: AgentState) -> AgentState:
    """
    Explain trading terms, order statuses, and calculations.
    
    Uses MCP getOrders/getLimits for context if needed.
    """
    logger.info(f"[DataInterpreter] Processing query: {state['user_query']}")
    state["agent_name"] = "DataInterpreter"
    
    try:
        # Build educational prompt
        educational_prompt = """
        You are a trading education expert. Explain concepts clearly.
        
        STRICT RULES:
        - Explain WHAT terms mean (definitions)
        - Use examples where helpful
        - NO specific trading advice
        - If explaining calculations, show generic formulas
        - Be patient and thorough
        """
        
        messages = [
            {"role": "system", "content": educational_prompt},
            {"role": "user", "content": state["user_query"]}
        ]
        
        response = await llm_client.chat_completion(
            messages=messages,
            model=AgentModels.MARKET_EXPLAINER,
            max_tokens=500
        )
        
        state["agent_response"] = response.get("choices", [{}])[0].get("message", {}).get("content", "Unable to explain")
        
    except Exception as e:
        logger.error(f"[DataInterpreter] Failed: {e}")
        state["agent_response"] = f"Error processing query: {str(e)}"
        state["error"] = str(e)
    
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
            state["agent_response"] = f"Navigating to {route}"
        else:
            state["agent_response"] = "Unable to navigate"
            
    except Exception as e:
        logger.error(f"[UINavigation] Failed: {e}")
        state["agent_response"] = f"Navigation error: {str(e)}"
        state["error"] = str(e)
    
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
    Assemble final response for user.
    
    Formats agent output and adds metadata.
    """
    logger.info(f"[ResponseAssembler] Finalizing response from {state.get('agent_name')}")
    
    # Response is already in agent_response
    # Add any formatting if needed
    
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


# ==========================
# Routing Logic
# ==========================

def route_after_intent(state: AgentState) -> str:
    """
    Route to appropriate agent based on intent.
    """
    intent = state.get("intent", "data_interpreter")
    
    routing_map = {
        "market_explainer": "market_explainer",
        "trend_news": "trend_news",
        "data_interpreter": "data_interpreter",
        "ui_navigation": "ui_navigation",
        "debug": "debug_agent"
    }
    
    return routing_map.get(intent, "data_interpreter")


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
    
    # Add conditional routing after intent classification
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
    
    # All agents flow to response assembler
    for agent in ["market_explainer", "trend_news", "data_interpreter", "ui_navigation", "debug_agent"]:
        graph.add_edge(agent, "response_assembler")
    
    # Response assembler → Persistence → END
    graph.add_edge("response_assembler", "persistence")
    graph.add_edge("persistence", END)
    
    return graph.compile()


# Export compiled graph
agent_graph = build_agent_graph()
