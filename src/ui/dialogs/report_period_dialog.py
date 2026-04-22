"""Diálogo para seleção de período dos relatórios."""

from datetime import date, timedelta
from typing import List, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QDateEdit, QFrame
)
from PyQt6.QtCore import Qt, QDate


# Presets de período: (label, timedelta em dias ou None para "desde sempre")
_PRESETS = [
    ("1 Semana", 7),
    ("1 Mês", 30),
    ("3 Meses", 90),
    ("6 Meses", 180),
    ("1 Ano", 365),
    ("5 Anos", 1825),
    ("Desde Sempre", None),
]


class ReportPeriodDialog(QDialog):
    """Diálogo para selecionar o período de geração de relatório."""

    def __init__(self, report_title: str = "Relatório", parent=None):
        super().__init__(parent)
        self._report_title = report_title
        self.setWindowTitle(f"Período — {report_title}")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setMaximumWidth(560)
        self._preset_buttons: List[QPushButton] = []
        self._setup_ui()

        # Padrão: último mês
        self._apply_preset(30)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(24, 24, 24, 24)

        # Título
        title = QLabel(f"📊 {self._report_title}")
        title.setObjectName("pageTitle")
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #1a2540;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Selecione o período de análise")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setStyleSheet("font-size: 13px; color: #718096;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # --- Preset buttons ---
        presets_label = QLabel("Períodos rápidos:")
        presets_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #1a2540;")
        layout.addWidget(presets_label)

        grid = QGridLayout()
        grid.setSpacing(8)
        for idx, (label, days) in enumerate(_PRESETS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(36)
            btn.setStyleSheet(self._preset_btn_style())
            btn.clicked.connect(lambda checked, d=days, b=btn: self._on_preset_clicked(d, b))
            row, col = divmod(idx, 4)
            grid.addWidget(btn, row, col)
            self._preset_buttons.append(btn)
        layout.addLayout(grid)

        # --- Separator ---
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #e2e8f0; margin: 4px 0;")
        layout.addWidget(sep)

        # --- Custom date pickers ---
        custom_label = QLabel("Ou defina datas manualmente:")
        custom_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #1a2540;")
        layout.addWidget(custom_label)

        dates_layout = QHBoxLayout()
        dates_layout.setSpacing(12)

        de_label = QLabel("De:")
        de_label.setStyleSheet("font-size: 13px; color: #4a5568;")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.start_date_edit.setStyleSheet(self._date_edit_style())
        self.start_date_edit.dateChanged.connect(self._on_custom_date_changed)

        ate_label = QLabel("Até:")
        ate_label.setStyleSheet("font-size: 13px; color: #4a5568;")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setStyleSheet(self._date_edit_style())
        self.end_date_edit.dateChanged.connect(self._on_custom_date_changed)

        dates_layout.addWidget(de_label)
        dates_layout.addWidget(self.start_date_edit, 1)
        dates_layout.addWidget(ate_label)
        dates_layout.addWidget(self.end_date_edit, 1)
        layout.addLayout(dates_layout)

        # --- Action buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setProperty("role", "danger")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)

        generate_btn = QPushButton("📄 Gerar Relatório")
        generate_btn.setProperty("role", "primary")
        generate_btn.setMinimumHeight(40)
        generate_btn.setDefault(True)
        generate_btn.setAutoDefault(True)
        generate_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(generate_btn)
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Preset logic
    # ------------------------------------------------------------------

    def _on_preset_clicked(self, days: Optional[int], clicked_btn: QPushButton):
        """Aplica um preset e marca o botão."""
        for btn in self._preset_buttons:
            btn.setChecked(btn is clicked_btn)
        self._apply_preset(days)

    def _apply_preset(self, days: Optional[int]):
        today = date.today()
        end = today
        if days is None:
            start = date(2000, 1, 1)
        else:
            start = today - timedelta(days=days)

        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        self.start_date_edit.setDate(QDate(start.year, start.month, start.day))
        self.end_date_edit.setDate(QDate(end.year, end.month, end.day))
        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)

    def _on_custom_date_changed(self):
        """Desmarca presets quando o usuário edita manualmente."""
        for btn in self._preset_buttons:
            btn.setChecked(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_period(self) -> Tuple[date, date]:
        """Retorna (start_date, end_date) selecionados."""
        qstart = self.start_date_edit.date()
        qend = self.end_date_edit.date()
        return (
            date(qstart.year(), qstart.month(), qstart.day()),
            date(qend.year(), qend.month(), qend.day()),
        )

    def get_period_label(self) -> str:
        """Retorna uma string legível do período selecionado."""
        start, end = self.get_period()
        return f"{start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}"

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    @staticmethod
    def _preset_btn_style() -> str:
        return """
            QPushButton {
                background-color: #ffffff;
                color: #4a5568;
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f0f4f8;
                color: #1a2540;
            }
            QPushButton:checked {
                background-color: rgba(230, 126, 34, 0.25);
                color: #E67E22;
                border: 2px solid #E67E22;
                font-weight: bold;
            }
        """

    @staticmethod
    def _date_edit_style() -> str:
        return """
            QDateEdit {
                padding: 8px;
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                font-size: 13px;
                background-color: #ffffff;
                color: #1a2540;
            }
            QDateEdit:focus {
                border: 1px solid #E67E22;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #cbd5e0;
            }
        """
