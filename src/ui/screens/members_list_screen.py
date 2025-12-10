"""Tela de listagem de membros com paginação."""

from datetime import datetime
from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QTextBrowser, QMessageBox,
    QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from src.config import PLANOS_COM_VENCIMENTO


class MembersListScreen(QWidget):
    """Tela de listagem paginada de membros."""
    
    # Sinais
    member_selected = pyqtSignal(dict)  # Sinal emitido quando um membro é selecionado
    edit_requested = pyqtSignal()
    renew_requested = pyqtSignal()
    delete_requested = pyqtSignal()
    refresh_requested = pyqtSignal()    # Emitido quando precisa recarregar dados
    
    def __init__(self):
        super().__init__()
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 0
        self.total_members = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Lista de Membros")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Filtros
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(10)
        
        # Filtro de busca por nome
        filters_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o nome...")
        self.search_input.setMaximumWidth(250)
        filters_layout.addWidget(self.search_input)
        
        # Filtro por plano
        filters_layout.addWidget(QLabel("Plano:"))
        self.plan_filter = QComboBox()
        self.plan_filter.addItem("Todos", "")
        self.plan_filter.setMaximumWidth(150)
        filters_layout.addWidget(self.plan_filter)
        
        # Filtro por status
        filters_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "ATIVO", "INATIVO"])
        self.status_filter.setMaximumWidth(120)
        filters_layout.addWidget(self.status_filter)
        
        # Botão de filtrar
        self.filter_button = QPushButton("Filtrar")
        self.filter_button.setMaximumWidth(100)
        filters_layout.addWidget(self.filter_button)
        
        # Botão de limpar filtros
        self.clear_filters_button = QPushButton("Limpar")
        self.clear_filters_button.setMaximumWidth(100)
        filters_layout.addWidget(self.clear_filters_button)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Informações de paginação
        self.info_label = QLabel("Carregando...")
        self.info_label.setStyleSheet("color: #555555; font-size: 12px;")
        layout.addWidget(self.info_label)
        
        # Container principal com duas colunas
        content_layout = QHBoxLayout()
        
        # Coluna esquerda: Lista de membros
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("Membros:")
        list_label.setStyleSheet("color: #007ACC; font-weight: bold; font-size: 14px;")
        left_layout.addWidget(list_label)
        
        self.members_list = QListWidget()
        self.members_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #EEEEEE;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
                color: white;
            }
        """)
        self.members_list.itemClicked.connect(self._on_item_clicked)
        left_layout.addWidget(self.members_list)
        
        content_layout.addWidget(left_container, 1)
        
        # Coluna direita: Detalhes com abas
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = QLabel("Detalhes:")
        details_label.setStyleSheet("color: #007ACC; font-weight: bold; font-size: 14px;")
        right_layout.addWidget(details_label)
        
        # Tab Widget
        self.member_tabs = QTabWidget()
        self.member_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                background: #FFFFFF;
            }
            QTabBar::tab {
                background: #E0E0E0;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #007ACC;
                color: white;
            }
            QTabBar::tab:hover {
                background: #D0D0D0;
            }
        """)
        
        # Aba 1: Informações
        info_tab_container = QWidget()
        info_tab_layout = QVBoxLayout(info_tab_container)
        info_tab_layout.setContentsMargins(0, 0, 0, 0)
        
        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        self.details_browser.setHtml("<div style='text-align: center; color: #666; margin-top: 20px;'>Selecione um membro para ver os detalhes</div>")
        info_tab_layout.addWidget(self.details_browser)
        
        # Botões de ação
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.addStretch()
        
        # Botão Deletar
        self.delete_button = QPushButton("🗑️ Deletar")
        self.delete_button.setFixedWidth(120)
        self.delete_button.setFixedHeight(35)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #B71C1C;
            }
        """)
        self.delete_button.clicked.connect(self.delete_requested.emit)
        self.delete_button.setVisible(False)
        button_layout.addWidget(self.delete_button)
        
        # Botão Renovar Plano
        self.renew_button = QPushButton("🔄 Renovar Plano")
        self.renew_button.setFixedWidth(150)
        self.renew_button.setFixedHeight(35)
        self.renew_button.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.renew_button.clicked.connect(self.renew_requested.emit)
        self.renew_button.setVisible(False)
        button_layout.addWidget(self.renew_button)
        
        # Botão Editar
        self.edit_button = QPushButton("✏️ Editar")
        self.edit_button.setFixedWidth(120)
        self.edit_button.setFixedHeight(35)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005FA3;
            }
        """)
        self.edit_button.clicked.connect(self.edit_requested.emit)
        self.edit_button.setVisible(False)
        button_layout.addWidget(self.edit_button)
        
        info_tab_layout.addWidget(button_container)
        self.member_tabs.addTab(info_tab_container, "Informações")
        
        # Aba 2: Histórico de Frequência
        self.history_browser = QTextBrowser()
        self.history_browser.setOpenExternalLinks(False)
        self.history_browser.setHtml("<p style='color: #888888;'>Selecione um membro para ver o histórico.</p>")
        self.member_tabs.addTab(self.history_browser, "Histórico de Frequência")
        
        # Aba 3: Histórico Financeiro
        self.financial_browser = QTextBrowser()
        self.financial_browser.setOpenExternalLinks(False)
        self.financial_browser.setHtml("<p style='color: #888888;'>Selecione um membro para ver o histórico financeiro.</p>")
        self.member_tabs.addTab(self.financial_browser, "Histórico Financeiro")
        
        right_layout.addWidget(self.member_tabs)
        
        content_layout.addWidget(right_container, 2)
        
        layout.addLayout(content_layout)
        
        # Controles de paginação
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(10)
        
        self.first_button = QPushButton("⏮ Primeira")
        self.first_button.setMaximumWidth(100)
        pagination_layout.addWidget(self.first_button)
        
        self.prev_button = QPushButton("◀ Anterior")
        self.prev_button.setMaximumWidth(100)
        pagination_layout.addWidget(self.prev_button)
        
        pagination_layout.addStretch()
        
        self.page_label = QLabel("Página 1 de 1")
        self.page_label.setStyleSheet("font-weight: bold; color: #007ACC;")
        pagination_layout.addWidget(self.page_label)
        
        pagination_layout.addStretch()
        
        self.next_button = QPushButton("Próxima ▶")
        self.next_button.setMaximumWidth(100)
        pagination_layout.addWidget(self.next_button)
        
        self.last_button = QPushButton("Última ⏭")
        self.last_button.setMaximumWidth(100)
        pagination_layout.addWidget(self.last_button)
        
        layout.addLayout(pagination_layout)
        
        # Conectar sinais
        self._connect_signals()
    
    def _connect_signals(self):
        """Conecta os sinais dos widgets."""
        self.filter_button.clicked.connect(self._on_filter)
        self.clear_filters_button.clicked.connect(self._on_clear_filters)
        self.search_input.returnPressed.connect(self._on_filter)
        
        self.first_button.clicked.connect(self._go_to_first_page)
        self.prev_button.clicked.connect(self._go_to_previous_page)
        self.next_button.clicked.connect(self._go_to_next_page)
        self.last_button.clicked.connect(self._go_to_last_page)
    
    def _on_filter(self):
        """Aplica os filtros e volta para a primeira página."""
        self.current_page = 1
        self.refresh_requested.emit()
    
    def _on_clear_filters(self):
        """Limpa todos os filtros."""
        self.search_input.clear()
        self.plan_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.current_page = 1
        self.refresh_requested.emit()
    
    def _go_to_first_page(self):
        """Vai para a primeira página."""
        if self.current_page != 1:
            self.current_page = 1
            self.refresh_requested.emit()
    
    def _go_to_previous_page(self):
        """Vai para a página anterior."""
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_requested.emit()
    
    def _go_to_next_page(self):
        """Vai para a próxima página."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh_requested.emit()
    
    def _go_to_last_page(self):
        """Vai para a última página."""
        if self.current_page != self.total_pages and self.total_pages > 0:
            self.current_page = self.total_pages
            self.refresh_requested.emit()
    
    def get_filters(self) -> Dict[str, Any]:
        """Retorna os filtros atuais."""
        status_text = self.status_filter.currentText()
        return {
            'text': self.search_input.text().strip(),
            'plan': self.plan_filter.currentData() or "",
            'status': status_text if status_text != "Todos" else ""
        }
    
    def populate_plan_filter(self, plans: List[str]):
        """Popula o filtro de planos."""
        current = self.plan_filter.currentData()
        self.plan_filter.clear()
        self.plan_filter.addItem("Todos", "")
        for plan in plans:
            self.plan_filter.addItem(plan, plan)
        
        # Restaurar seleção se possível
        if current:
            index = self.plan_filter.findData(current)
            if index >= 0:
                self.plan_filter.setCurrentIndex(index)
    
    def update_data(self, data: Dict[str, Any]):
        """
        Atualiza a tabela com os dados paginados.
        
        Args:
            data: Dicionário com 'members', 'total', 'page', 'total_pages'
        """
        members = data.get('members', [])
        self.total_members = data.get('total', 0)
        self.current_page = data.get('page', 1)
        self.total_pages = data.get('total_pages', 0)
        
        # Atualizar informações
        start = (self.current_page - 1) * self.page_size + 1
        end = min(start + len(members) - 1, self.total_members)
        
        if self.total_members > 0:
            self.info_label.setText(
                f"Exibindo {start}-{end} de {self.total_members} membros"
            )
        else:
            self.info_label.setText("Nenhum membro encontrado")
        
        self.page_label.setText(f"Página {self.current_page} de {max(1, self.total_pages)}")
        
        # Atualizar botões de paginação
        self.first_button.setEnabled(self.current_page > 1)
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)
        self.last_button.setEnabled(self.current_page < self.total_pages)
        
        # Atualizar lista
        self.members_list.clear()
        
        for member in members:
            nome = member.get('nome', '')
            apelido = member.get('apelido', '')
            
            display_text = f"{nome} ({apelido})" if apelido else nome
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, member)
            self.members_list.addItem(item)
            
        # Limpar detalhes
        self.details_browser.setHtml("<div style='text-align: center; color: #666; margin-top: 20px;'>Selecione um membro para ver os detalhes</div>")

    def _on_item_clicked(self, item):
        """Manipula o clique em um item da lista."""
        member_data = item.data(Qt.ItemDataRole.UserRole)
        if member_data:
            self.member_selected.emit(member_data)
            
    def display_member_data(self, member_data: dict):
        """Exibe os detalhes do membro no browser."""
        self.current_member_data = member_data
        
        # Formatar e exibir dados
        html = self._format_member_data(member_data)
        self.details_browser.setHtml(html)
        
        # Mostrar botões
        self.edit_button.setVisible(True)
        self.delete_button.setVisible(True)
        
        # Mostrar botão de renovar apenas para planos renováveis
        from src.config import PLANOS_COM_VENCIMENTO
        plano = member_data.get('plano', '')
        planos_nao_renovaveis = ["Diária", "Diária Boulder", "Gympass", "Totalpass", "Cortesia"]
        is_renewable = plano not in planos_nao_renovaveis and plano in PLANOS_COM_VENCIMENTO
        self.renew_button.setVisible(is_renewable)

    def display_member_history(self, history: list):
        """Exibe o histórico do membro."""
        member_name = self.current_member_data.get('nome', 'Membro') if self.current_member_data else 'Membro'
        html = self._format_member_history(member_name, history)
        self.history_browser.setHtml(html)
    
    def display_member_financial_history(self, payments: list):
        """Exibe o histórico financeiro do membro."""
        member_name = self.current_member_data.get('nome', 'Membro') if self.current_member_data else 'Membro'
        html = self._format_member_financial_history(member_name, payments)
        self.financial_browser.setHtml(html)

    def _format_member_data(self, member_data: dict) -> str:
        """Formata os dados do membro em HTML."""
        # Calcular frequência do mês atual
        member_id = member_data.get('id')
        frequencia_mes_atual = self._calculate_monthly_frequency(member_id) if member_id else 0
        
        html = """
            <div style="padding: 20px;">
                <h2 style="color: #007ACC; text-align: center; margin-bottom: 20px;">Dados do Membro</h2>
                <div style="background-color: #F8F8F8; border: 1px solid #DDDDDD; border-radius: 8px; padding: 15px;">
        """
        
        # 1. Nome
        nome = member_data.get('nome', '')
        apelido = member_data.get('apelido', '')
        nome_display = f"{nome} ({apelido})" if apelido else (nome if nome else '<span style="color: #888888; font-style: italic;">Não informado</span>')
        
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Nome:</strong>
                <span style="color: #555555;"> {nome_display}</span>
            </div>
        """
        
        # 2. Data de Nascimento
        data_nascimento = member_data.get('data_nascimento', '')
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Data de Nascimento:</strong>
                <span style="color: #555555;"> {data_nascimento if data_nascimento else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
            </div>
        """
        
        # 3. Gênero
        genero = member_data.get('genero', '')
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Gênero:</strong>
                <span style="color: #555555;"> {genero if genero else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
            </div>
        """
        
        # 4. WhatsApp
        whatsapp = member_data.get('whatsapp', '')
        if whatsapp:
            digits = ''.join(filter(str.isdigit, whatsapp))
            if len(digits) == 11:
                whatsapp_link = f"https://wa.me/55{digits}"
                html += f"""
                    <div style="margin-bottom: 10px;">
                        <strong style="color: #333333;">WhatsApp:</strong>
                        <span style="color: #555555;"> {whatsapp}</span>
                        <a href="{whatsapp_link}" style="color: #007ACC; margin-left: 10px;">[Abrir WhatsApp]</a>
                    </div>
                """
            else:
                html += f"""
                    <div style="margin-bottom: 10px;">
                        <strong style="color: #333333;">WhatsApp:</strong>
                        <span style="color: #555555;"> {whatsapp}</span>
                    </div>
                """
        else:
            html += f"""
                <div style="margin-bottom: 10px;">
                    <strong style="color: #333333;">WhatsApp:</strong>
                    <span style="color: #888888; font-style: italic;"> Não informado</span>
                </div>
            """
        
        # 5. Email
        email = member_data.get('email', '')
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Email:</strong>
                <span style="color: #555555;"> {email if email else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
            </div>
        """
        
        # 6. Calçado
        calcado = member_data.get('calcado', '')
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Calçado:</strong>
                <span style="color: #555555;"> {calcado if calcado else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
            </div>
        """
        
        # Separador visual
        html += """
            <hr style="border: none; border-top: 1px solid #DDDDDD; margin: 15px 0;">
        """
        
        # 7. Plano
        plano = member_data.get('plano', '')
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Plano:</strong>
                <span style="color: #555555;"> {plano if plano else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
            </div>
        """
        
        # 8. Vencimento do Plano (se aplicável)
        if plano in PLANOS_COM_VENCIMENTO:
            vencimento_plano = member_data.get('vencimento_plano', '')
            html += f"""
                <div style="margin-bottom: 10px;">
                    <strong style="color: #333333;">Vencimento do Plano:</strong>
                    <span style="color: #555555;"> {vencimento_plano if vencimento_plano else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
                </div>
            """
        
        # 9. Estado do Plano
        estado_plano = member_data.get('estado_plano', '')
        estado_color = '#28a745' if estado_plano.upper() == 'ATIVO' else '#FF6B6B'
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Estado do Plano:</strong>
                <span style="color: {estado_color}; font-weight: bold;"> {estado_plano if estado_plano else 'INATIVO'}</span>
            </div>
        """
        
        # 10. Treino
        treina = member_data.get('treina', 'Não')
        treina_color = '#28a745' if treina == 'Sim' else '#888888'
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Treina:</strong>
                <span style="color: {treina_color}; font-weight: bold;"> {treina}</span>
            </div>
        """
        
        # 11. Vencimento do Treino (se treina)
        if treina == 'Sim':
            vencimento_treino = member_data.get('vencimento_treino', '')
            html += f"""
                <div style="margin-bottom: 10px;">
                    <strong style="color: #333333;">Vencimento do Treino:</strong>
                    <span style="color: #555555;"> {vencimento_treino if vencimento_treino else '<span style="color: #888888; font-style: italic;">Não informado</span>'}</span>
                </div>
            """
        
        # 12. Frequência do Mês
        html += f"""
            <div style="margin-bottom: 10px;">
                <strong style="color: #333333;">Frequência (Este Mês):</strong>
                <span style="color: #007ACC; font-weight: bold;"> {frequencia_mes_atual} check-ins</span>
            </div>
        """
        
        html += """
                </div>
            </div>
        """
        
        return html

    def _format_member_history(self, member_name: str, history: list) -> str:
        """Formata o histórico do membro em HTML."""
        if not history:
            return f"""
                <div style="padding: 20px;">
                    <h3 style="color: #007ACC;">Histórico de {member_name}</h3>
                    <p style="color: #888888; font-style: italic;">
                        Nenhum check-in registrado ainda.
                    </p>
                </div>
            """
        
        html = f"""
            <div style="padding: 20px; font-family: 'Segoe UI', Arial, sans-serif;">
                <h3 style="color: #007ACC; margin-bottom: 15px;">
                    Histórico de Frequência: {member_name}
                </h3>
                <p style="color: #333333; margin-bottom: 20px;">
                    Total de check-ins: <strong style="color: #007ACC;">{len(history)}</strong>
                </p>
                <div style="max-height: 500px; overflow-y: auto;">
        """
        
        # Agrupar por mês/ano
        months_pt = {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
            'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
            'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
            'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        }
        
        days_pt = {
            'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira',
            'Wednesday': 'Quarta-feira', 'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        
        grouped = {}
        for checkin in history:
            try:
                checkin_dt = datetime.fromisoformat(checkin['checkin_datetime'])
                month_name = checkin_dt.strftime('%B')
                month_pt = months_pt.get(month_name, month_name)
                month_year = f"{month_pt} de {checkin_dt.year}"
                
                if month_year not in grouped:
                    grouped[month_year] = []
                grouped[month_year].append(checkin)
            except:
                continue
        
        for month_year, checkins in grouped.items():
            html += f"""
                <div style="margin-bottom: 20px;">
                    <h4 style="color: #007ACC; margin-bottom: 10px;">{month_year}</h4>
                    <div style="margin-left: 15px;">
            """
            
            for checkin_data in checkins:
                try:
                    dt = datetime.fromisoformat(checkin_data['checkin_datetime'])
                    day_name = dt.strftime('%A')
                    date_str = dt.strftime('%d/%m/%Y')
                    time_str = dt.strftime('%H:%M')
                    day_name_pt = days_pt.get(day_name, day_name)
                    
                    html += f"""
                        <div style="margin-bottom: 8px; padding: 8px; background: #F0F0F0; border-radius: 4px;">
                            <span style="color: #333333;">📅 {day_name_pt}</span>
                            <span style="color: #555555; margin-left: 10px;">{date_str}</span>
                            <span style="color: #007ACC; margin-left: 10px;">⏰ {time_str}</span>
                        </div>
                    """
                except:
                    continue
            
            html += """
                    </div>
                </div>
            """
        
        html += """
                </div>
            </div>
        """
        
        return html

    def _format_member_financial_history(self, member_name: str, payments: list) -> str:
        """Formata o histórico financeiro do membro em HTML."""
        if not payments:
            return f"""
                <div style="padding: 20px;">
                    <h3 style="color: #007ACC;">Histórico Financeiro: {member_name}</h3>
                    <p style="color: #888888; font-style: italic;">
                        Nenhum pagamento registrado ainda.
                    </p>
                </div>
            """
        
        # Calcular estatísticas
        total_pago = sum(p.get('valor', 0) for p in payments)
        num_transacoes = len(payments)
        
        html = f"""
            <div style="padding: 20px; font-family: 'Segoe UI', Arial, sans-serif;">
                <h3 style="color: #007ACC; margin-bottom: 15px;">
                    Histórico Financeiro: {member_name}
                </h3>
                
                <!-- Resumo Financeiro -->
                <div style="background: #F0F8FF; border-left: 4px solid #007ACC; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                    <h4 style="margin: 0 0 10px 0; color: #007ACC;">Resumo Geral</h4>
                    <div style="display: flex; gap: 30px;">
                        <div>
                            <div style="font-size: 12px; color: #666;">Total Pago</div>
                            <div style="font-size: 20px; font-weight: bold; color: #28a745;">
                                R$ {total_pago:,.2f}
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #666;">Transações</div>
                            <div style="font-size: 20px; font-weight: bold; color: #007ACC;">
                                {num_transacoes}
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Lista de Transações -->
                <h4 style="color: #007ACC; margin-bottom: 10px;">Histórico de Transações</h4>
                <div style="max-height: 400px; overflow-y: auto;">
        """
        
        # Ordenar pagamentos por data (mais recente primeiro)
        sorted_payments = sorted(
            payments, 
            key=lambda x: x.get('data_pagamento', ''), 
            reverse=True
        )
        
        for payment in sorted_payments:
            tipo = payment.get('tipo_transacao', 'N/A')
            valor = payment.get('valor', 0)
            data = payment.get('data_pagamento', '')
            
            # Formatar data
            try:
                data_dt = datetime.fromisoformat(data)
                data_str = data_dt.strftime('%d/%m/%Y às %H:%M')
            except:
                data_str = data
            
            html += f"""
                <div style="margin-bottom: 10px; padding: 10px; background: #FFFFFF; border: 1px solid #EEEEEE; border-radius: 4px; border-left: 4px solid #28a745;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <strong style="color: #333;">{tipo}</strong>
                        <strong style="color: #28a745;">R$ {valor:,.2f}</strong>
                    </div>
                    <div style="font-size: 12px; color: #666;">
                        📅 {data_str}
                    </div>
                </div>
            """
        
        html += """
                </div>
            </div>
        """
        
        return html

    def _calculate_monthly_frequency(self, member_id: int) -> int:
        """
        Calcula quantos check-ins o membro fez no mês atual.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Número de check-ins no mês atual
        """
        if not member_id:
            return 0
        
        try:
            from src.data.data_provider import get_provider
            
            # Buscar histórico completo do membro
            history = get_provider().get_member_checkin_history(member_id)
            
            if not history:
                return 0
            
            # Obter mês e ano atuais
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            
            # Contar check-ins do mês atual
            count = 0
            for checkin in history:
                checkin_datetime_str = checkin.get('checkin_datetime', '')
                
                try:
                    # Tentar parsear a data
                    checkin_dt = datetime.fromisoformat(checkin_datetime_str.replace(' ', 'T'))
                    
                    # Verificar se é do mês atual
                    if checkin_dt.month == current_month and checkin_dt.year == current_year:
                        count += 1
                except (ValueError, AttributeError):
                    continue
            
            return count
            
        except Exception as e:
            print(f"Erro ao calcular frequência mensal: {e}")
            return 0
