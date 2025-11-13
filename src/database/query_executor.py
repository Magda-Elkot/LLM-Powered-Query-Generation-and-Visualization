# src/database/query_executor.py
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .db_connector import DBConnector


class QueryExecutor:
    """
    Executes SQL queries safely and returns pandas DataFrames.
    Uses DBConnector for sessions/engine.
    """

    def __init__(self, db_connector: DBConnector):
        self.db_connector = db_connector

    def execute(self, sql: str, params: dict = None) -> pd.DataFrame:
        """
        Executes a SQL query and returns results as DataFrame.
        Supports parameterized queries for safety.
        """
        params = params or {}
        try:
            with self.db_connector.get_session() as session:
                result = session.execute(text(sql), params)
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                return df
        except SQLAlchemyError as e:
            print(f"Query execution failed: {e}")
            return pd.DataFrame()

    def execute_scalar(self, sql: str, params: dict = None):
        """Execute a query and return a single scalar value."""
        params = params or {}
        try:
            with self.db_connector.get_session() as session:
                result = session.execute(text(sql), params)
                return result.scalar()
        except SQLAlchemyError as e:
            print(f"Query execution failed: {e}")
            return None
