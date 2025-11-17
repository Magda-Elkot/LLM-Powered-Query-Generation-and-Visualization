# app/streamlit_app.py
import requests
import streamlit as st

from config.settings import get_settings

settings = get_settings()
# Prefer BACKEND_URL (inside Docker), fallback to API_URL, then localhost
API_URL = settings.BACKEND_URL or settings.API_URL or "http://localhost:8000"

st.set_page_config(page_title="Telecom LLM Query UI", layout="wide")

st.title("📊 Telecom LLM-Powered Query & Visualization")

st.markdown(
    """
    Enter a natural language question about the telecom data.

    The UI calls the FastAPI backend, which:
    1. Uses an LLM to generate SQL  
    2. Executes it on the PostgreSQL database  
    3. Returns a preview and a chart URL (via QuickChart)
    """
)

question = st.text_input(
    "Your question:",
    placeholder="e.g. Show me total revenue per product category last year",
)

if st.button("Run query") and question:
    try:
        with st.spinner("Contacting backend..."):
            resp = requests.post(f"{API_URL}/query", json={"question": question})

        if resp.status_code != 200:
            st.error(f"Backend error: {resp.status_code} - {resp.text}")
        else:
            payload = resp.json()

            st.subheader("Generated SQL")
            st.code(payload["sql"], language="sql")

            st.subheader("Data Preview")
            if payload.get("df_preview"):
                st.text(payload["df_preview"])
            else:
                st.info("No data preview available.")

            st.subheader("Visualization")
            chart_url = payload.get("chart_url")
            chart_title = payload.get("chart_title") or "Chart"
            message = payload.get("message")

            if message:
                st.warning(message)

            if chart_url:
                st.image(chart_url, caption=chart_title, use_column_width=True)
            else:
                st.info("No chart generated for this query.")

    except Exception as e:
        st.error(f"Error calling backend: {e}")