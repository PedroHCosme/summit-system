"""Diálogo com gráficos financeiros - Pizza de check-ins e Evolução de receita."""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QWidget, QDateEdit
)
from PyQt6.QtCore import Qt, QDate

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class FinancialGraphsDialog(QDialog):
    """Diálogo que mostra gráficos financeiros diversos."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gráficos Financeiros")
        self.setModal(False)
        self.resize(1100, 750)
        
        self.plan_data = {}
        self.total_checkins = 0
        self.revenue_data = []
        self.current_graph_type = "pizza"  # "pizza" ou "revenue"
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        self.title_label = QLabel("Check-ins por Plano")
        self.title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #007ACC;
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Seletor de tipo de gráfico - Linha 1
        graph_type_layout = QHBoxLayout()
        
        graph_type_layout.addWidget(QLabel("Tipo de Gráfico:"))
        
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems([
            "Check-ins por Plano",
            "Evolução da Receita"
        ])
        self.graph_type_combo.setCurrentIndex(0)
        self.graph_type_combo.currentIndexChanged.connect(self._on_graph_type_changed)
        graph_type_layout.addWidget(self.graph_type_combo)
        
        graph_type_layout.addStretch()
        layout.addLayout(graph_type_layout)
        
        # Controles de Período
        period_layout = QHBoxLayout()
        
        # Selector de período rápido
        period_layout.addWidget(QLabel("Período:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Hoje",
            "Últimos 7 Dias",
            "Últimos 30 Dias",
            "Este Mês",
            "Mês Passado",
            "Últimos 3 Meses",
            "Este Ano",
            "Personalizado"
        ])
        self.period_combo.setCurrentText("Este Mês")
        self.period_combo.currentTextChanged.connect(self._on_period_changed)
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
        
        period_layout.addStretch()
        
        # Botão de atualizar
        refresh_button = QPushButton("🔄 Atualizar")
        refresh_button.setStyleSheet("""
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
        refresh_button.clicked.connect(self._load_data)
        period_layout.addWidget(refresh_button)
        
        layout.addLayout(period_layout)
        
        # Informação de total
        self.info_label = QLabel("Total de check-ins: 0")
        self.info_label.setStyleSheet("font-size: 14px; color: #555555;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Canvas do matplotlib - aumentado para melhor visualização
        self.figure = Figure(figsize=(11, 7), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Botão de fechar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Fechar")
        close_button.setFixedSize(100, 35)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _on_graph_type_changed(self):
        """Chamado quando o tipo de gráfico é alterado."""
        selected_index = self.graph_type_combo.currentIndex()
        
        if selected_index == 0:  # Check-ins por Plano
            self.current_graph_type = "pizza"
            self.title_label.setText("Check-ins por Plano")
        else:  # Evolução da Receita
            self.current_graph_type = "revenue"
            self.title_label.setText("Evolução da Receita")
        
        self._generate_chart()
    
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
        elif period == "Últimos 7 Dias":
            self.start_date_input.setDate(today.addDays(-7))
            self.end_date_input.setDate(today)
        elif period == "Últimos 30 Dias":
            self.start_date_input.setDate(today.addDays(-30))
            self.end_date_input.setDate(today)
        elif period == "Este Mês":
            first_day = QDate(today.year(), today.month(), 1)
            self.start_date_input.setDate(first_day)
            self.end_date_input.setDate(today)
        elif period == "Mês Passado":
            first_day_this_month = QDate(today.year(), today.month(), 1)
            last_day_last_month = first_day_this_month.addDays(-1)
            first_day_last_month = QDate(last_day_last_month.year(), last_day_last_month.month(), 1)
            self.start_date_input.setDate(first_day_last_month)
            self.end_date_input.setDate(last_day_last_month)
        elif period == "Últimos 3 Meses":
            self.start_date_input.setDate(today.addMonths(-3))
            self.end_date_input.setDate(today)
        elif period == "Este Ano":
            first_day = QDate(today.year(), 1, 1)
            self.start_date_input.setDate(first_day)
            self.end_date_input.setDate(today)
        
        self._load_data()
    
    def _load_data(self):
        """Carrega os dados de check-ins e receita e gera o gráfico."""
        from src.data.data_provider import get_provider
        
        # Obter datas do filtro
        start_date = self.start_date_input.date().toPyDate()
        end_date = self.end_date_input.date().toPyDate()
        
        # Converter para datetime
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Buscar dados
        provider = get_provider()
        session = provider.session
        
        try:
            # 1. Buscar check-ins por plano
            results = session.execute(text("""
                SELECT m.plano, COUNT(f.id) as total_checkins
                FROM frequencia f
                JOIN membros m ON f.member_id = m.id
                WHERE f.checkin_datetime BETWEEN :start_date AND :end_date
                GROUP BY m.plano
                ORDER BY total_checkins DESC
            """), {
                "start_date": start_datetime.strftime('%Y-%m-%d %H:%M:%S'), 
                "end_date": end_datetime.strftime('%Y-%m-%d %H:%M:%S')
            }).fetchall()
            
            self.plan_data = {}
            self.total_checkins = 0
            
            for row in results:
                plano = row[0] if row[0] else 'Sem Plano'
                count = row[1]
                self.plan_data[plano] = count
                self.total_checkins += count
            
            # 2. Buscar evolução da receita
            revenue_results = session.execute(text("""
                SELECT DATE(data_pagamento) as data, SUM(valor) as receita_dia
                FROM pagamentos
                WHERE data_pagamento BETWEEN :start_date AND :end_date
                GROUP BY DATE(data_pagamento)
                ORDER BY data
            """), {
                "start_date": start_datetime.strftime('%Y-%m-%d %H:%M:%S'), 
                "end_date": end_datetime.strftime('%Y-%m-%d %H:%M:%S')
            }).fetchall()
            
            self.revenue_data = []
            total_revenue = 0
            for row in revenue_results:
                date_str = row[0]
                revenue = row[1]
                total_revenue += revenue
                self.revenue_data.append({
                    'date': datetime.strptime(date_str, '%Y-%m-%d').date(),
                    'revenue': revenue
                })

        except Exception as e:
            print(f"Erro ao carregar dados do gráfico: {e}")
            self.plan_data = {}
            self.total_checkins = 0
            self.revenue_data = []
            self.info_label.setText(f"Erro ao carregar dados: {e}")

        
        # Atualizar label de informação
        period_text = self.period_combo.currentText()
        if self.current_graph_type == "pizza":
            self.info_label.setText(
                f"Total de check-ins: {self.total_checkins} ({period_text})"
            )
        else:
            self.info_label.setText(
                f"Receita Total: R$ {total_revenue:,.2f} ({period_text})"
            )
        
        # Gerar gráfico
        self._generate_chart()
    
    def _generate_chart(self):
        """Gera o gráfico baseado no tipo selecionado."""
        if self.current_graph_type == "pizza":
            self._generate_pie_chart()
        else:
            self._generate_revenue_chart()
    
    def _generate_pie_chart(self):
        """Gera o gráfico de pizza de check-ins por plano."""
        self.figure.clear()
        
        if not self.plan_data or self.total_checkins == 0:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Nenhum check-in encontrado no período', 
                   horizontalalignment='center',
                   verticalalignment='center',
                   fontsize=16, color='#888888')
            ax.axis('off')
            self.canvas.draw()
            return
        
        # Preparar dados
        plans = list(self.plan_data.keys())
        counts = list(self.plan_data.values())
        
        # Calcular percentuais
        percentages = [(count / self.total_checkins * 100) for count in counts]
        
        # Ordenar por quantidade
        sorted_data = sorted(zip(plans, counts, percentages), key=lambda x: x[1], reverse=True)
        plans, counts, percentages = zip(*sorted_data) if sorted_data else ([], [], [])
        
        # Cores
        colors = [
            '#007ACC', '#28a745', '#FFA500', '#D32F2F', '#9C27B0',
            '#00BCD4', '#FF9800', '#4CAF50', '#E91E63', '#795548',
        ]
        
        ax = self.figure.add_subplot(111)
        
        def make_autopct(values):
            def my_autopct(pct):
                total = sum(values)
                val = int(round(pct * total / 100.0))
                if pct >= 3:
                    return f'{pct:.1f}%\n({val})'
                else:
                    return f'{val}'
            return my_autopct
        
        pie_result = ax.pie(
            counts,
            labels=None,
            colors=colors[:len(plans)],
            autopct=make_autopct(counts),
            startangle=90,
            textprops={'fontsize': 11, 'weight': 'bold'},
            explode=[0.03] * len(plans),
            pctdistance=0.75
        )
        
        if len(pie_result) == 3:
            wedges, texts, autotexts = pie_result
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')
        
        period_text = self.period_combo.currentText()
        ax.set_title(
            f'Check-ins por Plano ({period_text})',
            fontsize=16,
            weight='bold',
            color='#333333',
            pad=20
        )
        
        ax.axis('equal')
        
        legend_labels = [
            f'{plan}: {count} ({pct:.1f}%)'
            for plan, count, pct in zip(plans, counts, percentages)
        ]
        ax.legend(
            legend_labels,
            loc='center left',
            bbox_to_anchor=(1.05, 0.5),
            fontsize=11,
            frameon=True,
            fancybox=True,
            shadow=True,
            title='Planos',
            title_fontsize=12
        )
        
        self.figure.tight_layout(rect=(0, 0, 0.85, 1))
        self.canvas.draw()
    
    def _generate_revenue_chart(self):
        """Gera o gráfico de evolução da receita."""
        self.figure.clear()
        
        if not self.revenue_data:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Nenhuma receita encontrada no período', 
                   horizontalalignment='center',
                   verticalalignment='center',
                   fontsize=16, color='#888888')
            ax.axis('off')
            self.canvas.draw()
            return
        
        # Preparar dados
        dates = [item['date'] for item in self.revenue_data]
        revenues = [item['revenue'] for item in self.revenue_data]
        
        # Calcular receita acumulada
        cumulative_revenue = []
        total = 0
        for rev in revenues:
            total += rev
            cumulative_revenue.append(total)
        
        ax = self.figure.add_subplot(111)
        
        # Gráfico de barras da receita diária
        bars = ax.bar(dates, revenues, color='#007ACC', alpha=0.7, label='Receita Diária')
        
        # Linha da receita acumulada
        ax2 = ax.twinx()
        line = ax2.plot(dates, cumulative_revenue, color='#28a745', 
                       linewidth=2.5, marker='o', markersize=5, 
                       label='Receita Acumulada')
        
        # Títulos e labels
        period_text = self.period_combo.currentText()
        ax.set_title(
            f'Evolução da Receita ({period_text})',
            fontsize=16,
            weight='bold',
            color='#333333',
            pad=20
        )
        
        ax.set_xlabel('Data', fontsize=12, weight='bold')
        ax.set_ylabel('Receita Diária (R$)', fontsize=12, weight='bold', color='#007ACC')
        ax2.set_ylabel('Receita Acumulada (R$)', fontsize=12, weight='bold', color='#28a745')
        
        # Formatação do eixo X
        if len(dates) > 30:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        elif len(dates) > 7:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        
        # Rotacionar labels do eixo X
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Cores dos eixos Y
        ax.tick_params(axis='y', labelcolor='#007ACC')
        ax2.tick_params(axis='y', labelcolor='#28a745')
        
        # Legenda combinada
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc='upper left', 
                 frameon=True, fancybox=True, shadow=True)
        
        # Adicionar valores nas barras (apenas se não houver muitas)
        if len(dates) <= 15:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'R${height:.0f}',
                       ha='center', va='bottom', fontsize=9, weight='bold')
        
        self.figure.tight_layout()
        self.canvas.draw()
