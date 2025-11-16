FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2 / postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

EXPOSE 8000 8501

# Default command (FastAPI)
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]