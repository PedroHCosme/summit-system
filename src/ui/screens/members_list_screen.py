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
from src.core.plan_status import ATIVO, INATIVO


class MembersListScreen(QWidget):
    """Tela de listagem paginada de membros."""
    
    member_selected = pyqtSignal(dict)  # Sinal emitido quando um membro é selecionado
    edit_requested = pyqtSignal()
    renew_requested = pyqtSignal()
    delete_requested = pyqtSignal()
    whatsapp_requested = pyqtSignal()
    quick_payment_requested = pyqtSignal()
    history_requested = pyqtSignal()
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
        
        title_label = QLabel("Lista de Membros")
        title_label.setObjectName("pageTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Pesquise, filtre e acesse ações rápidas do membro selecionado")
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(10)
        
        filters_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o nome...")
        self.search_input.setMaximumWidth(250)
        filters_layout.addWidget(self.search_input)
        
        filters_layout.addWidget(QLabel("Plano:"))
        self.plan_filter = QComboBox()
        self.plan_filter.addItem("Todos", "")
        self.plan_filter.setMaximumWidth(150)
        filters_layout.addWidget(self.plan_filter)
        
        filters_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", ATIVO, INATIVO])
        self.status_filter.setMaximumWidth(120)
        filters_layout.addWidget(self.status_filter)
        
        filters_layout.addWidget(QLabel("Ordenar por:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Nome (A→Z)", ("nome", "asc"))
        self.sort_combo.addItem("Nome (Z→A)", ("nome", "desc"))
        self.sort_combo.addItem("Cadastro (Mais Recente)", ("data_cadastro", "desc"))
        self.sort_combo.addItem("Cadastro (Mais Antigo)", ("data_cadastro", "asc"))
        self.sort_combo.addItem("Vencimento (Próximo)", ("vencimento_plano", "asc"))
        self.sort_combo.addItem("Vencimento (Distante)", ("vencimento_plano", "desc"))
        self.sort_combo.setMaximumWidth(200)
        filters_layout.addWidget(self.sort_combo)
        
        self.filter_button = QPushButton("Filtrar")
        self.filter_button.setProperty("role", "primary")
        self.filter_button.setMaximumWidth(100)
        filters_layout.addWidget(self.filter_button)
        
        self.clear_filters_button = QPushButton("Limpar")
        self.clear_filters_button.setProperty("role", "secondary")
        self.clear_filters_button.setMaximumWidth(100)
        filters_layout.addWidget(self.clear_filters_button)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        self.info_label = QLabel("Carregando...")
        self.info_label.setStyleSheet("color: #555555; font-size: 12px;")
        layout.addWidget(self.info_label)
        
        content_layout = QHBoxLayout()
        
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("Membros:")
        list_label.setStyleSheet("color: #1a2540; font-weight: bold; font-size: 14px;")
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
                background-color: #E67E22;
                color: white;
            }
        """)
        self.members_list.itemClicked.connect(self._on_item_clicked)
        left_layout.addWidget(self.members_list)
        
        content_layout.addWidget(left_container, 1)
        
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = QLabel("Detalhes:")
        details_label.setStyleSheet("color: #1a2540; font-weight: bold; font-size: 14px;")
        right_layout.addWidget(details_label)
        
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
                background: #E67E22;
                color: white;
            }
            QTabBar::tab:hover {
                background: #D0D0D0;
            }
        """)
        
        info_tab_container = QWidget()
        info_tab_layout = QVBoxLayout(info_tab_container)
        info_tab_layout.setContentsMargins(0, 0, 0, 0)
        
        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        self.details_browser.setHtml("<div style='text-align: center; color: #666; margin-top: 20px;'>Selecione um membro para ver os detalhes</div>")
        info_tab_layout.addWidget(self.details_browser)
        
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.addStretch()
        
        self.delete_button = QPushButton("🗑️ Deletar")
        self.delete_button.setProperty("role", "danger")
        self.delete_button.setFixedWidth(120)
        self.delete_button.setFixedHeight(35)
        self.delete_button.clicked.connect(self.delete_requested.emit)
        self.delete_button.setVisible(False)
        button_layout.addWidget(self.delete_button)
        
        self.renew_button = QPushButton("🔄 Renovar Plano")
        self.renew_button.setProperty("role", "secondary")
        self.renew_button.setFixedWidth(150)
        self.renew_button.setFixedHeight(35)
        self.renew_button.clicked.connect(self.renew_requested.emit)
        self.renew_button.setVisible(False)
        button_layout.addWidget(self.renew_button)

        self.quick_payment_button = QPushButton("💵 Registrar Pagamento")
        self.quick_payment_button.setProperty("role", "secondary")
        self.quick_payment_button.setFixedWidth(180)
        self.quick_payment_button.setFixedHeight(35)
        self.quick_payment_button.clicked.connect(self.quick_payment_requested.emit)
        self.quick_payment_button.setVisible(False)
        button_layout.addWidget(self.quick_payment_button)

        self.whatsapp_button = QPushButton("💬 WhatsApp")
        self.whatsapp_button.setProperty("role", "secondary")
        self.whatsapp_button.setFixedWidth(130)
        self.whatsapp_button.setFixedHeight(35)
        self.whatsapp_button.clicked.connect(self.whatsapp_requested.emit)
        self.whatsapp_button.setVisible(False)
        button_layout.addWidget(self.whatsapp_button)

        self.history_button = QPushButton("📜 Histórico")
        self.history_button.setProperty("role", "secondary")
        self.history_button.setFixedWidth(120)
        self.history_button.setFixedHeight(35)
        self.history_button.clicked.connect(self._open_history_tab)
        self.history_button.setVisible(False)
        button_layout.addWidget(self.history_button)
        
        self.edit_button = QPushButton("✏️ Editar")
        self.edit_button.setProperty("role", "secondary")
        self.edit_button.setFixedWidth(120)
        self.edit_button.setFixedHeight(35)
        self.edit_button.clicked.connect(self.edit_requested.emit)
        self.edit_button.setVisible(False)
        button_layout.addWidget(self.edit_button)
        
        info_tab_layout.addWidget(button_container)
        self.member_tabs.addTab(info_tab_container, "Informações")
        
        self.history_browser = QTextBrowser()
        self.history_browser.setOpenExternalLinks(False)
        self.history_browser.setHtml("<p style='color: #888888;'>Selecione um membro para ver o histórico.</p>")
        self.member_tabs.addTab(self.history_browser, "Histórico de Frequência")
        
        self.financial_browser = QTextBrowser()
        self.financial_browser.setOpenExternalLinks(False)
        self.financial_browser.setHtml("<p style='color: #888888;'>Selecione um membro para ver o histórico financeiro.</p>")
        self.member_tabs.addTab(self.financial_browser, "Histórico Financeiro")
        
        right_layout.addWidget(self.member_tabs)
        
        content_layout.addWidget(right_container, 2)
        
        layout.addLayout(content_layout)
        
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
        self.page_label.setStyleSheet("font-weight: bold; color: #E67E22;")
        pagination_layout.addWidget(self.page_label)
        
        pagination_layout.addStretch()
        
        self.next_button = QPushButton("Próxima ▶")
        self.next_button.setMaximumWidth(100)
        pagination_layout.addWidget(self.next_button)
        
        self.last_button = QPushButton("Última ⏭")
        self.last_button.setMaximumWidth(100)
        pagination_layout.addWidget(self.last_button)
        
        layout.addLayout(pagination_layout)
        
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
        self.sort_combo.setCurrentIndex(0)
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
        sort_data = self.sort_combo.currentData() or ("nome", "asc")
        return {
            'text': self.search_input.text().strip(),
            'plan': self.plan_filter.currentData() or "",
            'status': status_text if status_text != "Todos" else "",
            'sort_by': sort_data[0],
            'sort_dir': sort_data[1]
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
            self.info_label.setText("Não encontramos membros com esses filtros. Ajuste a busca e tente novamente.")
        
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
        self.details_browser.setHtml("<div style='text-align: center; color: #666; margin-top: 20px;'>Selecione um membro na lista para ver os detalhes e ações rápidas.</div>")

        self.edit_button.setVisible(False)
        self.renew_button.setVisible(False)
        self.delete_button.setVisible(False)
        self.quick_payment_button.setVisible(False)
        self.whatsapp_button.setVisible(False)
        self.history_button.setVisible(False)

    def _on_item_clicked(self, item):
        """Manipula o clique em um item da lista."""
        member_data = item.data(Qt.ItemDataRole.UserRole)
        if member_data:
            self.member_selected.emit(member_data)
            
    def select_member_by_id(self, member_id: int, member_name: str):
        """
        Seleciona um membro específico na lista.
        
        Args:
            member_id: ID do membro a ser selecionado
            member_name: Nome do membro (para filtro)
        """
        # 1. Definir o filtro de nome
        self.search_input.setText(member_name)
        
        # 2. Aplicar filtro (isso recarrega a lista)
        self._on_filter()
        
        # 3. Encontrar e selecionar o item na lista
        for i in range(self.members_list.count()):
            item = self.members_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            
            if data and data.get('id') == member_id:
                # Selecionar visualmente
                self.members_list.setCurrentItem(item)
                # Disparar evento de clique
                self._on_item_clicked(item)
                break

    def display_member_data(self, member_data: dict):
        """Exibe os detalhes do membro no browser."""
        self.current_member_data = member_data
        
        # Formatar e exibir dados
        html = self._format_member_data(member_data)
        self.details_browser.setHtml(html)
        
        # Mostrar botões
        self.edit_button.setVisible(True)
        self.delete_button.setVisible(True)
        self.quick_payment_button.setVisible(True)
        self.whatsapp_button.setVisible(True)
        self.history_button.setVisible(True)
        
        # Mostrar botão de renovar apenas para planos renováveis
        from src.config import PLANOS_COM_VENCIMENTO, PLANOS_NAO_RENOVAVEIS
        plano = member_data.get('plano', '')
        is_renewable = plano not in PLANOS_NAO_RENOVAVEIS and plano in PLANOS_COM_VENCIMENTO
        self.renew_button.setVisible(is_renewable)

    def _open_history_tab(self):
        """Abre a aba de histórico de frequência no atalho rápido."""
        self.member_tabs.setCurrentIndex(1)
        self.history_requested.emit()

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
        from src.ui.components.member_info_formatter import format_member_data, calculate_monthly_frequency
        member_id = member_data.get('id')
        freq = calculate_monthly_frequency(member_id) if member_id else 0
        return format_member_data(member_data, freq)


    def _format_member_history(self, member_name: str, history: list) -> str:
        """Formata o histórico do membro em HTML."""
        if not history:
            return f"""
                <div style="padding: 20px;">
                    <h3 style="color: #007ACC;">Histórico de {member_name}</h3>
                    <p style="color: #888888; font-style: italic;">
                        Ainda não há check-ins. Faça um check-in para iniciar o histórico.
                    </p>
                </div>
            """

        ultimo_checkin = None
        try:
            ultimo_checkin = max(datetime.fromisoformat(c["checkin_datetime"]) for c in history)
        except Exception:
            pass
        ultimo_checkin_label = (
            ultimo_checkin.strftime("%d/%m/%Y às %H:%M")
            if ultimo_checkin else "Não disponível"
        )
        
        html = f"""
            <div style="padding: 20px; font-family: 'Segoe UI', Arial, sans-serif;">
                <h3 style="color: #007ACC; margin-bottom: 15px;">
                    Histórico de Frequência: {member_name}
                </h3>
                <div style="background:#F8F9FA; border:1px solid #E2E8F0; border-radius:8px; padding:12px; margin-bottom:14px;">
                    <div style="color:#1A2540; margin-bottom:6px;">
                        Total de check-ins: <strong style="color:#E67E22;">{len(history)}</strong>
                    </div>
                    <div style="color:#4A5568;">
                        Último check-in: <strong>{ultimo_checkin_label}</strong>
                    </div>
                </div>
                <details>
                    <summary style="cursor:pointer; color:#E67E22; font-weight:700; margin-bottom:10px;">
                        Ver histórico completo
                    </summary>
                    <div style="max-height: 500px; overflow-y: auto; padding-top:8px;">
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
                </details>
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
                        Ainda não há pagamentos. Use o atalho “Registrar Pagamento” para lançar a primeira transação.
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
                <details>
                    <summary style="cursor:pointer; color:#E67E22; font-weight:700; margin-bottom:10px;">
                        Ver histórico financeiro completo
                    </summary>
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
                </details>
            </div>
        """
        
        return html

    def _calculate_monthly_frequency(self, member_id: int) -> int:
        """Calcula quantos check-ins o membro fez no mês atual."""
        from src.ui.components.member_info_formatter import calculate_monthly_frequency
        return calculate_monthly_frequency(member_id)
