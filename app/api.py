# app/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from config import get_settings
from src import QueryOrchestrator

# Retrieve configuration
settings = get_settings()

# Initialize FastAPI app with title/version/description from settings
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LLM → SQL → DB → Visualization pipeline for telecom data",
)

# Initialize the query orchestrator once to handle incoming queries
# Keeps it in memory for performance rather than creating per request
orchestrator = QueryOrchestrator()

# Request model: only requires a 'question' string from user
class QueryRequest(BaseModel):
    question: str

# Response model: captures SQL, chart info, and optional messages
class QueryResponse(BaseModel):
    question: str
    sql: str
    df_preview: str
    chart_url: Optional[str]
    chart_config: Dict[str, Any]
    chart_type: Optional[str]
    chart_title: Optional[str]
    message: Optional[str] = None


# POST endpoint to submit a query
# Returns SQL, data preview, chart info, and messages
@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    try:
        # Run the pipeline with the user's question
        result = orchestrator.run(req.question)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Extract chart info if available
    chart_url = result.chart_payload.get("url")
    chart_config = result.chart_payload.get("config", {})
    chart_type = None
    chart_title = None

    # If chart spec is defined, pull type and title
    if result.chart_spec is not None:
        chart_type = result.chart_spec.chart_type
        chart_title = result.chart_spec.title

    # Optional message from chart payload (like errors or empty data)
    message = chart_config.get("message") if isinstance(chart_config, dict) else None

    # Return all relevant info in a structured response
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


# Simple health check endpoint for monitoring
# Can be used by Docker/K8s or load balancers
@app.get("/health")
def health():
    return {"status": "ok"}