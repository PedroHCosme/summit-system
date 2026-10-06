"""Diálogo para exibir planos a vencer nos próximos dias."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from src.utils.utils import format_whatsapp_link, parse_date_to_date
from src.ui.messages import show_error


class ExpiringPlansDialog(QDialog):
    """Diálogo para exibir membros com planos a vencer."""
    
    def __init__(self, database_manager, parent=None):
        super().__init__(parent)
        self.database_manager = database_manager
        self.setWindowTitle("⏰ Planos a Vencer")
        self.setMinimumSize(1000, 600)
        self.resize(1100, 650)
        
        self.days_ahead = 12  # Padrão: 12 dias
        
        self._setup_ui()
        self._load_expiring_plans()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel("⏰ Planos a Vencer")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Filtro de dias
        filter_group = QGroupBox("Filtrar por período")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_label = QLabel("Mostrar planos a vencer nos próximos:")
        filter_layout.addWidget(filter_label)
        
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 90)
        self.days_spin.setValue(self.days_ahead)
        self.days_spin.setSuffix(" dias")
        self.days_spin.setMinimumWidth(100)
        self.days_spin.setStyleSheet("""
            QSpinBox {
                font-size: 13px;
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
        """)
        self.days_spin.valueChanged.connect(self._on_days_changed)
        filter_layout.addWidget(self.days_spin)
        
        filter_layout.addStretch()
        
        self.refresh_button = QPushButton("🔄 Atualizar")
        self.refresh_button.setFixedHeight(35)
        self.refresh_button.clicked.connect(self._load_expiring_plans)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #005FA3;
            }
        """)
        filter_layout.addWidget(self.refresh_button)
        
        layout.addWidget(filter_group)
        
        # Contador de resultados
        self.count_label = QLabel()
        self.count_label.setStyleSheet("font-size: 13px; color: #666666; font-weight: bold;")
        layout.addWidget(self.count_label)
        
        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Nome", "Plano", "Vencimento", "Dias Restantes", "Estado", "WhatsApp"
        ])
        
        # Configurar header e colunas
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        vertical_header = self.table.verticalHeader()
        if vertical_header:
            vertical_header.setVisible(False)
        self.table.setRowHeight(0, 45)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                gridline-color: #E0E0E0;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                color: #333333;
                font-weight: bold;
                font-size: 13px;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #007ACC;
            }
            QTableWidget::item:alternate {
                background-color: #F9F9F9;
            }
            QTableWidget::item:selected {
                background-color: #CCE5FF;
                color: #000000;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Legenda de cores
        legend_layout = QHBoxLayout()
        legend_layout.addStretch()
        
        legend_label = QLabel("Legenda: ")
        legend_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        legend_layout.addWidget(legend_label)
        
        urgent_label = QLabel("🔴 Crítico (≤3 dias)")
        urgent_label.setStyleSheet("font-size: 12px; color: #D32F2F;")
        legend_layout.addWidget(urgent_label)
        
        warning_label = QLabel("🟡 Atenção (4-7 dias)")
        warning_label.setStyleSheet("font-size: 12px; color: #F57C00; margin-left: 15px;")
        legend_layout.addWidget(warning_label)
        
        normal_label = QLabel("🟢 Normal (8+ dias)")
        normal_label.setStyleSheet("font-size: 12px; color: #388E3C; margin-left: 15px;")
        legend_layout.addWidget(normal_label)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
        # Botões
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("Fechar")
        self.close_button.setFixedHeight(40)
        self.close_button.clicked.connect(self.accept)
        self.close_button.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                padding: 10px 20px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def _on_days_changed(self, value):
        """Atualiza o período de dias."""
        self.days_ahead = value
    
    def _load_expiring_plans(self):
        """Carrega os planos a vencer."""
        try:
            # Calcular data limite
            today = datetime.now().date()
            limit_date = today + timedelta(days=self.days_ahead)
            
            # Buscar membros do banco
            members = self.database_manager.get_all_members()
            
            # Filtrar membros com vencimento nos próximos N dias
            expiring_members = []
            for member in members:
                vencimento_str = member.get('vencimento_plano', '')
                if not vencimento_str:
                    continue

                vencimento = parse_date_to_date(vencimento_str)
                if not vencimento:
                    continue

                if today <= vencimento <= limit_date:
                    days_remaining = (vencimento - today).days
                    expiring_members.append({
                        'member': member,
                        'vencimento_date': vencimento,
                        'days_remaining': days_remaining
                    })
            
            # Ordenar por dias restantes (mais urgente primeiro)
            expiring_members.sort(key=lambda x: x['days_remaining'])
            
            # Atualizar contador
            self.count_label.setText(
                f"📋 {len(expiring_members)} plano(s) a vencer nos próximos {self.days_ahead} dias"
            )
            
            # Preencher tabela
            self.table.setRowCount(len(expiring_members))
            
            for row, item in enumerate(expiring_members):
                member = item['member']
                vencimento_date = item['vencimento_date']
                days_remaining = item['days_remaining']
                
                # Definir altura da linha
                self.table.setRowHeight(row, 45)
                
                # Nome
                name_item = QTableWidgetItem(member.get('nome', ''))
                font = QFont()
                font.setPointSize(12)
                name_item.setFont(font)
                self.table.setItem(row, 0, name_item)
                
                # Plano
                plano_item = QTableWidgetItem(member.get('plano', ''))
                plano_item.setFont(font)
                self.table.setItem(row, 1, plano_item)
                
                # Vencimento
                vencimento_item = QTableWidgetItem(vencimento_date.strftime('%d/%m/%Y'))
                vencimento_item.setFont(font)
                vencimento_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, vencimento_item)
                
                # Dias restantes (com cor)
                days_item = QTableWidgetItem(f"{days_remaining} dias")
                days_item.setFont(font)
                days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Aplicar cores baseadas na urgência
                if days_remaining <= 3:
                    days_item.setForeground(QColor("#D32F2F"))  # Vermelho
                    days_item.setBackground(QColor("#FFEBEE"))
                    font_bold = QFont(font)
                    font_bold.setBold(True)
                    days_item.setFont(font_bold)
                elif days_remaining <= 7:
                    days_item.setForeground(QColor("#F57C00"))  # Laranja
                    days_item.setBackground(QColor("#FFF3E0"))
                else:
                    days_item.setForeground(QColor("#388E3C"))  # Verde
                
                self.table.setItem(row, 3, days_item)
                
                # Estado (CORRIGIDO: usar estado calculado, não do banco)
                # Se o vencimento ainda não chegou, deve estar ATIVO
                from src.core.plan_status import ATIVO as _ATIVO, INATIVO as _INATIVO
                estado_correto = _ATIVO if days_remaining >= 0 else _INATIVO
                
                estado_item = QTableWidgetItem(estado_correto)
                estado_item.setFont(font)
                estado_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Cor baseada no estado
                if estado_correto == 'ATIVO':
                    estado_item.setForeground(QColor("#2E7D32"))
                else:
                    estado_item.setForeground(QColor("#C62828"))
                
                self.table.setItem(row, 4, estado_item)
                
                # WhatsApp (com link clicável)
                whatsapp_value = member.get('whatsapp', '')
                link, display_value = format_whatsapp_link(whatsapp_value)
                if link and display_value:
                    whatsapp_label = QLabel(f'<a href="{link}">{display_value}</a>')
                    whatsapp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    whatsapp_label.setOpenExternalLinks(True)
                    whatsapp_label.setStyleSheet("QLabel { font-size: 12px; color: #007ACC; }")
                    self.table.setCellWidget(row, 5, whatsapp_label)
                else:
                    whatsapp_text = display_value or 'Não informado'
                    whatsapp_item = QTableWidgetItem(whatsapp_text)
                    whatsapp_item.setFont(font)
                    whatsapp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, 5, whatsapp_item)
            
            # Mensagem se não houver resultados
            if len(expiring_members) == 0:
                QMessageBox.information(
                    self,
                    "Nenhum Plano a Vencer",
                    f"✅ Não há planos com vencimento nos próximos {self.days_ahead} dias!"
                )
        
        except Exception as e:
            show_error(
                self,
                "Não foi possível carregar os planos a vencer. Tente novamente.",
                detail=e,
                title="Erro ao carregar",
            )
