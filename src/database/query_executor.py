import logging
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .db_connector import DBConnector


logger = logging.getLogger(__name__)


class QueryExecutor:
    """
    Executes safe, single-statement SELECT SQL queries 
    (validation & sanitization are performed earlier).
    """

    def __init__(self, db_connector: DBConnector):
        self.db_connector = db_connector

    def _ensure_single_statement(self, sql: str):
        """
        Extra safety check to prevent multi-statement SQL injections.
        Even though validation occurs earlier, this ensures no accidental ';' chaining.
        """
        if ";" in sql.strip():
            raise ValueError("Multiple SQL statements are not allowed.")

    def execute(self, sql: str, params: dict = None) -> pd.DataFrame:
        params = params or {}

        # Only extra safety required at executor level, Safety: prevent multi-statement execution
        self._ensure_single_statement(sql)

        try:
            with self.db_connector.get_session() as session:
                result = session.execute(text(sql), params)
                # Convert result to DataFrame for downstream analysis
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                return df

        except SQLAlchemyError as e:
            logger.error("Query execution failed: %s", e)
            raise RuntimeError(f"Database execution failed: {e}")

    def execute_scalar(self, sql: str, params: dict = None):
        """
        Execute a query expected to return a single value (scalar).
        Useful for COUNT(*) or aggregation queries.
        """
        params = params or {}

        self._ensure_single_statement(sql)

        try:
            with self.db_connector.get_session() as session:
                result = session.execute(text(sql), params)
                return result.scalar()

        except SQLAlchemyError as e:
            logger.error("Scalar query failed: %s", e)
            raise RuntimeError(f"Database execution failed: {e}")
