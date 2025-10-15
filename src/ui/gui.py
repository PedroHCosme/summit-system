"""
Interface gráfica para o sistema de aniversariantes.
Módulo de compatibilidade - redireciona para a nova estrutura modular.
"""

# Importa a janela principal da nova estrutura
from src.ui.main_window import MainWindow as AniversariantesApp
from src.ui.main_window import main

# Para compatibilidade com imports antigos
__all__ = ['AniversariantesApp', 'main']
