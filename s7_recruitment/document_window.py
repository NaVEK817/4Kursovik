# -*- coding: utf-8 -*-
"""
Окно оформления документов для кандидатов
"""
import json
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, QComboBox,
                             QMessageBox, QFileDialog, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
import styles

class DocumentWindow(QWidget):
    """Окно оформления документов"""
    
    def __init__(self, vacancies):
        super().__init__()
        self.vacancies = vacancies
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("S7 Recruitment - Оформление документа")
        self.setGeometry(200, 200, 900, 700)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        # Основной layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header_label = QLabel("📄 Оформление документа для кандидата")
        header_label.setObjectName("headerLabel")
        layout.addWidget(header_label)
        
        # Группа поиска
        search_group = QGroupBox("Поиск вакансии")
        search_layout = QVBoxLayout()
        
        # Поиск по названию
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Поиск вакансии:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите название вакансии или ключевые слова...")
        self.search_input.textChanged.connect(self.search_vacancies)
        search_row.addWidget(self.search_input)
        
        search_layout.addLayout(search_row)
        
        # Выбор вакансии из результатов
        search_layout.addWidget(QLabel("Выберите вакансию:"))
        self.vacancy_combo = QComboBox()
        self.vacancy_combo.setEditable(False)
        self.vacancy_combo.currentIndexChanged.connect(self.load_vacancy_details)
        search_layout.addWidget(self.vacancy_combo)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Информация о вакансии
        info_group = QGroupBox("Информация о вакансии")
        info_layout = QVBoxLayout()
        
        self.vacancy_info = QTextEdit()
        self.vacancy_info.setReadOnly(True)
        self.vacancy_info.setMinimumHeight(200)
        info_layout.addWidget(self.vacancy_info)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Данные кандидата
        candidate_group = QGroupBox("Данные кандидата")
        candidate_layout = QVBoxLayout()
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("ФИО кандидата:"))
        self.candidate_name = QLineEdit()
        self.candidate_name.setPlaceholderText("Введите ФИО кандидата")
        name_layout.addWidget(self.candidate_name)
        candidate_layout.addLayout(name_layout)
        
        email_layout = QHBoxLayout()
        email_layout.addWidget(QLabel("Email:"))
        self.candidate_email = QLineEdit()
        self.candidate_email.setPlaceholderText("Введите email")
        email_layout.addWidget(self.candidate_email)
        candidate_layout.addLayout(email_layout)
        
        phone_layout = QHBoxLayout()
        phone_layout.addWidget(QLabel("Телефон:"))
        self.candidate_phone = QLineEdit()
        self.candidate_phone.setPlaceholderText("Введите телефон")
        phone_layout.addWidget(self.candidate_phone)
        candidate_layout.addLayout(phone_layout)
        
        candidate_group.setLayout(candidate_layout)
        layout.addWidget(candidate_group)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("📄 Создать документ")
        self.create_btn.clicked.connect(self.create_document)
        self.create_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.create_btn)
        
        buttons_layout.addStretch()
        
        self.clear_btn = QPushButton("🔄 Очистить")
        self.clear_btn.clicked.connect(self.clear_form)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.clear_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Загрузка вакансий в комбобокс
        self.update_vacancy_list()
    
    def update_vacancy_list(self):
        """Обновление списка вакансий"""
        self.vacancy_combo.clear()
        self.vacancy_combo.addItem("Выберите вакансию...", None)
        
        for vacancy in self.vacancies:
            title = vacancy.get('title', 'Без названия')
            area = vacancy.get('area', '')
            display_text = f"{title} ({area})" if area else title
            self.vacancy_combo.addItem(display_text, vacancy)
    
    def search_vacancies(self):
        """Поиск вакансий по названию"""
        search_text = self.search_input.text().lower()
        
        self.vacancy_combo.clear()
        self.vacancy_combo.addItem("Выберите вакансию...", None)
        
        if not search_text:
            # Если поиск пустой, показываем все вакансии
            for vacancy in self.vacancies:
                title = vacancy.get('title', 'Без названия')
                area = vacancy.get('area', '')
                display_text = f"{title} ({area})" if area else title
                self.vacancy_combo.addItem(display_text, vacancy)
        else:
            # Фильтруем вакансии
            for vacancy in self.vacancies:
                title = vacancy.get('title', '').lower()
                if search_text in title:
                    area = vacancy.get('area', '')
                    display_text = f"{vacancy.get('title', 'Без названия')} ({area})" if area else vacancy.get('title', 'Без названия')
                    self.vacancy_combo.addItem(display_text, vacancy)
    
    def load_vacancy_details(self, index):
        """Загрузка деталей выбранной вакансии"""
        if index <= 0:
            self.vacancy_info.clear()
            return
        
        vacancy = self.vacancy_combo.currentData()
        if vacancy:
            info = f"""
            <h2 style='color: {styles.S7_GREEN};'>{vacancy.get('title', '')}</h2>
            
            <p><b>ID:</b> {vacancy.get('id', '')}</p>
            <p><b>Город:</b> {vacancy.get('area', '')}</p>
            <p><b>Зарплата:</b> {vacancy.get('salary', 'Не указана')}</p>
            <p><b>Опыт:</b> {vacancy.get('experience', '')}</p>
            <p><b>График:</b> {vacancy.get('schedule', '')}</p>
            <p><b>Занятость:</b> {vacancy.get('employment', '')}</p>
            
            <h3>Требования:</h3>
            <p>{vacancy.get('requirements', 'Не указаны')}</p>
            
            <h3>Обязанности:</h3>
            <p>{vacancy.get('responsibilities', 'Не указаны')}</p>
            
            <h3>Условия:</h3>
            <p>{vacancy.get('conditions', 'Не указаны')}</p>
            
            <h3>Навыки:</h3>
            <p>{vacancy.get('skills', 'Не указаны')}</p>
            """
            
            self.vacancy_info.setHtml(info)
    
    def create_document(self):
        """Создание документа Word с информацией о вакансии"""
        # Проверка заполнения полей
        if self.vacancy_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите вакансию")
            return
        
        if not self.candidate_name.text().strip():
            QMessageBox.warning(self, "Предупреждение", "Введите ФИО кандидата")
            return
        
        vacancy = self.vacancy_combo.currentData()
        
        # Выбор места сохранения файла
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить документ",
            f"Кандидат_{self.candidate_name.text().strip()}_{vacancy.get('title', '')[:30]}.docx",
            "Word Documents (*.docx)"
        )
        
        if not filename:
            return
        
        try:
            # Создание документа
            doc = Document()
            
            # Заголовок
            doc.add_heading('S7 Recruitment - Информация о вакансии', 0)
            
            # Дата создания
            doc.add_paragraph(f"Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            
            # Информация о кандидате
            doc.add_heading('Данные кандидата', level=1)
            doc.add_paragraph(f"ФИО: {self.candidate_name.text().strip()}")
            doc.add_paragraph(f"Email: {self.candidate_email.text().strip()}")
            doc.add_paragraph(f"Телефон: {self.candidate_phone.text().strip()}")
            
            # Информация о вакансии
            doc.add_heading('Информация о вакансии', level=1)
            
            doc.add_heading('Основная информация', level=2)
            doc.add_paragraph(f"Название: {vacancy.get('title', '')}")
            doc.add_paragraph(f"ID вакансии: {vacancy.get('id', '')}")
            doc.add_paragraph(f"Город: {vacancy.get('area', '')}")
            doc.add_paragraph(f"Зарплата: {vacancy.get('salary', 'Не указана')}")
            doc.add_paragraph(f"Опыт: {vacancy.get('experience', '')}")
            doc.add_paragraph(f"График: {vacancy.get('schedule', '')}")
            doc.add_paragraph(f"Занятость: {vacancy.get('employment', '')}")
            
            # Требования
            doc.add_heading('Требования', level=2)
            if vacancy.get('requirements'):
                doc.add_paragraph(vacancy.get('requirements'))
            else:
                doc.add_paragraph('Не указаны')
            
            # Обязанности
            doc.add_heading('Обязанности', level=2)
            if vacancy.get('responsibilities'):
                doc.add_paragraph(vacancy.get('responsibilities'))
            else:
                doc.add_paragraph('Не указаны')
            
            # Условия
            doc.add_heading('Условия работы', level=2)
            if vacancy.get('conditions'):
                doc.add_paragraph(vacancy.get('conditions'))
            else:
                doc.add_paragraph('Не указаны')
            
            # Навыки
            doc.add_heading('Ключевые навыки', level=2)
            if vacancy.get('skills'):
                doc.add_paragraph(vacancy.get('skills'))
            else:
                doc.add_paragraph('Не указаны')
            
            # Сохранение документа
            doc.save(filename)
            
            # Отображение информации в окне
            info_text = f"""
            ✅ Документ успешно создан!
            
            Вакансия: {vacancy.get('title', '')}
            Кандидат: {self.candidate_name.text().strip()}
            
            Файл сохранен: {filename}
            """
            
            self.vacancy_info.setText(info_text)
            
            QMessageBox.information(self, "Успех", f"Документ успешно создан и сохранен:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать документ: {str(e)}")
    
    def clear_form(self):
        """Очистка формы"""
        self.search_input.clear()
        self.vacancy_combo.setCurrentIndex(0)
        self.candidate_name.clear()
        self.candidate_email.clear()
        self.candidate_phone.clear()
        self.vacancy_info.clear()