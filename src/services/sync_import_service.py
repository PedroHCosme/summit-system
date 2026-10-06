"""Pipeline de importação/sincronização isolada do runtime principal."""

from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from alembic import command
from alembic.config import Config
from dateutil.relativedelta import relativedelta
from src.config import (
    COL_CALCADO,
    COL_DATA_NASCIMENTO,
    COL_ESTADO_PLANO,
    COL_FREQUENCIA,
    COL_GENERO,
    COL_NOME,
    COL_PLANO,
    COL_VENCIMENTO_PLANO,
    COL_WHATSAPP,
)
from src.core.payment_constants import METODO_SINCRONIZACAO, TIPO_RENOVACAO_PLANO
from src.core.plan_policy import PlanPolicy
from src.core.plan_status import ATIVO, PENDENTE
from src.data.db import get_db_session
from src.data.legacy_sync_gateway import LegacySyncGateway
from src.data.models import Frequencia, Membro, Pagamento, Plano
from src.services.checkin_service import CheckinService
from src.utils.date_utils import coerce_to_date


ProgressCallback = Callable[[str, int], None]


class SyncImportService:
    """
    Orquestra sincronização de dados externos sem contaminar o core runtime.

    Esta classe concentra:
    - leitura legada (Sheets)
    - transformação para modelo canônico
    - persistência via SQLAlchemy
    """

    CHECKIN_DATA_START_COL = 4
    DAY_HEADER_ROW_INDEX = 1

    def __init__(
        self,
        gateway: LegacySyncGateway,
        sheet_names: List[str],
    ) -> None:
        self.gateway = gateway
        self.sheet_names = sheet_names

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def execute(self, progress_callback: Optional[ProgressCallback] = None) -> Dict[str, Any]:
        def emit(message: str, progress: int) -> None:
            if progress_callback:
                progress_callback(message, progress)

        emit("🔄 Conectando ao Google Sheets...", 5)
        if not self.gateway.connect_google_sheets():
            raise RuntimeError("❌ Erro ao autenticar no Google Sheets")

        emit("🔄 Conectando ao banco de dados local...", 10)
        if not self.gateway.connect_database():
            raise RuntimeError("❌ Erro ao conectar ao banco de dados")

        emit("🔄 Verificando estrutura do banco...", 15)
        if not self.gateway.ensure_database_schema():
            raise RuntimeError("❌ Erro ao criar/verificar tabelas")

        emit("🛠 Aplicando migrações (Alembic)...", 22)
        self._run_alembic_upgrade()

        emit("⚙️ Otimizando banco de dados...", 26)
        try:
            optimize_stats = self.gateway.optimize_database()
            indices_checked = optimize_stats.get("indices_processed", 0)
            emit(f"✓ Banco otimizado (índices verificados: {indices_checked})", 28)
        except Exception:
            emit("⚠️ Otimização automática falhou; prosseguindo com a sincronização", 28)

        emit("📊 Lendo dados do Google Sheets...", 30)
        consolidated_members = self._consolidate_members()
        emit(f"✓ {len(consolidated_members)} membros únicos encontrados", 45)

        emit("👥 Sincronizando membros...", 55)
        sync_result = self._sync_members(consolidated_members)
        emit(
            f"✓ {sync_result['novos']} novos, {sync_result['existentes']} existentes",
            75,
        )

        emit("📋 Sincronizando check-ins...", 82)
        checkin_result = self._sync_checkins(sync_result["mapeamento"])
        emit(f"✓ {checkin_result['novos']} novos check-ins", 96)

        emit("✅ Sincronização concluída!", 100)
        return {
            "membros_novos": sync_result["novos"],
            "membros_existentes": sync_result["existentes"],
            "membros_total": len(sync_result["mapeamento"]),
            "checkins_novos": checkin_result["novos"],
            "checkins_duplicados": checkin_result["duplicados"],
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }

    # ------------------------------------------------------------------
    # Infra helpers
    # ------------------------------------------------------------------

    def _run_alembic_upgrade(self) -> None:
        project_dir = Path(__file__).resolve().parents[2]
        alembic_cfg = Config(str(project_dir / "alembic.ini"))
        alembic_cfg.set_main_option(
            "script_location",
            str(project_dir / "alembic_migrations"),
        )
        command.upgrade(alembic_cfg, "head")

    # ------------------------------------------------------------------
    # Consolidation
    # ------------------------------------------------------------------

    @staticmethod
    def _get_safe_value(row: List[Any], col_index: int) -> str:
        if col_index < len(row) and row[col_index]:
            value = str(row[col_index]).strip()
            if value in ("----------", "---", "--", "N/A", "n/a", "#N/A"):
                return ""
            return value
        return ""

    def _consolidate_members(self) -> Dict[str, Dict[str, Any]]:
        consolidated: Dict[str, Dict[str, Any]] = {}

        for sheet_name in self.sheet_names:
            data = self.gateway.read_sheet(sheet_name, "A:CZ")
            if not data or len(data) <= 3:
                continue

            for row in data[3:]:
                nome = self._get_safe_value(row, COL_NOME)
                plano = self._get_safe_value(row, COL_PLANO)
                if not nome or not plano:
                    continue

                if nome not in consolidated:
                    consolidated[nome] = {"nome": nome}

                member_data = {
                    "plano": plano,
                    "vencimento_plano": self._get_safe_value(row, COL_VENCIMENTO_PLANO),
                    "estado_plano": self._get_safe_value(row, COL_ESTADO_PLANO),
                    "data_nascimento": self._get_safe_value(row, COL_DATA_NASCIMENTO),
                    "whatsapp": self._get_safe_value(row, COL_WHATSAPP),
                    "genero": self._get_safe_value(row, COL_GENERO),
                    "frequencia": self._get_safe_value(row, COL_FREQUENCIA),
                    "calcado": self._get_safe_value(row, COL_CALCADO),
                }
                for key, value in member_data.items():
                    if value:
                        consolidated[nome][key] = value
        return consolidated

    # ------------------------------------------------------------------
    # Member import
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_imported_state(raw_state: Optional[str], current_state: Optional[str]) -> str:
        normalized = (raw_state or "").strip().upper()
        if normalized == PENDENTE:
            return PENDENTE
        if (current_state or "").strip().upper() == PENDENTE:
            return PENDENTE
        # Evita reintroduzir semântica legada de INATIVO por vencimento no import.
        return ATIVO

    @staticmethod
    def _plan_duration(plan_name: Optional[str]) -> Optional[relativedelta]:
        durations = {
            "Mensal": relativedelta(months=1),
            "Mens. c/ Treino": relativedelta(months=1),
            "Trimestral": relativedelta(months=3),
            "Semestral": relativedelta(months=6),
            "Anual": relativedelta(years=1),
        }
        return durations.get(plan_name) if plan_name else None

    @staticmethod
    def _has_payment_for_due_date(session, member_id: int, due_date: date) -> bool:
        return (
            session.query(Pagamento.id)
            .filter(
                Pagamento.member_id == member_id,
                Pagamento.nova_data_vencimento == due_date,
            )
            .first()
            is not None
        )

    def _maybe_register_plan_payment(
        self,
        session,
        member: Membro,
        plan: Optional[Plano],
        policy: Optional[PlanPolicy],
        due_date: Optional[date],
        should_register: bool,
    ) -> None:
        if not should_register or not plan:
            return
        if (plan.preco or 0.0) <= 0:
            return
        if due_date is None:
            return
        if self._has_payment_for_due_date(session, member.id, due_date):
            return

        due_dt = datetime.combine(due_date, time(12, 0))
        duration = self._plan_duration(plan.nome)
        payment_date = due_dt - duration if duration else due_dt

        tipo_transacao = policy.renewal_transaction_type if policy else TIPO_RENOVACAO_PLANO
        payment = Pagamento(
            member_id=member.id,
            data_pagamento=payment_date,
            tipo_transacao=tipo_transacao,
            descricao=f"Plano: {plan.nome}",
            valor=plan.preco,
            metodo_pagamento=METODO_SINCRONIZACAO,
            nova_data_vencimento=due_date,
        )
        session.add(payment)

    def _sync_members(self, consolidated_members: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        membros_migrados: Dict[str, int] = {}
        novos = 0
        existentes = 0

        with get_db_session() as session:
            existing_members = session.query(Membro).all()
            existing_by_name = {m.nome: m for m in existing_members}
            plan_by_name = {p.nome: p for p in session.query(Plano).all()}

            for nome, data_dict in consolidated_members.items():
                member = existing_by_name.get(nome)
                is_new = member is None

                if is_new:
                    member = Membro(nome=nome, data_cadastro=date.today())
                    session.add(member)
                    session.flush()
                    existing_by_name[nome] = member

                old_plan = member.plano
                old_due = member.vencimento_plano

                plan_name = data_dict.get("plano") or member.plano
                plan = plan_by_name.get(plan_name) if plan_name else None
                policy = PlanPolicy(plan) if plan else None

                due_date = coerce_to_date(data_dict.get("vencimento_plano"))
                if policy and not policy.requires_due_date:
                    due_date = None

                member.plano = plan_name
                member.plano_id = plan.id if plan else None
                member.vencimento_plano = due_date
                member.estado_plano = self._normalize_imported_state(
                    data_dict.get("estado_plano"),
                    member.estado_plano,
                )

                if data_dict.get("data_nascimento"):
                    member.data_nascimento = coerce_to_date(data_dict.get("data_nascimento"))
                if data_dict.get("whatsapp"):
                    member.whatsapp = data_dict.get("whatsapp")
                if data_dict.get("genero"):
                    member.genero = data_dict.get("genero")
                if data_dict.get("frequencia"):
                    member.frequencia = data_dict.get("frequencia")
                if data_dict.get("calcado"):
                    member.calcado = data_dict.get("calcado")

                changed = (old_plan != member.plano) or (old_due != member.vencimento_plano)
                self._maybe_register_plan_payment(
                    session=session,
                    member=member,
                    plan=plan,
                    policy=policy,
                    due_date=member.vencimento_plano,
                    should_register=is_new or changed,
                )

                membros_migrados[nome] = member.id
                if is_new:
                    novos += 1
                else:
                    existentes += 1

        return {"mapeamento": membros_migrados, "novos": novos, "existentes": existentes}

    # ------------------------------------------------------------------
    # Check-in import
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_sheet_month_year(sheet_name: str) -> Tuple[int, int]:
        month_map = {
            "Jan": 1,
            "Fev": 2,
            "Mar": 3,
            "Abr": 4,
            "Mai": 5,
            "Jun": 6,
            "Jul": 7,
            "Ago": 8,
            "Set": 9,
            "Out": 10,
            "Nov": 11,
            "Dez": 12,
        }
        month_abbr, yy = sheet_name.split("/")
        return month_map[month_abbr], int(f"20{yy}")

    @staticmethod
    def _time_from_period(period: str) -> time:
        p = (period or "").upper()
        if p == "T":
            return time(14, 0)
        if p == "N":
            return time(19, 0)
        return time(9, 0)

    def _sync_checkins(self, member_mapping: Dict[str, int]) -> Dict[str, int]:
        total_novos = 0
        total_duplicados = 0

        with get_db_session() as session:
            checkin_service = CheckinService(db_session=session)

            for sheet_name in self.sheet_names:
                data = self.gateway.read_sheet(sheet_name, "A:CZ")
                if not data or len(data) <= self.DAY_HEADER_ROW_INDEX:
                    continue

                month, year = self._parse_sheet_month_year(sheet_name)
                day_header_row = data[self.DAY_HEADER_ROW_INDEX]
                date_map: Dict[int, date] = {}

                for col_index in range(self.CHECKIN_DATA_START_COL, len(day_header_row)):
                    day_str = self._get_safe_value(day_header_row, col_index)
                    if day_str.isdigit():
                        try:
                            date_map[col_index] = date(year, month, int(day_str))
                        except ValueError:
                            continue

                for row in data[3:]:
                    nome = self._get_safe_value(row, COL_NOME)
                    if not nome:
                        continue
                    member_id = member_mapping.get(nome)
                    if not member_id:
                        continue
                    plano_na_aba = self._get_safe_value(row, COL_PLANO)

                    for check_col, check_date in date_map.items():
                        check_value = self._get_safe_value(row, check_col)
                        if not check_value or check_value.upper() in ("FALSE", "F"):
                            continue

                        period_value = self._get_safe_value(row, check_col + 1)
                        full_datetime = datetime.combine(
                            check_date,
                            self._time_from_period(period_value),
                        )

                        exists_exact = (
                            session.query(Frequencia.id)
                            .filter(
                                Frequencia.member_id == member_id,
                                Frequencia.checkin_datetime == full_datetime,
                            )
                            .first()
                            is not None
                        )
                        if exists_exact:
                            checkin_service.ensure_payment_for_checkin(
                                member_id=member_id,
                                checkin_datetime=full_datetime,
                                plan_context=plano_na_aba,
                            )
                            total_duplicados += 1
                            continue

                        result = checkin_service.perform_checkin(
                            member_id=member_id,
                            checkin_datetime=full_datetime,
                            plan_context=plano_na_aba,
                            consume_voucher=False,
                        )
                        if result.success:
                            total_novos += 1
                            continue
                        if "duplicado" in result.message.lower():
                            total_duplicados += 1
                            continue
                        raise RuntimeError(result.message)

        return {"novos": total_novos, "duplicados": total_duplicados}
