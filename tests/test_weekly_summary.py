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


from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.reports.weekly_summary import montar_semanas, semana_fechada

HOJE = date(2026, 9, 28)


@pytest.fixture(scope="module")
def demo_session(demo_db):
    session = sessionmaker(bind=create_engine(f"sqlite:///{demo_db}"))()
    yield session
    session.close()


@pytest.fixture(scope="module")
def semanas(demo_session):
    return montar_semanas(demo_session, HOJE)


@pytest.mark.parametrize("hoje, segunda", [
    (date(2026, 9, 28), date(2026, 9, 21)),  # segunda: a semana passada fechou
    (date(2026, 9, 27), date(2026, 9, 14)),  # domingo: a semana atual ainda esta aberta
    (date(2026, 9, 26), date(2026, 9, 14)),  # sabado
])
def test_semana_fechada(hoje, segunda):
    assert semana_fechada(hoje) == segunda


def test_doze_semanas_da_mais_recente_para_a_mais_antiga(semanas):
    assert len(semanas) == 12
    assert semanas[0]["rotulo"] == "21/09 – 26/09"
    assert semanas[-1]["rotulo"] == "06/07 – 11/07"


def test_domingo_entra_no_total_mas_nao_no_grafico_por_dia(semanas):
    s = semanas[0]
    assert s["checkins"] == sum(sum(v) for v in s["por_dia"].values()) + 1


def test_conversoes_e_perdas_plantadas(semanas):
    assert sorted(n for s in semanas for n in s["conversoes"]) == ["Caio Moreira", "Lia Fontes", "Rui Teixeira"]
    assert sorted(n for s in semanas for n in s["perdas"]) == ["Bia Campos", "Davi Prado"]
    assert semanas[0]["perdas"] == ["Davi Prado"]


def test_candidatos_a_conversao(semanas):
    candidatos = semanas[0]["candidatos"]
    plantados = {"Alan Duarte", "Bela Nunes", "Cris Vale", "Duda Lobo", "Enzo Sales", "Flor Aguiar"}
    assert plantados <= {c["nome"] for c in candidatos}
    assert all(c["checkins"] >= 8 and c["whatsapp"].startswith("https://wa.me/") for c in candidatos)


def test_vencidos_que_vieram(semanas):
    plantados = {"Elis Barros", "Ivo Leal", "Nina Paiva", "Otto Reis", "Tais Mota"}
    assert plantados <= {v["nome"] for v in semanas[0]["vencidos"]}


def test_valor_por_visita_e_fatia_gym_totalpass(semanas):
    s = semanas[0]
    assert s["valor_visita_gt"] == 15.0
    assert s["valor_visita_assinante"] > 15.0
    assert 25 <= s["pct_gt"] <= 55


def test_comparativos(semanas):
    s = semanas[0]
    assert s["anterior"]["checkins"] == semanas[1]["checkins"]
    assert set(s["media4"]) == {"checkins", "pct_gt", "receita"}


def test_mapa_de_calor_e_perfil(semanas):
    s = semanas[0]
    assert len(s["calor"]) == 6 and all(len(linha) == 16 for linha in s["calor"])
    assert 1 <= len(s["destaques"]) <= 2
    assert sum(s["perfil"]["Gym/Totalpass"]["idade"].values()) > 0
