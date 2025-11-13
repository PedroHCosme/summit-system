"""Tela inicial de carregamento."""

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QLabel
from PyQt6.QtGui import QPixmap
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
        
        # Adicionar a logo
        logo_label = QLabel(self)
        # Navega da pasta 'screens' para 'ui' e depois para 'assets'
        base_path = os.path.dirname(os.path.dirname(__file__))
        logo_path = os.path.join(base_path, "assets", "summit.png")
        
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Redimensiona a imagem para uma largura de 400px mantendo a proporção
            scaled_pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)
        
        self.status_browser = QTextBrowser()
        self.status_browser.setHtml("<p style='text-align:center; font-size: 18px;'>Conectando ao banco de dados...</p>")
        self.status_browser.setMaximumHeight(100)
        self.status_browser.setStyleSheet("border: none;")
        
        layout.addWidget(self.status_browser)
    
    def append_status(self, message: str):
        """Adiciona uma mensagem de status."""
        self.status_browser.append(f"<p style='text-align:center;'>{message}</p>")
    
    def set_error(self, message: str):
        """Define uma mensagem de erro."""
        self.status_browser.setHtml(f"""
            <p style="color: #FF6B6B; text-align: center; font-size: 16px;">
                {message}
            </p>
        """)
