"""
Serviço de Pagamentos.

Encapsula toda a lógica de negócio relacionada à gestão financeira,
incluindo registro de pagamentos, relatórios e análises.

Este módulo utiliza SQLAlchemy para type safety e queries tipadas.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass

from sqlalchemy import func, and_, desc
from sqlalchemy.orm import Session

from src.data.models import Membro, Pagamento
from src.core.payment_constants import TIPO_RENOVACAO_PLANO
from src.utils.date_utils import coerce_to_date


@dataclass
class PaymentResult:
    """Resultado de uma operação de pagamento."""
    success: bool
    payment_id: Optional[int] = None
    message: str = ""


@dataclass
class FinancialSummary:
    """Resumo financeiro."""
    total_receita: float
    total_transacoes: int
    ticket_medio: float


@dataclass
class RevenueBreakdown:
    """Item de breakdown de receita."""
    tipo_transacao: str
    total_valor: float
    quantidade: int


class PaymentService:
    """
    Serviço responsável por gerenciar operações de pagamentos.
    
    Regras de negócio encapsuladas:
    - Registro de pagamentos
    - Relatórios financeiros
    - Histórico de transações
    
    """

    def __init__(self, db_session: Session):
        """
        Inicializa o serviço de pagamentos.

        Args:
            db_session: Sessão SQLAlchemy para acesso aos dados
        """
        self._session = db_session

    @property
    def session(self) -> Optional[Session]:
        """Retorna a sessão SQLAlchemy se disponível."""
        return self._session
    
    # =========================================================================
    # MÉTODOS CRUD
    # =========================================================================
    
    def create_payment(
        self,
        member_id: Optional[int],
        valor: float,
        tipo_transacao: str,
        descricao: str = "",
        metodo_pagamento: str = "",
        nova_data_vencimento: Optional[str] = None,
        data_pagamento: Optional[datetime] = None
    ) -> PaymentResult:
        """
        Registra um novo pagamento.
        
        Args:
            member_id: ID do membro (None para vendas sem membro específico)
            valor: Valor do pagamento
            tipo_transacao: Tipo da transação (ex: "Renovação Plano", "Diária")
            descricao: Descrição detalhada
            metodo_pagamento: Método de pagamento (ex: "PIX", "Cartão")
            nova_data_vencimento: Nova data de vencimento (para renovações)
            data_pagamento: Data e hora do pagamento (usa data atual se None)
            
        Returns:
            PaymentResult com o resultado da operação
        """
        if data_pagamento is None:
            data_pagamento = datetime.now()
        
        return self._create_payment_sqlalchemy(
            member_id, valor, tipo_transacao, descricao,
            metodo_pagamento, nova_data_vencimento, data_pagamento
        )
    
    def register_plan_payment(
        self,
        member_id: int,
        plan_name: str,
        vencimento: Optional[str] = None,
        metodo_pagamento: str = "",
        tipo_transacao: str = TIPO_RENOVACAO_PLANO,
        descricao: Optional[str] = None,
        payment_date: Optional[datetime] = None
    ) -> PaymentResult:
        """
        Registra um pagamento de renovação de plano.
        
        Args:
            member_id: ID do membro
            plan_name: Nome do plano
            vencimento: Data de vencimento do plano
            metodo_pagamento: Método de pagamento
            tipo_transacao: Tipo da transação
            descricao: Descrição (gerada automaticamente se None)
            payment_date: Data do pagamento (usa data atual se None)
            
        Returns:
            PaymentResult com o resultado da operação
        """
        from src.services.plan_service import PlanService
        valor = PlanService(db_session=self._session).get_plan_price(plan_name)
        if valor <= 0:
            return PaymentResult(
                success=False,
                message=f"Plano '{plan_name}' não tem preço definido."
            )
        
        if descricao is None:
            descricao = f"{plan_name}"
        
        return self.create_payment(
            member_id=member_id,
            valor=valor,
            tipo_transacao=tipo_transacao,
            descricao=descricao,
            metodo_pagamento=metodo_pagamento,
            nova_data_vencimento=vencimento,
            data_pagamento=payment_date
        )
    
    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================
    
    def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> FinancialSummary:
        """
        Obtém um resumo financeiro para um período.
        
        Args:
            start_date: Data inicial (None para desde o início)
            end_date: Data final (None para até hoje)
            
        Returns:
            FinancialSummary com totais e médias
        """
        return self._get_summary_sqlalchemy(start_date, end_date)
    
    def get_breakdown(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[RevenueBreakdown]:
        """
        Obtém a receita agrupada por tipo de transação.
        
        Args:
            start_date: Data inicial (None para desde o início)
            end_date: Data final (None para até hoje)
            
        Returns:
            Lista de RevenueBreakdown por tipo de transação
        """
        return self._get_breakdown_sqlalchemy(start_date, end_date)
    
    def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista todas as transações em um período.
        
        Args:
            start_date: Data inicial (None para desde o início)
            end_date: Data final (None para até hoje)
            limit: Número máximo de transações a retornar
            
        Returns:
            Lista de dicionários com dados das transações
        """
        return self._get_transactions_sqlalchemy(start_date, end_date, limit)
    
    def get_member_history(self, member_id: int) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de pagamentos de um membro.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Lista de pagamentos do membro
        """
        return self._get_member_history_sqlalchemy(member_id)
    
    def get_today_total(self) -> float:
        """Retorna o total de receita de hoje."""
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
        summary = self.get_summary(start, end)
        return summary.total_receita
    
    def get_month_total(self, year: int = None, month: int = None) -> float:
        """Retorna o total de receita de um mês."""
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
        
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        summary = self.get_summary(start, end)
        return summary.total_receita
    
    # =========================================================================
    # IMPLEMENTAÇÃO SQLALCHEMY
    # =========================================================================
    
    def _create_payment_sqlalchemy(
        self,
        member_id: Optional[int],
        valor: float,
        tipo_transacao: str,
        descricao: str,
        metodo_pagamento: str,
        nova_data_vencimento: Optional[str],
        data_pagamento: datetime
    ) -> PaymentResult:
        """Cria um pagamento usando SQLAlchemy."""
        try:
            new_payment = Pagamento(
                member_id=member_id,
                data_pagamento=data_pagamento,
                tipo_transacao=tipo_transacao,
                descricao=descricao,
                valor=valor,
                metodo_pagamento=metodo_pagamento,
                nova_data_vencimento=coerce_to_date(nova_data_vencimento)
            )
            
            self._session.add(new_payment)
            self._session.commit()
            
            return PaymentResult(
                success=True,
                payment_id=new_payment.id,
                message="Pagamento registrado com sucesso."
            )
            
        except Exception as e:
            self._session.rollback()
            return PaymentResult(
                success=False,
                message=f"Erro ao registrar pagamento: {str(e)}"
            )
    
    def _get_summary_sqlalchemy(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> FinancialSummary:
        """Obtém resumo financeiro usando SQLAlchemy."""
        query = self._session.query(
            func.sum(Pagamento.valor).label('total'),
            func.count(Pagamento.id).label('count')
        )
        
        if start_date:
            query = query.filter(Pagamento.data_pagamento >= start_date)
        if end_date:
            query = query.filter(Pagamento.data_pagamento <= end_date)
        
        result = query.first()
        
        total_receita = result.total or 0.0
        total_transacoes = result.count or 0
        ticket_medio = total_receita / total_transacoes if total_transacoes > 0 else 0.0
        
        return FinancialSummary(
            total_receita=total_receita,
            total_transacoes=total_transacoes,
            ticket_medio=ticket_medio
        )
    
    def _get_breakdown_sqlalchemy(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[RevenueBreakdown]:
        """Obtém breakdown de receita usando SQLAlchemy."""
        query = self._session.query(
            Pagamento.tipo_transacao,
            func.sum(Pagamento.valor).label('total_valor'),
            func.count(Pagamento.id).label('quantidade')
        )
        
        if start_date:
            query = query.filter(Pagamento.data_pagamento >= start_date)
        if end_date:
            query = query.filter(Pagamento.data_pagamento <= end_date)
        
        results = query.group_by(Pagamento.tipo_transacao).order_by(
            desc('total_valor')
        ).all()
        
        return [
            RevenueBreakdown(
                tipo_transacao=r.tipo_transacao or 'N/A',
                total_valor=r.total_valor or 0.0,
                quantidade=r.quantidade or 0
            )
            for r in results
        ]
    
    def _get_transactions_sqlalchemy(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Lista transações usando SQLAlchemy."""
        query = self._session.query(Pagamento, Membro.nome).outerjoin(
            Membro, Pagamento.member_id == Membro.id
        )
        
        if start_date:
            query = query.filter(Pagamento.data_pagamento >= start_date)
        if end_date:
            query = query.filter(Pagamento.data_pagamento <= end_date)
        
        results = query.order_by(
            desc(Pagamento.data_pagamento)
        ).limit(limit).all()
        
        transactions = []
        for payment, member_nome in results:
            tx = payment.to_dict()
            tx['member_nome'] = member_nome
            transactions.append(tx)
        
        return transactions
    
    def _get_member_history_sqlalchemy(self, member_id: int) -> List[Dict[str, Any]]:
        """Obtém histórico de pagamentos de um membro usando SQLAlchemy."""
        payments = self._session.query(Pagamento).filter(
            Pagamento.member_id == member_id
        ).order_by(desc(Pagamento.data_pagamento)).all()
        
        return [p.to_dict() for p in payments]
