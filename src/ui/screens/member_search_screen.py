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
        
        # Aba 1: Informações do Membro
        self.member_result_browser = QTextBrowser()
        self.member_result_browser.setOpenExternalLinks(True)
        self.member_result_browser.setHtml(self._get_initial_message())
        self.member_tabs.addTab(self.member_result_browser, "Informações")
        
        # Aba 2: Histórico de Frequência
        self.member_history_browser = QTextBrowser()
        self.member_history_browser.setOpenExternalLinks(False)
        self.member_history_browser.setHtml("<p style='color: #888888;'>Selecione um membro para ver o histórico.</p>")
        self.member_tabs.addTab(self.member_history_browser, "Histórico de Frequência")
        
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
    
    def show_empty_search_warning(self):
        """Mostra aviso de busca vazia."""
        self.member_result_browser.setHtml("""
            <div style="text-align: center; padding: 20px;">
                <p style="color: #FF6B6B;">Por favor, digite um nome para buscar.</p>
            </div>
        """)
    
    def populate_results(self, results: list):
        """Popula a lista de resultados."""
        self.results_list.clear()
        for result in results:
            item = QListWidgetItem(result['nome'])
            item.setData(Qt.ItemDataRole.UserRole, result.get('id', result.get('row_index', 0)))
            self.results_list.addItem(item)
        
        self.member_result_browser.setHtml(f"""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #007ACC;">{len(results)} resultado(s) encontrado(s)</h3>
                <p style="color: #555555;">Clique em um nome na lista ao lado para ver os detalhes.</p>
            </div>
        """)
    
    def display_member_data(self, member_data: dict):
        """Exibe os dados do membro."""
        html = self._format_member_data(member_data)
        self.member_result_browser.setHtml(html)
    
    def display_member_history(self, member_id: int, member_name: str, history: list):
        """Exibe o histórico do membro."""
        html = self._format_member_history(member_name, history)
        self.member_history_browser.setHtml(html)
    
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
    
    def _format_member_data(self, member_data: dict) -> str:
        """Formata os dados do membro em HTML."""
        fields = [
            ('nome', 'Nome'),
            ('plano', 'Plano'),
        ]
        
        plano = member_data.get('plano', '')
        if plano in PLANOS_COM_VENCIMENTO:
            fields.append(('vencimento_plano', 'Vencimento do Plano'))
        
        fields.extend([
            ('estado_plano', 'Estado do Plano'),
            ('data_nascimento', 'Data de Nascimento'),
            ('whatsapp', 'WhatsApp'),
            ('genero', 'Gênero'),
            ('frequencia', 'Frequência'),
            ('calcado', 'Calçado')
        ])
        
        html = """
            <div style="padding: 20px;">
                <h2 style="color: #007ACC; text-align: center; margin-bottom: 20px;">Dados do Membro</h2>
                <div style="background-color: #F8F8F8; border: 1px solid #DDDDDD; border-radius: 8px; padding: 15px;">
        """
        
        for field_key, field_label in fields:
            value = member_data.get(field_key, '')
            if value:
                if field_key == 'whatsapp' and value:
                    digits = ''.join(filter(str.isdigit, value))
                    if len(digits) == 11:
                        whatsapp_link = f"https://wa.me/55{digits}"
                        html += f"""
                            <div style="margin-bottom: 10px;">
                                <strong style="color: #333333;">{field_label}:</strong>
                                <span style="color: #555555;"> {value}</span>
                                <a href="{whatsapp_link}" style="color: #007ACC; margin-left: 10px;">[Abrir WhatsApp]</a>
                            </div>
                        """
                    else:
                        html += f"""
                            <div style="margin-bottom: 10px;">
                                <strong style="color: #333333;">{field_label}:</strong>
                                <span style="color: #555555;"> {value}</span>
                            </div>
                        """
                elif field_key == 'estado_plano':
                    color = '#28a745' if value.upper() == 'ATIVO' else '#FF6B6B'
                    html += f"""
                        <div style="margin-bottom: 10px;">
                            <strong style="color: #333333;">{field_label}:</strong>
                            <span style="color: {color}; font-weight: bold;"> {value}</span>
                        </div>
                    """
                else:
                    html += f"""
                        <div style="margin-bottom: 10px;">
                            <strong style="color: #333333;">{field_label}:</strong>
                            <span style="color: #555555;"> {value}</span>
                        </div>
                    """
            else:
                html += f"""
                    <div style="margin-bottom: 10px;">
                        <strong style="color: #333333;">{field_label}:</strong>
                        <span style="color: #888888; font-style: italic;"> Não informado</span>
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
            checkin_dt = datetime.fromisoformat(checkin['checkin_datetime'])
            month_name = checkin_dt.strftime('%B')
            month_pt = months_pt.get(month_name, month_name)
            month_year = f"{month_pt} de {checkin_dt.year}"
            
            if month_year not in grouped:
                grouped[month_year] = []
            grouped[month_year].append(checkin_dt)
        
        for month_year, dates in grouped.items():
            html += f"""
                <div style="margin-bottom: 20px;">
                    <h4 style="color: #007ACC; margin-bottom: 10px;">{month_year}</h4>
                    <div style="margin-left: 15px;">
            """
            
            for dt in dates:
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
            
            html += """
                    </div>
                </div>
            """
        
        html += """
                </div>
            </div>
        """
        
        return html
