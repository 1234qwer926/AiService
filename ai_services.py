import os
from typing import Dict, Any
import openai
from openai import OpenAI
from pydantic import BaseModel
from google import genai

class AIRequest(BaseModel):
    text: str
    model: str | None = None

class AIResponse(BaseModel):
    response: str
    model_used: str
    tokens: int = 0

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    async def analyze(self, text: str, model: str = "gpt-4o-mini") -> AIResponse:
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": text}]
        )
        return AIResponse(
            response=response.choices[0].message.content,
            model_used=model,
            tokens=response.usage.total_tokens if response.usage else 0
        )

class GeminiService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
    
    async def analyze(self, text: str, model: str = "gemini-1.5-flash") -> AIResponse:
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=text
        )
        return AIResponse(
            response=response.text,
            model_used=model
        )

class PerplexityService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
    
    async def analyze(self, text: str, model: str = "llama-3.1-sonar-small-128k-online") -> AIResponse:
        # Perplexity API implementation would go here
        # Using mock response for now
        return AIResponse(
            response=f"Perplexity analyzed: {text}",
            model_used=model
        )
