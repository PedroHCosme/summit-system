"""Diálogo para adicionar novo membro."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QPushButton
)
from PyQt6.QtCore import QDate

from src.config import PLANOS_COM_VENCIMENTO


class AddMemberDialog(QDialog):
    """Janela de diálogo para adicionar um novo membro."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Novo Membro")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._connect_signals()
        self._toggle_vencimento_visibility(self.plano_combo.currentText())
        self._toggle_treino_visibility(self.treina_combo.currentText())

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        self.layout = QVBoxLayout(self)
        
        # Formulário
        self.form_layout = QFormLayout()
        
        # Campos
        self.nome_input = QLineEdit()
        self.apelido_input = QLineEdit()
        self.apelido_input.setPlaceholderText("Opcional")
        
        self.plano_combo = QComboBox()
        # Importar PLANOS dinamicamente em tempo de execução para pegar atualizações
        from src import config
        self.plano_combo.addItems(config.PLANOS)
        
        self.vencimento_plano_input = QDateEdit()
        self.vencimento_plano_input.setCalendarPopup(True)
        self.vencimento_plano_input.setDate(QDate.currentDate())
        self.vencimento_plano_input.setDisplayFormat("dd/MM/yyyy")
        
        self.data_nascimento_input = QLineEdit()
        self.data_nascimento_input.setPlaceholderText("dd/mm/aaaa")

        self.whatsapp_input = QLineEdit()
        self.whatsapp_input.setPlaceholderText("(XX) XXXXX-XXXX")
        
        self.genero_combo = QComboBox()
        self.genero_combo.addItems(["", "M", "F"])
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemplo@email.com")

        self.calcado_input = QLineEdit()
        self.calcado_input.setPlaceholderText("Ex: 40")
        
        # Campos de treino
        self.treina_combo = QComboBox()
        self.treina_combo.addItems(["Não", "Sim"])
        
        self.vencimento_treino_input = QDateEdit()
        self.vencimento_treino_input.setCalendarPopup(True)
        self.vencimento_treino_input.setDate(QDate.currentDate())
        self.vencimento_treino_input.setDisplayFormat("dd/MM/yyyy")

        # Adiciona campos ao formulário
        self.form_layout.addRow("Nome (*):", self.nome_input)
        self.form_layout.addRow("Apelido:", self.apelido_input)
        self.form_layout.addRow("Plano (*):", self.plano_combo)
        self.vencimento_row = self.form_layout.addRow("Vencimento do Plano:", self.vencimento_plano_input)
        self.form_layout.addRow("Data de Nascimento (*):", self.data_nascimento_input)
        self.form_layout.addRow("WhatsApp (*):", self.whatsapp_input)
        self.form_layout.addRow("Gênero (*):", self.genero_combo)
        self.form_layout.addRow("Calçado:", self.calcado_input)
        self.form_layout.addRow("Email:", self.email_input)
        self.form_layout.addRow("Treina:", self.treina_combo)
        self.vencimento_treino_row = self.form_layout.addRow("Vencimento do Treino:", self.vencimento_treino_input)
        
        self.layout.addLayout(self.form_layout)

        # Botões
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar")
        self.cancel_button = QPushButton("Cancelar")
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
        self.save_button.setDefault(True)
        self.save_button.setAutoDefault(True)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.save_button)
        
        self.layout.addLayout(self.button_layout)

    def _connect_signals(self):
        """Conecta os sinais dos widgets."""
        self.save_button.clicked.connect(self._on_save)
        self.cancel_button.clicked.connect(self.reject)
        self.plano_combo.currentTextChanged.connect(self._toggle_vencimento_visibility)
        self.treina_combo.currentTextChanged.connect(self._toggle_treino_visibility)

    def _on_save(self):
        """Valida os dados e salva."""
        # Validar data de nascimento
        # Validar data de nascimento
        data_nasc_text = self.data_nascimento_input.text().strip()
        if not data_nasc_text:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Atenção", "Por favor, informe a data de nascimento.")
            return

        from src.utils.utils import parse_date
        if not parse_date(data_nasc_text):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Atenção", "Data de nascimento inválida. Use o formato dd/mm/aaaa.")
            return
            
        self.accept()

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
    
    def _toggle_treino_visibility(self, treina: str):
        """Mostra ou esconde o campo de vencimento do treino baseado na seleção."""
        is_visible = treina == "Sim"
        self.form_layout.labelForField(self.vencimento_treino_input).setVisible(is_visible)
        self.vencimento_treino_input.setVisible(is_visible)
        
        # Calcula automaticamente a data de vencimento do treino (1 mês)
        if is_visible:
            from datetime import timedelta
            from src import config
            
            today = datetime.now()
            vencimento = today + timedelta(days=config.TREINO_VALIDADE_DIAS)
            qdate = QDate(vencimento.year, vencimento.month, vencimento.day)
            self.vencimento_treino_input.setDate(qdate)

    def get_data(self):
        """Retorna os dados do formulário como um dicionário."""
        plano = self.plano_combo.currentText()
        treina = self.treina_combo.currentText()
        
        data = {
            "nome": self.nome_input.text().strip(),
            "apelido": self.apelido_input.text().strip(),
            "plano": plano,
            "data_nascimento": self.data_nascimento_input.text().strip(),
            "whatsapp": self.whatsapp_input.text().strip(),
            "genero": self.genero_combo.currentText(),
            "calcado": self.calcado_input.text().strip(),
            "email": self.email_input.text().strip(),
            "treina": treina,
        }
        
        # Para planos com vencimento, sempre incluir a data
        if plano in PLANOS_COM_VENCIMENTO:
            data["vencimento_plano"] = self.vencimento_plano_input.date().toString("dd/MM/yyyy")
        
        # Para treino ativo, incluir a data de vencimento
        if treina == "Sim":
            data["vencimento_treino"] = self.vencimento_treino_input.date().toString("dd/MM/yyyy")
        
        return data
