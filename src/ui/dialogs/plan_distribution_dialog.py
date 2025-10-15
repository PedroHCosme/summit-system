"""Diálogo com gráfico de pizza da distribuição de check-ins por plano."""

from typing import List, Dict, Any
from datetime import datetime, timedelta

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


class PlanDistributionDialog(QDialog):
    """Diálogo que mostra gráfico de pizza da distribuição de check-ins por plano."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Distribuição de Check-ins por Plano")
        self.setModal(False)
        self.resize(1000, 700)  # Aumentado para melhor visualização
        
        self.plan_data = {}
        self.total_checkins = 0
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Distribuição de Check-ins por Plano")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #007ACC;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Controles - Linha 1: Período
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
        self.figure = Figure(figsize=(10, 7), facecolor='white')
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
            # Primeiro dia do mês passado
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
        
        # Carregar dados automaticamente após mudar período
        self._load_data()
    
    def _load_data(self):
        """Carrega os dados de check-ins e gera o gráfico."""
        from src.data.data_provider import get_provider
        
        # Obter datas do filtro
        start_date = self.start_date_input.date().toPyDate()
        end_date = self.end_date_input.date().toPyDate()
        
        # Converter para datetime
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Buscar check-ins do período
        db_manager = get_provider().db_manager
        
        if not db_manager or not db_manager.connection:
            self.plan_data = {}
            self.total_checkins = 0
            self.info_label.setText("Erro: Sem conexão com o banco de dados")
            self._generate_chart()
            return
        
        # Query para buscar check-ins com plano do membro
        cursor = db_manager.connection.cursor()
        cursor.execute("""
            SELECT m.plano, COUNT(f.id) as total_checkins
            FROM frequencia f
            JOIN membros m ON f.member_id = m.id
            WHERE f.checkin_datetime BETWEEN ? AND ?
            GROUP BY m.plano
            ORDER BY total_checkins DESC
        """, (start_datetime.strftime('%Y-%m-%d %H:%M:%S'), 
              end_datetime.strftime('%Y-%m-%d %H:%M:%S')))
        
        results = cursor.fetchall()
        
        # Processar resultados
        self.plan_data = {}
        self.total_checkins = 0
        
        for row in results:
            plano = row[0] if row[0] else 'Sem Plano'
            count = row[1]
            self.plan_data[plano] = count
            self.total_checkins += count
        
        # Atualizar label de informação
        period_text = self.period_combo.currentText()
        self.info_label.setText(
            f"Total de check-ins: {self.total_checkins} ({period_text})"
        )
        
        # Gerar gráfico
        self._generate_chart()
    
    def _generate_chart(self):
        """Gera o gráfico de pizza."""
        self.figure.clear()
        
        if not self.plan_data or self.total_checkins == 0:
            # Mostrar mensagem de sem dados
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Nenhum dado disponível', 
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
        
        # Ordenar por quantidade (maior para menor)
        sorted_data = sorted(zip(plans, counts, percentages), key=lambda x: x[1], reverse=True)
        plans, counts, percentages = zip(*sorted_data) if sorted_data else ([], [], [])
        
        # Cores personalizadas (paleta profissional)
        colors = [
            '#007ACC',  # Azul
            '#28a745',  # Verde
            '#FFA500',  # Laranja
            '#D32F2F',  # Vermelho
            '#9C27B0',  # Roxo
            '#00BCD4',  # Ciano
            '#FF9800',  # Laranja escuro
            '#4CAF50',  # Verde claro
            '#E91E63',  # Rosa
            '#795548',  # Marrom
        ]
        
        # Criar gráfico de pizza
        ax = self.figure.add_subplot(111)
        
        # Função para formatar labels - apenas percentual, números grandes
        def make_autopct(values):
            def my_autopct(pct):
                total = sum(values)
                val = int(round(pct * total / 100.0))
                # Mostrar percentual apenas se >= 3%
                if pct >= 3:
                    return f'{pct:.1f}%\n({val})'
                else:
                    return f'{val}'
            return my_autopct
        
        # Criar o gráfico sem labels nas fatias (vamos usar apenas a legenda)
        pie_result = ax.pie(
            counts,
            labels=None,  # Sem labels nas fatias
            colors=colors[:len(plans)],
            autopct=make_autopct(counts),
            startangle=90,
            textprops={'fontsize': 11, 'weight': 'bold'},
            explode=[0.03] * len(plans),  # Pequena separação
            pctdistance=0.75  # Distância dos percentuais do centro
        )
        
        # Extrair elementos do resultado
        if len(pie_result) == 3:
            wedges, texts, autotexts = pie_result
            # Melhorar aparência dos textos de percentual
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')
        else:
            wedges, texts = pie_result
        
        # Título
        period_text = self.period_combo.currentText()
        ax.set_title(
            f'Check-ins por Plano ({period_text})',
            fontsize=16,
            weight='bold',
            color='#333333',
            pad=20
        )
        
        # Garantir aspecto circular
        ax.axis('equal')
        
        # Adicionar legenda com estatísticas - mais legível
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
        
        # Ajustar layout - dar mais espaço para a legenda à direita
        self.figure.tight_layout(rect=(0, 0, 0.85, 1))
        
        # Atualizar canvas
        self.canvas.draw()
