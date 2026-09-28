from src.data.db import get_database_url


def test_summit_db_path_aponta_para_outro_banco(monkeypatch, tmp_path):
    destino = tmp_path / "demo_database.db"
    monkeypatch.setenv("SUMMIT_DB_PATH", str(destino))
    assert get_database_url() == f"sqlite:///{destino}"


def test_sem_variavel_usa_banco_padrao(monkeypatch):
    monkeypatch.delenv("SUMMIT_DB_PATH", raising=False)
    assert get_database_url().endswith("gym_database.db")
