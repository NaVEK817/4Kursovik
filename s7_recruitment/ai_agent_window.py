# -*- coding: utf-8 -*-
"""
Окно AI-агента для анализа кандидатов с реальными данными из resume_file.json
"""
import json
import re
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QComboBox, QSpinBox, QProgressBar, QDialog,
                             QFormLayout, QDialogButtonBox, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import styles
from ai_analyzer import OllamaCandidateAnalyzer  # Импортируем наш новый AI-анализатор

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
        self.setGeometry(300, 300, 700, 600)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Заголовок с рейтингом
        title_layout = QHBoxLayout()
        
        # Формируем полное имя кандидата
        if 'first_name' in self.candidate and 'last_name' in self.candidate:
            full_name = f"{self.candidate.get('last_name', '')} {self.candidate.get('first_name', '')} {self.candidate.get('middle_name', '')}".strip()
        else:
            full_name = self.candidate.get('name', 'Неизвестно')
        
        name_label = QLabel(f"👤 {full_name}")
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
        
        # Желаемая должность
        job_title = QLabel(f"💼 Желаемая должность: {self.candidate.get('title', 'Не указана')}")
        job_title.setWordWrap(True)
        job_title.setStyleSheet(f"font-size: 14px; color: {styles.S7_DARK_GREEN};")
        layout.addWidget(job_title)
        
        # Основная информация
        info_group = QGroupBox("Контактная информация")
        info_layout = QFormLayout()
        
        # Возраст (если есть дата рождения)
        birth_date = self.candidate.get('birth_date', '')
        if birth_date:
            try:
                birth_year = int(birth_date.split('-')[0])
                current_year = datetime.now().year
                age = current_year - birth_year
                info_layout.addRow("🎂 Возраст:", QLabel(f"{age} лет ({birth_date})"))
            except:
                info_layout.addRow("🎂 Дата рождения:", QLabel(birth_date))
        
        # Город
        city = self.candidate.get('area', self.candidate.get('city', 'Не указан'))
        info_layout.addRow("🏙️ Город:", QLabel(city))
        
        # Телефон (если есть)
        phone = self.candidate.get('phone', 'Не указан')
        info_layout.addRow("📞 Телефон:", QLabel(phone))
        
        # Email (если есть)
        email = self.candidate.get('email', 'Не указан')
        info_layout.addRow("✉️ Email:", QLabel(email))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Образование
        edu_group = QGroupBox("Образование")
        edu_layout = QVBoxLayout()
        
        education = self.candidate.get('education', {})
        if isinstance(education, dict):
            edu_text = f"{education.get('level', 'Не указано')}"
            if education.get('institution'):
                edu_text += f" - {education.get('institution')}"
            if education.get('specialization'):
                edu_text += f"\nСпециализация: {education.get('specialization')}"
            if education.get('year'):
                edu_text += f"\nГод окончания: {education.get('year')}"
        else:
            edu_text = str(education) if education else 'Не указано'
        
        edu_label = QLabel(edu_text)
        edu_label.setWordWrap(True)
        edu_layout.addWidget(edu_label)
        
        edu_group.setLayout(edu_layout)
        layout.addWidget(edu_group)
        
        # Опыт работы
        exp_group = QGroupBox("Опыт работы")
        exp_layout = QVBoxLayout()
        
        experience = self.candidate.get('experience', [])
        if isinstance(experience, list) and experience:
            for exp in experience:
                if isinstance(exp, dict):
                    exp_text = f"🏢 {exp.get('company', 'Компания не указана')}"
                    if exp.get('position'):
                        exp_text += f"\n   Должность: {exp.get('position')}"
                    if exp.get('start') or exp.get('end'):
                        exp_text += f"\n   Период: {exp.get('start', '')} - {exp.get('end', 'н.в.')}"
                    if exp.get('description'):
                        exp_text += f"\n   {exp.get('description')}"
                    
                    exp_label = QLabel(exp_text)
                    exp_label.setWordWrap(True)
                    exp_label.setStyleSheet("margin-bottom: 10px;")
                    exp_layout.addWidget(exp_label)
        elif isinstance(experience, str):
            exp_label = QLabel(experience)
            exp_label.setWordWrap(True)
            exp_layout.addWidget(exp_label)
        else:
            exp_layout.addWidget(QLabel("Опыт работы не указан"))
        
        exp_group.setLayout(exp_layout)
        layout.addWidget(exp_group)
        
        # Навыки
        skills_group = QGroupBox("Ключевые навыки")
        skills_layout = QVBoxLayout()
        
        skills = self.candidate.get('skills', [])
        if isinstance(skills, list):
            skills_text = " • ".join(skills) if skills else "Не указаны"
        else:
            skills_text = str(skills) if skills else "Не указаны"
        
        skills_label = QLabel(skills_text)
        skills_label.setWordWrap(True)
        skills_layout.addWidget(skills_label)
        
        skills_group.setLayout(skills_layout)
        layout.addWidget(skills_group)
        
        # Детали анализа
        analysis_group = QGroupBox("Детали анализа")
        analysis_layout = QVBoxLayout()
        
        analysis_text = QTextEdit()
        analysis_text.setReadOnly(True)
        analysis_text.setMinimumHeight(200)
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
        self.ai_analyzer = OllamaCandidateAnalyzer()

    def run(self):
        """Запуск AI-анализа в отдельном потоке"""
        results = []
        total = len(self.candidates_data)

        for i, candidate in enumerate(self.candidates_data):
            try:
                # Вызываем AI-анализ для каждого кандидата
                ai_result = self.ai_analyzer.analyze(self.vacancy, candidate)

                # Формируем результат в старом формате для совместимости
                result_item = {
                    'candidate': candidate,
                    'score': ai_result.get('score', 0),
                    'details': self._format_details_for_display(ai_result, candidate)
                }
                results.append(result_item)
            except Exception as e:
                # В случае ошибки добавляем кандидата с низким рейтингом
                result_item = {
                    'candidate': candidate,
                    'score': 0,
                    'details': f"Ошибка анализа: {str(e)}"
                }
                results.append(result_item)

            # Обновляем прогресс
            self.progress_signal.emit(int((i + 1) / total * 100))

        # Сортировка по убыванию рейтинга
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
        lines.append(f"📊 ИТОГОВАЯ ОЦЕНКА: {ai_result.get('score', 0)}%\n")
        lines.append(f"📝 КРАТКОЕ РЕЗЮМЕ: {summary}\n")
        lines.append("=" * 50)
        lines.append("ДЕТАЛЬНЫЙ АНАЛИЗ:")
        lines.append("=" * 50)
        lines.append(f"🔹 ОПЫТ: {details.get('experience_match', 'Не указано')}")
        lines.append(f"🔹 НАВЫКИ: {details.get('skills_match', 'Не указано')}")
        lines.append(f"🔹 ЛОКАЦИЯ: {details.get('location_match', 'Не указано')}")
        lines.append(f"🔹 ЗАРПЛАТА: {details.get('salary_match', 'Не указано')}")
        lines.append(f"🔹 ГРАФИК/ЗАНЯТОСТЬ: {details.get('schedule_employment_match', 'Не указано')}")

        strengths = details.get('strengths', [])
        if strengths:
            lines.append("\n✅ СИЛЬНЫЕ СТОРОНЫ:")
            for s in strengths:
                lines.append(f"  • {s}")

        weaknesses = details.get('weaknesses', [])
        if weaknesses:
            lines.append("\n⚠️ СЛАБЫЕ СТОРОНЫ/РИСКИ:")
            for w in weaknesses:
                lines.append(f"  • {w}")

        lines.append(f"\n🎯 РЕКОМЕНДАЦИЯ: {details.get('recommendation', 'Не указано')}")

        return '\n'.join(lines)


class AIAgentWindow(QWidget):
    """Окно AI-агента для анализа кандидатов"""
    
    RESUME_FILE = "resume_file.json"
    
    def __init__(self, vacancy):
        super().__init__()
        self.vacancy = vacancy
        self.candidates = self.load_candidates_from_file()
        self.analysis_results = []
        self.init_ui()
        
    def load_candidates_from_file(self):
        """Загрузка кандидатов из resume_file.json"""
        candidates = []
        
        try:
            with open(self.RESUME_FILE, 'r', encoding='utf-8') as f:
                resumes_data = json.load(f)
            
            # Ищем резюме для текущей вакансии
            current_vacancy_id = self.vacancy.get('id')
            
            for item in resumes_data:
                # Если в файле есть привязка к вакансии
                if item.get('vacancy_id') == current_vacancy_id:
                    candidates.extend(item.get('resumes', []))
                    print(f"Найдено {len(item.get('resumes', []))} кандидатов для вакансии {current_vacancy_id}")
            
            # Если не нашли по ID, добавляем все резюме (для демонстрации)
            if not candidates:
                for item in resumes_data:
                    candidates.extend(item.get('resumes', []))
                print(f"Загружено {len(candidates)} кандидатов из файла (все вакансии)")
            
        except FileNotFoundError:
            QMessageBox.warning(self, "Предупреждение", 
                               f"Файл {self.RESUME_FILE} не найден. Будут использованы демо-данные.")
            # Если файл не найден, используем минимальные демо-данные
            candidates = self.generate_fallback_candidates()
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Предупреждение", 
                               "Ошибка при чтении файла с резюме. Будут использованы демо-данные.")
            candidates = self.generate_fallback_candidates()
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", 
                               f"Ошибка загрузки кандидатов: {str(e)}. Будут использованы демо-данные.")
            candidates = self.generate_fallback_candidates()
        
        return candidates
    
    def generate_fallback_candidates(self):
        """Запасной метод для генерации минимальных демо-данных (на случай отсутствия файла)"""
        candidates = []
        
        # Несколько примеров для демонстрации
        fallback_data = [
            {
                "title": "Специалист по работе с клиентами",
                "first_name": "Анна",
                "last_name": "Иванова",
                "middle_name": "Петровна",
                "gender": "female",
                "birth_date": "1995-05-15",
                "area": "Москва",
                "experience": [
                    {
                        "company": "Аэрофлот",
                        "position": "Агент по регистрации",
                        "start": "2020-01",
                        "end": "2023-12",
                        "description": "Регистрация пассажиров, работа с багажом, решение конфликтных ситуаций."
                    }
                ],
                "education": {
                    "level": "Высшее",
                    "institution": "МГУ",
                    "specialization": "Менеджмент",
                    "year": 2017
                },
                "skills": ["Английский язык", "Коммуникабельность", "Работа с возражениями", "MS Office"],
                "salary": "80000",
                "schedule": "Сменный график",
                "employment": "Полная занятость"
            },
            {
                "title": "Инженер-программист",
                "first_name": "Дмитрий",
                "last_name": "Смирнов",
                "middle_name": "Алексеевич",
                "gender": "male",
                "birth_date": "1990-10-20",
                "area": "Санкт-Петербург",
                "experience": [
                    {
                        "company": "IT-Company",
                        "position": "Python разработчик",
                        "start": "2018-03",
                        "end": "2024-01",
                        "description": "Разработка backend на Python, работа с базами данных."
                    }
                ],
                "education": {
                    "level": "Высшее",
                    "institution": "СПбГУ",
                    "specialization": "Прикладная математика",
                    "year": 2013
                },
                "skills": ["Python", "SQL", "Django", "FastAPI", "PostgreSQL"],
                "salary": "150000",
                "schedule": "Полный день",
                "employment": "Полная занятость"
            }
        ]
        
        candidates.extend(fallback_data)
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
        
        if self.vacancy.get('salary'):
            vacancy_salary = QLabel(f"💰 {self.vacancy.get('salary')}")
            vacancy_layout.addWidget(vacancy_salary)
        
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
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Рейтинг", "ФИО", "Желаемая должность", "Город", "Действия"])
        
        # Настройка колонок
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Рейтинг
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # ФИО
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Должность
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Город
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Действия
        
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
        
        # Показываем количество загруженных кандидатов
        if self.candidates:
            QMessageBox.information(self, "Информация", 
                                   f"Загружено кандидатов для анализа: {len(self.candidates)}")
    
    def start_analysis(self):
        """Запуск анализа кандидатов"""
        if not self.candidates:
            QMessageBox.warning(self, "Предупреждение", "Нет данных о кандидатах")
            return
        
        # Проверяем доступность Ollama перед запуском
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code != 200:
                QMessageBox.warning(self, "Предупреждение", 
                                   "Ollama не отвечает. Убедитесь, что она запущена.\n"
                                   "Запустите 'ollama serve' в терминале.")
                return
        except:
            QMessageBox.warning(self, "Предупреждение", 
                               "Не удалось подключиться к Ollama. Убедитесь, что она запущена.\n"
                               "Запустите 'ollama serve' в терминале.")
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
            
            # Формируем ФИО
            if 'first_name' in candidate and 'last_name' in candidate:
                full_name = f"{candidate.get('last_name', '')} {candidate.get('first_name', '')} {candidate.get('middle_name', '')}".strip()
            else:
                full_name = candidate.get('name', 'Неизвестно')
            
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
            name_item = QTableWidgetItem(full_name)
            name_item.setToolTip(full_name)
            self.results_table.setItem(row, 1, name_item)
            
            # Желаемая должность
            desired_title = candidate.get('title', 'Не указана')
            title_item = QTableWidgetItem(desired_title)
            title_item.setToolTip(desired_title)
            self.results_table.setItem(row, 2, title_item)
            
            # Город
            city = candidate.get('area', candidate.get('city', 'Не указан'))
            city_item = QTableWidgetItem(city)
            self.results_table.setItem(row, 3, city_item)
            
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
            self.results_table.setCellWidget(row, 4, details_btn)
        
        # Формирование рекомендации
        if display_results:
            best = display_results[0]
            candidate = best['candidate']
            
            if 'first_name' in candidate and 'last_name' in candidate:
                best_name = f"{candidate.get('last_name', '')} {candidate.get('first_name', '')} {candidate.get('middle_name', '')}".strip()
            else:
                best_name = candidate.get('name', 'Неизвестно')
            
            self.recommendation_label.setText(
                f"🏆 Рекомендованный кандидат (рейтинг {best['score']}%):\n"
                f"👤 {best_name}\n"
                f"💼 Желаемая должность: {candidate.get('title', 'Не указана')}\n"
                f"🏙️ Город: {candidate.get('area', candidate.get('city', 'Не указан'))}\n\n"
                f"📝 {best.get('details', '').split('\\n')[1] if '\\n' in best.get('details', '') else ''}"
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