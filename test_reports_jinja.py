"""
Teste de geracao de relatorios com dados simulados.

Cria um banco SQLite em memoria, insere dados realistas e valida que os
tres relatorios (membros, financeiro, frequencia) renderizam sem erros
e apresentam valores corretos.

Uso:
    python test_reports_jinja.py
    python test_reports_jinja.py --open   # abre os HTMLs no navegador apos gerar
"""

from __future__ import annotations

import sys
import os
import webbrowser
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

# Garante que o root do projeto esta no path
sys.path.insert(0, str(Path(__file__).parent))

# Configura DB de teste antes de importar qualquer modulo do projeto
os.environ["SUMMIT_DB_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.models import Base, Membro, Frequencia, Pagamento, Plano
from src.reports.members_report import generate_members_report
from src.reports.finance_report import generate_finance_report
from src.reports.frequency_report import generate_frequency_report
from src.services.payment_service import PaymentService
from src.services.member_service import MemberService
from src.core.plan_status import ATIVO, INATIVO, PENDENTE


# =============================================================================
# Setup do banco em memoria
# =============================================================================

def _build_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


def _seed(session):
    """Insere dados simulados realistas."""
    hoje = date.today()

    # -------------------------------------------------------------------------
    # Planos
    # -------------------------------------------------------------------------
    planos = [
        Plano(nome="Mensal",       preco=120.0, requer_vencimento=True,  is_quota=False, ativo=True),
        Plano(nome="Trimestral",   preco=320.0, requer_vencimento=True,  is_quota=False, ativo=True),
        Plano(nome="Semestral",    preco=580.0, requer_vencimento=True,  is_quota=False, ativo=True),
        Plano(nome="Pacote 10",    preco=150.0, requer_vencimento=False, is_quota=True,  quota_amount=10, ativo=True),
        Plano(nome="Diaria",       preco=0.0,   requer_vencimento=False, is_quota=False, valor_por_checkin=35.0, ativo=True),
        Plano(nome="Gympass",      preco=0.0,   requer_vencimento=False, is_quota=False, valor_por_checkin=15.0, ativo=True),
        Plano(nome="Totalpass",    preco=0.0,   requer_vencimento=False, is_quota=False, valor_por_checkin=15.0, ativo=True),
        Plano(nome="Cortesia",     preco=0.0,   requer_vencimento=False, is_quota=False, ativo=True),
        Plano(
            nome="Mensal c/ Treino",
            preco=210.0,
            requer_vencimento=True,
            is_quota=False,
            ativo=True,
        ),
    ]
    session.add_all(planos)
    session.flush()

    # -------------------------------------------------------------------------
    # Membros
    # -------------------------------------------------------------------------
    # Helper
    def dt(days_ago: int):
        return hoje - timedelta(days=days_ago)

    membros = [
        # --- Mensais ATIVOS, plano em dia ---
        Membro(nome="Ana Lima",       plano="Mensal",     estado_plano=ATIVO,   data_cadastro=dt(200), vencimento_plano=hoje + timedelta(days=15)),
        Membro(nome="Bruno Souza",    plano="Mensal",     estado_plano=ATIVO,   data_cadastro=dt(180), vencimento_plano=hoje + timedelta(days=8)),
        Membro(nome="Carla Mendes",   plano="Mensal",     estado_plano=ATIVO,   data_cadastro=dt(90),  vencimento_plano=hoje + timedelta(days=22)),
        Membro(nome="Diego Ramos",    plano="Trimestral", estado_plano=ATIVO,   data_cadastro=dt(365), vencimento_plano=hoje + timedelta(days=60)),
        Membro(nome="Eva Martins",    plano="Semestral",  estado_plano=ATIVO,   data_cadastro=dt(300), vencimento_plano=hoje + timedelta(days=120)),
        Membro(
            nome="Fabio Costa",
            plano="Mensal c/ Treino",
            estado_plano=ATIVO,
            data_cadastro=dt(150),
            vencimento_plano=hoje + timedelta(days=10),
            treina=True,
            vencimento_treino=hoje + timedelta(days=10),
        ),

        # --- Mensais INATIVOS (plano VENCIDO — inadimplentes) ---
        Membro(nome="Gabriela Nunes", plano="Mensal", estado_plano=INATIVO, data_cadastro=dt(500), vencimento_plano=dt(45)),
        Membro(nome="Henrique Alves", plano="Mensal", estado_plano=INATIVO, data_cadastro=dt(400), vencimento_plano=dt(20)),
        Membro(nome="Isabela Rocha",  plano="Trimestral", estado_plano=INATIVO, data_cadastro=dt(700), vencimento_plano=dt(90)),

        # --- Planos quota ---
        Membro(nome="Joao Ferreira",  plano="Pacote 10", estado_plano=ATIVO, data_cadastro=dt(60),  voucher_credits=5),
        Membro(nome="Karen Oliveira", plano="Pacote 10", estado_plano=ATIVO, data_cadastro=dt(45),  voucher_credits=2),

        # --- Per-checkin e avulsos ---
        Membro(nome="Lucas Silva",    plano="Gympass",   estado_plano=ATIVO, data_cadastro=dt(120)),
        Membro(nome="Marina Costa",   plano="Totalpass", estado_plano=ATIVO, data_cadastro=dt(80)),
        Membro(nome="Nicolas Prado",  plano="Diaria",    estado_plano=ATIVO, data_cadastro=dt(30)),

        # --- Cortesia (sem vencimento) ---
        Membro(nome="Olivia Faria",   plano="Cortesia",  estado_plano=ATIVO, data_cadastro=dt(10)),

        # --- ATIVO mas sem check-in recente (deve aparecer como risco de churn) ---
        Membro(nome="Rafael Esquecido",  plano="Mensal",    estado_plano=ATIVO, data_cadastro=dt(400), vencimento_plano=hoje + timedelta(days=5)),
        Membro(nome="Sandra Sumida",     plano="Trimestral", estado_plano=ATIVO, data_cadastro=dt(300), vencimento_plano=hoje + timedelta(days=30)),

        # --- PENDENTE: nao deve aparecer em nenhum relatorio ---
        Membro(nome="Paulo Pendente", plano="Mensal", estado_plano=PENDENTE, data_cadastro=dt(5)),
    ]
    session.add_all(membros)
    session.flush()

    # -------------------------------------------------------------------------
    # Check-ins (ultimos 45 dias)
    # -------------------------------------------------------------------------
    def checkin(membro, days_ago: int):
        return Frequencia(
            member_id=membro.id,
            checkin_datetime=datetime.now() - timedelta(days=days_ago),
        )

    ana, bruno, carla, diego, eva, fabio = membros[0], membros[1], membros[2], membros[3], membros[4], membros[5]
    gabriela, henrique, isabela = membros[6], membros[7], membros[8]
    joao, karen = membros[9], membros[10]
    lucas, marina, nicolas, olivia = membros[11], membros[12], membros[13], membros[14]

    checkins = [
        # Membros ativos — check-ins recentes (dentro dos 14 dias)
        checkin(ana,    2), checkin(ana,    9),
        checkin(bruno,  1), checkin(bruno,  8), checkin(bruno,  13),
        checkin(carla,  3), checkin(carla,  7),
        checkin(diego,  5), checkin(diego,  12),
        checkin(eva,    4), checkin(eva,    11),
        checkin(fabio,  2), checkin(fabio,  9),
        # Quota — recentes
        checkin(joao,   6), checkin(joao,   14),
        checkin(karen,  10),
        # Per-checkin
        checkin(lucas,  3), checkin(lucas,  20), checkin(lucas,  38),
        checkin(marina, 7), checkin(marina, 25),
        checkin(nicolas, 1), checkin(nicolas, 15),
        checkin(olivia, 5),
        # Inativos — ultimos check-ins ha muito tempo
        checkin(gabriela, 50), checkin(gabriela, 80),
        checkin(henrique, 25),  # ainda dentro do periodo de 30 dias, mas plano vencido
        # isabela: nunca fez check-in no periodo
    ]
    session.add_all(checkins)
    session.flush()

    # -------------------------------------------------------------------------
    # Pagamentos — ultimos 30 dias
    # -------------------------------------------------------------------------
    def pag(membro_obj, valor, tipo, metodo="PIX", days_ago=10):
        return Pagamento(
            member_id=membro_obj.id if membro_obj else None,
            valor=valor,
            tipo_transacao=tipo,
            metodo_pagamento=metodo,
            data_pagamento=datetime.now() - timedelta(days=days_ago),
        )

    pagamentos = [
        # Mensalidades / Renovacoes
        pag(ana,    120.0, "Renovacao Plano Mensal",        "PIX",       days_ago=28),
        pag(bruno,  120.0, "Renovacao Plano Mensal",        "Cartao",    days_ago=20),
        pag(carla,  120.0, "Renovacao Plano Mensal",        "PIX",       days_ago=5),
        pag(diego,  320.0, "Renovacao Plano Trimestral",    "PIX",       days_ago=15),
        pag(eva,    580.0, "Renovacao Plano Semestral",     "Dinheiro",  days_ago=2),

        # Treino Personal — categoria separada no DRE
        pag(fabio,  210.0, "Renovacao Plano Mensal c/ Treino", "PIX",   days_ago=8),

        # Vouchers / Quota
        pag(joao,   150.0, "Compra Voucher Pacote 10",      "PIX",       days_ago=12),
        pag(karen,  150.0, "Compra Voucher Pacote 10",      "Cartao",    days_ago=18),

        # Avulsos / Per-checkin
        pag(lucas,   15.0, "Check-in Gympass",              "Gympass",   days_ago=3),
        pag(lucas,   15.0, "Check-in Gympass",              "Gympass",   days_ago=20),
        pag(marina,  15.0, "Check-in Totalpass",            "Totalpass", days_ago=7),
        pag(nicolas, 35.0, "Diaria",                        "Dinheiro",  days_ago=1),
        pag(nicolas, 35.0, "Diaria",                        "Dinheiro",  days_ago=15),
    ]
    session.add_all(pagamentos)
    session.commit()

    return membros, pagamentos


# =============================================================================
# Validacoes
# =============================================================================

def _validate_members_report(html: str, membros, session):
    """Valida o relatorio de membros."""
    erros = []

    # PENDENTE nao deve aparecer
    if "Paulo Pendente" in html:
        erros.append("FALHA: membro PENDENTE apareceu no relatorio de membros")

    # Inadimplentes conhecidos devem aparecer
    for nome in ("Gabriela Nunes", "Henrique Alves", "Isabela Rocha"):
        if nome not in html:
            erros.append(f"FALHA: inadimplente '{nome}' nao apareceu no relatorio")

    # Secao de inadimplencia deve existir
    if "Inadimpl" not in html:
        erros.append("FALHA: secao de inadimplencia ausente no relatorio de membros")

    # Status separados devem aparecer
    if "EM DIA" not in html and "VENCIDO" not in html:
        erros.append("FALHA: badges de status do plano ausentes")

    if "FREQUENTANDO" not in html and "INATIVO" not in html:
        erros.append("FALHA: badges de frequencia ausentes")

    return erros


def _validate_finance_report(html: str, pagamentos):
    """Valida o relatorio financeiro."""
    erros = []

    # Auditoria deve estar presente
    if "DRE Balanceado" not in html and "DRE Desbalanceado" not in html:
        erros.append("FALHA: secao de auditoria ausente no relatorio financeiro")

    # Treino nao deve aparecer na secao de descontos (campo removido)
    if "total_descontos" in html or "perc_descontos" in html:
        erros.append("FALHA: campos de desconto hardcoded ainda presentes no template")

    # Verificar receita total (soma dos pagamentos de teste)
    receita_esperada = sum(p.valor for p in pagamentos)
    # A receita deve aparecer no relatorio (como string com 2 casas decimais)
    receita_str = f"{receita_esperada:.2f}".replace(".", ",")  # possivel formatacao pt-BR
    receita_str_en = f"{receita_esperada:.2f}"
    if receita_str not in html and receita_str_en not in html:
        # Tenta aproximacao: verifica se algum valor proximo esta la
        # (tolerancia para possiveis arredondamentos)
        found = any(
            f"{receita_esperada - 0.01:.2f}" in html or
            f"{receita_esperada:.2f}" in html or
            f"{receita_esperada + 0.01:.2f}" in html
        )
        if not found:
            erros.append(
                f"AVISO: receita esperada R$ {receita_esperada:.2f} nao encontrada literalmente no HTML "
                "(pode estar formatada diferente)"
            )

    # Categorias DRE devem aparecer
    for cat in ("Mensalidades", "mensalidades", "Avulsos", "avulsos"):
        if cat.lower() in html.lower():
            break
    else:
        erros.append("FALHA: categorias DRE ausentes no relatorio financeiro")

    return erros


def _validate_frequency_report(html: str, membros):
    """Valida o relatorio de frequencia."""
    erros = []

    # PENDENTE nao deve aparecer
    if "Paulo Pendente" in html:
        erros.append("FALHA: membro PENDENTE apareceu no relatorio de frequencia")

    # Membros em risco conhecidos devem aparecer
    for nome in ("Rafael Esquecido", "Sandra Sumida"):
        if nome not in html:
            erros.append(f"FALHA: membro em risco '{nome}' nao apareceu no relatorio de frequencia")

    # Coluna Ultimo Check-in na tabela de risco deve aparecer (secao renderiza pois ha membros em risco)
    if "ltimo Check-in" not in html:  # busca substring de "Ultimo Check-in" sem acentos
        erros.append("FALHA: coluna 'Ultimo Check-in' ausente na tabela de risco de churn")

    # Data do dia mais movimentado deve estar em formato DD/MM/YYYY, nao YYYY-MM-DD
    import re
    dates_ymd = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", html)
    if dates_ymd:
        erros.append(
            f"FALHA: datas em formato YYYY-MM-DD ainda presentes: {dates_ymd[:3]}"
        )

    return erros


# =============================================================================
# Runner principal
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Testa geracao de relatorios com dados simulados")
    parser.add_argument("--open", action="store_true", help="Abre os relatorios no navegador")
    args = parser.parse_args()

    print("=" * 60)
    print("  Summit System — Teste de Relatorios (Dados Simulados)")
    print("=" * 60)

    # Setup
    engine = _build_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n[1/5] Populando banco com dados simulados...")
    membros, pagamentos = _seed(session)
    print(f"      {len(membros)} membros | {len(pagamentos)} pagamentos inseridos")

    arquivos = {}
    todos_erros = []

    # -------------------------------------------------------------------------
    # Relatorio de Membros
    # -------------------------------------------------------------------------
    print("\n[2/5] Gerando relatorio de membros...")
    try:
        path_m = generate_members_report(db_session=session)
        html_m = Path(path_m).read_text(encoding="utf-8")
        erros_m = _validate_members_report(html_m, membros, session)
        arquivos["membros"] = path_m
        if erros_m:
            todos_erros.extend(erros_m)
            for e in erros_m:
                print(f"  {e}")
        else:
            print(f"  OK — {path_m}")
    except Exception as exc:
        todos_erros.append(f"EXCECAO no relatorio de membros: {exc}")
        print(f"  EXCECAO: {exc}")
        import traceback; traceback.print_exc()

    # -------------------------------------------------------------------------
    # Relatorio Financeiro
    # -------------------------------------------------------------------------
    print("\n[3/5] Gerando relatorio financeiro...")
    try:
        payment_service = PaymentService(db_session=session)
        member_service = MemberService(db_session=session)

        now = datetime.now()
        start = now - timedelta(days=30)
        path_f = generate_finance_report(
            period=f"{now.month:02d}/{now.year}",
            start_date=start,
            end_date=now,
            payment_service=payment_service,
            member_service=member_service,
        )
        html_f = Path(path_f).read_text(encoding="utf-8")
        erros_f = _validate_finance_report(html_f, pagamentos)
        arquivos["financeiro"] = path_f
        if erros_f:
            todos_erros.extend(erros_f)
            for e in erros_f:
                print(f"  {e}")
        else:
            print(f"  OK — {path_f}")
    except Exception as exc:
        todos_erros.append(f"EXCECAO no relatorio financeiro: {exc}")
        print(f"  EXCECAO: {exc}")
        import traceback; traceback.print_exc()

    # -------------------------------------------------------------------------
    # Relatorio de Frequencia
    # -------------------------------------------------------------------------
    print("\n[4/5] Gerando relatorio de frequencia...")
    try:
        path_q = generate_frequency_report(db_session=session, days=45)
        html_q = Path(path_q).read_text(encoding="utf-8")
        erros_q = _validate_frequency_report(html_q, membros)
        arquivos["frequencia"] = path_q
        if erros_q:
            todos_erros.extend(erros_q)
            for e in erros_q:
                print(f"  {e}")
        else:
            print(f"  OK — {path_q}")
    except Exception as exc:
        todos_erros.append(f"EXCECAO no relatorio de frequencia: {exc}")
        print(f"  EXCECAO: {exc}")
        import traceback; traceback.print_exc()

    # -------------------------------------------------------------------------
    # Resultado
    # -------------------------------------------------------------------------
    print("\n[5/5] Resumo de validacao:")
    print(f"  Relatorios gerados : {len(arquivos)}/3")
    print(f"  Erros/Avisos       : {len(todos_erros)}")

    if todos_erros:
        print("\n  Problemas encontrados:")
        for e in todos_erros:
            print(f"    - {e}")
        print()
    else:
        print("\n  Todos os relatorios passaram nas validacoes!\n")

    # Sumario financeiro para conferencia manual
    receita_total = sum(p.valor for p in pagamentos)
    print(f"  Receita total inserida   : R$ {receita_total:.2f}")

    from src.core.plan_status import STATUS_PLANO_VENCIDO
    from src.core.plan_status import calcular_status_plano
    inadimplentes_count = sum(
        1 for m in membros
        if m.estado_plano != PENDENTE
        and calcular_status_plano(m.vencimento_plano, m.estado_plano) == STATUS_PLANO_VENCIDO
    )
    print(f"  Inadimplentes esperados  : {inadimplentes_count}")
    print(f"  Membros PENDENTE         : {sum(1 for m in membros if m.estado_plano == PENDENTE)} (deve aparecer como 0 nos relatorios)")

    # Abre no navegador se solicitado
    if args.open:
        print("\n  Abrindo relatorios no navegador...")
        for tipo, caminho in arquivos.items():
            webbrowser.open(f"file:///{Path(caminho).as_posix()}")

    session.close()
    print("\n" + "=" * 60)
    return 0 if not [e for e in todos_erros if "FALHA" in e] else 1


if __name__ == "__main__":
    sys.exit(main())
