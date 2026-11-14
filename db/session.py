from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import Session, sessionmaker

class DatabaseSessionManager:
    """Manages the SQLAlchemy engine and sessions for the CLI engine."""

    def __init__(self, database_url: URL, echo: bool = False) -> None:
        self.engine: Engine = create_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,
        )
        self._session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Context manager for SQLAlchemy session"""
        db_session: Session = self._session_factory()
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.close()

    def dispose(self) -> None:
        """Dispose of the engine and session factory"""
        self.engine.dispose()
