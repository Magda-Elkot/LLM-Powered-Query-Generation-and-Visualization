import asyncio
import logging
import os

from src.llm.llm_fallback_manager import LLMFallbackManager
from src.llm.groq_client import GroqClient
from src.llm.prompt_templates import build_sql_prompt
from src.validation.sql_validator import SQLValidator
from src.validation.query_sanitizer import QuerySanitizer
from src import ContextRetriever
from config import get_settings

# -------------------------------
# Logging Setup
# -------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------
# Settings & Schema
# -------------------------------
settings = get_settings()
context_retriever = ContextRetriever(schema_json_path="config/schema_metadata.json")
tables = context_retriever.get_table_names()
logger.info(f"Tables found: {tables}")

# Generate textual schema for LLM prompts
schema_text = context_retriever.generate_schema_text(tables)

# -------------------------------
# User Question & Prompt
# -------------------------------
user_question = "the subscribers used each product in January 2024?"
prompt = build_sql_prompt(user_question, schema_text)
logger.info("Prompt constructed for LLM.")

# -------------------------------
# Offline model path (fallback)
# -------------------------------
offline_model_path = os.path.abspath(
    "./models/distilgpt2/models--distilgpt2/snapshots/2290a62682d06624634c1f46a6ad5be0f47f38aa"
)

# -------------------------------
# Initialize SQL Validator
# -------------------------------
validator = SQLValidator()

# -------------------------------
# Async main
# -------------------------------
async def main():
    groq_client = GroqClient(model=settings.GROQ_MODEL_NAME)
    sql_query = None

    try:
        # Generate SQL via Groq API
        sql_query = await asyncio.to_thread(groq_client.generate_sql, prompt)

        # Strip code blocks if present
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0].strip()

        # Sanitize SQL
        sql_query = QuerySanitizer.sanitize(sql_query)

        # Validate SQL (blocks destructive statements)
        validator.validate(sql_query)

        logger.info(
            "\n\n================= SQL OUTPUT (Groq) =================\n%s\n====================================================\n",
            sql_query
        )

    except Exception as e:
        # If validation blocked the query (DELETE/UPDATE/INSERT/CREATE), stop here
        if "Only SELECT statements allowed" in str(e):
            logger.warning("SQL validation failed: %s", e)
            logger.info("Only SELECT statements are allowed. The SQL will not be executed.")
            return

        # Otherwise, fallback to offline LLM (API/network issues, rate limits, etc.)
        logger.warning("Groq API failed, falling back to offline LLM: %s", e)

        fallback_llm = LLMFallbackManager(model_path=offline_model_path)
        offline_prompt = prompt

        # Truncate prompt to fit offline model max tokens
        max_tokens = 1024
        prompt_tokens = fallback_llm.tokenizer.encode(offline_prompt)
        if len(prompt_tokens) > max_tokens:
            logger.warning("Prompt too long for offline model, truncating to last %d tokens.", max_tokens)
            prompt_tokens = prompt_tokens[-max_tokens:]
            offline_prompt = fallback_llm.tokenizer.decode(prompt_tokens)

        # Generate SQL offline
        sql_query_offline = await fallback_llm.generate_sql(offline_prompt)

        # Strip code blocks
        if "```sql" in sql_query_offline:
            sql_query_offline = sql_query_offline.split("```sql")[1].split("```")[0].strip()

        # Sanitize and validate offline SQL
        try:
            sql_query_offline = QuerySanitizer.sanitize(sql_query_offline)
            validator.validate(sql_query_offline)

            logger.info(
                "\n\n================= SQL OUTPUT (Offline) =================\n%s\n========================================================\n",
                sql_query_offline
            )
        except Exception as ve:
            logger.error("Offline SQL failed validation: %s", ve)
            logger.info("SQL output (unvalidated) will not be used.")


if __name__ == "__main__":
    asyncio.run(main())
