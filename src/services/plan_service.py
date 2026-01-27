"""
Serviço centralizado para acesso a dados de planos.
Esta é a ÚNICA fonte de verdade para informações de planos no sistema.
"""

from typing import List, Dict, Optional, Any
from src.data.db import create_session
from src.data.models import Plano


class PlanService:
    """
    Serviço que fornece acesso centralizado aos planos do banco de dados.
    Substitui as constantes hardcoded em config.py.
    """
    
    def __init__(self, db_session=None):
        """
        Inicializa o serviço de planos.
        
        Args:
            db_session: Sessão SQLAlchemy opcional. Se não fornecida, cria uma nova.
        """
        self._session = db_session
        self._owns_session = db_session is None
        self._cache = None  # Cache de planos para evitar queries repetidas
    
    @property
    def session(self):
        """Retorna a sessão, criando uma se necessário."""
        if self._session is None:
            self._session = create_session()
            self._owns_session = True
        return self._session
    
    def _get_plans_cached(self) -> List[Plano]:
        """Retorna planos do cache ou carrega do banco."""
        if self._cache is None:
            self._cache = self.session.query(Plano).filter(Plano.ativo == True).all()
        return self._cache
    
    def invalidate_cache(self):
        """Invalida o cache de planos (chamar após modificações)."""
        self._cache = None
    
    # =========================================================================
    # MÉTODOS PRINCIPAIS
    # =========================================================================
    
    def get_all_plans(self) -> List[Plano]:
        """Retorna todos os planos ativos do banco de dados."""
        return self._get_plans_cached()
    
    def get_plan_names(self) -> List[str]:
        """Retorna lista de nomes de planos ativos."""
        return [p.nome for p in self._get_plans_cached()]
    
    def get_plan_by_name(self, name: str) -> Optional[Plano]:
        """Busca um plano pelo nome."""
        for plan in self._get_plans_cached():
            if plan.nome == name:
                return plan
        return None
    
    def get_plans_as_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna planos como dicionário para uso em UI.
        
        Returns:
            Dict[nome] = {preco, is_quota, quota_amount, valor_por_checkin, requer_vencimento}
        """
        return {
            p.nome: {
                'preco': p.preco,
                'is_quota': p.is_quota,
                'quota_amount': p.quota_amount,
                'valor_por_checkin': p.valor_por_checkin,
                'requer_vencimento': p.requer_vencimento
            }
            for p in self._get_plans_cached()
        }
    
    # =========================================================================
    # HELPERS DE TIPO DE PLANO
    # =========================================================================
    
    def is_quota_plan(self, plan_name: str) -> bool:
        """Verifica se o plano é baseado em quota (voucher/pacote)."""
        plan = self.get_plan_by_name(plan_name)
        return plan.is_quota if plan else False
    
    def requires_vencimento(self, plan_name: str) -> bool:
        """Verifica se o plano requer data de vencimento."""
        plan = self.get_plan_by_name(plan_name)
        if plan is None:
            return False
        # Quota plans don't require vencimento
        if plan.is_quota:
            return False
        return plan.requer_vencimento
    
    def get_plans_with_vencimento(self) -> List[str]:
        """Retorna nomes de planos que requerem vencimento."""
        return [p.nome for p in self._get_plans_cached() 
                if p.requer_vencimento and not p.is_quota]
    
    def get_quota_plans(self) -> List[str]:
        """Retorna nomes de planos baseados em quota."""
        return [p.nome for p in self._get_plans_cached() if p.is_quota]
    
    # =========================================================================
    # HELPERS DE PREÇO
    # =========================================================================
    
    def get_plan_price(self, plan_name: str) -> float:
        """Retorna o preço do plano (para renovação/compra)."""
        plan = self.get_plan_by_name(plan_name)
        return plan.preco if plan else 0.0
    
    def get_checkin_price(self, plan_name: str) -> Optional[float]:
        """
        Retorna o valor por check-in do plano.
        
        Returns:
            Valor por check-in, ou None se o plano não cobra por check-in.
        """
        plan = self.get_plan_by_name(plan_name)
        if plan and plan.valor_por_checkin and plan.valor_por_checkin > 0:
            return plan.valor_por_checkin
        return None
    
    def get_checkin_payment_plans(self) -> Dict[str, float]:
        """
        Retorna planos que geram pagamento por check-in.
        
        Returns:
            Dict[nome] = valor_por_checkin
        """
        return {
            p.nome: p.valor_por_checkin
            for p in self._get_plans_cached()
            if p.valor_por_checkin and p.valor_por_checkin > 0
        }
    
    def get_plan_prices(self) -> Dict[str, float]:
        """
        Retorna dicionário com preços de todos os planos.
        
        Returns:
            Dict[nome] = preco
        """
        return {p.nome: p.preco for p in self._get_plans_cached()}


# =========================================================================
# SINGLETON / FACTORY
# =========================================================================

_plan_service_instance: Optional[PlanService] = None


def get_plan_service(db_session=None) -> PlanService:
    """
    Retorna a instância do serviço de planos.
    
    Para uso em contextos com sessão compartilhada, passe a sessão.
    Para uso standalone, omita a sessão e uma será criada.
    """
    global _plan_service_instance
    
    if db_session is not None:
        # Quando uma sessão é passada, cria instância específica
        return PlanService(db_session)
    
    # Singleton para uso sem sessão específica
    if _plan_service_instance is None:
        _plan_service_instance = PlanService()
    
    return _plan_service_instance


def invalidate_plan_cache():
    """Invalida o cache global de planos."""
    global _plan_service_instance
    if _plan_service_instance is not None:
        _plan_service_instance.invalidate_cache()
