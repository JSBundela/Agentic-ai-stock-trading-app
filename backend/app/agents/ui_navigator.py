from app.agents.core import llm_client, AgentModels
from typing import Dict, Any

class UINavigationAgent:
    SYSTEM_PROMPT = """
    You are a UI Navigation Assistant for a Trading App.
    Map user natural language requests to specific internal application routes.
    
    ROUTES:
    - /dashboard : Dashboard, Home, Overview
    - /orders : Orders, Order Book, Order History, Open Orders, Trades
    - /positions : Portfolio, Positions, Holdings, P&L
    - /funds : Funds, Wallet, Balance, Add Money, Withdraw
    - /market-watch : Market, Search, Option Chain, Screeners
    
    OUTPUT FORMAT (JSON ONLY):
    {
        "route": "/route-path",
        "action": "OPTIONAL_ACTION_NAME",
        "message": "Brief confirmation message"
    }
    """
    
    async def process(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        query = parameters.get("query", "")
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Navigate me to: {query}"}
        ]
        
        return await llm_client.chat_completion(
            messages=messages,
            model=AgentModels.UI_NAVIGATION,
            json_mode=True
        )

ui_navigator = UINavigationAgent()
