"""
Estilos CSS para a interface gráfica.
"""

STYLESHEET = """
    /* Tema Claro Global */
    QWidget {
        background-color: #F5F5F5;
        color: #333333;
    }
    
    QMainWindow {
        background-color: #F0F0F0;
    }
    
    /* Diálogos com fundo claro */
    QDialog {
        background-color: #F5F5F5;
        color: #333333;
    }
    
    QLabel#title {
        font-size: 28px;
        font-weight: bold;
        color: #333333;
        padding-bottom: 10px;
    }
    
    /* Labels normais */
    QLabel {
        color: #333333;
        background-color: transparent;
    }
    QTextEdit, QTextBrowser {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 8px;
        font-size: 14px;
        padding: 10px;
    }
    QPushButton {
        background-color: #007ACC;
        color: white;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px;
        border: none;
    }
    QPushButton:hover {
        background-color: #005FA3;
    }
    QPushButton:disabled {
        background-color: #DDDDDD;
        color: #AAAAAA;
    }

    QLineEdit {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 8px;
        font-size: 14px;
    }
    
    /* ComboBox */
    QComboBox {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 6px;
        font-size: 14px;
    }
    
    QComboBox:hover {
        border: 1px solid #007ACC;
    }
    
    QComboBox::drop-down {
        border: none;
        padding-right: 8px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #333333;
        selection-background-color: #007ACC;
        selection-color: white;
        border: 1px solid #CCCCCC;
    }
    
    /* DateEdit */
    QDateEdit {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 6px;
        font-size: 14px;
    }
    
    QDateEdit:hover {
        border: 1px solid #007ACC;
    }
    
    QDateEdit::drop-down {
        border: none;
        padding-right: 8px;
    }
    
    /* Calendar Widget */
    QCalendarWidget {
        background-color: #FFFFFF;
        color: #333333;
    }
    
    QCalendarWidget QToolButton {
        background-color: #F0F0F0;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 4px;
    }
    
    QCalendarWidget QToolButton:hover {
        background-color: #007ACC;
        color: white;
    }
    
    QCalendarWidget QMenu {
        background-color: #FFFFFF;
        color: #333333;
    }
    
    QCalendarWidget QSpinBox {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
    }
    
    QCalendarWidget QAbstractItemView:enabled {
        background-color: #FFFFFF;
        color: #333333;
        selection-background-color: #007ACC;
        selection-color: white;
    }
    
    QCalendarWidget QWidget#qt_calendar_navigationbar {
        background-color: #F0F0F0;
    }
    
    /* GroupBox */
    QGroupBox {
        background-color: #FFFFFF;
        color: #333333;
        border: 2px solid #CCCCCC;
        border-radius: 8px;
        margin-top: 12px;
        font-weight: bold;
        padding: 15px;
    }
    
    QGroupBox::title {
        color: #007ACC;
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        background-color: #FFFFFF;
    }
    
    /* TabWidget */
    QTabWidget::pane {
        background-color: #FFFFFF;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
    }
    
    QTabBar::tab {
        background-color: #E0E0E0;
        color: #333333;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    
    QTabBar::tab:selected {
        background-color: #FFFFFF;
        color: #007ACC;
        font-weight: bold;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #D0D0D0;
    }
    
    /* ListWidget */
    QListWidget {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
    }
    
    QListWidget::item:selected {
        background-color: #007ACC;
        color: white;
    }
    
    QListWidget::item:hover:!selected {
        background-color: #F0F0F0;
    }

    QMenuBar {
        background-color: #E0E0E0;
        color: #333333;
    }

    QMenuBar::item:selected {
        background-color: #007ACC;
        color: white;
    }

    QMenu {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
    }

    QMenu::item:selected {
        background-color: #007ACC;
        color: white;
    }

    QScrollBar:vertical {
        border: none;
        background: #F0F0F0;
        width: 12px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: #C0C0C0;
        min-height: 20px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical:hover {
        background: #A0A0A0;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        border: none;
        background: #F0F0F0;
        height: 12px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:horizontal {
        background: #C0C0C0;
        min-width: 20px;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #A0A0A0;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    
    /* MessageBox */
    QMessageBox {
        background-color: #F5F5F5;
        color: #333333;
    }
    
    QMessageBox QLabel {
        color: #333333;
    }
    
    QMessageBox QPushButton {
        min-width: 80px;
    }
    
    /* Tooltips */
    QToolTip {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        padding: 4px;
    }
    
    /* SpinBox */
    QSpinBox, QDoubleSpinBox {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 6px;
    }
    
    /* CheckBox e RadioButton */
    QCheckBox, QRadioButton {
        color: #333333;
        spacing: 8px;
    }
    
    QCheckBox::indicator, QRadioButton::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #CCCCCC;
        background-color: #FFFFFF;
        border-radius: 3px;
    }
    
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {
        background-color: #007ACC;
        border-color: #007ACC;
    }
    
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {
        border-color: #007ACC;
    }
    
    /* ProgressBar */
    QProgressBar {
        background-color: #F0F0F0;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        text-align: center;
        color: #333333;
    }
    
    QProgressBar::chunk {
        background-color: #007ACC;
        border-radius: 3px;
    }
"""
