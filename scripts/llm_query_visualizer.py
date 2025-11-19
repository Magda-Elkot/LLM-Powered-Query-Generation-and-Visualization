3 #scripts/llm_query_visualizer.py
import asyncio
import logging
import os
import pandas as pd

from config import get_settings

from src import (
    SchemaManager,
    ContextRetriever,
    DBConnector,
    QueryExecutor,
    GroqClient,
    build_sql_prompt,
    SQLValidator,
    QuerySanitizer,
    infer_chart,
    render,
    ChartSpec,
    LLMFallbackManager,
)


# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# -------------------------
# Load Schema
# -------------------------
context = ContextRetriever(schema_json_path="config/schema_metadata.json")
schema_text = context.generate_schema_text()

# -------------------------
# Offline fallback model (optional)
# -------------------------
OFFLINE_MODEL_PATH = os.path.abspath(
    "./models/distilgpt2/models--distilgpt2/snapshots/2290a62682d06624634c1f46a6ad5be0f47f38aa"
)

validator = SQLValidator()

# -------------------------
# MAIN EXECUTION
# -------------------------
async def run_visual_test(user_question: str):
    logger.info(f"User question: {user_question}")

    # Build prompt for Groq
    prompt = build_sql_prompt(user_question, schema_text)

    groq_client = GroqClient()

    try:
        # -------------------------
        # SQL FROM GROQ
        # -------------------------
        sql_query = await asyncio.to_thread(groq_client.generate_sql, prompt)
        sql_query = QuerySanitizer.sanitize(sql_query)
        validator.validate(sql_query)

        logger.info("\n===== SQL FROM GROQ =====\n%s\n=========================\n", sql_query)

    except Exception as e:
        logger.error(f"Groq failed: {e}")

        # Fallback only for API/network errors
        if any(k in str(e).lower() for k in ["api", "network", "connection", "timeout"]):
            logger.warning("Using OFFLINE fallback model...")

            fallback = LLMFallbackManager(OFFLINE_MODEL_PATH)

            offline_sql = await fallback.generate_sql(prompt)
            offline_sql = QuerySanitizer.sanitize(offline_sql)

            try:
                validator.validate(offline_sql)
                sql_query = offline_sql
                logger.info("\n===== SQL FROM OFFLINE MODEL =====\n%s\n=================================\n", sql_query)
            except Exception as e2:
                logger.error(f"Offline SQL invalid: {e2}")
                return None
        else:
            return None

    # -------------------------
    # Execute SQL
    # -------------------------
    db = DBConnector()
    executor = QueryExecutor(db)

    try:
        df: pd.DataFrame = executor.execute(sql_query)
        logger.info("\nReturned %d rows\n", len(df))
        logger.info("\nDataFrame:\n%s", df.head())

    except Exception as e:
        logger.error("SQL Execution failed: %s", e)
        return None

    # -------------------------
    # Infer chart type
    # -------------------------
    spec = infer_chart(df, user_question=user_question, sql_query=sql_query)
    logger.info("\nChart Spec: %s\n", spec)

    # -------------------------
    # Render chart using QuickChart.io
    # -------------------------
    chart_output = render(df, spec, backend="quickchart")

    logger.info("\n===== CHART URL =====\n%s\n=====================\n", chart_output["url"])

    return {
        "sql": sql_query,
        "chart_url": chart_output["url"],
        "chart_config": chart_output["config"],
        "chart_type": spec.chart_type,
        "data": df.head().to_dict(orient="records")
    }


# -------------------------
# DIRECT EXECUTION
# -------------------------
if __name__ == "__main__":
    question = "i want all the subscribers in 2024"
    asyncio.run(run_visual_test(question))
