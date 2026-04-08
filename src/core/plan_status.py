"""
Constantes e funções canônicas para status de plano e status de membro.

DOIS CONCEITOS SEPARADOS:
  1. Status do Plano  — baseado em data de vencimento (EM_DIA, VENCIDO, SEM_VENCIMENTO)
  2. Status do Membro — baseado em frequência de check-ins (ATIVO, INATIVO)

O banco de dados persiste `estado_plano` com valores: ATIVO, INATIVO, PENDENTE.
O status do plano (EM_DIA/VENCIDO) e o status do membro (ATIVO por frequência)
são COMPUTADOS em tempo de execução — nunca persistidos separadamente.

Regras de negócio (definidas pelo dono da academia):
  - Plano VENCIDO NÃO bloqueia check-in, mas emite aviso na tela.
  - Não existe mais "Período de Graça" como conceito persistido.
  - Membro ATIVO ≠ Plano EM DIA. Um membro pode ter plano em dia mas
    não estar frequentando (e portanto ser INATIVO por frequência).
"""

from datetime import date
from typing import Optional


# =============================================================================
# CONSTANTES PERSISTIDAS NO BANCO (campo estado_plano)
# =============================================================================

ATIVO = "ATIVO"
INATIVO = "INATIVO"
PENDENTE = "PENDENTE"   # Cadastro web aguardando aprovação do dono

# Conjunto de estados válidos para validação
VALID_STATES = frozenset({ATIVO, INATIVO, PENDENTE})


# =============================================================================
# CONSTANTES DE STATUS DO PLANO (computadas, não persistidas)
# =============================================================================

STATUS_PLANO_EM_DIA = "EM DIA"
STATUS_PLANO_VENCIDO = "VENCIDO"
STATUS_PLANO_SEM_VENCIMENTO = "SEM VENCIMENTO"   # quota, per-checkin, cortesia


# =============================================================================
# CONSTANTES DE STATUS DO MEMBRO POR FREQUÊNCIA (computadas, não persistidas)
# =============================================================================

STATUS_MEMBRO_ATIVO = "ATIVO"
STATUS_MEMBRO_INATIVO = "INATIVO"

# Thresholds em dias sem check-in para considerar membro inativo
LIMIAR_INATIVO_PADRAO = 14     # Mensal, Trimestral, Semestral, Anual, Escolinha, Mens. c/ Treino
LIMIAR_INATIVO_AVULSO = 45    # Gympass, Totalpass, Diária, Cortesia
LIMIAR_INATIVO_QUOTA = 30     # Planos quota (Pacote 10 etc)

# Planos que usam o limiar longo (45 dias) — frequência irregular é normal
PLANOS_LIMIAR_AVULSO = frozenset({
    "Gympass", "Totalpass", "Diária", "Cortesia"
})


# =============================================================================
# LABELS DE EXIBIÇÃO
# =============================================================================

DISPLAY_LABEL_ATIVO = "Ativo"
DISPLAY_LABEL_PLANO_VENCIDO = "Plano vencido"


# =============================================================================
# FUNÇÕES DE STATUS DO PLANO
# =============================================================================

def calcular_status_plano(
    vencimento_plano,
    estado_plano_db: Optional[str] = None,
    is_quota: bool = False,
    valor_por_checkin: float = 0.0,
) -> str:
    """
    Calcula o status do plano baseado na data de vencimento.

    Args:
        vencimento_plano: Data de vencimento (date, datetime, string, ou None)
        estado_plano_db: Valor atual no banco (para detectar PENDENTE)
        is_quota: Se é plano baseado em créditos
        valor_por_checkin: Preço por check-in (> 0 para Diária/Gympass/Totalpass)

    Returns:
        STATUS_PLANO_EM_DIA | STATUS_PLANO_VENCIDO | STATUS_PLANO_SEM_VENCIMENTO
    """
    # Membros pendentes têm status próprio — não classificar como plano
    if estado_plano_db == PENDENTE:
        return PENDENTE

    # Planos sem vencimento: quota, per-checkin (valor_por_checkin > 0) ou sem data
    if is_quota or (valor_por_checkin and valor_por_checkin > 0) or vencimento_plano is None:
        return STATUS_PLANO_SEM_VENCIMENTO

    # Normalizar vencimento para date
    venc = _coerce_to_date(vencimento_plano)
    if venc is None:
        return STATUS_PLANO_SEM_VENCIMENTO

    hoje = date.today()
    return STATUS_PLANO_EM_DIA if venc >= hoje else STATUS_PLANO_VENCIDO


def calcular_status_membro(
    plano_nome: Optional[str],
    ultimo_checkin,
    voucher_credits: int = 0,
    is_quota: bool = False,
    valor_por_checkin: float = 0.0,
) -> str:
    """
    Calcula o status de atividade do membro baseado em frequência.

    Regras (definidas pelo dono da academia):
      - Mensal, Trimestral, Semestral, Anual, Mens. c/ Treino, Escolinha:
            ATIVO se último check-in <= 14 dias atrás
      - Gympass, Totalpass, Diária, Cortesia:
            ATIVO se último check-in <= 45 dias atrás
      - Planos quota (Pacote 10 etc):
            ATIVO se créditos > 0 E último check-in <= 30 dias atrás
      - Sem check-in algum: sempre INATIVO

    Ao fazer check-in, o membro volta a ATIVO automaticamente.

    Args:
        plano_nome: Nome do plano do membro
        ultimo_checkin: Datetime/date do último check-in, ou None
        voucher_credits: Saldo de créditos (para planos quota)
        is_quota: Se é plano baseado em créditos
        valor_por_checkin: Preço por check-in (para classificar avulsos)

    Returns:
        STATUS_MEMBRO_ATIVO | STATUS_MEMBRO_INATIVO
    """
    if ultimo_checkin is None:
        return STATUS_MEMBRO_INATIVO

    uc = _coerce_to_date(ultimo_checkin)
    if uc is None:
        return STATUS_MEMBRO_INATIVO

    dias_sem_checkin = (date.today() - uc).days

    # Plano quota: exige créditos E frequência
    if is_quota:
        if voucher_credits <= 0:
            return STATUS_MEMBRO_INATIVO
        return STATUS_MEMBRO_ATIVO if dias_sem_checkin <= LIMIAR_INATIVO_QUOTA else STATUS_MEMBRO_INATIVO

    # Planos per-checkin e avulsos: limiar longo
    if (valor_por_checkin and valor_por_checkin > 0) or plano_nome in PLANOS_LIMIAR_AVULSO:
        return STATUS_MEMBRO_ATIVO if dias_sem_checkin <= LIMIAR_INATIVO_AVULSO else STATUS_MEMBRO_INATIVO

    # Planos com vencimento (mensal, trimestral, etc): limiar curto
    return STATUS_MEMBRO_ATIVO if dias_sem_checkin <= LIMIAR_INATIVO_PADRAO else STATUS_MEMBRO_INATIVO


# =============================================================================
# FUNÇÕES LEGADAS (mantidas para compatibilidade)
# =============================================================================

def is_active(estado: str) -> bool:
    """Retorna True se o estado persistido representa um plano ativo.

    Args:
        estado: Valor de estado_plano do banco (pode ser None/vazio)
    """
    if not estado:
        return False
    return estado.strip().upper() == ATIVO


def display_label(estado: str) -> str:
    """Retorna label amigável para exibição na UI."""
    if is_active(estado):
        return DISPLAY_LABEL_ATIVO
    return DISPLAY_LABEL_PLANO_VENCIDO


# =============================================================================
# HELPERS INTERNOS
# =============================================================================

def _coerce_to_date(value) -> Optional[date]:
    """Converte date, datetime ou string ISO para date. Retorna None se inválido."""
    if value is None:
        return None
    if isinstance(value, date):
        # datetime é subclasse de date — .date() existe para datetime
        return value.date() if hasattr(value, 'hour') else value
    if isinstance(value, str):
        try:
            from src.utils.date_utils import parse_date_to_date
            return parse_date_to_date(value)
        except Exception:
            return None
    return None
