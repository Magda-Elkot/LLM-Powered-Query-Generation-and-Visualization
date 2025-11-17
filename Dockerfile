FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2 / postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

#  IMPORTANT: make root of repo importable (so `config` works)
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Copy code
COPY . .

EXPOSE 8000 8501

# Default command for backend container
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]