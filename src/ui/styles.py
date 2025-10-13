"""
Estilos CSS para a interface gráfica.
"""

STYLESHEET = """
    QMainWindow {
        background-color: #F0F0F0;
    }
    QLabel#title {
        font-size: 28px;
        font-weight: bold;
        color: #333333;
        padding-bottom: 10px;
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
"""
