"""
Camada de serviços da aplicação.

Este pacote contém os serviços que encapsulam a lógica de negócio,
separando-a da camada de dados e da camada de apresentação.

Serviços disponíveis:
- CheckinService: Operações de check-in de membros
- MemberService: Gestão de membros (CRUD, busca, etc.)
- PaymentService: Gestão financeira e pagamentos
"""

from src.services.checkin_service import CheckinService, CheckinResult
from src.services.member_service import MemberService, MemberResult, PaginatedResult
from src.services.payment_service import PaymentService, PaymentResult, FinancialSummary, RevenueBreakdown

__all__ = [
    # Check-in
    'CheckinService',
    'CheckinResult',
    # Member
    'MemberService',
    'MemberResult',
    'PaginatedResult',
    # Payment
    'PaymentService',
    'PaymentResult',
    'FinancialSummary',
    'RevenueBreakdown',
]
