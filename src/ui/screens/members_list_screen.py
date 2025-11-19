"""Tela de listagem de membros com paginação."""

from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class MembersListScreen(QWidget):
    """Tela de listagem paginada de membros."""
    
    # Sinais
    member_selected = pyqtSignal(dict)  # Emitido quando um membro é selecionado
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
        
        # Tabela de membros
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Nome", "Plano", "Status", "Vencimento", "WhatsApp", "Treina", "Ações"
        ])
        
        # Configurar header
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Nome
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Plano
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Status
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Vencimento
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # WhatsApp
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Treina
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Ações
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
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
        
        # Atualizar tabela
        self.table.setRowCount(0)
        self.table.setRowCount(len(members))
        
        for row, member in enumerate(members):
            # Nome
            name_item = QTableWidgetItem(member.get('nome', ''))
            self.table.setItem(row, 0, name_item)
            
            # Plano
            plan_item = QTableWidgetItem(member.get('plano', ''))
            self.table.setItem(row, 1, plan_item)
            
            # Status
            status = member.get('estado_plano', '')
            status_item = QTableWidgetItem(status)
            if status == 'ATIVO':
                status_item.setForeground(QColor('#28a745'))
            else:
                status_item.setForeground(QColor('#FF6B6B'))
            status_item.setData(Qt.ItemDataRole.FontRole, "bold")
            self.table.setItem(row, 2, status_item)
            
            # Vencimento
            vencimento = member.get('vencimento_plano', '')
            venc_item = QTableWidgetItem(vencimento if vencimento else '-')
            self.table.setItem(row, 3, venc_item)
            
            # WhatsApp
            whatsapp_item = QTableWidgetItem(member.get('whatsapp', ''))
            self.table.setItem(row, 4, whatsapp_item)
            
            # Treina
            treina = member.get('treina', 'Não')
            treina_item = QTableWidgetItem(treina)
            if treina == 'Sim':
                treina_item.setForeground(QColor('#28a745'))
            self.table.setItem(row, 5, treina_item)
            
            # Botão de Ver Detalhes
            view_button = QPushButton("Ver Detalhes")
            view_button.setMaximumWidth(100)
            view_button.clicked.connect(lambda checked, m=member: self.member_selected.emit(m))
            self.table.setCellWidget(row, 6, view_button)
