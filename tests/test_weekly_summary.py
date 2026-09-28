import importlib.util
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _seed():
    spec = importlib.util.spec_from_file_location("seed_demo_db", ROOT / "scripts" / "seed_demo_db.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def demo_db(tmp_path_factory):
    return _seed().gerar(tmp_path_factory.mktemp("demo") / "demo_database.db")


def test_recusa_gravar_no_banco_real(tmp_path):
    with pytest.raises(SystemExit):
        _seed().gerar(tmp_path / "gym_database.db")


def test_banco_simulado_tem_tipo_do_checkin_em_tudo(demo_db):
    con = sqlite3.connect(demo_db)
    total, sem_tipo = con.execute("SELECT count(*), sum(plano IS NULL) FROM frequencia").fetchone()
    con.close()
    assert total > 1500
    assert sem_tipo == 0
