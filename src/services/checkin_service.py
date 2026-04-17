"""
Serviço de Check-in.

Encapsula toda a lógica de negócio relacionada ao check-in de membros,
incluindo validações, registro de presença e geração automática de pagamentos.

Este módulo utiliza SQLAlchemy para type safety e queries tipadas.
"""

from datetime import datetime, date
from typing import Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.data.models import Membro, Frequencia, Pagamento, Plano


@dataclass
class CheckinResult:
    """Resultado de uma operação de check-in."""
    success: bool
    checkin_id: Optional[int] = None
    message: str = ""
    payment_generated: bool = False
    payment_amount: Optional[float] = None


class CheckinService:
    """
    Serviço responsável por gerenciar operações de check-in.
    
    Regras de negócio encapsuladas:
    - Apenas 1 check-in por membro por dia é permitido
    - Planos por check-in (Diária, Gympass, Totalpass) geram pagamento automático
    - Validação de existência do membro
    
    Suporta dois modos de operação:
    - SQLAlchemy Session (recomendado para novo código)
    - DatabaseManager legado (para compatibilidade)
    """
    
    # Planos que geram pagamento por check-in
    # Importados dinamicamente do config para evitar dependência circular
    _per_checkin_plans: Optional[dict] = None
    
    def __init__(
        self, 
        db_session: Session
    ):
        """
        Inicializa o serviço de check-in usando obrigatoriamente SQLAlchemy.
        
        Args:
            db_session: Sessão SQLAlchemy para acesso aos dados
        """
        if db_session is None:
            raise ValueError("CheckinService requer db_session (SQLAlchemy)")
        self._session = db_session
    
    @property
    def session(self) -> Session:
        """Retorna a sessão SQLAlchemy."""
        return self._session
    
    @property
    def per_checkin_plans(self) -> dict:
        """Retorna os planos que cobram por check-in (lazy loading do banco)."""
        if self._per_checkin_plans is None:
            # Buscar do banco de dados (prioridade)
            plans = self.session.query(Plano).filter(
                Plano.valor_por_checkin > 0,
                Plano.ativo == True
            ).all()
            self._per_checkin_plans = {p.nome: p.valor_por_checkin for p in plans}
        return self._per_checkin_plans
    
    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================
    
    def validate_checkin(
        self,
        member_id: int,
        checkin_datetime: datetime
    ) -> Tuple[bool, str]:
        """
        Valida se um check-in pode ser realizado.
        """
        # Verificar se o membro existe
        member = self._get_member(member_id)
        if not member:
            return False, f"Membro com ID {member_id} não encontrado."
        
        member_name = member.nome
        
        # Verificar se já existe check-in no mesmo dia
        if self._has_checkin_today(member_id, checkin_datetime):
            checkin_date_str = checkin_datetime.strftime('%d/%m/%Y')
            return False, (
                f"Check-in duplicado detectado!\n"
                f"Membro '{member_name}' já fez check-in hoje ({checkin_date_str}).\n"
                f"Apenas 1 check-in por dia é permitido."
            )
        
        return True, ""
    
    def perform_checkin(
        self,
        member_id: int,
        checkin_datetime: Optional[datetime] = None,
        plan_context: Optional[str] = None,
        consume_voucher: bool = True
    ) -> CheckinResult:
        """
        Realiza o check-in completo de um membro.
        """
        if checkin_datetime is None:
            checkin_datetime = datetime.now()
        
        # Etapa 1: Validação
        is_valid, error_message = self.validate_checkin(member_id, checkin_datetime)
        if not is_valid:
            return CheckinResult(success=False, message=error_message)
        
        # Etapa 2: Buscar dados do membro
        member = self._get_member(member_id)
        if not member:
            return CheckinResult(
                success=False,
                message=f"Membro com ID {member_id} não encontrado."
            )
        
        member_name = member.nome
        member_plan = member.plano
        
        # Determinar qual plano usar para pagamento
        effective_plan = plan_context or member_plan
        
        # Etapa 3 & 4: Inserir check-in e gerar pagamento usando ORM
        return self._perform_checkin_sqlalchemy(
            member_id, checkin_datetime, member_name, effective_plan, consume_voucher
        )
    
    def ensure_payment_for_checkin(
        self,
        member_id: int,
        checkin_datetime: datetime,
        plan_context: Optional[str] = None
    ) -> bool:
        """
        Garante que existe um pagamento registrado para o check-in informado.
        """
        member = self._get_member(member_id)
        if not member:
            return False
        
        member_plan = member.plano
        effective_plan = plan_context or member_plan
        should_pay, normalized_plan, amount = self._should_generate_payment(effective_plan)
        
        if not should_pay:
            return True  # Não precisa de pagamento
        
        if self._payment_exists_for_checkin(member_id, checkin_datetime):
            return True  # Já existe
        
        # Criar pagamento
        member_name = member.nome
        descricao = f"Check-in - {normalized_plan}"
        if member_name:
            descricao += f" ({member_name})"
        
        self._create_payment(
            member_id=member_id,
            checkin_datetime=checkin_datetime,
            tipo_transacao=normalized_plan,
            descricao=descricao,
            valor=amount
        )
        
        return True
    
    # =========================================================================
    # MÉTODOS PRIVADOS - ABSTRAÇÃO DE DADOS
    # =========================================================================
    
    def _get_member(self, member_id: int) -> Optional[Membro]:
        """Obtém um membro por ID (SQLAlchemy)."""
        return self._session.query(Membro).filter(Membro.id == member_id).first()
    
    def _has_checkin_today(self, member_id: int, checkin_datetime: datetime) -> bool:
        """Verifica se o membro já fez check-in no dia da data informada."""
        checkin_date = checkin_datetime.date()
        count = self._session.query(Frequencia).filter(
            Frequencia.member_id == member_id,
            func.date(Frequencia.checkin_datetime) == checkin_date
        ).count()
        return count > 0
    
    def _payment_exists_for_checkin(self, member_id: int, checkin_datetime: datetime) -> bool:
        """Verifica se já existe um pagamento registrado para este check-in."""
        from src.core.payment_constants import METODO_CHECKIN
        checkin_date = checkin_datetime.date()
        
        count = self._session.query(Pagamento).filter(
            Pagamento.member_id == member_id,
            func.date(Pagamento.data_pagamento) == checkin_date,
            Pagamento.metodo_pagamento == METODO_CHECKIN
        ).count()
        return count > 0
    
    # =========================================================================
    # MÉTODOS PRIVADOS - LÓGICA DE NEGÓCIO
    # =========================================================================
    
    def _normalize_plan_for_payment(self, plan_name: Optional[str]) -> Optional[str]:
        """Normaliza o nome do plano para fins de cobrança por check-in."""
        from src.core.plan_utils import normalize_plan_for_payment
        return normalize_plan_for_payment(plan_name, self.per_checkin_plans)
    
    def _should_generate_payment(
        self, plan_name: Optional[str]
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """Determina se o plano deve gerar pagamento automático no check-in."""
        # Quota plans don't generate per-checkin payments
        if self._is_quota_plan(plan_name):
            return False, None, None
        
        normalized = self._normalize_plan_for_payment(plan_name)
        if normalized and normalized in self.per_checkin_plans:
            return True, normalized, self.per_checkin_plans[normalized]
        return False, None, None
    
    def _is_quota_plan(self, plan_name: Optional[str]) -> bool:
        """Check if plan is quota-based by querying the database."""
        if not plan_name:
            return False
        
        plan = self._session.query(Plano).filter(Plano.nome == plan_name).first()
        return plan.is_quota if plan else False
    
    # =========================================================================
    # MÉTODOS PRIVADOS - IMPLEMENTAÇÃO SQLALCHEMY
    # =========================================================================
    
    def _perform_checkin_sqlalchemy(
        self,
        member_id: int,
        checkin_datetime: datetime,
        member_name: str,
        effective_plan: str,
        consume_voucher: bool = True
    ) -> CheckinResult:
        """Implementação do check-in usando SQLAlchemy."""
        from src.core.payment_constants import METODO_CHECKIN
        try:
            # Fetch member first to check quota status
            member = self._session.query(Membro).filter(Membro.id == member_id).first()
            if not member:
                return CheckinResult(
                    success=False,
                    message=f"Membro com ID {member_id} não encontrado."
                )
            
            # Check if this is a quota-based plan
            is_quota = self._is_quota_plan(member.plano)
            voucher_warning = False
            remaining_balance = 0
            
            # Handle voucher credit deduction for quota plans
            if is_quota:
                current_credits = member.voucher_credits or 0
                if consume_voucher:
                    if current_credits > 0:
                        member.voucher_credits = current_credits - 1
                        remaining_balance = member.voucher_credits
                    else:
                        voucher_warning = True
                        remaining_balance = 0
                else:
                    # Not consuming, just reporting current balance
                    remaining_balance = current_credits
            
            # Inserir check-in
            new_checkin = Frequencia(
                member_id=member_id,
                checkin_datetime=checkin_datetime
            )
            self._session.add(new_checkin)
            self._session.flush()  # Para obter o ID gerado
            
            checkin_id = new_checkin.id
            
            # Verificar se precisa gerar pagamento (not for quota plans)
            payment_generated = False
            payment_amount = None
            
            if not is_quota:
                should_pay, normalized_plan, amount = self._should_generate_payment(effective_plan)
                
                if should_pay and not self._payment_exists_for_checkin(member_id, checkin_datetime):
                    descricao = f"Check-in - {normalized_plan}"
                    if member_name:
                        descricao += f" ({member_name})"
                    
                    new_payment = Pagamento(
                        member_id=member_id,
                        data_pagamento=checkin_datetime,
                        tipo_transacao=normalized_plan,
                        descricao=descricao,
                        valor=amount,
                        metodo_pagamento=METODO_CHECKIN
                    )
                    self._session.add(new_payment)
                    payment_generated = True
                    payment_amount = amount
            
            self._session.commit()
            
            # Build appropriate success message
            if is_quota:
                if voucher_warning:
                    message = "⚠️ ALERTA: Membro sem saldo de vouchers! Check-in registrado, mas saldo é 0."
                else:
                    message = f"✅ Bom treino! Restam {remaining_balance} vouchers."
            else:
                message = "Check-in registrado com sucesso!"
            
            return CheckinResult(
                success=True,
                checkin_id=checkin_id,
                message=message,
                payment_generated=payment_generated,
                payment_amount=payment_amount
            )
            
        except Exception as e:
            self._session.rollback()
            return CheckinResult(
                success=False,
                message=f"Erro ao registrar check-in: {str(e)}"
            )
    
    # =========================================================================
    # MÉTODOS PRIVADOS - CRIAÇÃO DE PAGAMENTO
    # =========================================================================
    
    def _create_payment(
        self,
        member_id: int,
        checkin_datetime: datetime,
        tipo_transacao: str,
        descricao: str,
        valor: float
    ) -> None:
        """Cria um pagamento (SQLAlchemy)."""
        from src.core.payment_constants import METODO_CHECKIN
        new_payment = Pagamento(
            member_id=member_id,
            data_pagamento=checkin_datetime,
            tipo_transacao=tipo_transacao,
            descricao=descricao,
            valor=valor,
            metodo_pagamento=METODO_CHECKIN
        )
        self._session.add(new_payment)
        self._session.commit()
    
    # =========================================================================
    # MÉTODOS ADICIONAIS DE CHECK-IN
    # =========================================================================
    
    def delete_checkin(self, checkin_id: int) -> CheckinResult:
        """
        Remove um registro de check-in.
        """
        try:
            checkin = self._session.query(Frequencia).filter(
                Frequencia.id == checkin_id
            ).first()
            
            if not checkin:
                return CheckinResult(
                    success=False,
                    message=f"Check-in com ID {checkin_id} não encontrado."
                )
            
            self._session.delete(checkin)
            self._session.commit()
            
            return CheckinResult(
                success=True,
                checkin_id=checkin_id,
                message="Check-in removido com sucesso."
            )
        except Exception as e:
            self._session.rollback()
            return CheckinResult(
                success=False,
                message=f"Erro ao remover check-in: {str(e)}"
            )
    
    def update_datetime(
        self, 
        checkin_id: int, 
        new_datetime: datetime
    ) -> CheckinResult:
        """
        Atualiza a data/hora de um check-in existente.
        """
        try:
            checkin = self._session.query(Frequencia).filter(
                Frequencia.id == checkin_id
            ).first()
            
            if not checkin:
                return CheckinResult(
                    success=False,
                    message=f"Check-in com ID {checkin_id} não encontrado."
                )
            
            checkin.checkin_datetime = new_datetime
            self._session.commit()
            
            return CheckinResult(
                success=True,
                checkin_id=checkin_id,
                message="Check-in atualizado com sucesso."
            )
        except Exception as e:
            self._session.rollback()
            return CheckinResult(
                success=False,
                message=f"Erro ao atualizar check-in: {str(e)}"
            )
    
    def get_member_history(self, member_id: int) -> list:
        """
        Busca o histórico de check-ins de um membro.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Lista de check-ins ordenados do mais recente ao mais antigo
        """
        checkins = self._session.query(Frequencia).filter(
            Frequencia.member_id == member_id
        ).order_by(Frequencia.checkin_datetime.desc()).all()
        return [c.to_dict() for c in checkins]
    
    def count_today(self) -> int:
        """
        Conta o número de check-ins realizados hoje.
        """
        today = date.today()
        
        return self._session.query(Frequencia).filter(
            func.date(Frequencia.checkin_datetime) == today
        ).count()
    
    def get_today_details(self) -> list:
        """
        Busca os detalhes de todos os check-ins de hoje.
        """
        today = date.today()
        
        results = self._session.query(
            Frequencia, Membro.nome, Membro.plano, Membro.estado_plano
        ).join(Membro, Frequencia.member_id == Membro.id).filter(
            func.date(Frequencia.checkin_datetime) == today
        ).order_by(Frequencia.checkin_datetime.desc()).all()
        
        return [
            {
                'id': f.id,
                'member_id': f.member_id,
                'nome': nome,
                'plano': plano,
                'estado_plano': estado_plano,
                'checkin_datetime': f.checkin_datetime.isoformat() if f.checkin_datetime else None
            }
            for f, nome, plano, estado_plano in results
        ]
    
    def get_by_date(self, date_str: str) -> list:
        """
        Busca check-ins de uma data específica.
        """
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return []
        
        results = self._session.query(
            Frequencia, Membro.nome, Membro.plano, Membro.estado_plano
        ).join(Membro, Frequencia.member_id == Membro.id).filter(
            func.date(Frequencia.checkin_datetime) == target_date
        ).order_by(Frequencia.checkin_datetime.desc()).all()
        
        return [
            {
                'id': f.id,
                'member_id': f.member_id,
                'nome': nome,
                'plano': plano,
                'estado_plano': estado_plano,
                'checkin_datetime': f.checkin_datetime.isoformat() if f.checkin_datetime else None
            }
            for f, nome, plano, estado_plano in results
        ]
    
    def get_recent(self, limit: int = 5) -> list:
        """
        Busca os últimos check-ins realizados.
        
        Args:
            limit: Número máximo de check-ins a retornar
            
        Returns:
            Lista dos últimos check-ins
        """
        results = self._session.query(
            Frequencia, Membro.nome, Membro.plano, Membro.estado_plano
        ).join(Membro, Frequencia.member_id == Membro.id).order_by(
            Frequencia.checkin_datetime.desc()
        ).limit(limit).all()
        
        return [
            {
                'id': f.id,
                'member_id': f.member_id,
                'nome': nome,
                'plano': plano,
                'estado_plano': estado_plano,
                'checkin_datetime': f.checkin_datetime.isoformat() if f.checkin_datetime else None
            }
            for f, nome, plano, estado_plano in results
        ]
    
    def get_today_list(self) -> list:
        """
        Busca todos os check-ins de hoje (alias para get_today_details).
        
        Returns:
            Lista de check-ins de hoje
        """
        return self.get_today_details()

