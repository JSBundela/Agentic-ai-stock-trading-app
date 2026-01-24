from app.config import get_settings
from app.core.logger import logger
import httpx
import json
from typing import List, Dict, Any, Optional

class AgentModels:
    ORCHESTRATOR = "anthropic/claude-3.5-sonnet" # Powerful reasoning
    MARKET_EXPLAINER = "meta-llama/llama-3.3-70b-instruct"   # Reliable and fast
    TREND_ANALYSIS = "meta-llama/llama-3.1-70b-instruct"
    UI_NAVIGATION = "meta-llama/llama-3.1-8b-instruct" # Fast/Cheap

class LLMClient:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            model: str,
                            temperature: float = 0.7,
                            max_tokens: int = 500,
                            json_mode: bool = False) -> Dict[str, Any]:
        
        import time
        start_time = time.time()
        
        if not self.api_key:
            logger.error("OpenRouter API Key missing")
            return {"error": "AI configuration missing"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://kotak-neo-agent.com",
            "X-Title": "Kotak Neo Agent",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"❌ [LLM Error] Status: {response.status_code}, Response: {error_text}")
                    logger.error(f"OpenRouter Error {response.status_code}: {error_text}")
                    return {"error": f"AI Service Error: {error_text}"}
                    
                result = response.json()
                
                # Extract token usage and log
                usage = result.get("usage", {})
                latency_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"[LLM] Model: {model} | "
                    f"Tokens: {usage.get('total_tokens', 'N/A')} "
                    f"(prompt: {usage.get('prompt_tokens', 'N/A')}, completion: {usage.get('completion_tokens', 'N/A')}) | "
                    f"Latency: {latency_ms:.2f}ms"
                )
                
                content = result['choices'][0]['message']['content']
                
                if json_mode:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON response: {content}")
                        return {"error": "Invalid JSON response from AI"}
                
                return result
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"LLM Call Failed after {latency_ms:.2f}ms: {e}")
            return {"error": str(e)}

llm_client = LLMClient()
