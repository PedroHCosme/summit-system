"""Coordenação de fluxos de membros na UI."""

from __future__ import annotations

from datetime import datetime
import re
import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QMessageBox, QInputDialog

from src.ui.dialogs import AddMemberDialog
from src.ui.workers import MemberSearchWorker


class MembersCoordinator:
    """Orquestra operações de membros sem acoplar regras às telas."""

    def __init__(self, window):
        self.window = window

    def on_dashboard_member_clicked(self, member_id: int):
        from src.ui.components.sidebar import SidebarContext
        from src.data.data_provider import get_member_by_id

        if not self.window.is_connected:
            return

        try:
            member = get_member_by_id(member_id)
            if member:
                self.window.sidebar.set_context(SidebarContext.MEMBERS)
                self.window.stacked_widget.setCurrentIndex(3)
                self.window.member_search_screen.display_member_data(member)
            else:
                QMessageBox.warning(self.window, "Aviso", "Membro não encontrado.")
        except Exception as e:
            QMessageBox.critical(self.window, "Erro", f"Erro ao buscar membro: {e}")

    def on_member_search_by_name(self):
        search_term = self.window.member_search_screen.name_input.text().strip()
        if not search_term:
            self.window.member_search_screen.show_empty_search_warning()
            return

        self.window.member_search_screen.set_searching_state()
        self.window.worker = MemberSearchWorker(search_term)
        self.window.worker.search_completed.connect(self.on_member_search_completed)
        self.window.worker.status_updated.connect(
            lambda msg: self.window.home_screen.append_status(msg)
        )
        self.window.worker.start()

    # ------------------------------------------------------------------
    # Ações rápidas contextuais
    # ------------------------------------------------------------------

    def on_whatsapp_clicked(self):
        self._open_whatsapp_for_member(self.window.member_search_screen.current_member_data)

    def on_list_whatsapp_clicked(self):
        self._open_whatsapp_for_member(self.window.members_list_screen.current_member_data)

    def on_quick_payment_clicked(self):
        self._register_quick_payment(self.window.member_search_screen.current_member_data)

    def on_list_quick_payment_clicked(self):
        self._register_quick_payment(self.window.members_list_screen.current_member_data)

    def on_history_shortcut_clicked(self):
        self.window.member_search_screen.member_tabs.setCurrentIndex(1)

    def on_list_history_shortcut_clicked(self):
        self.window.members_list_screen.member_tabs.setCurrentIndex(1)

    def _open_whatsapp_for_member(self, member_data: dict | None):
        if not member_data:
            QMessageBox.warning(self.window, "Ação indisponível", "Selecione um membro primeiro.")
            return
        raw_phone = (member_data.get("whatsapp") or "").strip()
        digits = re.sub(r"\D", "", raw_phone)
        if not digits:
            QMessageBox.warning(
                self.window,
                "WhatsApp não encontrado",
                "Este membro não possui número de WhatsApp cadastrado.",
            )
            return
        if not digits.startswith("55"):
            digits = f"55{digits}"
        url = f"https://wa.me/{digits}"
        webbrowser.open(url)

    def _register_quick_payment(self, member_data: dict | None):
        if not member_data:
            QMessageBox.warning(self.window, "Ação indisponível", "Selecione um membro primeiro.")
            return

        tipos = [
            "Renovação Plano",
            "Treino",
            "Diária",
            "Gympass",
            "Totalpass",
            "Venda Produto",
            "Pagamento Manual",
        ]
        tipo, ok = QInputDialog.getItem(
            self.window,
            "Registrar Pagamento",
            "Tipo de transação:",
            tipos,
            editable=False,
        )
        if not ok:
            return

        valor, ok = QInputDialog.getDouble(
            self.window,
            "Registrar Pagamento",
            "Valor (R$):",
            0.0,
            0.0,
            999999.99,
            2,
        )
        if not ok:
            return
        if valor <= 0:
            QMessageBox.warning(self.window, "Valor inválido", "Informe um valor maior que zero.")
            return

        metodos = ["PIX", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Transferência"]
        metodo, ok = QInputDialog.getItem(
            self.window,
            "Registrar Pagamento",
            "Método de pagamento:",
            metodos,
            editable=False,
        )
        if not ok:
            return

        descricao, ok = QInputDialog.getText(
            self.window,
            "Registrar Pagamento",
            "Descrição (opcional):",
        )
        if not ok:
            return

        try:
            from src.data.db import create_session
            from src.services.payment_service import PaymentService

            session = create_session()
            try:
                payment_service = PaymentService(db_session=session)
                result = payment_service.create_payment(
                    member_id=member_data["id"],
                    valor=valor,
                    tipo_transacao=tipo,
                    descricao=descricao.strip() if descricao else "",
                    metodo_pagamento=metodo,
                )
            finally:
                session.close()

            if result.success:
                QMessageBox.information(
                    self.window,
                    "Pagamento Registrado",
                    f"Pagamento de R$ {valor:.2f} registrado para {member_data.get('nome', 'membro')}.",
                )
                member_id = member_data["id"]
                member_name = member_data.get("nome", "Membro")
                self.load_member_financial_history(member_id, member_name)
                self.load_list_member_financial_history(member_id, member_name)
            else:
                QMessageBox.warning(self.window, "Erro", result.message or "Não foi possível registrar o pagamento.")
        except Exception as e:
            QMessageBox.critical(self.window, "Erro", f"Falha ao registrar pagamento: {e}")

    def on_member_search_completed(self, results):
        if not results:
            self.window.member_search_screen.show_no_results()
        else:
            self.window.member_search_screen.populate_results(results)
        self.window.member_search_screen.set_ready_state()

    def on_member_result_clicked(self, item):
        member_id = item.data(Qt.ItemDataRole.UserRole)
        member_data = self.window.search_service.get_member_by_id(member_id)

        if member_data:
            self.window.member_search_screen.display_member_data(member_data)
            self.load_member_history(member_id, member_data.get("nome", "Membro"))
            self.load_member_financial_history(member_id, member_data.get("nome", "Membro"))
        else:
            self.window.member_search_screen.show_error()

    def load_member_history(self, member_id: int, member_name: str):
        try:
            from src.data.data_provider import get_member_checkin_history

            history = get_member_checkin_history(member_id)
            self.window.member_search_screen.display_member_history(
                member_id, member_name, history
            )
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            self.window.member_search_screen.member_history_browser.setHtml(
                f"""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #FF6B6B;">Erro ao carregar histórico</h3>
                    <p style="color: #888;">{str(e)}</p>
                </div>
                """
            )

    def load_member_financial_history(self, member_id: int, member_name: str):
        try:
            from src.data.data_provider import get_provider

            provider = get_provider()
            payments = provider.get_member_payment_history(member_id)
            self.window.member_search_screen.display_member_financial_history(
                member_id, member_name, payments
            )
        except Exception as e:
            print(f"Erro ao carregar histórico financeiro: {e}")
            import traceback

            traceback.print_exc()
            self.window.member_search_screen.member_financial_browser.setHtml(
                f"""
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: #FF6B6B;">Erro ao carregar histórico financeiro</h3>
                    <p style="color: #888;">{str(e)}</p>
                </div>
                """
            )

    def on_edit_member_clicked(self):
        if not self.window.member_search_screen.current_member_data:
            return
        from src.ui.dialogs.edit_member_dialog import EditMemberDialog

        dialog = EditMemberDialog(self.window.member_search_screen.current_member_data, self.window)
        dialog.member_updated.connect(self.on_member_updated)
        dialog.exec()

    def on_renew_plan_clicked(self):
        if not self.window.member_search_screen.current_member_data:
            return
        from src.ui.dialogs.renew_plan_dialog import RenewPlanDialog

        dialog = RenewPlanDialog(self.window.member_search_screen.current_member_data, self.window)
        dialog.plan_renewed.connect(self.on_plan_renewed)
        dialog.exec()

    def on_delete_member_clicked(self):
        if not self.window.member_search_screen.current_member_data:
            return
        from src.ui.dialogs.delete_member_dialog import DeleteMemberDialog

        dialog = DeleteMemberDialog(self.window.member_search_screen.current_member_data, self.window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.delete_member(self.window.member_search_screen.current_member_data)

    def delete_member(self, member_data: dict):
        try:
            from src.data.data_provider import delete_member

            member_id = member_data["id"]
            member_name = member_data["nome"]
            success = delete_member(member_id)

            if success:
                QMessageBox.information(
                    self.window,
                    "Sucesso",
                    f"Membro '{member_name}' foi excluído com sucesso!\n\n"
                    "Todos os check-ins e pagamentos relacionados também foram removidos.",
                )
                self.window.member_search_screen.results_list.clear()
                self.window.member_search_screen.member_result_browser.setHtml(
                    self.window.member_search_screen._get_initial_message()
                )
                self.window.member_search_screen.member_history_browser.setHtml(
                    "<p style='color: #888888;'>Selecione um membro para ver o histórico.</p>"
                )
                self.window.member_search_screen.edit_button.setVisible(False)
                self.window.member_search_screen.delete_button.setVisible(False)
                self.window.member_search_screen.current_member_data = None
            else:
                QMessageBox.warning(
                    self.window, "Erro", f"Não foi possível excluir o membro '{member_name}'."
                )
        except Exception as e:
            QMessageBox.critical(self.window, "Erro", f"Erro ao excluir membro: {str(e)}")

    def on_member_updated(self, updated_data: dict):
        try:
            from src.data.data_provider import update_member

            metodo_pagamento = updated_data.pop("metodo_pagamento", "")
            register_payment = bool(metodo_pagamento)

            success = update_member(
                updated_data,
                register_payment=register_payment,
                metodo_pagamento=metodo_pagamento,
            )

            if success:
                mensagem = f"Membro '{updated_data['nome']}' atualizado com sucesso!"
                if register_payment:
                    mensagem += "\n\n💰 Pagamento registrado no sistema financeiro."
                QMessageBox.information(self.window, "Sucesso", mensagem)

                member_id = updated_data["id"]
                updated_member = self.window.search_service.get_member_by_id(member_id)
                if updated_member:
                    self.window.member_search_screen.display_member_data(updated_member)
                    if register_payment:
                        from src.data.data_provider import get_provider

                        provider = get_provider()
                        payments = provider.get_member_payment_history(member_id)
                        self.window.member_search_screen.display_member_financial_history(
                            member_id, updated_data["nome"], payments
                        )
            else:
                QMessageBox.warning(
                    self.window, "Erro", "Não foi possível atualizar o membro. Verifique o console."
                )
        except Exception as e:
            QMessageBox.critical(self.window, "Erro Crítico", f"Ocorreu um erro inesperado: {e}")

    def on_plan_renewed(self, renewal_data: dict):
        try:
            from src.data.data_provider import update_member
            from src.services.plan_service import get_plan_service

            metodo_pagamento = renewal_data.pop("metodo_pagamento", "")
            current_data = self.window.member_search_screen.current_member_data
            member_name = current_data.get("nome", "") if current_data else ""

            success = update_member(
                renewal_data,
                register_payment=True,
                metodo_pagamento=metodo_pagamento,
            )

            if success:
                valor = get_plan_service().get_plan_price(renewal_data.get("plano", ""))
                mensagem = "Plano renovado com sucesso!"
                mensagem += f"\n\n💰 Pagamento de R$ {valor:.2f} registrado no sistema financeiro."
                mensagem += f"\n📅 Novo vencimento: {renewal_data.get('vencimento_plano', 'N/A')}"
                QMessageBox.information(self.window, "Sucesso", mensagem)

                member_id = renewal_data["id"]
                updated_member = self.window.search_service.get_member_by_id(member_id)
                if updated_member:
                    self.window.member_search_screen.display_member_data(updated_member)
                    from src.data.data_provider import get_provider

                    provider = get_provider()
                    payments = provider.get_member_payment_history(member_id)
                    self.window.member_search_screen.display_member_financial_history(
                        member_id, member_name, payments
                    )
            else:
                QMessageBox.warning(
                    self.window, "Erro", "Não foi possível renovar o plano. Verifique o console."
                )
        except Exception as e:
            QMessageBox.critical(self.window, "Erro Crítico", f"Ocorreu um erro inesperado: {e}")

    def on_delete_checkin_requested(self, checkin_id: int):
        reply = QMessageBox.question(
            self.window,
            "Confirmar Exclusão",
            "Tem certeza que deseja deletar este check-in?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from src.data.data_provider import delete_checkin

            success = delete_checkin(checkin_id)
            if success:
                QMessageBox.information(self.window, "Sucesso", "Check-in deletado com sucesso!")
                if self.window.member_search_screen.current_member_data:
                    member_id = self.window.member_search_screen.current_member_data["id"]
                    member_name = self.window.member_search_screen.current_member_data["nome"]
                    self.load_member_history(member_id, member_name)
            else:
                QMessageBox.warning(
                    self.window, "Erro", "Não foi possível deletar o check-in. Verifique o console."
                )
        except Exception as e:
            QMessageBox.critical(self.window, "Erro", f"Erro ao deletar check-in: {str(e)}")

    def on_edit_checkin_requested(self, checkin_id: int):
        try:
            from src.data.data_provider import get_provider, update_checkin_datetime
            from src.ui.dialogs import EditCheckinDialog

            provider = get_provider()
            if not self.window.member_search_screen.current_member_data:
                QMessageBox.warning(self.window, "Erro", "Nenhum membro selecionado.")
                return

            member_id = self.window.member_search_screen.current_member_data["id"]
            member_name = self.window.member_search_screen.current_member_data["nome"]
            history = provider.get_member_checkin_history(member_id)
            checkin_data = next((c for c in history if c["id"] == checkin_id), None)

            if not checkin_data:
                QMessageBox.warning(self.window, "Erro", "Check-in não encontrado.")
                return

            current_datetime = datetime.fromisoformat(checkin_data["checkin_datetime"])
            dialog = EditCheckinDialog(checkin_id, current_datetime, member_name, self.window)

            def on_checkin_updated(cid: int, new_dt: datetime):
                success = update_checkin_datetime(cid, new_dt)
                if success:
                    QMessageBox.information(
                        self.window, "Sucesso", "Horário do check-in atualizado com sucesso!"
                    )
                    self.load_member_history(member_id, member_name)
                else:
                    QMessageBox.warning(
                        self.window,
                        "Erro",
                        "Não foi possível atualizar o check-in. Verifique o console.",
                    )

            dialog.checkin_updated.connect(on_checkin_updated)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self.window, "Erro", f"Erro ao editar check-in: {str(e)}")

    def show_add_member_dialog(self):
        if not self.window.is_connected:
            QMessageBox.warning(
                self.window, "Aviso", "A conexão com o banco de dados ainda não foi estabelecida."
            )
            return

        dialog = AddMemberDialog(self.window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        member_data = dialog.get_data()
        required_fields = ["nome", "plano", "data_nascimento", "whatsapp", "genero"]
        for field in required_fields:
            if not member_data.get(field):
                QMessageBox.warning(
                    self.window,
                    "Campo Obrigatório",
                    f"O campo '{field.replace('_', ' ').title()}' é obrigatório.",
                )
                return

        try:
            from src.data.data_provider import add_member

            new_id = add_member(member_data)
            if new_id:
                QMessageBox.information(
                    self.window, "Sucesso", f"Membro '{member_data['nome']}' adicionado com sucesso!"
                )
            else:
                QMessageBox.critical(
                    self.window,
                    "Erro",
                    "Não foi possível adicionar o membro. Verifique o console.",
                )
        except Exception as e:
            QMessageBox.critical(
                self.window,
                "Erro Crítico",
                f"Ocorreu um erro inesperado ao salvar o membro: {e}",
            )

    def load_members_list(self):
        from src.services.plan_service import get_plan_service

        plan_service = get_plan_service()
        self.window.members_list_screen.populate_plan_filter(plan_service.get_plan_names())
        self.on_members_list_refresh()

    def on_members_list_refresh(self):
        from src.data.data_provider import get_provider

        provider = get_provider()
        filters = self.window.members_list_screen.get_filters()
        data = provider.get_members_paginated(
            page=self.window.members_list_screen.current_page,
            page_size=self.window.members_list_screen.page_size,
            filter_text=filters["text"],
            filter_plan=filters["plan"],
            filter_status=filters["status"],
            sort_by=filters.get("sort_by", "nome"),
            sort_dir=filters.get("sort_dir", "asc"),
        )
        self.window.members_list_screen.update_data(data)

    def on_members_list_member_selected(self, member_data: dict):
        full_member_data = self.window.search_service.get_member_by_id(member_data["id"])
        if full_member_data:
            self.window.members_list_screen.display_member_data(full_member_data)
            self.load_list_member_history(full_member_data["id"], full_member_data["nome"])
            self.load_list_member_financial_history(full_member_data["id"], full_member_data["nome"])

    def load_list_member_history(self, member_id: int, member_name: str):
        try:
            from src.data.data_provider import get_member_checkin_history

            history = get_member_checkin_history(member_id)
            self.window.members_list_screen.display_member_history(history)
        except Exception as e:
            print(f"Erro ao carregar histórico na lista: {e}")

    def load_list_member_financial_history(self, member_id: int, member_name: str):
        try:
            from src.data.data_provider import get_provider

            provider = get_provider()
            if provider:
                payments = provider.get_member_payment_history(member_id)
                self.window.members_list_screen.display_member_financial_history(payments)
        except Exception as e:
            print(f"Erro ao carregar histórico financeiro na lista: {e}")

    def on_list_edit_member_clicked(self):
        if not self.window.members_list_screen.current_member_data:
            return
        from src.ui.dialogs.edit_member_dialog import EditMemberDialog

        dialog = EditMemberDialog(self.window.members_list_screen.current_member_data, self.window)
        dialog.member_updated.connect(self.on_list_member_updated)
        dialog.exec()

    def on_list_renew_plan_clicked(self):
        if not self.window.members_list_screen.current_member_data:
            return
        from src.ui.dialogs.renew_plan_dialog import RenewPlanDialog

        dialog = RenewPlanDialog(self.window.members_list_screen.current_member_data, self.window)
        dialog.plan_renewed.connect(self.on_list_plan_renewed)
        dialog.exec()

    def on_list_delete_member_clicked(self):
        if not self.window.members_list_screen.current_member_data:
            return
        from src.ui.dialogs.delete_member_dialog import DeleteMemberDialog

        dialog = DeleteMemberDialog(self.window.members_list_screen.current_member_data, self.window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.delete_list_member(self.window.members_list_screen.current_member_data)

    def on_list_member_updated(self, updated_data: dict):
        self.on_member_updated(updated_data)
        full_data = self.window.search_service.get_member_by_id(updated_data["id"])
        if full_data:
            self.window.members_list_screen.display_member_data(full_data)
            self.load_members_list()

    def on_list_plan_renewed(self, renewal_data: dict):
        self.on_plan_renewed(renewal_data)
        full_data = self.window.search_service.get_member_by_id(renewal_data["id"])
        if full_data:
            self.window.members_list_screen.display_member_data(full_data)
            self.load_list_member_financial_history(full_data["id"], full_data["nome"])
            self.load_members_list()

    def delete_list_member(self, member_data: dict):
        try:
            from src.data.data_provider import delete_member

            member_id = member_data["id"]
            member_name = member_data["nome"]
            success = delete_member(member_id)
            if success:
                QMessageBox.information(
                    self.window, "Sucesso", f"Membro '{member_name}' foi excluído com sucesso!"
                )
                self.load_members_list()
                self.window.members_list_screen.details_browser.setHtml(
                    "<div style='text-align: center; color: #666; margin-top: 20px;'>Selecione um membro para ver os detalhes</div>"
                )
                self.window.members_list_screen.history_browser.clear()
                self.window.members_list_screen.financial_browser.clear()
                self.window.members_list_screen.edit_button.setVisible(False)
                self.window.members_list_screen.renew_button.setVisible(False)
                self.window.members_list_screen.delete_button.setVisible(False)
                self.window.members_list_screen.current_member_data = None
            else:
                QMessageBox.warning(
                    self.window, "Erro", f"Não foi possível excluir o membro '{member_name}'."
                )
        except Exception as e:
            QMessageBox.critical(self.window, "Erro", f"Erro ao excluir membro: {str(e)}")
