"""
Tela de Bloco de Notas.

Permite ao usuário criar, editar, excluir notas (bugs, ideias, sugestões)
e enviá-las por e-mail ao desenvolvedor.
"""

from datetime import datetime
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QListWidget, QListWidgetItem,
    QFrame, QMessageBox, QSplitter, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from src.data.db import create_session
from src.data.models import Nota
from src.ui.messages import show_error


# ── Constantes ─────────────────────────────────────────────────────────
_TIPO_OPTIONS = [
    ("🐛 Bug / Erro", "bug"),
    ("💡 Ideia / Sugestão", "ideia"),
    ("📝 Outro", "outro"),
]

_TIPO_ICONS = {"bug": "🐛", "ideia": "💡", "outro": "📝"}


# ── NoteListItem ───────────────────────────────────────────────────────
class _NoteListItem(QListWidgetItem):
    """Item customizado que carrega o id da nota."""

    def __init__(self, nota: Nota):
        icon = _TIPO_ICONS.get(nota.tipo, "📝")
        label = f"{icon}  {nota.titulo}"
        super().__init__(label)
        self.nota_id = nota.id
        self.setSizeHint(QSize(0, 42))

        # Texto secundário com data
        if nota.created_at:
            date_str = nota.created_at.strftime("%d/%m/%Y %H:%M")
        else:
            date_str = ""
        sent_mark = "  ✅" if nota.enviada else ""
        self.setToolTip(f"Criada em {date_str}{sent_mark}")


# ── NotesScreen ────────────────────────────────────────────────────────
class NotesScreen(QWidget):
    """Tela principal do Bloco de Notas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_nota_id: Optional[int] = None
        self._dirty = False
        self._setup_ui()

    # ── UI ─────────────────────────────────────────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QWidget {
                background-color: #1a2540;
                border-bottom: 2px solid #E67E22;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 0, 25, 0)

        title = QLabel("📝 Bloco de Notas")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #fff; border: none;")
        header_layout.addWidget(title)

        subtitle = QLabel("Registre erros, ideias e sugestões")
        subtitle.setStyleSheet("color: #a0aec0; font-size: 12px; border: none;")
        header_layout.addStretch()
        header_layout.addWidget(subtitle)

        root.addWidget(header)

        # ── Body ──────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background-color: #f0f2f5;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(15)

        # ── Left panel ────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(300)
        left.setStyleSheet("""
            QWidget {
                background-color: #fff;
                border-radius: 12px;
            }
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_new = QPushButton("➕ Nova Nota")
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new.setStyleSheet(self._action_btn_style("#27ae60"))
        self.btn_new.clicked.connect(self._on_new)
        btn_row.addWidget(self.btn_new)

        self.btn_delete = QPushButton("🗑 Excluir")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet(self._action_btn_style("#e74c3c"))
        self.btn_delete.clicked.connect(self._on_delete)
        btn_row.addWidget(self.btn_delete)
        left_layout.addLayout(btn_row)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: rgba(230, 126, 34, 0.15);
                color: #1a2540;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.list_widget)

        body_layout.addWidget(left)

        # ── Right panel (editor) ──────────────────────────────────────
        right = QWidget()
        right.setStyleSheet("""
            QWidget {
                background-color: #fff;
                border-radius: 12px;
            }
        """)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)

        # Title input
        lbl_titulo = QLabel("Título")
        lbl_titulo.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        right_layout.addWidget(lbl_titulo)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Ex: Botão de check-in não funciona")
        self.title_input.setStyleSheet(self._input_style())
        self.title_input.textChanged.connect(self._mark_dirty)
        right_layout.addWidget(self.title_input)

        # Type combo
        type_row = QHBoxLayout()
        lbl_tipo = QLabel("Tipo")
        lbl_tipo.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        type_row.addWidget(lbl_tipo)

        self.type_combo = QComboBox()
        for display, value in _TIPO_OPTIONS:
            self.type_combo.addItem(display, value)
        self.type_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 13px;
                min-width: 200px;
            }
            QComboBox:focus { border-color: #E67E22; }
            QComboBox::drop-down { border: none; }
        """)
        self.type_combo.currentIndexChanged.connect(self._mark_dirty)
        type_row.addWidget(self.type_combo)
        type_row.addStretch()
        right_layout.addLayout(type_row)

        # Content
        lbl_conteudo = QLabel("Conteúdo")
        lbl_conteudo.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        right_layout.addWidget(lbl_conteudo)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText(
            "Descreva o erro encontrado, a ideia ou sugestão em detalhes..."
        )
        self.content_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.5;
                background-color: #fafafa;
            }
            QTextEdit:focus { border-color: #E67E22; }
        """)
        self.content_edit.textChanged.connect(self._mark_dirty)
        right_layout.addWidget(self.content_edit, 1)

        # Footer buttons
        footer = QHBoxLayout()
        footer.addStretch()

        self.btn_save = QPushButton("💾 Salvar")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet(self._action_btn_style("#3498db"))
        self.btn_save.clicked.connect(self._on_save)
        footer.addWidget(self.btn_save)

        self.btn_send = QPushButton("📧 Enviar ao Desenvolvedor")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setStyleSheet(self._action_btn_style("#E67E22"))
        self.btn_send.clicked.connect(self._on_send)
        footer.addWidget(self.btn_send)

        right_layout.addLayout(footer)

        body_layout.addWidget(right, 1)  # stretch = 1

        root.addWidget(body, 1)

        # Start with editor disabled
        self._set_editor_enabled(False)

    # ── Styles ────────────────────────────────────────────────────────

    @staticmethod
    def _action_btn_style(color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                color: #fff;
                border: none;
                border-radius: 6px;
                padding: 9px 18px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
        """

    @staticmethod
    def _input_style() -> str:
        return """
            QLineEdit {
                padding: 10px 14px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus { border-color: #E67E22; }
        """

    # ── Data ──────────────────────────────────────────────────────────

    def refresh(self):
        """Recarrega as notas do banco."""
        self._save_if_dirty()
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        self.list_widget.blockSignals(False)

        session = create_session()
        try:
            notas = session.execute(
                select(Nota).order_by(Nota.created_at.desc())
            ).scalars().all()

            for nota in notas:
                item = _NoteListItem(nota)
                self.list_widget.addItem(item)

        finally:
            session.close()

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        else:
            self._clear_editor()
            self._set_editor_enabled(False)

    # ── Slots ─────────────────────────────────────────────────────────

    def _on_selection_changed(self, current: Optional[_NoteListItem], previous):
        """Carrega a nota selecionada no editor."""
        if previous is not None:
            self._save_if_dirty()

        if current is None:
            self._clear_editor()
            self._set_editor_enabled(False)
            return

        nota_id = current.nota_id
        session = create_session()
        try:
            nota = session.get(Nota, nota_id)
            if not nota:
                return
            self._current_nota_id = nota.id
            self._populate_editor(nota)
            self._set_editor_enabled(True)
            self._dirty = False
        finally:
            session.close()

    def _on_new(self):
        """Cria uma nova nota."""
        self._save_if_dirty()
        session = create_session()
        try:
            nota = Nota(
                titulo="Nova Nota",
                conteudo="",
                tipo="outro",
                enviada=False,
            )
            session.add(nota)
            session.commit()
            new_id = nota.id
        finally:
            session.close()

        self.refresh()
        # Selecionar a nova nota (é a primeira pois ordenamos desc)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_delete(self):
        """Exclui a nota selecionada."""
        if self._current_nota_id is None:
            return

        reply = QMessageBox.question(
            self,
            "Excluir Nota",
            "Tem certeza que deseja excluir esta nota?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        session = create_session()
        try:
            nota = session.get(Nota, self._current_nota_id)
            if nota:
                session.delete(nota)
                session.commit()
        finally:
            session.close()

        self._current_nota_id = None
        self._dirty = False
        self.refresh()

    def _on_save(self):
        """Salva a nota atual."""
        self._save_current()
        # Atualizar visualmente o item na lista
        self._refresh_current_item_text()

    def _on_send(self):
        """Envia a nota por e-mail ao desenvolvedor."""
        if self._current_nota_id is None:
            return

        # Salvar primeiro
        self._save_current()

        session = create_session()
        try:
            nota = session.get(Nota, self._current_nota_id)
            if not nota:
                return

            titulo = nota.titulo
            conteudo = nota.conteudo or ""
            tipo = nota.tipo
            created_at = nota.created_at

            # Enviar e-mail
            from src.services.email_service import send_note_email
            send_note_email(titulo, conteudo, tipo, created_at)

            # Marcar como enviada
            nota.enviada = True
            session.commit()

            QMessageBox.information(
                self,
                "Nota Enviada",
                f"A nota \"{titulo}\" foi enviada com sucesso ao desenvolvedor! ✅",
            )
            self._refresh_current_item_text()

        except Exception as e:
            show_error(
                self,
                "Não foi possível enviar a nota por e-mail. Verifique a conexão com a internet e tente novamente.",
                detail=e,
                title="Erro ao enviar",
            )
        finally:
            session.close()

    # ── Helpers ────────────────────────────────────────────────────────

    def _save_current(self):
        """Persiste os dados do editor no banco."""
        if self._current_nota_id is None:
            return

        session = create_session()
        try:
            nota = session.get(Nota, self._current_nota_id)
            if not nota:
                return
            nota.titulo = self.title_input.text().strip() or "Sem título"
            nota.conteudo = self.content_edit.toPlainText()
            nota.tipo = self.type_combo.currentData()
            session.commit()
        finally:
            session.close()

        self._dirty = False

    def _save_if_dirty(self):
        if self._dirty:
            self._save_current()

    def _populate_editor(self, nota: Nota):
        self.title_input.blockSignals(True)
        self.content_edit.blockSignals(True)
        self.type_combo.blockSignals(True)

        self.title_input.setText(nota.titulo or "")
        self.content_edit.setPlainText(nota.conteudo or "")

        # Selecionar tipo
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == nota.tipo:
                self.type_combo.setCurrentIndex(i)
                break

        self.title_input.blockSignals(False)
        self.content_edit.blockSignals(False)
        self.type_combo.blockSignals(False)

    def _clear_editor(self):
        self.title_input.blockSignals(True)
        self.content_edit.blockSignals(True)
        self.type_combo.blockSignals(True)

        self.title_input.clear()
        self.content_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self._current_nota_id = None

        self.title_input.blockSignals(False)
        self.content_edit.blockSignals(False)
        self.type_combo.blockSignals(False)

    def _set_editor_enabled(self, enabled: bool):
        self.title_input.setEnabled(enabled)
        self.content_edit.setEnabled(enabled)
        self.type_combo.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)
        self.btn_send.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)

    def _mark_dirty(self):
        self._dirty = True

    def _refresh_current_item_text(self):
        """Atualiza o texto do item selecionado na lista."""
        item = self.list_widget.currentItem()
        if item and self._current_nota_id is not None:
            icon = _TIPO_ICONS.get(self.type_combo.currentData(), "📝")
            item.setText(f"{icon}  {self.title_input.text().strip() or 'Sem título'}")
