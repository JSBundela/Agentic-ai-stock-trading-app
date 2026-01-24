from app.agents.core import llm_client, AgentModels
from app.core.logger import logger
from typing import Dict, Any

class OrchestratorAgent:
    SYSTEM_PROMPT = """
    You are the Orchestrator for a Professional Trading Platform AI.
    Your job is to specific user intent and route it to the correct specialized agent.
    
    AVAILABLE AGENTS:
    1. MARKET_EXPLAINER: Explains price movements, volume, volatility of specific stocks or indices.
       - Triggers: "Why is Nifty down?", "Explain Reliance price action", "What's happening with Tata Motors?"
    
    2. TREND_NEWS: Summarizes news and broad market trends.
       - Triggers: "Latest news on HDFC", "Market outlook", "Sector performance news"
       
    3. UI_NAVIGATION: Helps user navigate the app/website.
       - Triggers: "Go to funds", "Show open orders", "Where is the option chain?", "Open Dashboard"
       
    4. DATA_INTERPRETER: Explains trading terms, order statuses, or calculations.
       - Triggers: "What is margin?", "Why was order rejected?", "Calculate brokerage"
       
    5. GENERAL_CHAT: Simple greetings or out-of-scope non-trading questions.
    
    OUTPUT FORMAT (JSON ONLY):
    {
        "agent": "MARKET_EXPLAINER" | "TREND_NEWS" | "UI_NAVIGATION" | "DATA_INTERPRETER" | "GENERAL_CHAT",
        "confidence": 0.0-1.0,
        "parameters": {
            "symbol": "extracted symbol if any (e.g. RELIANCE, NIFTY 50)",
            "page": "extracted page name if any",
            "query": "refined query string"
        }
    }
    """
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ]
        
        logger.info(f"Orchestrator processing: {user_query}")
        
        response = await llm_client.chat_completion(
            messages=messages,
            model=AgentModels.ORCHESTRATOR,
            max_tokens=300,
            json_mode=True
        )
        
        if "error" in response:
            return {"agent": "ERROR", "message": response["error"]}
            
        return response

orchestrator = OrchestratorAgent()
