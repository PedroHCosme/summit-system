#!/usr/bin/env python3
"""
Script de entrada para executar a GUI.
"""
import sys
import os

# Adiciona o diretório do projeto ao Python path para que `src` seja um módulo
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Importa e executa a função principal da GUI
from src.ui.gui import main

if __name__ == "__main__":
    main()
