# scripts/test_llm_query.py
import asyncio
import logging
import pandas as pd

from config import get_settings

from src import (
    SchemaManager,
    ContextRetriever,
    DBConnector,
    QueryExecutor,
    GroqClient,
    build_sql_prompt,
    LLMFallbackManager,
    QuerySanitizer,
    SQLValidator,
    infer_chart,
    ChartSpec,
    render,
)


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
user_question = "i need all the subscribers used each product in January 2024?"
prompt = build_sql_prompt(user_question, schema_text)
logger.info("Prompt constructed for LLM.")

# -------------------------------
# Initialize SQL Validator
# -------------------------------
validator = SQLValidator()
fallback_llm = LLMFallbackManager()

# -------------------------------
# Async main
# -------------------------------
async def main():
    groq_client = GroqClient(model=settings.GROQ_MODEL_NAME)
    sql_query = None

    try:
        # Generate SQL via Groq API
        sql_query = await asyncio.to_thread(groq_client.generate_sql, prompt)
        sql_query = QuerySanitizer.sanitize(sql_query)
        validator.validate(sql_query)
        logger.info("SQL generated (Groq API):\n%s", sql_query)

    except Exception as e:
        # Use fallback LLM for any Groq API/network errors
        logger.warning("Groq API failed, using fallback LLM: %s", e)
        sql_query = fallback_llm.generate_sql(prompt)
        logger.info("SQL generated (Fallback LLM):\n%s", sql_query)

    # -------------------------------
    # Execute SQL
    # -------------------------------
    db = DBConnector()
    executor = QueryExecutor(db)
    try:
        df: pd.DataFrame = executor.execute(sql_query)
        logger.info("Query returned %d rows", len(df))
        logger.info("\nData Preview:\n%s", df.head())
    except Exception as e:
        logger.error("SQL execution failed: %s", e)
        return

    # -------------------------------
    # Infer chart type and render
    # -------------------------------
    spec = infer_chart(df, user_question=user_question, sql_query=sql_query)
    logger.info("Inferred chart spec: %s", spec)

    chart_output = render(df, spec, backend="quickchart")
    logger.info("Chart URL: %s", chart_output.get("url"))

    # Print results
    print("\n===== SQL =====")
    print(sql_query)
    print("\n===== Data Preview =====")
    print(df.head())
    print("\n===== Chart URL =====")
    print(chart_output.get("url"))


if __name__ == "__main__":
    asyncio.run(main())
