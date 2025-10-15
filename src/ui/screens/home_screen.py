"""Tela inicial de carregamento."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PyQt6.QtCore import Qt


class HomeScreen(QWidget):
    """Tela de carregamento/conexão inicial."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_browser = QTextBrowser()
        self.status_browser.setHtml("<p style='text-align:center; font-size: 18px;'>Conectando ao banco de dados...</p>")
        self.status_browser.setMaximumHeight(100)
        self.status_browser.setStyleSheet("border: none;")
        
        layout.addWidget(self.status_browser)
    
    def append_status(self, message: str):
        """Adiciona uma mensagem de status."""
        self.status_browser.append(message)
    
    def set_error(self, message: str):
        """Define uma mensagem de erro."""
        self.status_browser.setHtml(f"""
            <p style="color: #FF6B6B; text-align: center; font-size: 16px;">
                {message}
            </p>
        """)
