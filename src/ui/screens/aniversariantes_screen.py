"""Tela de aniversariantes do mês."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextBrowser, QComboBox
from PyQt6.QtCore import Qt
from datetime import datetime


class AniversariantesScreen(QWidget):
    """Tela de aniversariantes."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Aniversariantes do Mês")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Layout horizontal para seletor de mês e botão de busca
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        # Label do seletor
        month_label = QLabel("Selecione o mês:")
        month_label.setStyleSheet("font-size: 14px; color: #555555;")
        control_layout.addWidget(month_label)
        
        # Seletor de mês
        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(150)
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        self.month_combo.addItems(meses)
        
        # Selecionar o mês atual por padrão
        mes_atual = datetime.now().month - 1  # 0-indexed
        self.month_combo.setCurrentIndex(mes_atual)
        
        control_layout.addWidget(self.month_combo)
        control_layout.addStretch()
        
        # Botão de busca
        self.search_button = QPushButton("Buscar Aniversariantes")
        self.search_button.setMinimumWidth(180)
        control_layout.addWidget(self.search_button)
        
        layout.addLayout(control_layout)
        
        # Área de resultados
        self.result_browser = QTextBrowser()
        self.result_browser.setOpenExternalLinks(True)
        self.result_browser.setHtml(self._get_initial_message())
        layout.addWidget(self.result_browser)
    
    def get_selected_month(self) -> int:
        """Retorna o mês selecionado (1-12)."""
        return self.month_combo.currentIndex() + 1
    
    def get_selected_month_name(self) -> str:
        """Retorna o nome do mês selecionado."""
        return self.month_combo.currentText()
    
    def _get_initial_message(self):
        """Retorna a mensagem inicial."""
        return """
            <div style="text-align: center; padding: 40px;">
                <h3 style="color: #007ACC;">Bem-vindo!</h3>
                <p style="color: #333333;">Selecione um mês e clique no botão para buscar os aniversariantes.</p>
            </div>
        """
    
    def set_searching_state(self):
        """Define o estado de busca."""
        self.search_button.setText("Buscando...")
        self.search_button.setEnabled(False)
        self.result_browser.clear()
    
    def set_ready_state(self):
        """Define o estado pronto."""
        self.search_button.setText("Buscar Aniversariantes")
        self.search_button.setEnabled(True)
    
    def append_status(self, status: str):
        """Adiciona status ao browser."""
        self.result_browser.append(status)
    
    def set_results(self, html: str):
        """Define os resultados em HTML."""
        self.result_browser.setHtml(html)
