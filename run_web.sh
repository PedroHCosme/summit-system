#!/bin/bash

# Ativa o ambiente virtual se existir (opcional, mas recomendado)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Define o PYTHONPATH para incluir a raiz do projeto
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "🚀 Iniciando Summit Mobile Pass..."
echo "📱 Acesso local: http://localhost:5000"
echo "Press Ctrl+C to stop."

# Roda com Gunicorn (Produção)
# Workers = 2 * CPU + 1 (para um PC simples, 3 ou 4 workers está bom)
gunicorn --reload --workers 3 --bind 0.0.0.0:5000 src.web.app:app
