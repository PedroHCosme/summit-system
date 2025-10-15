"""Diálogo para adicionar novo membro."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QPushButton
)
from PyQt6.QtCore import QDate

from src.config import PLANOS, PLANOS_COM_VENCIMENTO


class AddMemberDialog(QDialog):
    """Janela de diálogo para adicionar um novo membro."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Novo Membro")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._connect_signals()
        self._toggle_vencimento_visibility(self.plano_combo.currentText())

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        self.layout = QVBoxLayout(self)
        
        # Formulário
        self.form_layout = QFormLayout()
        
        # Campos
        self.nome_input = QLineEdit()
        
        self.plano_combo = QComboBox()
        self.plano_combo.addItems(PLANOS)
        
        self.vencimento_plano_input = QDateEdit()
        self.vencimento_plano_input.setCalendarPopup(True)
        self.vencimento_plano_input.setDate(QDate.currentDate())
        self.vencimento_plano_input.setDisplayFormat("dd/MM/yyyy")
        
        self.data_nascimento_input = QDateEdit()
        self.data_nascimento_input.setCalendarPopup(True)
        self.data_nascimento_input.setDate(QDate.currentDate())
        self.data_nascimento_input.setDisplayFormat("dd/MM/yyyy")

        self.whatsapp_input = QLineEdit()
        self.whatsapp_input.setPlaceholderText("(XX) XXXXX-XXXX")
        
        self.genero_combo = QComboBox()
        self.genero_combo.addItems(["", "M", "F"])
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemplo@email.com")

        # Adiciona campos ao formulário
        self.form_layout.addRow("Nome (*):", self.nome_input)
        self.form_layout.addRow("Plano (*):", self.plano_combo)
        self.vencimento_row = self.form_layout.addRow("Vencimento do Plano:", self.vencimento_plano_input)
        self.form_layout.addRow("Data de Nascimento (*):", self.data_nascimento_input)
        self.form_layout.addRow("WhatsApp (*):", self.whatsapp_input)
        self.form_layout.addRow("Gênero (*):", self.genero_combo)
        self.form_layout.addRow("Email:", self.email_input)
        
        self.layout.addLayout(self.form_layout)

        # Botões
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar")
        self.cancel_button = QPushButton("Cancelar")
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.save_button)
        
        self.layout.addLayout(self.button_layout)

    def _connect_signals(self):
        """Conecta os sinais dos widgets."""
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.plano_combo.currentTextChanged.connect(self._toggle_vencimento_visibility)

    def _toggle_vencimento_visibility(self, plano: str):
        """Mostra ou esconde o campo de vencimento baseado no plano e calcula a data automaticamente."""
        is_visible = plano in PLANOS_COM_VENCIMENTO
        self.form_layout.labelForField(self.vencimento_plano_input).setVisible(is_visible)
        self.vencimento_plano_input.setVisible(is_visible)
        
        # Calcula automaticamente a data de vencimento
        if is_visible:
            from src.utils.utils import calculate_new_due_date
            
            new_due_date = calculate_new_due_date(plano)
            if new_due_date and isinstance(new_due_date, datetime):
                # Já é um objeto datetime, converter diretamente para QDate
                qdate = QDate(new_due_date.year, new_due_date.month, new_due_date.day)
                self.vencimento_plano_input.setDate(qdate)

    def get_data(self):
        """Retorna os dados do formulário como um dicionário."""
        plano = self.plano_combo.currentText()
        
        data = {
            "nome": self.nome_input.text().strip(),
            "plano": plano,
            "data_nascimento": self.data_nascimento_input.date().toString("dd/MM/yyyy"),
            "whatsapp": self.whatsapp_input.text().strip(),
            "genero": self.genero_combo.currentText(),
            "email": self.email_input.text().strip(),
        }
        
        # Para planos com vencimento, sempre incluir a data
        if plano in PLANOS_COM_VENCIMENTO:
            data["vencimento_plano"] = self.vencimento_plano_input.date().toString("dd/MM/yyyy")
        
        return data
