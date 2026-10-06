"""Banco novo: init_db + stamp inicial + upgrade head deve chegar ao head."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

import src.data.db as db

PROJECT_DIR = Path(__file__).resolve().parent.parent


def test_fresh_db_upgrades_to_head(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "_DEFAULT_DB_PATH", tmp_path / "fresh.db")
    db.reset_engine()
    try:
        cfg = Config(str(PROJECT_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(PROJECT_DIR / "alembic_migrations"))

        # Mesmo fluxo de run.py:run_migrations() para banco novo.
        db.init_db()
        command.stamp(cfg, "b7156d140f0a")
        command.upgrade(cfg, "head")

        with db.get_engine().connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert version == ScriptDirectory.from_config(cfg).get_current_head()
    finally:
        db.reset_engine()
