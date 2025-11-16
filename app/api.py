# app/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from src.run_pipeline import QueryOrchestrator  

app = FastAPI(
    title="Telecom LLM Query API",
    version="1.0.0",
    description="LLM → SQL → DB → Visualization pipeline for telecom data",
)

# Single orchestrator instance
orchestrator = QueryOrchestrator()


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    sql: str
    df_preview: str
    chart_url: Optional[str]
    chart_config: Dict[str, Any]
    chart_type: Optional[str]
    chart_title: Optional[str]
    message: Optional[str] = None


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    try:
        result = orchestrator.run(req.question)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Extract chart info
    chart_url = result.chart_payload.get("url")
    chart_config = result.chart_payload.get("config", {})
    chart_type = None
    chart_title = None

    if result.chart_spec is not None:
        chart_type = result.chart_spec.chart_type
        chart_title = result.chart_spec.title

    message = chart_config.get("message") if isinstance(chart_config, dict) else None

    return QueryResponse(
        question=result.user_question,
        sql=result.sql_clean,
        df_preview=result.df_preview,
        chart_url=chart_url,
        chart_config=chart_config,
        chart_type=chart_type,
        chart_title=chart_title,
        message=message,
    )


@app.get("/health")
def health():
    return {"status": "ok"}