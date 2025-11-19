# src/run_pipeline.py

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

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



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class PipelineResult:
    user_question: str
    sql_raw: str
    sql_clean: str
    df_preview: str       # df.head().to_string() or error message
    chart_spec: Optional[ChartSpec]
    chart_payload: Dict[str, Any]  # e.g. quickchart URL + config


class QueryOrchestrator:
    """
    High-level pipeline:
      question → schema context → LLM → SQL → sanitize + validate → execute → visualize

    Now with:
      - Primary Groq LLM
      - Safe fallback LLM (for API/network/rate-limit issues)
    """

    def __init__(
        self,
        schema_path: str = "config/schema_metadata.json",
        llm_client: Optional[GroqClient] = None,
    ):
        # Context / schema
        self.context = ContextRetriever(schema_json_path=schema_path)

        # Fallback LLM (simple offline/placeholder)
        self.fallback_llm = LLMFallbackManager()

        # Primary LLM (Groq). If it fails at init, we mark it unavailable.
        try:
            self.llm_client: Optional[GroqClient] = llm_client or GroqClient()
            self.primary_llm_available = True
        except Exception as e:
            logger.warning(
                "Primary LLM (Groq) unavailable at init, using fallback only. Error: %s",
                e,
            )
            self.llm_client = None
            self.primary_llm_available = False

        # Validator, sanitizer, DB connection, and query executor
        self.sanitizer = QuerySanitizer()
        self.validator = SQLValidator()
        self.db_connector = DBConnector()
        self.executor = QueryExecutor(self.db_connector)

    # ------------------------------------------------------------------ #
    # Helper: classify transient API errors (no internet / rate limit)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _is_transient_llm_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        network_keywords = [
            "connection error",
            "connection aborted",
            "connection refused",
            "connection reset",
            "network is unreachable",
            "name or service not known",
            "temporary failure in name resolution",
            "failed to establish a new connection",
            "max retries exceeded",
            "timeout",
            "timed out",
            "ssl",
        ]
        rate_limit_keywords = [
            "rate limit",
            "too many requests",
            "status code: 429",
            "http 429",
        ]
        if any(k in msg for k in network_keywords):
            return True
        if any(k in msg for k in rate_limit_keywords):
            return True
        return False

    # ------------------------------------------------------------------ #
    # Helper: generate SQL, with primary + fallback
    # ------------------------------------------------------------------ #
    def _generate_sql_with_fallback(self, prompt: str) -> str:
        """
        Generate SQL using Groq LLM; switch to fallback if primary is unavailable or transient error occurs.
        """
        if not self.primary_llm_available or self.llm_client is None:
            logger.info("Primary LLM not available at init. Using fallback directly.")
            return self.fallback_llm.generate_sql(prompt)

        try:
            return self.llm_client.generate_sql(prompt)
        except Exception as e:
            if self._is_transient_llm_error(e):
                logger.error(
                    "Primary LLM failed due to network / rate-limit issue. "
                    "Switching to fallback. Error: %s",
                    e,
                )
                return self.fallback_llm.generate_sql(prompt)
            logger.error("Primary LLM failed with non-transient error: %s", e)
            raise

    # ------------------------------------------------------------------ #
    # Main pipeline execution
    # ------------------------------------------------------------------ #
    def run(self, user_question: str) -> PipelineResult:
        """
        Run the full pipeline for a single user question.

        Returns:
            PipelineResult containing SQL, DataFrame preview, chart specification, and rendered chart.
        """

        # 1) Build schema text for the prompt
        schema_text = self.context.generate_schema_text()

        # 2) Build LLM prompt
        prompt = build_sql_prompt(user_question=user_question, schema_text=schema_text)

        # 3) Generate SQL via LLM (with fallback only on API/network/rate-limit)
        try:
            sql_raw = self._generate_sql_with_fallback(prompt)
        except Exception as e:
            msg = f"Primary LLM error (non-transient): {e}"
            logger.error(msg)
            chart_payload = {
                "backend": "quickchart",
                "config": {"type": "table", "data": {}, "message": msg},
                "url": "",
            }
            return PipelineResult(
                user_question=user_question,
                sql_raw="",
                sql_clean="",
                df_preview=msg,
                chart_spec=None,
                chart_payload=chart_payload,
            )

        # 4) Validate immediately (block destructive queries)
        try:
            self.validator.validate(sql_raw)
        except ValueError as e:
            chart_payload = {
                "backend": "quickchart",
                "config": {"type": "table", "data": {}, "message": str(e)},
                "url": "",
            }
            return PipelineResult(
                user_question=user_question,
                sql_raw=sql_raw,
                sql_clean="",
                df_preview=str(e),
                chart_spec=None,
                chart_payload=chart_payload,
            )

        # 5) Sanitize
        sql_clean = self.sanitizer.sanitize(sql_raw)

        # 6) Execute with error handling
        try:
            df = self.executor.execute(sql_clean)
        except Exception as e:
            logger.error("Query execution failed: %s", e)
            fallback_sql_raw = self.fallback_llm.generate_sql(prompt)
            sql_raw = fallback_sql_raw
            sql_clean = self.sanitizer.sanitize(fallback_sql_raw)
            try:
                self.validator.validate(sql_clean)
                df = self.executor.execute(sql_clean)
            except Exception as e2:
                msg = f"Query execution failed: {e}. Fallback also failed: {e2}"
                logger.error(msg)
                chart_payload = {
                    "backend": "quickchart",
                    "config": {"type": "table", "data": {}, "message": msg},
                    "url": "",
                }
                return PipelineResult(
                    user_question=user_question,
                    sql_raw=sql_raw,
                    sql_clean=sql_clean,
                    df_preview="Query execution failed",
                    chart_spec=None,
                    chart_payload=chart_payload,
                )

        # 7) Special case: 'message' column
        if df.shape == (1, 1) and "message" in df.columns:
            msg = str(df.iloc[0]["message"])
            chart_payload = {
                "backend": "quickchart",
                "config": {
                    "type": "table",
                    "data": {"columns": ["message"], "rows": [[msg]]},
                    "message": msg,
                },
                "url": "",
            }
            return PipelineResult(
                user_question=user_question,
                sql_raw=sql_raw,
                sql_clean=sql_clean,
                df_preview=msg,
                chart_spec=None,
                chart_payload=chart_payload,
            )

        # 8) Handle empty DataFrame
        if df.empty:
            chart_payload = {
                "backend": "quickchart",
                "config": {"type": "table", "data": {}, "message": "No data to display"},
                "url": "",
            }
            return PipelineResult(
                user_question=user_question,
                sql_raw=sql_raw,
                sql_clean=sql_clean,
                df_preview="Empty DataFrame",
                chart_spec=None,
                chart_payload=chart_payload,
            )

        # 9) Decide chart
        chart_spec = infer_chart(df, user_question=user_question, sql_query=sql_clean)

        # 10) Render chart
        chart_payload = render(df, chart_spec, backend="quickchart")

        # 11) Return final pipeline result
        return PipelineResult(
            user_question=user_question,
            sql_raw=sql_raw,
            sql_clean=sql_clean,
            df_preview=df.head().to_string(),
            chart_spec=chart_spec,
            chart_payload=chart_payload,
        )


if __name__ == "__main__":
    orchestrator = QueryOrchestrator()
    question = "Total revenue in the year 2050"
    result = orchestrator.run(question)

    print("===== SQL =====")
    print(result.sql_clean)
    print("\n===== DataFrame Preview =====")
    print(result.df_preview)
    print("\n===== Chart URL =====")
    print(result.chart_payload.get("url"))
