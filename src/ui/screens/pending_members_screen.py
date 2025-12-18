"""Tela de aprovação de novos membros."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMessageBox, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.data.database_manager import DatabaseManager

class PendingMembersScreen(QWidget):
    """Tela para aprovar ou rejeitar membros pendentes."""
    
    # Sinais
    member_approved = pyqtSignal()
    member_rejected = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.db_manager.connect()
        self.current_member_data = None
        self._setup_ui()
        self.refresh_list()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Aprovação de Novos Membros")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Container principal
        content_layout = QHBoxLayout()
        
        # Lista de membros pendentes
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Membros Pendentes:"))
        
        self.members_list = QListWidget()
        self.members_list.itemClicked.connect(self._on_item_clicked)
        left_layout.addWidget(self.members_list)
        
        content_layout.addLayout(left_layout, 1)
        
        # Detalhes do membro
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Detalhes:"))
        
        self.details_browser = QTextBrowser()
        self.details_browser.setHtml("<div style='text-align: center; color: #666; margin-top: 20px;'>Selecione um membro para ver os detalhes</div>")
        right_layout.addWidget(self.details_browser)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.approve_button = QPushButton("✅ Aprovar")
        self.approve_button.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 10px;")
        self.approve_button.clicked.connect(self._on_approve_clicked)
        self.approve_button.setEnabled(False)
        buttons_layout.addWidget(self.approve_button)
        
        self.reject_button = QPushButton("❌ Rejeitar")
        self.reject_button.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 10px;")
        self.reject_button.clicked.connect(self._on_reject_clicked)
        self.reject_button.setEnabled(False)
        buttons_layout.addWidget(self.reject_button)
        
        right_layout.addLayout(buttons_layout)
        
        content_layout.addLayout(right_layout, 2)
        
        layout.addLayout(content_layout)
        
        # Botão de atualizar
        refresh_button = QPushButton("Atualizar Lista")
        refresh_button.clicked.connect(self.refresh_list)
        layout.addWidget(refresh_button)

    def refresh_list(self):
        """Recarrega a lista de membros pendentes."""
        self.members_list.clear()
        self.current_member_data = None
        self.details_browser.setHtml("<div style='text-align: center; color: #666; margin-top: 20px;'>Selecione um membro para ver os detalhes</div>")
        self.approve_button.setEnabled(False)
        self.reject_button.setEnabled(False)
        
        # Busca membros com status PENDENTE
        # Usamos page_size grande para pegar todos, ou poderíamos implementar paginação se fossem muitos
        result = self.db_manager.get_members_paginated(page=1, page_size=100, filter_status="PENDENTE")
        members = result.get('members', [])
        
        if not members:
            self.members_list.addItem("Nenhum membro pendente.")
            self.members_list.item(0).setFlags(Qt.ItemFlag.NoItemFlags) # Desabilita seleção
            return

        for member in members:
            display_text = f"{member['nome']}"
            if member.get('apelido'):
                display_text += f" ({member['apelido']})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, member)
            self.members_list.addItem(item)

    def _on_item_clicked(self, item):
        """Exibe detalhes do membro selecionado."""
        member_data = item.data(Qt.ItemDataRole.UserRole)
        if not member_data:
            return
            
        self.current_member_data = member_data
        self.approve_button.setEnabled(True)
        self.reject_button.setEnabled(True)
        
        # Formata detalhes em HTML
        html = f"""
            <h3>{member_data['nome']}</h3>
            <p><strong>Apelido:</strong> {member_data.get('apelido', '-')}</p>
            <p><strong>Plano:</strong> {member_data.get('plano', '-')}</p>
            <p><strong>Data Nascimento:</strong> {member_data.get('data_nascimento', '-')}</p>
            <p><strong>WhatsApp:</strong> {member_data.get('whatsapp', '-')}</p>
            <p><strong>Email:</strong> {member_data.get('email', '-')}</p>
            <p><strong>Gênero:</strong> {member_data.get('genero', '-')}</p>
            <p><strong>Calçado:</strong> {member_data.get('calcado', '-')}</p>
            <p><strong>Treina:</strong> {member_data.get('treina', '-')}</p>
            <hr>
            <p><strong>Status Atual:</strong> <span style='color: orange;'>{member_data.get('estado_plano', 'PENDENTE')}</span></p>
        """
        self.details_browser.setHtml(html)

    def _on_approve_clicked(self):
        """Aprova o membro selecionado."""
        if not self.current_member_data:
            return
            
        confirm = QMessageBox.question(
            self, "Confirmar Aprovação",
            f"Deseja aprovar o membro {self.current_member_data['nome']}?\n\nO status será alterado para ATIVO.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.db_manager.update_member(
                self.current_member_data['id'],
                estado_plano='ATIVO'
            )
            
            if success:
                QMessageBox.information(self, "Sucesso", "Membro aprovado com sucesso!")
                self.refresh_list()
                self.member_approved.emit()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao aprovar membro.")

    def _on_reject_clicked(self):
        """Rejeita (deleta) o membro selecionado."""
        if not self.current_member_data:
            return
            
        confirm = QMessageBox.question(
            self, "Confirmar Rejeição",
            f"Deseja REJEITAR e REMOVER o membro {self.current_member_data['nome']}?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.db_manager.delete_member(self.current_member_data['id'])
            
            if success:
                QMessageBox.information(self, "Sucesso", "Membro rejeitado e removido.")
                self.refresh_list()
                self.member_rejected.emit()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao rejeitar membro.")
