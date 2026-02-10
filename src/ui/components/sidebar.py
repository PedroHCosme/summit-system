"""
Dynamic Sidebar Navigation Component

Barra lateral de navegação dinâmica que muda conforme o contexto atual.
Suporta diferentes menus para: Home, Membros, Check-in, Financeiro, Configurações.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from enum import Enum


class SidebarContext(Enum):
    """Contextos disponíveis para a sidebar."""
    HOME = "home"
    MEMBERS = "members"
    CHECKIN = "checkin"
    FINANCIAL = "financial"
    SETTINGS = "settings"


class Sidebar(QWidget):
    """Barra lateral de navegação dinâmica."""
    
    # Sinais de navegação principal (Dashboard)
    home_clicked = pyqtSignal()
    checkin_clicked = pyqtSignal()
    members_clicked = pyqtSignal()
    financial_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    
    # Sinais específicos do contexto Membros
    members_list_clicked = pyqtSignal()
    members_add_clicked = pyqtSignal()
    members_pending_clicked = pyqtSignal()
    members_birthday_clicked = pyqtSignal()
    members_search_clicked = pyqtSignal()
    
    # Sinais específicos do contexto Check-in
    checkin_register_clicked = pyqtSignal()
    
    # Sinais específicos do contexto Financeiro
    financial_overview_clicked = pyqtSignal()
    financial_plans_clicked = pyqtSignal()
    financial_expiring_clicked = pyqtSignal()
    
    # Sinais específicos do contexto Configurações
    settings_plans_clicked = pyqtSignal()
    settings_backup_clicked = pyqtSignal()
    settings_sync_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        # Largura inicial: 60px (apenas ícones). Expande para 200px no hover.
        self.setFixedWidth(65) 
        self.buttons = []
        self.current_context = SidebarContext.HOME
        self._setup_ui()
        self._build_home_menu()
        self._setup_animation()

    def _setup_animation(self):
        """Configura a animação de expansão/contração."""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self.max_animation = QPropertyAnimation(self, b"maximumWidth")
        self.max_animation.setDuration(300)
        self.max_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def enterEvent(self, event):
        """Expande a sidebar ao passar o mouse."""
        self.expand()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Contrai a sidebar ao sair com o mouse."""
        self.collapse()
        super().leaveEvent(event)

    def expand(self):
        """Expande para mostrar texto."""
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(280) # Aumentado para 240px
        self.animation.start()
        
        self.max_animation.setStartValue(self.width())
        self.max_animation.setEndValue(280) # Aumentado para 240px
        self.max_animation.start()
        
        # Ajusta logo se necessário (opcional, pode ser fixo pequeno)

    def collapse(self):
        """Contrai para mostrar apenas ícones."""
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(60)
        self.animation.start()
        
        self.max_animation.setStartValue(self.width())
        self.max_animation.setEndValue(60)
        self.max_animation.start()

    def _setup_ui(self):
        """Configura a estrutura base da sidebar."""
        import os
        from PyQt6.QtGui import QPixmap
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 20, 5, 20) # Margens reduzidas
        self.layout.setSpacing(5)
        
        # Logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        base_path = os.path.dirname(os.path.dirname(__file__))  # Vai para src/ui
        logo_path = os.path.join(base_path, "assets", "summit.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Logo pequena (40px) para caber no modo colapsado
            scaled_pixmap = pixmap.scaledToWidth(40, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Fallback para texto se a logo não existir
            logo_label.setText("S") # Apenas S
            logo_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            logo_label.setStyleSheet("color: #E67E22;")
        
        logo_label.setStyleSheet("margin-bottom: 20px;")
        self.layout.addWidget(logo_label)
        
        # Container para botões dinâmicos
        self.buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(5)
        self.layout.addWidget(self.buttons_container)
        
        # Espaçador
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Estilo do container - Dark Navy sidebar
        self.setStyleSheet("""
            QWidget#sidebar {
                background-color: #1a2540;
                border-right: 1px solid #2d3748;
            }
        """)
    
    def _clear_buttons(self):
        """Remove todos os widgets do layout de botões."""
        # Remove todos os widgets do layout
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.buttons.clear()

    def _create_nav_button(self, text: str, signal: pyqtSignal, is_back: bool = False) -> QPushButton:
        """Cria um botão de navegação estilizado."""
        btn = QPushButton(text)
        btn.setObjectName("sidebarButton")
        btn.setCheckable(True)
        btn.setMinimumHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if is_back:
            # Estilo especial para botão de voltar
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(230, 126, 34, 0.1);
                    color: #E67E22;
                    border: 1px solid #E67E22;
                    border-radius: 8px;
                    padding: 12px 15px;
                    text-align: left;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(230, 126, 34, 0.2);
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #a0aec0;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 10px; /* Padding ajustado para ícones */
                    text-align: left;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2d3748;
                    color: #ffffff;
                }
                QPushButton:checked {
                    background-color: rgba(230, 126, 34, 0.15);
                    color: #E67E22;
                    font-weight: bold;
                    border-left: 3px solid #E67E22;
                }
            """)
        
        # Conecta o sinal
        btn.clicked.connect(lambda: self._on_button_clicked(btn, signal))
        
        return btn
    
    def _add_section_header(self, text: str):
        """Adiciona um cabeçalho de seção."""
        header = QLabel(text)
        header.setStyleSheet("""
            color: #4a5568;
            font-size: 9px;  /* Reduzido de 11px */
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            padding: 15px 15px 5px 15px;
        """)
        self.buttons_layout.addWidget(header)
    
    def _add_separator(self):
        """Adiciona um separador visual."""
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #2d3748; margin: 10px 15px;")
        self.buttons_layout.addWidget(separator)
    
    def _on_button_clicked(self, clicked_btn: QPushButton, signal: pyqtSignal):
        """Gerencia o estado dos botões e emite o sinal."""
        # Desmarca todos os outros botões
        for btn in self.buttons:
            if btn != clicked_btn:
                btn.setChecked(False)
        
        # Marca o botão clicado
        clicked_btn.setChecked(True)
        
        # Emite o sinal correspondente
        signal.emit()
    
    # =========================================================================
    # MENUS CONTEXTUAIS
    # =========================================================================
    
    def _build_home_menu(self):
        """Constrói o menu principal (Dashboard)."""
        self._clear_buttons()
        self.current_context = SidebarContext.HOME
        
        nav_items = [
            ("🏠  Dashboard", self.home_clicked),
            ("✅  Check-in", self.checkin_clicked),
            ("👥  Membros", self.members_clicked),
            ("💰  Financeiro", self.financial_clicked),
        ]
        
        for text, signal in nav_items:
            btn = self._create_nav_button(text, signal)
            self.buttons_layout.addWidget(btn)
            self.buttons.append(btn)
        
        self._add_separator()
        
        settings_btn = self._create_nav_button("⚙️  Configurações", self.settings_clicked)
        self.buttons_layout.addWidget(settings_btn)
        self.buttons.append(settings_btn)
    
    def _build_members_menu(self):
        """Constrói o menu de Membros."""
        self._clear_buttons()
        self.current_context = SidebarContext.MEMBERS
        
        # Botão de voltar
        back_btn = self._create_nav_button("🏠 Dashboard", self.home_clicked, is_back=True)
        self.buttons_layout.addWidget(back_btn)
        self.buttons.append(back_btn)
        
        self._add_section_header("MEMBROS")
        
        nav_items = [
            ("📋  Lista de Membros", self.members_list_clicked),
            ("🔍  Buscar Membro", self.members_search_clicked),
            ("➕  Adicionar Membro", self.members_add_clicked),
            ("⏳  Aprovar Pendentes", self.members_pending_clicked),
            ("🎂  Aniversariantes", self.members_birthday_clicked),
        ]
        
        for text, signal in nav_items:
            btn = self._create_nav_button(text, signal)
            self.buttons_layout.addWidget(btn)
            self.buttons.append(btn)
    
    def _build_checkin_menu(self):
        """Constrói o menu de Check-in."""
        self._clear_buttons()
        self.current_context = SidebarContext.CHECKIN
        
        # Botão de voltar
        back_btn = self._create_nav_button("🏠 Dashboard", self.home_clicked, is_back=True)
        self.buttons_layout.addWidget(back_btn)
        self.buttons.append(back_btn)
        
        self._add_section_header("CHECK-IN")
        
        nav_items = [
            ("✅  Registrar Check-in", self.checkin_register_clicked),
        ]
        
        for text, signal in nav_items:
            btn = self._create_nav_button(text, signal)
            self.buttons_layout.addWidget(btn)
            self.buttons.append(btn)
    
    def _build_financial_menu(self):
        """Constrói o menu Financeiro."""
        self._clear_buttons()
        self.current_context = SidebarContext.FINANCIAL
        
        # Botão de voltar
        back_btn = self._create_nav_button("🏠 Dashboard", self.home_clicked, is_back=True)
        self.buttons_layout.addWidget(back_btn)
        self.buttons.append(back_btn)
        
        self._add_section_header("FINANCEIRO")
        
        nav_items = [
            ("📈  Visão Geral", self.financial_overview_clicked),
            ("💳  Gerenciar Planos", self.financial_plans_clicked),
            ("⏰  Planos a Vencer", self.financial_expiring_clicked),
        ]
        
        for text, signal in nav_items:
            btn = self._create_nav_button(text, signal)
            self.buttons_layout.addWidget(btn)
            self.buttons.append(btn)
    
    def _build_settings_menu(self):
        """Constrói o menu de Configurações."""
        self._clear_buttons()
        self.current_context = SidebarContext.SETTINGS
        
        # Botão de voltar
        back_btn = self._create_nav_button("🏠 Dashboard", self.home_clicked, is_back=True)
        self.buttons_layout.addWidget(back_btn)
        self.buttons.append(back_btn)
        
        self._add_section_header("CONFIGURAÇÕES")
        
        nav_items = [
            ("💳  Gerenciar Planos", self.settings_plans_clicked),
            ("💾  Backup do Banco", self.settings_backup_clicked),
            ("🔄  Sincronizar Sheets", self.settings_sync_clicked),
        ]
        
        for text, signal in nav_items:
            btn = self._create_nav_button(text, signal)
            self.buttons_layout.addWidget(btn)
            self.buttons.append(btn)
    
    # =========================================================================
    # API PÚBLICA
    # =========================================================================
    
    def set_context(self, context: SidebarContext):
        """Define o contexto atual e reconstrói o menu."""
        if context == SidebarContext.HOME:
            self._build_home_menu()
        elif context == SidebarContext.MEMBERS:
            self._build_members_menu()
        elif context == SidebarContext.CHECKIN:
            self._build_checkin_menu()
        elif context == SidebarContext.FINANCIAL:
            self._build_financial_menu()
        elif context == SidebarContext.SETTINGS:
            self._build_settings_menu()
    
    def go_home(self):
        """Volta para o menu principal."""
        self.set_context(SidebarContext.HOME)
    
    def set_active(self, index: int):
        """Define o botão ativo pelo índice."""
        if 0 <= index < len(self.buttons):
            for i, btn in enumerate(self.buttons):
                btn.setChecked(i == index)
    
    def set_enabled(self, enabled: bool):
        """Habilita ou desabilita todos os botões."""
        for btn in self.buttons:
            btn.setEnabled(enabled)
