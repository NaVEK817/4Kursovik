# -*- coding: utf-8 -*-
"""
Окно AI-агента для анализа кандидатов с реальными данными из resume_file.json
"""
import json
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QComboBox, QSpinBox, QProgressBar, QDialog,
                             QFormLayout, QVBoxLayout as QVBoxDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush
import styles
from ai_analyzer import OllamaCandidateAnalyzer


class CandidateDetailDialog(QDialog):
    """Диалог с детальной информацией о кандидате"""
    
    def __init__(self, candidate_data, analysis_details, rank_info, parent=None):
        super().__init__(parent)
        self.candidate = candidate_data['candidate']
        self.score = candidate_data['score']
        self.rank = rank_info['rank']
        self.total = rank_info['total']
        self.analysis_details = analysis_details
        self.ai_result = candidate_data.get('ai_result', {})
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"Детальная информация о кандидате")
        self.setGeometry(300, 300, 800, 700)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Заголовок с рейтингом и местом
        title_layout = QHBoxLayout()
        
        # Формируем полное имя кандидата
        full_name = f"{self.candidate.get('last_name', '')} {self.candidate.get('first_name', '')} {self.candidate.get('middle_name', '')}".strip()
        if not full_name:
            full_name = "Кандидат"
        
        name_label = QLabel(f"👤 {full_name}")
        name_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {styles.S7_GREEN};")
        title_layout.addWidget(name_label)
        
        title_layout.addStretch()
        
        # Место в рейтинге
        rank_label = QLabel(f"#{self.rank} из {self.total}")
        rank_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {styles.S7_DARK_GREEN};
            background-color: {styles.S7_LIGHT_GRAY};
            padding: 5px 10px;
            border-radius: 10px;
            margin-right: 10px;
        """)
        title_layout.addWidget(rank_label)
        
        # Основной рейтинг
        score_label = QLabel(f"{self.score}%")
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
        info_group = QGroupBox("Основная информация")
        info_layout = QFormLayout()
        
        # Возраст
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
        city = self.candidate.get('area', 'Не указан')
        info_layout.addRow("🏙️ Город:", QLabel(city))
        
        # Пол
        gender = self.candidate.get('gender', '')
        if gender:
            gender_text = "Мужской" if gender == 'male' else "Женский" if gender == 'female' else gender
            info_layout.addRow("⚥ Пол:", QLabel(gender_text))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Образование
        edu_group = QGroupBox("Образование")
        edu_layout = QVBoxLayout()
        
        education = self.candidate.get('education', {})
        if isinstance(education, dict):
            edu_text = f"Уровень: {education.get('level', 'Не указано')}"
            if education.get('institution'):
                edu_text += f"\nУчебное заведение: {education.get('institution')}"
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
                    # Расчет продолжительности
                    start = exp.get('start', '')
                    end = exp.get('end', 'н.в.')
                    duration = ""
                    if start and len(start) >= 4:
                        start_year = int(start[:4])
                        if end and end != 'null' and end != 'н.в.':
                            if len(end) >= 4:
                                end_year = int(end[:4])
                            else:
                                end_year = 2026
                        else:
                            end_year = 2026
                        years = end_year - start_year
                        if years > 0:
                            duration = f" ({years} лет)"
                    
                    exp_text = f"🏢 {exp.get('company', 'Компания не указана')}"
                    if exp.get('position'):
                        exp_text += f"\n   Должность: {exp.get('position')}{duration}"
                    if start or end:
                        exp_text += f"\n   Период: {start} - {end}"
                    if exp.get('description'):
                        exp_text += f"\n   {exp.get('description')}"
                    
                    exp_label = QLabel(exp_text)
                    exp_label.setWordWrap(True)
                    exp_label.setStyleSheet("margin-bottom: 10px;")
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
        
        # Зарплатные ожидания
        salary_group = QGroupBox("Зарплатные ожидания")
        salary_layout = QFormLayout()
        
        salary = self.candidate.get('salary', 'Не указаны')
        salary_layout.addRow("💰 Ожидаемая зарплата:", QLabel(str(salary)))
        
        schedule = self.candidate.get('schedule', 'Не указан')
        salary_layout.addRow("⏰ Желаемый график:", QLabel(schedule))
        
        employment = self.candidate.get('employment', 'Не указана')
        salary_layout.addRow("📊 Желаемая занятость:", QLabel(employment))
        
        salary_group.setLayout(salary_layout)
        layout.addWidget(salary_group)
        
        # AI Анализ
        analysis_group = QGroupBox("AI Анализ соответствия вакансии")
        analysis_layout = QVBoxLayout()
        
        # Краткое резюме
        summary = self.ai_result.get('summary', '')
        if summary:
            summary_label = QLabel(f"📝 {summary}")
            summary_label.setWordWrap(True)
            summary_label.setStyleSheet(f"""
                background-color: {styles.S7_LIGHT_GREEN};
                color: {styles.S7_BLACK};
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            """)
            analysis_layout.addWidget(summary_label)
        
        # Детальный анализ
        analysis_text = QTextEdit()
        analysis_text.setReadOnly(True)
        analysis_text.setMinimumHeight(300)
        analysis_text.setText(self.analysis_details)
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
        self.ai_analyzer = OllamaCandidateAnalyzer()

    def run(self):
        """Запуск AI-анализа в отдельном потоке"""
        results = []
        total = len(self.candidates_data)

        for i, candidate in enumerate(self.candidates_data):
            try:
                # Вызываем AI-анализ для каждого кандидата
                ai_result = self.ai_analyzer.analyze(self.vacancy, candidate)

                # Используем weighted_score если есть, иначе обычный score
                score = ai_result.get('weighted_score', ai_result.get('score', 30))
                # Убеждаемся, что score не меньше 30
                score = max(30, score)
                
                result_item = {
                    'candidate': candidate,
                    'score': score,
                    'ai_result': ai_result,
                    'details': self._format_details_for_display(ai_result, candidate)
                }
                results.append(result_item)
                
                print(f"Анализ кандидата {i+1}/{total} завершен. Оценка: {score}%")
                
            except Exception as e:
                print(f"Ошибка при анализе кандидата {i+1}: {str(e)}")
                result_item = {
                    'candidate': candidate,
                    'score': 30,  # Минимальный рейтинг при ошибке
                    'ai_result': {},
                    'details': f"Ошибка анализа: {str(e)}\n\nПрисвоен минимальный рейтинг 30%."
                }
                results.append(result_item)

            # Обновляем прогресс
            self.progress_signal.emit(int((i + 1) / total * 100))

        # Сортировка по убыванию рейтинга
        results.sort(key=lambda x: x['score'], reverse=True)
        self.result_signal.emit(results)
        self.finished_signal.emit()

    def _format_details_for_display(self, ai_result: dict, candidate: dict) -> str:
        """Преобразует структурированный ответ от AI в красивый текст для отображения."""
        
        lines = []
        lines.append("=" * 60)
        lines.append("🤖 AI АНАЛИЗ СООТВЕТСТВИЯ ВАКАНСИИ")
        lines.append("=" * 60)
        lines.append("")
        
        # Основные оценки
        score = ai_result.get('score', 30)
        weighted_score = ai_result.get('weighted_score', score)
        lines.append(f"📊 ИТОГОВАЯ ОЦЕНКА: {score}%")
        lines.append(f"⚖️  ВЗВЕШЕННАЯ ОЦЕНКА: {weighted_score}%")
        lines.append("")
        
        # Краткое резюме
        summary = ai_result.get('summary', '')
        if summary:
            lines.append("📝 КРАТКОЕ РЕЗЮМЕ:")
            lines.append(f"   {summary}")
            lines.append("")
        
        # Детальные оценки по критериям
        criterion_scores = ai_result.get('criterion_scores', {})
        if criterion_scores:
            lines.append("📊 ОЦЕНКИ ПО КРИТЕРИЯМ:")
            lines.append("-" * 40)
            
            criteria_names = {
                'experience': 'Опыт работы',
                'skills': 'Навыки',
                'education': 'Образование',
                'location': 'Локация',
                'schedule': 'График',
                'salary': 'Зарплата'
            }
            
            for criterion, display_name in criteria_names.items():
                if criterion in criterion_scores:
                    score_data = criterion_scores[criterion]
                    if isinstance(score_data, dict):
                        crit_score = score_data.get('score', 30)
                        comment = score_data.get('comment', '')
                    else:
                        crit_score = score_data
                        comment = ''
                    
                    # Визуальная шкала
                    bar_length = 20
                    filled = int(crit_score / 100 * bar_length)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    
                    lines.append(f"{display_name:15} [{bar}] {crit_score:3}%")
                    if comment:
                        lines.append(f"{' ' * 17}💬 {comment}")
            lines.append("")
        
        # Детальный анализ
        details = ai_result.get('details', {})
        
        if details.get('experience_match'):
            lines.append("🔹 ОПЫТ РАБОТЫ:")
            lines.append(f"   {details['experience_match']}")
            lines.append("")
        
        if details.get('skills_match'):
            lines.append("🔹 НАВЫКИ:")
            lines.append(f"   {details['skills_match']}")
            lines.append("")
        
        if details.get('education_match'):
            lines.append("🔹 ОБРАЗОВАНИЕ:")
            lines.append(f"   {details['education_match']}")
            lines.append("")
        
        if details.get('location_match'):
            lines.append("🔹 ЛОКАЦИЯ:")
            lines.append(f"   {details['location_match']}")
            lines.append("")
        
        if details.get('salary_match'):
            lines.append("🔹 ЗАРПЛАТА:")
            lines.append(f"   {details['salary_match']}")
            lines.append("")
        
        if details.get('schedule_employment_match'):
            lines.append("🔹 ГРАФИК И ЗАНЯТОСТЬ:")
            lines.append(f"   {details['schedule_employment_match']}")
            lines.append("")
        
        # Сильные стороны
        strengths = details.get('strengths', [])
        if strengths:
            lines.append("✅ СИЛЬНЫЕ СТОРОНЫ:")
            for s in strengths:
                lines.append(f"   • {s}")
            lines.append("")
        
        # Слабые стороны
        weaknesses = details.get('weaknesses', [])
        if weaknesses:
            lines.append("⚠️ СЛАБЫЕ СТОРОНЫ/РИСКИ:")
            for w in weaknesses:
                lines.append(f"   • {w}")
            lines.append("")
        
        # Ключевые выводы
        key_findings = details.get('key_findings', [])
        if key_findings:
            lines.append("🔑 КЛЮЧЕВЫЕ ВЫВОДЫ:")
            for finding in key_findings:
                lines.append(f"   • {finding}")
            lines.append("")
        
        # Рекомендация
        recommendation = details.get('recommendation', 'Не указано')
        recommendation_reason = details.get('recommendation_reason', '')
        
        lines.append("🎯 РЕКОМЕНДАЦИЯ:")
        if recommendation == "Да":
            lines.append(f"   ✅ {recommendation}")
        elif recommendation == "Сомнительно":
            lines.append(f"   ⚠️ {recommendation}")
        elif recommendation == "Нет":
            lines.append(f"   ❌ {recommendation}")
        else:
            lines.append(f"   {recommendation}")
        
        if recommendation_reason:
            lines.append(f"   💬 {recommendation_reason}")
        
        lines.append("")
        lines.append("=" * 60)
        
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
                if item.get('vacancy_id') == current_vacancy_id:
                    candidates.extend(item.get('resumes', []))
                    print(f"Найдено {len(item.get('resumes', []))} кандидатов для вакансии {current_vacancy_id}")
            
            # Если не нашли по ID, показываем все резюме
            if not candidates:
                for item in resumes_data:
                    candidates.extend(item.get('resumes', []))
                print(f"Загружено {len(candidates)} кандидатов из файла (все вакансии)")
            
        except FileNotFoundError:
            QMessageBox.warning(self, "Предупреждение", 
                               f"Файл {self.RESUME_FILE} не найден.")
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Предупреждение", 
                               "Ошибка при чтении файла с резюме.")
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", 
                               f"Ошибка загрузки кандидатов: {str(e)}")
        
        return candidates
    
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
        
        vacancy_exp = QLabel(f"💼 Требуемый опыт: {self.vacancy.get('experience', 'Не указан')}")
        vacancy_layout.addWidget(vacancy_exp)
        
        vacancy_group.setLayout(vacancy_layout)
        layout.addWidget(vacancy_group)
        
        # Параметры анализа
        params_group = QGroupBox("Параметры анализа")
        params_layout = QHBoxLayout()
        
        params_layout.addWidget(QLabel("Минимальный рейтинг:"))
        self.min_score = QSpinBox()
        self.min_score.setRange(30, 100)  # Минимум теперь 30
        self.min_score.setValue(50)
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
        self.results_table.setColumnCount(6)  # Добавили колонку для места
        self.results_table.setHorizontalHeaderLabels([
            "Место", "Рейтинг", "ФИО", "Желаемая должность", "Город", "Опыт (лет)"
        ])
        
        # Настройка колонок
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Место
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Рейтинг
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # ФИО
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Должность
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Город
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Опыт
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.doubleClicked.connect(self.show_candidate_details)
        
        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Статистика
        stats_group = QGroupBox("Статистика по кандидатам")
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel(f"Всего кандидатов: {len(self.candidates)}")
        stats_layout.addWidget(self.total_label)
        
        stats_layout.addStretch()
        
        self.analyzed_label = QLabel("Ожидание анализа...")
        stats_layout.addWidget(self.analyzed_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        self.setLayout(layout)
    
    def start_analysis(self):
        """Запуск анализа кандидатов"""
        if not self.candidates:
            QMessageBox.warning(self, "Предупреждение", "Нет данных о кандидатах")
            return
        
        # Проверяем доступность Ollama
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code != 200:
                QMessageBox.warning(self, "Предупреждение", 
                                   "Ollama не отвечает. Будет использован базовый анализ.")
        except:
            QMessageBox.warning(self, "Предупреждение", 
                               "Не удалось подключиться к Ollama. Будет использован базовый анализ.")
        
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_table.setRowCount(0)
        self.analyzed_label.setText("Анализ в процессе...")
        
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
            full_name = f"{candidate.get('last_name', '')} {candidate.get('first_name', '')} {candidate.get('middle_name', '')}".strip()
            if not full_name:
                full_name = "Кандидат"
            
            # Место в рейтинге
            rank_item = QTableWidgetItem(f"#{row + 1}")
            rank_item.setTextAlignment(Qt.AlignCenter)
            rank_item.setForeground(QBrush(QColor(styles.S7_DARK_GREEN)))
            rank_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.results_table.setItem(row, 0, rank_item)
            
            # Рейтинг
            score = result['score']
            score_item = QTableWidgetItem(f"{score}%")
            
            # Цветовая индикация
            if score >= 80:
                score_item.setForeground(QColor(styles.S7_GREEN))
            elif score >= 60:
                score_item.setForeground(QColor(styles.S7_LIGHT_GREEN))
            elif score >= 40:
                score_item.setForeground(QColor("#FFA500"))
            else:
                score_item.setForeground(QColor(styles.S7_RED))
            
            score_item.setTextAlignment(Qt.AlignCenter)
            score_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.results_table.setItem(row, 1, score_item)
            
            # ФИО
            name_item = QTableWidgetItem(full_name)
            name_item.setToolTip(full_name)
            self.results_table.setItem(row, 2, name_item)
            
            # Желаемая должность
            desired_title = candidate.get('title', 'Не указана')
            title_item = QTableWidgetItem(desired_title)
            title_item.setToolTip(desired_title)
            self.results_table.setItem(row, 3, title_item)
            
            # Город
            city = candidate.get('area', 'Не указан')
            city_item = QTableWidgetItem(city)
            self.results_table.setItem(row, 4, city_item)
            
            # Расчет общего опыта
            total_years = 0
            experience = candidate.get('experience', [])
            if isinstance(experience, list):
                for exp in experience:
                    if isinstance(exp, dict):
                        start = exp.get('start', '')
                        end = exp.get('end', '')
                        if start and len(start) >= 4:
                            start_year = int(start[:4])
                            if end and end != 'null' and end:
                                if len(end) >= 4:
                                    end_year = int(end[:4])
                                else:
                                    end_year = 2026
                            else:
                                end_year = 2026
                            total_years += end_year - start_year
            
            years_item = QTableWidgetItem(f"{total_years} лет")
            years_item.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(row, 5, years_item)
        
        # Обновляем статистику
        self.analyzed_label.setText(f"Проанализировано: {len(results)} кандидатов")
        
        # Показываем топ-кандидата
        if display_results:
            best = display_results[0]
            best_name = f"{best['candidate'].get('last_name', '')} {best['candidate'].get('first_name', '')}".strip()
            QMessageBox.information(self, "Топ кандидат", 
                                   f"🥇 Лучший кандидат:\n\n"
                                   f"{best_name}\n"
                                   f"Рейтинг: {best['score']}%\n"
                                   f"Должность: {best['candidate'].get('title', 'Не указана')}")
    
    def analysis_finished(self):
        """Завершение анализа"""
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def show_candidate_details(self, index):
        """Показать детали кандидата при двойном клике"""
        row = index.row()
        if 0 <= row < len(self.analysis_results):
            result = self.analysis_results[row]
            rank_info = {
                'rank': row + 1,
                'total': len(self.analysis_results)
            }
            dialog = CandidateDetailDialog(result, result['details'], rank_info, self)
            dialog.exec_()