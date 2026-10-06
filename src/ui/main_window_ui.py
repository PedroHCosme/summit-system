"""Construção da UI da MainWindow (extraído de MainWindow._setup_ui)."""

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer, QTime

from src.ui.styles import STYLESHEET
from src.ui.components import Sidebar
from src.ui.screens import (
    HomeScreen,
    DashboardScreen,
    AniversariantesScreen,
    MemberSearchScreen,
    CheckinScreen,
    FinancialScreen,
    MembersListScreen,
    PendingMembersScreen,
    PlansScreen,
    NotesScreen
)


def build_ui(window):
    """Constrói a UI da MainWindow (barra de título, sidebar flutuante, stack de telas).

    Mutação in-place: define os mesmos atributos em `window` que _setup_ui definia
    (title_bar, content_container, sidebar, stacked_widget, *_screen, is_fullscreen).
    """
    window.setWindowTitle("Summit Escalada")
    # Iniciar em modo Full Screen (solicitação do usuário para corrigir resolução em produção)
    window.showFullScreen()
    window.is_fullscreen = True
    window.setStyleSheet(STYLESHEET)

    # Esconde a barra de menu padrão do QMainWindow
    window.menuBar().hide()

    # Define o ícone da janela
    base_path = os.path.dirname(__file__)
    icon_path = os.path.join(base_path, "assets", "summit.png")
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    # Container principal (Root) com layout VERTICAL para incluir a barra de título
    root_container = QWidget()
    root_layout = QVBoxLayout(root_container)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    # --- Barra de Título Customizada ---
    window.title_bar = QWidget()
    window.title_bar.setFixedHeight(40)
    window.title_bar.setStyleSheet("""
        QWidget {
            background-color: #1a1a1a;
            border-bottom: 1px solid #333;
        }
        QLabel {
            color: #fff;
            font-weight: bold;
            padding-left: 15px;
        }
        QPushButton {
            background-color: transparent;
            border: none;
            color: #fff;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #333;
        }
        QPushButton#close_btn:hover {
            background-color: #e81123;
        }
    """)

    title_layout = QHBoxLayout(window.title_bar)
    title_layout.setContentsMargins(0, 0, 0, 0)
    title_layout.setSpacing(0)

    # Título / Logo
    title_label = QLabel("Summit Escalada")
    title_layout.addWidget(title_label)

    title_layout.addStretch()

    # Relógio digital 24h, atualizado a cada segundo
    window.clock_label = QLabel()
    window.clock_label.setStyleSheet("color:#fff;font-weight:bold;font-size:16px;letter-spacing:2px;")

    def _tick():
        window.clock_label.setText(QTime.currentTime().toString("HH:mm:ss"))

    _tick()
    window.clock_timer = QTimer(window)
    window.clock_timer.timeout.connect(_tick)
    window.clock_timer.start(1000)
    title_layout.addWidget(window.clock_label)

    title_layout.addStretch()

    # Botões de controle
    # Minimizar
    btn_min = QPushButton("—")
    btn_min.setFixedSize(45, 40)
    btn_min.clicked.connect(window.showMinimized)
    title_layout.addWidget(btn_min)

    # Maximizar / Restaurar (Toggle)
    btn_max = QPushButton("❐")
    btn_max.setFixedSize(45, 40)
    btn_max.clicked.connect(window._toggle_maximize_restore)
    title_layout.addWidget(btn_max)

    # Fechar
    btn_close = QPushButton("✕")
    btn_close.setObjectName("close_btn")
    btn_close.setFixedSize(45, 40)
    btn_close.clicked.connect(window.close)
    title_layout.addWidget(btn_close)

    # Adiciona barra ao layout principal
    root_layout.addWidget(window.title_bar)

    # --- Área de Conteúdo (Sidebar + Telas) ---
    window.content_container = QWidget()  # Tornar atributo para acesso no resizeEvent
    content_layout = QHBoxLayout(window.content_container)
    content_layout.setContentsMargins(60, 0, 0, 0)  # Margem esquerda de 60px para a sidebar colapsada
    content_layout.setSpacing(0)

    # Sidebar (Flutuante - não adicionada ao layout)
    # Ela será posicionada manualmente no resizeEvent
    window.sidebar = Sidebar()
    window.sidebar.setParent(window.content_container)
    window.sidebar.set_enabled(False)
    window._connect_sidebar_signals()

    window.stacked_widget = QStackedWidget()
    content_layout.addWidget(window.stacked_widget)

    # Adiciona contéudo ao root
    root_layout.addWidget(window.content_container)

    # Define widget central
    window.setCentralWidget(root_container)

    # Cria as telas
    window.home_screen = HomeScreen()
    window.dashboard_screen = DashboardScreen()
    window.aniversariantes_screen = AniversariantesScreen()
    window.member_search_screen = MemberSearchScreen()
    window.checkin_screen = CheckinScreen()
    window.financial_screen = FinancialScreen()
    window.members_list_screen = MembersListScreen()
    window.pending_members_screen = PendingMembersScreen()
    window.plans_screen = PlansScreen()

    # Adiciona ao stack
    window.stacked_widget.addWidget(window.home_screen)  # 0
    window.stacked_widget.addWidget(window.dashboard_screen)  # 1
    window.stacked_widget.addWidget(window.aniversariantes_screen)  # 2
    window.stacked_widget.addWidget(window.member_search_screen)  # 3
    window.stacked_widget.addWidget(window.checkin_screen)  # 4
    window.stacked_widget.addWidget(window.financial_screen)  # 5
    window.stacked_widget.addWidget(window.members_list_screen)  # 6
    window.stacked_widget.addWidget(window.pending_members_screen)  # 7
    window.stacked_widget.addWidget(window.plans_screen)  # 8

    window.notes_screen = NotesScreen()
    window.stacked_widget.addWidget(window.notes_screen)  # 9

    # Conecta botões específicos
    window.dashboard_screen.refresh_button.clicked.connect(window._update_dashboard)

    # Conecta sinais das telas
    window._connect_screen_signals()

    # Mostra a tela de conexão
    window.stacked_widget.setCurrentIndex(0)
