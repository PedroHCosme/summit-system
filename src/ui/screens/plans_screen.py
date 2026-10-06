"""Tela de gerenciamento de planos – layout Cards & Editor Lateral."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDoubleSpinBox, QSpinBox, QCheckBox, QScrollArea,
    QGridLayout, QFrame, QMessageBox, QSizePolicy, QButtonGroup,
    QRadioButton, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.data.data_provider import get_provider
from src.data.models import Plano
from src.ui.messages import show_error


# ---------------------------------------------------------------------------
# PlanCard – widget individual para cada plano
# ---------------------------------------------------------------------------

class PlanCard(QFrame):
    """Card visual para um plano."""

    clicked = pyqtSignal(object)  # emits Plano

    # Cores por tipo
    COLOR_TIME = "#007ACC"
    COLOR_QUOTA = "#E67E22"

    def __init__(self, plano: Plano, parent=None):
        """Inicializa o card visual de um plano."""
        super().__init__(parent)
        self.plano = plano
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(200, 150)
        self._build()

    def _build(self):
        """Monta os elementos visuais do card."""
        border_color = self.COLOR_QUOTA if self.plano.is_quota else self.COLOR_TIME
        self._border_color = border_color
        self._apply_style(selected=False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Tipo badge
        tipo = "Quota" if self.plano.is_quota else "Tempo"
        emoji = "🟠" if self.plano.is_quota else "🔵"
        badge = QLabel(f"{emoji} {tipo}")
        badge.setStyleSheet(f"color: {border_color}; font-size: 11px; font-weight: bold;")
        layout.addWidget(badge)

        # Nome
        name_label = QLabel(self.plano.nome)
        name_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #222;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # Preço
        preco = self.plano.preco or 0
        price_label = QLabel(f"R$ {preco:,.2f}")
        price_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        price_label.setStyleSheet(f"color: {border_color};")
        layout.addWidget(price_label)

        # Info extra
        if self.plano.is_quota and self.plano.quota_amount:
            extra = QLabel(f"{self.plano.quota_amount} aulas")
            extra.setStyleSheet("color: #888; font-size: 11px;")
            layout.addWidget(extra)
        elif self.plano.valor_por_checkin and self.plano.valor_por_checkin > 0:
            extra = QLabel(f"R$ {self.plano.valor_por_checkin:.2f}/check-in")
            extra.setStyleSheet("color: #888; font-size: 11px;")
            layout.addWidget(extra)

        layout.addStretch()

    def _apply_style(self, selected: bool):
        """Aplica o estilo do card conforme estado de seleção."""
        border_color = self._border_color if hasattr(self, '_border_color') else "#ccc"
        bg = "#EBF5FB" if selected and not getattr(self, 'plano', None) or False else "#FFFFFF"
        if selected:
            bg = "#EBF5FB" if border_color == self.COLOR_TIME else "#FDF2E9"
        self.setStyleSheet(f"""
            PlanCard {{
                background-color: {bg};
                border: 2px solid {border_color};
                border-radius: 10px;
            }}
            PlanCard:hover {{
                border-width: 3px;
            }}
        """)

    def set_selected(self, selected: bool):
        """Marca o card como selecionado ou não selecionado."""
        self._selected = selected
        self._apply_style(selected)

    def mousePressEvent(self, event):
        """Emite o plano selecionado ao clicar no card."""
        self.clicked.emit(self.plano)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# PlansScreen – tela principal
# ---------------------------------------------------------------------------

class PlansScreen(QWidget):
    """Tela de Catálogo de Planos com editor lateral."""

    plans_updated = pyqtSignal()

    def __init__(self, parent=None):
        """Inicializa a tela de catálogo de planos."""
        super().__init__(parent)
        self._cards: list[PlanCard] = []
        self._current_plano: Plano | None = None
        self._is_new = False
        self._setup_ui()

    def _setup_ui(self):
        """Cria layout principal com grade de cards e painel editor."""
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 10)
        root.setSpacing(10)

        # Título
        title = QLabel("💳 Catálogo de Planos")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #333;")
        root.addWidget(title)

        subtitle = QLabel("Clique em um card para editar. Planos 🔵 são por tempo, planos 🟠 são por quota/voucher.")
        subtitle.setStyleSheet("color: #777; font-size: 13px; margin-bottom: 5px;")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        # Corpo: cards + editor
        body = QHBoxLayout()
        body.setSpacing(20)

        # ---- ESQUERDA: grade de cards ----
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QWidget#cardsContainer { background: transparent; }
        """)

        self._cards_container = QWidget()
        self._cards_container.setObjectName("cardsContainer")
        self._cards_grid = QGridLayout(self._cards_container)
        self._cards_grid.setSpacing(14)
        self._cards_grid.setContentsMargins(0, 0, 0, 0)
        self._scroll.setWidget(self._cards_container)

        left_panel.addWidget(self._scroll)

        # Botões inferiores (novo + restaurar)
        left_buttons = QHBoxLayout()
        self._btn_new = QPushButton("➕ Novo Plano")
        self._btn_new.setFixedHeight(40)
        self._btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_new.setStyleSheet("""
            QPushButton {
                background-color: #007ACC; color: white; font-weight: bold;
                font-size: 13px; border: none; border-radius: 6px; padding: 8px 18px;
            }
            QPushButton:hover { background-color: #005FA3; }
        """)
        self._btn_new.clicked.connect(self._on_new_plan)
        left_buttons.addWidget(self._btn_new)

        self._btn_restore = QPushButton("🔄 Restaurar Padrões")
        self._btn_restore.setFixedHeight(40)
        self._btn_restore.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_restore.setStyleSheet("""
            QPushButton {
                background-color: #FFA726; color: white; font-weight: bold;
                font-size: 13px; border: none; border-radius: 6px; padding: 8px 18px;
            }
            QPushButton:hover { background-color: #FB8C00; }
        """)
        self._btn_restore.clicked.connect(self._on_restore_defaults)
        left_buttons.addWidget(self._btn_restore)

        left_buttons.addStretch()
        left_panel.addLayout(left_buttons)

        body.addLayout(left_panel, 3)

        # ---- DIREITA: editor ----
        self._editor = self._build_editor()
        body.addWidget(self._editor, 2)

        root.addLayout(body)

    def _build_editor(self) -> QFrame:
        """Cria o painel lateral de edição/criação de planos."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame#editorFrame {
                background-color: #FAFAFA;
                border: 1px solid #DDD;
                border-radius: 10px;
            }
        """)
        frame.setObjectName("editorFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Título do editor
        self._editor_title = QLabel("Selecione um plano")
        self._editor_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._editor_title.setStyleSheet("color: #333;")
        layout.addWidget(self._editor_title)

        # Nome
        layout.addWidget(self._make_label("Nome do Plano"))
        self._input_nome = QLineEdit()
        self._input_nome.setPlaceholderText("Ex: Mensal, Trimestral, Voucher...")
        self._input_nome.setMinimumHeight(36)
        self._input_nome.setStyleSheet(self._input_style())
        layout.addWidget(self._input_nome)

        # Tipo (radio)
        layout.addWidget(self._make_label("Tipo do Plano"))
        type_layout = QHBoxLayout()
        self._radio_time = QRadioButton("🔵 Tempo (Mensal, Trimestral...)")
        self._radio_quota = QRadioButton("🟠 Quota (Voucher, Pacote...)")
        self._radio_time.setStyleSheet("font-size: 13px; color: #333;")
        self._radio_quota.setStyleSheet("font-size: 13px; color: #333;")
        self._type_group = QButtonGroup(self)
        self._type_group.addButton(self._radio_time, 0)
        self._type_group.addButton(self._radio_quota, 1)
        self._radio_time.setChecked(True)
        self._radio_time.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self._radio_time)
        type_layout.addWidget(self._radio_quota)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Preço de renovação
        layout.addWidget(self._make_label("Preço de Renovação"))
        self._input_preco = QDoubleSpinBox()
        self._input_preco.setRange(0, 99999)
        self._input_preco.setDecimals(2)
        self._input_preco.setPrefix("R$ ")
        self._input_preco.setSingleStep(10)
        self._input_preco.setMinimumHeight(36)
        self._input_preco.setStyleSheet(self._spin_style())
        layout.addWidget(self._input_preco)

        # Valor por check-in
        layout.addWidget(self._make_label("Valor por Check-in"))
        self._input_checkin = QDoubleSpinBox()
        self._input_checkin.setRange(0, 9999)
        self._input_checkin.setDecimals(2)
        self._input_checkin.setPrefix("R$ ")
        self._input_checkin.setSingleStep(5)
        self._input_checkin.setMinimumHeight(36)
        self._input_checkin.setStyleSheet(self._spin_style())
        layout.addWidget(self._input_checkin)

        # Requer vencimento (só para Tempo)
        self._check_vencimento = QCheckBox("Requer data de vencimento")
        self._check_vencimento.setStyleSheet("font-size: 13px; color: #333; padding: 4px;")
        self._lbl_vencimento = self._make_label("Vencimento")
        layout.addWidget(self._lbl_vencimento)
        layout.addWidget(self._check_vencimento)

        # Quota amount (só para Quota)
        self._lbl_quota = self._make_label("Quantidade de Aulas")
        layout.addWidget(self._lbl_quota)
        self._input_quota = QSpinBox()
        self._input_quota.setRange(0, 999)
        self._input_quota.setSuffix(" aulas")
        self._input_quota.setMinimumHeight(36)
        self._input_quota.setStyleSheet(self._spin_style())
        layout.addWidget(self._input_quota)

        layout.addStretch()

        # Botões do editor
        btn_row = QHBoxLayout()

        self._btn_save = QPushButton("💾 Salvar")
        self._btn_save.setFixedHeight(42)
        self._btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_save.setStyleSheet("""
            QPushButton {
                background-color: #28A745; color: white; font-weight: bold;
                font-size: 14px; border: none; border-radius: 6px; padding: 8px 24px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self._btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(self._btn_save)

        self._btn_deactivate = QPushButton("🗑 Desativar")
        self._btn_deactivate.setFixedHeight(42)
        self._btn_deactivate.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_deactivate.setStyleSheet("""
            QPushButton {
                background-color: #DC3545; color: white; font-weight: bold;
                font-size: 14px; border: none; border-radius: 6px; padding: 8px 24px;
            }
            QPushButton:hover { background-color: #C82333; }
        """)
        self._btn_deactivate.clicked.connect(self._on_deactivate)
        btn_row.addWidget(self._btn_deactivate)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Iniciar com editor desabilitado
        self._set_editor_enabled(False)

        return frame

    def refresh(self):
        """Recarrega os planos do banco e reconstrói os cards."""
        plan_service = get_provider().plan_service
        plan_service.invalidate_cache()

        try:
            planos = sorted(plan_service.get_all_plans(), key=lambda p: p.nome)
        except Exception as e:
            show_error(self, "Não foi possível carregar os planos. Tente novamente.", detail=e)
            return

        self._cards.clear()
        while self._cards_grid.count():
            item = self._cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        col_count = 3
        for i, plano in enumerate(planos):
            card = PlanCard(plano)
            card.clicked.connect(self._on_card_clicked)
            self._cards_grid.addWidget(card, i // col_count, i % col_count)
            self._cards.append(card)

        if self._current_plano:
            for card in self._cards:
                if card.plano.id == self._current_plano.id:
                    card.set_selected(True)
                    self._current_plano = card.plano
                    self._populate_editor(card.plano)
                    break
            else:
                self._clear_editor()

    def _on_card_clicked(self, plano: Plano):
        """Seleciona um plano e carrega seus dados no editor."""
        self._is_new = False
        self._current_plano = plano

        for card in self._cards:
            card.set_selected(card.plano.id == plano.id)

        self._populate_editor(plano)
        self._set_editor_enabled(True)
        self._btn_deactivate.setEnabled(True)
        self._editor_title.setText(f"Editando: {plano.nome}")

    def _populate_editor(self, plano: Plano):
        """Preenche o editor com os dados de um plano existente."""
        self._input_nome.setText(plano.nome)
        self._input_preco.setValue(plano.preco or 0)
        self._input_checkin.setValue(plano.valor_por_checkin or 0)
        self._check_vencimento.setChecked(plano.requer_vencimento)
        self._input_quota.setValue(plano.quota_amount or 0)

        if plano.is_quota:
            self._radio_quota.setChecked(True)
        else:
            self._radio_time.setChecked(True)

        self._on_type_changed()

    def _clear_editor(self):
        """Limpa o editor e remove seleção de cards."""
        self._current_plano = None
        self._is_new = False
        self._input_nome.clear()
        self._input_preco.setValue(0)
        self._input_checkin.setValue(0)
        self._check_vencimento.setChecked(False)
        self._input_quota.setValue(0)
        self._radio_time.setChecked(True)
        self._on_type_changed()
        self._set_editor_enabled(False)
        self._editor_title.setText("Selecione um plano")

        for card in self._cards:
            card.set_selected(False)

    def _set_editor_enabled(self, enabled: bool):
        """Habilita ou desabilita todos os controles de edição."""
        self._input_nome.setEnabled(enabled)
        self._input_preco.setEnabled(enabled)
        self._input_checkin.setEnabled(enabled)
        self._check_vencimento.setEnabled(enabled)
        self._input_quota.setEnabled(enabled)
        self._radio_time.setEnabled(enabled)
        self._radio_quota.setEnabled(enabled)
        self._btn_save.setEnabled(enabled)
        self._btn_deactivate.setEnabled(enabled and not self._is_new)

    def _on_type_changed(self):
        """Adapta campos visíveis conforme o tipo selecionado."""
        is_quota = self._radio_quota.isChecked()

        self._lbl_quota.setVisible(is_quota)
        self._input_quota.setVisible(is_quota)

        self._lbl_vencimento.setVisible(not is_quota)
        self._check_vencimento.setVisible(not is_quota)

    def _on_new_plan(self):
        """Prepara o editor para criação de um novo plano."""
        self._clear_editor()
        self._is_new = True
        self._set_editor_enabled(True)
        self._btn_deactivate.setEnabled(False)
        self._editor_title.setText("✨ Novo Plano")
        self._input_nome.setFocus()

    def _on_save(self):
        """Salva criação/edição do plano atual com validações de nome único."""
        nome = self._input_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Campo Obrigatório", "O nome do plano é obrigatório.")
            return

        is_quota = self._radio_quota.isChecked()
        plan_service = get_provider().plan_service

        try:
            if self._is_new:
                existing = plan_service.find_by_name_any_status(nome)
                if existing:
                    if not existing.ativo:
                        reply = QMessageBox.question(
                            self, "Plano Existente",
                            f"O plano '{nome}' existe mas está desativado.\n"
                            "Deseja reativá-lo com os novos dados?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        if reply != QMessageBox.StandardButton.Yes:
                            return
                        plano = existing
                        plano.ativo = True
                    else:
                        QMessageBox.warning(self, "Duplicata", f"Já existe um plano ativo com o nome '{nome}'.")
                        return
                else:
                    plano = Plano(nome=nome, ativo=True)
                    plan_service.add(plano)
            else:
                plano = self._current_plano
                if not plano:
                    return
                plano.nome = nome

            plano.preco = self._input_preco.value()
            plano.valor_por_checkin = self._input_checkin.value()
            plano.is_quota = is_quota
            plano.quota_amount = self._input_quota.value() if is_quota else 0
            plano.requer_vencimento = self._check_vencimento.isChecked() if not is_quota else False

            plan_service.commit()

            QMessageBox.information(self, "Salvo", f"Plano '{nome}' salvo com sucesso!")

            self._current_plano = plano
            self._is_new = False
            self.plans_updated.emit()
            self.refresh()

        except Exception as e:
            plan_service.rollback()
            show_error(self, "Não foi possível salvar o plano. Tente novamente.", detail=e, title="Erro ao salvar")

    def _on_deactivate(self):
        """Desativa o plano selecionado sem removê-lo fisicamente."""
        if not self._current_plano:
            return

        nome = self._current_plano.nome
        reply = QMessageBox.question(
            self, "Desativar Plano",
            f"Deseja realmente desativar o plano '{nome}'?\n\n"
            "O plano não será excluído, apenas ficará invisível.\n"
            "Membros existentes com este plano não serão afetados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        plan_service = get_provider().plan_service

        try:
            plano = plan_service.get_by_id(self._current_plano.id)
            if plano:
                plano.ativo = False
                plan_service.commit()

                QMessageBox.information(self, "Desativado", f"Plano '{nome}' desativado.")
                self._clear_editor()
                self.plans_updated.emit()
                self.refresh()

        except Exception as e:
            plan_service.rollback()
            show_error(self, "Não foi possível desativar o plano. Tente novamente.", detail=e)

    def _on_restore_defaults(self):
        """Restaura o catálogo para os valores padrão definidos em configuração."""
        reply = QMessageBox.question(
            self, "Restaurar Padrões",
            "Deseja restaurar todos os planos para os valores padrão?\n\n"
            "Planos existentes serão atualizados. Esta ação não pode ser desfeita!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from src import config
            import importlib
            importlib.reload(config)

            plan_service = get_provider().plan_service
            default_vencimento = config.PLANOS_COM_VENCIMENTO

            plans_data = [
                {
                    "nome": name,
                    "preco": config.PLANOS_PRECOS.get(name, 0),
                    "valor_por_checkin": config.PLANOS_PAGAMENTO_POR_CHECKIN.get(name, 0),
                    "requer_vencimento": name in default_vencimento,
                }
                for name in config.PLANOS
            ]
            plan_service.upsert_plans(plans_data)

            QMessageBox.information(self, "Restaurado", "Planos restaurados para os valores padrão!")

            self._clear_editor()
            self.plans_updated.emit()
            self.refresh()

        except Exception as e:
            show_error(self, "Não foi possível restaurar os planos padrão. Tente novamente.", detail=e)

    @staticmethod
    def _make_label(text: str) -> QLabel:
        """Cria um label padrão para campos do editor."""
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #555; margin-top: 4px;")
        return lbl

    @staticmethod
    def _input_style() -> str:
        """Retorna estilo padrão de campos de texto."""
        return """
            QLineEdit {
                font-size: 14px; padding: 8px 10px;
                border: 1px solid #CCC; border-radius: 6px;
                background: #FFF;
            }
            QLineEdit:focus { border-color: #007ACC; }
        """

    @staticmethod
    def _spin_style() -> str:
        """Retorna estilo padrão de campos numéricos."""
        return """
            QDoubleSpinBox, QSpinBox {
                font-size: 14px; padding: 8px 10px;
                border: 1px solid #CCC; border-radius: 6px;
                background: #FFF;
            }
            QDoubleSpinBox:focus, QSpinBox:focus { border-color: #007ACC; }
        """
