#!/usr/bin/env python3
"""
Script para testar o diálogo de distribuição de check-ins por plano.
"""

import sys
from pathlib import Path

# Adiciona o diretório src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from PyQt6.QtWidgets import QApplication
from src.ui.dialogs.plan_distribution_dialog import PlanDistributionDialog


def main():
    """Testa o diálogo de distribuição de check-ins por plano."""
    print("="*50)
    print("Teste do Diálogo de Check-ins por Plano")
    print("="*50)
    
    app = QApplication(sys.argv)
    
    try:
        dialog = PlanDistributionDialog()
        dialog.exec()
        
        print("\n✓ Diálogo testado com sucesso!")
        
    except Exception as e:
        print(f"\n✗ Erro ao testar diálogo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
