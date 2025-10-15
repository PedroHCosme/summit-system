"""Tela de aniversariantes do mês."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextBrowser
from PyQt6.QtCore import Qt


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
        
        # Informação do mês atual
        from src.utils.utils import get_current_sheet_name
        mes_atual = get_current_sheet_name()
        self.mes_label = QLabel(f"Consultando aba: {mes_atual}")
        self.mes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mes_label.setStyleSheet("font-size: 14px; color: #555555;")
        layout.addWidget(self.mes_label)
        
        # Área de resultados
        self.result_browser = QTextBrowser()
        self.result_browser.setOpenExternalLinks(True)
        self.result_browser.setHtml(self._get_initial_message())
        layout.addWidget(self.result_browser)
        
        # Botão de busca
        self.search_button = QPushButton("Buscar Aniversariantes")
        layout.addWidget(self.search_button)
    
    def _get_initial_message(self):
        """Retorna a mensagem inicial."""
        return """
            <div style="text-align: center; padding: 40px;">
                <h3 style="color: #007ACC;">Bem-vindo!</h3>
                <p style="color: #333333;">Clique no botão abaixo para buscar os aniversariantes do mês.</p>
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
