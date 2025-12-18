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
    "Mens. c/ Treino",
    "Semestral",
    "Anual",
    "Trimestral",
    "Diária",
    "Gympass",
    "Totalpass",
    "Cortesia",
    "Escolinha 1x",
    "Escolinha 2x"
]

# Planos que exigem uma data de vencimento
PLANOS_COM_VENCIMENTO = [
    "Mensal",
    "Mens. c/ Treino",
    "Trimestral",
    "Semestral",
    "Anual",
    "Escolinha 1x",
    "Escolinha 2x"
]

# Preços dos planos (em R$)
# Nota: Diária, Gympass e Totalpass têm valor 0 para renovação
# pois cobram apenas por check-in (ver PLANOS_PAGAMENTO_POR_CHECKIN)
PLANOS_PRECOS = {
    "Mensal": 190.0,
    "Mens. c/ Treino": 280.0,
    "Trimestral": 500.0,
    "Semestral": 950.0,
    "Anual": 1900.0,
    "Diária": 0.0,       # CORRIGIDO: Diária cobra apenas no check-in, não na renovação
    "Gympass": 0.0,      # Gympass: renovação não gera receita (pago por check-in)
    "Totalpass": 0.0,    # CORRIGIDO: era 00.0 (typo), agora 0.0
    "Cortesia": 0.0,     # Cortesia não tem custo
    "Escolinha 1x": 0.0,
    "Escolinha 2x": 0.0
}

# Planos que geram pagamento por check-in
PLANOS_PAGAMENTO_POR_CHECKIN = {
    "Diária": 35.0,      # Cada check-in = R$ 35,00
    "Gympass": 15.0,     # Cada check-in = R$ 15,00
    "Totalpass": 15.0    # Cada check-in = R$ 15,00
}

# --- CONFIGURAÇÕES DE TREINO ---
# Treino é um serviço adicional independente do plano
TREINO_PRECO = 90.0  # R$ 90,00 por mês
TREINO_VALIDADE_DIAS = 30  # 1 mês de validade


# --- CARREGAR CONFIGURAÇÕES PERSONALIZADAS ---
# Carrega configurações salvas pelo diálogo de gerenciar planos, se existirem
def _load_custom_plans_config():
    """Carrega configurações de planos do arquivo plans_config.json se existir."""
    import json
    from pathlib import Path
    
    # Caminho do arquivo de configuração
    project_root = Path(__file__).parent.parent
    config_file = project_root / "plans_config.json"
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Atualizar variáveis globais com dados salvos
            global PLANOS, PLANOS_PRECOS, PLANOS_PAGAMENTO_POR_CHECKIN, PLANOS_COM_VENCIMENTO
            
            PLANOS = config_data.get("PLANOS", PLANOS)
            PLANOS_PRECOS = config_data.get("PLANOS_PRECOS", PLANOS_PRECOS)
            PLANOS_PAGAMENTO_POR_CHECKIN = config_data.get("PLANOS_PAGAMENTO_POR_CHECKIN", PLANOS_PAGAMENTO_POR_CHECKIN)
            PLANOS_COM_VENCIMENTO = config_data.get("PLANOS_COM_VENCIMENTO", PLANOS_COM_VENCIMENTO)
            
            print(f"✓ Configurações personalizadas de planos carregadas de {config_file.name}")
        except Exception as e:
            print(f"⚠ Aviso: Erro ao carregar plans_config.json: {e}")
            print("  Usando configurações padrão.")

# Carregar configurações personalizadas ao importar o módulo
_load_custom_plans_config()
