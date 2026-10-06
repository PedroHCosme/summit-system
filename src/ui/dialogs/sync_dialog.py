"""Diálogo de sincronização com Google Sheets."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from src.ui.workers import SyncWorker


class SyncDialog(QDialog):
    """Diálogo para executar e monitorar sincronização."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.sync_result = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface do diálogo."""
        self.setWindowTitle("Sincronização com Google Sheets")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("🔄 Sincronização de Dados")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Descrição
        description = QLabel(
            "Esta operação sincronizará os dados do Google Sheets com o banco local.\n"
            "Novos membros e check-ins serão adicionados. Dados existentes serão preservados."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(description)
        
        # Status label
        self.status_label = QLabel("Pronto para iniciar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #2196F3; padding: 5px;"
        )
        layout.addWidget(self.status_label)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Log de atividades
        log_label = QLabel("📋 Log de Atividades:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Botões
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.start_button = QPushButton("▶ Iniciar Sincronização")
        self.start_button.clicked.connect(self._start_sync)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        self.close_button = QPushButton("Fechar")
        self.close_button.clicked.connect(self.reject)
        self.close_button.setEnabled(False)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def _start_sync(self):
        """Inicia o processo de sincronização."""
        # Confirmar com o usuário
        reply = QMessageBox.question(
            self,
            "Confirmar Sincronização",
            "Deseja realmente sincronizar os dados?\n\n"
            "Esta operação pode levar alguns minutos dependendo\n"
            "da quantidade de dados no Google Sheets.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Desabilita o botão de iniciar
        self.start_button.setEnabled(False)
        self.close_button.setEnabled(False)
        
        # Limpa o log
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # Adiciona log inicial
        self._add_log("🚀 Iniciando sincronização...")
        
        # Cria e inicia o worker
        self.worker = SyncWorker()
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.sync_completed.connect(self._on_sync_completed)
        self.worker.sync_failed.connect(self._on_sync_failed)
        self.worker.start()
    
    @pyqtSlot(str, int)
    def _on_progress_updated(self, message: str, progress: int):
        """Atualiza o progresso da sincronização."""
        self.status_label.setText(message)
        self.progress_bar.setValue(progress)
        self._add_log(message)
    
    @pyqtSlot(dict)
    def _on_sync_completed(self, result: dict):
        """Callback quando a sincronização é concluída."""
        self.sync_result = result
        
        # Atualiza UI
        self.status_label.setText("✅ Sincronização concluída com sucesso!")
        self.status_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #4CAF50; padding: 5px;"
        )
        self.progress_bar.setValue(100)
        
        # Log final detalhado
        self._add_log("\n" + "="*50)
        self._add_log("📊 RESUMO DA SINCRONIZAÇÃO")
        self._add_log("="*50)
        self._add_log(f"👥 Membros:")
        self._add_log(f"   • Novos: {result['membros_novos']}")
        self._add_log(f"   • Existentes: {result['membros_existentes']}")
        self._add_log(f"   • Total processado: {result['membros_total']}")
        self._add_log(f"\n📋 Check-ins:")
        self._add_log(f"   • Novos: {result['checkins_novos']}")
        self._add_log(f"   • Duplicados ignorados: {result['checkins_duplicados']}")
        self._add_log(f"\n🕐 Horário: {result['timestamp']}")
        self._add_log("="*50)
        
        # Habilita botão de fechar
        self.close_button.setEnabled(True)
        
        # Mostra mensagem de sucesso
        QMessageBox.information(
            self,
            "Sincronização Concluída",
            f"✅ Sincronização realizada com sucesso!\n\n"
            f"📊 Resumo:\n"
            f"• {result['membros_novos']} novos membros adicionados\n"
            f"• {result['membros_existentes']} membros já existentes\n"
            f"• {result['checkins_novos']} novos check-ins registrados\n"
            f"• {result['checkins_duplicados']} check-ins duplicados ignorados"
        )
    
    @pyqtSlot(str)
    def _on_sync_failed(self, error_message: str):
        """Callback quando a sincronização falha."""
        self.status_label.setText("❌ Sincronização falhou")
        self.status_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #f44336; padding: 5px;"
        )
        
        self._add_log(f"\n{error_message}")
        
        # Habilita botões
        self.start_button.setEnabled(True)
        self.close_button.setEnabled(True)
        
        # Mostra erro
        QMessageBox.critical(
            self,
            "Erro na Sincronização",
            f"{error_message}\n\n"
            f"Verifique:\n"
            f"• Conexão com a internet\n"
            f"• Credenciais do Google Sheets\n"
            f"• Permissões do banco de dados"
        )
    
    def _add_log(self, message: str):
        """Adiciona mensagem ao log."""
        self.log_text.append(message)
        # Scroll para o final
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def get_result(self):
        """Retorna o resultado da sincronização."""
        return self.sync_result
