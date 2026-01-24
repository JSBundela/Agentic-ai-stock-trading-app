from app.agents.core import llm_client, AgentModels
from app.core.logger import logger
from typing import Dict, Any

class DataInterpreterAgent:
    SYSTEM_PROMPT = """
    You are an Expert Trading Educator and Data Analyst.
    
    CRITICAL FORMATTING RULE:
    - ALWAYS use bullet points ("-" character)
    - Maximum 5 bullets per response
    - Each bullet = one concise sentence
    - NO long paragraphs
    
    Example format:
    - First key point here
    - Second important detail
    - Third supporting fact
    
    CAPABILITIES:
    - Explain Order Types (Limit, Market, SL, AMO)
    - Explain Order Statuses and rejections
    - Define trading terms (P&L, MTM, Holdings)
    
    CRITICAL: NO TRADING ADVICE. Refuse politely if asked "should I buy/sell?".
    """
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user query about data interpretation.
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\nContext: {context or {}}"}
        ]
        
        return await llm_client.chat_completion(
            messages=messages,
            model=AgentModels.MARKET_EXPLAINER # Use faster model for explanations
        )

data_interpreter_agent = DataInterpreterAgent()
