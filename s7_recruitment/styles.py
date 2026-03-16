# -*- coding: utf-8 -*-
"""
Стили интерфейса в цветах S7 Airlines
"""
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

# Цвета бренда S7
S7_GREEN = "#00A651"      # Основной зеленый
S7_LIGHT_GREEN = "#8DC63F"  # Светло-зеленый
S7_DARK_GREEN = "#00853E"   # Темно-зеленый
S7_BG = "#F5F5F5"          # Светло-серый фон
S7_WHITE = "#FFFFFF"
S7_BLACK = "#333333"
S7_GRAY = "#666666"
S7_LIGHT_GRAY = "#E0E0E0"
S7_RED = "#E30613"         # Акцентный красный

# Основной стиль приложения
MAIN_STYLE = f"""
QMainWindow {{
    background-color: {S7_BG};
}}

QWidget {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    color: {S7_BLACK};
}}

QPushButton {{
    background-color: {S7_GREEN};
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {S7_DARK_GREEN};
}}

QPushButton:pressed {{
    background-color: {S7_DARK_GREEN};
}}

QPushButton:disabled {{
    background-color: {S7_LIGHT_GRAY};
    color: {S7_GRAY};
}}

QLineEdit, QTextEdit, QComboBox {{
    border: 1px solid {S7_LIGHT_GRAY};
    border-radius: 4px;
    padding: 6px;
    background-color: {S7_WHITE};
}}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border: 2px solid {S7_GREEN};
}}

QTableWidget {{
    background-color: {S7_WHITE};
    alternate-background-color: {S7_BG};
    gridline-color: {S7_LIGHT_GRAY};
    selection-background-color: {S7_LIGHT_GREEN};
}}

QTableWidget::item:selected {{
    background-color: {S7_LIGHT_GREEN};
    color: {S7_BLACK};
}}

QHeaderView::section {{
    background-color: {S7_GREEN};
    color: white;
    padding: 8px;
    border: none;
    font-weight: bold;
}}

QTabWidget::pane {{
    border: 1px solid {S7_LIGHT_GRAY};
    border-radius: 4px;
}}

QTabBar::tab {{
    background-color: {S7_LIGHT_GRAY};
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}

QTabBar::tab:selected {{
    background-color: {S7_GREEN};
    color: white;
}}

QTabBar::tab:hover:!selected {{
    background-color: {S7_LIGHT_GREEN};
}}

QCalendarWidget QWidget {{
    alternate-background-color: {S7_BG};
}}

QCalendarWidget QAbstractItemView:enabled {{
    font-size: 12px;
    color: {S7_BLACK};
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {S7_GREEN};
}}

QLabel {{
    color: {S7_BLACK};
}}

QLabel#headerLabel {{
    font-size: 18px;
    font-weight: bold;
    color: {S7_DARK_GREEN};
}}
"""

# Стиль для окон авторизации
AUTH_STYLE = f"""
QWidget {{
    background-color: {S7_WHITE};
}}

QLabel {{
    color: {S7_BLACK};
    font-size: 14px;
}}

QLineEdit {{
    border: 2px solid {S7_LIGHT_GRAY};
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border: 2px solid {S7_GREEN};
}}

QPushButton {{
    background-color: {S7_GREEN};
    color: white;
    border: none;
    padding: 12px;
    border-radius: 6px;
    font-size: 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {S7_DARK_GREEN};
}}
"""

# Стиль для ячеек календаря (занятые слоты)
BUSY_SLOT_STYLE = f"""
    background-color: {S7_RED};
    color: white;
    border-radius: 3px;
"""