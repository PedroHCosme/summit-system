"""Tela de check-in de membros."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QTextBrowser
)
from PyQt6.QtCore import Qt


class CheckinScreen(QWidget):
    """Tela de check-in de membros."""
    
    def __init__(self):
        super().__init__()
        self.current_member_id = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title_label = QLabel("Check-in de Membro")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Campo de busca
        search_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Digite o nome do membro para check-in...")
        search_layout.addWidget(self.name_input)

        self.search_button = QPushButton("Buscar")
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # Layout para resultados e detalhes
        main_content_layout = QHBoxLayout()

        # Coluna de resultados da busca
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_label = QLabel("Resultados da Busca:")
        results_label.setStyleSheet("color: #007ACC; font-weight: bold; font-size: 14px;")
        results_layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #DDDDDD;
            }
            QListWidget::item:hover {
                background-color: #F0F0F0;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
                color: white;
            }
        """)
        results_layout.addWidget(self.results_list)
        main_content_layout.addWidget(results_container, 1)

        # Coluna de detalhes do membro e check-in
        checkin_details_container = QWidget()
        checkin_details_layout = QVBoxLayout(checkin_details_container)
        
        self.member_details_browser = QTextBrowser()
        self.member_details_browser.setHtml("<p style='color: #888888; text-align: center;'>Busque um membro para fazer o check-in.</p>")
        checkin_details_layout.addWidget(self.member_details_browser)

        self.confirm_button = QPushButton("Confirmar Check-in")
        self.confirm_button.setEnabled(False)
        self.confirm_button.setMinimumHeight(50)
        self.confirm_button.setStyleSheet("font-size: 18px; font-weight: bold;")
        checkin_details_layout.addWidget(self.confirm_button)
        
        main_content_layout.addWidget(checkin_details_container, 2)

        layout.addLayout(main_content_layout)
    
    def set_searching_state(self):
        """Define o estado de busca."""
        self.search_button.setText("Buscando...")
        self.search_button.setEnabled(False)
        self.results_list.clear()
        self.member_details_browser.clear()
        self.confirm_button.setEnabled(False)
        self.current_member_id = None
    
    def set_ready_state(self):
        """Define o estado pronto."""
        self.search_button.setText("Buscar")
        self.search_button.setEnabled(True)
    
    def populate_results(self, results: list):
        """Popula a lista de resultados."""
        self.results_list.clear()
        if not results:
            self.member_details_browser.setHtml("<p style='color: #FF6B6B; text-align: center;'>Nenhum membro encontrado.</p>")
        else:
            for result in results:
                item = QListWidgetItem(result['nome'])
                item.setData(Qt.ItemDataRole.UserRole, result.get('id'))
                self.results_list.addItem(item)
    
    def display_member_for_checkin(self, member_id: int, member_data: dict):
        """Exibe dados do membro para check-in."""
        self.current_member_id = member_id
        nome = member_data.get('nome', 'N/A')
        plano = member_data.get('plano', 'N/A')
        estado_plano = member_data.get('estado_plano', 'N/A')
        
        is_active = estado_plano.upper() == 'ATIVO'
        color = '#28a745' if is_active else '#FF6B6B'

        html = f"""
            <div style='padding: 10px; font-size: 16px;'>
                <p><b>Nome:</b> {nome}</p>
                <p><b>Plano:</b> {plano}</p>
                <p><b>Status:</b> <span style='color: {color}; font-weight: bold;'>{estado_plano}</span></p>
            </div>
        """
        self.member_details_browser.setHtml(html)
        
        self.confirm_button.setEnabled(is_active)
        if not is_active:
            self.confirm_button.setText("Plano Inativo")
        else:
            self.confirm_button.setText("Confirmar Check-in")
    
    def show_error(self):
        """Mostra erro ao carregar dados."""
        self.member_details_browser.setHtml("<p style='color: #FF6B6B; text-align: center;'>Erro ao carregar dados do membro.</p>")
        self.confirm_button.setEnabled(False)
        self.current_member_id = None
    
    def clear_after_checkin(self):
        """Limpa a tela após check-in bem-sucedido."""
        self.name_input.clear()
        self.results_list.clear()
        self.member_details_browser.clear()
        self.confirm_button.setEnabled(False)
        self.current_member_id = None
