"""Diálogo para renovar plano de um membro."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
    QPushButton, QLabel, QDateEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from src.config import PLANOS_PRECOS, PLANOS
from src.utils.utils import calculate_new_due_date, parse_date


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
        self.setMinimumWidth(450)
        
        self._setup_ui()
    
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
        self.plan_combo.addItems(PLANOS)
        self.plan_combo.setCurrentText(self.current_plan)
        self.plan_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #007ACC;
                border-radius: 5px;
                font-size: 13px;
            }
        """)
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
        
        vencimento_layout.addWidget(vencimento_label)
        vencimento_layout.addWidget(self.vencimento_input, 1)
        layout.addLayout(vencimento_layout)
        
        # Valor da renovação
        self.valor_label = QLabel()
        self._update_price_display(self.current_plan)
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
    
    def _on_plan_changed(self, new_plan):
        """Atualiza a data de vencimento e o valor quando o plano muda."""
        # Atualizar valor
        self._update_price_display(new_plan)
        
        # Recalcular vencimento
        # Se mudou de plano, calculamos a partir de hoje. 
        # Se é o mesmo plano, tentamos manter a lógica de extensão (start_date=current_due_date)
        
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
        valor = PLANOS_PRECOS.get(plan, 0.0)
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
            QMessageBox.warning(
                self,
                "Atenção",
                "Selecione um método de pagamento."
            )
            return
        
        # Obter nova data de vencimento
        new_vencimento_date = self.vencimento_input.date()
        new_vencimento_str = new_vencimento_date.toString("dd/MM/yyyy")
        
        # Preparar dados da renovação
        renewal_data = {
            'id': self.member_id,
            'vencimento_plano': new_vencimento_str,
            'metodo_pagamento': metodo,
            'plano': self.plan_combo.currentText()
        }
        
        # Emitir sinal com os dados
        self.plan_renewed.emit(renewal_data)
        
        # Fechar o diálogo
        self.accept()
