"""Helpers compartilhados pelos geradores de relatório."""

from datetime import date
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import func

from src.core.plan_status import esta_arquivado
from src.data.models import Frequencia, Membro, Pagamento


def get_reports_dir() -> Path:
    project_root = Path(__file__).parent.parent.parent
    reports_dir = project_root / "relatorios"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def get_template_env() -> Environment:
    project_root = Path(__file__).parent.parent.parent
    templates_dir = project_root / "src" / "templates" / "reports"
    return Environment(loader=FileSystemLoader(str(templates_dir)))


def ids_arquivados(session, hoje: Optional[date] = None) -> set:
    """Ids dos Membros arquivados (regra em plan_status.esta_arquivado)."""
    ultimo_checkin = dict(
        session.query(Frequencia.member_id, func.max(Frequencia.checkin_datetime))
        .group_by(Frequencia.member_id).all()
    )
    ultimo_pagamento = dict(
        session.query(Pagamento.member_id, func.max(Pagamento.data_pagamento))
        .group_by(Pagamento.member_id).all()
    )
    return {
        m.id for m in session.query(Membro)
        if esta_arquivado(ultimo_checkin.get(m.id), ultimo_pagamento.get(m.id), m.vencimento_plano,
                          m.vencimento_treino, m.data_cadastro, hoje)
    }
