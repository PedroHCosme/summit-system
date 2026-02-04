"""Diálogo para renovar plano de um membro."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
    QPushButton, QLabel, QDateEdit, QMessageBox,
    QSpinBox, QDoubleSpinBox, QWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from src.data.data_provider import get_provider
from src.data.models import Plano
from src.utils.utils import calculate_new_due_date, parse_date
from sqlalchemy import select


class RenewPlanDialog(QDialog):
    """Diálogo para renovar o plano de um membro."""
    
    plan_renewed = pyqtSignal(dict)  # Sinal emitido quando o plano é renovado
    
    def __init__(self, member_data: dict, parent=None):
        super().__init__(parent)
        self.member_data = member_data
        self.member_id = member_data.get('id')
        self.current_plan = member_data.get('plano', '')
        self.current_vencimento = member_data.get('vencimento_plano', '')
        
        self.setWindowTitle("Renovar Plano")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        self._setup_ui()
    
    def _load_plans(self):
        """Carrega os planos do banco de dados ou configuração."""
        try:
            from src.services.plan_service import get_plan_service
            plan_service = get_plan_service()
            
            plans_dict = plan_service.get_plans_as_dict()
            self.plans_cache = {name: info['preco'] for name, info in plans_dict.items()}
            
            # Populate combo
            self.plan_combo.clear()
            self.plan_combo.addItems(sorted(plan_service.get_plan_names()))
            
            # Set current plan if valid
            if self.current_plan in self.plans_cache:
                self.plan_combo.setCurrentText(self.current_plan)
                
        except Exception as e:
            print(f"Erro ao carregar planos: {e}")
            # Fallback
            from src import config
            self.plans_cache = config.PLANOS_PRECOS.copy()
            self.plan_combo.addItems(sorted(config.PLANOS))

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Título
        title_label = QLabel("🔄 Renovar Plano")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #007ACC;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Informações do membro
        # Informações do membro
        member_info = f"""
        <div style='background-color: #F5F5F5; padding: 15px; border-radius: 8px; border-left: 4px solid #007ACC;'>
            <p style='font-size: 14px; margin: 5px 0;'><b>Membro:</b> {self.member_data.get('nome', 'N/A')}</p>
            <p style='font-size: 14px; margin: 5px 0;'><b>Vencimento Atual:</b> {self.current_vencimento or 'N/A'}</p>
        </div>
        """
        info_label = QLabel(member_info)
        layout.addWidget(info_label)

        # Seleção de Plano
        plan_layout = QHBoxLayout()
        plan_label = QLabel("Plano:")
        plan_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.plan_combo = QComboBox()
        self.plan_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #007ACC;
                border-radius: 5px;
                font-size: 13px;
            }
        """)
        
        # Carregar planos do banco
        self.plans_cache = {}  # {nome: preco}
        self._load_plans()
        
        self.plan_combo.currentTextChanged.connect(self._on_plan_changed)
        
        plan_layout.addWidget(plan_label)
        plan_layout.addWidget(self.plan_combo, 1)
        layout.addLayout(plan_layout)
        
        # Nova data de vencimento
        vencimento_layout = QHBoxLayout()
        vencimento_label = QLabel("Nova Data de Vencimento:")
        vencimento_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.vencimento_input = QDateEdit()
        self.vencimento_input.setCalendarPopup(True)
        self.vencimento_input.setDisplayFormat("dd/MM/yyyy")
        
        # Calcular nova data de vencimento baseada no plano atual
        current_due_date = parse_date(self.current_vencimento)
        new_due_date = calculate_new_due_date(self.current_plan, start_date=current_due_date)
        if new_due_date:
            # Converter datetime para QDate
            self.vencimento_input.setDate(QDate(new_due_date.year, new_due_date.month, new_due_date.day))
        else:
            self.vencimento_input.setDate(QDate.currentDate())
        
        self.vencimento_input.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 2px solid #007ACC;
                border-radius: 5px;
                font-size: 13px;
            }
        """)
        
        self.vencimento_label = vencimento_label # Store reference to toggle visibility
        self.vencimento_input = self.vencimento_input # Already stored
        self.vencimento_widget = QWidget() # Wrapper to hide the whole row
        self.vencimento_widget.setLayout(vencimento_layout)
        layout.addWidget(self.vencimento_widget)
        
        # --- Voucher Fields (initially hidden) ---
        
        # Voucher Credits Input
        self.voucher_credits_widget = QWidget()
        vc_layout = QHBoxLayout(self.voucher_credits_widget)
        vc_layout.setContentsMargins(0, 0, 0, 0)
        
        vc_label = QLabel("Quantidade de Diárias (Créditos):")
        vc_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.voucher_credits_spin = QSpinBox()
        self.voucher_credits_spin.setRange(1, 100)
        self.voucher_credits_spin.setValue(10) # Default sensible value
        self.voucher_credits_spin.setStyleSheet("""
            QSpinBox { padding: 8px; border: 2px solid #007ACC; border-radius: 5px; font-size: 13px; }
        """)
        
        vc_layout.addWidget(vc_label)
        vc_layout.addWidget(self.voucher_credits_spin, 1)
        layout.addWidget(self.voucher_credits_widget)
        
        # Voucher Custom Price Input
        self.voucher_price_widget = QWidget()
        vp_layout = QHBoxLayout(self.voucher_price_widget)
        vp_layout.setContentsMargins(0, 0, 0, 0)
        
        vp_label = QLabel("Valor do Voucher (R$):")
        vp_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.voucher_price_spin = QDoubleSpinBox()
        self.voucher_price_spin.setRange(0, 99999)
        self.voucher_price_spin.setDecimals(2)
        self.voucher_price_spin.setPrefix("R$ ")
        self.voucher_price_spin.setValue(0.0)
        self.voucher_price_spin.setStyleSheet("""
            QDoubleSpinBox { padding: 8px; border: 2px solid #007ACC; border-radius: 5px; font-size: 13px; }
        """)
        
        vp_layout.addWidget(vp_label)
        vp_layout.addWidget(self.voucher_price_spin, 1)
        layout.addWidget(self.voucher_price_widget)
        
        # Valor da renovação (original label)
        self.valor_label = QLabel()
        self._update_price_display(self.plan_combo.currentText()) # Use current text from combo
        layout.addWidget(self.valor_label)
        
        # Método de pagamento
        metodo_layout = QHBoxLayout()
        metodo_label = QLabel("Método de Pagamento:")
        metodo_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.metodo_combo = QComboBox()
        self.metodo_combo.addItems([
            "PIX", 
            "Cartão de Crédito", 
            "Cartão de Débito", 
            "Dinheiro", 
            "Transferência"
        ])
        self.metodo_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #007ACC;
                border-radius: 5px;
                font-size: 13px;
            }
        """)
        
        metodo_layout.addWidget(metodo_label)
        metodo_layout.addWidget(self.metodo_combo, 1)
        layout.addLayout(metodo_layout)
        
        # Botões
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Botão Cancelar
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        # Botão Confirmar
        confirm_btn = QPushButton("✅ Confirmar Renovação")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        confirm_btn.setDefault(True)
        confirm_btn.setAutoDefault(True)
        confirm_btn.clicked.connect(self._on_confirm)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(confirm_btn)
        layout.addLayout(button_layout)
        
        # Initialize visibility based on current plan selection
        self._on_plan_changed(self.plan_combo.currentText())
    
    def _on_plan_changed(self, new_plan):
        """Atualiza a interface quando o plano muda."""
        is_voucher = (new_plan == "Voucher")
        
        # Toggle visibility
        self.vencimento_widget.setVisible(not is_voucher)
        self.voucher_credits_widget.setVisible(is_voucher)
        self.voucher_price_widget.setVisible(is_voucher)
        self.valor_label.setVisible(not is_voucher) # Hide standard price display for voucher
        
        # Update standard price display
        if not is_voucher:
            self._update_price_display(new_plan)
        
        # Recalcular vencimento (only if not voucher)
        if not is_voucher:
            if new_plan == self.current_plan:
                start_date = parse_date(self.current_vencimento)
            else:
                start_date = datetime.now()
                
            new_due_date = calculate_new_due_date(new_plan, start_date=start_date)
            
            if new_due_date:
                self.vencimento_input.setDate(QDate(new_due_date.year, new_due_date.month, new_due_date.day))
            else:
                self.vencimento_input.setDate(QDate.currentDate())

    def _update_price_display(self, plan):
        """Atualiza o display do preço."""
        valor = self.plans_cache.get(plan, 0.0)
        valor_info = f"""
        <div style='background-color: #E8F5E9; padding: 12px; border-radius: 8px; border-left: 4px solid #4CAF50;'>
            <p style='font-size: 15px; margin: 5px 0; text-align: center;'>
                <b>💰 Valor da Renovação:</b> <span style='color: #2E7D32; font-size: 18px;'>R$ {valor:.2f}</span>
            </p>
        </div>
        """
        self.valor_label.setText(valor_info)
    
    def _on_confirm(self):
        """Confirma a renovação do plano."""
        # Validar se selecionou método de pagamento
        metodo = self.metodo_combo.currentText()
        if not metodo:
            QMessageBox.warning(self, "Atenção", "Selecione um método de pagamento.")
            return
        
        selected_plan = self.plan_combo.currentText()
        is_voucher = (selected_plan == "Voucher")
        
        # Preparar dados da renovação
        renewal_data = {
            'id': self.member_id,
            'metodo_pagamento': metodo,
            'plano': selected_plan
        }
        
        if is_voucher:
            renewal_data['voucher_credits'] = self.voucher_credits_spin.value()
            renewal_data['price'] = self.voucher_price_spin.value()
            # Voucher generally doesn't have a due date, or it's infinite. 
            # We can leave it explicitly None or empty.
            renewal_data['vencimento_plano'] = None 
        else:
            new_vencimento_date = self.vencimento_input.date()
            renewal_data['vencimento_plano'] = new_vencimento_date.toString("dd/MM/yyyy")
        
        # Emitir sinal com os dados
        self.plan_renewed.emit(renewal_data)
        
        # Fechar o diálogo
        self.accept()
