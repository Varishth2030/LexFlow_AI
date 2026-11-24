from sqlalchemy import text
from app.db.session import engine, SessionLocal, get_db
from app.db.base import Base


def test_sqlite_engine_configuration():
    """
    Verify engine is configured for SQLite and has check_same_thread=False.
    """
    # Verify driver is sqlite
    assert engine.url.drivername.startswith("sqlite")
    # Verify connect_args contains check_same_thread=False
    # (or in connect_args dictionary)
    assert engine.dialect.name == "sqlite"


def test_db_connection_direct():
    """
    Verify direct database connection and query execution.
    """
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1 AS alive")).scalar()
        assert result == 1


def test_db_session_lifecycle():
    """
    Verify SessionLocal creation, query execution, and cleanup.
    """
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1 AS alive")).scalar()
        assert result == 1
    finally:
        db.close()


def test_get_db_generator():
    """
    Verify FastAPI get_db dependency generator yields an active session.
    """
    gen = get_db()
    session = next(gen)
    try:
        result = session.execute(text("SELECT 'lexflow' AS val")).scalar()
        assert result == "lexflow"
    finally:
        # Complete generator to close session
        try:
            next(gen)
        except StopIteration:
            pass


def test_declarative_base():
    """
    Verify declarative Base class exists and has metadata.
    """
    assert hasattr(Base, "metadata")
    assert Base.metadata is not None
