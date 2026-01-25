from app.config import get_settings
from app.core.logger import logger
import httpx
import json
import re
from typing import List, Dict, Any, Optional

class AgentModels:
    ORCHESTRATOR = "anthropic/claude-3.5-sonnet" # Powerful reasoning
    MARKET_EXPLAINER = "meta-llama/llama-3.3-70b-instruct"   # Reliable and fast
    TREND_ANALYSIS = "meta-llama/llama-3.1-70b-instruct"
    UI_NAVIGATION = "meta-llama/llama-3.1-8b-instruct" # Fast/Cheap

def format_as_bullets(text: str) -> str:
    """
    Convert paragraph text to bullet points if not already formatted.
    """
    # If already has bullets, return as-is
    if '\n-' in text or '\n•' in text:
        return text
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    # Filter out very short sentences (< 10 chars) and empty ones
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    # If only 1-2 sentences, return as-is (too short for bullets)
    if len(sentences) <= 2:
        return text
    
    # Convert to bullets (max 5 points)
    bullets = sentences[:5]
    return '\n'.join(f'- {bullet}' for bullet in bullets)

class LLMClient:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            model: str,
                            temperature: float = 0.7,
                            max_tokens: int = 300,  # Reduced from 500 to force brevity
                            json_mode: bool = False) -> Dict[str, Any]:
        
        import time
        start_time = time.time()
        
        if not self.api_key:
            logger.error("OpenRouter API Key missing")
            raise ValueError("OpenRouter API Key is required")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AgenticAI Trading App",
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
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # Log metrics
                elapsed = time.time() - start_time
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                logger.info(f"[LLM] Model: {model} | Tokens: {tokens_used} | Time: {elapsed:.2f}s")
                
                return result
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"LLM Call Failed after {latency_ms:.2f}ms: {e}")
            return {"error": str(e)}

llm_client = LLMClient()
