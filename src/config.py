"""
Configurações do aplicativo.
"""

# ID da planilha do Google Sheets
SPREADSHEET_ID = '1xjIv3wMnnPKVXVWc8EwhaTqkSG-jJoFQUodOJe-GZjQ'

# Caminho para o arquivo de credenciais
CREDENTIALS_PATH = 'credentials.json'

# Índices das colunas na planilha (zero-based)
COL_NOME = 0  # Coluna A
COL_PLANO = 1  # Coluna B
COL_VENCIMENTO_PLANO = 2  # Coluna C (Data de vencimento do plano)
COL_ESTADO_PLANO = 3  # Coluna D (Ativo/Inativo)
COL_GENERO = 66  # Coluna BO
COL_DATA_NASCIMENTO = 67  # Coluna BP (68ª coluna)
COL_FREQUENCIA = 69  # Coluna BR
COL_WHATSAPP = 70  # Coluna BS (71ª coluna)
COL_CALCADO = 71  # Coluna BT (72ª coluna)

# Planos que possuem data de vencimento
PLANOS_COM_VENCIMENTO = [
    'Mensal',
    'Mens. c/ Treino',
    'Trimestral',
    'Semestral',
    'Anual'
]
