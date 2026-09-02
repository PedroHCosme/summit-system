"""Janela principal da aplicação."""

import sys
import os

from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import QTimer

from src.core.aniversariantes_manager import AniversariantesManager
from src.ui.html_formatter import HTMLFormatter
from src.ui.styles import STYLESHEET

from src.ui.workers import (
    DatabaseConnectionWorker,
    DashboardWorker
)
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
        from src.ui.main_window_ui import build_ui
        build_ui(self)

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
        self.reports_coordinator.load_financial_data()



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
            self.members_coordinator.on_aniversariantes_search_clicked
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
            self.reports_coordinator.load_financial_data
        )
        self.financial_screen.plan_chart_button.clicked.connect(
            self.reports_coordinator.show_plan_distribution_dialog
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
        self.reports_coordinator.load_financial_data()
    
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
            self.home_screen.set_error(
                "Não foi possível conectar ao banco de dados.\n"
                "Feche e abra o sistema. Se o problema continuar, avise o suporte técnico."
            )
    
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
