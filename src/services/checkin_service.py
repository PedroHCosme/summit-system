"""
Serviço de Check-in.

Encapsula toda a lógica de negócio relacionada ao check-in de membros,
incluindo validações, registro de presença e geração automática de pagamentos.

Este módulo utiliza SQLAlchemy para type safety e queries tipadas.
"""

from datetime import datetime, date
from typing import Optional, Tuple, Union, TYPE_CHECKING
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.data.models import Membro, Frequencia, Pagamento, Plano

if TYPE_CHECKING:
    from src.data.database_manager import DatabaseManager


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
        db_session: Optional[Session] = None,
        db_manager: Optional["DatabaseManager"] = None
    ):
        """
        Inicializa o serviço de check-in.
        
        Args:
            db_session: Sessão SQLAlchemy para acesso aos dados (preferencial)
            db_manager: Instância do DatabaseManager legado (compatibilidade)
        
        Raises:
            ValueError: Se nenhum dos parâmetros for fornecido
        """
        self._session = db_session
        self._db_manager = db_manager
        
        if db_session is None and db_manager is None:
            raise ValueError(
                "CheckinService requer db_session (SQLAlchemy) ou db_manager (legado)"
            )
    
    @property
    def session(self) -> Optional[Session]:
        """Retorna a sessão SQLAlchemy se disponível."""
        return self._session
    
    @property
    def per_checkin_plans(self) -> dict:
        """Retorna os planos que cobram por check-in (lazy loading do banco)."""
        if self._per_checkin_plans is None:
            if self.session:
                # Buscar do banco de dados (prioridade)
                plans = self.session.query(Plano).filter(
                    Plano.valor_por_checkin > 0,
                    Plano.ativo == True
                ).all()
                self._per_checkin_plans = {p.nome: p.valor_por_checkin for p in plans}
            else:
                # Fallback para config (modo legado)
                from src.config import PLANOS_PAGAMENTO_POR_CHECKIN
                self._per_checkin_plans = PLANOS_PAGAMENTO_POR_CHECKIN
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
        
        Args:
            member_id: ID do membro
            checkin_datetime: Data e hora do check-in
            
        Returns:
            Tupla (is_valid, error_message)
        """
        # Verificar se o membro existe
        member = self._get_member(member_id)
        if not member:
            return False, f"Membro com ID {member_id} não encontrado."
        
        # Obter nome do membro (suporta dict ou ORM)
        member_name = self._get_member_name(member, member_id)
        
        # Verificar se já existe check-in no mesmo dia
        if self._has_checkin_today(member_id, checkin_datetime):
            checkin_date_str = checkin_datetime.strftime('%d/%m/%Y')
            return False, (
                f"Check-in duplicado detectado!\n"
                f"Membro '{member_name}' já fez check-in hoje ({checkin_date_str}).\n"
                f"Apenas 1 check-in por dia é permitido."
            )
        
        # For quota plans, we allow check-in even with zero balance (per business rule)
        # The warning will be shown in the result message, not as a validation error
        
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
        
        Esta é a operação principal que:
        1. Valida se o check-in é permitido
        2. Insere o registro de frequência
        3. Gera pagamento automático se necessário (planos por check-in)
        
        Args:
            member_id: ID do membro
            checkin_datetime: Data/hora do check-in (default: agora)
            plan_context: Opcional - plano a considerar para pagamento
                         (sobrepõe o plano atual do membro)
        
        Returns:
            CheckinResult com o resultado da operação
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
        
        member_name = self._get_member_name(member, member_id)
        member_plan = self._get_member_plan(member)
        
        # Determinar qual plano usar para pagamento
        effective_plan = plan_context or member_plan
        
        # Etapa 3 & 4: Inserir check-in e gerar pagamento
        if self._session is not None:
            return self._perform_checkin_sqlalchemy(
                member_id, checkin_datetime, member_name, effective_plan, consume_voucher
            )
        else:
            return self._perform_checkin_legacy(
                member_id, checkin_datetime, member_name, effective_plan
            )
    
    def ensure_payment_for_checkin(
        self,
        member_id: int,
        checkin_datetime: datetime,
        plan_context: Optional[str] = None
    ) -> bool:
        """
        Garante que existe um pagamento registrado para o check-in informado.
        
        Útil para backfill ou correção de dados.
        
        Args:
            member_id: ID do membro
            checkin_datetime: Data/hora do check-in
            plan_context: Opcional - plano a considerar
            
        Returns:
            True se pagamento foi criado ou já existia
        """
        member = self._get_member(member_id)
        if not member:
            return False
        
        member_plan = self._get_member_plan(member)
        effective_plan = plan_context or member_plan
        should_pay, normalized_plan, amount = self._should_generate_payment(effective_plan)
        
        if not should_pay:
            return True  # Não precisa de pagamento
        
        if self._payment_exists_for_checkin(member_id, checkin_datetime):
            return True  # Já existe
        
        # Criar pagamento
        member_name = self._get_member_name(member, member_id)
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
    
    def _get_member(self, member_id: int) -> Optional[Union[Membro, dict]]:
        """Obtém um membro por ID (SQLAlchemy ou legado)."""
        if self._session is not None:
            return self._session.query(Membro).filter(Membro.id == member_id).first()
        else:
            return self._db_manager.get_member_by_id(member_id)
    
    def _get_member_name(self, member: Union[Membro, dict], member_id: int) -> str:
        """Extrai o nome do membro (suporta ORM ou dict)."""
        if isinstance(member, Membro):
            return member.nome or f"ID {member_id}"
        else:
            return member.get('nome', f'ID {member_id}')
    
    def _get_member_plan(self, member: Union[Membro, dict]) -> str:
        """Extrai o plano do membro (suporta ORM ou dict)."""
        if isinstance(member, Membro):
            return member.plano or ""
        else:
            return member.get('plano', '')
    
    def _has_checkin_today(self, member_id: int, checkin_datetime: datetime) -> bool:
        """Verifica se o membro já fez check-in no dia da data informada."""
        checkin_date = checkin_datetime.date()
        
        if self._session is not None:
            # SQLAlchemy
            count = self._session.query(Frequencia).filter(
                Frequencia.member_id == member_id,
                func.date(Frequencia.checkin_datetime) == checkin_date
            ).count()
            return count > 0
        else:
            # Legado
            if not self._db_manager.connection:
                return False
            cursor = self._db_manager.connection.cursor()
            cursor.execute("""
                SELECT id FROM frequencia
                WHERE member_id = ?
                AND DATE(checkin_datetime) = ?
            """, (member_id, checkin_date.isoformat()))
            return cursor.fetchone() is not None
    
    def _payment_exists_for_checkin(self, member_id: int, checkin_datetime: datetime) -> bool:
        """Verifica se já existe um pagamento registrado para este check-in."""
        checkin_date = checkin_datetime.date()
        
        if self._session is not None:
            # SQLAlchemy
            count = self._session.query(Pagamento).filter(
                Pagamento.member_id == member_id,
                func.date(Pagamento.data_pagamento) == checkin_date,
                Pagamento.metodo_pagamento == "Check-in"
            ).count()
            return count > 0
        else:
            # Legado
            if not self._db_manager.connection:
                return False
            cursor = self._db_manager.connection.cursor()
            cursor.execute("""
                SELECT id FROM pagamentos
                WHERE member_id = ?
                AND DATE(data_pagamento) = DATE(?)
                AND metodo_pagamento = 'Check-in'
            """, (member_id, checkin_datetime.strftime('%Y-%m-%d %H:%M:%S')))
            return cursor.fetchone() is not None
    
    # =========================================================================
    # MÉTODOS PRIVADOS - LÓGICA DE NEGÓCIO
    # =========================================================================
    
    def _normalize_plan_for_payment(self, plan_name: Optional[str]) -> Optional[str]:
        """Normaliza o nome do plano para fins de cobrança por check-in."""
        if not plan_name:
            return None
            
        plan_name = plan_name.strip()
        if not plan_name:
            return None
        
        # Verificar se é exatamente um plano por check-in
        if plan_name in self.per_checkin_plans:
            return plan_name
        
        # Tentar normalizar por palavras-chave
        lowered = plan_name.lower()
        if 'diária' in lowered:
            return 'Diária'
        if 'gympass' in lowered:
            return 'Gympass'
        if 'totalpass' in lowered:
            return 'Totalpass'
        
        return None
    
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
        
        if self._session is not None:
            plan = self._session.query(Plano).filter(Plano.nome == plan_name).first()
            return plan.is_quota if plan else False
        else:
            # Fallback: use plan_service for legacy mode
            from src.services.plan_service import get_plan_service
            return get_plan_service().is_quota_plan(plan_name)
    
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
                        metodo_pagamento="Check-in"
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
    # MÉTODOS PRIVADOS - IMPLEMENTAÇÃO LEGADO
    # =========================================================================
    
    def _perform_checkin_legacy(
        self,
        member_id: int,
        checkin_datetime: datetime,
        member_name: str,
        effective_plan: str
    ) -> CheckinResult:
        """Implementação do check-in usando DatabaseManager legado."""
        try:
            cursor = self._db_manager.connection.cursor()
            cursor.execute("""
                INSERT INTO frequencia (member_id, checkin_datetime)
                VALUES (?, ?)
            """, (member_id, checkin_datetime.strftime('%Y-%m-%d %H:%M:%S')))
            
            checkin_id = cursor.lastrowid
            
            # Verificar se precisa gerar pagamento
            payment_generated = False
            payment_amount = None
            
            should_pay, normalized_plan, amount = self._should_generate_payment(effective_plan)
            
            if should_pay and not self._payment_exists_for_checkin(member_id, checkin_datetime):
                descricao = f"Check-in - {normalized_plan}"
                if member_name:
                    descricao += f" ({member_name})"
                
                self._db_manager.add_payment(
                    member_id=member_id,
                    data_pagamento=checkin_datetime,
                    tipo_transacao=normalized_plan,
                    descricao=descricao,
                    valor=amount,
                    metodo_pagamento="Check-in"
                )
                payment_generated = True
                payment_amount = amount
            
            self._db_manager.connection.commit()
            
            return CheckinResult(
                success=True,
                checkin_id=checkin_id,
                message="Check-in registrado com sucesso!",
                payment_generated=payment_generated,
                payment_amount=payment_amount
            )
            
        except Exception as e:
            if self._db_manager.connection:
                self._db_manager.connection.rollback()
            return CheckinResult(
                success=False,
                message=f"Erro ao registrar check-in: {str(e)}"
            )
    
    def _create_payment(
        self,
        member_id: int,
        checkin_datetime: datetime,
        tipo_transacao: str,
        descricao: str,
        valor: float
    ) -> None:
        """Cria um pagamento (SQLAlchemy ou legado)."""
        if self._session is not None:
            new_payment = Pagamento(
                member_id=member_id,
                data_pagamento=checkin_datetime,
                tipo_transacao=tipo_transacao,
                descricao=descricao,
                valor=valor,
                metodo_pagamento="Check-in"
            )
            self._session.add(new_payment)
            self._session.commit()
        else:
            self._db_manager.add_payment(
                member_id=member_id,
                data_pagamento=checkin_datetime,
                tipo_transacao=tipo_transacao,
                descricao=descricao,
                valor=valor,
                metodo_pagamento="Check-in"
            )
            if self._db_manager.connection:
                self._db_manager.connection.commit()
    
    # =========================================================================
    # MÉTODOS ADICIONAIS DE CHECK-IN
    # =========================================================================
    
    def delete_checkin(self, checkin_id: int) -> CheckinResult:
        """
        Remove um registro de check-in.
        
        Args:
            checkin_id: ID do check-in a ser removido
            
        Returns:
            CheckinResult com o resultado da operação
        """
        if self._session is not None:
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
        else:
            success = self._db_manager.delete_checkin(checkin_id)
            return CheckinResult(
                success=success,
                checkin_id=checkin_id,
                message="Check-in removido." if success else "Erro ao remover check-in."
            )
    
    def update_datetime(
        self, 
        checkin_id: int, 
        new_datetime: datetime
    ) -> CheckinResult:
        """
        Atualiza a data/hora de um check-in existente.
        
        Args:
            checkin_id: ID do check-in a ser atualizado
            new_datetime: Nova data/hora para o check-in
            
        Returns:
            CheckinResult com o resultado da operação
        """
        if self._session is not None:
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
        else:
            success = self._db_manager.update_checkin_datetime(checkin_id, new_datetime)
            return CheckinResult(
                success=success,
                checkin_id=checkin_id,
                message="Check-in atualizado." if success else "Erro ao atualizar check-in."
            )
    
    def get_member_history(self, member_id: int) -> list:
        """
        Busca o histórico de check-ins de um membro.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Lista de check-ins ordenados do mais recente ao mais antigo
        """
        if self._session is not None:
            checkins = self._session.query(Frequencia).filter(
                Frequencia.member_id == member_id
            ).order_by(Frequencia.checkin_datetime.desc()).all()
            
            return [c.to_dict() for c in checkins]
        else:
            return self._db_manager.get_member_checkin_history(member_id)
    
    def count_today(self) -> int:
        """
        Conta o número de check-ins realizados hoje.
        
        Returns:
            Número de check-ins de hoje
        """
        today = date.today()
        
        if self._session is not None:
            return self._session.query(Frequencia).filter(
                func.date(Frequencia.checkin_datetime) == today
            ).count()
        else:
            return self._db_manager.get_checkins_today()
    
    def get_today_details(self) -> list:
        """
        Busca os detalhes de todos os check-ins de hoje.
        
        Returns:
            Lista de dicionários com nome, plano e horário
        """
        today = date.today()
        
        if self._session is not None:
            results = self._session.query(
                Frequencia, Membro.nome, Membro.plano
            ).join(Membro, Frequencia.member_id == Membro.id).filter(
                func.date(Frequencia.checkin_datetime) == today
            ).order_by(Frequencia.checkin_datetime.desc()).all()
            
            return [
                {
                    'id': f.id,
                    'member_id': f.member_id,
                    'nome': nome,
                    'plano': plano,
                    'checkin_datetime': f.checkin_datetime.isoformat() if f.checkin_datetime else None
                }
                for f, nome, plano in results
            ]
        else:
            return self._db_manager.get_checkins_today_details()
    
    def get_by_date(self, date_str: str) -> list:
        """
        Busca check-ins de uma data específica.
        
        Args:
            date_str: Data no formato 'YYYY-MM-DD'
            
        Returns:
            Lista de check-ins dessa data
        """
        if self._session is not None:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return []
            
            results = self._session.query(
                Frequencia, Membro.nome, Membro.plano
            ).join(Membro, Frequencia.member_id == Membro.id).filter(
                func.date(Frequencia.checkin_datetime) == target_date
            ).order_by(Frequencia.checkin_datetime.desc()).all()
            
            return [
                {
                    'id': f.id,
                    'member_id': f.member_id,
                    'nome': nome,
                    'plano': plano,
                    'checkin_datetime': f.checkin_datetime.isoformat() if f.checkin_datetime else None
                }
                for f, nome, plano in results
            ]
        else:
            return self._db_manager.get_checkins_by_date(date_str)
    
    def get_recent(self, limit: int = 5) -> list:
        """
        Busca os últimos check-ins realizados.
        
        Args:
            limit: Número máximo de check-ins a retornar
            
        Returns:
            Lista dos últimos check-ins
        """
        if self._session is not None:
            results = self._session.query(
                Frequencia, Membro.nome, Membro.plano
            ).join(Membro, Frequencia.member_id == Membro.id).order_by(
                Frequencia.checkin_datetime.desc()
            ).limit(limit).all()
            
            return [
                {
                    'id': f.id,
                    'member_id': f.member_id,
                    'nome': nome,
                    'plano': plano,
                    'checkin_datetime': f.checkin_datetime.isoformat() if f.checkin_datetime else None
                }
                for f, nome, plano in results
            ]
        else:
            return self._db_manager.get_last_checkins(limit)
    
    def get_today_list(self) -> list:
        """
        Busca todos os check-ins de hoje (alias para get_today_details).
        
        Returns:
            Lista de check-ins de hoje
        """
        return self.get_today_details()

