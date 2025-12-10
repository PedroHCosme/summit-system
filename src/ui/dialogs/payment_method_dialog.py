"""Diálogo para solicitar método de pagamento."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt


class PaymentMethodDialog(QDialog):
    """Diálogo para selecionar método de pagamento."""
    
    def __init__(self, old_plan: str, new_plan: str, valor: float, parent=None):
        super().__init__(parent)
        self.selected_method = None
        self.old_plan = old_plan
        self.new_plan = new_plan
        self.valor = valor
        
        self.setWindowTitle("Método de Pagamento Necessário")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("💳 Mudança de Plano Detectada")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007ACC;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Informação da mudança
        info_text = f"""
        <p style='font-size: 13px;'>
        Você está alterando o plano:<br>
        <b>De:</b> {self.old_plan}<br>
        <b>Para:</b> {self.new_plan}<br>
        <b>Valor:</b> R$ {self.valor:.2f}
        </p>
        <p style='font-size: 12px; color: #666;'>
        Para registrar este pagamento no sistema financeiro,<br>
        por favor, selecione o método de pagamento utilizado:
        </p>
        """
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Combo de método de pagamento
        method_layout = QHBoxLayout()
        method_label = QLabel("Método de Pagamento:")
        method_label.setStyleSheet("font-weight: bold;")
        
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "PIX", 
            "Cartão de Crédito", 
            "Cartão de Débito", 
            "Dinheiro", 
            "Transferência"
        ])
        self.method_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #007ACC;
                border-radius: 5px;
                font-size: 13px;
            }
        """)
        
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.method_combo, 1)
        layout.addLayout(method_layout)
        
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
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        # Botão Confirmar
        confirm_btn = QPushButton("Confirmar Pagamento")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
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
    
    def _on_confirm(self):
        """Confirma a seleção do método de pagamento."""
        self.selected_method = self.method_combo.currentText()
        self.accept()
    
    def get_payment_method(self) -> str:
        """Retorna o método de pagamento selecionado."""
        return self.selected_method if self.selected_method else ""
