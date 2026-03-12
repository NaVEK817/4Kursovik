# -*- coding: utf-8 -*-
"""
Окно AI-агента для анализа кандидатов
"""
import json
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QComboBox, QSpinBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import styles

class CandidateAnalyzer(QThread):
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
        keywords = self.extract_keywords(requirements_text)
        
        total = len(self.candidates_data)
        for i, candidate in enumerate(self.candidates_data):
            score = self.analyze_candidate(candidate, keywords)
            results.append({
                'candidate': candidate,
                'score': score,
                'details': self.generate_details(candidate, keywords)
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
            'образование': ['высшее', 'образование', 'диплом', 'university', 'degree'],
            'опыт': ['опыт', 'стаж', 'experience', 'years'],
            'языки': ['английский', 'english', 'intermediate', 'upper-intermediate', 'fluent'],
            'навыки': ['python', 'java', 'sql', 'excel', 'word', 'photoshop', '1с', 'autocad'],
            'личные_качества': ['коммуникабельность', 'ответственность', 'стрессоустойчивость',
                               'team player', 'leadership', 'initiative']
        }
        
        found_keywords = []
        for category, words in keywords.items():
            for word in words:
                if word in text:
                    found_keywords.append(word)
        
        return found_keywords
    
    def analyze_candidate(self, candidate, keywords):
        """Анализ кандидата и вычисление рейтинга"""
        # В реальном приложении здесь был бы более сложный алгоритм
        # Для демо используем упрощенную оценку
        
        score = 50  # Базовый score
        
        # Объединяем всю информацию о кандидате
        candidate_text = json.dumps(candidate).lower()
        
        # Увеличиваем score за каждое найденное ключевое слово
        for keyword in keywords:
            if keyword in candidate_text:
                score += 5
        
        # Бонус за опыт работы
        experience = candidate.get('experience', '')
        if 'более 6' in experience or '6' in experience:
            score += 20
        elif '3 до 6' in experience:
            score += 15
        elif '1 до 3' in experience:
            score += 10
        elif 'нет опыта' in experience:
            score += 5
        
        # Бонус за наличие навыков
        skills = candidate.get('skills', '')
        if skills:
            score += len(skills.split(',')) * 2
        
        return min(100, score)  # Ограничиваем 100
    
    def generate_details(self, candidate, keywords):
        """Генерация детального отчета"""
        details = []
        
        # Образование
        req_text = self.vacancy.get('requirements', '').lower()
        if 'высшее' in req_text:
            details.append("Требуется высшее образование")
        
        # Опыт
        exp = candidate.get('experience', '')
        details.append(f"Опыт кандидата: {exp}")
        
        # Навыки
        skills = candidate.get('skills', '')
        if skills:
            details.append(f"Навыки: {skills}")
        
        # Найденные ключевые слова
        found = []
        candidate_text = json.dumps(candidate).lower()
        for keyword in keywords[:5]:
            if keyword in candidate_text:
                found.append(keyword)
        
        if found:
            details.append(f"Ключевые слова: {', '.join(found)}")
        
        return '\n'.join(details)

class AIAgentWindow(QWidget):
    """Окно AI-агента для анализа кандидатов"""
    
    def __init__(self, vacancy):
        super().__init__()
        self.vacancy = vacancy
        self.candidates = []
        self.analysis_results = []
        self.init_ui()
        self.load_candidates()
        
    def load_candidates(self):
        """Загрузка кандидатов из файла с вакансиями"""
        try:
            with open('vacancy_test_file.json', 'r', encoding='utf-8') as f:
                self.candidates = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить кандидатов: {str(e)}")
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle(f"S7 Recruitment - AI Анализ кандидатов")
        self.setGeometry(200, 200, 1000, 700)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        # Основной layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header_label = QLabel(f"🤖 AI Анализ кандидатов для вакансии:\n{self.vacancy.get('title', '')}")
        header_label.setObjectName("headerLabel")
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # Информация о вакансии
        info_group = QGroupBox("Требования вакансии")
        info_layout = QVBoxLayout()
        
        req_text = QTextEdit()
        req_text.setReadOnly(True)
        req_text.setMaximumHeight(150)
        req_text.setText(
            f"Требования: {self.vacancy.get('requirements', 'Не указаны')}\n\n"
            f"Обязанности: {self.vacancy.get('responsibilities', 'Не указаны')}\n\n"
            f"Навыки: {self.vacancy.get('skills', 'Не указаны')}"
        )
        info_layout.addWidget(req_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
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
        self.max_results.setRange(1, 20)
        self.max_results.setValue(5)
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
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Рейтинг", "Кандидат", "Опыт", "Детали"])
        
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Рекомендация
        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet(f"""
            background-color: {styles.S7_LIGHT_GREEN};
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
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
            score_item = QTableWidgetItem(f"{result['score']}%")
            score_item.setForeground(Qt.darkGreen if result['score'] >= 80 else Qt.darkYellow)
            self.results_table.setItem(row, 0, score_item)
            
            # Название вакансии (как кандидат)
            self.results_table.setItem(row, 1, QTableWidgetItem(candidate.get('title', '')))
            
            # Опыт
            self.results_table.setItem(row, 2, QTableWidgetItem(candidate.get('experience', '')))
            
            # Детали
            details_item = QTableWidgetItem(result['details'])
            details_item.setToolTip(result['details'])
            self.results_table.setItem(row, 3, details_item)
        
        # Формирование рекомендации
        if display_results:
            best = display_results[0]
            self.recommendation_label.setText(
                f"🏆 Рекомендованный кандидат с рейтингом {best['score']}%:\n"
                f"{best['candidate'].get('title', '')}\n"
                f"Опыт: {best['candidate'].get('experience', '')}"
            )
        else:
            self.recommendation_label.setText("😕 Не найдено кандидатов с достаточным рейтингом")
    
    def analysis_finished(self):
        """Завершение анализа"""
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)