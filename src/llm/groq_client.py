# src/llm/groq_client.py
import logging
from config import get_settings
from groq import Groq
import asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

settings = get_settings()

class GroqClient:
    """
    Lightweight wrapper around Groq API for generating SQL from natural language prompts.

    Responsibilities:
    - Handle API key and model settings
    - Provide synchronous or async SQL generation
    - Log success/failure for debugging
    """

    def __init__(self, model: str = None):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set in settings")
        self.model = model or settings.GROQ_MODEL_NAME
        self.client = Groq(api_key=self.api_key)

    async def _generate_sql_async(self, prompt: str) -> str:
        """
        Internal async method to generate SQL via Groq.
        """
        try:
            # Send prompt to Groq chat endpoint
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model
            )
            sql = response.choices[0].message.content.strip()
            logger.info("Successfully generated SQL from Groq.")
            return sql
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    def generate_sql(self, prompt: str) -> str:
        """
        Synchronous wrapper to call the async Groq API method.
        Can be used directly in scripts without asyncio.
        """
        return asyncio.run(self._generate_sql_async(prompt))
