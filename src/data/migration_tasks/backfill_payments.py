"""Backfill historical plan payments for members with recurring plans."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, List, Optional

from src.config import PLANOS_PAGAMENTO_POR_CHECKIN
from src.core.payment_constants import TIPO_RENOVACAO_PLANO
from src.data.database_manager import DatabaseManager
from src.utils.date_utils import parse_date_to_date


@dataclass
class _MemberInfo:
    member_id: int
    name: str
    plan: Optional[str]
    vencimento: Optional[str]


def _ensure_connection(db: DatabaseManager) -> None:
    if not db.connection and not db.connect():
        raise RuntimeError("Não foi possível conectar ao banco para o backfill de pagamentos")


def _fetch_members(db: DatabaseManager) -> List[_MemberInfo]:
    if not db.connection:
        raise RuntimeError("Conexão com o banco não inicializada")
    cursor = db.connection.cursor()
    try:
        cursor.execute(
            """
            SELECT id, nome, plano, vencimento_plano
            FROM membros
            WHERE plano IS NOT NULL AND plano != ''
            """
        )
        return [
            _MemberInfo(
                member_id=row["id"],
                name=row["nome"],
                plan=row["plano"],
                vencimento=row["vencimento_plano"],
            )
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()


def _get_earliest_checkin_date(db: DatabaseManager, member_id: int) -> Optional[date]:
    if not db.connection:
        raise RuntimeError("Conexão com o banco não inicializada")
    cursor = db.connection.cursor()
    try:
        cursor.execute(
            """
            SELECT MIN(DATE(checkin_datetime))
            FROM frequencia
            WHERE member_id = ?
            """,
            (member_id,),
        )
        result = cursor.fetchone()
        value = result[0] if result else None
        return parse_date_to_date(value) if value else None
    finally:
        cursor.close()


def _has_checkins_between(
    db: DatabaseManager,
    member_id: int,
    start_date: date,
    end_date: date,
) -> bool:
    if not db.connection:
        raise RuntimeError("Conexão com o banco não inicializada")
    cursor = db.connection.cursor()
    try:
        cursor.execute(
            """
            SELECT 1
            FROM frequencia
            WHERE member_id = ?
              AND DATE(checkin_datetime) >= ?
              AND DATE(checkin_datetime) < ?
            LIMIT 1
            """,
            (member_id, start_date.isoformat(), end_date.isoformat()),
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def _has_per_checkin_payments(
    db: DatabaseManager,
    member_id: int,
    start_date: date,
    end_date: date,
) -> bool:
    if not db.connection:
        raise RuntimeError("Conexão com o banco não inicializada")
    per_checkin_types = list(PLANOS_PAGAMENTO_POR_CHECKIN.keys())
    if not per_checkin_types:
        return False

    placeholders = ",".join("?" for _ in per_checkin_types)
    cursor = db.connection.cursor()
    try:
        cursor.execute(
            f"""
            SELECT 1
            FROM pagamentos
            WHERE member_id = ?
              AND tipo_transacao IN ({placeholders})
              AND DATE(data_pagamento) >= ?
              AND DATE(data_pagamento) < ?
            LIMIT 1
            """,
            (member_id, *per_checkin_types, start_date.isoformat(), end_date.isoformat()),
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def backfill_plan_payments(db: DatabaseManager, max_cycles: int = 60) -> Dict[str, int]:
    """Creates missing monthly/recurring plan payments going backwards in time."""
    _ensure_connection(db)

    stats = {
        "pagamentos_registrados": 0,
        "membros_processados": 0,
    }

    members = _fetch_members(db)
    for member in members:
        duration = DatabaseManager.get_plan_duration(member.plan)
        if not duration:
            continue

        due_date = parse_date_to_date(member.vencimento)
        if not due_date:
            continue

        earliest_checkin = _get_earliest_checkin_date(db, member.member_id)
        if not earliest_checkin:
            continue

        stats["membros_processados"] += 1

        current_due = due_date
        cycles = 0
        while cycles < max_cycles:
            cycle_start = current_due - duration
            if cycle_start >= current_due:
                break

            if cycle_start < earliest_checkin:
                break

            if not _has_checkins_between(db, member.member_id, cycle_start, current_due):
                break

            if _has_per_checkin_payments(db, member.member_id, cycle_start, current_due):
                break

            payment_id = db.auto_register_plan_payment(
                member_id=member.member_id,
                plan_name=member.plan,
                vencimento=current_due.strftime("%Y-%m-%d"),
                metodo_pagamento="Backfill Histórico",
                tipo_transacao=TIPO_RENOVACAO_PLANO,
                descricao=f"{member.plan} (retroativo)",
                payment_date=datetime.combine(cycle_start, datetime.min.time()).replace(hour=12),
            )

            if payment_id:
                stats["pagamentos_registrados"] += 1

            current_due = cycle_start
            cycles += 1

            if current_due <= earliest_checkin:
                break

    return stats
