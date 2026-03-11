"""Diálogo para adicionar novo membro."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QPushButton, QTextEdit,
    QSpinBox, QDoubleSpinBox, QWidget, QLabel
)
from PyQt6.QtCore import QDate

from src.config import PLANOS_COM_VENCIMENTO


class AddMemberDialog(QDialog):
    """Janela de diálogo para adicionar um novo membro."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Novo Membro")
        self.setMinimumWidth(350)
        self.plans_cache = {}  # {nome: {preco, is_quota, quota_amount}}
        self._setup_ui()
        self._connect_signals()
        self._toggle_vencimento_visibility(self.plano_combo.currentText())
        self._toggle_treino_visibility(self.treina_combo.currentText())
        self._toggle_voucher_visibility(self.plano_combo.currentText())

    def _load_plans_from_db(self):
        """Load plans from database using centralized PlanService."""
        try:
            from src.services.plan_service import get_plan_service
            plan_service = get_plan_service()
            
            # Get plans as dict from centralized service
            self.plans_cache = plan_service.get_plans_as_dict()
            return plan_service.get_plan_names()
        except Exception as e:
            print(f"Error loading plans from PlanService: {e}")
        
        # Fallback to config (should not happen in normal operation)
        from src import config
        return config.PLANOS

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Scroll Area
        from PyQt6.QtWidgets import QScrollArea, QWidget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 10, 0)
        
        # Formulário
        self.form_layout = QFormLayout()
        
        # Campos
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Primeiro nome")
        self.sobrenome_input = QLineEdit()
        self.sobrenome_input.setPlaceholderText("Sobrenome")
        self.apelido_input = QLineEdit()
        self.apelido_input.setPlaceholderText("Opcional")
        
        self.plano_combo = QComboBox()
        # Load plans from database
        plan_names = self._load_plans_from_db()
        self.plano_combo.addItems(plan_names)
        
        self.vencimento_plano_input = QDateEdit()
        self.vencimento_plano_input.setCalendarPopup(True)
        self.vencimento_plano_input.setDate(QDate.currentDate())
        self.vencimento_plano_input.setDisplayFormat("dd/MM/yyyy")
        
        # --- Voucher fields ---
        self.voucher_widget = QWidget()
        voucher_layout = QVBoxLayout(self.voucher_widget)
        voucher_layout.setContentsMargins(0, 0, 0, 0)
        voucher_layout.setSpacing(5)
        
        # Voucher credits
        vc_layout = QHBoxLayout()
        vc_label = QLabel("Quantidade de Diárias:")
        self.voucher_credits_spin = QSpinBox()
        self.voucher_credits_spin.setRange(1, 100)
        self.voucher_credits_spin.setValue(10)
        vc_layout.addWidget(vc_label)
        vc_layout.addWidget(self.voucher_credits_spin, 1)
        voucher_layout.addLayout(vc_layout)
        
        # Voucher price
        vp_layout = QHBoxLayout()
        vp_label = QLabel("Valor Pago (R$):")
        self.voucher_price_spin = QDoubleSpinBox()
        self.voucher_price_spin.setRange(0, 99999)
        self.voucher_price_spin.setDecimals(2)
        self.voucher_price_spin.setPrefix("R$ ")
        self.voucher_price_spin.setValue(200.0)
        vp_layout.addWidget(vp_label)
        vp_layout.addWidget(self.voucher_price_spin, 1)
        voucher_layout.addLayout(vp_layout)
        # --- End voucher fields ---
        
        self.data_nascimento_input = QLineEdit()
        self.data_nascimento_input.setPlaceholderText("dd/mm/aaaa")

        self.whatsapp_input = QLineEdit()
        self.whatsapp_input.setPlaceholderText("(XX) XXXXX-XXXX")
        
        self.genero_combo = QComboBox()
        self.genero_combo.addItems(["", "Masculino", "Feminino", "Outro"])
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemplo@email.com")

        self.calcado_input = QLineEdit()
        self.calcado_input.setPlaceholderText("Ex: 40")

        self.profissao_input = QLineEdit()
        self.profissao_input.setPlaceholderText("Ex: Advogado")

        self.contato_emergencia_input = QLineEdit()
        self.contato_emergencia_input.setPlaceholderText("Nome e Telefone")
        
        self.observacoes_input = QTextEdit()
        self.observacoes_input.setPlaceholderText("Informações adicionais...")
        self.observacoes_input.setMaximumHeight(80)

        
        # Campos de treino
        self.treina_combo = QComboBox()
        self.treina_combo.addItems(["Não", "Sim"])
        
        self.vencimento_treino_input = QDateEdit()
        self.vencimento_treino_input.setCalendarPopup(True)
        self.vencimento_treino_input.setDate(QDate.currentDate())
        self.vencimento_treino_input.setDisplayFormat("dd/MM/yyyy")

        # Adiciona campos ao formulário
        self.form_layout.addRow("Nome (*):", self.nome_input)
        self.form_layout.addRow("Sobrenome (*):", self.sobrenome_input)
        self.form_layout.addRow("Apelido:", self.apelido_input)
        self.form_layout.addRow("Plano (*):", self.plano_combo)
        self.vencimento_row = self.form_layout.addRow("Vencimento do Plano:", self.vencimento_plano_input)
        self.form_layout.addRow("", self.voucher_widget)  # Voucher fields
        self.form_layout.addRow("Data de Nascimento (*):", self.data_nascimento_input)
        self.form_layout.addRow("WhatsApp (*):", self.whatsapp_input)
        self.form_layout.addRow("Gênero (*):", self.genero_combo)
        self.form_layout.addRow("Calçado:", self.calcado_input)
        self.form_layout.addRow("Profissão:", self.profissao_input)
        self.form_layout.addRow("Contato de Emergência:", self.contato_emergencia_input)
        self.form_layout.addRow("Observações:", self.observacoes_input)
        self.form_layout.addRow("Email:", self.email_input)
        self.form_layout.addRow("Treina:", self.treina_combo)
        self.vencimento_treino_row = self.form_layout.addRow("Vencimento do Treino:", self.vencimento_treino_input)
        
        scroll_layout.addLayout(self.form_layout)
        scroll_area.setWidget(scroll_content)
        self.layout.addWidget(scroll_area)

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
        self.plano_combo.currentTextChanged.connect(self._on_plano_changed)
        self.treina_combo.currentTextChanged.connect(self._toggle_treino_visibility)

    def _on_plano_changed(self, plano: str):
        """Handle plan change - update visibility of vencimento and voucher fields."""
        self._toggle_vencimento_visibility(plano)
        self._toggle_voucher_visibility(plano)
        
        # Update default voucher values based on plan
        if plano in self.plans_cache:
            plan_info = self.plans_cache[plano]
            if plan_info.get('is_quota'):
                self.voucher_credits_spin.setValue(plan_info.get('quota_amount', 10))
                self.voucher_price_spin.setValue(plan_info.get('preco', 0))

    def _on_save(self):
        """Valida os dados e salva."""
        from PyQt6.QtWidgets import QMessageBox
        from src.utils.utils import parse_date
        from datetime import date
        
        # Validar nome e sobrenome
        if not self.nome_input.text().strip():
            QMessageBox.warning(self, "Atenção", "Por favor, informe o nome.")
            return
        
        if not self.sobrenome_input.text().strip():
            QMessageBox.warning(self, "Atenção", "Por favor, informe o sobrenome.")
            return
        
        # Validar data de nascimento
        data_nasc_text = self.data_nascimento_input.text().strip()
        if not data_nasc_text:
            QMessageBox.warning(self, "Atenção", "Por favor, informe a data de nascimento.")
            return

        data_nasc = parse_date(data_nasc_text)
        if not data_nasc:
            QMessageBox.warning(self, "Atenção", "Data de nascimento inválida. Use o formato dd/mm/aaaa.")
            return
        
        # Não permitir data de nascimento igual à data atual
        if data_nasc.date() == date.today() if hasattr(data_nasc, 'date') else data_nasc == date.today():
            QMessageBox.warning(self, "Atenção", "A data de nascimento não pode ser a data de hoje.")
            return
            
        self.accept()

    def _toggle_vencimento_visibility(self, plano: str):
        """Mostra ou esconde o campo de vencimento baseado no plano e calcula a data automaticamente."""
        # Check if it's a quota plan (no vencimento needed)
        is_quota = False
        if plano in self.plans_cache:
            is_quota = self.plans_cache[plano].get('is_quota', False)
        
        is_visible = plano in PLANOS_COM_VENCIMENTO and not is_quota
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
    
    def _toggle_voucher_visibility(self, plano: str):
        """Show or hide voucher fields based on plan type."""
        is_quota = False
        if plano in self.plans_cache:
            is_quota = self.plans_cache[plano].get('is_quota', False)
        
        self.voucher_widget.setVisible(is_quota)
    
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
        
        # Check if quota plan
        is_quota = False
        if plano in self.plans_cache:
            is_quota = self.plans_cache[plano].get('is_quota', False)
        
        # Concatena nome + sobrenome para salvar como campo único no banco
        nome_completo = f"{self.nome_input.text().strip()} {self.sobrenome_input.text().strip()}".strip()
        
        data = {
            "nome": nome_completo,
            "apelido": self.apelido_input.text().strip(),
            "plano": plano,
            "data_nascimento": self.data_nascimento_input.text().strip(),
            "whatsapp": self.whatsapp_input.text().strip(),
            "genero": self.genero_combo.currentText(),
            "calcado": self.calcado_input.text().strip(),
            "profissao": self.profissao_input.text().strip(),
            "contato_emergencia": self.contato_emergencia_input.text().strip(),
            "observacoes": self.observacoes_input.toPlainText().strip(),
            "email": self.email_input.text().strip(),
            "treina": treina,
        }
        
        # For quota plans, include voucher data
        if is_quota:
            data["voucher_credits"] = self.voucher_credits_spin.value()
            data["price"] = self.voucher_price_spin.value()
            data["vencimento_plano"] = None  # Quota plans don't expire
            data["estado_plano"] = "ATIVO"
        elif plano in PLANOS_COM_VENCIMENTO:
            # Para planos com vencimento, sempre incluir a data
            data["vencimento_plano"] = self.vencimento_plano_input.date().toPyDate()
        
        # Para treino ativo, incluir a data de vencimento
        if treina == "Sim":
            data["vencimento_treino"] = self.vencimento_treino_input.date().toPyDate()
        
        return data
