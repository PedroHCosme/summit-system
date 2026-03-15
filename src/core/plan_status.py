"""
Constantes canônicas para o estado do plano de membros.

Este módulo é a ÚNICA fonte de verdade para os valores de `estado_plano`.

ATIVO  — Plano vigente (vencimento_plano >= hoje ou plano sem vencimento)
INATIVO — Plano expirado (vencimento_plano < hoje) ou desativado manualmente

O conceito de "vencido" é derivado da comparação de datas e deve ser
tratado apenas como label de exibição na UI, nunca como estado persistido.
"""

# --- Valores canônicos persistidos no banco de dados ---
ATIVO = "ATIVO"
INATIVO = "INATIVO"

# Conjunto imutável de todos os estados válidos (para validação/constraints)
VALID_STATES = frozenset({ATIVO, INATIVO})

# --- Labels de exibição para a interface ---
DISPLAY_LABEL_ATIVO = "Ativo"
DISPLAY_LABEL_PLANO_VENCIDO = "Plano vencido"


def is_active(estado: str) -> bool:
    """Retorna True se o estado representa um plano ativo.

    Trata case-insensitive e espaços extras.

    Args:
        estado: Valor de estado_plano (pode ser None/vazio)

    Returns:
        True se o plano está ativo, False caso contrário
    """
    if not estado:
        return False
    return estado.strip().upper() == ATIVO


def display_label(estado: str) -> str:
    """Retorna o label de exibição amigável para o estado do plano.

    O banco armazena 'ATIVO'/'INATIVO', mas na interface o usuário vê
    termos mais claros como 'Plano vencido'.

    Args:
        estado: Valor de estado_plano

    Returns:
        Label amigável para exibição na UI
    """
    if is_active(estado):
        return DISPLAY_LABEL_ATIVO
    return DISPLAY_LABEL_PLANO_VENCIDO
