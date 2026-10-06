#!/bin/bash

# Ativa o ambiente virtual se existir (opcional, mas recomendado)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Define o PYTHONPATH para incluir a raiz do projeto
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Lê configuração do config_local.py
# Lê configuração do config_local.py, com fallback para Produção
DEVELOPMENT_MODE=$(python3 -c "from config_local import DEVELOPMENT_MODE; print(DEVELOPMENT_MODE)" 2>/dev/null || echo "False")
WEB_PORT=$(python3 -c "from config_local import WEB_PORT; print(WEB_PORT)" 2>/dev/null || echo "5000")

if [ "$DEVELOPMENT_MODE" = "True" ]; then
    BIND_HOST="127.0.0.1"
else
    BIND_HOST="0.0.0.0"
fi

echo "🚀 Iniciando Summit Mobile Pass..."
echo "📱 Acesso: http://${BIND_HOST}:${WEB_PORT}"
echo "Press Ctrl+C to stop."

# Roda com Gunicorn
gunicorn --reload --workers 3 --bind ${BIND_HOST}:${WEB_PORT} src.web.app:app

