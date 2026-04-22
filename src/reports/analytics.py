"""Camada analitica compartilhada para relatorios de membros e financeiro."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.core.plan_status import (
    LIMIAR_INATIVO_AVULSO,
    LIMIAR_INATIVO_PADRAO,
    LIMIAR_INATIVO_QUOTA,
    PENDENTE,
    PLANOS_LIMIAR_AVULSO,
    STATUS_MEMBRO_ATIVO,
    STATUS_MEMBRO_INATIVO,
    STATUS_PLANO_VENCIDO,
    calcular_status_membro,
    calcular_status_plano,
)
from src.data.models import Frequencia, Membro, Pagamento
from src.services.plan_service import PlanService


SEGMENTO_MUITO_ATIVO = "muito_ativo"
SEGMENTO_ESTAVEL = "estavel"
SEGMENTO_RISCO_MODERADO = "risco_moderado"
SEGMENTO_RISCO_ALTO = "risco_alto"
SEGMENTO_REATIVACAO_URGENTE = "reativacao_urgente"

SEGMENTOS_ORDENADOS = [
    SEGMENTO_REATIVACAO_URGENTE,
    SEGMENTO_RISCO_ALTO,
    SEGMENTO_RISCO_MODERADO,
    SEGMENTO_MUITO_ATIVO,
    SEGMENTO_ESTAVEL,
]

_SEGMENTO_LABEL = {
    SEGMENTO_MUITO_ATIVO: "Muito ativo",
    SEGMENTO_ESTAVEL: "Estavel",
    SEGMENTO_RISCO_MODERADO: "Risco moderado",
    SEGMENTO_RISCO_ALTO: "Risco alto",
    SEGMENTO_REATIVACAO_URGENTE: "Reativacao urgente",
}

_PRIORIDADE_SEGMENTO = {
    SEGMENTO_REATIVACAO_URGENTE: "Alta",
    SEGMENTO_RISCO_ALTO: "Alta",
    SEGMENTO_RISCO_MODERADO: "Media",
    SEGMENTO_MUITO_ATIVO: "Baixa",
    SEGMENTO_ESTAVEL: "Baixa",
}


@dataclass
class MemberFeature:
    """Dados normalizados por membro para decisao de retencao."""

    member_id: int
    nome: str
    plano: str
    estado_plano: str
    status_plano: str
    status_membro: str
    checkins_periodo: int
    checkins_periodo_anterior: int
    trend_checkins: int
    ultimo_checkin: Optional[datetime]
    dias_desde_ultimo_checkin: int
    limiar_inatividade: int
    valor_receita_periodo: float
    valor_mensal_estimado: float
    is_pendente: bool
    segmento: str = SEGMENTO_ESTAVEL
    prioridade: str = "Baixa"
    reason_flags: Optional[List[str]] = None

    def to_template_row(self) -> Dict[str, Any]:
        ultimo_checkin_display = "Nunca"
        if self.ultimo_checkin:
            ultimo_checkin_display = self.ultimo_checkin.strftime("%d/%m/%Y")
        return {
            "member_id": self.member_id,
            "nome": self.nome,
            "plano": self.plano,
            "status_plano": self.status_plano,
            "status_membro": self.status_membro,
            "checkins_periodo": self.checkins_periodo,
            "trend_checkins": self.trend_checkins,
            "dias_desde_ultimo_checkin": self.dias_desde_ultimo_checkin,
            "ultimo_checkin": ultimo_checkin_display,
            "segmento": self.segmento,
            "segmento_label": _SEGMENTO_LABEL[self.segmento],
            "prioridade": self.prioridade,
            "valor_receita_periodo": self.valor_receita_periodo,
            "valor_mensal_estimado": self.valor_mensal_estimado,
            "reason_flags": self.reason_flags or [],
        }


def to_date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


def period_bounds(
    start_date: date | datetime,
    end_date: date | datetime,
) -> Tuple[datetime, datetime]:
    """Normaliza periodo para [00:00:00, 23:59:59.999999]."""
    start = to_date(start_date)
    end = to_date(end_date)
    return datetime.combine(start, time.min), datetime.combine(end, time.max)


def previous_period_bounds(
    start_date: date | datetime,
    end_date: date | datetime,
) -> Tuple[datetime, datetime]:
    """Retorna periodo anterior com mesmo comprimento (inclusive)."""
    start = to_date(start_date)
    end = to_date(end_date)
    days = max((end - start).days + 1, 1)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    return datetime.combine(prev_start, time.min), datetime.combine(prev_end, time.max)


def percentile_nearest_rank(values: List[int], quantile: float) -> int:
    """Percentil pelo metodo nearest-rank (estavel para amostras pequenas)."""
    if not values:
        return 0
    ordered = sorted(values)
    rank = max(1, ceil(quantile * len(ordered)))
    return ordered[rank - 1]


class ReportAnalyticsService:
    """Servico OO compartilhado para metricas e segmentacao de retencao."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.plan_service = PlanService(db_session=db_session)
        self.planos_dict = self.plan_service.get_plans_as_dict()

    def compute_member_features(
        self,
        start_date: date | datetime,
        end_date: date | datetime,
    ) -> Dict[str, Any]:
        """Computa features normalizadas, segmentos e filas de acao."""
        start_dt, end_dt = period_bounds(start_date, end_date)
        prev_start_dt, prev_end_dt = previous_period_bounds(start_date, end_date)
        period_days = max((end_dt.date() - start_dt.date()).days + 1, 1)

        ultimo_checkin_sq = (
            self.db_session.query(
                Frequencia.member_id,
                func.max(Frequencia.checkin_datetime).label("ultimo_checkin"),
            )
            .group_by(Frequencia.member_id)
            .subquery()
        )
        checkins_periodo_sq = (
            self.db_session.query(
                Frequencia.member_id,
                func.count(Frequencia.id).label("checkins_periodo"),
            )
            .filter(
                and_(
                    Frequencia.checkin_datetime >= start_dt,
                    Frequencia.checkin_datetime <= end_dt,
                )
            )
            .group_by(Frequencia.member_id)
            .subquery()
        )
        checkins_prev_sq = (
            self.db_session.query(
                Frequencia.member_id,
                func.count(Frequencia.id).label("checkins_prev"),
            )
            .filter(
                and_(
                    Frequencia.checkin_datetime >= prev_start_dt,
                    Frequencia.checkin_datetime <= prev_end_dt,
                )
            )
            .group_by(Frequencia.member_id)
            .subquery()
        )
        receita_periodo_sq = (
            self.db_session.query(
                Pagamento.member_id,
                func.sum(Pagamento.valor).label("receita_periodo"),
            )
            .filter(
                and_(
                    Pagamento.data_pagamento >= start_dt,
                    Pagamento.data_pagamento <= end_dt,
                )
            )
            .group_by(Pagamento.member_id)
            .subquery()
        )

        rows = (
            self.db_session.query(
                Membro,
                ultimo_checkin_sq.c.ultimo_checkin,
                checkins_periodo_sq.c.checkins_periodo,
                checkins_prev_sq.c.checkins_prev,
                receita_periodo_sq.c.receita_periodo,
            )
            .outerjoin(ultimo_checkin_sq, Membro.id == ultimo_checkin_sq.c.member_id)
            .outerjoin(checkins_periodo_sq, Membro.id == checkins_periodo_sq.c.member_id)
            .outerjoin(checkins_prev_sq, Membro.id == checkins_prev_sq.c.member_id)
            .outerjoin(receita_periodo_sq, Membro.id == receita_periodo_sq.c.member_id)
            .filter(Membro.estado_plano != PENDENTE)
            .all()
        )

        features: List[MemberFeature] = []
        for membro, ultimo_checkin, checkins_periodo, checkins_prev, receita_periodo in rows:
            plano_nome = membro.plano or "Sem Plano"
            plano_info = self.planos_dict.get(plano_nome, {})
            is_quota = bool(plano_info.get("is_quota", False))
            valor_por_checkin = float(plano_info.get("valor_por_checkin", 0.0) or 0.0)
            preco_plano = float(plano_info.get("preco", 0.0) or 0.0)

            status_plano = calcular_status_plano(
                vencimento_plano=membro.vencimento_plano,
                estado_plano_db=membro.estado_plano,
                is_quota=is_quota,
                valor_por_checkin=valor_por_checkin,
            )
            status_membro = calcular_status_membro(
                plano_nome=plano_nome,
                ultimo_checkin=ultimo_checkin,
                voucher_credits=membro.voucher_credits or 0,
                is_quota=is_quota,
                valor_por_checkin=valor_por_checkin,
            )
            limiar = self._limiar_por_plano(plano_nome, is_quota, valor_por_checkin)
            dias_sem_checkin = self._dias_desde_ultimo_checkin(ultimo_checkin, limiar)
            checkins_atual = int(checkins_periodo or 0)
            checkins_anterior = int(checkins_prev or 0)

            feature = MemberFeature(
                member_id=membro.id,
                nome=membro.nome or "Sem Nome",
                plano=plano_nome,
                estado_plano=membro.estado_plano or "",
                status_plano=status_plano,
                status_membro=status_membro,
                checkins_periodo=checkins_atual,
                checkins_periodo_anterior=checkins_anterior,
                trend_checkins=checkins_atual - checkins_anterior,
                ultimo_checkin=ultimo_checkin,
                dias_desde_ultimo_checkin=dias_sem_checkin,
                limiar_inatividade=limiar,
                valor_receita_periodo=float(receita_periodo or 0.0),
                valor_mensal_estimado=self._estimar_valor_mensal(
                    preco_plano=preco_plano,
                    valor_por_checkin=valor_por_checkin,
                    checkins_periodo=checkins_atual,
                    period_days=period_days,
                ),
                is_pendente=False,
            )
            features.append(feature)

        p90 = percentile_nearest_rank([f.checkins_periodo for f in features], 0.9)
        for feature in features:
            segment, reasons = self._assign_segment(feature, p90)
            feature.segmento = segment
            feature.reason_flags = reasons
            feature.prioridade = _PRIORIDADE_SEGMENTO[segment]

        return {
            "member_features": features,
            "p90_checkins": p90,
            "executive_summary": self._build_executive_summary(features),
            "segment_distribution": self._build_segment_distribution(features),
            "action_queues": self._build_action_queues(features),
            "outreach_scripts": self._build_outreach_scripts(),
            "retention_recommendations": self._build_retention_recommendations(features),
            "list_data": [f.to_template_row() for f in sorted(features, key=self._sort_rows)],
            "comparison_previous_period": {
                "start_date": prev_start_dt.strftime("%d/%m/%Y"),
                "end_date": prev_end_dt.strftime("%d/%m/%Y"),
                "period_days": period_days,
            },
        }

    def _assign_segment(self, feature: MemberFeature, p90: int) -> Tuple[str, List[str]]:
        reasons: List[str] = []
        if feature.dias_desde_ultimo_checkin > feature.limiar_inatividade + 30:
            reasons.append(
                f"Sem check-in ha {feature.dias_desde_ultimo_checkin} dias (>{feature.limiar_inatividade + 30})"
            )
            return SEGMENTO_REATIVACAO_URGENTE, reasons

        if (
            feature.dias_desde_ultimo_checkin > feature.limiar_inatividade + 14
            or (
                feature.status_plano == STATUS_PLANO_VENCIDO
                and feature.dias_desde_ultimo_checkin > 14
            )
        ):
            reasons.append("Indicadores de risco alto de churn")
            if feature.status_plano == STATUS_PLANO_VENCIDO:
                reasons.append("Plano vencido + sem check-in recente")
            return SEGMENTO_RISCO_ALTO, reasons

        if (
            feature.status_membro == STATUS_MEMBRO_INATIVO
            or feature.dias_desde_ultimo_checkin > feature.limiar_inatividade
        ):
            reasons.append("Queda de frequencia acima do limiar do plano")
            return SEGMENTO_RISCO_MODERADO, reasons

        if feature.checkins_periodo >= p90 and feature.checkins_periodo >= 4:
            reasons.append(f"Acima do P90 de frequencia no periodo ({p90})")
            return SEGMENTO_MUITO_ATIVO, reasons

        reasons.append("Comportamento estavel no periodo")
        return SEGMENTO_ESTAVEL, reasons

    @staticmethod
    def _dias_desde_ultimo_checkin(ultimo_checkin: Optional[datetime], limiar: int) -> int:
        if not ultimo_checkin:
            return limiar + 365
        return max((date.today() - ultimo_checkin.date()).days, 0)

    @staticmethod
    def _limiar_por_plano(plano_nome: str, is_quota: bool, valor_por_checkin: float) -> int:
        if is_quota:
            return LIMIAR_INATIVO_QUOTA
        if valor_por_checkin > 0 or plano_nome in PLANOS_LIMIAR_AVULSO:
            return LIMIAR_INATIVO_AVULSO
        return LIMIAR_INATIVO_PADRAO

    @staticmethod
    def _estimar_valor_mensal(
        preco_plano: float,
        valor_por_checkin: float,
        checkins_periodo: int,
        period_days: int,
    ) -> float:
        if valor_por_checkin > 0:
            media_dia = checkins_periodo / max(period_days, 1)
            estimado = valor_por_checkin * media_dia * 30
            return round(max(estimado, valor_por_checkin * 4), 2)
        return round(max(preco_plano, 0.0), 2)

    @staticmethod
    def _build_executive_summary(features: List[MemberFeature]) -> Dict[str, Any]:
        total = len(features)
        ativos = sum(1 for f in features if f.status_membro == STATUS_MEMBRO_ATIVO)
        inativos = total - ativos
        at_risk = sum(
            1
            for f in features
            if f.segmento in (SEGMENTO_RISCO_MODERADO, SEGMENTO_RISCO_ALTO, SEGMENTO_REATIVACAO_URGENTE)
        )
        return {
            "total_base": total,
            "ativos": ativos,
            "inativos": inativos,
            "at_risk_count": at_risk,
            "reativacao_oportunidade_count": sum(
                1 for f in features if f.segmento == SEGMENTO_REATIVACAO_URGENTE
            ),
        }

    @staticmethod
    def _build_segment_distribution(features: List[MemberFeature]) -> Dict[str, Any]:
        total = len(features)
        raw_counts = {segment: 0 for segment in SEGMENTOS_ORDENADOS}
        for feature in features:
            raw_counts[feature.segmento] += 1
        items = []
        for segment in SEGMENTOS_ORDENADOS:
            count = raw_counts[segment]
            pct = round((count / total * 100), 1) if total > 0 else 0.0
            items.append(
                {
                    "segment": segment,
                    "label": _SEGMENTO_LABEL[segment],
                    "count": count,
                    "pct": pct,
                }
            )
        return {"total": total, "items": items, "counts": raw_counts}

    @staticmethod
    def _build_action_queues(features: List[MemberFeature]) -> Dict[str, List[Dict[str, Any]]]:
        queues: Dict[str, List[Dict[str, Any]]] = {segment: [] for segment in SEGMENTOS_ORDENADOS}
        for feature in features:
            queue_item = feature.to_template_row()
            queue_item["canal_sugerido"] = ReportAnalyticsService._suggest_channel(feature.segmento)
            queue_item["acao_sugerida"] = ReportAnalyticsService._suggest_action(feature.segmento)
            queue_item["script_key"] = feature.segmento
            queues[feature.segmento].append(queue_item)

        for segment, rows in queues.items():
            if segment == SEGMENTO_MUITO_ATIVO:
                rows.sort(key=lambda row: row["checkins_periodo"], reverse=True)
            else:
                rows.sort(
                    key=lambda row: (row["dias_desde_ultimo_checkin"], row["valor_mensal_estimado"]),
                    reverse=True,
                )
        return queues

    @staticmethod
    def _build_outreach_scripts() -> Dict[str, str]:
        return {
            SEGMENTO_REATIVACAO_URGENTE: (
                "Oi, {nome}! Sentimos sua falta na Summit. Faz {dias_desde_ultimo_checkin} dias sem check-in. "
                "Podemos te ajudar a voltar com um plano rapido para essa semana?"
            ),
            SEGMENTO_RISCO_ALTO: (
                "Oi, {nome}! Notei que seu ritmo caiu e quero te ajudar a manter consistencia. "
                "Que tal alinharmos dois horarios fixos para voce essa semana?"
            ),
            SEGMENTO_RISCO_MODERADO: (
                "Oi, {nome}! Tudo bem? Seu plano {plano} segue ativo, mas vimos menos check-ins recentemente. "
                "Quer que eu te sugira uma rotina leve para retomar?"
            ),
            SEGMENTO_MUITO_ATIVO: (
                "Oi, {nome}! Parabens pelo ritmo excelente nesse periodo. "
                "Queremos te reconhecer com uma acao especial de fidelidade."
            ),
            SEGMENTO_ESTAVEL: (
                "Oi, {nome}! Passando para reforcar que estamos aqui para manter seu progresso. "
                "Se quiser, montamos metas simples para o proximo mes."
            ),
        }

    @staticmethod
    def _build_retention_recommendations(features: List[MemberFeature]) -> List[Dict[str, Any]]:
        total = max(len(features), 1)
        urgentes = [f for f in features if f.segmento == SEGMENTO_REATIVACAO_URGENTE]
        alto = [f for f in features if f.segmento == SEGMENTO_RISCO_ALTO]
        moderado = [f for f in features if f.segmento == SEGMENTO_RISCO_MODERADO]
        muito_ativos = [f for f in features if f.segmento == SEGMENTO_MUITO_ATIVO]

        recs: List[Dict[str, Any]] = []
        if len(urgentes) > 0:
            recs.append(
                {
                    "titulo": "Forca-tarefa de reativacao em 72h",
                    "descricao": f"Contato imediato com {len(urgentes)} membros de reativacao urgente.",
                    "impacto": "alto",
                    "esforco": "rapido",
                }
            )
        if len(alto) / total >= 0.2:
            recs.append(
                {
                    "titulo": "Campanha de risco alto com oferta de retorno",
                    "descricao": f"{len(alto)} membros em risco alto. Priorizar WhatsApp + follow-up.",
                    "impacto": "alto",
                    "esforco": "medio",
                }
            )
        if len(moderado) > 0:
            recs.append(
                {
                    "titulo": "Sequencia preventiva para risco moderado",
                    "descricao": f"Criar rotina de contato semanal para {len(moderado)} membros.",
                    "impacto": "medio",
                    "esforco": "rapido",
                }
            )
        if len(muito_ativos) > 0:
            recs.append(
                {
                    "titulo": "Programa de fidelidade para muito ativos",
                    "descricao": f"Retencao e upsell para {len(muito_ativos)} membros de alta frequencia.",
                    "impacto": "medio",
                    "esforco": "medio",
                }
            )
        if not recs:
            recs.append(
                {
                    "titulo": "Base estavel: manter monitoramento semanal",
                    "descricao": "Sem sinais fortes de risco, focar consistencia operacional.",
                    "impacto": "baixo",
                    "esforco": "rapido",
                }
            )
        return recs[:5]

    @staticmethod
    def _suggest_channel(segment: str) -> str:
        if segment == SEGMENTO_REATIVACAO_URGENTE:
            return "WhatsApp + ligacao"
        if segment == SEGMENTO_RISCO_ALTO:
            return "WhatsApp"
        if segment == SEGMENTO_RISCO_MODERADO:
            return "WhatsApp"
        if segment == SEGMENTO_MUITO_ATIVO:
            return "WhatsApp"
        return "WhatsApp"

    @staticmethod
    def _suggest_action(segment: str) -> str:
        if segment == SEGMENTO_REATIVACAO_URGENTE:
            return "Contato imediato com proposta de retorno"
        if segment == SEGMENTO_RISCO_ALTO:
            return "Plano de retorno com agenda fixa"
        if segment == SEGMENTO_RISCO_MODERADO:
            return "Mensagem preventiva e reforco de rotina"
        if segment == SEGMENTO_MUITO_ATIVO:
            return "Acao de fidelidade e reconhecimento"
        return "Monitorar e manter engajamento"

    @staticmethod
    def _sort_rows(feature: MemberFeature) -> Tuple[int, int, float]:
        weight = {
            SEGMENTO_REATIVACAO_URGENTE: 0,
            SEGMENTO_RISCO_ALTO: 1,
            SEGMENTO_RISCO_MODERADO: 2,
            SEGMENTO_MUITO_ATIVO: 3,
            SEGMENTO_ESTAVEL: 4,
        }
        return (
            weight.get(feature.segmento, 99),
            -feature.dias_desde_ultimo_checkin,
            -feature.valor_mensal_estimado,
        )

