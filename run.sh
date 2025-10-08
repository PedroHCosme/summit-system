#!/bin/bash
# Script para executar a aplicação Summit

# Configura o PYTHONPATH para incluir as bibliotecas locais
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src/lib"

# Executa a aplicação
python src/gui.py
