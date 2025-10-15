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
    CheckinScreen
)
from src.ui.dialogs import AddMemberDialog


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
        
        # Adiciona ao stack
        self.stacked_widget.addWidget(self.home_screen)  # 0
        self.stacked_widget.addWidget(self.dashboard_screen)  # 1
        self.stacked_widget.addWidget(self.aniversariantes_screen)  # 2
        self.stacked_widget.addWidget(self.member_search_screen)  # 3
        self.stacked_widget.addWidget(self.checkin_screen)  # 4
        
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
        self.gestao_menu = self.menubar.addMenu("Gestão")
        if self.gestao_menu:
            self.gestao_menu.setEnabled(False)

            add_member_action = QAction("Adicionar Membro", self)
            add_member_action.triggered.connect(self._show_add_member_dialog)
            self.gestao_menu.addAction(add_member_action)

            buscar_action = QAction("Buscar Membro", self)
            buscar_action.triggered.connect(self._show_member_search)
            self.gestao_menu.addAction(buscar_action)

            aniversariantes_action = QAction("Aniversariantes", self)
            aniversariantes_action.triggered.connect(self._show_aniversariantes)
            self.gestao_menu.addAction(aniversariantes_action)

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
    
    def _on_edit_member_clicked(self):
        """Abre o diálogo de edição do membro atual."""
        if not self.member_search_screen.current_member_data:
            return
        
        from src.ui.dialogs.edit_member_dialog import EditMemberDialog
        
        dialog = EditMemberDialog(self.member_search_screen.current_member_data, self)
        dialog.member_updated.connect(self._on_member_updated)
        dialog.exec()
    
    def _on_member_updated(self, updated_data: dict):
        """Manipula a atualização de um membro."""
        try:
            from src.data.data_provider import update_member
            
            success = update_member(updated_data)
            
            if success:
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Membro '{updated_data['nome']}' atualizado com sucesso!"
                )
                
                # Atualiza a exibição com os novos dados
                member_id = updated_data['id']
                updated_member = self.search_service.get_member_by_id(member_id)
                
                if updated_member:
                    self.member_search_screen.display_member_data(updated_member)
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


def main():
    """Função principal."""
    from PyQt6.QtWidgets import QApplication
    
    print("Iniciando aplicação...")
    
    app = QApplication(sys.argv)
    print("QApplication criada")
    
    window = MainWindow()
    print("Janela criada")
    
    window.show()
    print("Janela exibida")
    print("A interface gráfica deve estar visível agora!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
