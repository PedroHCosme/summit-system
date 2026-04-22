"""Coordenação de fluxos de check-in na UI."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from src.ui.workers import CheckinWorker, MemberSearchWorker


class CheckinCoordinator:
    """Orquestra ações de check-in mantendo telas passivas."""

    def __init__(self, window):
        self.window = window

    def on_checkin_search_by_name(self):
        search_term = self.window.checkin_screen.name_input.text().strip()
        if not search_term:
            return

        self.window.checkin_screen.set_searching_state()
        self.window.worker = MemberSearchWorker(search_term)
        self.window.worker.search_completed.connect(self.on_checkin_search_completed)
        self.window.worker.start()

    def on_checkin_search_completed(self, results):
        self.window.checkin_screen.populate_results(results)
        self.window.checkin_screen.set_ready_state()

    def on_checkin_result_clicked(self, item):
        member_id = item.data(Qt.ItemDataRole.UserRole)
        member_data = self.window.search_service.get_member_by_id(member_id)
        if member_data:
            self.window.checkin_screen.display_member_for_checkin(member_id, member_data)
        else:
            self.window.checkin_screen.show_error()

    def on_confirm_checkin_clicked(self):
        if self.window.checkin_screen.current_member_id is None:
            return
        self.window.checkin_screen.confirm_button.setEnabled(False)
        self.window.checkin_screen.confirm_button.setText("Processando...")
        self.window.worker = CheckinWorker(self.window.checkin_screen.current_member_id)
        self.window.worker.checkin_completed.connect(self.on_checkin_worker_completed)
        self.window.worker.start()

    def on_checkin_worker_completed(self, success, message, details):
        self.window.checkin_screen.confirm_button.setEnabled(True)
        self.window.checkin_screen.confirm_button.setText("Confirmar Check-in")

        if success:
            msg = "Check-in confirmado com sucesso!"
            if details.get("payment_generated"):
                msg += f"\n\n💰 Pagamento de R$ {details.get('payment_amount', 0):.2f} gerado."
            self.window.checkin_screen.show_checkin_success_feedback(
                payment_generated=details.get("payment_generated", False),
                payment_amount=details.get("payment_amount", 0.0),
            )
            QMessageBox.information(self.window, "Check-in Realizado", msg)
            self.window.checkin_screen.clear_after_checkin()
            if self.window.stacked_widget.currentIndex() == 1:
                self.window._update_dashboard()
        else:
            QMessageBox.warning(self.window, "Atenção", message)

    def on_checkin_profile_clicked(self):
        member_id = self.window.checkin_screen.current_member_id
        if member_id is None:
            return

        member_data = self.window.search_service.get_member_by_id(member_id)
        if not member_data:
            return
        member_name = member_data.get("nome", "")
        self.window._show_members_list()
        self.window.members_list_screen.select_member_by_id(member_id, member_name)
