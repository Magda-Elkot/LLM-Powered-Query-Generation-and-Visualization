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
        Ensure SQL does not contain multiple statements.
        Validator checks SQL type, but not multi-statement attacks.
        """
        if ";" in sql.strip():
            raise ValueError("Multiple SQL statements are not allowed.")

    def execute(self, sql: str, params: dict = None) -> pd.DataFrame:
        params = params or {}

        # Only extra safety required at executor level
        self._ensure_single_statement(sql)

        try:
            with self.db_connector.get_session() as session:
                result = session.execute(text(sql), params)
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                return df

        except SQLAlchemyError as e:
            logger.error("Query execution failed: %s", e)
            raise RuntimeError(f"Database execution failed: {e}")

    def execute_scalar(self, sql: str, params: dict = None):
        params = params or {}

        self._ensure_single_statement(sql)

        try:
            with self.db_connector.get_session() as session:
                result = session.execute(text(sql), params)
                return result.scalar()

        except SQLAlchemyError as e:
            logger.error("Scalar query failed: %s", e)
            raise RuntimeError(f"Database execution failed: {e}")
