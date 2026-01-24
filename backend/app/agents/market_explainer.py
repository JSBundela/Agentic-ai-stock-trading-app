import json
from app.agents.core import llm_client, AgentModels
from app.market.service import market_service
from app.core.logger import logger
from typing import Dict, Any

class MarketExplainerAgent:
    SYSTEM_PROMPT = """
    You are a Senior Financial Analyst.
    
    CRITICAL FORMATTING RULE:
    - ALWAYS use bullet points ("-" character)
    - Maximum 3-4 bullets
    - Each bullet = one clear insight
    
    Example:
    - NIFTY down 241 points (-0.96%), bearish trend
    - Trading near day's low, weak momentum
    - Consider broader market sentiment
    
    ANALYSIS RULES:
    - >0.5% change = bullish | <-0.5% = bearish | else sideways
    - NO hallucinated news, stick to price data
    - NO trading recommendations
    """
    
    async def process(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        symbol_query = parameters.get("symbol", "NIFTY 50")
        
        # 1. Normalize Symbol (Basic mapping)
        # TODO: Use a proper scrip search in future. For now, map common indices.
        token = symbol_query
        if "nifty" in symbol_query.lower() and "bank" not in symbol_query.lower():
            token = "nse_cm|Nifty 50"
        elif "sensex" in symbol_query.lower():
            token = "bse_cm|SENSEX"
        elif "bank" in symbol_query.lower() and "nifty" in symbol_query.lower():
            token = "nse_cm|Nifty Bank"
        elif "|" not in symbol_query: 
            # If it's a stock name without token, we might fail or need a search. 
            # For now, let's try to assume it's a known token or return a specific message.
            # But the Orchestrator often extracts names like "RELIANCE". 
            # We'll rely on the user asking about Indices for now, or implement a lookup later.
            pass

        logger.info(f"MarketExplainer: Analyzing {token}")
        
        # 2. Fetch Live Data
        market_data = None
        try:
            # We put it in a list as get_quotes expects a list
            # Note: get_quotes expects "exchange|token". If we don't have it, we might fail.
            # Ideally we'd search scrip master here. 
            # For the MVP, let's assume it works for Indices primarily.
            quotes = await market_service.get_quotes([token])
            if quotes:
                market_data = quotes[0]
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            print(f"❌ [MarketExplainer] Data fetch error: {e}")
            return {"type": "text", "content": f"I couldn't fetch live data for **{symbol_query}**. Note: {str(e)}"}

        if not market_data:
             return {"type": "text", "content": f"Data unavailable for **{symbol_query}** right now."}

        # 3. Generate Explanation
        prompt = f"""
        Analyze this market data:
        Symbol: {market_data.get('tradingSymbol') or symbol_query}
        Price: {market_data.get('ltp')}
        Change: {market_data.get('netChange')} ({market_data.get('percentChange')}%)
        High: {market_data.get('high')}
        Low: {market_data.get('low')}
        
        User Question: "{parameters.get('original_query', 'Explain this')}"
        """
        
        response = await llm_client.chat_completion(
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            model=AgentModels.MARKET_EXPLAINER
        )
        
        if "error" in response:
             return {"type": "text", "content": "My analysis engine is briefly unavailable."}
             
        return {
            "type": "markdown",
            "content": response.get("content", "No analysis generated.")
        }

market_explainer = MarketExplainerAgent()
