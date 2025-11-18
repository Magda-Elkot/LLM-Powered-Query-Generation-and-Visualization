# Telecom LLM Query System

An LLM-powered system that converts natural-language telecom questions into validated SQL, executes them safely against a PostgreSQL warehouse, and returns clean data previews and visualizations.

This document contains:

- Full system overview  
- Installation and setup instructions  
- Environment configuration  
- Database and schema setup  
- Running backend and frontend  
- Docker usage  
- Error handling  
- Architecture breakdown  

---

## 1. Features

- Natural language → SQL using Groq (OpenAI-compatible)
- Schema-aware prompting via JSON metadata
- SQL sanitizer to remove unsafe statements
- SQL validator enforcing SELECT-only rules
- Automatic chart detection and rendering via QuickChart
- FastAPI backend
- Streamlit user interface
- Offline fallback LLM for no-internet or rate limit scenarios

---

## 2. Requirements

- Python 3.10+
- PostgreSQL
- Groq API Key
- (Optional) Docker and Docker Compose

Install all Python dependencies via:

```bash
pip install -r requirements.txt
```

---

## 3. Setup Guide

### 3.1 Clone the Repository

```bash
git https://github.com/Magda-Elkot/LLM-Powered-Query-Generation-and-Visualization.git
cd telecom-llm-query-system
```

---

### 3.2 Create Python Environment

#### Option A: venv

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows
```

#### Option B: Conda

```bash
conda create -n telecom-llm python=3.10
conda activate telecom-llm
```

---

### 3.3 Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3.4 Configure Environment Variables (.env)

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# LLM
GROQ_API_KEY=your_groq_key
GROQ_MODEL_NAME=llama-3.1-70b-versatile

# Database Config
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=telecom

# URLs
API_URL=http://localhost:8000
BACKEND_URL=http://backend:8000
```

---

## 4. Database Setup

### 4.1 Start PostgreSQL

#### Local Installation:

```bash
createdb telecom
```

#### Or via Docker:

```bash
docker run -d \
  --name telecom-postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_USER=your_user \
  -e POSTGRES_DB=telecom \
  -p 5433:5432 postgres
```

---

### 4.2 Generate Database Schema

This script imports tables and data from the Excel model:

```bash
python scripts/setup_schema.py
```

It will:

- Read Excel file  
- Infer data types, PKs, FKs  
- Generate `schema_metadata.json`  
- Recreate PostgreSQL tables  
- Load all data  

Verify DB:

```bash
python scripts/test_db.py
```

---

## 5. Run the Backend (FastAPI)

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

Health endpoint:

```
http://localhost:8000/health
```

---

## 6. Run the UI (Streamlit)

```bash
streamlit run app/streamlit_app.py
```

Open:

```
http://localhost:8501
```

You can now ask questions, generate SQL, and view visualizations.

---

## 7. Run Using Docker Compose

```bash
docker-compose up --build
```

Available services:

```
Backend:  http://localhost:8000
UI:       http://localhost:8501
```

---

## 8. System Architecture

### Context Layer
- SchemaManager: builds schema + metadata  
- ContextRetriever: loads schema metadata for LLM  

### LLM Layer
- build_sql_prompt  
- GroqClient for SQL generation  
- LLMFallbackManager for offline fallback  

### Validation Layer
- QuerySanitizer: removes comments, fences, semicolons  
- SQLValidator: ensures safe, schema-valid SQL  

### Database Layer
- DBConnector: SQLAlchemy engine/session  
- QueryExecutor: safe SELECT execution  

### Visualization Layer
- infer_chart: auto-select best chart  
- render: QuickChart renderer  

### Orchestrator Layer (run_pipeline.py)
```
question → prompt → LLM SQL → sanitize → validate → execute → chart → return result
```



---

## 9. Recommended Extensions

- Add SQL few-shot examples  
- Add logging of SQL and questions  
- Cloud deployment  
