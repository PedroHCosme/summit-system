"""Tela do dashboard de atividade."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate


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

        # Header com título e botão de refresh
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Dashboard de Atividade")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botão de atualização manual
        refresh_button = QPushButton("🔄 Atualizar")
        refresh_button.setObjectName("refresh_button")
        refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.refresh_button = refresh_button
        header_layout.addWidget(refresh_button)
        
        layout.addLayout(header_layout)

        # Layout para as estatísticas
        stats_layout = QHBoxLayout()
        
        # Botão de atualização manual
        refresh_button = QPushButton("🔄 Atualizar")
        refresh_button.setObjectName("refresh_button")
        refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        # Nota: O clique será conectado pelo MainWindow no _connect_screen_signals ou similar,
        # MAS como MainWindow cria a tela, podemos deixar a tela emitir um sinal ou conectar direto lá.
        # Para facilitar, vou expor o botão.
        self.refresh_button = refresh_button
        
        # Header layout para alinhar o título e o botão
        header_layout = QHBoxLayout()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_button)
        
        # Substitui o title_label original pelo header_layout
        # Precisamos remover o widget anterior se for substituir
        # Mas como estamos no setup_ui, vou alterar a ordem de adição:
        
        # Removemos title_label do layout principal (linha 29) e usamos header_layout
        # Como replace_file_content é por bloco, vou reescrever o bloco inicial


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

        # Lista de Check-ins de Hoje
        last_checkins_label = QLabel("Check-ins de Hoje")
        last_checkins_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(last_checkins_label)
        
        self.last_checkins_browser = QTextBrowser()
        self.last_checkins_browser.setMinimumHeight(250)  # Aumentado para acomodar mais check-ins
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
            html = "<p style='color: #888; font-style: italic; text-align: center; padding: 20px;'>Nenhum check-in registrado hoje.</p>"
        else:
            html = "<div style='padding: 10px;'>"
            html += f"<p style='color: #555; margin-bottom: 10px;'><b>Total:</b> {len(last_checkins)} check-in(s)</p>"
            html += "<ul style='list-style-type: none; padding-left: 0;'>"
            for checkin in last_checkins:
                nome = checkin.get('nome')
                dt_str = checkin.get('checkin_datetime')
                dt_obj = datetime.fromisoformat(dt_str)
                checkin_datetime_str = dt_obj.strftime('%d/%m/%Y às %H:%M')
                html += f"<li style='margin-bottom: 8px; padding: 8px; background: #F5F5F5; border-radius: 4px;'><b>{nome}</b> - {checkin_datetime_str}</li>"
            html += "</ul>"
            html += "</div>"
        self.last_checkins_browser.setHtml(html)

    def show_error(self, error_message: str):
        """Exibe um erro no dashboard."""
        self.last_checkins_browser.setHtml(f"<p style='color: #FF6B6B;'>{error_message}</p>")

    def show_checkins_details(self):
        """Mostra uma janela com os detalhes dos check-ins com seletor de data."""
        try:
            from src.data.data_provider import get_checkins_by_date

            # Cria a janela de diálogo
            dialog = QDialog(self)
            dialog.setWindowTitle("Detalhes dos Check-ins")
            dialog.setMinimumSize(700, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Header com seletor de data
            header_layout = QHBoxLayout()
            
            date_label = QLabel("Selecione a data:")
            date_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
            header_layout.addWidget(date_label)
            
            # Seletor de data
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("dd/MM/yyyy")
            date_edit.setDate(QDate.currentDate())
            date_edit.setMaximumDate(QDate.currentDate())  # Não permite datas futuras
            date_edit.setStyleSheet("""
                QDateEdit {
                    padding: 8px;
                    font-size: 14px;
                    border: 2px solid #007ACC;
                    border-radius: 4px;
                    min-width: 150px;
                }
            """)
            header_layout.addWidget(date_edit)
            
            # Botão para atualizar
            update_button = QPushButton("Atualizar")
            update_button.setStyleSheet("""
                QPushButton {
                    background-color: #007ACC;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #005FA3;
                }
            """)
            header_layout.addWidget(update_button)
            header_layout.addStretch()
            
            layout.addLayout(header_layout)
            
            # Label para mostrar informações
            info_label = QLabel("")
            info_label.setStyleSheet("font-size: 13px; color: #555; margin: 10px 0;")
            layout.addWidget(info_label)
            
            # Tabela
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Nome do Membro", "Plano", "Data", "Horário"])
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            
            header = table.horizontalHeader()
            if header:
                header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            layout.addWidget(table)
            
            # Função para carregar os dados
            def load_checkins():
                selected_date = date_edit.date()
                date_str = selected_date.toString("yyyy-MM-dd")
                date_display = selected_date.toString("dd/MM/yyyy")
                
                checkins = get_checkins_by_date(date_str)
                
                if not checkins:
                    info_label.setText(f"📅 {date_display} - Nenhum check-in registrado nesta data.")
                    info_label.setStyleSheet("font-size: 13px; color: #FF6B6B; margin: 10px 0; font-weight: bold;")
                    table.setRowCount(0)
                else:
                    info_label.setText(f"📅 {date_display} - Total: {len(checkins)} check-in(s)")
                    info_label.setStyleSheet("font-size: 13px; color: #28a745; margin: 10px 0; font-weight: bold;")
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
            
            # Conectar o botão de atualizar
            update_button.clicked.connect(load_checkins)
            
            # Conectar mudança de data para auto-atualizar
            date_edit.dateChanged.connect(load_checkins)
            
            # Carregar dados iniciais (hoje)
            load_checkins()
            
            # Botão fechar
            close_button = QPushButton("Fechar")
            close_button.setStyleSheet("""
                QPushButton {
                    background-color: #CCCCCC;
                    color: #333333;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 10px;
                    font-size: 14px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #BBBBBB;
                }
            """)
            close_button.clicked.connect(dialog.close)
            layout.addWidget(close_button)
            
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar detalhes dos check-ins: {e}")
