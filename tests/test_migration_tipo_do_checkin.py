import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from src.data.models import Base

ROOT = Path(__file__).resolve().parent.parent


def _alembic_cfg():
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic_migrations"))
    return cfg


def test_backfill_usa_pagamento_do_dia_e_senao_plano_atual(tmp_path, monkeypatch):
    db = tmp_path / "antigo.db"
    monkeypatch.setenv("SUMMIT_DB_PATH", str(db))
    Base.metadata.create_all(create_engine(f"sqlite:///{db}"))
    con = sqlite3.connect(db)
    con.execute("ALTER TABLE frequencia DROP COLUMN plano")  # esquema de antes do ADR 0001
    con.executescript("""
        INSERT INTO membros (id, nome, plano, voucher_credits) VALUES (1, 'Ana', 'Mensal', 0);
        INSERT INTO frequencia (id, member_id, checkin_datetime) VALUES
            (1, 1, '2026-03-02 19:00:00'),
            (2, 1, '2026-04-06 19:00:00');
        INSERT INTO pagamentos (member_id, data_pagamento, tipo_transacao, valor, metodo_pagamento)
            VALUES (1, '2026-03-02 19:00:00', 'Gympass', 15, 'Check-in');
    """)
    con.commit()
    con.close()

    cfg = _alembic_cfg()
    command.stamp(cfg, "5e3b8f4d2a11")
    command.upgrade(cfg, "head")

    con = sqlite3.connect(db)
    linhas = con.execute("SELECT id, plano FROM frequencia ORDER BY id").fetchall()
    con.close()
    # 1: veio pelo Gympass (tem pagamento no dia); 2: sem pagamento, herda o plano atual
    assert linhas == [(1, "Gympass"), (2, "Mensal")]
