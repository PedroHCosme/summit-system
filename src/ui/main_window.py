"""Janela principal da aplicação."""

import sys
import webbrowser
from datetime import datetime
import os

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QMessageBox, QDialog, QInputDialog, QApplication,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

from src.core.aniversariantes_manager import AniversariantesManager
from src.ui.html_formatter import HTMLFormatter
from src.reports.finance_report import generate_finance_report
from src.reports.members_report import generate_members_report
from src.ui.styles import STYLESHEET

from src.ui.workers import (
    DataFetchWorker,
    DatabaseConnectionWorker,
    MemberSearchWorker,
    DashboardWorker
)
from src.ui.screens import (
    HomeScreen,
    DashboardScreen,
    AniversariantesScreen,
    MemberSearchScreen,
    CheckinScreen,
    FinancialScreen,
    FinancialScreen,
    MembersListScreen,
    PendingMembersScreen,
    PlansScreen,
    NotesScreen
)
from src.ui.dialogs import AddMemberDialog, SyncDialog, ExpiringPlansDialog
from src.ui.components import Sidebar
from src.ui.coordinators import (
    MembersCoordinator,
    CheckinCoordinator,
    ReportsCoordinator,
    SettingsCoordinator,
)


class MainWindow(QMainWindow):
    """Janela principal da aplicação."""
    
    def __init__(self):
        """Inicializa a aplicação."""
        super().__init__()
        
        # Serviços
        self.manager = AniversariantesManager()
        self.formatter = HTMLFormatter()
        self.worker = None
        self.is_connected = False
        self.members_coordinator = None
        self.checkin_coordinator = None
        self.reports_coordinator = None
        self.settings_coordinator = None
        
        # Timer para auto-atualização do dashboard
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self._update_dashboard)
        
        # Ordem importa: os coordinators precisam existir antes de _setup_ui,
        # que liga os sinais direto aos métodos deles (.connect resolve o
        # método no momento da conexão — coordinator None quebraria a montagem).
        self._setup_coordinators()
        self._setup_ui()
        self._auto_connect()

    def _setup_coordinators(self):
        """Inicializa coordenadores de domínio da UI."""
        self.members_coordinator = MembersCoordinator(self)
        self.checkin_coordinator = CheckinCoordinator(self)
        self.reports_coordinator = ReportsCoordinator(self)
        self.settings_coordinator = SettingsCoordinator(self)

    def _auto_connect(self):
        """Inicia a conexão com o banco de dados automaticamente."""
        self.worker = DatabaseConnectionWorker()
        self.worker.status_updated.connect(self._on_connection_status_updated)
        self.worker.connection_completed.connect(self._on_connection_completed)
        self.worker.start()
    
    def _setup_ui(self):
        """Configura a interface do usuário."""
        self.setWindowTitle("Summit Escalada")
        # Iniciar em modo Full Screen (solicitação do usuário para corrigir resolução em produção)
        self.showFullScreen()
        self.is_fullscreen = True
        self.setStyleSheet(STYLESHEET)
        
        # Esconde a barra de menu padrão do QMainWindow
        self.menuBar().hide()
        
        # Define o ícone da janela
        base_path = os.path.dirname(__file__)
        icon_path = os.path.join(base_path, "assets", "summit.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Container principal (Root) com layout VERTICAL para incluir a barra de título
        root_container = QWidget()
        root_layout = QVBoxLayout(root_container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # --- Barra de Título Customizada ---
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-bottom: 1px solid #333;
            }
            QLabel {
                color: #fff;
                font-weight: bold;
                padding-left: 15px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #fff;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333;
            }
            QPushButton#close_btn:hover {
                background-color: #e81123;
            }
        """)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        # Título / Logo
        title_label = QLabel("Summit Escalada")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Botões de controle
        # Minimizar
        btn_min = QPushButton("—")
        btn_min.setFixedSize(45, 40)
        btn_min.clicked.connect(self.showMinimized)
        title_layout.addWidget(btn_min)
        
        # Maximizar / Restaurar (Toggle)
        btn_max = QPushButton("❐")
        btn_max.setFixedSize(45, 40)
        btn_max.clicked.connect(self._toggle_maximize_restore)
        title_layout.addWidget(btn_max)
        
        # Fechar
        btn_close = QPushButton("✕")
        btn_close.setObjectName("close_btn")
        btn_close.setFixedSize(45, 40)
        btn_close.clicked.connect(self.close)
        title_layout.addWidget(btn_close)
        
        # Adiciona barra ao layout principal
        root_layout.addWidget(self.title_bar)
        
        # --- Área de Conteúdo (Sidebar + Telas) ---
        self.content_container = QWidget() # Tornar atributo para acesso no resizeEvent
        content_layout = QHBoxLayout(self.content_container)
        content_layout.setContentsMargins(60, 0, 0, 0) # Margem esquerda de 60px para a sidebar colapsada
        content_layout.setSpacing(0)
        
        # Sidebar (Flutuante - não adicionada ao layout)
        # Ela será posicionada manualmente no resizeEvent
        self.sidebar = Sidebar()
        self.sidebar.setParent(self.content_container)
        self.sidebar.set_enabled(False)
        self._connect_sidebar_signals()
        
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        # Adiciona contéudo ao root
        root_layout.addWidget(self.content_container)
        
        # Define widget central
        self.setCentralWidget(root_container)


        
        # Cria as telas
        self.home_screen = HomeScreen()
        self.dashboard_screen = DashboardScreen()
        self.aniversariantes_screen = AniversariantesScreen()
        self.member_search_screen = MemberSearchScreen()
        self.checkin_screen = CheckinScreen()
        self.financial_screen = FinancialScreen()
        self.members_list_screen = MembersListScreen()
        self.pending_members_screen = PendingMembersScreen()
        self.plans_screen = PlansScreen()
        
        # Adiciona ao stack
        self.stacked_widget.addWidget(self.home_screen)  # 0
        self.stacked_widget.addWidget(self.dashboard_screen)  # 1
        self.stacked_widget.addWidget(self.aniversariantes_screen)  # 2
        self.stacked_widget.addWidget(self.member_search_screen)  # 3
        self.stacked_widget.addWidget(self.checkin_screen)  # 4
        self.stacked_widget.addWidget(self.financial_screen)  # 5
        self.stacked_widget.addWidget(self.members_list_screen)  # 6
        self.stacked_widget.addWidget(self.pending_members_screen)  # 7
        self.stacked_widget.addWidget(self.plans_screen)  # 8

        self.notes_screen = NotesScreen()
        self.stacked_widget.addWidget(self.notes_screen)  # 9
        
        # Conecta botões específicos
        self.dashboard_screen.refresh_button.clicked.connect(self._update_dashboard)
        
        # Conecta sinais das telas
        self._connect_screen_signals()

        
        # Mostra a tela de conexão
        self.stacked_widget.setCurrentIndex(0)
    
    def _toggle_maximize_restore(self):
        """Alterna entre tela cheia e modo janela (800x600)."""
        if self.isFullScreen():
            self.showNormal()
            self.resize(800, 600)
            self._center_window()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True
            
    def _center_window(self):
        screen = self.screen()
        frame_geo = self.frameGeometry()
        center_point = screen.availableGeometry().center()
        frame_geo.moveCenter(center_point)
        self.move(frame_geo.topLeft())
    
    def _connect_sidebar_signals(self):
        """Conecta os sinais da sidebar aos métodos de navegação."""
        from src.ui.components.sidebar import SidebarContext
        
        # === Menu Principal (HOME) ===
        self.sidebar.home_clicked.connect(self._on_home_clicked)
        self.sidebar.checkin_clicked.connect(self._on_checkin_section_clicked)
        self.sidebar.members_clicked.connect(self._on_members_section_clicked)
        self.sidebar.financial_clicked.connect(self._on_financial_section_clicked)
        self.sidebar.settings_clicked.connect(self._on_settings_section_clicked)
        
        # === Submenu Membros ===
        self.sidebar.members_list_clicked.connect(self._show_members_list_only)
        self.sidebar.members_search_clicked.connect(self._show_member_search)
        self.sidebar.members_add_clicked.connect(self.members_coordinator.show_add_member_dialog)
        self.sidebar.members_pending_clicked.connect(self._show_pending_members_only)
        self.sidebar.members_birthday_clicked.connect(self._show_aniversariantes)
        
        # === Submenu Check-in ===
        self.sidebar.checkin_register_clicked.connect(self._show_checkin_screen_only)
        
        # === Submenu Financeiro ===
        self.sidebar.financial_overview_clicked.connect(self._show_financial_screen_only)
        self.sidebar.financial_plans_clicked.connect(self.settings_coordinator.show_manage_plans)
        self.sidebar.financial_expiring_clicked.connect(self.settings_coordinator.show_expiring_plans_dialog)

        # === Submenu Configurações ===
        self.sidebar.settings_plans_clicked.connect(self.settings_coordinator.show_manage_plans)
        self.sidebar.settings_backup_clicked.connect(self.settings_coordinator.create_database_backup)
        self.sidebar.settings_sync_clicked.connect(self.settings_coordinator.show_sync_dialog)

        # === Submenu Relatórios ===
        self.sidebar.reports_clicked.connect(self._on_reports_section_clicked)
        self.sidebar.reports_members_clicked.connect(self.reports_coordinator.generate_members_report)
        self.sidebar.reports_financial_clicked.connect(self.reports_coordinator.generate_financial_report)

        # === Bloco de Notas ===
        self.sidebar.notes_clicked.connect(self._show_notes_screen)
    
    def _on_home_clicked(self):
        """Volta para o Dashboard e menu principal."""
        from src.ui.components.sidebar import SidebarContext
        self.sidebar.set_context(SidebarContext.HOME)
        self.sidebar.set_active(0)
        self._show_dashboard()
    
    def _on_members_section_clicked(self):
        """Entra na seção Membros."""
        from src.ui.components.sidebar import SidebarContext
        self.sidebar.set_context(SidebarContext.MEMBERS)
        self.sidebar.set_active(1)  # Lista de Membros
        self._show_members_list_only()
    
    def _on_checkin_section_clicked(self):
        """Entra na seção Check-in."""
        from src.ui.components.sidebar import SidebarContext
        self.sidebar.set_context(SidebarContext.CHECKIN)
        self.sidebar.set_active(1)  # Registrar Check-in
        self._show_checkin_screen_only()
    
    def _on_financial_section_clicked(self):
        """Entra na seção Financeiro."""
        from src.ui.components.sidebar import SidebarContext
        self.sidebar.set_context(SidebarContext.FINANCIAL)
        self.sidebar.set_active(1)  # Visão Geral
        self._show_financial_screen_only()
    
    def _on_settings_section_clicked(self):
        """Entra na seção Configurações."""
        from src.ui.components.sidebar import SidebarContext
        self.sidebar.set_context(SidebarContext.SETTINGS)

    def _on_reports_section_clicked(self):
        """Entra na seção Relatórios."""
        from src.ui.components.sidebar import SidebarContext
        self.sidebar.set_context(SidebarContext.REPORTS)

    def _show_notes_screen(self):
        """Abre a tela do Bloco de Notas."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(9)
        self.notes_screen.refresh()

    # === Métodos de navegação sem troca de contexto ===
    def _show_members_list_only(self):
        """Mostra lista de membros sem trocar contexto."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(6)
        self.members_coordinator.load_members_list()
    
    def _show_pending_members_only(self):
        """Mostra pendentes sem trocar contexto."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(7)
        self.pending_members_screen.refresh_list()
    
    def _show_checkin_screen_only(self):
        """Mostra check-in sem trocar contexto."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(4)
    
    def _show_financial_screen_only(self):
        """Mostra financeiro sem trocar contexto."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(5)
        self._load_financial_data()
    

    
    def _connect_screen_signals(self):
        """Conecta sinais das telas."""
        # Dashboard
        self.dashboard_screen.view_checkins_button.clicked.connect(
            self.dashboard_screen.show_checkins_details
        )
        self.dashboard_screen.member_clicked.connect(
            self.members_coordinator.on_dashboard_member_clicked
        )
        
        # Aniversariantes
        self.aniversariantes_screen.search_button.clicked.connect(
            self._on_aniversariantes_search_clicked
        )
        
        # Busca de Membros
        self.member_search_screen.name_input.returnPressed.connect(
            self.members_coordinator.on_member_search_by_name
        )
        self.member_search_screen.search_button.clicked.connect(
            self.members_coordinator.on_member_search_by_name
        )
        self.member_search_screen.results_list.itemClicked.connect(
            self.members_coordinator.on_member_result_clicked
        )
        self.member_search_screen.edit_button.clicked.connect(
            self.members_coordinator.on_edit_member_clicked
        )
        self.member_search_screen.renew_button.clicked.connect(
            self.members_coordinator.on_renew_plan_clicked
        )
        self.member_search_screen.delete_button.clicked.connect(
            self.members_coordinator.on_delete_member_clicked
        )
        self.member_search_screen.whatsapp_requested.connect(
            self.members_coordinator.on_whatsapp_clicked
        )
        self.member_search_screen.quick_payment_requested.connect(
            self.members_coordinator.on_quick_payment_clicked
        )
        self.member_search_screen.history_requested.connect(
            self.members_coordinator.on_history_shortcut_clicked
        )
        # Substituir o método request_delete_checkin por nossa implementação
        self.member_search_screen.request_delete_checkin = self.members_coordinator.on_delete_checkin_requested
        # Substituir o método request_edit_checkin por nossa implementação
        self.member_search_screen.request_edit_checkin = self.members_coordinator.on_edit_checkin_requested

        # Lista de Membros
        self.members_list_screen.refresh_requested.connect(self.members_coordinator.on_members_list_refresh)
        self.members_list_screen.member_selected.connect(self.members_coordinator.on_members_list_member_selected)
        # Conectar sinais da lista de membros
        self.members_list_screen.edit_requested.connect(self.members_coordinator.on_list_edit_member_clicked)
        self.members_list_screen.renew_requested.connect(self.members_coordinator.on_list_renew_plan_clicked)
        self.members_list_screen.delete_requested.connect(self.members_coordinator.on_list_delete_member_clicked)
        self.members_list_screen.whatsapp_requested.connect(
            self.members_coordinator.on_list_whatsapp_clicked
        )
        self.members_list_screen.quick_payment_requested.connect(
            self.members_coordinator.on_list_quick_payment_clicked
        )
        self.members_list_screen.history_requested.connect(
            self.members_coordinator.on_list_history_shortcut_clicked
        )

        # Check-in
        self.checkin_screen.name_input.returnPressed.connect(
            self.checkin_coordinator.on_checkin_search_by_name
        )
        self.checkin_screen.search_button.clicked.connect(
            self.checkin_coordinator.on_checkin_search_by_name
        )
        self.checkin_screen.results_list.itemClicked.connect(
            self.checkin_coordinator.on_checkin_result_clicked
        )
        self.checkin_screen.confirm_button.clicked.connect(
            self.checkin_coordinator.on_confirm_checkin_clicked
        )
        self.checkin_screen.profile_button.clicked.connect(
            self.checkin_coordinator.on_checkin_profile_clicked
        )
        
        # Financeiro
        self.financial_screen.update_button.clicked.connect(
            self._load_financial_data
        )
        self.financial_screen.plan_chart_button.clicked.connect(
            self._show_plan_distribution_dialog
        )
    
    # === Navegação entre telas ===
    
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
    
    def _show_members_list(self):
        """Mostra a tela de lista de membros."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(6)
        self.members_coordinator.load_members_list()

    def _show_pending_members(self):
        """Mostra a tela de aprovação de membros."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(7)
        self.pending_members_screen.refresh_list()
    
    def _show_checkin_screen(self):
        """Mostra a tela de check-in."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(4)
    
    def _show_financial_screen(self):
        """Mostra a tela de gestão financeira."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(5)
        self._load_financial_data()
    
    def _show_settings_menu(self):
        """Mostra menu de configurações como popup."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QCursor
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #3c3f41;
                color: #ecf0f1;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 30px 10px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #E67E22;
                color: #2b2d30;
            }
        """)
        
        # Opções de configurações
        plans_action = menu.addAction("💳 Gerenciar Planos")
        plans_action.triggered.connect(self.settings_coordinator.show_manage_plans)

        menu.addSeparator()

        backup_action = menu.addAction("💾 Backup do Banco")
        backup_action.triggered.connect(self.settings_coordinator.create_database_backup)

        sync_action = menu.addAction("🔄 Sincronizar Sheets")
        sync_action.triggered.connect(self.settings_coordinator.show_sync_dialog)

        menu.addSeparator()

        add_member_action = menu.addAction("➕ Novo Membro")
        add_member_action.triggered.connect(self.members_coordinator.show_add_member_dialog)
        
        # Mostra o menu na posição do cursor
        menu.exec(QCursor.pos())
    
    # === Handlers de Conexão ===
    
    def _on_connection_status_updated(self, status):
        """Manipula atualização de status da conexão."""
        self.home_screen.append_status(status)
    
    def _on_connection_completed(self, success):
        """Manipula a conclusão da conexão."""
        if success:
            self.is_connected = True
            
            # Executa migrações do banco de dados
            self._run_migrations()
            
            # Habilita a sidebar
            self.sidebar.set_enabled(True)
            self.sidebar.set_active(0)  # Dashboard é o primeiro item
            
            if hasattr(self, 'gestao_menu') and self.gestao_menu:
                self.gestao_menu.setEnabled(True)
            if hasattr(self, 'atividade_menu') and self.atividade_menu:
                self.atividade_menu.setEnabled(True)
            if hasattr(self, 'tools_menu') and self.tools_menu:
                self.tools_menu.setEnabled(True)
            
            self._show_dashboard()
            
            # Inicia o timer de atualização (a cada 5 segundos)
            self.dashboard_timer.start(5000)
        else:
            self.home_screen.set_error("Falha na conexão. Verifique o console para mais detalhes.")
    
    def _run_migrations(self):
        """Executa as migrações do banco de dados via Alembic."""
        try:
            import os
            from alembic import command
            from alembic.config import Config
            
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            alembic_ini_path = os.path.join(project_dir, "alembic.ini")
            
            alembic_cfg = Config(alembic_ini_path)
            alembic_cfg.set_main_option("script_location", os.path.join(project_dir, "alembic_migrations"))
            
            command.upgrade(alembic_cfg, "head")
            print("✓ Migrações do banco de dados (Alembic) executadas com sucesso")
        except Exception as e:
            print(f"⚠ Erro ao executar migrações Alembic: {e}")
            # Não bloqueia a aplicação se houver erro nas migrações
    
    # === Dashboard ===
    
    def _update_dashboard(self):
        """Inicia a atualização dos dados do dashboard."""
        if not self.is_connected:
            return
        
        self.dashboard_worker = DashboardWorker(self.manager)
        self.dashboard_worker.dashboard_updated.connect(self.dashboard_screen.update_dashboard)
        self.dashboard_worker.error_occurred.connect(self.dashboard_screen.show_error)
        self.dashboard_worker.start()
    
    # === Aniversariantes ===
    
    def _on_aniversariantes_search_clicked(self):
        """Manipula o clique no botão de busca de aniversariantes."""
        self.aniversariantes_screen.set_searching_state()
        
        # Obtém o mês selecionado
        mes_selecionado = self.aniversariantes_screen.get_selected_month()
        
        self.worker = DataFetchWorker(self.manager, mes_selecionado)
        self.worker.status_updated.connect(self.aniversariantes_screen.append_status)
        self.worker.fetch_completed.connect(self._on_aniversariantes_fetch_completed)
        self.worker.start()
    
    def _on_aniversariantes_fetch_completed(self, aniversariantes, mes_nome):
        """Manipula a conclusão da busca de aniversariantes."""
        if not aniversariantes:
            html = self.formatter.format_no_results(mes_nome)
        else:
            html = self.formatter.format_header(mes_nome)
            html += f"<p style='color: #007ACC; text-align: center;'>Total: {len(aniversariantes)} aniversariante(s)</p>"
            
            for aniversariante in aniversariantes:
                html += self.formatter.format_aniversariante(aniversariante)
        
        self.aniversariantes_screen.set_results(html)
        self.aniversariantes_screen.set_ready_state()
    
    # === Financeiro ===
    
    def _load_financial_data(self):
        """Carrega os dados financeiros com base no período selecionado rodando em background."""
        try:
            # Mostra estado de carregamento
            self.financial_screen.show_loading()
            
            # Obter datas
            start_date = self.financial_screen.start_date_input.date().toPyDate()
            end_date = self.financial_screen.end_date_input.date().toPyDate()
            
            # Converter para datetime com hora mínima/máxima
            from datetime import datetime, time
            start_datetime = datetime.combine(start_date, time.min)
            end_datetime = datetime.combine(end_date, time.max)
            
            # Instanciar e iniciar Worker para não travar a UI
            from src.ui.workers.financial_worker import FinancialDataWorker
            
            # Desativar botões ou evitar múltiplas requisições se necessário aqui
            self._financial_worker = FinancialDataWorker(
                self.manager.data_provider, 
                start_datetime, 
                end_datetime
            )
            
            self._financial_worker.data_loaded.connect(self._on_financial_data_loaded)
            self._financial_worker.error_occurred.connect(self._on_financial_data_error)
            
            # Iniciar thread
            self._financial_worker.start()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao iniciar carregamento financeiro: {str(e)}"
            )
            
    def _on_financial_data_loaded(self, result: dict):
        """Callback invocado quando o worker financeiro conclui com sucesso."""
        try:
            summary = result.get('summary', {})
            # Atualizar cards de resumo
            self.financial_screen.update_summary(
                summary.get('total_receita', 0.0),
                summary.get('total_transacoes', 0),
                summary.get('ticket_medio', 0.0)
            )
            
            breakdown = result.get('breakdown', {})
            self.financial_screen.update_breakdown(breakdown)
            
            transactions = result.get('transactions', [])
            self.financial_screen.update_transactions(transactions)
            
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Erro processando os dados financeiros: {str(e)}")
            
    def _on_financial_data_error(self, error_msg: str):
        """Callback invocado quando o worker financeiro encontra erro."""
        QMessageBox.critical(
            self,
            "Erro de Banco de Dados",
            f"Falha gravíssima ao carregar as métricas financeiras:\n\n{error_msg}"
        )
    def _show_plan_distribution_dialog(self):
        """Abre o diálogo de gráficos financeiros."""
        from src.ui.dialogs.finance_graphs import FinancialGraphsDialog
        
        dialog = FinancialGraphsDialog(self)
        dialog.exec()
    
    def resizeEvent(self, event):
        """Atualiza geometria da sidebar flutuante ao redimensionar a janela."""
        super().resizeEvent(event)
        if hasattr(self, 'sidebar') and hasattr(self, 'content_container'):
            # Sidebar ocupa toda a altura do container de conteúdo
            container_height = self.content_container.height()
            self.sidebar.setFixedHeight(container_height)
            self.sidebar.move(0, 0)
            self.sidebar.raise_()

def main():
    """Função principal."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    
    print("Iniciando aplicação...")
    
    # FIX: Desabilitar escala automática de High DPI (Linux Mint / 1024x768)
    # Isso é crítico para evitar que a interface fique GIGANTE em telas de baixa resolução
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "0.9"  # Reduzindo para 90% do tamanho original
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_FONT_DPI"] = "96"
    
    app = QApplication(sys.argv)
    print("QApplication criada")
    
    # Define fonte global ultra-compacta com tamanha em PIXELS
    # Segoe UI tamanho 12px (padrão solicitado)
    font = QFont("Segoe UI")
    font.setPixelSize(12)
    app.setFont(font)
    
    # Aplicar estilo globalmente para todos os widgets, incluindo diálogos
    app.setStyleSheet(STYLESHEET)
    print("Estilo global aplicado")
    
    window = MainWindow()
    print("Janela criada")
    
    window.show()
    print("Janela exibida")
    print("A interface gráfica deve estar visível agora!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
