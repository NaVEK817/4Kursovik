# -*- coding: utf-8 -*-
"""
Окно AI-агента для анализа кандидатов с реальными данными
"""
import json
import re
import random
from datetime import datetime
from ai_analyzer import OllamaCandidateAnalyzer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QComboBox, QSpinBox, QProgressBar, QDialog,
                             QFormLayout, QDialogButtonBox, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import styles

class CandidateDetailDialog(QDialog):
    """Диалог с детальной информацией о кандидате"""
    
    def __init__(self, candidate_data, analysis_details, parent=None):
        super().__init__(parent)
        self.candidate = candidate_data['candidate']
        self.score = candidate_data['score']
        self.details = analysis_details
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"Детальная информация о кандидате")
        self.setGeometry(300, 300, 600, 500)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Заголовок с рейтингом
        title_layout = QHBoxLayout()
        
        name_label = QLabel(f"👤 {self.candidate.get('name', 'Неизвестно')}")
        name_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {styles.S7_GREEN};")
        title_layout.addWidget(name_label)
        
        title_layout.addStretch()
        
        score_label = QLabel(f"Рейтинг: {self.score}%")
        score_label.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: bold; 
            color: white;
            background-color: {styles.S7_GREEN if self.score >= 70 else styles.S7_RED if self.score < 50 else styles.S7_LIGHT_GREEN};
            padding: 5px 15px;
            border-radius: 15px;
        """)
        title_layout.addWidget(score_label)
        
        layout.addLayout(title_layout)
        
        # Основная информация
        info_group = QGroupBox("Контактная информация")
        info_layout = QFormLayout()
        
        # Телефон
        phone = self.candidate.get('phone', 'Не указан')
        info_layout.addRow("📞 Телефон:", QLabel(phone))
        
        # Email
        email = self.candidate.get('email', 'Не указан')
        info_layout.addRow("✉️ Email:", QLabel(email))
        
        # Город
        city = self.candidate.get('city', 'Не указан')
        info_layout.addRow("🏙️ Город:", QLabel(city))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Информация о вакансии
        vacancy_group = QGroupBox("Рассматриваемая вакансия")
        vacancy_layout = QVBoxLayout()
        
        vacancy_text = QLabel(self.candidate.get('vacancy_title', 'Не указана'))
        vacancy_text.setWordWrap(True)
        vacancy_text.setStyleSheet(f"font-weight: bold; color: {styles.S7_DARK_GREEN};")
        vacancy_layout.addWidget(vacancy_text)
        
        # Опыт
        experience = self.candidate.get('experience', 'Не указан')
        vacancy_layout.addWidget(QLabel(f"Опыт: {experience}"))
        
        vacancy_group.setLayout(vacancy_layout)
        layout.addWidget(vacancy_group)
        
        # Детали анализа
        analysis_group = QGroupBox("Детали анализа")
        analysis_layout = QVBoxLayout()
        
        analysis_text = QTextEdit()
        analysis_text.setReadOnly(True)
        analysis_text.setMaximumHeight(150)
        analysis_text.setText(self.details)
        analysis_layout.addWidget(analysis_text)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        close_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)

class CandidateAnalyzer(QThread):
    """Поток для анализа кандидатов с использованием AI (Ollama)"""

    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(list)
    finished_signal = pyqtSignal()

    def __init__(self, vacancy, candidates_data):
        super().__init__()
        self.vacancy = vacancy
        self.candidates_data = candidates_data
        # Инициализируем AI-анализатор
        self.ai_analyzer = OllamaCandidateAnalyzer() # Можно передать имя модели, если нужно

    def run(self):
        """Запуск AI-анализа в отдельном потоке"""
        results = []
        total = len(self.candidates_data)

        for i, candidate in enumerate(self.candidates_data):
            # Вызываем AI-анализ для каждого кандидата
            ai_result = self.ai_analyzer.analyze(self.vacancy, candidate)

            # Формируем результат в старом формате для совместимости
            result_item = {
                'candidate': candidate,
                'score': ai_result.get('score', 0),
                'details': self._format_details_for_display(ai_result, candidate)
            }
            results.append(result_item)

            # Обновляем прогресс
            self.progress_signal.emit(int((i + 1) / total * 100))

        # Сортировка по убыванию рейтинга (AI уже дает score)
        results.sort(key=lambda x: x['score'], reverse=True)
        self.result_signal.emit(results)
        self.finished_signal.emit()

    def _format_details_for_display(self, ai_result: dict, candidate: dict) -> str:
        """
        Преобразует структурированный ответ от AI в красивый текст для отображения.
        """
        details = ai_result.get('details', {})
        summary = ai_result.get('summary', 'Нет краткого описания.')

        lines = []
        lines.append(f"📊 Итоговая оценка: {ai_result.get('score', 0)}%\n")
        lines.append(f"📝 Резюме: {summary}\n")
        lines.append("--- Детальный анализ ---")
        lines.append(f"🔹 Опыт: {details.get('experience_match', 'Не указано')}")
        lines.append(f"🔹 Навыки: {details.get('skills_match', 'Не указано')}")
        lines.append(f"🔹 Локация: {details.get('location_match', 'Не указано')}")
        lines.append(f"🔹 Зарплата: {details.get('salary_match', 'Не указано')}")
        lines.append(f"🔹 График/Занятость: {details.get('schedule_employment_match', 'Не указано')}")

        strengths = details.get('strengths', [])
        if strengths:
            lines.append("✅ Сильные стороны:")
            for s in strengths:
                lines.append(f"  - {s}")

        weaknesses = details.get('weaknesses', [])
        if weaknesses:
            lines.append("⚠️ Слабые стороны/Риски:")
            for w in weaknesses:
                lines.append(f"  - {w}")

        lines.append(f"🎯 Рекомендация: {details.get('recommendation', 'Не указано')}")

        # Добавим контактную информацию из кандидата, как было в старой версии
        lines.append("\n--- Контактная информация ---")
        if candidate.get('phone'):
            lines.append(f"📞 Телефон: {candidate.get('phone')}")
        if candidate.get('email'):
            lines.append(f"✉️ Email: {candidate.get('email')}")

        return '\n'.join(lines)

    # Старые методы extract_keywords, analyze_candidate, generate_details можно удалить
    """Поток для анализа кандидатов"""
    
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(list)
    finished_signal = pyqtSignal()
    
    def __init__(self, vacancy, candidates_data):
        super().__init__()
        self.vacancy = vacancy
        self.candidates_data = candidates_data
        
    def run(self):
        """Запуск анализа в отдельном потоке"""
        results = []
        
        # Извлечение требований из вакансии
        requirements_text = self.vacancy.get('requirements', '') + ' ' + \
                           self.vacancy.get('responsibilities', '') + ' ' + \
                           self.vacancy.get('skills', '')
        
        # Ключевые слова для оценки
        keywords = self.extract_keywords(requirements_text.lower())
        
        total = len(self.candidates_data)
        for i, candidate in enumerate(self.candidates_data):
            score = self.analyze_candidate(candidate, keywords)
            details = self.generate_details(candidate, keywords)
            
            results.append({
                'candidate': candidate,
                'score': score,
                'details': details
            })
            self.progress_signal.emit(int((i + 1) / total * 100))
        
        # Сортировка по убыванию рейтинга
        results.sort(key=lambda x: x['score'], reverse=True)
        self.result_signal.emit(results)
        self.finished_signal.emit()
    
    def extract_keywords(self, text):
        """Извлечение ключевых слов из текста требований"""
        text = text.lower()
        
        # Словари ключевых слов по категориям
        keywords = {
            'образование': ['высшее', 'образование', 'диплом', 'university', 'degree', 'бакалавр', 'магистр'],
            'опыт': ['опыт', 'стаж', 'experience', 'years', 'лет', 'года'],
            'языки': ['английский', 'english', 'intermediate', 'upper-intermediate', 'fluent', 'ielts', 'toefl'],
            'программирование': ['python', 'java', 'c++', 'javascript', 'sql', '1с', 'php', 'ruby', 'go'],
            'офисные': ['excel', 'word', 'powerpoint', 'outlook', '1с', 'photoshop', 'autocad', 'solidworks'],
            'личные': ['коммуникабельность', 'ответственность', 'стрессоустойчивость', 'инициативность',
                      'team player', 'leadership', 'самостоятельность', 'обучаемость']
        }
        
        found_keywords = []
        for category, words in keywords.items():
            for word in words:
                if word in text:
                    found_keywords.append(word)
        
        return found_keywords
    
    def analyze_candidate(self, candidate, keywords):
        """Анализ кандидата и вычисление рейтинга"""
        score = 40  # Базовый score
        
        # Объединяем всю информацию о кандидате
        candidate_text = f"{candidate.get('name', '')} {candidate.get('experience', '')} {candidate.get('skills', '')}".lower()
        
        # Увеличиваем score за каждое найденное ключевое слово
        for keyword in keywords:
            if keyword in candidate_text:
                score += 3
        
        # Бонус за опыт работы
        experience = candidate.get('experience', '').lower()
        if 'более 6' in experience or '>6' in experience:
            score += 20
        elif '3 до 6' in experience or '3-6' in experience:
            score += 15
        elif '1 до 3' in experience or '1-3' in experience:
            score += 10
        elif 'нет опыта' in experience:
            score += 5
        
        # Бонус за наличие email и телефона
        if candidate.get('email') and '@' in candidate.get('email', ''):
            score += 5
        if candidate.get('phone') and len(candidate.get('phone', '')) > 10:
            score += 5
        
        # Бонус за соответствие города
        vacancy_city = self.vacancy.get('area', '').lower()
        candidate_city = candidate.get('city', '').lower()
        if vacancy_city and candidate_city and vacancy_city in candidate_city:
            score += 10
        
        return min(100, max(0, score))  # Ограничиваем 0-100
    
    def generate_details(self, candidate, keywords):
        """Генерация детального отчета"""
        details = []
        
        # Контактная информация
        if candidate.get('phone'):
            details.append(f"📞 Телефон: {candidate.get('phone')}")
        if candidate.get('email'):
            details.append(f"✉️ Email: {candidate.get('email')}")
        if candidate.get('city'):
            details.append(f"🏙️ Город: {candidate.get('city')}")
        
        details.append("")  # Пустая строка для разделения
        
        # Опыт
        exp = candidate.get('experience', 'Не указан')
        details.append(f"📊 Опыт: {exp}")
        
        # Навыки
        skills = candidate.get('skills', '')
        if skills:
            details.append(f"🔧 Навыки: {skills}")
        
        # Найденные ключевые слова
        found = []
        candidate_text = f"{candidate.get('name', '')} {exp} {skills}".lower()
        for keyword in keywords[:10]:  # Ограничиваем до 10 ключевых слов
            if keyword in candidate_text:
                found.append(keyword)
        
        if found:
            details.append(f"✅ Соответствие требованиям: {', '.join(found)}")
        
        # Проверка контактных данных
        if not candidate.get('phone') or not candidate.get('email'):
            details.append("⚠️ Отсутствуют контактные данные")
        
        return '\n'.join(details)

class AIAgentWindow(QWidget):
    """Окно AI-агента для анализа кандидатов"""
    
    def __init__(self, vacancy):
        super().__init__()
        self.vacancy = vacancy
        self.candidates = self.generate_demo_candidates()
        self.analysis_results = []
        self.init_ui()
        
    def generate_demo_candidates(self):
        """Генерация демо-кандидатов с реальными данными"""
        candidates = []
        
        # Список реальных имен
        first_names = ["Александр", "Елена", "Дмитрий", "Анна", "Сергей", "Ольга", "Михаил", "Татьяна", "Андрей", "Наталья"]
        last_names = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев", "Михайлов", "Федоров", "Морозов"]
        
        # Список телефонов
        phones = [
            "+7 (903) 123-45-67",
            "+7 (916) 234-56-78",
            "+7 (925) 345-67-89",
            "+7 (926) 456-78-90",
            "+7 (977) 567-89-01",
            "+7 (985) 678-90-12",
            "+7 (495) 123-45-67",
            "+7 (812) 234-56-78",
            "+7 (383) 345-67-89",
            "+7 (846) 456-78-90"
        ]
        
        # Список email
        emails = [
            "ivanov.a@gmail.com",
            "petrova.elena@yandex.ru",
            "dmitry.s@mail.ru",
            "anna.smirnova@outlook.com",
            "sergey.k@yahoo.com",
            "olga.popova@inbox.ru",
            "mikhail.v@company.ru",
            "tatiana.m@workmail.com",
            "andrey.f@hotmail.com",
            "natalia.m@bk.ru"
        ]
        
        # Список городов
        cities = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", 
                  "Краснодар", "Сочи", "Ростов-на-Дону", "Самара", "Уфа"]
        
        # Список вакансий (названия из исходного файла)
        job_titles = [
            "Инженер-контролер по неразрушающему контролю",
            "Специалист по работе с клиентами",
            "Специалист по снабжению",
            "Инженер-программист станков ЧПУ",
            "Водитель-тракторист",
            "Слесарь-сборщик летательных аппаратов",
            "Специалист по кадровому администрированию",
            "Специалист call-центра",
            "Электромонтер",
            "Менеджер IT-Решений"
        ]
        
        # Опыт работы
        experiences = ["Нет опыта", "От 1 года до 3 лет", "От 3 до 6 лет", "Более 6 лет"]
        
        # Навыки
        skills_list = [
            "Python, SQL, Excel",
            "Коммуникабельность, стрессоустойчивость",
            "1С, документооборот, Excel",
            "AutoCAD, SolidWorks, Компас",
            "Права категории B, C",
            "Слесарные работы, чтение чертежей",
            "Кадровый учет, 1С ЗУП, трудовое право",
            "Английский язык, деловая переписка",
            "Электробезопасность, ПУЭ",
            "Project Management, Agile, Scrum"
        ]
        
        # Генерация 20 кандидатов
        for i in range(20):
            name = f"{random.choice(last_names)} {random.choice(first_names)}"
            if i % 2 == 0:  # Добавляем отчество для разнообразия
                name += f" {random.choice(['Александрович', 'Дмитриевич', 'Сергеевич', 'Михайлович'])}"
            
            candidate = {
                'name': name,
                'phone': random.choice(phones),
                'email': random.choice(emails),
                'city': random.choice(cities),
                'vacancy_title': random.choice(job_titles),
                'experience': random.choice(experiences),
                'skills': random.choice(skills_list),
                'source': 'hh.ru',
                'id': f"candidate_{i+1}"
            }
            candidates.append(candidate)
        
        return candidates
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle(f"S7 Recruitment - AI Анализ кандидатов")
        self.setGeometry(200, 200, 1200, 800)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        # Основной layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header_label = QLabel(f"🤖 AI Анализ кандидатов")
        header_label.setObjectName("headerLabel")
        layout.addWidget(header_label)
        
        # Информация о вакансии
        vacancy_group = QGroupBox("Анализируемая вакансия")
        vacancy_layout = QVBoxLayout()
        
        vacancy_title = QLabel(self.vacancy.get('title', 'Неизвестно'))
        vacancy_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {styles.S7_GREEN};")
        vacancy_title.setWordWrap(True)
        vacancy_layout.addWidget(vacancy_title)
        
        vacancy_city = QLabel(f"📍 {self.vacancy.get('area', 'Город не указан')}")
        vacancy_layout.addWidget(vacancy_city)
        
        vacancy_group.setLayout(vacancy_layout)
        layout.addWidget(vacancy_group)
        
        # Параметры анализа
        params_group = QGroupBox("Параметры анализа")
        params_layout = QHBoxLayout()
        
        params_layout.addWidget(QLabel("Минимальный рейтинг:"))
        self.min_score = QSpinBox()
        self.min_score.setRange(0, 100)
        self.min_score.setValue(60)
        self.min_score.setSuffix("%")
        params_layout.addWidget(self.min_score)
        
        params_layout.addWidget(QLabel("Количество результатов:"))
        self.max_results = QSpinBox()
        self.max_results.setRange(1, 50)
        self.max_results.setValue(10)
        params_layout.addWidget(self.max_results)
        
        params_layout.addStretch()
        
        self.analyze_btn = QPushButton("🚀 Запустить анализ")
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        params_layout.addWidget(self.analyze_btn)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Таблица результатов
        results_group = QGroupBox("Результаты анализа")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(["Рейтинг", "ФИО", "Телефон", "Email", "Вакансия", "Действия"])
        
        # Настройка колонок
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Рейтинг
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # ФИО
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Телефон
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Email
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # Вакансия
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Действия
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.doubleClicked.connect(self.show_candidate_details)
        
        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Рекомендация
        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet(f"""
            background-color: {styles.S7_GREEN};
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
        """)
        layout.addWidget(self.recommendation_label)
        
        self.setLayout(layout)
    
    def start_analysis(self):
        """Запуск анализа кандидатов"""
        if not self.candidates:
            QMessageBox.warning(self, "Предупреждение", "Нет данных о кандидатах")
            return
        
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_table.setRowCount(0)
        self.recommendation_label.clear()
        
        # Запуск анализа в отдельном потоке
        self.analyzer = CandidateAnalyzer(self.vacancy, self.candidates)
        self.analyzer.progress_signal.connect(self.progress_bar.setValue)
        self.analyzer.result_signal.connect(self.display_results)
        self.analyzer.finished_signal.connect(self.analysis_finished)
        self.analyzer.start()
    
    def display_results(self, results):
        """Отображение результатов анализа"""
        self.analysis_results = results
        
        # Фильтрация по минимальному рейтингу
        min_score = self.min_score.value()
        filtered_results = [r for r in results if r['score'] >= min_score]
        
        # Ограничение количества
        max_results = self.max_results.value()
        display_results = filtered_results[:max_results]
        
        self.results_table.setRowCount(len(display_results))
        
        for row, result in enumerate(display_results):
            candidate = result['candidate']
            
            # Рейтинг
            score = result['score']
            score_item = QTableWidgetItem(f"{score}%")
            
            # Цветовая индикация рейтинга
            if score >= 80:
                score_item.setForeground(QColor(styles.S7_GREEN))
            elif score >= 60:
                score_item.setForeground(QColor(styles.S7_LIGHT_GREEN))
            elif score >= 40:
                score_item.setForeground(QColor("#FFA500"))  # Оранжевый
            else:
                score_item.setForeground(QColor(styles.S7_RED))
            
            score_item.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(row, 0, score_item)
            
            # ФИО
            name_item = QTableWidgetItem(candidate.get('name', 'Неизвестно'))
            name_item.setToolTip(candidate.get('name', ''))
            self.results_table.setItem(row, 1, name_item)
            
            # Телефон
            phone = candidate.get('phone', 'Не указан')
            phone_item = QTableWidgetItem(phone)
            phone_item.setToolTip(phone)
            self.results_table.setItem(row, 2, phone_item)
            
            # Email
            email = candidate.get('email', 'Не указан')
            email_item = QTableWidgetItem(email)
            email_item.setToolTip(email)
            self.results_table.setItem(row, 3, email_item)
            
            # Вакансия кандидата
            vacancy_title = candidate.get('vacancy_title', 'Не указана')
            vacancy_item = QTableWidgetItem(vacancy_title)
            vacancy_item.setToolTip(vacancy_title)
            self.results_table.setItem(row, 4, vacancy_item)
            
            # Кнопка деталей
            details_btn = QPushButton("👁️ Подробнее")
            details_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {styles.S7_LIGHT_GREEN};
                    color: white;
                    padding: 5px 10px;
                    font-size: 11px;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: {styles.S7_GREEN};
                }}
            """)
            details_btn.clicked.connect(lambda checked, r=result: self.show_candidate_details_with_data(r))
            details_btn.setCursor(Qt.PointingHandCursor)
            self.results_table.setCellWidget(row, 5, details_btn)
        
        # Формирование рекомендации
        if display_results:
            best = display_results[0]
            candidate = best['candidate']
            self.recommendation_label.setText(
                f"🏆 Рекомендованный кандидат (рейтинг {best['score']}%):\n"
                f"👤 {candidate.get('name', 'Неизвестно')}\n"
                f"📞 {candidate.get('phone', 'Телефон не указан')}\n"
                f"✉️ {candidate.get('email', 'Email не указан')}\n"
                f"💼 Текущая вакансия: {candidate.get('vacancy_title', 'Не указана')}"
            )
        else:
            self.recommendation_label.setText("😕 Не найдено кандидатов с достаточным рейтингом")
    
    def analysis_finished(self):
        """Завершение анализа"""
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def show_candidate_details(self, index):
        """Показать детали кандидата при двойном клике"""
        row = index.row()
        if 0 <= row < len(self.analysis_results):
            result = self.analysis_results[row]
            dialog = CandidateDetailDialog(result, result['details'], self)
            dialog.exec_()
    
    def show_candidate_details_with_data(self, result):
        """Показать детали кандидата по кнопке"""
        dialog = CandidateDetailDialog(result, result['details'], self)
        dialog.exec_()