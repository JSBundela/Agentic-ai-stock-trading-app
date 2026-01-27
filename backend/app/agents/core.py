from app.config import get_settings
from app.core.logger import logger
import httpx
import json
import re
from typing import List, Dict, Any, Optional

class AgentModels:
    # Using Groq models (FREE & FAST!)
    ORCHESTRATOR = "llama-3.3-70b-versatile"     # Fast reasoning
    MARKET_EXPLAINER = "llama-3.3-70b-versatile" # Analysis
    TREND_ANALYSIS = "llama-3.1-70b-versatile"   # News
    UI_NAVIGATION = "llama-3.1-8b-instant"       # Ultra-fast navigation

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
        # Check for Groq API key (FREE & FAST)
        self.groq_key = self.settings.GROQ_API_KEY if hasattr(self.settings, 'GROQ_API_KEY') else None
        self.openrouter_key = self.settings.OPENROUTER_API_KEY
        
        if self.groq_key:
            logger.info("⚡ Using Groq API (FREE & BLAZINGLY FAST)")
            self.provider = "groq"
            self.api_key = self.groq_key
            self.base_url = "https://api.groq.com/openai/v1"
        else:
            logger.warning("⚠️ GROQ_API_KEY not found, falling back to OpenRouter (requires credits)")
            self.provider = "openrouter"
            self.api_key = self.openrouter_key
            self.base_url = "https://openrouter.ai/api/v1"
        
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            model: str,
                            temperature: float = 0.7,
                            max_tokens: int = 300,
                            json_mode: bool = False) -> Dict[str, Any]:
        
        import time
        start_time = time.time()
        
        if not self.api_key:
            logger.error("No API Key configured (neither GROQ nor OPENROUTER)")
            return {"error": "API Key missing"}
        
        # Groq uses OpenAI-compatible format, so same call works for both!
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "http://localhost:3000"
            headers["X-Title"] = "AgenticAI Trading App"
        
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
                provider_name = "Groq" if self.provider == "groq" else "OpenRouter"
                logger.info(f"[LLM] {provider_name} {model} | Tokens: {tokens_used} | Time: {elapsed:.2f}s")
                
                return result
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"LLM Call Failed after {latency_ms:.2f}ms: {e}")
            return {"error": str(e)}

llm_client = LLMClient()
