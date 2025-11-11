"""Janela principal da aplicação."""

import sys

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QMessageBox, QDialog
)
from PyQt6.QtGui import QAction

from src.core.aniversariantes_manager import AniversariantesManager
from src.ui.html_formatter import HTMLFormatter
from src.core.member_search_service import MemberSearchService
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
    FinancialScreen
)
from src.ui.dialogs import AddMemberDialog, SyncDialog, ManagePlansDialog


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
        self.setWindowTitle("Sistema de Gestão de Membros")
        self.setGeometry(100, 100, 800, 650)
        self.setStyleSheet(STYLESHEET)
        
        # Cria o menu
        self._create_menu()
        
        # Cria o stack widget para alternar entre telas
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Cria as telas
        self.home_screen = HomeScreen()
        self.dashboard_screen = DashboardScreen()
        self.aniversariantes_screen = AniversariantesScreen()
        self.member_search_screen = MemberSearchScreen()
        self.checkin_screen = CheckinScreen()
        self.financial_screen = FinancialScreen()
        
        # Adiciona ao stack
        self.stacked_widget.addWidget(self.home_screen)  # 0
        self.stacked_widget.addWidget(self.dashboard_screen)  # 1
        self.stacked_widget.addWidget(self.aniversariantes_screen)  # 2
        self.stacked_widget.addWidget(self.member_search_screen)  # 3
        self.stacked_widget.addWidget(self.checkin_screen)  # 4
        self.stacked_widget.addWidget(self.financial_screen)  # 5
        
        # Conecta sinais das telas
        self._connect_screen_signals()
        
        # Mostra a tela de conexão
        self.stacked_widget.setCurrentIndex(0)
    
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

            buscar_action = QAction("🔍 Buscar Membro", self)
            buscar_action.setShortcut("Ctrl+F")
            buscar_action.triggered.connect(self._show_member_search)
            membros_menu.addAction(buscar_action)

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
            
            # === SUBMENU: Pagamentos ===
            pagamentos_menu = self.gestao_menu.addMenu("💰 Pagamentos")
            
            financial_action = QAction("📈 Visão Financeira", self)
            financial_action.setShortcut("Ctrl+$")
            financial_action.triggered.connect(self._show_financial_screen)
            pagamentos_menu.addAction(financial_action)
            
            pagamentos_menu.addSeparator()
            
            # Placeholder para relatórios (futuro)
            export_financial_action = QAction("📄 Exportar Relatório Financeiro", self)
            export_financial_action.setEnabled(False)  # Será implementado na etapa 5
            export_financial_action.setToolTip("Em breve: exportar CSV/PDF")
            pagamentos_menu.addAction(export_financial_action)
            
            # === SUBMENU: Relatórios ===
            relatorios_menu = self.gestao_menu.addMenu("📊 Relatórios")
            
            freq_report_action = QAction("📅 Relatório de Frequência", self)
            freq_report_action.setEnabled(False)  # Será implementado na etapa 5
            freq_report_action.setToolTip("Em breve: relatório detalhado de frequência")
            relatorios_menu.addAction(freq_report_action)
            
            member_report_action = QAction("👤 Relatório de Membros", self)
            member_report_action.setEnabled(False)  # Será implementado na etapa 5
            member_report_action.setToolTip("Em breve: listagem completa de membros")
            relatorios_menu.addAction(member_report_action)
            
            # === SEPARADOR ===
            self.gestao_menu.addSeparator()
            
            # === SUBMENU: Banco de Dados ===
            database_menu = self.gestao_menu.addMenu("🗄️ Banco de Dados")
            
            backup_action = QAction("💾 Backup do Banco", self)
            backup_action.triggered.connect(self._create_database_backup)
            database_menu.addAction(backup_action)
            
            optimize_action = QAction("⚡ Otimizar e Reindexar", self)
            optimize_action.triggered.connect(self._optimize_database)
            database_menu.addAction(optimize_action)
            
            database_menu.addSeparator()
            
            migrate_action = QAction("🔧 Migrar Banco (Correções Críticas)", self)
            migrate_action.triggered.connect(self._run_database_migration)
            migrate_action.setToolTip("Executa migração crítica: foreign keys, datas, índices")
            database_menu.addAction(migrate_action)

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
    
    # === Handlers de Conexão ===
    
    def _on_connection_status_updated(self, status):
        """Manipula atualização de status da conexão."""
        self.home_screen.append_status(status)
    
    def _on_connection_completed(self, success):
        """Manipula a conclusão da conexão."""
        if success:
            self.is_connected = True
            if hasattr(self, 'gestao_menu') and self.gestao_menu:
                self.gestao_menu.setEnabled(True)
            if hasattr(self, 'atividade_menu') and self.atividade_menu:
                self.atividade_menu.setEnabled(True)
            if hasattr(self, 'tools_menu') and self.tools_menu:
                self.tools_menu.setEnabled(True)
            
            self._show_dashboard()
        else:
            self.home_screen.set_error("Falha na conexão. Verifique o console para mais detalhes.")
    
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
        
        self.worker = DataFetchWorker(self.manager)
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
        
        self.worker = MemberSearchWorker(self.search_service, search_term)
        self.worker.search_completed.connect(self._on_member_search_completed)
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
            
            # Buscar histórico de pagamentos do membro
            db_manager = get_provider().db_manager
            if db_manager and db_manager.connection:
                payments = db_manager.get_member_payment_history(member_id)
                self.member_search_screen.display_member_financial_history(
                    member_id, member_name, payments
                )
            else:
                self.member_search_screen.member_financial_browser.setHtml("""
                    <div style="text-align: center; padding: 20px;">
                        <h3 style="color: #FF6B6B;">Erro de Conexão</h3>
                        <p style="color: #888;">Sem conexão com o banco de dados</p>
                    </div>
                """)
            
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
                        payments = provider.db_manager.get_member_payment_history(member_id)
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
                    payments = provider.db_manager.get_member_payment_history(member_id)
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
                    "Erro Crítico",
                    f"Ocorreu um erro inesperado: {e}"
                )
    
    # === Check-in ===
    
    def _on_checkin_search_by_name(self):
        """Manipula a busca por nome na tela de check-in."""
        search_term = self.checkin_screen.name_input.text().strip()
        if not search_term:
            return

        self.checkin_screen.set_searching_state()

        self.worker = MemberSearchWorker(self.search_service, search_term)
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

        from src.data.data_provider import add_checkin
        from datetime import datetime

        try:
            checkin_id = add_checkin(self.checkin_screen.current_member_id, datetime.now())
            if checkin_id:
                QMessageBox.information(self, "Check-in Realizado", "Check-in confirmado com sucesso!")
                self.checkin_screen.clear_after_checkin()
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível registrar o check-in.")
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Ocorreu um erro inesperado: {e}")
    
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
            summary = self.manager.data_provider.db_manager.get_financial_summary(
                start_datetime, end_datetime
            )
            
            # Atualizar cards de resumo
            self.financial_screen.update_summary(
                summary['total_receita'],
                summary['total_transacoes'],
                summary['ticket_medio']
            )
            
            # Obter breakdown por tipo
            breakdown = self.manager.data_provider.db_manager.get_revenue_breakdown(
                start_datetime, end_datetime
            )
            self.financial_screen.update_breakdown(breakdown)
            
            # Obter transações
            transactions = self.manager.data_provider.db_manager.get_transactions_in_range(
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
        """Abre o diálogo de gerenciamento de planos."""
        if not self.is_connected:
            QMessageBox.warning(
                self,
                "Não Conectado",
                "Conecte-se ao banco de dados primeiro."
            )
            return
        
        dialog = ManagePlansDialog(self)
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
                if not db.connect():
                    raise Exception("Não foi possível conectar ao banco de dados")
                
                cursor = db.connection.cursor()
                
                # Criar índices
                indices_created = 0
                indices = [
                    ("idx_membros_nome", "CREATE INDEX IF NOT EXISTS idx_membros_nome ON membros(nome)"),
                    ("idx_membros_plano", "CREATE INDEX IF NOT EXISTS idx_membros_plano ON membros(plano)"),
                    ("idx_membros_estado", "CREATE INDEX IF NOT EXISTS idx_membros_estado_plano ON membros(estado_plano)"),
                    ("idx_membros_vencimento", "CREATE INDEX IF NOT EXISTS idx_membros_vencimento ON membros(vencimento_plano)"),
                    ("idx_frequencia_member", "CREATE INDEX IF NOT EXISTS idx_frequencia_member_id ON frequencia(member_id)"),
                    ("idx_frequencia_datetime", "CREATE INDEX IF NOT EXISTS idx_frequencia_datetime ON frequencia(checkin_datetime)"),
                    ("idx_pagamentos_member", "CREATE INDEX IF NOT EXISTS idx_pagamentos_member_id ON pagamentos(member_id)"),
                    ("idx_pagamentos_data", "CREATE INDEX IF NOT EXISTS idx_pagamentos_data ON pagamentos(data_pagamento)"),
                    ("idx_pagamentos_tipo", "CREATE INDEX IF NOT EXISTS idx_pagamentos_tipo ON pagamentos(tipo_transacao)"),
                ]
                
                for idx_name, sql in indices:
                    try:
                        cursor.execute(sql)
                        indices_created += 1
                    except Exception as e:
                        print(f"Aviso: Erro ao criar índice {idx_name}: {e}")
                
                # VACUUM e ANALYZE
                cursor.execute("VACUUM")
                cursor.execute("ANALYZE")
                
                db.connection.commit()
                db.close()
                
                QMessageBox.information(
                    self,
                    "Otimização Concluída",
                    f"Banco de dados otimizado com sucesso!\n\n"
                    f"• {indices_created} índices criados/verificados\n"
                    f"• VACUUM executado\n"
                    f"• Estatísticas atualizadas\n\n"
                    f"As buscas devem estar significativamente mais rápidas agora."
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
