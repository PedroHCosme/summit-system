"""
Constantes relacionadas a pagamentos e transações financeiras.

Centraliza as magic strings usadas no banco de dados para garantir consistência.
"""

# =============================================================================
# MÉTODOS DE PAGAMENTO
# =============================================================================

METODO_CHECKIN = "Check-in"
METODO_PIX = "PIX"
METODO_CARTAO_CREDITO = "Cartão de Crédito"
METODO_CARTAO_DEBITO = "Cartão de Débito"
METODO_DINHEIRO = "Dinheiro"
METODO_TRANSFERENCIA = "Transferência"
METODO_SINCRONIZACAO = "Sincronização (Sheets)"

# Lista canônica para dropdowns de UI (sem blank — adicionar "" como primeiro item se o campo for opcional)
METODOS_PAGAMENTO_UI = [
    METODO_PIX,
    METODO_CARTAO_CREDITO,
    METODO_CARTAO_DEBITO,
    METODO_DINHEIRO,
    METODO_TRANSFERENCIA,
]

# =============================================================================
# TIPOS DE TRANSAÇÃO
# =============================================================================

TIPO_RENOVACAO_PLANO = "Renovação Plano"
TIPO_COMPRA_VOUCHER = "Compra Voucher"
TIPO_PAGAMENTO_TREINO = "Pagamento Treino"
TIPO_VENDA_PRODUTO = "Venda de Produto"
TIPO_PAGAMENTO_MANUAL = "Pagamento Manual"

# Legado — string incompleta usada antes da padronização; preferir TIPO_RENOVACAO_PLANO
TIPO_RENOVACAO = "Renovação"
