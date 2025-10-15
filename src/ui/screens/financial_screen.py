"""Tela de gestão financeira."""

from datetime import datetime, timedelta
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QComboBox, QTextBrowser,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QDate


class FinancialScreen(QWidget):
    """Tela de gestão financeira com dashboards e relatórios."""
    
    def __init__(self):
        super().__init__()
        self._card_labels = {}  # Armazena referências aos labels dos cards
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Gestão Financeira")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Controles de Período
        period_group = QGroupBox("Filtrar por Período")
        period_layout = QHBoxLayout(period_group)
        
        # Selector de período rápido
        period_layout.addWidget(QLabel("Período:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Hoje",
            "Esta Semana",
            "Este Mês",
            "Últimos 30 Dias",
            "Últimos 3 Meses",
            "Este Ano",
            "Personalizado"
        ])
        self.period_combo.setCurrentText("Este Mês")
        period_layout.addWidget(self.period_combo)
        
        period_layout.addSpacing(20)
        
        # Data inicial
        period_layout.addWidget(QLabel("De:"))
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("dd/MM/yyyy")
        self.start_date_input.setDate(QDate.currentDate().addDays(-30))
        self.start_date_input.setEnabled(False)
        period_layout.addWidget(self.start_date_input)
        
        # Data final
        period_layout.addWidget(QLabel("Até:"))
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDisplayFormat("dd/MM/yyyy")
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setEnabled(False)
        period_layout.addWidget(self.end_date_input)
        
        period_layout.addSpacing(20)
        
        # Botão de atualizar
        self.update_button = QPushButton("Atualizar")
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #005FA3;
            }
        """)
        period_layout.addWidget(self.update_button)
        
        period_layout.addSpacing(10)
        
        # Botão de gráfico de distribuição de check-ins por plano
        self.plan_chart_button = QPushButton("📊 Check-ins por Plano")
        self.plan_chart_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        period_layout.addWidget(self.plan_chart_button)
        
        period_layout.addStretch()
        
        layout.addWidget(period_group)
        
        # Cards de Resumo
        summary_layout = QHBoxLayout()
        
        # Card 1: Receita Total
        card1, label1 = self._create_summary_card(
            "Receita Total",
            "R$ 0,00",
            "#28a745"
        )
        self.total_revenue_card = card1
        self._card_labels['revenue'] = label1
        summary_layout.addWidget(card1)
        
        # Card 2: Transações
        card2, label2 = self._create_summary_card(
            "Transações",
            "0",
            "#007ACC"
        )
        self.transactions_card = card2
        self._card_labels['transactions'] = label2
        summary_layout.addWidget(card2)
        
        # Card 3: Ticket Médio
        card3, label3 = self._create_summary_card(
            "Ticket Médio",
            "R$ 0,00",
            "#FFA500"
        )
        self.avg_ticket_card = card3
        self._card_labels['avg_ticket'] = label3
        summary_layout.addWidget(card3)
        
        layout.addLayout(summary_layout)
        
        # Área de Gráficos e Detalhes
        content_layout = QHBoxLayout()
        
        # Coluna Esquerda: Breakdown por Tipo
        left_group = QGroupBox("Receita por Tipo de Transação")
        left_layout = QVBoxLayout(left_group)
        
        self.breakdown_browser = QTextBrowser()
        self.breakdown_browser.setOpenExternalLinks(False)
        self.breakdown_browser.setHtml(self._get_initial_breakdown_message())
        left_layout.addWidget(self.breakdown_browser)
        
        content_layout.addWidget(left_group, 1)
        
        # Coluna Direita: Transações Recentes
        right_group = QGroupBox("Transações Recentes")
        right_layout = QVBoxLayout(right_group)
        
        self.transactions_browser = QTextBrowser()
        self.transactions_browser.setOpenExternalLinks(False)
        self.transactions_browser.setHtml(self._get_initial_transactions_message())
        right_layout.addWidget(self.transactions_browser)
        
        content_layout.addWidget(right_group, 1)
        
        layout.addLayout(content_layout)
        
        # Conectar sinais
        self.period_combo.currentTextChanged.connect(self._on_period_changed)
    
    def _create_summary_card(self, title: str, value: str, color: str) -> tuple[QGroupBox, QLabel]:
        """Cria um card de resumo."""
        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333333;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        return card, value_label
    
    def _on_period_changed(self, period: str):
        """Atualiza as datas baseado no período selecionado."""
        today = QDate.currentDate()
        
        if period == "Personalizado":
            self.start_date_input.setEnabled(True)
            self.end_date_input.setEnabled(True)
            return
        else:
            self.start_date_input.setEnabled(False)
            self.end_date_input.setEnabled(False)
        
        if period == "Hoje":
            self.start_date_input.setDate(today)
            self.end_date_input.setDate(today)
        elif period == "Esta Semana":
            # Segunda-feira da semana atual
            days_since_monday = today.dayOfWeek() - 1
            monday = today.addDays(-days_since_monday)
            self.start_date_input.setDate(monday)
            self.end_date_input.setDate(today)
        elif period == "Este Mês":
            first_day = QDate(today.year(), today.month(), 1)
            self.start_date_input.setDate(first_day)
            self.end_date_input.setDate(today)
        elif period == "Últimos 30 Dias":
            self.start_date_input.setDate(today.addDays(-30))
            self.end_date_input.setDate(today)
        elif period == "Últimos 3 Meses":
            self.start_date_input.setDate(today.addMonths(-3))
            self.end_date_input.setDate(today)
        elif period == "Este Ano":
            first_day = QDate(today.year(), 1, 1)
            self.start_date_input.setDate(first_day)
            self.end_date_input.setDate(today)
    
    def _get_initial_breakdown_message(self) -> str:
        """Retorna a mensagem inicial do breakdown."""
        return """
            <div style="text-align: center; padding: 40px;">
                <h3 style="color: #007ACC;">Receita por Tipo</h3>
                <p style="color: #333333;">Clique em "Atualizar" para carregar os dados.</p>
            </div>
        """
    
    def _get_initial_transactions_message(self) -> str:
        """Retorna a mensagem inicial das transações."""
        return """
            <div style="text-align: center; padding: 40px;">
                <h3 style="color: #007ACC;">Transações</h3>
                <p style="color: #333333;">Clique em "Atualizar" para carregar os dados.</p>
            </div>
        """
    
    def update_summary(self, total_receita: float, total_transacoes: int, ticket_medio: float):
        """Atualiza os cards de resumo."""
        self._card_labels['revenue'].setText(f"R$ {total_receita:,.2f}")
        self._card_labels['transactions'].setText(f"{total_transacoes}")
        self._card_labels['avg_ticket'].setText(f"R$ {ticket_medio:,.2f}")
    
    def update_breakdown(self, breakdown_data: list):
        """Atualiza o breakdown de receita por tipo."""
        if not breakdown_data:
            self.breakdown_browser.setHtml("""
                <div style="text-align: center; padding: 20px;">
                    <p style="color: #888888;">Nenhuma transação encontrada no período.</p>
                </div>
            """)
            return
        
        html = """
            <div style="padding: 15px; font-family: 'Segoe UI', Arial, sans-serif;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 2px solid #007ACC;">
                            <th style="text-align: left; padding: 10px; color: #007ACC;">Tipo</th>
                            <th style="text-align: right; padding: 10px; color: #007ACC;">Qtd</th>
                            <th style="text-align: right; padding: 10px; color: #007ACC;">Valor</th>
                            <th style="text-align: right; padding: 10px; color: #007ACC;">%</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        total = sum(item['total_valor'] for item in breakdown_data)
        
        for item in breakdown_data:
            tipo = item['tipo_transacao']
            quantidade = item['quantidade']
            valor = item['total_valor']
            percentual = (valor / total * 100) if total > 0 else 0
            
            html += f"""
                <tr style="border-bottom: 1px solid #EEEEEE;">
                    <td style="padding: 10px; color: #333333;">{tipo}</td>
                    <td style="text-align: right; padding: 10px; color: #555555;">{quantidade}</td>
                    <td style="text-align: right; padding: 10px; color: #28a745; font-weight: bold;">
                        R$ {valor:,.2f}
                    </td>
                    <td style="text-align: right; padding: 10px; color: #007ACC;">
                        {percentual:.1f}%
                    </td>
                </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        """
        
        self.breakdown_browser.setHtml(html)
    
    def update_transactions(self, transactions: list):
        """Atualiza a lista de transações recentes."""
        if not transactions:
            self.transactions_browser.setHtml("""
                <div style="text-align: center; padding: 20px;">
                    <p style="color: #888888;">Nenhuma transação encontrada no período.</p>
                </div>
            """)
            return
        
        html = """
            <div style="padding: 15px; font-family: 'Segoe UI', Arial, sans-serif;">
        """
        
        for trans in transactions:
            member_nome = trans.get('member_nome', 'N/A')
            tipo = trans['tipo_transacao']
            descricao = trans.get('descricao', '')
            valor = trans['valor']
            metodo = trans.get('metodo_pagamento', 'N/A')
            data = trans['data_pagamento']
            
            # Parse da data
            try:
                data_dt = datetime.fromisoformat(data)
                data_str = data_dt.strftime('%d/%m/%Y %H:%M')
            except:
                data_str = data
            
            html += f"""
                <div style="margin-bottom: 15px; padding: 12px; background: #F8F8F8; border-left: 4px solid #007ACC; border-radius: 4px;">
                    <div style="margin-bottom: 5px;">
                        <strong style="color: #007ACC; font-size: 16px;">R$ {valor:,.2f}</strong>
                        <span style="color: #888888; font-size: 12px; float: right;">{data_str}</span>
                    </div>
                    <div style="color: #333333; margin-bottom: 3px;">
                        <strong>{tipo}</strong>
                        {f" - {descricao}" if descricao else ""}
                    </div>
                    <div style="color: #666666; font-size: 12px;">
                        Membro: {member_nome} | Método: {metodo}
                    </div>
                </div>
            """
        
        html += """
            </div>
        """
        
        self.transactions_browser.setHtml(html)
    
    def show_loading(self):
        """Mostra estado de carregamento."""
        self.breakdown_browser.setHtml("""
            <div style="text-align: center; padding: 40px;">
                <p style="color: #007ACC; font-size: 16px;">Carregando dados...</p>
            </div>
        """)
        self.transactions_browser.setHtml("""
            <div style="text-align: center; padding: 40px;">
                <p style="color: #007ACC; font-size: 16px;">Carregando transações...</p>
            </div>
        """)
