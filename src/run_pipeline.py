# src/run_pipeline.py

from dataclasses import dataclass
from typing import Dict, Any, Optional

from src.context.schema_manager import SchemaManager
from src.context.context_retriever import ContextRetriever
from src.database.db_connector import DBConnector
from src.database.query_executor import QueryExecutor
from src.llm.groq_client import GroqClient
from src.llm.prompt_templates import build_sql_prompt
from src.validation.sql_validator import SQLValidator
from src.validation.query_sanitizer import QuerySanitizer
from src.visualization.chart_selector import infer_chart
from src.visualization.renderers import render
from config.settings import get_settings

from src.visualization.chart_selector import ChartSpec  # ensure ChartSpec is imported


@dataclass
class PipelineResult:
    user_question: str
    sql_raw: str
    sql_clean: str
    df_preview: str       # df.head().to_string()
    chart_spec: Optional[ChartSpec]
    chart_payload: Dict[str, Any]  # e.g. quickchart URL + config


class QueryOrchestrator:
    """
    High-level pipeline:
      question → schema context → LLM → SQL → sanitize + validate → execute → visualize
    """

    def __init__(
        self,
        schema_path: str = "config/schema_metadata.json",
        llm_client: Optional[GroqClient] = None,
    ):
        # Context / schema
        self.context = ContextRetriever(schema_json_path=schema_path)

        # LLM
        self.llm_client = llm_client or GroqClient()

        # Validation & DB
        self.sanitizer = QuerySanitizer()
        self.validator = SQLValidator()
        self.db_connector = DBConnector()
        self.executor = QueryExecutor(self.db_connector)

    def run(self, user_question: str) -> PipelineResult:
        # 1) Build schema text for the prompt
        schema_text = self.context.generate_schema_text()

        # 2) Build LLM prompt
        prompt = build_sql_prompt(user_question=user_question, schema_text=schema_text)

        # 3) Generate SQL via LLM
        sql_raw = self.llm_client.generate_sql(prompt)

        # 4) Sanitize
        sql_clean = self.sanitizer.sanitize(sql_raw)

        # 5) Validate (only SELECT / WITH)
        self.validator.validate(sql_clean)

        # 6) Execute with error handling
        try:
            df = self.executor.execute(sql_clean)
        except Exception as e:
            # Return empty DataFrame and include error message in chart payload
            chart_payload = {
                "backend": "quickchart",
                "config": {"type": "table", "data": {}, "message": f"Query execution failed: {e}"},
                "url": ""
            }
            return PipelineResult(
                user_question=user_question,
                sql_raw=sql_raw,
                sql_clean=sql_clean,
                df_preview="Query execution failed",
                chart_spec=None,
                chart_payload=chart_payload,
            )

        # --- Handle empty DataFrame ---
        if df.empty:
            chart_payload = {
                "backend": "quickchart",
                "config": {"type": "table", "data": {}, "message": "No data to display"},
                "url": ""
            }
            return PipelineResult(
                user_question=user_question,
                sql_raw=sql_raw,
                sql_clean=sql_clean,
                df_preview="Empty DataFrame",
                chart_spec=None,
                chart_payload=chart_payload,
            )

        # 7) Decide chart
        chart_spec = infer_chart(df, user_question=user_question, sql_query=sql_clean)

        # 8) Render chart
        chart_payload = render(df, chart_spec, backend="quickchart")

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
    question = "hello"
    result = orchestrator.run(question)

    print("===== SQL =====")
    print(result.sql_clean)
    print("\n===== DataFrame Preview =====")
    print(result.df_preview)
    print("\n===== Chart URL =====")
    print(result.chart_payload.get("url"))
