"""Coordenação de configurações e manutenção na UI."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QDialog, QMessageBox

from src.ui.dialogs import ExpiringPlansDialog, SyncDialog
from src.ui.messages import show_error


class SettingsCoordinator:
    """Orquestra fluxos de configurações para manter MainWindow enxuta."""

    def __init__(self, window):
        self.window = window

    def show_manage_plans(self):
        if not self.window.is_connected:
            return
        self.window.stacked_widget.setCurrentIndex(8)
        self.window.plans_screen.refresh()

    def show_expiring_plans_dialog(self):
        dialog = ExpiringPlansDialog(self.window.manager.data_provider, self.window)
        dialog.exec()

    def show_sync_dialog(self):
        dialog = SyncDialog(self.window)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted and dialog.get_result():
            QMessageBox.information(
                self.window,
                "Atualização Recomendada",
                "Sincronização concluída!\n\n"
                "Recomenda-se atualizar o dashboard para visualizar\n"
                "os novos dados sincronizados.",
            )
            if self.window.is_connected:
                self.window._update_dashboard()

    def create_database_backup(self):
        reply = QMessageBox.question(
            self.window,
            "Criar Backup",
            "Deseja criar um backup do banco de dados?\n\n"
            "O backup será salvo na pasta 'backups/' do projeto.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            project_root = Path(__file__).parent.parent.parent.parent
            from src.config import DB_FILENAME

            db_path = os.path.join(project_root, DB_FILENAME)
            backup_dir = os.path.join(project_root, "backups")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"gym_database_backup_{timestamp}.db")
            shutil.copy2(db_path, backup_path)

            QMessageBox.information(
                self.window,
                "Backup Criado",
                "Backup criado com sucesso!\n\n"
                f"Arquivo: gym_database_backup_{timestamp}.db\n"
                "Localização: backups/",
            )
        except Exception as e:
            show_error(
                self.window,
                "Não foi possível criar o backup. Verifique se há espaço livre no computador e tente novamente.",
                detail=e,
                title="Erro no backup",
            )

    def optimize_database(self):
        reply = QMessageBox.question(
            self.window,
            "Otimizar Banco de Dados",
            "Esta operação irá:\n"
            "• Criar índices para melhorar a performance\n"
            "• Executar VACUUM para compactar o banco\n"
            "• Atualizar estatísticas\n\n"
            "Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from src.config import DB_FILENAME
            from src.data.maintenance import optimize_and_reindex

            project_root = Path(__file__).parent.parent.parent.parent
            db_path = os.path.join(project_root, DB_FILENAME)
            stats = optimize_and_reindex(db_path)

            indices_checked = stats.get("indices_processed", 0)
            vacuum_status = "Sim" if stats.get("vacuum_executed") else "Não"
            analyze_status = "Sim" if stats.get("analyze_executed") else "Não"
            pragma_status = "Sim" if stats.get("pragma_optimize_executed") else "Não"

            QMessageBox.information(
                self.window,
                "Otimização Concluída",
                "Banco de dados otimizado com sucesso!\n\n"
                f"• {indices_checked} índices verificados/recriados\n"
                f"• VACUUM executado: {vacuum_status}\n"
                f"• ANALYZE executado: {analyze_status}\n"
                f"• PRAGMA optimize executado: {pragma_status}\n\n"
                "As buscas devem estar significativamente mais rápidas agora.",
            )
        except Exception as e:
            show_error(
                self.window,
                "Não foi possível otimizar o banco de dados. Tente novamente mais tarde.",
                detail=e,
                title="Erro na otimização",
            )

    def run_database_migration(self):
        reply = QMessageBox.warning(
            self.window,
            "Migração Crítica do Banco",
            "⚠️  ATENÇÃO: Esta operação irá modificar a estrutura do banco!\n\n"
            "Mudanças aplicadas:\n"
            "• Foreign keys com ON DELETE CASCADE\n"
            "• Conversão de datas de TEXT para DATE/DATETIME\n"
            "• Criação de índices para performance\n"
            "• Triggers e constraints de validação\n\n"
            "Um backup automático será criado antes da migração.\n\n"
            "Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            project_root = Path(__file__).parent.parent.parent.parent
            script_path = project_root / "scripts" / "fix_database_critical.py"

            if not script_path.exists():
                raise FileNotFoundError(f"Script de migração não encontrado: {script_path}")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(project_root),
                input="sim\n",
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                QMessageBox.information(
                    self.window,
                    "Migração Concluída",
                    "✅ Migração executada com sucesso!\n\n"
                    "O banco de dados foi atualizado.",
                )
            else:
                show_error(
                    self.window,
                    "A migração foi concluída, mas com alguns avisos. Se notar algo estranho no sistema, avise o suporte técnico.",
                    detail=f"Código de saída: {result.returncode}",
                    title="Migração com avisos",
                )

            if result.stdout:
                print("\n=== OUTPUT DA MIGRAÇÃO ===")
                print(result.stdout)
            if result.stderr:
                print("\n=== ERROS DA MIGRAÇÃO ===")
                print(result.stderr)
        except Exception as e:
            show_error(
                self.window,
                "Não foi possível executar a migração do banco de dados. Avise o suporte técnico.",
                detail=e,
                title="Erro na migração",
            )
