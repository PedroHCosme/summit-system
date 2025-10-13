"""
Interface gráfica para o sistema de aniversariantes.
"""
import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextBrowser, QLabel, QLineEdit, QStackedWidget,
    QMenuBar, QListWidget, QListWidgetItem, QTabWidget, QMessageBox,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QAction

from config import CREDENTIALS_PATH, PLANOS_COM_VENCIMENTO
from styles import STYLESHEET
from aniversariantes_manager import AniversariantesManager
from html_formatter import HTMLFormatter
from member_search_service import MemberSearchService


class DataFetchWorker(QThread):
    """Thread para buscar dados sem travar a GUI."""
    
    # Sinais
    status_updated = pyqtSignal(str)
    fetch_completed = pyqtSignal(list, str)
    
    def __init__(self, manager):
        """
        Inicializa o worker.
        
        Args:
            manager: Instância do AniversariantesManager
        """
        super().__init__()
        self.manager = manager
    
    def run(self):
        """Executa a busca de dados."""
        # Busca aniversariantes
        self.status_updated.emit("Buscando aniversariantes...")
        
        aniversariantes = self.manager.get_aniversariantes_mes_atual()
        mes_nome = self.manager.get_nome_mes_atual()
        
        if not aniversariantes:
            self.status_updated.emit("Nenhum aniversariante encontrado.")
        else:
            self.status_updated.emit(f"{len(aniversariantes)} aniversariante(s) encontrado(s)!")
        
        self.fetch_completed.emit(aniversariantes, mes_nome)


class DatabaseConnectionWorker(QThread):
    """Thread para conexão inicial com a fonte de dados."""
    
    # Sinais
    status_updated = pyqtSignal(str)
    connection_completed = pyqtSignal(bool)
    
    def __init__(self):
        """Inicializa o worker."""
        super().__init__()
    
    def run(self):
        """Executa a conexão com a fonte de dados."""
        try:
            from data_provider import USE_SQLITE, get_provider
            
            if USE_SQLITE:
                self.status_updated.emit("Conectando ao banco de dados SQLite...")
            else:
                self.status_updated.emit("Verificando credenciais...")
                
                # Verifica credenciais
                if not os.path.exists(CREDENTIALS_PATH):
                    self.status_updated.emit("Erro: Arquivo de credenciais não encontrado.")
                    self.connection_completed.emit(False)
                    return
                
                self.status_updated.emit("Conectando ao Google Sheets...")
            
            # Tenta inicializar o provider
            provider = get_provider()
            
            self.status_updated.emit("Conexão estabelecida com sucesso!")
            self.connection_completed.emit(True)
            
        except Exception as e:
            self.status_updated.emit(f"Erro na conexão: {e}")
            self.connection_completed.emit(False)


class MemberSearchWorker(QThread):
    """Thread para buscar membros sem travar a GUI."""
    
    # Sinais
    status_updated = pyqtSignal(str)
    search_completed = pyqtSignal(list)  # Retorna lista de resultados
    
    def __init__(self, search_service, search_term):
        """
        Inicializa o worker.
        
        Args:
            search_service: Instância do MemberSearchService
            search_term: Termo de busca
        """
        super().__init__()
        self.search_service = search_service
        self.search_term = search_term
    
    def run(self):
        """Executa a busca de membro por nome."""
        self.status_updated.emit("Buscando...")
        
        # Busca por nome retorna lista de resultados
        results = self.search_service.search_by_name(self.search_term)
        if results:
            self.status_updated.emit(f"{len(results)} resultado(s) encontrado(s)!")
            self.search_completed.emit(results)
        else:
            self.status_updated.emit("Nenhum membro encontrado.")
            self.search_completed.emit([])


class DashboardWorker(QThread):
    """Thread para buscar dados do dashboard."""
    
    dashboard_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    def run(self):
        """Executa a busca de dados do dashboard."""
        try:
            from data_provider import get_checkins_today, get_last_checkins
            
            checkins_count = get_checkins_today()
            last_checkins = get_last_checkins(5)
            
            dashboard_data = {
                "checkins_today": checkins_count,
                "last_checkins": last_checkins
            }
            self.dashboard_updated.emit(dashboard_data)
            
        except Exception as e:
            self.error_occurred.emit(f"Erro ao atualizar dashboard: {e}")


class AniversariantesApp(QMainWindow):
    """Janela principal da aplicação."""
    
    def __init__(self):
        """Inicializa a aplicação."""
        super().__init__()
        
        # Serviços (agora usam data_provider)
        self.manager = AniversariantesManager()
        self.search_service = MemberSearchService()
        self.formatter = HTMLFormatter()
        self.worker = None
        self.is_connected = False  # Flag de conexão
        self.current_checkin_member_id = None # ID do membro para check-in
        
        self._setup_ui()
        self._auto_connect()

    def _auto_connect(self):
        """Inicia a conexão com o banco de dados automaticamente."""
        self.worker = DatabaseConnectionWorker()
        self.worker.status_updated.connect(self._on_connection_status_updated)
        self.worker.connection_completed.connect(self._on_connection_completed)
        self.worker.start()
    
    def _setup_ui(self):
        """Configura a interface do usuário."""
        # Configuração da janela
        self.setWindowTitle("Sistema de Gestão de Membros")
        self.setGeometry(100, 100, 800, 650)
        self.setStyleSheet(STYLESHEET)
        
        # Cria o menu (inicialmente desabilitado)
        self._create_menu()
        
        # Cria o stack widget para alternar entre telas
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Cria a tela de carregamento/conexão primeiro
        self._create_home_screen()
        
        # Cria as outras telas
        self._create_dashboard_screen()
        self._create_aniversariantes_screen()
        self._create_member_search_screen()
        self._create_checkin_screen()
        
        # Mostra a tela de conexão (índice 0)
        self.stacked_widget.setCurrentIndex(0)
    
    def _create_menu(self):
        """Cria o menu superior."""
        self.menubar = self.menuBar()
        
        # Menu Membros
        self.membros_menu = self.menubar.addMenu("Membros") if self.menubar else None
        if self.membros_menu:
            self.membros_menu.setEnabled(False)  # Desabilitado até conectar
        
            # Ação para o Dashboard
            dashboard_action = QAction("Dashboard", self)
            dashboard_action.triggered.connect(self._show_dashboard)
            self.membros_menu.addAction(dashboard_action)

            # Submenu Aniversariantes
            aniversariantes_action = QAction("Aniversariantes", self)
            aniversariantes_action.triggered.connect(self._show_aniversariantes)
            self.membros_menu.addAction(aniversariantes_action)
            
            # Submenu Buscar Membro
            buscar_action = QAction("Buscar Membro", self)
            buscar_action.triggered.connect(self._show_member_search)
            self.membros_menu.addAction(buscar_action)

            # Submenu Check-in
            checkin_action = QAction("Check-in", self)
            checkin_action.triggered.connect(self._show_checkin_screen)
            self.membros_menu.addAction(checkin_action)
    
    def _create_dashboard_screen(self):
        """Cria a tela do dashboard."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title_label = QLabel("Dashboard de Atividade")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Layout para as estatísticas
        stats_layout = QHBoxLayout()

        # Card para Check-ins Hoje
        checkins_today_card = self._create_stat_card("Check-ins Hoje", "0")
        self.checkins_today_label = checkins_today_card.findChild(QLabel, "stat_value")

        # Botão para ver detalhes dos check-ins
        self.view_checkins_button = QPushButton("Ver Detalhes")
        self.view_checkins_button.clicked.connect(self._show_checkins_today_details)
        
        # Adiciona o botão ao layout do card
        card_layout = checkins_today_card.layout()
        if card_layout:
            card_layout.addWidget(self.view_checkins_button)

        stats_layout.addWidget(checkins_today_card)
        layout.addLayout(stats_layout)

        # Lista de Últimos Check-ins
        last_checkins_label = QLabel("Últimos Check-ins")
        last_checkins_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(last_checkins_label)
        
        self.last_checkins_browser = QTextBrowser()
        self.last_checkins_browser.setMinimumHeight(150)
        layout.addWidget(self.last_checkins_browser)

        # Placeholder para o gráfico
        graph_label = QLabel("Gráfico de Frequência (Em breve)")
        graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        graph_label.setStyleSheet("font-size: 16px; color: #888;")
        layout.addWidget(graph_label)
        layout.addStretch()

        self.stacked_widget.addWidget(widget)

    def _show_checkins_today_details(self):
        """Mostra uma janela com os detalhes dos check-ins de hoje."""
        try:
            from data_provider import get_checkins_today_details
            from datetime import datetime

            checkins = get_checkins_today_details()

            if not checkins:
                QMessageBox.information(self, "Check-ins de Hoje", "Nenhum check-in registrado hoje.")
                return

            # Cria a janela de diálogo
            dialog = QDialog(self)
            dialog.setWindowTitle("Detalhes dos Check-ins de Hoje")
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Nome do Membro", "Plano", "Data", "Horário"])
            table.setRowCount(len(checkins))
            
            for row, checkin in enumerate(checkins):
                nome = checkin.get('nome', 'N/A')
                plano = checkin.get('plano', 'N/A')
                checkin_datetime_str = checkin.get('checkin_datetime')
                
                if checkin_datetime_str:
                    dt_obj = datetime.fromisoformat(checkin_datetime_str)
                    table.setItem(row, 2, QTableWidgetItem(dt_obj.strftime('%d/%m/%Y')))
                    table.setItem(row, 3, QTableWidgetItem(dt_obj.strftime('%H:%M:%S')))
                else:
                    table.setItem(row, 2, QTableWidgetItem('N/A'))
                    table.setItem(row, 3, QTableWidgetItem('N/A'))

                table.setItem(row, 0, QTableWidgetItem(nome))
                table.setItem(row, 1, QTableWidgetItem(plano))


            header = table.horizontalHeader()
            if header:
                header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Read-only
            
            layout.addWidget(table)
            
            close_button = QPushButton("Fechar")
            close_button.clicked.connect(dialog.close)
            layout.addWidget(close_button)
            
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar detalhes dos check-ins: {e}")

    def _create_stat_card(self, title: str, initial_value: str) -> QWidget:
        """Cria um card de estatística para o dashboard."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border: 1px solid #DDDDDD;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #555;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(initial_value)
        value_label.setObjectName("stat_value")
        value_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #007ACC;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        
        return card

    def _create_home_screen(self):
        """Cria a tela inicial (agora uma tela de carregamento)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.home_status_browser = QTextBrowser()
        self.home_status_browser.setHtml("<p style='text-align:center; font-size: 18px;'>Conectando ao banco de dados...</p>")
        self.home_status_browser.setMaximumHeight(100)
        self.home_status_browser.setStyleSheet("border: none;")
        
        layout.addWidget(self.home_status_browser)
        self.stacked_widget.addWidget(widget)

    def _create_aniversariantes_screen(self):
        """Cria a tela de aniversariantes."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Aniversariantes do Mês")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Informação do mês atual
        from utils import get_current_sheet_name
        mes_atual = get_current_sheet_name()
        self.aniver_mes_label = QLabel(f"Consultando aba: {mes_atual}")
        self.aniver_mes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Cor do texto de informação ajustada
        self.aniver_mes_label.setStyleSheet("font-size: 14px; color: #555555;")
        layout.addWidget(self.aniver_mes_label)
        
        # Área de resultados
        self.result_browser = QTextBrowser()
        self.result_browser.setOpenExternalLinks(True)
        self.result_browser.setHtml(self._get_initial_message())
        layout.addWidget(self.result_browser)
        
        # Botão de busca
        self.search_button = QPushButton("Buscar Aniversariantes")
        self.search_button.clicked.connect(self._on_search_clicked)
        layout.addWidget(self.search_button)
        
        self.stacked_widget.addWidget(widget)
    
    def _create_member_search_screen(self):
        """Cria a tela de busca de membros."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Buscar Membro")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Informação do mês atual
        from utils import get_current_sheet_name
        mes_atual = get_current_sheet_name()
        self.search_mes_label = QLabel(f"Consultando aba: {mes_atual}")
        self.search_mes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Cor do texto de informação ajustada
        self.search_mes_label.setStyleSheet("font-size: 14px; color: #555555;")
        layout.addWidget(self.search_mes_label)
        
        # Campo de busca
        search_layout = QHBoxLayout()
        
        # Campo de nome
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Digite o nome do membro...")
        self.name_input.returnPressed.connect(self._on_search_by_name)
        search_layout.addWidget(self.name_input)
        
        # Botão buscar por nome
        self.search_name_button = QPushButton("Buscar")
        self.search_name_button.clicked.connect(self._on_search_by_name)
        search_layout.addWidget(self.search_name_button)
        
        layout.addLayout(search_layout)
        
        # Container com duas colunas: lista de resultados e detalhes
        results_layout = QHBoxLayout()
        
        # Coluna esquerda: Lista de resultados
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        results_label = QLabel("Resultados:")
        # Cor do rótulo de resultados ajustada
        results_label.setStyleSheet("color: #007ACC; font-weight: bold; font-size: 14px;")
        left_layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        # Estilos da lista de resultados ajustados para tema claro
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
        self.results_list.itemClicked.connect(self._on_result_clicked)
        left_layout.addWidget(self.results_list)
        
        results_layout.addWidget(left_container, 1)
        
        # Coluna direita: Detalhes do membro com abas
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = QLabel("Detalhes:")
        # Cor do rótulo de detalhes ajustada
        details_label.setStyleSheet("color: #007ACC; font-weight: bold; font-size: 14px;")
        right_layout.addWidget(details_label)
        
        # Tab Widget para Informações e Histórico
        self.member_tabs = QTabWidget()
        # Estilos das abas ajustados para tema claro
        self.member_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                background: #FFFFFF;
            }
            QTabBar::tab {
                background: #E0E0E0;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #007ACC;
                color: white;
            }
            QTabBar::tab:hover {
                background: #D0D0D0;
            }
        """)
        
        # Aba 1: Informações do Membro
        self.member_result_browser = QTextBrowser()
        self.member_result_browser.setOpenExternalLinks(True)
        self.member_result_browser.setHtml(self._get_search_initial_message())
        self.member_tabs.addTab(self.member_result_browser, "Informações")
        
        # Aba 2: Histórico de Frequência
        self.member_history_browser = QTextBrowser()
        self.member_history_browser.setOpenExternalLinks(False)
        # Cor do texto de placeholder ajustada
        self.member_history_browser.setHtml("<p style='color: #888888;'>Selecione um membro para ver o histórico.</p>")
        self.member_tabs.addTab(self.member_history_browser, "Histórico de Frequência")
        
        right_layout.addWidget(self.member_tabs)
        
        results_layout.addWidget(right_container, 2)
        
        layout.addLayout(results_layout)
        
        self.stacked_widget.addWidget(widget)
    
    def _create_checkin_screen(self):
        """Cria a tela de check-in de membros."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title_label = QLabel("Check-in de Membro")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Campo de busca
        search_layout = QHBoxLayout()
        self.checkin_name_input = QLineEdit()
        self.checkin_name_input.setPlaceholderText("Digite o nome do membro para check-in...")
        self.checkin_name_input.returnPressed.connect(self._on_checkin_search_by_name)
        search_layout.addWidget(self.checkin_name_input)

        self.checkin_search_button = QPushButton("Buscar")
        self.checkin_search_button.clicked.connect(self._on_checkin_search_by_name)
        search_layout.addWidget(self.checkin_search_button)
        layout.addLayout(search_layout)

        # Layout para resultados e detalhes
        main_content_layout = QHBoxLayout()

        # Coluna de resultados da busca
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_label = QLabel("Resultados da Busca:")
        results_label.setStyleSheet("color: #007ACC; font-weight: bold; font-size: 14px;")
        results_layout.addWidget(results_label)
        self.checkin_results_list = QListWidget()
        self.checkin_results_list.setStyleSheet("""
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
        self.checkin_results_list.itemClicked.connect(self._on_checkin_result_clicked)
        results_layout.addWidget(self.checkin_results_list)
        main_content_layout.addWidget(results_container, 1)

        # Coluna de detalhes do membro e check-in
        checkin_details_container = QWidget()
        checkin_details_layout = QVBoxLayout(checkin_details_container)
        
        self.checkin_member_details_browser = QTextBrowser()
        self.checkin_member_details_browser.setHtml("<p style='color: #888888; text-align: center;'>Busque um membro para fazer o check-in.</p>")
        checkin_details_layout.addWidget(self.checkin_member_details_browser)

        self.confirm_checkin_button = QPushButton("Confirmar Check-in")
        self.confirm_checkin_button.setEnabled(False)
        self.confirm_checkin_button.setMinimumHeight(50)
        self.confirm_checkin_button.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.confirm_checkin_button.clicked.connect(self._on_confirm_checkin_clicked)
        checkin_details_layout.addWidget(self.confirm_checkin_button)
        
        main_content_layout.addWidget(checkin_details_container, 2)

        layout.addLayout(main_content_layout)
        self.stacked_widget.addWidget(widget)

    def _show_dashboard(self):
        """Mostra a tela do dashboard."""
        self.stacked_widget.setCurrentIndex(1)
        self._update_dashboard()

    def _show_aniversariantes(self):
        """Mostra a tela de aniversariantes."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(2)
    
    def _show_member_search(self):
        """Mostra a tela de busca de membros."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(3)
    
    def _show_checkin_screen(self):
        """Mostra a tela de check-in."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(4)

    def _on_connection_status_updated(self, status):
        """
        Manipula atualização de status da conexão.
        
        Args:
            status: Mensagem de status
        """
        self.home_status_browser.append(status)
    
    def _on_connection_completed(self, success):
        """
        Manipula a conclusão da conexão.
        
        Args:
            success: True se a conexão foi bem-sucedida
        """
        if success:
            self.is_connected = True
            if self.membros_menu:
                self.membros_menu.setEnabled(True)
            self._show_dashboard() # Vai para o dashboard
        else:
            self.home_status_browser.setHtml("""
                <p style="color: #FF6B6B; text-align: center; font-size: 16px;">
                    Falha na conexão. Verifique o console para mais detalhes.
                </p>
            """)

    def _update_dashboard(self):
        """Inicia a atualização dos dados do dashboard."""
        if not self.is_connected:
            return
        
        self.dashboard_worker = DashboardWorker(self.manager)
        self.dashboard_worker.dashboard_updated.connect(self._on_dashboard_updated)
        self.dashboard_worker.error_occurred.connect(self._on_dashboard_error)
        self.dashboard_worker.start()

    def _get_periodo_checkin(self, hour: int) -> str:
        """Retorna o período do dia com base na hora."""
        if 6 <= hour < 12:
            return "Manhã"
        elif 12 <= hour < 18:
            return "Tarde"
        elif 18 <= hour < 24:
            return "Noite"
        else:  # 00:00 - 05:59
            return "Pernoite"

    def _on_dashboard_updated(self, data):
        """Atualiza a UI do dashboard com novos dados."""
        self.checkins_today_label.setText(str(data.get("checkins_today", 0)))
        
        last_checkins = data.get("last_checkins", [])
        html = ""
        if not last_checkins:
            html = "<p style='color: #888;'>Nenhum check-in recente.</p>"
        else:
            from datetime import datetime
            html = "<ul style='list-style-type: none; padding-left: 0;'>"
            for checkin in last_checkins:
                nome = checkin.get('nome')
                dt_str = checkin.get('checkin_datetime')
                dt_obj = datetime.fromisoformat(dt_str)
                periodo = self._get_periodo_checkin(dt_obj.hour)
                html += f"<li style='margin-bottom: 5px;'><b>{nome}</b> - {periodo}</li>"
            html += "</ul>"
        self.last_checkins_browser.setHtml(html)

    def _on_dashboard_error(self, error_message):
        """Exibe um erro no dashboard."""
        self.last_checkins_browser.setHtml(f"<p style='color: #FF6B6B;'>{error_message}</p>")

    def _get_initial_message(self):
        """Retorna a mensagem inicial da tela de aniversariantes."""
        return """
            <div style="text-align: center; padding: 40px;">
                <h3 style="color: #007ACC;">Bem-vindo!</h3>
                <p style="color: #333333;">Clique no botão abaixo para buscar os aniversariantes do mês.</p>
            </div>
        """
    
    def _get_search_initial_message(self):
        """Retorna a mensagem inicial da tela de busca."""
        return """
            <div style="text-align: center; padding: 40px;">
                <h3 style="color: #007ACC;">Buscar Membro</h3>
                <p style="color: #333333;">Digite o nome do membro e clique em buscar.</p>
            </div>
        """
    
    def _on_search_by_name(self):
        """Manipula a busca por nome."""
        search_term = self.name_input.text().strip()
        
        if not search_term:
            self.member_result_browser.setHtml("""
                <div style="text-align: center; padding: 20px;">
                    <p style="color: #FF6B6B;">Por favor, digite um nome para buscar.</p>
                </div>
            """)
            return
        
        self._disable_search_buttons()
        self.results_list.clear()
        self.member_result_browser.clear()
        
        # Inicia worker
        self.worker = MemberSearchWorker(
            self.search_service, 
            search_term
        )
        self.worker.status_updated.connect(self._on_member_search_status_updated)
        self.worker.search_completed.connect(self._on_name_search_completed)
        self.worker.start()
    
    def _disable_search_buttons(self):
        """Desabilita o botão de busca de membro."""
        self.search_name_button.setText("Buscando...")
        self.search_name_button.setEnabled(False)
    
    def _enable_search_buttons(self):
        """Habilita o botão de busca de membro."""
        self.search_name_button.setText("Buscar")
        self.search_name_button.setEnabled(True)
    
    def _on_member_search_status_updated(self, status):
        """
        Manipula atualização de status da busca de membro.
        
        Args:
            status: Mensagem de status
        """
        # Exibe status temporariamente na área de detalhes
        pass
    
    def _on_name_search_completed(self, results):
        """
        Manipula a conclusão da busca por nome (múltiplos resultados).
        
        Args:
            results: Lista de dicionários com resultados
        """
        self.results_list.clear()
        
        if not results:
            self.member_result_browser.setHtml("""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #FF6B6B;">Nenhum membro encontrado</h3>
                    <p style="color: #555555;">Tente buscar com outros termos.</p>
                </div>
            """)
        else:
            # Adiciona resultados à lista
            for result in results:
                item = QListWidgetItem(result['nome'])
                # Armazenando o ID único do banco de dados!
                item.setData(Qt.ItemDataRole.UserRole, result.get('id', result.get('row_index', 0)))
                self.results_list.addItem(item)
            
            self.member_result_browser.setHtml(f"""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #007ACC;">{len(results)} resultado(s) encontrado(s)</h3>
                    <p style="color: #555555;">Clique em um nome na lista ao lado para ver os detalhes.</p>
                </div>
            """)
        
        self._enable_search_buttons()
    
    def _on_checkin_search_by_name(self):
        """Manipula a busca por nome na tela de check-in."""
        search_term = self.checkin_name_input.text().strip()
        if not search_term:
            return

        self.checkin_search_button.setText("Buscando...")
        self.checkin_search_button.setEnabled(False)
        self.checkin_results_list.clear()
        self.checkin_member_details_browser.clear()
        self.confirm_checkin_button.setEnabled(False)
        self.current_checkin_member_id = None

        # Reutiliza o MemberSearchWorker
        self.worker = MemberSearchWorker(self.search_service, search_term)
        self.worker.search_completed.connect(self._on_checkin_search_completed)
        self.worker.start()

    def _on_checkin_search_completed(self, results):
        """Manipula a conclusão da busca na tela de check-in."""
        self.checkin_results_list.clear()
        if not results:
            self.checkin_member_details_browser.setHtml("<p style='color: #FF6B6B; text-align: center;'>Nenhum membro encontrado.</p>")
        else:
            for result in results:
                item = QListWidgetItem(result['nome'])
                item.setData(Qt.ItemDataRole.UserRole, result.get('id'))
                self.checkin_results_list.addItem(item)
        
        self.checkin_search_button.setText("Buscar")
        self.checkin_search_button.setEnabled(True)

    def _on_result_clicked(self, item):
        """
        Manipula o clique em um resultado da lista.
        
        Args:
            item: QListWidgetItem clicado
        """
        member_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Busca os dados completos do membro por ID
        member_data = self.search_service.get_member_by_id(member_id)
        
        if member_data:
            html = self._format_member_data(member_data)
            self.member_result_browser.setHtml(html)
            
            # Carregar histórico de frequência
            self._load_member_history(member_id, member_data.get('nome', 'Membro'))
        else:
            self.member_result_browser.setHtml("""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #FF6B6B;">Erro ao carregar dados</h3>
                </div>
            """)
            self.member_history_browser.setHtml("""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #FF6B6B;">Erro ao carregar histórico</h3>
                </div>
            """)

    def _on_checkin_result_clicked(self, item):
        """Manipula o clique em um resultado na lista de check-in."""
        member_id = item.data(Qt.ItemDataRole.UserRole)
        member_data = self.search_service.get_member_by_id(member_id)

        if member_data:
            self.current_checkin_member_id = member_id
            nome = member_data.get('nome', 'N/A')
            plano = member_data.get('plano', 'N/A')
            estado_plano = member_data.get('estado_plano', 'N/A')
            
            color = '#28a745' if estado_plano.upper() == 'ATIVO' else '#FF6B6B'

            html = f"""
                <div style='padding: 10px; font-size: 16px;'>
                    <p><b>Nome:</b> {nome}</p>
                    <p><b>Plano:</b> {plano}</p>
                    <p><b>Status:</b> <span style='color: {color}; font-weight: bold;'>{estado_plano}</span></p>
                </div>
            """
            self.checkin_member_details_browser.setHtml(html)
            self.confirm_checkin_button.setEnabled(True)
        else:
            self.checkin_member_details_browser.setHtml("<p style='color: #FF6B6B; text-align: center;'>Erro ao carregar dados do membro.</p>")
            self.confirm_checkin_button.setEnabled(False)
            self.current_checkin_member_id = None

    def _on_confirm_checkin_clicked(self):
        """Confirma e registra o check-in do membro."""
        if self.current_checkin_member_id is None:
            return

        from data_provider import add_checkin
        from datetime import datetime

        try:
            checkin_id = add_checkin(self.current_checkin_member_id, datetime.now())
            if checkin_id:
                QMessageBox.information(self, "Check-in Realizado", "Check-in confirmado com sucesso!")
                # Limpar campos após sucesso
                self.checkin_name_input.clear()
                self.checkin_results_list.clear()
                self.checkin_member_details_browser.clear()
                self.confirm_checkin_button.setEnabled(False)
                self.current_checkin_member_id = None
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível registrar o check-in.")
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Ocorreu um erro inesperado: {e}")

    def _format_member_data(self, member_data):
        """
        Formata os dados do membro em HTML.
        Exibe: Nome, Plano, Vencimento do Plano (condicional), Estado do Plano, 
        Data de Nascimento, WhatsApp, Gênero, Frequência e Calçado.
        
        Args:
            member_data: Dicionário com os dados do membro
            
        Returns:
            String HTML formatada
        """
        # Define campos básicos
        fields = [
            ('nome', 'Nome'),
            ('plano', 'Plano'),
        ]
        
        # Adiciona vencimento do plano apenas se o plano estiver na lista
        plano = member_data.get('plano', '')
        if plano in PLANOS_COM_VENCIMENTO:
            fields.append(('vencimento_plano', 'Vencimento do Plano'))
        
        # Adiciona campos restantes
        fields.extend([
            ('estado_plano', 'Estado do Plano'),
            ('data_nascimento', 'Data de Nascimento'),
            ('whatsapp', 'WhatsApp'),
            ('genero', 'Gênero'),
            ('frequencia', 'Frequência'),
            ('calcado', 'Calçado')
        ])
        
        html = """
            <div style="padding: 20px;">
                <h2 style="color: #007ACC; text-align: center; margin-bottom: 20px;">Dados do Membro</h2>
                <div style="background-color: #F8F8F8; border: 1px solid #DDDDDD; border-radius: 8px; padding: 15px;">
        """
        
        for field_key, field_label in fields:
            value = member_data.get(field_key, '')
            if value:  # Só mostra se houver valor
                # Formatação especial para WhatsApp com link
                if field_key == 'whatsapp' and value:
                    # Remove formatação e adiciona link
                    digits = ''.join(filter(str.isdigit, value))
                    if len(digits) == 11:
                        whatsapp_link = f"https://wa.me/55{digits}"
                        html += f"""
                            <div style="margin-bottom: 10px;">
                                <strong style="color: #333333;">{field_label}:</strong>
                                <span style="color: #555555;"> {value}</span>
                                <a href="{whatsapp_link}" style="color: #007ACC; margin-left: 10px;">[Abrir WhatsApp]</a>
                            </div>
                        """
                    else:
                        html += f"""
                            <div style="margin-bottom: 10px;">
                                <strong style="color: #333333;">{field_label}:</strong>
                                <span style="color: #555555;"> {value}</span>
                            </div>
                        """
                # Destaque para estado do plano
                elif field_key == 'estado_plano':
                    color = '#28a745' if value.upper() == 'ATIVO' else '#FF6B6B'
                    html += f"""
                        <div style="margin-bottom: 10px;">
                            <strong style="color: #333333;">{field_label}:</strong>
                            <span style="color: {color}; font-weight: bold;"> {value}</span>
                        </div>
                    """
                else:
                    html += f"""
                        <div style="margin-bottom: 10px;">
                            <strong style="color: #333333;">{field_label}:</strong>
                            <span style="color: #555555;"> {value}</span>
                        </div>
                    """
            else:
                # Exibe campos vazios como "Não informado"
                html += f"""
                    <div style="margin-bottom: 10px;">
                        <strong style="color: #333333;">{field_label}:</strong>
                        <span style="color: #888888; font-style: italic;"> Não informado</span>
                    </div>
                """
        
        html += """
                </div>
            </div>
        """
        
        return html
    
    def _load_member_history(self, member_id: int, member_name: str):
        """
        Carrega e exibe o histórico de check-ins do membro.
        
        Args:
            member_id: ID do membro
            member_name: Nome do membro (para exibição)
        """
        try:
            # Importar data_provider aqui para evitar importação circular
            from data_provider import get_member_checkin_history
            
            history = get_member_checkin_history(member_id)
            
            if not history:
                self.member_history_browser.setHtml(f"""
                    <div style="padding: 20px;">
                        <h3 style="color: #007ACC;">Histórico de {member_name}</h3>
                        <p style="color: #888888; font-style: italic;">
                            Nenhum check-in registrado ainda.
                        </p>
                    </div>
                """)
                return
            
            # Formatar o histórico em HTML
            html = f"""
                <div style="padding: 20px; font-family: 'Segoe UI', Arial, sans-serif;">
                    <h3 style="color: #007ACC; margin-bottom: 15px;">
                        Histórico de Frequência: {member_name}
                    </h3>
                    <p style="color: #333333; margin-bottom: 20px;">
                        Total de check-ins: <strong style="color: #007ACC;">{len(history)}</strong>
                    </p>
                    <div style="max-height: 500px; overflow-y: auto;">
            """
            
            # Agrupar por mês/ano
            from datetime import datetime
            
            # Traduzir meses para português
            months_pt = {
                'January': 'Janeiro',
                'February': 'Fevereiro',
                'March': 'Março',
                'April': 'Abril',
                'May': 'Maio',
                'June': 'Junho',
                'July': 'Julho',
                'August': 'Agosto',
                'September': 'Setembro',
                'October': 'Outubro',
                'November': 'Novembro',
                'December': 'Dezembro'
            }
            
            grouped = {}
            for checkin in history:
                checkin_dt = datetime.fromisoformat(checkin['checkin_datetime'])
                month_name = checkin_dt.strftime('%B')
                month_pt = months_pt.get(month_name, month_name)
                month_year = f"{month_pt} de {checkin_dt.year}"
                
                if month_year not in grouped:
                    grouped[month_year] = []
                grouped[month_year].append(checkin_dt)
            
            # Exibir agrupado
            for month_year, dates in grouped.items():
                html += f"""
                    <div style="margin-bottom: 20px;">
                        <h4 style="color: #007ACC; margin-bottom: 10px;">{month_year}</h4>
                        <div style="margin-left: 15px;">
                """
                
                for dt in dates:
                    day_name = dt.strftime('%A')  # Nome do dia da semana
                    date_str = dt.strftime('%d/%m/%Y')
                    time_str = dt.strftime('%H:%M')
                    
                    # Traduzir dias da semana
                    days_pt = {
                        'Monday': 'Segunda-feira',
                        'Tuesday': 'Terça-feira',
                        'Wednesday': 'Quarta-feira',
                        'Thursday': 'Quinta-feira',
                        'Friday': 'Sexta-feira',
                        'Saturday': 'Sábado',
                        'Sunday': 'Domingo'
                    }
                    day_name_pt = days_pt.get(day_name, day_name)
                    
                    html += f"""
                        <div style="margin-bottom: 8px; padding: 8px; background: #F0F0F0; border-radius: 4px;">
                            <span style="color: #333333;">📅 {day_name_pt}</span>
                            <span style="color: #555555; margin-left: 10px;">{date_str}</span>
                            <span style="color: #007ACC; margin-left: 10px;">⏰ {time_str}</span>
                        </div>
                    """
                
                html += """
                        </div>
                    </div>
                """
            
            html += """
                    </div>
                </div>
            """
            
            self.member_history_browser.setHtml(html)
            
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            self.member_history_browser.setHtml(f"""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #FF6B6B;">Erro ao carregar histórico</h3>
                    <p style="color: #888;">{str(e)}</p>
                </div>
            """)
    
    def _on_search_clicked(self):
        """Manipula o clique no botão de busca."""
        self._disable_search_button()
        self.result_browser.clear()
        
        # Inicia worker
        self.worker = DataFetchWorker(self.manager)
        self.worker.status_updated.connect(self._on_status_updated)
        self.worker.fetch_completed.connect(self._on_fetch_completed)
        self.worker.start()
    
    def _disable_search_button(self):
        """Desabilita o botão de busca."""
        self.search_button.setText("Buscando...")
        self.search_button.setEnabled(False)
    
    def _enable_search_button(self):
        """Habilita o botão de busca."""
        self.search_button.setText("Buscar Aniversariantes")
        self.search_button.setEnabled(True)
    
    def _on_status_updated(self, status):
        """
        Manipula atualização de status.
        
        Args:
            status: Mensagem de status
        """
        self.result_browser.append(status)
    
    def _on_fetch_completed(self, aniversariantes, mes_nome):
        """
        Manipula a conclusão da busca.
        
        Args:
            aniversariantes: Lista de objetos Aniversariante
            mes_nome: Nome do mês
        """
        self.result_browser.clear()
        
        if not aniversariantes:
            html = self.formatter.format_no_results(mes_nome)
        else:
            html = self.formatter.format_header(mes_nome)
            html += f"<p style='color: #007ACC; text-align: center;'>Total: {len(aniversariantes)} aniversariante(s)</p>"
            
            for aniversariante in aniversariantes:
                html += self.formatter.format_aniversariante(aniversariante)
        
        self.result_browser.setHtml(html)
        self._enable_search_button()


def main():
    """Função principal."""
    print("Iniciando aplicação...")
    print(f"Diretório de trabalho: {os.getcwd()}")
    print(f"Arquivo de credenciais: {CREDENTIALS_PATH}")
    print(f"Credenciais encontradas: {os.path.exists(CREDENTIALS_PATH)}")
    
    app = QApplication(sys.argv)
    print("QApplication criada")
    
    window = AniversariantesApp()
    print("Janela criada")
    
    window.show()
    print("Janela exibida")
    print("A interface gráfica deve estar visível agora!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
