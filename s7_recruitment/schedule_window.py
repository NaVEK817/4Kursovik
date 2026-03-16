# -*- coding: utf-8 -*-
"""
Окно расписания собеседований с календарем и информацией о пользователях
"""
import json
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QCalendarWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QMessageBox, QGroupBox, QHeaderView,
                             QComboBox, QTimeEdit, QTextEdit, QLineEdit)
from PyQt5.QtCore import Qt, QDate, QTime
import styles

class ScheduleWindow(QWidget):
    """Окно расписания собеседований"""
    
    SCHEDULE_FILE = "interviews_schedule.json"
    
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.interviews = self.load_interviews()
        self.init_ui()
        self.update_interviews_list()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("S7 Recruitment - Расписание собеседований")
        self.setGeometry(200, 200, 1200, 700)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        # Основной layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Левая панель с календарем
        left_panel = QVBoxLayout()
        
        # Заголовок
        header_label = QLabel("📅 Календарь собеседований")
        header_label.setObjectName("headerLabel")
        left_panel.addWidget(header_label)
        
        # Календарь
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.clicked.connect(self.date_selected)
        self.calendar.setMinimumHeight(300)
        left_panel.addWidget(self.calendar)
        
        # Информация о выбранной дате
        date_group = QGroupBox("Выбранная дата")
        date_layout = QVBoxLayout()
        
        self.selected_date_label = QLabel()
        self.selected_date_label.setStyleSheet(f"font-size: 14px; color: {styles.S7_GREEN};")
        date_layout.addWidget(self.selected_date_label)
        
        date_group.setLayout(date_layout)
        left_panel.addWidget(date_group)
        
        # Форма для добавления собеседования
        add_group = QGroupBox("Добавить собеседование")
        add_layout = QVBoxLayout()
        
        # Кандидат
        candidate_layout = QHBoxLayout()
        candidate_layout.addWidget(QLabel("Кандидат:"))
        self.candidate_input = QLineEdit()
        self.candidate_input.setPlaceholderText("Введите ФИО кандидата")
        candidate_layout.addWidget(self.candidate_input)
        add_layout.addLayout(candidate_layout)
        
        # Время
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Время:"))
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm")
        time_layout.addWidget(self.time_input)
        add_layout.addLayout(time_layout)
        
        # Комментарий
        comment_layout = QVBoxLayout()
        comment_layout.addWidget(QLabel("Комментарий:"))
        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(80)
        comment_layout.addWidget(self.comment_input)
        add_layout.addLayout(comment_layout)
        
        # Кнопка добавления
        add_btn = QPushButton("➕ Добавить собеседование")
        add_btn.clicked.connect(self.add_interview)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_layout.addWidget(add_btn)
        
        add_group.setLayout(add_layout)
        left_panel.addWidget(add_group)
        
        left_panel.addStretch()
        
        # Правая панель со списком собеседований
        right_panel = QVBoxLayout()
        
        # Заголовок
        interviews_header = QLabel("Собеседования на выбранную дату")
        interviews_header.setObjectName("headerLabel")
        right_panel.addWidget(interviews_header)
        
        # Таблица собеседований
        self.interviews_table = QTableWidget()
        self.interviews_table.setColumnCount(5)
        self.interviews_table.setHorizontalHeaderLabels(["Время", "Кандидат", "Комментарий", "Создатель", "Действия"])
        
        header = self.interviews_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.interviews_table.setAlternatingRowColors(True)
        right_panel.addWidget(self.interviews_table)
        
        # Статистика
        stats_group = QGroupBox("Статистика")
        stats_layout = QVBoxLayout()
        
        self.stats_label = QLabel()
        stats_layout.addWidget(self.stats_label)
        
        stats_group.setLayout(stats_layout)
        right_panel.addWidget(stats_group)
        
        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.update_interviews_list)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        right_panel.addWidget(refresh_btn)
        
        # Добавление панелей в основной layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(400)
        main_layout.addWidget(left_widget)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        main_layout.addWidget(right_widget)
        
        self.setLayout(main_layout)
        
        # Установка текущей даты
        self.date_selected(self.calendar.selectedDate())
    
    def load_interviews(self):
        """Загрузка собеседований из файла"""
        if os.path.exists(self.SCHEDULE_FILE):
            try:
                with open(self.SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_interviews(self):
        """Сохранение собеседований в файл"""
        try:
            with open(self.SCHEDULE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.interviews, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить расписание: {str(e)}")
    
    def date_selected(self, date):
        """Обработка выбора даты в календаре"""
        date_str = date.toString("yyyy-MM-dd")
        self.selected_date_label.setText(f"Выбрана дата: {date.toString('dd.MM.yyyy')}")
        self.update_interviews_for_date(date_str)
    
    def update_interviews_for_date(self, date_str):
        """Обновление списка собеседований для выбранной даты"""
        self.interviews_table.setRowCount(0)
        
        interviews = self.interviews.get(date_str, [])
        interviews.sort(key=lambda x: x.get('time', ''))
        
        for row, interview in enumerate(interviews):
            self.interviews_table.insertRow(row)
            
            # Время
            self.interviews_table.setItem(row, 0, QTableWidgetItem(interview.get('time', '')))
            
            # Кандидат
            self.interviews_table.setItem(row, 1, QTableWidgetItem(interview.get('candidate', '')))
            
            # Комментарий
            comment_item = QTableWidgetItem(interview.get('comment', ''))
            comment_item.setToolTip(interview.get('comment', ''))
            self.interviews_table.setItem(row, 2, comment_item)
            
            # Создатель
            creator = interview.get('created_by', 'Неизвестно')
            creator_item = QTableWidgetItem(creator)
            creator_item.setForeground(Qt.darkGreen if creator == self.user_data.get('username') else Qt.black)
            self.interviews_table.setItem(row, 3, creator_item)
            
            # Кнопка удаления (только для своего создателя или админа)
            if creator == self.user_data.get('username') or self.user_data.get('role') == 'admin':
                delete_btn = QPushButton("✖ Удалить")
                delete_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {styles.S7_RED};
                        color: white;
                        padding: 4px 8px;
                        font-size: 11px;
                    }}
                    QPushButton:hover {{
                        background-color: {styles.S7_RED};
                        opacity: 0.8;
                    }}
                """)
                delete_btn.clicked.connect(lambda checked, d=date_str, i=interview: self.delete_interview(d, i))
                delete_btn.setCursor(Qt.PointingHandCursor)
                self.interviews_table.setCellWidget(row, 4, delete_btn)
    
    def update_interviews_list(self):
        """Обновление всего списка (вызывается после изменений)"""
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.update_interviews_for_date(date_str)
        
        # Обновление статистики
        total_interviews = sum(len(v) for v in self.interviews.values())
        today = QDate.currentDate().toString("yyyy-MM-dd")
        today_count = len(self.interviews.get(today, []))
        user_interviews = sum(1 for interviews in self.interviews.values() 
                              for i in interviews if i.get('created_by') == self.user_data.get('username'))
        
        self.stats_label.setText(
            f"Всего собеседований: {total_interviews}\n"
            f"На сегодня: {today_count}\n"
            f"Ваших собеседований: {user_interviews}\n"
            f"Всего дней с собеседованиями: {len(self.interviews)}"
        )
    
    def add_interview(self):
        """Добавление нового собеседования"""
        date = self.calendar.selectedDate()
        date_str = date.toString("yyyy-MM-dd")
        
        candidate = self.candidate_input.text().strip()
        if not candidate:
            QMessageBox.warning(self, "Предупреждение", "Введите имя кандидата")
            return
        
        time_str = self.time_input.time().toString("HH:mm")
        comment = self.comment_input.toPlainText().strip()
        
        # Проверка на занятость времени
        interviews = self.interviews.get(date_str, [])
        for interview in interviews:
            if interview.get('time') == time_str:
                QMessageBox.warning(self, "Предупреждение", 
                                   f"Время {time_str} уже занято другим собеседованием")
                return
        
        # Добавление собеседования с информацией о создателе
        new_interview = {
            'candidate': candidate,
            'time': time_str,
            'comment': comment,
            'created_by': self.user_data.get('username', 'Неизвестно'),
            'created_at': datetime.now().isoformat()
        }
        
        if date_str not in self.interviews:
            self.interviews[date_str] = []
        
        self.interviews[date_str].append(new_interview)
        self.save_interviews()
        
        # Очистка формы
        self.candidate_input.clear()
        self.comment_input.clear()
        
        # Обновление отображения
        self.update_interviews_for_date(date_str)
        self.update_interviews_list()
        
        QMessageBox.information(self, "Успех", "Собеседование успешно добавлено")
    
    def delete_interview(self, date_str, interview):
        """Удаление собеседования"""
        reply = QMessageBox.question(
            self, 
            "Подтверждение",
            f"Удалить собеседование с {interview.get('candidate')} "
            f"на {interview.get('time')}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if date_str in self.interviews:
                self.interviews[date_str] = [
                    i for i in self.interviews[date_str] 
                    if i.get('time') != interview.get('time')
                ]
                
                if not self.interviews[date_str]:
                    del self.interviews[date_str]
                
                self.save_interviews()
                self.update_interviews_for_date(date_str)
                self.update_interviews_list()