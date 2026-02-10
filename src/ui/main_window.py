"""Janela principal da aplicação."""

import sys
import webbrowser
from datetime import datetime
import os

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QMessageBox, QDialog, QInputDialog, QApplication,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QTimer

from src.core.aniversariantes_manager import AniversariantesManager
from src.ui.html_formatter import HTMLFormatter
from src.core.member_search_service import MemberSearchService
from src.reports.finance_report import generate_finance_report
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
    PlansScreen
)
from src.ui.dialogs import AddMemberDialog, SyncDialog, ManagePlansDialog, ExpiringPlansDialog
from src.ui.components import Sidebar


class MainWindow(QMainWindow):
    """Janela principal da aplicação."""
    
    def __init__(self):
        """Inicializa a aplicação."""
        super().__init__()
        
        # Serviços
        self.manager = AniversariantesManager()
        self.search_service = MemberSearchService()
        self.formatter = HTMLFormatter()
        self.worker = None
        self.is_connected = False
        
        # Timer para auto-atualização do dashboard
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self._update_dashboard)
        
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
        self.setWindowTitle("Summit Escalada - Mission Control")
        # Iniciar com resolução pequena (640x360) e centralizado
        self.resize(640, 360)
        self._center_window()
        self.is_fullscreen = False  # Começa em modo janela
        self.setStyleSheet(STYLESHEET)
        
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
        title_label = QLabel("Summit Escalada - Mission Control")
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
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Adiciona sidebar e stack ao layout de conteúdo
        self.sidebar = Sidebar()
        self.sidebar.set_enabled(False)
        self._connect_sidebar_signals()
        content_layout.addWidget(self.sidebar)
        
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        # Adiciona contéudo ao root
        root_layout.addWidget(content_container)
        
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
        
        # Conecta botões específicos
        self.dashboard_screen.refresh_button.clicked.connect(self._update_dashboard)
        
        # Conecta sinais das telas
        self._connect_screen_signals()
        
        # Cria menu (mantido como backup para atalhos e ações avançadas)
        self._create_menu()
        
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
        self.sidebar.members_add_clicked.connect(self._show_add_member_dialog)
        self.sidebar.members_pending_clicked.connect(self._show_pending_members_only)
        self.sidebar.members_birthday_clicked.connect(self._show_aniversariantes)
        
        # === Submenu Check-in ===
        self.sidebar.checkin_register_clicked.connect(self._show_checkin_screen_only)
        
        # === Submenu Financeiro ===
        self.sidebar.financial_overview_clicked.connect(self._show_financial_screen_only)
        self.sidebar.financial_plans_clicked.connect(self._show_manage_plans_dialog)
        self.sidebar.financial_expiring_clicked.connect(self._show_expiring_plans_dialog)
        
        # === Submenu Configurações ===
        self.sidebar.settings_plans_clicked.connect(self._show_manage_plans_dialog)
        self.sidebar.settings_backup_clicked.connect(self._create_database_backup)
        self.sidebar.settings_sync_clicked.connect(self._show_sync_dialog)
    
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
    
    # === Métodos de navegação sem troca de contexto ===
    def _show_members_list_only(self):
        """Mostra lista de membros sem trocar contexto."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(6)
        self._load_members_list()
    
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
    
    def _create_menu(self):
        """Cria o menu superior."""
        self.menubar = self.menuBar()
        if not self.menubar:
            return

        # Menu Gestão
        self.gestao_menu = self.menubar.addMenu("📋 Gestão")
        if self.gestao_menu:
            self.gestao_menu.setEnabled(False)

            # === SUBMENU: Membros ===
            membros_menu = self.gestao_menu.addMenu("👥 Membros")
            
            add_member_action = QAction("➕ Adicionar Membro", self)
            add_member_action.setShortcut("Ctrl+N")
            add_member_action.triggered.connect(self._show_add_member_dialog)
            membros_menu.addAction(add_member_action)

            list_members_action = QAction("📋 Lista de Membros", self)
            list_members_action.setShortcut("Ctrl+L")
            list_members_action.triggered.connect(self._show_members_list)
            membros_menu.addAction(list_members_action)

            buscar_action = QAction("🔍 Buscar Membro", self)
            buscar_action.setShortcut("Ctrl+F")
            buscar_action.triggered.connect(self._show_member_search)
            buscar_action.triggered.connect(self._show_member_search)
            membros_menu.addAction(buscar_action)

            pending_members_action = QAction("⏳ Aprovar Novos Membros", self)
            pending_members_action.triggered.connect(self._show_pending_members)
            membros_menu.addAction(pending_members_action)

            aniversariantes_action = QAction("🎂 Aniversariantes do Mês", self)
            aniversariantes_action.triggered.connect(self._show_aniversariantes)
            membros_menu.addAction(aniversariantes_action)
            
            membros_menu.addSeparator()
            
            # Placeholder para ações em lote (futuro)
            bulk_action = QAction("⚡ Ações em Lote...", self)
            bulk_action.setEnabled(False)  # Desabilitado por enquanto
            bulk_action.setToolTip("Em breve: renovação em lote, mudança de status, etc.")
            membros_menu.addAction(bulk_action)
            
            # === SUBMENU: Planos ===
            planos_menu = self.gestao_menu.addMenu("💳 Planos")
            
            manage_plans_action = QAction("⚙️ Gerenciar Planos e Preços", self)
            manage_plans_action.triggered.connect(self._show_manage_plans_dialog)
            planos_menu.addAction(manage_plans_action)
            
            plan_distribution_action = QAction("📊 Distribuição de Planos", self)
            plan_distribution_action.triggered.connect(self._show_plan_distribution_dialog)
            planos_menu.addAction(plan_distribution_action)
            
            planos_menu.addSeparator()
            
            expiring_plans_action = QAction("⏰ Planos a Vencer", self)
            expiring_plans_action.triggered.connect(self._show_expiring_plans_dialog)
            expiring_plans_action.setToolTip("Visualizar planos com vencimento próximo")
            planos_menu.addAction(expiring_plans_action)
            
            # === SUBMENU: Pagamentos ===
            pagamentos_menu = self.gestao_menu.addMenu("💰 Pagamentos")
            
            financial_action = QAction("📈 Visão Financeira", self)
            financial_action.setShortcut("Ctrl+$")
            financial_action.triggered.connect(self._show_financial_screen)
            pagamentos_menu.addAction(financial_action)
            
            pagamentos_menu.addSeparator()
            
            # Placeholder para relatórios (futuro)
            export_financial_action = QAction("📄 Exportar Relatório Financeiro", self)
            export_financial_action.triggered.connect(self._generate_financial_report)
            export_financial_action.setToolTip("Gera um relatório financeiro detalhado em HTML")
            pagamentos_menu.addAction(export_financial_action)
            
            # === SUBMENU: Relatórios ===
            relatorios_menu = self.gestao_menu.addMenu("📊 Relatórios")
            
            freq_report_action = QAction("📅 Relatório de Frequência", self)
            freq_report_action.triggered.connect(self._generate_frequency_report)
            relatorios_menu.addAction(freq_report_action)
            
            member_report_action = QAction("👤 Relatório de Membros", self)
            member_report_action.triggered.connect(self._generate_members_report)
            relatorios_menu.addAction(member_report_action)
            
            # === SEPARADOR ===
            self.gestao_menu.addSeparator()
            
            # === SUBMENU: Banco de Dados ===
            database_menu = self.gestao_menu.addMenu("🗄️ Banco de Dados")
            
            backup_action = QAction("💾 Backup do Banco", self)
            backup_action.triggered.connect(self._create_database_backup)
            database_menu.addAction(backup_action)

        # Menu Atividade
        self.atividade_menu = self.menubar.addMenu("Atividade")
        if self.atividade_menu:
            self.atividade_menu.setEnabled(False)

            dashboard_action = QAction("Dashboard", self)
            dashboard_action.triggered.connect(self._show_dashboard)
            self.atividade_menu.addAction(dashboard_action)

            checkin_action = QAction("Check-in", self)
            checkin_action.triggered.connect(self._show_checkin_screen)
            self.atividade_menu.addAction(checkin_action)
            
            financeiro_action = QAction("Financeiro", self)
            financeiro_action.triggered.connect(self._show_financial_screen)
            self.atividade_menu.addAction(financeiro_action)
        
        # Menu Ferramentas
        self.tools_menu = self.menubar.addMenu("Ferramentas")
        if self.tools_menu:
            self.tools_menu.setEnabled(False)
            
            sync_action = QAction("🔄 Sincronizar com Google Sheets", self)
            sync_action.triggered.connect(self._show_sync_dialog)
            self.tools_menu.addAction(sync_action)
    
    def _connect_screen_signals(self):
        """Conecta sinais das telas."""
        # Dashboard
        self.dashboard_screen.view_checkins_button.clicked.connect(
            self.dashboard_screen.show_checkins_details
        )
        self.dashboard_screen.member_clicked.connect(
            self._on_dashboard_member_clicked
        )
        
        # Aniversariantes
        self.aniversariantes_screen.search_button.clicked.connect(
            self._on_aniversariantes_search_clicked
        )
        
        # Busca de Membros
        self.member_search_screen.name_input.returnPressed.connect(
            self._on_member_search_by_name
        )
        self.member_search_screen.search_button.clicked.connect(
            self._on_member_search_by_name
        )
        self.member_search_screen.results_list.itemClicked.connect(
            self._on_member_result_clicked
        )
        self.member_search_screen.edit_button.clicked.connect(
            self._on_edit_member_clicked
        )
        self.member_search_screen.renew_button.clicked.connect(
            self._on_renew_plan_clicked
        )
        self.member_search_screen.delete_button.clicked.connect(
            self._on_delete_member_clicked
        )
        # Substituir o método request_delete_checkin por nossa implementação
        self.member_search_screen.request_delete_checkin = self._on_delete_checkin_requested
        # Substituir o método request_edit_checkin por nossa implementação
        self.member_search_screen.request_edit_checkin = self._on_edit_checkin_requested
        
        # Lista de Membros
        self.members_list_screen.refresh_requested.connect(self._on_members_list_refresh)
        self.members_list_screen.member_selected.connect(self._on_members_list_member_selected)
        # Conectar sinais da lista de membros
        self.members_list_screen.edit_requested.connect(self._on_list_edit_member_clicked)
        self.members_list_screen.renew_requested.connect(self._on_list_renew_plan_clicked)
        self.members_list_screen.delete_requested.connect(self._on_list_delete_member_clicked)
        
        # Check-in
        self.checkin_screen.name_input.returnPressed.connect(
            self._on_checkin_search_by_name
        )
        self.checkin_screen.search_button.clicked.connect(
            self._on_checkin_search_by_name
        )
        self.checkin_screen.results_list.itemClicked.connect(
            self._on_checkin_result_clicked
        )
        self.checkin_screen.confirm_button.clicked.connect(
            self._on_confirm_checkin_clicked
        )
        self.checkin_screen.profile_button.clicked.connect(
            self._on_checkin_profile_clicked
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
    
    def _on_dashboard_member_clicked(self, member_id: int):
        """Navega para o perfil do membro a partir do dashboard."""
        from src.ui.components.sidebar import SidebarContext
        from src.data.data_provider import get_member_by_id
        
        if not self.is_connected:
            return
        
        try:
            # Busca os dados do membro pelo ID
            member = get_member_by_id(member_id)
            
            if member:
                # Muda para o contexto de Membros e mostra o perfil
                self.sidebar.set_context(SidebarContext.MEMBERS)
                self.stacked_widget.setCurrentIndex(3)  # MemberSearchScreen
                self.member_search_screen.display_member_data(member)
            else:
                QMessageBox.warning(self, "Aviso", "Membro não encontrado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar membro: {e}")

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
        self._load_members_list()

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
        plans_action.triggered.connect(self._show_manage_plans_dialog)
        
        menu.addSeparator()
        
        backup_action = menu.addAction("💾 Backup do Banco")
        backup_action.triggered.connect(self._create_database_backup)
        
        sync_action = menu.addAction("🔄 Sincronizar Sheets")
        sync_action.triggered.connect(self._show_sync_dialog)
        
        menu.addSeparator()
        
        add_member_action = menu.addAction("➕ Novo Membro")
        add_member_action.triggered.connect(self._show_add_member_dialog)
        
        # Mostra o menu na posição do cursor
        menu.exec(QCursor.pos())
    
    def _show_manage_plans_dialog(self):
        """Abre a tela de gerenciamento de planos."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(8)
        self.plans_screen.refresh()
    
    def _show_add_member_dialog(self):
        """Abre o diálogo para adicionar novo membro."""
        try:
            dialog = AddMemberDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Atualiza a lista de membros se estiver visível
                if self.stacked_widget.currentIndex() == 6:
                    self._load_members_list()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir formulário de novo membro: {e}")
    
    def _show_sync_dialog(self):
        """Abre o diálogo de sincronização com Google Sheets."""
        try:
            dialog = SyncDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir sincronização: {e}")
    
    def _show_expiring_plans_dialog(self):
        """Abre o diálogo de planos a vencer."""
        try:
            dialog = ExpiringPlansDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir planos a vencer: {e}")
    
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
        """Executa as migrações do banco de dados automaticamente."""
        try:
            from src.data.migrations import DatabaseMigrator
            from src.data.database_manager import DatabaseManager
            
            # Instanciar DatabaseManager apenas para migrações
            db_manager = DatabaseManager()
            db_manager.connect()
            
            migrator = DatabaseMigrator(db_manager)
            migrator.run_all()
            
            db_manager.close()
            print("✓ Migrações do banco de dados executadas com sucesso")
        except Exception as e:
            print(f"⚠ Erro ao executar migrações: {e}")
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
    
    # === Busca de Membros ===
    
    def _on_member_search_by_name(self):
        """Manipula a busca por nome."""
        search_term = self.member_search_screen.name_input.text().strip()
        
        if not search_term:
            self.member_search_screen.show_empty_search_warning()
            return
        
        self.member_search_screen.set_searching_state()
        
        self.worker = MemberSearchWorker(search_term)
        self.worker.search_completed.connect(self._on_member_search_completed)
        self.worker.status_updated.connect(lambda msg: self.home_screen.append_status(msg))
        self.worker.start()
    
    def _on_member_search_completed(self, results):
        """Manipula a conclusão da busca por nome."""
        if not results:
            self.member_search_screen.show_no_results()
        else:
            self.member_search_screen.populate_results(results)
        
        self.member_search_screen.set_ready_state()
    
    def _on_member_result_clicked(self, item):
        """Manipula o clique em um resultado da lista."""
        from PyQt6.QtCore import Qt
        
        member_id = item.data(Qt.ItemDataRole.UserRole)
        member_data = self.search_service.get_member_by_id(member_id)
        
        if member_data:
            self.member_search_screen.display_member_data(member_data)
            self._load_member_history(member_id, member_data.get('nome', 'Membro'))
            self._load_member_financial_history(member_id, member_data.get('nome', 'Membro'))
        else:
            self.member_search_screen.show_error()
    
    def _load_member_history(self, member_id: int, member_name: str):
        """Carrega e exibe o histórico de check-ins do membro."""
        try:
            from src.data.data_provider import get_member_checkin_history
            
            history = get_member_checkin_history(member_id)
            self.member_search_screen.display_member_history(member_id, member_name, history)
            
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            self.member_search_screen.member_history_browser.setHtml(f"""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #FF6B6B;">Erro ao carregar histórico</h3>
                    <p style="color: #888;">{str(e)}</p>
                </div>
            """)
    
    def _load_member_financial_history(self, member_id: int, member_name: str):
        """Carrega e exibe o histórico financeiro do membro."""
        try:
            from src.data.data_provider import get_provider
            
            # Buscar histórico de pagamentos do membro via DataProvider
            provider = get_provider()
            payments = provider.get_member_payment_history(member_id)
            self.member_search_screen.display_member_financial_history(
                member_id, member_name, payments
            )
        except Exception as e:
            print(f"Erro ao carregar histórico financeiro: {e}")
            import traceback
            traceback.print_exc()
            self.member_search_screen.member_financial_browser.setHtml(f"""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #FF6B6B;">Erro ao carregar histórico financeiro</h3>
                    <p style="color: #888;">{str(e)}</p>
                </div>
            """)
    
    def _on_edit_member_clicked(self):
        """Abre o diálogo de edição do membro atual."""
        if not self.member_search_screen.current_member_data:
            return
        
        from src.ui.dialogs.edit_member_dialog import EditMemberDialog
        
        dialog = EditMemberDialog(self.member_search_screen.current_member_data, self)
        dialog.member_updated.connect(self._on_member_updated)
        dialog.exec()
    
    def _on_renew_plan_clicked(self):
        """Abre o diálogo de renovação de plano do membro atual."""
        if not self.member_search_screen.current_member_data:
            return
        
        from src.ui.dialogs.renew_plan_dialog import RenewPlanDialog
        
        dialog = RenewPlanDialog(self.member_search_screen.current_member_data, self)
        dialog.plan_renewed.connect(self._on_plan_renewed)
        dialog.exec()
    
    def _on_delete_member_clicked(self):
        """Abre o diálogo de confirmação de exclusão do membro atual."""
        if not self.member_search_screen.current_member_data:
            return
        
        from src.ui.dialogs.delete_member_dialog import DeleteMemberDialog
        
        dialog = DeleteMemberDialog(self.member_search_screen.current_member_data, self)
        
        # Se o usuário confirmar a exclusão
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._delete_member(self.member_search_screen.current_member_data)
    
    def _delete_member(self, member_data: dict):
        """Executa a exclusão do membro."""
        try:
            from src.data.data_provider import delete_member
            
            member_id = member_data['id']
            member_name = member_data['nome']
            
            success = delete_member(member_id)
            
            if success:
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Membro '{member_name}' foi excluído com sucesso!\n\n"
                    f"Todos os check-ins e pagamentos relacionados também foram removidos."
                )
                
                # Limpa a tela
                self.member_search_screen.results_list.clear()
                self.member_search_screen.member_result_browser.setHtml(
                    self.member_search_screen._get_initial_message()
                )
                self.member_search_screen.member_history_browser.setHtml(
                    "<p style='color: #888888;'>Selecione um membro para ver o histórico.</p>"
                )
                self.member_search_screen.edit_button.setVisible(False)
                self.member_search_screen.delete_button.setVisible(False)
                self.member_search_screen.current_member_data = None
                
            else:
                QMessageBox.warning(
                    self,
                    "Erro",
                    f"Não foi possível excluir o membro '{member_name}'."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao excluir membro: {str(e)}"
            )
    
    def _on_member_updated(self, updated_data: dict):
        """Manipula a atualização de um membro."""
        try:
            from src.data.data_provider import update_member
            
            # Extrai o método de pagamento
            metodo_pagamento = updated_data.pop('metodo_pagamento', '')
            
            # Define se deve registrar pagamento (apenas se método foi informado)
            register_payment = bool(metodo_pagamento)
            
            success = update_member(
                updated_data, 
                register_payment=register_payment,
                metodo_pagamento=metodo_pagamento
            )
            
            if success:
                mensagem = f"Membro '{updated_data['nome']}' atualizado com sucesso!"
                if register_payment:
                    mensagem += "\n\n💰 Pagamento registrado no sistema financeiro."
                
                QMessageBox.information(
                    self,
                    "Sucesso",
                    mensagem
                )
                
                # Atualiza a exibição com os novos dados
                member_id = updated_data['id']
                updated_member = self.search_service.get_member_by_id(member_id)
                
                if updated_member:
                    self.member_search_screen.display_member_data(updated_member)
                    
                    # Se registrou pagamento, atualizar a aba financeira também
                    if register_payment:
                        from src.data.data_provider import get_provider
                        provider = get_provider()
                        payments = provider.get_member_payment_history(member_id)
                        self.member_search_screen.display_member_financial_history(
                            member_id, 
                            updated_data['nome'], 
                            payments
                        )
            else:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Não foi possível atualizar o membro. Verifique o console."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro Crítico",
                f"Ocorreu um erro inesperado: {e}"
            )
    
    def _on_plan_renewed(self, renewal_data: dict):
        """Manipula a renovação do plano de um membro."""
        try:
            from src.data.data_provider import update_member
            
            # Extrair método de pagamento
            metodo_pagamento = renewal_data.pop('metodo_pagamento', '')
            
            # Para renovação, sempre registrar pagamento
            register_payment = True
            
            # Nome do membro (para mensagens)
            current_data = self.member_search_screen.current_member_data
            member_name = current_data.get('nome', '') if current_data else ''
            
            # Atualizar o membro (apenas vencimento - o plano continua o mesmo)
            success = update_member(
                renewal_data, 
                register_payment=register_payment,
                metodo_pagamento=metodo_pagamento
            )
            
            if success:
                from src.config import PLANOS_PRECOS
                valor = PLANOS_PRECOS.get(renewal_data.get('plano', ''), 0.0)
                
                mensagem = f"Plano renovado com sucesso!"
                mensagem += f"\n\n💰 Pagamento de R$ {valor:.2f} registrado no sistema financeiro."
                mensagem += f"\n📅 Novo vencimento: {renewal_data.get('vencimento_plano', 'N/A')}"
                
                QMessageBox.information(
                    self,
                    "Sucesso",
                    mensagem
                )
                
                # Atualiza a exibição com os novos dados
                member_id = renewal_data['id']
                updated_member = self.search_service.get_member_by_id(member_id)
                
                if updated_member:
                    self.member_search_screen.display_member_data(updated_member)
                    
                    # Atualizar a aba financeira
                    from src.data.data_provider import get_provider
                    provider = get_provider()
                    payments = provider.get_member_payment_history(member_id)
                    self.member_search_screen.display_member_financial_history(
                        member_id, 
                        member_name, 
                        payments
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Não foi possível renovar o plano. Verifique o console."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro Crítico",
                f"Ocorreu um erro inesperado: {e}"
            )
    
    def _on_delete_checkin_requested(self, checkin_id: int):
        """Manipula a solicitação de exclusão de um check-in."""
        # Confirmação
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            "Tem certeza que deseja deletar este check-in?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from src.data.data_provider import delete_checkin
                
                success = delete_checkin(checkin_id)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        "Check-in deletado com sucesso!"
                    )
                    
                    # Recarrega o histórico do membro atual
                    if self.member_search_screen.current_member_data:
                        member_id = self.member_search_screen.current_member_data['id']
                        member_name = self.member_search_screen.current_member_data['nome']
                        self._load_member_history(member_id, member_name)
                else:
                    QMessageBox.warning(
                        self,
                        "Erro",
                        "Não foi possível deletar o check-in. Verifique o console."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao deletar check-in: {str(e)}"
                )
    
    def _on_edit_checkin_requested(self, checkin_id: int):
        """Manipula a solicitação de edição de um check-in."""
        try:
            from src.data.data_provider import get_provider, update_checkin_datetime
            from src.ui.dialogs import EditCheckinDialog
            
            # Buscar dados do check-in
            provider = get_provider()
            if not self.member_search_screen.current_member_data:
                QMessageBox.warning(self, "Erro", "Nenhum membro selecionado.")
                return
            
            member_id = self.member_search_screen.current_member_data['id']
            member_name = self.member_search_screen.current_member_data['nome']
            
            # Buscar o histórico para encontrar o check-in específico
            history = provider.get_member_checkin_history(member_id)
            checkin_data = next((c for c in history if c['id'] == checkin_id), None)
            
            if not checkin_data:
                QMessageBox.warning(self, "Erro", "Check-in não encontrado.")
                return
            
            # Converter data/hora
            current_datetime = datetime.fromisoformat(checkin_data['checkin_datetime'])
            
            # Abrir dialog de edição
            dialog = EditCheckinDialog(checkin_id, current_datetime, member_name, self)
            
            # Conectar sinal de atualização
            def on_checkin_updated(cid: int, new_dt: datetime):
                success = update_checkin_datetime(cid, new_dt)
                if success:
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        "Horário do check-in atualizado com sucesso!"
                    )
                    # Recarrega o histórico
                    self._load_member_history(member_id, member_name)
                else:
                    QMessageBox.warning(
                        self,
                        "Erro",
                        "Não foi possível atualizar o check-in. Verifique o console."
                    )
            
            dialog.checkin_updated.connect(on_checkin_updated)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao editar check-in: {str(e)}"
            )
    
    # === Check-in ===
    
    def _on_checkin_search_by_name(self):
        """Manipula a busca por nome na tela de check-in."""
        search_term = self.checkin_screen.name_input.text().strip()
        if not search_term:
            return

        self.checkin_screen.set_searching_state()

        self.worker = MemberSearchWorker(search_term)
        self.worker.search_completed.connect(self._on_checkin_search_completed)
        self.worker.start()

    def _on_checkin_search_completed(self, results):
        """Manipula a conclusão da busca na tela de check-in."""
        self.checkin_screen.populate_results(results)
        self.checkin_screen.set_ready_state()

    def _on_checkin_result_clicked(self, item):
        """Manipula o clique em um resultado na lista de check-in."""
        from PyQt6.QtCore import Qt
        
        member_id = item.data(Qt.ItemDataRole.UserRole)
        member_data = self.search_service.get_member_by_id(member_id)

        if member_data:
            self.checkin_screen.display_member_for_checkin(member_id, member_data)
        else:
            self.checkin_screen.show_error()

    def _on_confirm_checkin_clicked(self):
        """Confirma e registra o check-in do membro."""
        if self.checkin_screen.current_member_id is None:
            return

        from src.ui.workers import CheckinWorker

        # Desabilitar botão para evitar duplo clique
        self.checkin_screen.confirm_button.setEnabled(False)
        self.checkin_screen.confirm_button.setText("Processando...")

        # Iniciar worker
        self.worker = CheckinWorker(self.checkin_screen.current_member_id)
        self.worker.checkin_completed.connect(self._on_checkin_worker_completed)
        self.worker.start()
    
    def _on_checkin_worker_completed(self, success, message, details):
        """Manipula o resultado do worker de check-in."""
        # Reabilitar botão
        self.checkin_screen.confirm_button.setEnabled(True)
        self.checkin_screen.confirm_button.setText("Confirmar Presença")
        
        if success:
            msg = "Check-in confirmado com sucesso!"
            if details.get('payment_generated'):
                msg += f"\n\n💰 Pagamento de R$ {details.get('payment_amount', 0):.2f} gerado."
            
            QMessageBox.information(self, "Check-in Realizado", msg)
            self.checkin_screen.clear_after_checkin()
            
            # Atualizar dashboard se estiver visível
            if self.stacked_widget.currentIndex() == 1:
                self._update_dashboard()
        else:
            QMessageBox.warning(self, "Atenção", message)

    def _on_checkin_profile_clicked(self):
        """Manipula o clique no botão de perfil do membro na tela de check-in."""
        member_id = self.checkin_screen.current_member_id
        if member_id is None:
            return
            
        # Obter dados do membro para pegar o nome
        member_data = self.search_service.get_member_by_id(member_id)
        if not member_data:
            return
            
        member_name = member_data.get('nome', '')
        
        # Mudar para a tela de lista de membros
        self._show_members_list()
        
        # Selecionar o membro
        self.members_list_screen.select_member_by_id(member_id, member_name)
    
    # === Adicionar Membro ===
    
    def _show_add_member_dialog(self):
        """Mostra a janela de diálogo para adicionar um novo membro."""
        if not self.is_connected:
            QMessageBox.warning(self, "Aviso", "A conexão com o banco de dados ainda não foi estabelecida.")
            return

        dialog = AddMemberDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            member_data = dialog.get_data()

            # Validação dos campos obrigatórios
            required_fields = ["nome", "plano", "data_nascimento", "whatsapp", "genero"]
            for field in required_fields:
                if not member_data.get(field):
                    QMessageBox.warning(self, "Campo Obrigatório", 
                                       f"O campo '{field.replace('_', ' ').title()}' é obrigatório.")
                    return

            try:
                from src.data.data_provider import add_member
                
                new_id = add_member(member_data)
                if new_id:
                    QMessageBox.information(self, "Sucesso", 
                                          f"Membro '{member_data['nome']}' adicionado com sucesso!")
                else:
                    QMessageBox.critical(self, "Erro", 
                                        "Não foi possível adicionar o membro. Verifique o console.")
            except Exception as e:
                QMessageBox.critical(self, "Erro Crítico", 
                                    f"Ocorreu um erro inesperado ao salvar o membro: {e}")
    
    # === Financeiro ===
    
    def _load_financial_data(self):
        """Carrega os dados financeiros com base no período selecionado."""
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
            
            # Obter resumo
            summary = self.manager.data_provider.get_financial_summary(
                start_datetime, end_datetime
            )
            
            # Atualizar cards de resumo
            self.financial_screen.update_summary(
                summary['total_receita'],
                summary['total_transacoes'],
                summary['ticket_medio']
            )
            
            # Obter breakdown por tipo
            breakdown = self.manager.data_provider.get_revenue_breakdown(
                start_datetime, end_datetime
            )
            self.financial_screen.update_breakdown(breakdown)
            
            # Obter transações
            transactions = self.manager.data_provider.get_transactions_in_range(
                start_datetime, end_datetime
            )
            self.financial_screen.update_transactions(transactions)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar dados financeiros: {str(e)}"
            )
    
    def _show_plan_distribution_dialog(self):
        """Abre o diálogo de gráficos financeiros."""
        from src.ui.dialogs.finance_graphs import FinancialGraphsDialog
        
        dialog = FinancialGraphsDialog(self)
        dialog.exec()
    
    def _show_manage_plans_dialog(self):
        """Exibe a tela de gerenciamento de planos."""
        if not self.is_connected:
            return
        self.stacked_widget.setCurrentIndex(8)
        self.plans_screen.refresh()
    
    def _show_expiring_plans_dialog(self):
        """Exibe o diálogo de planos a vencer."""
        # DataProvider agora é compatível co o ExpiringPlansDialog (duck typing)
        # pois ambos implementam get_all_members()
        dialog = ExpiringPlansDialog(self.manager.data_provider, self)
        dialog.exec()
    
    # === Sincronização ===
    
    def _show_sync_dialog(self):
        """Abre o diálogo de sincronização com Google Sheets."""
        dialog = SyncDialog(self)
        result = dialog.exec()
        
        # Se a sincronização foi bem-sucedida, atualiza o dashboard
        if result == QDialog.DialogCode.Accepted and dialog.get_result():
            QMessageBox.information(
                self,
                "Atualização Recomendada",
                "Sincronização concluída!\n\n"
                "Recomenda-se atualizar o dashboard para visualizar\n"
                "os novos dados sincronizados."
            )
            
            # Atualiza automaticamente o dashboard
            if self.is_connected:
                self._update_dashboard()
    
    # === Gerenciamento de Banco de Dados ===
    
    def _create_database_backup(self):
        """Cria um backup do banco de dados."""
        reply = QMessageBox.question(
            self,
            "Criar Backup",
            "Deseja criar um backup do banco de dados?\n\n"
            "O backup será salvo na pasta 'backups/' do projeto.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import os
                import shutil
                from datetime import datetime
                from pathlib import Path
                
                # Caminho do banco de dados
                project_root = Path(__file__).parent.parent.parent
                db_path = os.path.join(project_root, "gym_database.db")
                backup_dir = os.path.join(project_root, "backups")
                
                # Criar diretório de backup se não existir
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                # Nome do backup com timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f"gym_database_backup_{timestamp}.db")
                
                # Copiar arquivo
                shutil.copy2(db_path, backup_path)
                
                QMessageBox.information(
                    self,
                    "Backup Criado",
                    f"Backup criado com sucesso!\n\n"
                    f"Arquivo: gym_database_backup_{timestamp}.db\n"
                    f"Localização: backups/"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro no Backup",
                    f"Erro ao criar backup do banco de dados:\n\n{str(e)}"
                )
    
    def _generate_frequency_report(self):
        """Gera relatório de frequência em HTML."""
        if not self.is_connected:
            QMessageBox.warning(
                self,
                "Banco Desconectado",
                "Conecte-se ao banco de dados antes de gerar relatórios."
            )
            return
        
        try:
            from src.reports.frequency_report import generate_frequency_report
            import webbrowser
            
            # Gerar relatório (últimos 30 dias por padrão)
            filepath = generate_frequency_report(days=30)
            
            # Abrir no navegador
            webbrowser.open(f'file://{filepath}')
            
            QMessageBox.information(
                self,
                "Relatório Gerado",
                f"Relatório de frequência gerado com sucesso!\n\n"
                f"O arquivo foi aberto no navegador e salvo em:\n"
                f"relatorios/"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Gerar Relatório",
                f"Erro ao gerar relatório de frequência:\n\n{str(e)}"
            )
    
    def _generate_members_report(self):
        """Gera relatório de membros em HTML."""
        if not self.is_connected:
            QMessageBox.warning(
                self,
                "Banco Desconectado",
                "Conecte-se ao banco de dados antes de gerar relatórios."
            )
            return
        
        try:
            from src.reports.members_report import generate_members_report
            import webbrowser
            
            # Gerar relatório
            filepath = generate_members_report()
            
            # Abrir no navegador
            webbrowser.open(f'file://{filepath}')
            
            QMessageBox.information(
                self,
                "Relatório Gerado",
                f"Relatório de membros gerado com sucesso!\n\n"
                f"O arquivo foi aberto no navegador e salvo em:\n"
                f"relatorios/"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Gerar Relatório",
                f"Erro ao gerar relatório de membros:\n\n{str(e)}"
            )
    
    def _generate_financial_report(self):
        """Gera o relatório financeiro em HTML."""
        if not self.is_connected:
            QMessageBox.warning(
                self,
                "Banco Desconectado",
                "Conecte-se ao banco de dados antes de gerar relatórios."
            )
            return

        # Solicitar o período ao usuário
        period, ok = QInputDialog.getText(
            self, 
            "Período do Relatório", 
            "Digite o período (ex: '10/2025' para mensal ou 'T4/2025' para trimestral):"
        )

        if ok and period:
            try:
                # Gerar o relatório
                filepath = generate_finance_report(
                    period=period
                )
                
                # Abrir no navegador
                webbrowser.open(f'file://{filepath}')
                
                QMessageBox.information(
                    self,
                    "Relatório Gerado",
                    f"Relatório financeiro para o período '{period}' gerado com sucesso!\n\n"
                    f"O arquivo foi aberto no navegador e salvo em:\n"
                    f"relatorios/"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro ao Gerar Relatório",
                    f"Erro ao gerar relatório financeiro:\n\n{str(e)}"
                )
    
    def _optimize_database(self):
        """Otimiza o banco de dados criando índices e executando VACUUM."""
        reply = QMessageBox.question(
            self,
            "Otimizar Banco de Dados",
            "Esta operação irá:\n"
            "• Criar índices para melhorar a performance\n"
            "• Executar VACUUM para compactar o banco\n"
            "• Atualizar estatísticas\n\n"
            "Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from src.data.database_manager import DatabaseManager
                
                db = DatabaseManager()
                stats = db.optimize_and_reindex()
                db.close()

                indices_checked = stats.get("indices_processed", 0)
                vacuum_status = "Sim" if stats.get("vacuum_executed") else "Não"
                analyze_status = "Sim" if stats.get("analyze_executed") else "Não"
                pragma_status = "Sim" if stats.get("pragma_optimize_executed") else "Não"

                QMessageBox.information(
                    self,
                    "Otimização Concluída",
                    "Banco de dados otimizado com sucesso!\n\n"
                    f"• {indices_checked} índices verificados/recriados\n"
                    f"• VACUUM executado: {vacuum_status}\n"
                    f"• ANALYZE executado: {analyze_status}\n"
                    f"• PRAGMA optimize executado: {pragma_status}\n\n"
                    "As buscas devem estar significativamente mais rápidas agora."
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro na Otimização",
                    f"Erro ao otimizar banco de dados:\n\n{str(e)}"
                )
    
    def _run_database_migration(self):
        """Executa o script de migração crítica do banco de dados."""
        reply = QMessageBox.warning(
            self,
            "Migração Crítica do Banco",
            "⚠️  ATENÇÃO: Esta operação irá modificar a estrutura do banco!\n\n"
            "Mudanças aplicadas:\n"
            "• Foreign keys com ON DELETE CASCADE\n"
            "• Conversão de datas de TEXT para DATE/DATETIME\n"
            "• Criação de índices para performance\n"
            "• Triggers e constraints de validação\n\n"
            "Um backup automático será criado antes da migração.\n\n"
            "Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import subprocess
                import sys
                from pathlib import Path
                
                # Caminho do script de migração
                project_root = Path(__file__).parent.parent.parent
                script_path = project_root / "scripts" / "fix_database_critical.py"
                
                if not script_path.exists():
                    raise FileNotFoundError(f"Script de migração não encontrado: {script_path}")
                
                # Executar script em processo separado
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=str(project_root),
                    input="sim\n",
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    QMessageBox.information(
                        self,
                        "Migração Concluída",
                        "✅ Migração executada com sucesso!\n\n"
                        "O banco de dados foi atualizado com:\n"
                        "• Foreign keys CASCADE\n"
                        "• Tipos de dados corretos\n"
                        "• Índices de performance\n\n"
                        "Verifique o console para detalhes."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Migração com Avisos",
                        f"A migração foi executada mas reportou avisos.\n\n"
                        f"Código de saída: {result.returncode}\n\n"
                        f"Verifique o console para detalhes."
                    )
                
                # Mostrar output no console
                if result.stdout:
                    print("\n=== OUTPUT DA MIGRAÇÃO ===")
                    print(result.stdout)
                if result.stderr:
                    print("\n=== ERROS DA MIGRAÇÃO ===")
                    print(result.stderr)
                    
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro na Migração",
                    f"Erro ao executar migração:\n\n{str(e)}\n\n"
                    f"Você pode executar manualmente:\n"
                    f"python scripts/fix_database_critical.py"
                )
    
    # === Lista de Membros ===
    
    def _load_members_list(self):
        """Carrega a lista de membros com paginação."""
        from src.data.data_provider import get_provider
        from src.services.plan_service import get_plan_service
        
        # Popula filtro de planos from database (centralized source)
        plan_service = get_plan_service()
        self.members_list_screen.populate_plan_filter(plan_service.get_plan_names())
        
        # Carrega dados paginados
        self._on_members_list_refresh()
    
    def _on_members_list_refresh(self):
        """Atualiza a lista de membros."""
        from src.data.data_provider import get_provider
        
        provider = get_provider()
        filters = self.members_list_screen.get_filters()
        
        data = provider.get_members_paginated(
            page=self.members_list_screen.current_page,
            page_size=self.members_list_screen.page_size,
            filter_text=filters['text'],
            filter_plan=filters['plan'],
            filter_status=filters['status']
        )
        
        self.members_list_screen.update_data(data)
    
    def _on_members_list_member_selected(self, member_data: dict):
        """Quando um membro é selecionado na lista."""
        # Carregar dados completos (garantir que temos tudo)
        full_member_data = self.search_service.get_member_by_id(member_data['id'])
        
        if full_member_data:
            # Exibir dados básicos
            self.members_list_screen.display_member_data(full_member_data)
            
            # Carregar históricos
            self._load_list_member_history(full_member_data['id'], full_member_data['nome'])
            self._load_list_member_financial_history(full_member_data['id'], full_member_data['nome'])
            
    def _load_list_member_history(self, member_id: int, member_name: str):
        """Carrega e exibe o histórico de check-ins do membro na lista."""
        try:
            from src.data.data_provider import get_member_checkin_history
            history = get_member_checkin_history(member_id)
            self.members_list_screen.display_member_history(history)
        except Exception as e:
            print(f"Erro ao carregar histórico na lista: {e}")

    def _load_list_member_financial_history(self, member_id: int, member_name: str):
        """Carrega e exibe o histórico financeiro do membro na lista."""
        try:
            from src.data.data_provider import get_provider
            provider = get_provider()
            if provider:
                payments = provider.get_member_payment_history(member_id)
                self.members_list_screen.display_member_financial_history(payments)
        except Exception as e:
            print(f"Erro ao carregar histórico financeiro na lista: {e}")

    def _on_list_edit_member_clicked(self):
        """Abre o diálogo de edição do membro atual da lista."""
        if not self.members_list_screen.current_member_data:
            return
        
        from src.ui.dialogs.edit_member_dialog import EditMemberDialog
        
        dialog = EditMemberDialog(self.members_list_screen.current_member_data, self)
        dialog.member_updated.connect(self._on_list_member_updated)
        dialog.exec()

    def _on_list_renew_plan_clicked(self):
        """Abre o diálogo de renovação de plano do membro atual da lista."""
        if not self.members_list_screen.current_member_data:
            return
        
        from src.ui.dialogs.renew_plan_dialog import RenewPlanDialog
        
        dialog = RenewPlanDialog(self.members_list_screen.current_member_data, self)
        dialog.plan_renewed.connect(self._on_list_plan_renewed)
        dialog.exec()

    def _on_list_delete_member_clicked(self):
        """Abre o diálogo de confirmação de exclusão do membro atual da lista."""
        if not self.members_list_screen.current_member_data:
            return
        
        from src.ui.dialogs.delete_member_dialog import DeleteMemberDialog
        
        dialog = DeleteMemberDialog(self.members_list_screen.current_member_data, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._delete_list_member(self.members_list_screen.current_member_data)

    def _on_list_member_updated(self, updated_data: dict):
        """Manipula a atualização de um membro na lista."""
        # Reutiliza a lógica de atualização, mas atualiza a tela da lista
        self._on_member_updated(updated_data) # Atualiza lógica geral (pagamentos, etc)
        
        # Atualiza especificamente a tela da lista
        full_data = self.search_service.get_member_by_id(updated_data['id'])
        if full_data:
            self.members_list_screen.display_member_data(full_data)
            self._load_members_list() # Recarrega a lista para atualizar nomes/planos na esquerda

    def _on_list_plan_renewed(self, renewal_data: dict):
        """Manipula a renovação de plano na lista."""
        self._on_plan_renewed(renewal_data) # Reutiliza lógica geral
        
        # Atualiza tela da lista
        full_data = self.search_service.get_member_by_id(renewal_data['id'])
        if full_data:
            self.members_list_screen.display_member_data(full_data)
            self._load_list_member_financial_history(full_data['id'], full_data['nome'])
            self._load_members_list()

    def _delete_list_member(self, member_data: dict):
        """Executa a exclusão do membro a partir da lista."""
        try:
            from src.data.data_provider import delete_member
            
            member_id = member_data['id']
            member_name = member_data['nome']
            
            success = delete_member(member_id)
            
            if success:
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Membro '{member_name}' foi excluído com sucesso!"
                )
                self._load_members_list() # Recarrega a lista
                # Limpar detalhes
                self.members_list_screen.details_browser.setHtml(
                    "<div style='text-align: center; color: #666; margin-top: 20px;'>Selecione um membro para ver os detalhes</div>"
                )
                self.members_list_screen.history_browser.clear()
                self.members_list_screen.financial_browser.clear()
                self.members_list_screen.edit_button.setVisible(False)
                self.members_list_screen.renew_button.setVisible(False)
                self.members_list_screen.delete_button.setVisible(False)
                self.members_list_screen.current_member_data = None
            else:
                QMessageBox.warning(self, "Erro", f"Não foi possível excluir o membro '{member_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir membro: {str(e)}")


def main():
    """Função principal."""
    from PyQt6.QtWidgets import QApplication
    
    print("Iniciando aplicação...")
    
    app = QApplication(sys.argv)
    print("QApplication criada")
    
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
