"""Coordenação de relatórios na UI."""

from __future__ import annotations

import webbrowser

from PyQt6.QtWidgets import QDialog, QMessageBox

from src.reports.finance_report import generate_finance_report
from src.reports.members_report import generate_members_report


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
            QMessageBox.critical(
                self.window, "Erro", f"Erro ao gerar relatório de membros: {e}"
            )

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
            QMessageBox.critical(
                self.window, "Erro", f"Erro ao gerar relatório financeiro: {e}"
            )

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
            QMessageBox.critical(self.window, "Erro", f"Erro ao gerar relatório de frequência: {e}")
