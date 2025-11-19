"""Diálogo para editar data/hora de um check-in."""

from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDateTimeEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal


class EditCheckinDialog(QDialog):
    """Diálogo para editar a data/hora de um check-in existente."""
    
    checkin_updated = pyqtSignal(int, datetime)  # Sinal emitido quando o check-in é atualizado (checkin_id, new_datetime)
    
    def __init__(self, checkin_id: int, current_datetime: datetime, member_name: str = "", parent=None):
        super().__init__(parent)
        self.checkin_id = checkin_id
        self.current_datetime = current_datetime
        self.member_name = member_name
        
        self.setWindowTitle("Editar Horário do Check-in")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        self._setup_ui()
        self._populate_fields()
    
    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel("Editar Data e Horário do Check-in")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007ACC;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Informação do membro
        if self.member_name:
            member_label = QLabel(f"Membro: {self.member_name}")
            member_label.setStyleSheet("font-size: 14px; color: #333333;")
            member_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(member_label)
        
        # Formulário
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Data e hora atual
        current_label = QLabel(
            f"<b>Horário atual:</b> {self.current_datetime.strftime('%d/%m/%Y às %H:%M')}"
        )
        current_label.setStyleSheet("color: #555555; background-color: #F0F0F0; padding: 10px; border-radius: 4px;")
        form_layout.addRow(current_label)
        
        # Campo de edição de data/hora
        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setCalendarPopup(True)
        self.datetime_input.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.datetime_input.setDateTime(QDateTime.currentDateTime())
        self.datetime_input.setStyleSheet("""
            QDateTimeEdit {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #007ACC;
                border-radius: 4px;
            }
        """)
        form_layout.addRow("<b>Nova data e hora:</b>", self.datetime_input)
        
        layout.addLayout(form_layout)
        
        # Nota informativa
        info_label = QLabel("💡 Você pode alterar tanto a data quanto o horário do check-in.")
        info_label.setStyleSheet("color: #666666; font-size: 12px; font-style: italic;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setFixedWidth(120)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #CCCCCC;
                color: #333333;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #BBBBBB;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Salvar")
        self.save_button.setFixedWidth(120)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005FA3;
            }
        """)
        self.save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def _populate_fields(self):
        """Preenche os campos com os dados atuais."""
        # Converter datetime para QDateTime
        qdt = QDateTime(
            self.current_datetime.year,
            self.current_datetime.month,
            self.current_datetime.day,
            self.current_datetime.hour,
            self.current_datetime.minute
        )
        self.datetime_input.setDateTime(qdt)
    
    def _on_save_clicked(self):
        """Manipula o clique no botão Salvar."""
        # Obter nova data/hora
        new_qdt = self.datetime_input.dateTime()
        new_datetime = datetime(
            new_qdt.date().year(),
            new_qdt.date().month(),
            new_qdt.date().day(),
            new_qdt.time().hour(),
            new_qdt.time().minute()
        )
        
        # Validar que a nova data não é futura
        if new_datetime > datetime.now():
            QMessageBox.warning(
                self,
                "Data Inválida",
                "Não é possível definir um check-in para o futuro.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Confirmar se houve mudança
        if new_datetime == self.current_datetime:
            QMessageBox.information(
                self,
                "Sem Alterações",
                "A data e hora não foram alteradas.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Confirmar alteração
        reply = QMessageBox.question(
            self,
            "Confirmar Alteração",
            f"Deseja alterar o horário do check-in de:\n\n"
            f"DE: {self.current_datetime.strftime('%d/%m/%Y às %H:%M')}\n"
            f"PARA: {new_datetime.strftime('%d/%m/%Y às %H:%M')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Emitir sinal com os novos dados
            self.checkin_updated.emit(self.checkin_id, new_datetime)
            self.accept()
    
    def get_new_datetime(self) -> datetime:
        """Retorna a nova data/hora selecionada."""
        qdt = self.datetime_input.dateTime()
        return datetime(
            qdt.date().year(),
            qdt.date().month(),
            qdt.date().day(),
            qdt.time().hour(),
            qdt.time().minute()
        )
