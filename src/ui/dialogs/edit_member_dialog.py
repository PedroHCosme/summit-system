"""Diálogo para editar informações de um membro."""

from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QPushButton,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from src.config import PLANOS, PLANOS_COM_VENCIMENTO
from src.utils.utils import calculate_new_due_date, parse_date


class EditMemberDialog(QDialog):
    """Diálogo para editar um membro existente."""
    
    member_updated = pyqtSignal(dict)  # Sinal emitido quando o membro é atualizado
    
    def __init__(self, member_data: dict, parent=None):
        super().__init__(parent)
        self.member_data = member_data.copy()  # Cópia dos dados originais
        self.member_id = member_data.get('id')
        
        self.setWindowTitle("Editar Membro")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._setup_ui()
        self._populate_fields()
        self._connect_signals()
    
    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Editar Informações do Membro")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007ACC;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Formulário
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Nome (obrigatório)
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome completo do membro")
        form_layout.addRow("Nome *:", self.nome_input)
        
        # Plano (obrigatório)
        self.plano_combo = QComboBox()
        self.plano_combo.addItems(PLANOS)
        form_layout.addRow("Plano *:", self.plano_combo)
        
        # Vencimento do Plano (condicional)
        self.vencimento_plano_label = QLabel("Vencimento do Plano *:")
        self.vencimento_plano_input = QDateEdit()
        self.vencimento_plano_input.setCalendarPopup(True)
        self.vencimento_plano_input.setDisplayFormat("dd/MM/yyyy")
        self.vencimento_plano_input.setDate(QDate.currentDate())
        form_layout.addRow(self.vencimento_plano_label, self.vencimento_plano_input)
        
        # Data de Nascimento
        self.data_nascimento_input = QDateEdit()
        self.data_nascimento_input.setCalendarPopup(True)
        self.data_nascimento_input.setDisplayFormat("dd/MM/yyyy")
        self.data_nascimento_input.setDate(QDate.currentDate())
        self.data_nascimento_input.setSpecialValueText("Não informado")
        form_layout.addRow("Data de Nascimento:", self.data_nascimento_input)
        
        # WhatsApp
        self.whatsapp_input = QLineEdit()
        self.whatsapp_input.setPlaceholderText("(00) 00000-0000")
        form_layout.addRow("WhatsApp:", self.whatsapp_input)
        
        # Gênero
        self.genero_combo = QComboBox()
        self.genero_combo.addItems(["", "Masculino", "Feminino", "Outro"])
        form_layout.addRow("Gênero:", self.genero_combo)
        
        # Calçado
        self.calcado_input = QLineEdit()
        self.calcado_input.setPlaceholderText("Ex: 42")
        form_layout.addRow("Calçado:", self.calcado_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemplo@email.com")
        form_layout.addRow("Email:", self.email_input)
        
        # Método de Pagamento (para registrar transação)
        self.metodo_pagamento_combo = QComboBox()
        self.metodo_pagamento_combo.addItems(["", "PIX", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Transferência"])
        form_layout.addRow("Método de Pagamento:", self.metodo_pagamento_combo)
        
        layout.addLayout(form_layout)
        
        # Nota sobre campos obrigatórios
        note_label = QLabel("* Campos obrigatórios")
        note_label.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        layout.addWidget(note_label)
        
        # Botões
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setFixedWidth(100)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Salvar")
        self.save_button.setFixedWidth(100)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #005FA3;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Popula os campos com os dados do membro."""
        # Nome
        self.nome_input.setText(self.member_data.get('nome', ''))
        
        # Plano
        plano = self.member_data.get('plano', '')
        if plano in PLANOS:
            self.plano_combo.setCurrentText(plano)
        
        # Vencimento do Plano
        vencimento_str = self.member_data.get('vencimento_plano', '')
        if vencimento_str:
            vencimento_dt = parse_date(vencimento_str)
            if vencimento_dt:
                self.vencimento_plano_input.setDate(
                    QDate(vencimento_dt.year, vencimento_dt.month, vencimento_dt.day)
                )
        
        # Data de Nascimento
        data_nasc_str = self.member_data.get('data_nascimento', '')
        if data_nasc_str:
            data_nasc_dt = parse_date(data_nasc_str)
            if data_nasc_dt:
                self.data_nascimento_input.setDate(
                    QDate(data_nasc_dt.year, data_nasc_dt.month, data_nasc_dt.day)
                )
        
        # WhatsApp
        self.whatsapp_input.setText(self.member_data.get('whatsapp', ''))
        
        # Gênero
        genero = self.member_data.get('genero', '')
        if genero:
            self.genero_combo.setCurrentText(genero)
        
        # Calçado
        self.calcado_input.setText(self.member_data.get('calcado', ''))
        
        # Email
        self.email_input.setText(self.member_data.get('email', ''))
        
        # Ajusta visibilidade do campo de vencimento
        self._toggle_vencimento_visibility()
    
    def _connect_signals(self):
        """Conecta os sinais."""
        self.plano_combo.currentTextChanged.connect(self._on_plano_changed)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._on_save)
    
    def _on_plano_changed(self, plano: str):
        """Atualiza a visibilidade e valor do campo de vencimento quando o plano muda."""
        self._toggle_vencimento_visibility()
        
        # Calcula automaticamente a nova data de vencimento
        if plano in PLANOS_COM_VENCIMENTO:
            new_due_date = calculate_new_due_date(plano)
            if new_due_date:
                self.vencimento_plano_input.setDate(
                    QDate(new_due_date.year, new_due_date.month, new_due_date.day)
                )
    
    def _toggle_vencimento_visibility(self):
        """Mostra ou esconde o campo de vencimento baseado no plano selecionado."""
        plano = self.plano_combo.currentText()
        has_vencimento = plano in PLANOS_COM_VENCIMENTO
        
        self.vencimento_plano_label.setVisible(has_vencimento)
        self.vencimento_plano_input.setVisible(has_vencimento)
    
    def _validate_fields(self) -> bool:
        """Valida os campos obrigatórios."""
        # Nome é obrigatório
        if not self.nome_input.text().strip():
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "O nome do membro é obrigatório."
            )
            self.nome_input.setFocus()
            return False
        
        # Plano é obrigatório
        if not self.plano_combo.currentText():
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "O plano do membro é obrigatório."
            )
            self.plano_combo.setFocus()
            return False
        
        return True
    
    def _calculate_estado_plano(self, vencimento_str: Optional[str]) -> str:
        """Calcula o estado do plano baseado na data de vencimento."""
        if not vencimento_str:
            return "ATIVO"
        
        vencimento_dt = parse_date(vencimento_str)
        if not vencimento_dt:
            return "ATIVO"
        
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        vencimento_dt = vencimento_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Se a data de vencimento já passou, o plano está INATIVO
        if vencimento_dt < hoje:
            return "INATIVO"
        else:
            return "ATIVO"
    
    def _on_save(self):
        """Salva as alterações do membro."""
        if not self._validate_fields():
            return
        
        # Coleta os dados do formulário
        plano = self.plano_combo.currentText()
        
        # Vencimento do plano (apenas se aplicável)
        vencimento_str = None
        if plano in PLANOS_COM_VENCIMENTO:
            vencimento_date = self.vencimento_plano_input.date()
            vencimento_str = vencimento_date.toString("dd/MM/yyyy")
        
        # Calcula o estado do plano
        estado_plano = self._calculate_estado_plano(vencimento_str)
        
        # Data de nascimento (opcional)
        data_nasc_str = None
        if self.data_nascimento_input.text() != "Não informado":
            data_nasc_date = self.data_nascimento_input.date()
            data_nasc_str = data_nasc_date.toString("dd/MM/yyyy")
        
        # Monta o dicionário com os dados atualizados
        updated_data = {
            'id': self.member_id,
            'nome': self.nome_input.text().strip(),
            'plano': plano,
            'vencimento_plano': vencimento_str,
            'estado_plano': estado_plano,
            'data_nascimento': data_nasc_str,
            'whatsapp': self.whatsapp_input.text().strip(),
            'genero': self.genero_combo.currentText(),
            'calcado': self.calcado_input.text().strip(),
            'email': self.email_input.text().strip(),
            'metodo_pagamento': self.metodo_pagamento_combo.currentText()
        }
        
        # Emite o sinal com os dados atualizados
        self.member_updated.emit(updated_data)
        
        # Fecha o diálogo
        self.accept()
