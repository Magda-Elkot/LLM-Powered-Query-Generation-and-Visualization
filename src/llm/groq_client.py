# src/llm/groq_client.py
import logging
from config import get_settings
from groq import Groq
import asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

settings = get_settings()

class GroqClient:
    """Client to interact with Groq API for SQL generation."""

    def __init__(self, model: str = None):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set in settings")
        self.model = model or settings.GROQ_MODEL_NAME
        self.client = Groq(api_key=self.api_key)

    async def _generate_sql_async(self, prompt: str) -> str:
        try:
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
        return asyncio.run(self._generate_sql_async(prompt))
