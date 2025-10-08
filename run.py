#!/usr/bin/env python3
"""
Script de entrada para executar a GUI.
"""
import sys
import os

# Adiciona o diretório src ao Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_dir)

# Muda para o diretório src (para que credentials.json seja encontrado)
os.chdir(src_dir)

# Importa e executa
from gui import main

if __name__ == "__main__":
    main()
