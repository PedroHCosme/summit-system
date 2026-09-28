"""
Utilitários de planos — funções de classificação e normalização.

Este módulo centraliza lógica de planos que seria duplicada
entre services e data layers.
"""

import unicodedata
from typing import Optional


def normalize_plan_for_payment(
    plan_name: Optional[str],
    per_checkin_plans: dict,
) -> Optional[str]:
    """Normaliza o nome do plano para fins de cobrança por check-in.

    Tenta match exato primeiro, depois match por keyword (case-insensitive).

    Args:
        plan_name: Nome do plano do membro (pode conter variações).
        per_checkin_plans: Dicionário {nome_canônico: valor} dos planos
                          que cobram por check-in.

    Returns:
        Nome canônico do plano se for per-checkin, ou None.
    """
    if not plan_name:
        return None

    plan_name = plan_name.strip()
    if not plan_name:
        return None

    # 1. Match exato
    if plan_name in per_checkin_plans:
        return plan_name

    # 2. Match por keyword (case-insensitive)
    lowered = plan_name.lower()
    for canonical_name in per_checkin_plans:
        if canonical_name.lower() in lowered:
            return canonical_name

    return None


# Categorias de Cliente (ver CONTEXT.md)
ASSINANTE = "Assinante"
PACOTE = "Pacote"
AVULSO = "Avulso"
GYM_TOTALPASS = "Gym/Totalpass"
SEM_RECEITA = "Sem Receita"
OUTROS = "Outros"
CATEGORIAS = (ASSINANTE, PACOTE, AVULSO, GYM_TOTALPASS, SEM_RECEITA, OUTROS)

# ponytail: classifica por prefixo do nome; vira coluna em `planos` se o dono passar a criar planos novos com frequencia
_PREFIXOS_POR_CATEGORIA = (
    (("gympass", "totalpass"), GYM_TOTALPASS),
    (("diaria",), AVULSO),
    (("pacote", "voucher"), PACOTE),
    (("cortesia", "livre", "evento", "airbnb"), SEM_RECEITA),
    (("mensal", "mens.", "trimestral", "semestral", "anual", "escolinha"), ASSINANTE),
)


def categoria_do_plano(plan_name: Optional[str]) -> str:
    """Categoria de Cliente de um plano, pelo nome (sem acento e sem caixa)."""
    nome = unicodedata.normalize("NFD", plan_name or "")
    nome = "".join(c for c in nome if unicodedata.category(c) != "Mn").strip().lower()
    for prefixos, categoria in _PREFIXOS_POR_CATEGORIA:
        if nome.startswith(prefixos):
            return categoria
    return OUTROS
