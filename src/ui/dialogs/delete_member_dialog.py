"""Diálogo de confirmação para deletar um membro."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt


class DeleteMemberDialog(QDialog):
    """Diálogo de confirmação para deletar um membro."""
    
    def __init__(self, member_data: dict, parent=None):
        super().__init__(parent)
        self.member_data = member_data
        self.setWindowTitle("Confirmar Exclusão")
        self.setModal(True)
        self.setFixedSize(450, 200)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Ícone e título
        title_layout = QHBoxLayout()
        
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 40px;")
        title_layout.addWidget(icon_label)
        
        title_label = QLabel("Confirmar Exclusão")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #D32F2F;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Mensagem de confirmação
        member_name = self.member_data.get('nome', 'este membro')
        message_label = QLabel(
            f"Tem certeza que deseja excluir o membro:\n\n"
            f"<b>{member_name}</b>\n\n"
            f"Esta ação não pode ser desfeita!"
        )
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            font-size: 14px;
            color: #333333;
            padding: 10px;
        """)
        layout.addWidget(message_label)
        
        layout.addStretch()
        
        # Botões
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Botão Cancelar
        cancel_button = QPushButton("Cancelar")
        cancel_button.setFixedSize(120, 35)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Botão Deletar
        delete_button = QPushButton("Deletar")
        delete_button.setFixedSize(120, 35)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #B71C1C;
            }
        """)
        delete_button.clicked.connect(self.accept)
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
