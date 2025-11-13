# src/database/db_connector.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from config import get_settings


settings = get_settings()  # use a consistent variable name


class DBConnector:
    """
    Manages PostgreSQL connection using SQLAlchemy.
    Provides engine and session objects.
    """

    def __init__(self):
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _create_engine(self):
        """Create a SQLAlchemy engine using PostgreSQL connection details."""
        url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        return create_engine(url, echo=False, future=True)

    def get_session(self) -> Session:
        """Provides a new SQLAlchemy session."""
        return self.SessionLocal()

    def test_connection(self):
        """Quick test to ensure database is reachable."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1;"))
                return result.scalar() == 1
        except SQLAlchemyError as e:
            print("Database connection failed:", e)
            return False
