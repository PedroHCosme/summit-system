"""Tela do dashboard de atividade."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from src.core.plan_status import is_active as plan_is_active


class DashboardScreen(QWidget):
    """Tela do dashboard de atividade."""
    
    # Sinal emitido quando um membro é clicado (passa o ID do membro)
    member_clicked = pyqtSignal(int)
    
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
                background-color: #E67E22;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D35400;
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
        last_checkins_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a2540;")
        layout.addWidget(last_checkins_label)
        
        self.today_checkins_table = QTableWidget()
        self.today_checkins_table.setColumnCount(5)
        self.today_checkins_table.setHorizontalHeaderLabels(
            ["Nome do Membro", "Plano", "Data", "Horário", "Status do Plano"]
        )
        self.today_checkins_table.setMinimumHeight(250)
        self.today_checkins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.today_checkins_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.today_checkins_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.today_checkins_table.cellDoubleClicked.connect(self._on_today_table_double_clicked)
        header = self.today_checkins_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.today_checkins_table)

        recent_members_label = QLabel("Últimos membros cadastrados")
        recent_members_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a2540;")
        layout.addWidget(recent_members_label)

        self.recent_members_table = QTableWidget()
        self.recent_members_table.setColumnCount(4)
        self.recent_members_table.setHorizontalHeaderLabels(
            ["Nome do Membro", "Plano", "Cadastro", "Status do Plano"]
        )
        self.recent_members_table.setMaximumHeight(260)
        self.recent_members_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_members_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_members_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.recent_members_table.cellDoubleClicked.connect(
            self._on_recent_members_table_double_clicked
        )
        recent_header = self.recent_members_table.horizontalHeader()
        if recent_header:
            recent_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.recent_members_table)

        layout.addStretch()

    def _create_stat_card(self, title: str, initial_value: str) -> QWidget:
        """Cria um card de estatística para o dashboard."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a2540;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(initial_value)
        value_label.setObjectName("stat_value")
        value_label.setStyleSheet("font-size: 42px; font-weight: bold; color: #E67E22;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        
        return card

    def update_dashboard(self, data: dict):
        """Atualiza a UI do dashboard com novos dados."""
        self.checkins_today_label.setText(str(data.get("checkins_today", 0)))
        
        last_checkins = data.get("last_checkins", [])
        if not last_checkins:
            self.today_checkins_table.setRowCount(0)
        else:
            self.today_checkins_table.setRowCount(len(last_checkins))
            for row, checkin in enumerate(last_checkins):
                nome = checkin.get("nome", "N/A")
                plano = checkin.get("plano", "N/A")
                status_plano = checkin.get("status_plano", "")
                estado_plano = checkin.get("estado_plano", "")
                member_id = checkin.get("member_id", 0)

                dt_str = checkin.get("checkin_datetime")
                date_text = "N/A"
                time_text = "N/A"
                if dt_str:
                    dt_obj = datetime.fromisoformat(dt_str)
                    date_text = dt_obj.strftime("%d/%m/%Y")
                    time_text = dt_obj.strftime("%H:%M:%S")

                name_item = QTableWidgetItem(nome)
                name_item.setData(Qt.ItemDataRole.UserRole, member_id)
                plan_item = QTableWidgetItem(plano)
                date_item = QTableWidgetItem(date_text)
                time_item = QTableWidgetItem(time_text)
                status_item = QTableWidgetItem(self._format_plan_status_label(checkin))

                needs_renewal = self._needs_plan_renewal(checkin)
                if needs_renewal:
                    name_item.setForeground(Qt.GlobalColor.red)
                    plan_item.setForeground(Qt.GlobalColor.red)
                    status_item.setForeground(Qt.GlobalColor.red)
                elif plan_is_active(estado_plano):
                    name_item.setForeground(Qt.GlobalColor.blue)
                    plan_item.setForeground(Qt.GlobalColor.blue)
                    status_item.setForeground(Qt.GlobalColor.blue)

                self.today_checkins_table.setItem(row, 0, name_item)
                self.today_checkins_table.setItem(row, 1, plan_item)
                self.today_checkins_table.setItem(row, 2, date_item)
                self.today_checkins_table.setItem(row, 3, time_item)
                self.today_checkins_table.setItem(row, 4, status_item)

        recent_members = data.get("recent_members", [])
        self.recent_members_table.setRowCount(len(recent_members))
        for row, member in enumerate(recent_members):
            member_id = member.get("id", 0)
            nome_item = QTableWidgetItem(member.get("nome", "N/A"))
            nome_item.setData(Qt.ItemDataRole.UserRole, member_id)
            plano_item = QTableWidgetItem(member.get("plano") or "N/A")
            cadastro_item = QTableWidgetItem(member.get("data_cadastro") or "N/A")
            status_item = QTableWidgetItem(member.get("estado_plano") or "-")

            estado_plano = member.get("estado_plano", "")
            if plan_is_active(estado_plano):
                nome_item.setForeground(Qt.GlobalColor.blue)
                plano_item.setForeground(Qt.GlobalColor.blue)
                status_item.setForeground(Qt.GlobalColor.blue)

            self.recent_members_table.setItem(row, 0, nome_item)
            self.recent_members_table.setItem(row, 1, plano_item)
            self.recent_members_table.setItem(row, 2, cadastro_item)
            self.recent_members_table.setItem(row, 3, status_item)

    def _needs_plan_renewal(self, checkin: dict) -> bool:
        estado_plano = checkin.get("estado_plano", "")
        status_plano = checkin.get("status_plano", "")
        is_quota_plan = bool(checkin.get("is_quota_plan", False))
        voucher_credits = int(checkin.get("voucher_credits", 0) or 0)

        if is_quota_plan and voucher_credits <= 0:
            return True
        if status_plano and status_plano.strip().upper() == "VENCIDO":
            return True
        if estado_plano and not plan_is_active(estado_plano):
            return True
        return False

    def _format_plan_status_label(self, checkin: dict) -> str:
        """Normaliza rótulos de status do plano para o padrão da dashboard."""
        is_quota_plan = bool(checkin.get("is_quota_plan", False))
        voucher_credits = int(checkin.get("voucher_credits", 0) or 0)
        if is_quota_plan:
            if voucher_credits <= 0:
                return "Sem vouchers"
            return f"{voucher_credits} voucher(s)"

        status_plano = checkin.get("status_plano", "")
        normalized = (status_plano or "").strip().upper()
        if normalized == "EM DIA":
            return "Em dia"
        if normalized == "VENCIDO":
            return "Vencido"
        if normalized == "SEM VENCIMENTO":
            return "-"
        if normalized == "PENDENTE":
            return "Pendente"
        return "-"

    def _on_today_table_double_clicked(self, row: int, _column: int) -> None:
        name_item = self.today_checkins_table.item(row, 0)
        if not name_item:
            return
        member_id = name_item.data(Qt.ItemDataRole.UserRole)
        if isinstance(member_id, int) and member_id > 0:
            self.member_clicked.emit(member_id)

    def _on_recent_members_table_double_clicked(self, row: int, _column: int) -> None:
        name_item = self.recent_members_table.item(row, 0)
        if not name_item:
            return
        member_id = name_item.data(Qt.ItemDataRole.UserRole)
        if isinstance(member_id, int) and member_id > 0:
            self.member_clicked.emit(member_id)

    def show_error(self, error_message: str):
        """Exibe um erro no dashboard."""
        self.today_checkins_table.setRowCount(0)
        self.recent_members_table.setRowCount(0)
        QMessageBox.warning(self, "Erro no Dashboard", error_message)

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
                    background-color: white;
                }
                QDateEdit::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 30px;
                    border-left: 1px solid #007ACC;
                    border-top-right-radius: 3px;
                    border-bottom-right-radius: 3px;
                    background-color: #007ACC;
                }
                QDateEdit::down-arrow {
                    image: none;
                    width: 14px;
                    height: 14px;
                }
                QDateEdit::down-arrow:on {
                    top: 1px;
                }
                QCalendarWidget {
                    background-color: white;
                }
                QCalendarWidget QToolButton {
                    color: #333;
                    background-color: #f0f0f0;
                    border-radius: 4px;
                    padding: 5px;
                }
                QCalendarWidget QToolButton:hover {
                    background-color: #007ACC;
                    color: white;
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
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(
                ["Nome do Membro", "Plano", "Data", "Horário", "Status do Plano"]
            )
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            
            header = table.horizontalHeader()
            if header:
                header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            layout.addWidget(table)
            
            # Lista para armazenar member_ids para cada linha
            member_ids = []
            
            # Função para carregar os dados
            def load_checkins():
                nonlocal member_ids
                member_ids.clear()
                
                selected_date = date_edit.date()
                date_str = selected_date.toString("yyyy-MM-dd")
                date_display = selected_date.toString("dd/MM/yyyy")
                
                checkins = get_checkins_by_date(date_str)
                
                if not checkins:
                    info_label.setText(f"📅 {date_display} - Nenhum check-in registrado nesta data.")
                    info_label.setStyleSheet("font-size: 13px; color: #FF6B6B; margin: 10px 0; font-weight: bold;")
                    table.setRowCount(0)
                else:
                    info_label.setText(f"📅 {date_display} - Total: {len(checkins)} check-in(s) (duplo clique para ver perfil)")
                    info_label.setStyleSheet("font-size: 13px; color: #28a745; margin: 10px 0; font-weight: bold;")
                    table.setRowCount(len(checkins))
                    
                    for row, checkin in enumerate(checkins):
                        nome = checkin.get('nome', 'N/A')
                        plano = checkin.get('plano', 'N/A')
                        member_id = checkin.get('member_id', 0)
                        estado_plano = checkin.get('estado_plano', '')
                        status_plano = checkin.get('status_plano', '')
                        member_ids.append(member_id)
                        checkin_datetime_str = checkin.get('checkin_datetime')
                        
                        if checkin_datetime_str:
                            dt_obj = datetime.fromisoformat(checkin_datetime_str)
                            table.setItem(row, 2, QTableWidgetItem(dt_obj.strftime('%d/%m/%Y')))
                            table.setItem(row, 3, QTableWidgetItem(dt_obj.strftime('%H:%M:%S')))
                        else:
                            table.setItem(row, 2, QTableWidgetItem('N/A'))
                            table.setItem(row, 3, QTableWidgetItem('N/A'))

                        nome_item = QTableWidgetItem(nome)
                        status_item = QTableWidgetItem(
                            self._format_plan_status_label(checkin)
                        )
                        cor = Qt.GlobalColor.blue
                        if self._needs_plan_renewal(checkin):
                            cor = Qt.GlobalColor.red
                        nome_item.setForeground(cor)
                        status_item.setForeground(cor)
                        table.setItem(row, 0, nome_item)
                        table.setItem(row, 1, QTableWidgetItem(plano))
                        table.setItem(row, 4, status_item)
            
            # Handler para duplo clique em linha
            def on_row_double_clicked(row, column):
                if 0 <= row < len(member_ids):
                    member_id = member_ids[row]
                    if member_id > 0:
                        dialog.close()
                        self.member_clicked.emit(member_id)
            
            # Conectar duplo clique
            table.cellDoubleClicked.connect(on_row_double_clicked)
            
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
