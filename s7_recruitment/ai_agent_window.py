# -*- coding: utf-8 -*-
"""
Окно AI-агента для анализа кандидатов с реальными данными из resume_file.json
"""
import json
import time
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QComboBox, QSpinBox, QProgressBar, QDialog,
                             QFormLayout, QDialogButtonBox, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import styles
from ai_analyzer import OllamaCandidateAnalyzer

# Кэш для результатов анализа, чтобы не пересчитывать при повторном открытии
analysis_cache = {}

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
    status_signal = pyqtSignal(str)  # Для отображения текущего статуса

    def __init__(self, vacancy, candidates_data):
        super().__init__()
        self.vacancy = vacancy
        self.candidates_data = candidates_data
        self.ai_analyzer = OllamaCandidateAnalyzer(model_name="mistral:7b-instruct-q4_0")
        self.is_running = True

    def run(self):
        """Запуск AI-анализа в отдельном потоке"""
        results = []
        total = len(self.candidates_data)
        
        # Создаем ключ для кэша на основе ID вакансии
        cache_key = self.vacancy.get('id', 'default')
        
        # Проверяем, есть ли уже результаты в кэше
        if cache_key in analysis_cache:
            self.status_signal.emit("Загрузка результатов из кэша...")
            results = analysis_cache[cache_key]
            for i in range(total):
                self.progress_signal.emit(int((i + 1) / total * 100))
                self.msleep(50)  # Небольшая задержка для плавности
        else:
            # Анализируем каждого кандидата
            for i, candidate in enumerate(self.candidates_data):
                if not self.is_running:
                    break
                    
                try:
                    self.status_signal.emit(f"Анализ кандидата {i+1} из {total}...")
                    
                    # Вызываем AI-анализ с таймаутом
                    ai_result = self.ai_analyzer.analyze(self.vacancy, candidate)

                    result_item = {
                        'candidate': candidate,
                        'score': ai_result.get('score', 0),
                        'details': self._format_details_for_display(ai_result, candidate)
                    }
                    results.append(result_item)
                    
                except Exception as e:
                    self.status_signal.emit(f"Ошибка при анализе кандидата {i+1}: {str(e)}")
                    result_item = {
                        'candidate': candidate,
                        'score': 0,
                        'details': f"Ошибка анализа: {str(e)}"
                    }
                    results.append(result_item)

                # Обновляем прогресс
                self.progress_signal.emit(int((i + 1) / total * 100))
                
                # Небольшая задержка между запросами, чтобы не перегружать Ollama
                self.msleep(500)

            # Сохраняем результаты в кэш
            if self.is_running:
                analysis_cache[cache_key] = results

        # Сортировка по убыванию рейтинга
        results.sort(key=lambda x: x['score'], reverse=True)
        self.result_signal.emit(results)
        self.finished_signal.emit()

    def stop(self):
        """Остановка анализа"""
        self.is_running = False

    def _format_details_for_display(self, ai_result: dict, candidate: dict) -> str:
        """Преобразует структурированный ответ от AI в текст для отображения"""
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
        self.analyzer = None
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
                if item.get('vacancy_id') == current_vacancy_id:
                    candidates.extend(item.get('resumes', []))
                    print(f"Найдено {len(item.get('resumes', []))} кандидатов для вакансии {current_vacancy_id}")
        
            # Если не нашли по ID, показываем первые 5 кандидатов для примера
            if not candidates and resumes_data:
                # Берем кандидатов из первой вакансии в файле
                candidates = resumes_data[0].get('resumes', [])[:5]  # ← ОГРАНИЧЕНИЕ ДО 5
                print(f"Загружено {len(candidates)} кандидатов для примера")
        
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            candidates = []
    
        return candidates

    def generate_fallback_candidates(self):
        """Запасной метод для генерации минимальных демо-данных"""
        return [
            {
                "title": "Специалист по работе с клиентами",
                "first_name": "Анна",
                "last_name": "Иванова",
                "area": self.vacancy.get('area', 'Москва'),
                "experience": "Опыт работы в аэропорту 2 года",
                "skills": ["Английский язык", "Коммуникабельность"],
                "salary": "80000"
            }
        ]
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle(f"S7 Recruitment - AI Анализ кандидатов")
        self.setGeometry(200, 200, 1200, 800)
        self.setStyleSheet(styles.MAIN_STYLE)
        
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
        
        # Кнопка остановки
        self.stop_btn = QPushButton("⏹️ Остановить")
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {styles.S7_RED};
                color: white;
            }}
            QPushButton:hover {{
                background-color: {styles.S7_RED};
                opacity: 0.8;
            }}
        """)
        params_layout.addWidget(self.stop_btn)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Статус и прогресс
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Готов к анализу")
        self.status_label.setStyleSheet(f"color: {styles.S7_GRAY};")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        status_layout.addWidget(self.progress_bar)
        
        layout.addLayout(status_layout)
        
        # Таблица результатов
        results_group = QGroupBox("Результаты анализа")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Рейтинг", "ФИО", "Желаемая должность", "Город", "Действия"])
        
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
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
        
        # Проверяем, есть ли уже результаты в кэше
        cache_key = self.vacancy.get('id', 'default')
        if cache_key in analysis_cache:
            self.analyze_btn.setText("🔄 Показать результаты из кэша")
            self.status_label.setText("Найдены сохраненные результаты")
    
    def check_ollama_connection(self):
        """Проверка подключения к Ollama"""
        ports_to_check = [11434, 11435, 11436]
    
        for port in ports_to_check:
            try:
                import requests
                response = requests.get(f"http://localhost:{port}/api/tags", timeout=1)
                if response.status_code == 200:
                    print(f"✅ Ollama доступна на порту {port}")
                    return True
            except:
                continue
    
        print("❌ Ollama не найдена")
        return False
    
    def start_analysis(self):
        """Запуск анализа кандидатов"""
        if not self.candidates:
            QMessageBox.warning(self, "Предупреждение", "Нет данных о кандидатах")
            return
        
        cache_key = self.vacancy.get('id', 'default')
        
        # Если есть кэш, показываем его сразу
        if cache_key in analysis_cache:
            self.display_results(analysis_cache[cache_key])
            self.status_label.setText("Результаты загружены из кэша")
            return
        
        # Проверяем доступность Ollama
        if not self.check_ollama_connection():
            reply = QMessageBox.question(
                self, 
                "Подключение к Ollama",
                "Не удалось подключиться к Ollama. Хотите продолжить с упрощенным анализом?\n\n"
                "(Будет использован базовый анализ без AI)",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.analyze_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_table.setRowCount(0)
        self.recommendation_label.clear()
        self.status_label.setText("Подготовка к анализу...")
        
        # Запуск анализа в отдельном потоке
        self.analyzer = CandidateAnalyzer(self.vacancy, self.candidates)
        self.analyzer.progress_signal.connect(self.update_progress)
        self.analyzer.result_signal.connect(self.display_results)
        self.analyzer.finished_signal.connect(self.analysis_finished)
        self.analyzer.status_signal.connect(self.status_label.setText)
        self.analyzer.start()
        
        # Таймаут на случай зависания
        QTimer.singleShot(30000, self.check_analysis_timeout)  # 30 секунд
    
    def check_analysis_timeout(self):
        """Проверка таймаута анализа"""
        if self.analyzer and self.analyzer.isRunning():
            reply = QMessageBox.question(
                self,
                "Анализ завис",
                "Анализ выполняется дольше обычного. Продолжить ожидание?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                self.stop_analysis()
    
    def stop_analysis(self):
        """Остановка анализа"""
        if self.analyzer and self.analyzer.isRunning():
            self.analyzer.stop()
            self.analyzer.wait(2000)  # Ждем завершения потока
            self.status_label.setText("Анализ остановлен пользователем")
            self.analysis_finished()
    
    def update_progress(self, value):
        """Обновление прогресса"""
        self.progress_bar.setValue(value)
        if value < 100:
            self.status_label.setText(f"Анализ... {value}%")
    
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
        
            if score >= 80:
                score_item.setForeground(QColor(styles.S7_GREEN))
            elif score >= 60:
                score_item.setForeground(QColor(styles.S7_LIGHT_GREEN))
            elif score >= 40:
                score_item.setForeground(QColor("#FFA500"))
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
    
        # Формирование топа кандидатов
        if display_results:
            top_3 = display_results[:min(3, len(display_results))]
            top_text = "🏆 ТОП КАНДИДАТОВ:\n\n"
        
            for i, result in enumerate(top_3, 1):
                candidate = result['candidate']
                if 'first_name' in candidate:
                    name = f"{candidate.get('last_name', '')} {candidate.get('first_name', '')}"
                else:
                    name = candidate.get('name', 'Неизвестно')
            
            # Добавляем разбалловку если есть
                criteria = result.get('criteria', {})
                if criteria:
                    scores = f" [Опыт:{criteria.get('experience',0)} Навыки:{criteria.get('skills',0)} Локация:{criteria.get('location',0)}]"
                else:
                    scores = ""
            
                top_text += f"{i}. {name} - {result['score']}%{scores}\n"
                top_text += f"   💼 {candidate.get('title', 'Не указана')}\n"
                if result.get('strengths'):
                    top_text += f"   ✅ {', '.join(result['strengths'][:2])}\n"
                top_text += "\n"
        
            self.recommendation_label.setText(top_text)
        else:
            self.recommendation_label.setText("😕 Не найдено кандидатов с достаточным рейтингом")

    def analysis_finished(self):
        """Завершение анализа"""
        self.analyze_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Анализ завершен")
        
        # Освобождаем ресурсы
        if self.analyzer:
            self.analyzer = None
    
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
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.analyzer and self.analyzer.isRunning():
            self.analyzer.stop()
            self.analyzer.wait(1000)
        event.accept()