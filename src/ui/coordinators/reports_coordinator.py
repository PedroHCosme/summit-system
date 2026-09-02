"""Coordenação de relatórios na UI."""

from __future__ import annotations

import webbrowser

from PyQt6.QtWidgets import QDialog, QMessageBox

from src.reports.finance_report import generate_finance_report
from src.reports.members_report import generate_members_report
from src.ui.messages import show_error


class ReportsCoordinator:
    """Orquestra geração de relatórios sem acoplar lógica nas telas."""

    def __init__(self, window):
        self.window = window

    def generate_members_report(self):
        if not self.window.is_connected:
            return

        from src.ui.dialogs.report_period_dialog import ReportPeriodDialog

        dialog = ReportPeriodDialog("Relatório de Membros", self.window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        start_date, end_date = dialog.get_period()
        period_label = dialog.get_period_label()

        try:
            report_path = generate_members_report(
                start_date=start_date, end_date=end_date, period_label=period_label
            )
            webbrowser.open(f"file://{report_path}")
        except Exception as e:
            show_error(self.window, "Não foi possível gerar o relatório de membros. Tente novamente.", detail=e)

    def generate_financial_report(self):
        if not self.window.is_connected:
            return

        from src.ui.dialogs.report_period_dialog import ReportPeriodDialog

        dialog = ReportPeriodDialog("Relatório Financeiro", self.window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        start_date, end_date = dialog.get_period()
        period_label = dialog.get_period_label()

        try:
            report_path = generate_finance_report(
                period=period_label, start_date=start_date, end_date=end_date
            )
            webbrowser.open(f"file://{report_path}")
        except Exception as e:
            show_error(self.window, "Não foi possível gerar o relatório financeiro. Tente novamente.", detail=e)

    def generate_frequency_report(self):
        if not self.window.is_connected:
            QMessageBox.warning(
                self.window,
                "Banco Desconectado",
                "Conecte-se ao banco de dados antes de gerar relatórios.",
            )
            return

        from src.ui.dialogs.report_period_dialog import ReportPeriodDialog

        dialog = ReportPeriodDialog("Relatório de Frequência", self.window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        start_date, end_date = dialog.get_period()
        try:
            from src.reports.frequency_report import generate_frequency_report

            filepath = generate_frequency_report(start_date=start_date, end_date=end_date)
            webbrowser.open(f"file://{filepath}")
        except Exception as e:
            show_error(self.window, "Não foi possível gerar o relatório de frequência. Tente novamente.", detail=e)

    # === Financeiro ===

    def load_financial_data(self):
        """Carrega os dados financeiros com base no período selecionado rodando em background."""
        try:
            # Mostra estado de carregamento
            self.window.financial_screen.show_loading()

            # Obter datas
            start_date = self.window.financial_screen.start_date_input.date().toPyDate()
            end_date = self.window.financial_screen.end_date_input.date().toPyDate()

            # Converter para datetime com hora mínima/máxima
            from datetime import datetime, time
            start_datetime = datetime.combine(start_date, time.min)
            end_datetime = datetime.combine(end_date, time.max)

            # Instanciar e iniciar Worker para não travar a UI
            from src.ui.workers.financial_worker import FinancialDataWorker

            # Desativar botões ou evitar múltiplas requisições se necessário aqui
            self.window._financial_worker = FinancialDataWorker(
                self.window.manager.data_provider,
                start_datetime,
                end_datetime
            )

            self.window._financial_worker.data_loaded.connect(self.on_financial_data_loaded)
            self.window._financial_worker.error_occurred.connect(self.on_financial_data_error)

            # Iniciar thread
            self.window._financial_worker.start()

        except Exception as e:
            show_error(self.window, "Não foi possível carregar os dados financeiros. Tente novamente.", detail=e)

    def on_financial_data_loaded(self, result: dict):
        """Callback invocado quando o worker financeiro conclui com sucesso."""
        try:
            summary = result.get('summary', {})
            # Atualizar cards de resumo
            self.window.financial_screen.update_summary(
                summary.get('total_receita', 0.0),
                summary.get('total_transacoes', 0),
                summary.get('ticket_medio', 0.0)
            )

            breakdown = result.get('breakdown', {})
            self.window.financial_screen.update_breakdown(breakdown)

            transactions = result.get('transactions', [])
            self.window.financial_screen.update_transactions(transactions)

        except Exception as e:
            show_error(self.window, "Não foi possível exibir os dados financeiros. Tente novamente.", detail=e)

    def on_financial_data_error(self, error_msg: str):
        """Callback invocado quando o worker financeiro encontra erro."""
        show_error(self.window, "Não foi possível carregar os dados financeiros. Tente novamente.", detail=error_msg)

    def show_plan_distribution_dialog(self):
        """Abre o diálogo de gráficos financeiros."""
        from src.ui.dialogs.finance_graphs import FinancialGraphsDialog

        dialog = FinancialGraphsDialog(self.window)
        dialog.exec()
