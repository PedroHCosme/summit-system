"""Diálogo para editar informações de um membro."""

from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDateEdit, QPushButton,
    QLabel, QMessageBox, QTextEdit, QSpinBox, QDoubleSpinBox, QWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from src.config import PLANOS_COM_VENCIMENTO
from src.utils.utils import calculate_new_due_date, parse_date
from src.utils.date_utils import coerce_to_date, format_display_date


class EditMemberDialog(QDialog):
    """Diálogo para editar um membro existente."""
    
    member_updated = pyqtSignal(dict)
    
    def __init__(self, member_data: dict, parent=None):
        """Inicializa diálogo com dados atuais e opções dinâmicas de plano."""
        super().__init__(parent)
        self.member_data = member_data.copy()
        self.member_id = member_data.get('id')
        self.plans_cache = {}
        
        self.setWindowTitle("Editar Membro")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self._setup_ui()
        self._populate_fields()
        self._connect_signals()
    
    def _load_plans_from_db(self):
        """Carrega planos ativos usando o serviço centralizado."""
        try:
            from src.services.plan_service import get_plan_service
            plan_service = get_plan_service()

            self.plans_cache = plan_service.get_plans_as_dict()
            return plan_service.get_plan_names()
        except Exception as e:
            print(f"Error loading plans from PlanService: {e}")

        from src import config
        return config.PLANOS
    
    def _setup_ui(self):
        """Configura a interface do diálogo."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("Editar Informações do Membro")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007ACC;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        from PyQt6.QtWidgets import QScrollArea, QWidget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 10, 0)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome completo do membro")
        form_layout.addRow("Nome *:", self.nome_input)
        
        self.apelido_input = QLineEdit()
        self.apelido_input.setPlaceholderText("Opcional")
        form_layout.addRow("Apelido:", self.apelido_input)
        
        self.plano_combo = QComboBox()
        plan_names = self._load_plans_from_db()
        self.plano_combo.addItems(plan_names)
        form_layout.addRow("Plano *:", self.plano_combo)
        
        self.vencimento_plano_label = QLabel("Vencimento do Plano *:")
        self.vencimento_plano_input = QDateEdit()
        self.vencimento_plano_input.setCalendarPopup(True)
        self.vencimento_plano_input.setDisplayFormat("dd/MM/yyyy")
        self.vencimento_plano_input.setDate(QDate.currentDate())
        form_layout.addRow(self.vencimento_plano_label, self.vencimento_plano_input)
        
        self.voucher_widget = QWidget()
        voucher_layout = QVBoxLayout(self.voucher_widget)
        voucher_layout.setContentsMargins(0, 0, 0, 0)
        voucher_layout.setSpacing(5)
        
        vc_layout = QHBoxLayout()
        vc_label = QLabel("Quantidade de Diárias:")
        self.voucher_credits_spin = QSpinBox()
        self.voucher_credits_spin.setRange(1, 100)
        self.voucher_credits_spin.setValue(10)
        vc_layout.addWidget(vc_label)
        vc_layout.addWidget(self.voucher_credits_spin, 1)
        voucher_layout.addLayout(vc_layout)
        
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
        form_layout.addRow("", self.voucher_widget)
        
        self.data_nascimento_input = QLineEdit()
        self.data_nascimento_input.setPlaceholderText("dd/mm/aaaa")
        form_layout.addRow("Data de Nascimento:", self.data_nascimento_input)
        
        self.whatsapp_input = QLineEdit()
        self.whatsapp_input.setPlaceholderText("(00) 00000-0000")
        form_layout.addRow("WhatsApp *:", self.whatsapp_input)
        
        self.genero_combo = QComboBox()
        self.genero_combo.addItems(["", "Masculino", "Feminino", "Outro"])
        form_layout.addRow("Gênero:", self.genero_combo)
        
        self.calcado_input = QLineEdit()
        self.calcado_input.setPlaceholderText("Ex: 42")
        form_layout.addRow("Calçado *:", self.calcado_input)

        self.profissao_input = QLineEdit()
        self.profissao_input.setPlaceholderText("Ex: Engenheiro")
        form_layout.addRow("Profissão:", self.profissao_input)

        self.contato_emergencia_input = QLineEdit()
        self.contato_emergencia_input.setPlaceholderText("Nome e Telefone")
        form_layout.addRow("Contato de Emergência:", self.contato_emergencia_input)

        self.observacoes_input = QTextEdit()
        self.observacoes_input.setPlaceholderText("Informações adicionais...")
        self.observacoes_input.setMaximumHeight(80)
        form_layout.addRow("Observações:", self.observacoes_input)

        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemplo@email.com")
        form_layout.addRow("Email:", self.email_input)
        
        self.treina_combo = QComboBox()
        self.treina_combo.addItems(["Não", "Sim"])
        form_layout.addRow("Treina:", self.treina_combo)
        
        self.vencimento_treino_label = QLabel("Vencimento do Treino:")
        self.vencimento_treino_input = QDateEdit()
        self.vencimento_treino_input.setCalendarPopup(True)
        self.vencimento_treino_input.setDisplayFormat("dd/MM/yyyy")
        self.vencimento_treino_input.setDate(QDate.currentDate())
        form_layout.addRow(self.vencimento_treino_label, self.vencimento_treino_input)
        
        self.metodo_pagamento_combo = QComboBox()
        from src.core.payment_constants import METODOS_PAGAMENTO_UI
        self.metodo_pagamento_combo.addItems([""] + METODOS_PAGAMENTO_UI)
        form_layout.addRow("Método de Pagamento:", self.metodo_pagamento_combo)
        
        scroll_layout.addLayout(form_layout)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        note_label = QLabel("* Campos obrigatórios")
        note_label.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        main_layout.addWidget(note_label)
        
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
        self.save_button.setDefault(True)
        self.save_button.setAutoDefault(True)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Popula os campos com os dados do membro."""
        self.nome_input.setText(self.member_data.get('nome', ''))

        self.apelido_input.setText(self.member_data.get('apelido', ''))

        plano = self.member_data.get('plano', '')
        if plano in self.plans_cache or self.plano_combo.findText(plano) >= 0:
            self.plano_combo.setCurrentText(plano)

        vencimento_val = self.member_data.get('vencimento_plano')
        vencimento_dt = coerce_to_date(vencimento_val)
        if vencimento_dt:
            self.vencimento_plano_input.setDate(
                QDate(vencimento_dt.year, vencimento_dt.month, vencimento_dt.day)
            )
        
        voucher_credits = self.member_data.get('voucher_credits', 0) or 0
        self.voucher_credits_spin.setValue(voucher_credits)

        self.data_nascimento_input.setText(self.member_data.get('data_nascimento', ''))

        self.whatsapp_input.setText(self.member_data.get('whatsapp', ''))

        genero = self.member_data.get('genero', '')
        if genero:
            self.genero_combo.setCurrentText(genero)

        self.calcado_input.setText(self.member_data.get('calcado', ''))
        self.profissao_input.setText(self.member_data.get('profissao', ''))
        self.contato_emergencia_input.setText(self.member_data.get('contato_emergencia', ''))

        self.observacoes_input.setText(self.member_data.get('observacoes', ''))

        self.email_input.setText(self.member_data.get('email', ''))

        treina = self.member_data.get('treina', 'Não')
        self.treina_combo.setCurrentText(treina)

        vencimento_treino_val = self.member_data.get('vencimento_treino')
        vencimento_treino_dt = coerce_to_date(vencimento_treino_val)
        if vencimento_treino_dt:
            self.vencimento_treino_input.setDate(
                QDate(vencimento_treino_dt.year, vencimento_treino_dt.month, vencimento_treino_dt.day)
            )
        
        self._toggle_vencimento_visibility()
        self._toggle_voucher_visibility()
        self._toggle_treino_visibility()
    
    def _connect_signals(self):
        """Conecta os sinais."""
        self.plano_combo.currentTextChanged.connect(self._on_plano_changed)
        self.treina_combo.currentTextChanged.connect(self._on_treina_changed)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._on_save)
    
    def _on_plano_changed(self, plano: str):
        """Atualiza a visibilidade e valor do campo de vencimento quando o plano muda."""
        self._toggle_vencimento_visibility()
        self._toggle_voucher_visibility()
        
        is_quota = False
        if plano in self.plans_cache:
            is_quota = self.plans_cache[plano].get('is_quota', False)
        
        if is_quota:
            plan_info = self.plans_cache[plano]
            self.voucher_credits_spin.setValue(plan_info.get('quota_amount', 10))
            self.voucher_price_spin.setValue(plan_info.get('preco', 0))
        elif plano in PLANOS_COM_VENCIMENTO:
            new_due_date = calculate_new_due_date(plano)
            if new_due_date:
                self.vencimento_plano_input.setDate(
                    QDate(new_due_date.year, new_due_date.month, new_due_date.day)
                )
    
    def _toggle_vencimento_visibility(self):
        """Mostra ou esconde o campo de vencimento baseado no plano selecionado."""
        plano = self.plano_combo.currentText()
        
        is_quota = False
        if plano in self.plans_cache:
            is_quota = self.plans_cache[plano].get('is_quota', False)
        
        has_vencimento = plano in PLANOS_COM_VENCIMENTO and not is_quota
        
        self.vencimento_plano_label.setVisible(has_vencimento)
        self.vencimento_plano_input.setVisible(has_vencimento)
    
    def _toggle_voucher_visibility(self):
        """Mostra ou esconde campos de voucher conforme tipo do plano."""
        plano = self.plano_combo.currentText()
        is_quota = False
        if plano in self.plans_cache:
            is_quota = self.plans_cache[plano].get('is_quota', False)
        
        self.voucher_widget.setVisible(is_quota)
    
    def _on_treina_changed(self, treina: str):
        """Atualiza a visibilidade e valor do campo de vencimento do treino quando muda."""
        self._toggle_treino_visibility()
        
        if treina == "Sim":
            from datetime import timedelta
            from src import config
            
            today = datetime.now()
            vencimento = today + timedelta(days=config.TREINO_VALIDADE_DIAS)
            self.vencimento_treino_input.setDate(
                QDate(vencimento.year, vencimento.month, vencimento.day)
            )
    
    def _toggle_treino_visibility(self):
        """Mostra ou esconde o campo de vencimento do treino baseado na seleção."""
        treina = self.treina_combo.currentText()
        has_treino = treina == "Sim"
        
        self.vencimento_treino_label.setVisible(has_treino)
        self.vencimento_treino_input.setVisible(has_treino)
    
    def _validate_fields(self) -> bool:
        """Valida os campos obrigatórios."""
        if not self.nome_input.text().strip():
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "O nome do membro é obrigatório."
            )
            self.nome_input.setFocus()
            return False
        
        if not self.plano_combo.currentText():
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "O plano do membro é obrigatório."
            )
            self.plano_combo.setFocus()
            return False

        if not self.whatsapp_input.text().strip():
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "O telefone (WhatsApp) é obrigatório."
            )
            self.whatsapp_input.setFocus()
            return False

        if not self.calcado_input.text().strip():
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "O número de calçado é obrigatório."
            )
            self.calcado_input.setFocus()
            return False

        return True
    
    def _calculate_estado_plano(self, vencimento: Optional['date']) -> str:
        """Calcula o estado do plano baseado na data de vencimento."""
        from src.core.plan_status import ATIVO, INATIVO
        if not vencimento:
            return ATIVO
        
        from datetime import date as _date
        hoje = _date.today()
        
        if vencimento < hoje:
            return INATIVO
        else:
            return ATIVO
    
    def _on_save(self):
        """Salva as alterações e fecha o diálogo."""
        if not self._validate_fields():
            return
        
        plano = self.plano_combo.currentText()

        vencimento_date_obj = None
        if plano in PLANOS_COM_VENCIMENTO:
            vencimento_date_obj = self.vencimento_plano_input.date().toPyDate()
        
        estado_plano = self._calculate_estado_plano(vencimento_date_obj)

        data_nasc_str = self.data_nascimento_input.text().strip()
        if data_nasc_str:
            from src.utils.utils import parse_date
            if not parse_date(data_nasc_str):
                QMessageBox.warning(
                    self,
                    "Data Inválida",
                    "A data de nascimento informada é inválida. Use o formato dd/mm/aaaa."
                )
                return
        
        metodo_pagamento = self.metodo_pagamento_combo.currentText()

        old_plano = self.member_data.get('plano', '')
        plano_changed = plano != old_plano

        treina = self.treina_combo.currentText()
        vencimento_treino_date_obj = None
        if treina == "Sim":
            vencimento_treino_date_obj = self.vencimento_treino_input.date().toPyDate()
        
        old_treina = self.member_data.get('treina', 'Não')
        treina_activated = old_treina == "Não" and treina == "Sim"

        if plano_changed and not metodo_pagamento:
            from src.ui.dialogs.payment_method_dialog import PaymentMethodDialog
            from src.config import PLANOS_PRECOS
            
            valor = PLANOS_PRECOS.get(plano, 0.0)
            
            if valor > 0 or plano == "Cortesia":
                dialog = PaymentMethodDialog(old_plano, plano, valor, self)
                
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    metodo_pagamento = dialog.get_payment_method()
                else:
                    return

        if treina_activated and not metodo_pagamento:
            from src.ui.dialogs.payment_method_dialog import PaymentMethodDialog
            from src import config
            
            valor = config.TREINO_PRECO
            
            dialog = PaymentMethodDialog("", "Treino", valor, self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                metodo_pagamento = dialog.get_payment_method()
            else:
                return

        is_quota = False
        if plano in self.plans_cache:
            is_quota = self.plans_cache[plano].get('is_quota', False)

        if is_quota:
            vencimento_date_obj = None
            estado_plano = 'ATIVO'

        updated_data = {
            'id': self.member_id,
            'nome': self.nome_input.text().strip(),
            'apelido': self.apelido_input.text().strip(),
            'plano': plano,
            'vencimento_plano': vencimento_date_obj,
            'estado_plano': estado_plano,
            'data_nascimento': data_nasc_str,
            'whatsapp': self.whatsapp_input.text().strip(),
            'genero': self.genero_combo.currentText(),
            'calcado': self.calcado_input.text().strip(),
            'profissao': self.profissao_input.text().strip(),
            'contato_emergencia': self.contato_emergencia_input.text().strip(),
            'observacoes': self.observacoes_input.toPlainText().strip(),
            'email': self.email_input.text().strip(),
            'metodo_pagamento': metodo_pagamento,
            'treina': treina,
            'vencimento_treino': vencimento_treino_date_obj,
            'treina_activated': treina_activated
        }

        if is_quota:
            updated_data['voucher_credits'] = self.voucher_credits_spin.value()
            updated_data['price'] = self.voucher_price_spin.value()

        self.member_updated.emit(updated_data)
        self.accept()
