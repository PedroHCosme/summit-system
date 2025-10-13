"""
Configurações do aplicativo.
"""

import os

# --- CONFIGURAÇÕES GLOBAIS ---

# ID da planilha do Google Sheets
SPREADSHEET_ID = '1xjIv3wMnnPKVXVWc8EwhaTqkSG-jJoFQUodOJe-GZjQ'

# Caminho para o arquivo de credenciais (relativo à raiz do projeto)
CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials.json')

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

# Usado para determinar se a conexão será com SQLite ou Google Sheets
USE_SQLITE = True

# Lista de todos os planos disponíveis
PLANOS = [
    "Mensal",
    "Mens c/. Treino",
    "Semestral",
    "Anual",
    "Escolhinha",
    "FitDance",
    "Funcional",
    "Luta",
    "Pilates",
    "Yoga"
]

# Planos que exigem uma data de vencimento
PLANOS_COM_VENCIMENTO = [
    "Mensal",
    "Mens. c/ Treino",
    "Trimestral",
    "Semestral",
    "Anual"
]
