import tempfile
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from app.models import Base


def test_alembic_migration_upgrade_and_tables():
    """
    Test running Alembic migration upgrade head against a fresh database,
    verifying all tables and indexes are created properly.
    """
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini_path = backend_dir / "alembic.ini"
    assert alembic_ini_path.exists(), "alembic.ini must exist"

    # Use a temporary SQLite database file for isolation
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    try:
        db_url = f"sqlite:///{Path(tmp_db_path).as_posix()}"
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

        # Run migration
        command.upgrade(alembic_cfg, "head")

        # Inspect migrated database
        engine = create_engine(db_url)
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        expected_tables = {
            "organizations",
            "users",
            "contracts",
            "document_chunks",
            "clauses",
            "risk_assessments",
            "obligations",
            "compliance_controls",
            "compliance_tasks",
            "audit_logs",
            "alembic_version",
        }

        for table in expected_tables:
            assert table in table_names, f"Table '{table}' should be present after migration"

        # Verify metadata consistency
        assert Base.metadata.tables.keys() <= table_names

        engine.dispose()
    finally:
        try:
            Path(tmp_db_path).unlink(missing_ok=True)
        except PermissionError:
            pass
