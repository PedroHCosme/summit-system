"""Tela do dashboard de atividade."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt


class DashboardScreen(QWidget):
    """Tela do dashboard de atividade."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title_label = QLabel("Dashboard de Atividade")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Layout para as estatísticas
        stats_layout = QHBoxLayout()

        # Card para Check-ins Hoje
        checkins_today_card = self._create_stat_card("Check-ins Hoje", "0")
        self.checkins_today_label = checkins_today_card.findChild(QLabel, "stat_value")

        # Botão para ver detalhes dos check-ins
        self.view_checkins_button = QPushButton("Ver Detalhes")
        self.view_checkins_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005C99;
            }
        """)
        
        # Adiciona o botão ao layout do card
        card_layout = checkins_today_card.layout()
        if card_layout:
            card_layout.addWidget(self.view_checkins_button)

        stats_layout.addWidget(checkins_today_card)
        layout.addLayout(stats_layout)

        # Lista de Últimos Check-ins
        last_checkins_label = QLabel("Últimos Check-ins")
        last_checkins_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(last_checkins_label)
        
        self.last_checkins_browser = QTextBrowser()
        self.last_checkins_browser.setMinimumHeight(150)
        layout.addWidget(self.last_checkins_browser)

        # Placeholder para o gráfico
        graph_label = QLabel("Gráfico de Frequência (Em breve)")
        graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        graph_label.setStyleSheet("font-size: 16px; color: #888;")
        layout.addWidget(graph_label)
        layout.addStretch()

    def _create_stat_card(self, title: str, initial_value: str) -> QWidget:
        """Cria um card de estatística para o dashboard."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border: 1px solid #DDDDDD;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #555;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(initial_value)
        value_label.setObjectName("stat_value")
        value_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #007ACC;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        
        return card

    def update_dashboard(self, data: dict):
        """Atualiza a UI do dashboard com novos dados."""
        self.checkins_today_label.setText(str(data.get("checkins_today", 0)))
        
        last_checkins = data.get("last_checkins", [])
        html = ""
        if not last_checkins:
            html = "<p style='color: #888;'>Nenhum check-in recente.</p>"
        else:
            html = "<ul style='list-style-type: none; padding-left: 0;'>"
            for checkin in last_checkins:
                nome = checkin.get('nome')
                dt_str = checkin.get('checkin_datetime')
                dt_obj = datetime.fromisoformat(dt_str)
                checkin_datetime_str = dt_obj.strftime('%d/%m/%Y às %H:%M')
                html += f"<li style='margin-bottom: 5px;'><b>{nome}</b> - {checkin_datetime_str}</li>"
            html += "</ul>"
        self.last_checkins_browser.setHtml(html)

    def show_error(self, error_message: str):
        """Exibe um erro no dashboard."""
        self.last_checkins_browser.setHtml(f"<p style='color: #FF6B6B;'>{error_message}</p>")

    def show_checkins_details(self):
        """Mostra uma janela com os detalhes dos check-ins de hoje."""
        try:
            from src.data.data_provider import get_checkins_today_details

            checkins = get_checkins_today_details()

            if not checkins:
                QMessageBox.information(self, "Check-ins de Hoje", "Nenhum check-in registrado hoje.")
                return

            # Cria a janela de diálogo
            dialog = QDialog(self)
            dialog.setWindowTitle("Detalhes dos Check-ins de Hoje")
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Nome do Membro", "Plano", "Data", "Horário"])
            table.setRowCount(len(checkins))
            
            for row, checkin in enumerate(checkins):
                nome = checkin.get('nome', 'N/A')
                plano = checkin.get('plano', 'N/A')
                checkin_datetime_str = checkin.get('checkin_datetime')
                
                if checkin_datetime_str:
                    dt_obj = datetime.fromisoformat(checkin_datetime_str)
                    table.setItem(row, 2, QTableWidgetItem(dt_obj.strftime('%d/%m/%Y')))
                    table.setItem(row, 3, QTableWidgetItem(dt_obj.strftime('%H:%M:%S')))
                else:
                    table.setItem(row, 2, QTableWidgetItem('N/A'))
                    table.setItem(row, 3, QTableWidgetItem('N/A'))

                table.setItem(row, 0, QTableWidgetItem(nome))
                table.setItem(row, 1, QTableWidgetItem(plano))

            header = table.horizontalHeader()
            if header:
                header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            
            layout.addWidget(table)
            
            close_button = QPushButton("Fechar")
            close_button.clicked.connect(dialog.close)
            layout.addWidget(close_button)
            
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar detalhes dos check-ins: {e}")
