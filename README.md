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
### Architecture Diagram

![alt text](<Untitled diagram-2025-11-19-172535.png>)


Or view the interactive diagram: [Link Text](https://mermaid.live/view#pako:eNp1VNty2jAQ_RWNnpIp0HCJA37oTDAYaCEYG_JQkclsbAEqsgSynCv598o2l5KZPlnec86udveMPnAoI4ptXC6X5yKUYsGW9lwgxKVc2yjkkCQsnIscXnD5Eq5AaTT0Mw5CMzJLqHpA5fKP3R3oVAFHHMQyhSVF25QmmkmxQ8GUBFpRiDnTaDZ4KMTBNNd5Y3P4bsjqbYduvQFxIdHmi9oQrqmI9uwsYuho7Dt9MsnYYxWuTAUFWqo9KQNzluMTRwpNX7VPtWL0mR4ojp8TRt3pLblITIYYHmOqIQINlT-JFJdfc3n-eORNyVPKePSYbPnjRsl4o_e0As2JPYf0lNw6nFFxgHvO8dbnaXeDBdooFoN6QwtgPNkht02Gw5ELnD-Z1kcgzBQP13bb_8mDJkExjgAE0-z9qJgEORzck2AyvAfOon8GFdwX2m6h7b7SMD2hk26OdtrkwpOJXipqUiBNOQ1lbMKXX3gu8UBEkKCOGaKrIKZ7QsfNCQMnIE5mnCBLcapj4sW2-nt4Q8Nzpd-96xDfuICq0wb7R6gIZKeiHce0w8J1ngzN_OHhnsUSjIXOvLT7GYzvbJT19g15ij4z-mJOuToz7ZlNp_DE6Qmdnbuy7_R_kV7XGHlFgeuVKYxLeKlYhG2tUlrCMVUxZL_4I5POsTbWo3Nsm2MEaj3Hc_FpNBsQv6WMDzIl0-UK2wvgiflLN2aJtMNgaYZ8pOTjcWQqNLZrtUaeA9sf-BXb5aZVq1xZVrNVq7eajUa1XsJv2G5dVVpXVr1RbzaarepN9fqzhN_zqtXKzfV1rdqwqlatcVOtt6wSphEzOxsVD0X-Xnz-BfybR1Y)



---

## 9. Future Work

- **Offline LLM & Rate Limit Handling**  
  Currently, the system depends on the online Groq LLM. If the API is unreachable or rate-limited, `LLMFallbackManager` provides a safe placeholder SQL. Future work could explore lightweight local models or caching strategies.

- **Query History & Context-Aware Refinement**  
  Store user query history to refine follow-up queries and improve context-aware SQL generation.

- **Multi-Provider LLM Support**  
  Integrate multiple LLM providers for automatic failover and increased reliability.

- **Extended Visualizations & Analytics**  
  Add more chart types and customizable dashboards for richer insights.

