"""Gera um banco SIMULADO (demo_database.db) para testar o Resumo Semanal.

Nunca grava no banco real. Uso, na raiz do repo:
    python scripts/seed_demo_db.py
    $env:SUMMIT_DB_PATH = "demo_database.db"; python run.py      # PowerShell
"""

from __future__ import annotations

import os
import random
import sqlite3
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402

from src.config import DB_FILENAME  # noqa: E402
from src.core.payment_constants import METODO_CHECKIN, METODO_PIX  # noqa: E402
from src.core.plan_utils import ASSINANTE, GYM_TOTALPASS, categoria_do_plano  # noqa: E402
from src.data.models import Base  # noqa: E402
from src.utils.utils import calculate_new_due_date  # noqa: E402

DEMO_PATH = ROOT / "demo_database.db"
HOJE = date(2026, 9, 28)        # segunda-feira: ultima Semana fechada = 21/09–26/09
INICIO = date(2026, 6, 8)       # 16 Semanas (12 navegaveis + 4 de historico)
FIM = date(2026, 9, 27)         # domingo excepcional com 1 check-in
MIGRACAO = date(2026, 8, 17)    # dia em que o app passou a gravar o Tipo do Check-in

# (nome, preco, valor_por_checkin, requer_vencimento, is_quota, quota_amount)
PLANOS = [
    ("Mensal", 190.0, 0.0, True, False, 0),
    ("Mens. c/ Treino", 280.0, 0.0, True, False, 0),
    ("Trimestral", 500.0, 0.0, True, False, 0),
    ("Semestral", 950.0, 0.0, True, False, 0),
    ("Anual", 1900.0, 0.0, True, False, 0),
    ("Escolinha 2x", 250.0, 0.0, True, False, 0),
    ("Diária", 0.0, 35.0, False, False, 0),
    ("Diária Boulder", 0.0, 35.0, False, False, 0),
    ("Gympass", 0.0, 15.0, False, False, 0),
    ("Totalpass", 0.0, 15.0, False, False, 0),
    ("Voucher", 300.0, 0.0, False, True, 10),
    ("Cortesia", 0.0, 0.0, False, False, 0),
    ("Livre", 0.0, 0.0, False, False, 0),
    ("Evento", 0.0, 0.0, False, False, 0),
]
PRECO = {p[0]: p[1] for p in PLANOS}
VALOR_POR_CHECKIN = {p[0]: p[2] for p in PLANOS if p[2]}

# Fundo aleatorio: (plano, quantidade de membros, visitas por semana)
PERFIS = [
    ("Gympass", 34, 1.4), ("Totalpass", 4, 1.2),
    ("Mensal", 20, 2.0), ("Mens. c/ Treino", 4, 2.5), ("Trimestral", 4, 2.0),
    ("Semestral", 2, 2.0), ("Anual", 3, 2.0), ("Escolinha 2x", 3, 2.0),
    ("Diária", 20, 0.3), ("Diária Boulder", 6, 0.3),
    ("Voucher", 8, 1.0),
    ("Cortesia", 2, 1.0), ("Livre", 3, 1.5), ("Evento", 2, 0.1),
]

# Cenarios plantados (nomes ficticios e fixos, usados nos testes)
CANDIDATOS = [("Alan Duarte", "Masculino"), ("Bela Nunes", "Feminino"), ("Cris Vale", "Feminino"),
              ("Duda Lobo", "Feminino"), ("Enzo Sales", "Masculino"), ("Flor Aguiar", "Feminino")]
CONVERSOES = [("Caio Moreira", "Masculino", date(2026, 7, 13)),
              ("Lia Fontes", "Feminino", date(2026, 8, 3)),
              ("Rui Teixeira", "Masculino", date(2026, 9, 8))]
PERDAS = [("Bia Campos", "Feminino", date(2026, 8, 31)),
          ("Davi Prado", "Masculino", date(2026, 9, 22))]
VENCIDOS = [("Elis Barros", "Feminino"), ("Ivo Leal", "Masculino"), ("Nina Paiva", "Feminino"),
            ("Otto Reis", "Masculino"), ("Tais Mota", "Feminino")]
DOMINGO = ("Gil Sampaio", "Masculino")

FEM = ["Ana", "Beatriz", "Camila", "Daniela", "Eduarda", "Fernanda", "Gabriela", "Helena", "Isabela",
       "Julia", "Larissa", "Mariana", "Natalia", "Paula", "Renata", "Sofia", "Tatiana", "Vitoria"]
MASC = ["Andre", "Bruno", "Carlos", "Diego", "Eduardo", "Felipe", "Gustavo", "Henrique", "Igor",
        "Joao", "Lucas", "Marcelo", "Nicolas", "Otavio", "Pedro", "Rafael", "Thiago", "Vinicius"]
SOBRENOMES = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Rodrigues",
              "Almeida", "Nascimento", "Araujo", "Ribeiro", "Carvalho", "Gomes", "Martins", "Rocha"]

# Calibrado pelo banco real (dez/2025–jan/2026): picos 10h e 18–20h, terca e quinta mais cheias
HORAS_PESO = {8: 3, 9: 5, 10: 12, 11: 4, 12: 2, 16: 5, 17: 8, 18: 22, 19: 23, 20: 10, 21: 2}
HORAS_PESO_GT = {8: 2, 9: 4, 10: 16, 11: 3, 12: 2, 16: 4, 17: 7, 18: 20, 19: 30, 20: 9, 21: 1}
DIA_PESO = [0.9, 1.3, 0.9, 1.2, 0.8, 0.9]  # seg..sab


def _dias_de_treino(inicio: date, fim: date):
    d = inicio
    while d <= fim:
        if d.weekday() < 6:
            yield d
        d += timedelta(days=1)


def _alembic_upgrade(destino: Path) -> None:
    antes = os.environ.get("SUMMIT_DB_PATH")
    os.environ["SUMMIT_DB_PATH"] = str(destino)
    try:
        cfg = Config(str(ROOT / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "alembic_migrations"))
        command.stamp(cfg, "5e3b8f4d2a11")
        command.upgrade(cfg, "head")
    finally:
        if antes is None:
            os.environ.pop("SUMMIT_DB_PATH", None)
        else:
            os.environ["SUMMIT_DB_PATH"] = antes


def gerar(destino: Path = DEMO_PATH) -> Path:
    destino = Path(destino)
    if destino.name == DB_FILENAME:
        raise SystemExit(f"Recusado: '{destino}' tem o nome do banco real. O simulado e demo_database.db.")
    destino.unlink(missing_ok=True)
    rng = random.Random(42)

    membros, checkins, pagamentos = [], [], []
    nomes_usados = {n for n, *_ in CANDIDATOS + CONVERSOES + PERDAS + VENCIDOS + [DOMINGO]}

    def novo_membro(nome, genero, nasc, fases):
        mid = len(membros) + 1
        membros.append({"id": mid, "nome": nome, "genero": genero, "nasc": nasc, "fases": fases,
                        "whatsapp": f"(00) 9{mid:04d}-{mid:04d}", "vencimento": None, "creditos": 0})
        return membros[-1]

    def plano_em(m, d):
        return [plano for inicio, plano in m["fases"] if inicio <= d][-1]

    def nasc_aleatorio(ano_min, ano_max):
        return date(rng.randint(ano_min, ano_max), rng.randint(1, 12), rng.randint(1, 28))

    def checkin(m, d):
        plano = plano_em(m, d)
        pesos = HORAS_PESO_GT if categoria_do_plano(plano) == GYM_TOTALPASS else HORAS_PESO
        hora = rng.choices(list(pesos), weights=list(pesos.values()))[0]
        dt = datetime.combine(d, time(hora, rng.randrange(60)))
        checkins.append((m["id"], dt, plano))
        if plano in VALOR_POR_CHECKIN:  # como o app: pagamento automatico por check-in
            pagamentos.append((m["id"], dt, plano, VALOR_POR_CHECKIN[plano], METODO_CHECKIN, None))

    def fixo(m, dias_semana, desde=INICIO, ate=FIM):
        for d in _dias_de_treino(desde, ate):
            if d.weekday() in dias_semana:
                checkin(m, d)

    def renovar(m, plano, desde, ate):
        d = desde
        while d < ate:
            vence = calculate_new_due_date(plano, datetime.combine(d, time(10))).date()
            pagamentos.append((m["id"], datetime.combine(d, time(10)), "Renovação Plano",
                               PRECO[plano], METODO_PIX, vence))
            m["vencimento"], d = vence, vence

    # --- Fundo aleatorio ---
    for plano, quantidade, por_semana in PERFIS:
        categoria = categoria_do_plano(plano)
        anos = (1995, 2006) if categoria == GYM_TOTALPASS else (2012, 2016) if plano.startswith("Escolinha") else (1972, 2006)
        for _ in range(quantidade):
            genero = rng.choice(["Feminino", "Masculino"])
            while True:
                nome = f"{rng.choice(FEM if genero == 'Feminino' else MASC)} {rng.choice(SOBRENOMES)}"
                if nome not in nomes_usados:
                    break
            nomes_usados.add(nome)
            m = novo_membro(nome, genero, nasc_aleatorio(*anos), [(INICIO, plano)])
            if categoria == ASSINANTE:
                if plano == "Anual":  # pagamento grande numa semana so (testa caixa vs competencia)
                    renovar(m, plano, INICIO + timedelta(days=rng.randrange(100)), HOJE)
                else:
                    duracao = (calculate_new_due_date(plano, datetime(2026, 1, 1)) - datetime(2026, 1, 1)).days
                    renovar(m, plano, INICIO - timedelta(days=rng.randrange(duracao)), HOJE)
            total_dias = (FIM - INICIO).days
            for d in _dias_de_treino(INICIO, FIM - timedelta(days=1)):  # domingo 27/09 so o plantado
                rampa = 0.8 + 0.4 * (d - INICIO).days / total_dias if categoria == GYM_TOTALPASS else 1.0
                if rng.random() < por_semana / 6 * DIA_PESO[d.weekday()] * rampa:
                    checkin(m, d)
            if plano == "Voucher":  # compra de 10 creditos a cada 10 visitas
                meus = [c for c in checkins if c[0] == m["id"]]
                for n, (_, dt, _) in enumerate(meus):
                    if n % 10 == 0:
                        pagamentos.append((m["id"], dt, "Compra Voucher", PRECO["Voucher"], METODO_PIX, None))
                m["creditos"] = (-len(meus)) % 10

    # --- Cenarios plantados ---
    for nome, genero in CANDIDATOS:
        fixo(novo_membro(nome, genero, nasc_aleatorio(1995, 2004), [(INICIO, "Gympass")]), {1, 3, 5})
    for nome, genero, quando in CONVERSOES:
        m = novo_membro(nome, genero, nasc_aleatorio(1990, 2002), [(INICIO, "Gympass"), (quando, "Mensal")])
        renovar(m, "Mensal", quando, HOJE)
        fixo(m, {0, 2})
    for nome, genero, quando in PERDAS:
        m = novo_membro(nome, genero, nasc_aleatorio(1985, 2000), [(INICIO, "Mensal"), (quando, "Gympass")])
        renovar(m, "Mensal", INICIO - timedelta(days=10), quando)
        m["vencimento"] = None  # virou Gympass: plano sem vencimento
        fixo(m, {0, 2})
    for nome, genero in VENCIDOS:
        m = novo_membro(nome, genero, nasc_aleatorio(1980, 2000), [(INICIO, "Mensal")])
        renovar(m, "Mensal", date(2026, 5, 1), date(2026, 8, 2))  # ultimo pagamento 01/08, venceu 01/09
        fixo(m, {0, 2, 4})
    m = novo_membro(*DOMINGO, nasc_aleatorio(1980, 1995), [(INICIO, "Livre")])
    fixo(m, {1})
    checkin(m, FIM)

    checkins.sort(key=lambda c: c[1])
    primeiro_checkin = {}  # data_cadastro do demo: dia do 1o check-in (sem check-in: INICIO); nao gasta o rng
    for mid, dt, _ in checkins:
        primeiro_checkin.setdefault(mid, dt.date())

    # --- Fase 1: esquema antigo (sem frequencia.plano), dados ate a migracao ---
    Base.metadata.create_all(create_engine(f"sqlite:///{destino}"))
    con = sqlite3.connect(destino)
    con.execute("ALTER TABLE frequencia DROP COLUMN plano")
    con.executemany(
        "INSERT INTO planos (nome, preco, valor_por_checkin, requer_vencimento, ativo, is_quota, quota_amount)"
        " VALUES (?, ?, ?, ?, 1, ?, ?)", PLANOS)
    con.executemany(
        "INSERT INTO membros (id, nome, plano, vencimento_plano, estado_plano, data_nascimento,"
        " data_cadastro, whatsapp, genero, voucher_credits) VALUES (?, ?, ?, ?, 'ATIVO', ?, ?, ?, ?, ?)",
        [(m["id"], m["nome"], plano_em(m, MIGRACAO),
          m["vencimento"].isoformat() if m["vencimento"] else None,
          m["nasc"].isoformat(), primeiro_checkin.get(m["id"], INICIO).isoformat(), m["whatsapp"], m["genero"], m["creditos"])
         for m in membros])
    con.executemany(
        "INSERT INTO pagamentos (member_id, data_pagamento, tipo_transacao, descricao, valor,"
        " metodo_pagamento, nova_data_vencimento) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(mid, dt.isoformat(sep=" "), tipo, f"{tipo} (simulado)", valor, metodo,
          vence.isoformat() if vence else None)
         for mid, dt, tipo, valor, metodo, vence in pagamentos])
    con.executemany(
        "INSERT INTO frequencia (member_id, checkin_datetime) VALUES (?, ?)",
        [(mid, dt.isoformat(sep=" ")) for mid, dt, _ in checkins if dt.date() < MIGRACAO])
    con.commit()
    con.close()

    # --- Fase 2: a migracao real (coluna + backfill) ---
    _alembic_upgrade(destino)

    # --- Fase 3: app novo grava o Tipo do Check-in; membros chegam ao plano final ---
    con = sqlite3.connect(destino)
    con.executemany(
        "INSERT INTO frequencia (member_id, checkin_datetime, plano) VALUES (?, ?, ?)",
        [(mid, dt.isoformat(sep=" "), plano) for mid, dt, plano in checkins if dt.date() >= MIGRACAO])
    con.executemany("UPDATE membros SET plano = ? WHERE id = ?", [(plano_em(m, FIM), m["id"]) for m in membros])
    con.commit()
    con.close()
    return destino


if __name__ == "__main__":
    caminho = gerar()
    print(f"Banco simulado criado em {caminho}")
    print('Abrir o app com ele (PowerShell, na raiz): $env:SUMMIT_DB_PATH = "demo_database.db"; python run.py')
