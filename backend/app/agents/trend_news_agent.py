from app.agents.core import llm_client, AgentModels
from app.core.logger import logger
from typing import Dict, Any, List

class TrendNewsAgent:
    SYSTEM_PROMPT = """
    You are a Senior Financial Market Analyst.
    
    CRITICAL FORMATTING RULE:
    - ALWAYS use bullet points ("-" character)
    - Maximum 5 bullets per response
    - Each bullet = one news item or insight
    - Include source when available
    
    Example:
    - Markets decline 2% on global concerns (Reuters)
    - IT sector leads losses, down 3.5%
    - Banking stocks hold steady
    
    CAPABILITIES:
    - Summarize market news concisely
    - Explain sector trends
    - Report market movements objectively
    
    CRITICAL: NO trading recommendations. Report news objectively only.
    """
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user query about trends/news.
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\nContext: {context or {}}"}
        ]
        
        return await llm_client.chat_completion(
            messages=messages,
            model=AgentModels.TREND_ANALYSIS
        )

trend_news_agent = TrendNewsAgent()
