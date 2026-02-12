"""Tela de busca de membros."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QTextBrowser, QTabWidget
)
from PyQt6.QtCore import Qt

from src.config import PLANOS_COM_VENCIMENTO


class MemberSearchScreen(QWidget):
    """Tela de busca de membros."""
    
    def __init__(self):
        super().__init__()
        self.current_member_data = None  # Armazena os dados do membro atual
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Buscar Membro")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Informação do mês atual
        from src.utils.utils import get_current_sheet_name
        mes_atual = get_current_sheet_name()
        self.mes_label = QLabel(f"Consultando aba: {mes_atual}")
        self.mes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mes_label.setStyleSheet("font-size: 14px; color: #555555;")
        layout.addWidget(self.mes_label)
        
        # Campo de busca
        search_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Digite o nome do membro...")
        search_layout.addWidget(self.name_input)
        
        self.search_button = QPushButton("Buscar")
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # Container com duas colunas: lista de resultados e detalhes
        results_layout = QHBoxLayout()
        
        # Coluna esquerda: Lista de resultados
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        results_label = QLabel("Resultados:")
        results_label.setStyleSheet("color: #007ACC; font-weight: bold; font-size: 14px;")
        left_layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #DDDDDD;
            }
            QListWidget::item:hover {
                background-color: #F0F0F0;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
                color: white;
            }
        """)
        left_layout.addWidget(self.results_list)
        
        results_layout.addWidget(left_container, 1)
        
        # Coluna direita: Detalhes do membro com abas
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header com título apenas
        details_label = QLabel("Detalhes:")
        details_label.setStyleSheet("color: #007ACC; font-weight: bold; font-size: 14px;")
        right_layout.addWidget(details_label)
        
        # Tab Widget para Informações e Histórico
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
        
        # Aba 1: Informações do Membro com botão de editar
        info_tab_container = QWidget()
        info_tab_layout = QVBoxLayout(info_tab_container)
        info_tab_layout.setContentsMargins(0, 0, 0, 0)
        info_tab_layout.setSpacing(0)
        
        self.member_result_browser = QTextBrowser()
        self.member_result_browser.setOpenExternalLinks(True)
        self.member_result_browser.setHtml(self._get_initial_message())
        info_tab_layout.addWidget(self.member_result_browser)
        
        # Botões de ação no canto inferior direito
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
        self.delete_button.setVisible(False)  # Escondido até que um membro seja selecionado
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
        self.renew_button.setVisible(False)  # Escondido até que um membro seja selecionado
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
        self.edit_button.setVisible(False)  # Escondido até que um membro seja selecionado
        button_layout.addWidget(self.edit_button)
        
        info_tab_layout.addWidget(button_container)
        
        self.member_tabs.addTab(info_tab_container, "Informações")
        
        # Aba 2: Histórico de Frequência
        self.member_history_browser = QTextBrowser()
        self.member_history_browser.setOpenExternalLinks(False)
        self.member_history_browser.setHtml("<p style='color: #888888;'>Selecione um membro para ver o histórico.</p>")
        self.member_history_browser.anchorClicked.connect(self._on_history_link_clicked)
        self.member_tabs.addTab(self.member_history_browser, "Histórico de Frequência")
        
        # Aba 3: Histórico Financeiro
        self.member_financial_browser = QTextBrowser()
        self.member_financial_browser.setOpenExternalLinks(False)
        self.member_financial_browser.setHtml("<p style='color: #888888;'>Selecione um membro para ver o histórico financeiro.</p>")
        self.member_tabs.addTab(self.member_financial_browser, "Histórico Financeiro")
        
        right_layout.addWidget(self.member_tabs)
        
        results_layout.addWidget(right_container, 2)
        
        layout.addLayout(results_layout)
    
    def _get_initial_message(self):
        """Retorna a mensagem inicial."""
        return """
            <div style="text-align: center; padding: 40px;">
                <h3 style="color: #007ACC;">Buscar Membro</h3>
                <p style="color: #333333;">Digite o nome do membro e clique em buscar.</p>
            </div>
        """
    
    def set_searching_state(self):
        """Define o estado de busca."""
        self.search_button.setText("Buscando...")
        self.search_button.setEnabled(False)
        self.results_list.clear()
        self.member_result_browser.clear()
        self.edit_button.setVisible(False)  # Esconde os botões durante a busca
        self.delete_button.setVisible(False)
        self.current_member_data = None
    
    def set_ready_state(self):
        """Define o estado pronto."""
        self.search_button.setText("Buscar")
        self.search_button.setEnabled(True)
    
    def show_no_results(self):
        """Mostra mensagem de nenhum resultado."""
        self.member_result_browser.setHtml("""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #FF6B6B;">Nenhum membro encontrado</h3>
                <p style="color: #555555;">Tente buscar com outros termos.</p>
            </div>
        """)
        self.edit_button.setVisible(False)
        self.delete_button.setVisible(False)
    
    def show_empty_search_warning(self):
        """Mostra aviso de busca vazia."""
        self.member_result_browser.setHtml("""
            <div style="text-align: center; padding: 20px;">
                <p style="color: #FF6B6B;">Por favor, digite um nome para buscar.</p>
            </div>
        """)
        self.edit_button.setVisible(False)
        self.delete_button.setVisible(False)
    
    def populate_results(self, results: list):
        """Popula a lista de resultados."""
        self.results_list.clear()
        for result in results:
            nome = result.get('nome', '')
            apelido = result.get('apelido', '')
            display_text = f"{nome} ({apelido})" if apelido else nome
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, result.get('id', result.get('row_index', 0)))
            self.results_list.addItem(item)
        
        self.member_result_browser.setHtml(f"""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #007ACC;">{len(results)} resultado(s) encontrado(s)</h3>
                <p style="color: #555555;">Clique em um nome na lista ao lado para ver os detalhes.</p>
            </div>
        """)
        self.edit_button.setVisible(False)  # Esconde até selecionar um membro
        self.delete_button.setVisible(False)
    
    def display_member_data(self, member_data: dict):
        """Exibe os dados do membro."""
        self.current_member_data = member_data  # Armazena os dados atuais
        html = self._format_member_data(member_data)
        self.member_result_browser.setHtml(html)
        self.edit_button.setVisible(True)  # Mostra os botões de ação
        self.delete_button.setVisible(True)
        
        # Mostrar botão de renovar apenas para planos renováveis
        plano = member_data.get('plano', '')
        planos_nao_renovaveis = ["Diária", "Diária Boulder", "Gympass", "Totalpass", "Cortesia"]
        is_renewable = plano not in planos_nao_renovaveis and plano in PLANOS_COM_VENCIMENTO
        self.renew_button.setVisible(is_renewable)
    
    def display_member_history(self, member_id: int, member_name: str, history: list):
        """Exibe o histórico do membro."""
        html = self._format_member_history(member_name, history)
        self.member_history_browser.setHtml(html)
    
    def display_member_financial_history(self, member_id: int, member_name: str, payments: list):
        """Exibe o histórico financeiro do membro."""
        html = self._format_member_financial_history(member_name, payments)
        self.member_financial_browser.setHtml(html)
    
    def show_error(self):
        """Mostra mensagem de erro."""
        self.member_result_browser.setHtml("""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #FF6B6B;">Erro ao carregar dados</h3>
            </div>
        """)
        self.member_history_browser.setHtml("""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #FF6B6B;">Erro ao carregar histórico</h3>
            </div>
        """)
        self.edit_button.setVisible(False)
        self.delete_button.setVisible(False)
        self.renew_button.setVisible(False)
    
    def open_edit_dialog(self):
        """Abre o diálogo de edição do membro atual."""
        if not self.current_member_data:
            return
        
        from src.ui.dialogs.edit_member_dialog import EditMemberDialog
        
        dialog = EditMemberDialog(self.current_member_data, self)
        
        # Quando o membro for atualizado, o sinal será emitido
        # A conexão desse sinal será feita no controller
        
        dialog.exec()
    
    def open_renew_dialog(self):
        """Abre o diálogo de renovação do plano."""
        if not self.current_member_data:
            return
        
        from src.ui.dialogs.renew_plan_dialog import RenewPlanDialog
        
        dialog = RenewPlanDialog(self.current_member_data, self)
        
        # Quando o plano for renovado, o sinal será emitido
        # A conexão desse sinal será feita no controller
        
        dialog.exec()
    
    def _on_history_link_clicked(self, url):
        """Manipula cliques em links no histórico."""
        from PyQt6.QtCore import QUrl
        
        url_str = url.toString() if isinstance(url, QUrl) else str(url)
        
        # Verifica se é um link de deletar
        if url_str.startswith("delete:"):
            checkin_id = int(url_str.split(":")[1])
            # Emite um sinal ou chama diretamente o controller
            # Por enquanto, vamos armazenar o ID para ser tratado externamente
            self.request_delete_checkin(checkin_id)
        # Verifica se é um link de editar
        elif url_str.startswith("edit:"):
            checkin_id = int(url_str.split(":")[1])
            self.request_edit_checkin(checkin_id)
    
    def request_delete_checkin(self, checkin_id: int):
        """
        Solicita a exclusão de um check-in.
        Este método será conectado ao controller na main_window.
        """
        # Placeholder - será conectado no main_window
        pass
    
    def request_edit_checkin(self, checkin_id: int):
        """
        Solicita a edição de um check-in.
        Este método será conectado ao controller na main_window.
        """
        # Placeholder - será conectado no main_window
        pass
    
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
            checkin_dt = datetime.fromisoformat(checkin['checkin_datetime'])
            month_name = checkin_dt.strftime('%B')
            month_pt = months_pt.get(month_name, month_name)
            month_year = f"{month_pt} de {checkin_dt.year}"
            
            if month_year not in grouped:
                grouped[month_year] = []
            grouped[month_year].append(checkin)
        
        for month_year, checkins in grouped.items():
            html += f"""
                <div style="margin-bottom: 20px;">
                    <h4 style="color: #007ACC; margin-bottom: 10px;">{month_year}</h4>
                    <div style="margin-left: 15px;">
            """
            
            for checkin_data in checkins:
                dt = datetime.fromisoformat(checkin_data['checkin_datetime'])
                checkin_id = checkin_data['id']
                day_name = dt.strftime('%A')
                date_str = dt.strftime('%d/%m/%Y')
                time_str = dt.strftime('%H:%M')
                day_name_pt = days_pt.get(day_name, day_name)
                
                html += f"""
                    <div style="margin-bottom: 8px; padding: 8px; background: #F0F0F0; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: #333333;">📅 {day_name_pt}</span>
                            <span style="color: #555555; margin-left: 10px;">{date_str}</span>
                            <span style="color: #007ACC; margin-left: 10px;">⏰ {time_str}</span>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <a href="edit:{checkin_id}" style="color: #007ACC; text-decoration: none; font-weight: bold; padding: 4px 8px; background: #E3F2FD; border-radius: 4px;">✏️ Editar</a>
                            <a href="delete:{checkin_id}" style="color: #FF6B6B; text-decoration: none; font-weight: bold; padding: 4px 8px; background: #FFE5E5; border-radius: 4px;">🗑️ Deletar</a>
                        </div>
                    </div>
                """
            
            html += """
                    </div>
                </div>
            """
        
        html += """
                </div>
            </div>
        """
        
        return html
    

    def _calculate_monthly_frequency(self, member_id: int) -> int:
        """Calcula quantos check-ins o membro fez no mes atual."""
        from src.ui.components.member_info_formatter import calculate_monthly_frequency
        return calculate_monthly_frequency(member_id)

    
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
        ticket_medio = total_pago / num_transacoes if num_transacoes > 0 else 0
        
        # Agrupar por tipo de transação
        tipos_count = {}
        tipos_total = {}
        for p in payments:
            tipo = p.get('tipo_transacao', 'Não especificado')
            tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
            tipos_total[tipo] = tipos_total.get(tipo, 0) + p.get('valor', 0)
        
        html = f"""
            <div style="padding: 20px; font-family: 'Segoe UI', Arial, sans-serif;">
                <h3 style="color: #007ACC; margin-bottom: 15px;">
                    Histórico Financeiro: {member_name}
                </h3>
                
                <!-- Resumo Financeiro -->
                <div style="background: #F0F8FF; border-left: 4px solid #007ACC; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                    <h4 style="margin: 0 0 10px 0; color: #007ACC;">Resumo Geral</h4>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
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
                        <div>
                            <div style="font-size: 12px; color: #666;">Ticket Médio</div>
                            <div style="font-size: 20px; font-weight: bold; color: #FFA500;">
                                R$ {ticket_medio:,.2f}
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Breakdown por Tipo -->
                <div style="background: #FFF9E6; border-left: 4px solid #FFA500; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                    <h4 style="margin: 0 0 10px 0; color: #FFA500;">Por Tipo de Transação</h4>
                    <table style="width: 100%; border-collapse: collapse;">
        """
        
        for tipo in sorted(tipos_count.keys()):
            count = tipos_count[tipo]
            total = tipos_total[tipo]
            perc = (total / total_pago * 100) if total_pago > 0 else 0
            
            html += f"""
                        <tr style="border-bottom: 1px solid #EEEEEE;">
                            <td style="padding: 8px; color: #333;">{tipo}</td>
                            <td style="padding: 8px; text-align: center; color: #666;">{count}x</td>
                            <td style="padding: 8px; text-align: right; font-weight: bold; color: #28a745;">
                                R$ {total:,.2f}
                            </td>
                            <td style="padding: 8px; text-align: right; color: #007ACC;">
                                {perc:.1f}%
                            </td>
                        </tr>
            """
        
        html += """
                    </table>
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
            descricao = payment.get('descricao', '')
            valor = payment.get('valor', 0)
            metodo = payment.get('metodo_pagamento', 'N/A')
            data = payment.get('data_pagamento', '')
            nova_data_vencimento = payment.get('nova_data_vencimento', '')
            
            # Formatar data
            try:
                data_dt = datetime.fromisoformat(data)
                data_str = data_dt.strftime('%d/%m/%Y às %H:%M')
            except:
                data_str = data
            
            # Cor do tipo
            if 'Renovação' in tipo or 'Plano' in tipo:
                tipo_color = '#28a745'
                tipo_icon = '🔄'
            elif 'Diária' in tipo or 'Gympass' in tipo or 'Totalpass' in tipo:
                tipo_color = '#007ACC'
                tipo_icon = '✓'
            else:
                tipo_color = '#FFA500'
                tipo_icon = '💰'
            
            html += f"""
                    <div style="margin-bottom: 12px; padding: 12px; background: #FAFAFA; 
                                border-left: 4px solid {tipo_color}; border-radius: 4px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <div>
                                <span style="font-size: 16px;">{tipo_icon}</span>
                                <strong style="color: {tipo_color}; font-size: 15px;">{tipo}</strong>
                                {f" - {descricao}" if descricao else ""}
                            </div>
                            <div style="font-size: 18px; font-weight: bold; color: #28a745;">
                                R$ {valor:,.2f}
                            </div>
                        </div>
                        <div style="font-size: 12px; color: #666;">
                            <span>📅 {data_str}</span>
                            <span style="margin-left: 15px;">💳 {metodo}</span>
            """
            
            if nova_data_vencimento:
                html += f"""
                            <span style="margin-left: 15px;">⏰ Novo vencimento: {nova_data_vencimento}</span>
                """
            
            html += """
                        </div>
                    </div>
            """
        
        html += """
                </div>
            </div>
        """
        
        return html
