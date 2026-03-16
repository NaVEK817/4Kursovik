# -*- coding: utf-8 -*-
"""
Главное окно приложения с таблицей вакансий и контекстным меню
"""
import json
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QLabel, QMessageBox, QMenu,
                             QDialog, QTextEdit, QVBoxLayout as QVBoxDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QCursor
import styles

class VacancyDetailDialog(QDialog):
    """Диалог с полной информацией о вакансии"""
    
    def __init__(self, vacancy, parent=None):
        super().__init__(parent)
        self.vacancy = vacancy
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"Детали вакансии: {self.vacancy.get('title', '')}")
        self.setGeometry(300, 300, 700, 600)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        layout = QVBoxDialog()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel(self.vacancy.get('title', ''))
        title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {styles.S7_GREEN};")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Основная информация
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setStyleSheet(f"background-color: {styles.S7_WHITE};")
        
        # Формирование текста
        info = f"""
        <table width="100%" cellpadding="5">
            <tr><td width="150"><b>ID:</b></td><td>{self.vacancy.get('id', '')}</td></tr>
            <tr><td><b>Название:</b></td><td>{self.vacancy.get('title', '')}</td></tr>
            <tr><td><b>Зарплата:</b></td><td>{self.vacancy.get('salary', 'Не указана')}</td></tr>
            <tr><td><b>Город:</b></td><td>{self.vacancy.get('area', '')}</td></tr>
            <tr><td><b>Опыт:</b></td><td>{self.vacancy.get('experience', '')}</td></tr>
            <tr><td><b>График:</b></td><td>{self.vacancy.get('schedule', '')}</td></tr>
            <tr><td><b>Занятость:</b></td><td>{self.vacancy.get('employment', '')}</td></tr>
            <tr><td><b>Дата публикации:</b></td><td>{self.vacancy.get('published_at', '')}</td></tr>
        </table>
        
        <h3 style='color: {styles.S7_GREEN}; margin-top: 20px;'>Требования</h3>
        <p>{self.vacancy.get('requirements', 'Не указаны')}</p>
        
        <h3 style='color: {styles.S7_GREEN};'>Обязанности</h3>
        <p>{self.vacancy.get('responsibilities', 'Не указаны')}</p>
        
        <h3 style='color: {styles.S7_GREEN};'>Условия</h3>
        <p>{self.vacancy.get('conditions', 'Не указаны')}</p>
        
        <h3 style='color: {styles.S7_GREEN};'>Ключевые навыки</h3>
        <p>{self.vacancy.get('skills', 'Не указаны')}</p>
        
        <h3 style='color: {styles.S7_GREEN};'>Ссылка</h3>
        <p><a href="{self.vacancy.get('link', '#')}">{self.vacancy.get('link', '')}</a></p>
        """
        
        info_text.setHtml(info)
        layout.addWidget(info_text)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        close_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.vacancies = []
        self.init_ui()
        self.load_vacancies()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle(f"S7 Recruitment - Главная (Пользователь: {self.user_data.get('username', '')})")
        self.showMaximized()  # Окно на весь экран
        self.setStyleSheet(styles.MAIN_STYLE)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Верхняя панель с кнопками навигации
        nav_layout = QHBoxLayout()
        
        # Кнопки навигации
        self.schedule_btn = QPushButton("📅 Расписание собеседований")
        self.schedule_btn.clicked.connect(self.open_schedule_window)
        nav_layout.addWidget(self.schedule_btn)
        
        self.update_btn = QPushButton("🔄 Обновление данных")
        self.update_btn.clicked.connect(self.open_update_window)
        nav_layout.addWidget(self.update_btn)
        
        # Кнопка управления пользователями (только для админа)
        if self.user_data.get('role') == 'admin':
            self.users_btn = QPushButton("👥 Управление пользователями")
            self.users_btn.clicked.connect(self.open_users_window)
            nav_layout.addWidget(self.users_btn)
        
        nav_layout.addStretch()
        
        # Информация о пользователе
        user_label = QLabel(f"👤 {self.user_data.get('username', '')} ({self.user_data.get('role', '')})")
        user_label.setStyleSheet(f"color: {styles.S7_GREEN}; font-weight: bold;")
        nav_layout.addWidget(user_label)
        
        main_layout.addLayout(nav_layout)
        
        # Заголовок таблицы
        header_label = QLabel("Актуальные вакансии")
        header_label.setObjectName("headerLabel")
        main_layout.addWidget(header_label)
        
        # Таблица вакансий
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Включение контекстного меню
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Установка колонок
        columns = ["ID", "Название", "Зарплата", "Город", "Опыт", "График", 
                   "Занятость", "Дата публикации", "Навыки"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Растягивание колонок
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Название
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Зарплата
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Город
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Опыт
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # График
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Занятость
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Дата
        header.setSectionResizeMode(8, QHeaderView.Stretch)           # Навыки
        
        main_layout.addWidget(self.table)
        
        # Нижняя панель с информацией
        bottom_layout = QHBoxLayout()
        
        self.count_label = QLabel("Загрузка вакансий...")
        bottom_layout.addWidget(self.count_label)
        
        bottom_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Обновить таблицу")
        refresh_btn.clicked.connect(self.load_vacancies)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        bottom_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(bottom_layout)
    
    def show_context_menu(self, pos: QPoint):
        """Показать контекстное меню при правом клике"""
        row = self.table.currentRow()
        if row >= 0:
            menu = QMenu()
            
            view_action = menu.addAction("👁️ Просмотреть детали")
            view_action.triggered.connect(self.show_vacancy_details)
            
            menu.addSeparator()
            
            ai_action = menu.addAction("🤖 Анализ кандидатов для этой вакансии")
            ai_action.triggered.connect(self.analyze_candidates_for_vacancy)
            
            # Показываем меню в позиции курсора
            menu.exec_(QCursor.pos())
    
    def show_vacancy_details(self):
        """Показать детали выбранной вакансии"""
        row = self.table.currentRow()
        if row >= 0:
            vacancy = self.vacancies[row]
            dialog = VacancyDetailDialog(vacancy, self)
            dialog.exec_()
    
    def analyze_candidates_for_vacancy(self):
        """Открыть окно анализа кандидатов для выбранной вакансии"""
        row = self.table.currentRow()
        if row >= 0:
            from ai_agent_window import AIAgentWindow
            self.ai_window = AIAgentWindow(self.vacancies[row])
            self.ai_window.show()
    
    def load_vacancies(self):
        """Загрузка вакансий из JSON файла"""
        try:
            with open('vacancy_test_file.json', 'r', encoding='utf-8') as f:
                self.vacancies = json.load(f)
            
            self.update_table()
            self.count_label.setText(f"Всего вакансий: {len(self.vacancies)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить вакансии: {str(e)}")
            self.count_label.setText("Ошибка загрузки данных")
    
    def update_table(self):
        """Обновление таблицы данными"""
        self.table.setRowCount(len(self.vacancies))
        
        for row, vacancy in enumerate(self.vacancies):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(vacancy.get('id', ''))))
            
            # Название
            title_item = QTableWidgetItem(vacancy.get('title', ''))
            title_item.setToolTip(vacancy.get('title', ''))
            self.table.setItem(row, 1, title_item)
            
            # Зарплата
            self.table.setItem(row, 2, QTableWidgetItem(vacancy.get('salary', '')))
            
            # Город
            self.table.setItem(row, 3, QTableWidgetItem(vacancy.get('area', '')))
            
            # Опыт
            self.table.setItem(row, 4, QTableWidgetItem(vacancy.get('experience', '')))
            
            # График
            self.table.setItem(row, 5, QTableWidgetItem(vacancy.get('schedule', '')))
            
            # Занятость
            self.table.setItem(row, 6, QTableWidgetItem(vacancy.get('employment', '')))
            
            # Дата публикации
            date_str = vacancy.get('published_at', '')
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace('+0300', '+03:00'))
                    date_str = date.strftime('%d.%m.%Y')
                except:
                    pass
            self.table.setItem(row, 7, QTableWidgetItem(date_str))
            
            # Навыки
            skills = vacancy.get('skills', '')
            skills_item = QTableWidgetItem(skills)
            skills_item.setToolTip(skills)
            self.table.setItem(row, 8, skills_item)
    
    def open_schedule_window(self):
        """Открытие окна расписания собеседований"""
        from schedule_window import ScheduleWindow
        self.schedule_window = ScheduleWindow(self.user_data)
        self.schedule_window.show()
    
    def open_update_window(self):
        """Открытие окна обновления данных"""
        from update_window import UpdateWindow
        self.update_window = UpdateWindow()
        self.update_window.show()
        self.update_window.update_completed.connect(self.load_vacancies)
    
    def open_users_window(self):
        """Открытие окна управления пользователями"""
        from users_window import UsersWindow
        self.users_window = UsersWindow()
        self.users_window.show()