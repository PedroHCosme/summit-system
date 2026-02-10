"""
Estilos QSS para a interface gráfica - Tema Light Summit

Paleta de Cores:
- BACKGROUND: #f8f9fa (Off-White)
- SURFACE: #ffffff (Branco)
- ACCENT: #E67E22 (Laranja Summit)
- TEXT_PRIMARY: #1a2540 (Azul Marinho Escuro - Deep Navy)
- TEXT_SECONDARY: #4a5568 (Azul Acinzentado)
"""

# Cores do tema
COLORS = {
    'background': '#f8f9fa',
    'surface': '#ffffff',
    'surface_hover': '#f0f4f8',
    'accent': '#E67E22',
    'accent_hover': '#D35400',
    'accent_light': 'rgba(230, 126, 34, 0.15)',
    'text_primary': '#1a2540',
    'text_secondary': '#4a5568',
    'text_muted': '#718096',
    'border': '#e2e8f0',
    'border_focus': '#E67E22',
    'success': '#27ae60',
    'success_bg': 'rgba(39, 174, 96, 0.15)',
    'warning': '#f39c12',
    'warning_bg': 'rgba(243, 156, 18, 0.15)',
    'danger': '#e74c3c',
    'danger_bg': 'rgba(231, 76, 60, 0.15)',
    'sidebar_bg': '#1a2540',
    'sidebar_text': '#a0aec0',
    'sidebar_active': '#E67E22',
}

STYLESHEET = """
    /* =====================================================
       TEMA LIGHT SUMMIT - MISSION CONTROL
       ===================================================== */
    
    /* Base */
    QWidget {
        background-color: #f8f9fa;
        color: #1a2540;
        font-family: 'Segoe UI', sans-serif;
    }
    
    QMainWindow {
        background-color: #f8f9fa;
    }
    
    /* Diálogos */
    QDialog {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    
    /* Labels */
    QLabel {
        color: #1a2540;
        background-color: transparent;
    }
    
    QLabel#title {
        font-size: 20px;
        font-weight: bold;
        color: #1a2540;
        padding-bottom: 10px;
    }
    
    QLabel#sectionTitle {
        font-size: 11px;
        font-weight: bold;
        color: #E67E22;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Text Areas */
    QTextEdit, QTextBrowser {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        font-size: 12px;
        padding: 10px;
        selection-background-color: #E67E22;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #ffffff;
        color: #1a2540;
        font-size: 12px;
        font-weight: bold;
        border-radius: 6px;
        padding: 10px 16px;
        border: 1px solid #e2e8f0;
    }
    
    QPushButton:hover {
        background-color: #f0f4f8;
        border-color: #E67E22;
    }
    
    QPushButton:pressed {
        background-color: #e2e8f0;
    }
    
    QPushButton:disabled {
        background-color: #f8f9fa;
        color: #a0aec0;
        border-color: #e2e8f0;
    }
    
    /* Primary Button - Laranja */
    QPushButton#primary, QPushButton[primary="true"] {
        background-color: #E67E22;
        color: white;
        border: none;
    }
    
    QPushButton#primary:hover, QPushButton[primary="true"]:hover {
        background-color: #D35400;
    }
    
    /* Success Button - Verde */
    QPushButton#success, QPushButton[success="true"] {
        background-color: #27ae60;
        color: white;
        border: none;
    }
    
    QPushButton#success:hover, QPushButton[success="true"]:hover {
        background-color: #219a52;
    }
    
    /* Danger Button - Vermelho */
    QPushButton#danger, QPushButton[danger="true"] {
        background-color: #e74c3c;
        color: white;
        border: none;
    }
    
    QPushButton#danger:hover, QPushButton[danger="true"]:hover {
        background-color: #c0392b;
    }
    
    /* Line Edit */
    QLineEdit {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px;
        font-size: 12px;
        selection-background-color: #E67E22;
    }
    
    QLineEdit:focus {
        border-color: #E67E22;
    }
    
    QLineEdit:disabled {
        background-color: #f8f9fa;
        color: #a0aec0;
    }
    
    /* ComboBox */
    QComboBox {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 11px;
    }
    
    QComboBox:hover {
        border-color: #E67E22;
    }
    
    QComboBox::drop-down {
        border: none;
        padding-right: 10px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #1a2540;
        selection-background-color: #E67E22;
        selection-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
    }
    
    /* DateEdit */
    QDateEdit {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 11px;
    }
    
    QDateEdit:hover {
        border-color: #E67E22;
    }
    
    QDateEdit::drop-down {
        border: none;
        padding-right: 10px;
    }
    
    /* Calendar Widget */
    QCalendarWidget {
        background-color: #ffffff;
        color: #1a2540;
    }
    
    QCalendarWidget QToolButton {
        background-color: #f8f9fa;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 4px;
    }
    
    QCalendarWidget QToolButton:hover {
        background-color: #E67E22;
        color: white;
    }
    
    QCalendarWidget QMenu {
        background-color: #ffffff;
        color: #1a2540;
    }
    
    QCalendarWidget QSpinBox {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
    }
    
    QCalendarWidget QAbstractItemView:enabled {
        background-color: #ffffff;
        color: #1a2540;
        selection-background-color: #E67E22;
        selection-color: white;
    }
    
    QCalendarWidget QWidget#qt_calendar_navigationbar {
        background-color: #f8f9fa;
    }
    
    /* GroupBox */
    QGroupBox {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-top: 16px;
        font-weight: bold;
        padding: 20px 15px 15px 15px;
    }
    
    QGroupBox::title {
        color: #E67E22;
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 10px;
        background-color: #ffffff;
    }
    
    /* TabWidget */
    QTabWidget::pane {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-top: -1px;
    }
    
    QTabBar::tab {
        background-color: #f8f9fa;
        color: #4a5568;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        border: 1px solid #e2e8f0;
        border-bottom: none;
    }
    
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #E67E22;
        font-weight: bold;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #f0f4f8;
        color: #1a2540;
    }
    
    /* ListWidget */
    QListWidget {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 5px;
    }
    
    QListWidget::item {
        padding: 8px;
        border-radius: 4px;
        margin: 2px 0;
    }
    
    QListWidget::item:selected {
        background-color: #E67E22;
        color: white;
    }
    
    QListWidget::item:hover:!selected {
        background-color: #f0f4f8;
    }
    
    /* TableWidget */
    QTableWidget {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        gridline-color: #e2e8f0;
    }
    
    QTableWidget::item {
        padding: 8px;
    }
    
    QTableWidget::item:selected {
        background-color: #E67E22;
        color: white;
    }
    
    QHeaderView::section {
        background-color: #f8f9fa;
        color: #1a2540;
        padding: 10px;
        border: none;
        border-bottom: 2px solid #E67E22;
        font-weight: bold;
        font-size: 12px;
    }
    
    /* ScrollBar Vertical */
    QScrollBar:vertical {
        border: none;
        background: #f8f9fa;
        width: 10px;
        margin: 0;
        border-radius: 5px;
    }
    
    QScrollBar::handle:vertical {
        background: #cbd5e0;
        min-height: 30px;
        border-radius: 5px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: #E67E22;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    
    /* ScrollBar Horizontal */
    QScrollBar:horizontal {
        border: none;
        background: #f8f9fa;
        height: 10px;
        margin: 0;
        border-radius: 5px;
    }
    
    QScrollBar::handle:horizontal {
        background: #cbd5e0;
        min-width: 30px;
        border-radius: 5px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background: #E67E22;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0;
    }
    
    /* MessageBox */
    QMessageBox {
        background-color: #ffffff;
        color: #1a2540;
    }
    
    QMessageBox QLabel {
        color: #1a2540;
    }
    
    QMessageBox QPushButton {
        min-width: 80px;
    }
    
    /* Tooltips */
    QToolTip {
        background-color: #1a2540;
        color: #ffffff;
        border: none;
        padding: 6px;
        border-radius: 4px;
    }
    
    /* SpinBox */
    QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px;
    }
    
    QSpinBox:focus, QDoubleSpinBox:focus {
        border-color: #E67E22;
    }
    
    /* CheckBox e RadioButton */
    QCheckBox, QRadioButton {
        color: #1a2540;
        spacing: 10px;
    }
    
    QCheckBox::indicator, QRadioButton::indicator {
        width: 20px;
        height: 20px;
        border: 2px solid #e2e8f0;
        background-color: #ffffff;
        border-radius: 4px;
    }
    
    QRadioButton::indicator {
        border-radius: 10px;
    }
    
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {
        background-color: #E67E22;
        border-color: #E67E22;
    }
    
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {
        border-color: #E67E22;
    }
    
    /* ProgressBar */
    QProgressBar {
        background-color: #f8f9fa;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        text-align: center;
        color: #1a2540;
        height: 20px;
    }
    
    QProgressBar::chunk {
        background-color: #E67E22;
        border-radius: 5px;
    }
    
    /* =====================================================
       SIDEBAR STYLES - DARK NAVY
       ===================================================== */
    
    QWidget#sidebar {
        background-color: #1a2540;
        border-right: 1px solid #2d3748;
    }
    
    QPushButton#sidebarButton {
        background-color: transparent;
        color: #a0aec0;
        border: none;
        border-radius: 8px;
        padding: 15px;
        text-align: left;
        font-size: 14px;
        font-weight: normal;
    }
    
    QPushButton#sidebarButton:hover {
        background-color: #2d3748;
        color: #ffffff;
    }
    
    QPushButton#sidebarButton:checked, QPushButton#sidebarButton[active="true"] {
        background-color: rgba(230, 126, 34, 0.2);
        color: #E67E22;
        font-weight: bold;
        border-left: 3px solid #E67E22;
    }
    
    /* =====================================================
       DASHBOARD CARD STYLES
       ===================================================== */
    
    QFrame#statCard {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
    }
    
    QFrame#statCard:hover {
        border-color: #E67E22;
    }
    
    QLabel#statValue {
        font-size: 20px;
        font-weight: bold;
        color: #E67E22;
    }
    
    QLabel#statTitle {
        font-size: 12px;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* =====================================================
       MENU BAR (Legacy - keeping for backwards compat)
       ===================================================== */
    
    QMenuBar {
        background-color: #1a2540;
        color: #a0aec0;
        border-bottom: 1px solid #2d3748;
    }
    
    QMenuBar::item {
        padding: 8px 12px;
    }
    
    QMenuBar::item:selected {
        background-color: #E67E22;
        color: white;
    }
    
    QMenu {
        background-color: #ffffff;
        color: #1a2540;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 5px;
    }
    
    QMenu::item {
        padding: 8px 30px 8px 20px;
        border-radius: 4px;
    }
    
    QMenu::item:selected {
        background-color: #E67E22;
        color: white;
    }
    
    QMenu::separator {
        height: 1px;
        background-color: #e2e8f0;
        margin: 5px 10px;
    }
"""

# Estilos específicos para componentes
SIDEBAR_BUTTON_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #a0aec0;
        border: none;
        border-radius: 8px;
        padding: 12px 10px;
        text-align: left;
        font-size: 11px;
    }
    QPushButton:hover {
        background-color: #2d3748;
        color: #ffffff;
    }
    QPushButton:checked {
        background-color: rgba(230, 126, 34, 0.2);
        color: #E67E22;
        font-weight: bold;
        border-left: 3px solid #E67E22;
    }
"""

STAT_CARD_STYLE = """
    QFrame {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }
    QFrame:hover {
        border-color: #E67E22;
    }
"""
