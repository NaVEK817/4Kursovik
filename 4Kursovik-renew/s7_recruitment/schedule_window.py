# -*- coding: utf-8 -*-
"""
Окно расписания собеседований с ИИ-ассистентом
"""
import json
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QCalendarWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QMessageBox, QGroupBox, QHeaderView,
                             QComboBox, QTimeEdit, QTextEdit, QLineEdit,
                             QDialog, QDialogButtonBox, QFormLayout, QSpinBox,
                             QTabWidget, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QColor  # ❗ ВАЖНО: добавить этот импорт
import styles
from ai_schedule_manager import AIScheduleManager  # Обновленный импорт


class ScheduleWindow(QWidget):
    """Окно расписания собеседований с ИИ-ассистентом"""

    SCHEDULE_FILE = "interviews_schedule.json"

    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.interviews = self.load_interviews()
        self.ai_agent = AIScheduleManager()  # Используем новый менеджер
        self.init_ui()
        self.update_interviews_list()

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("S7 Recruitment - Расписание собеседований")
        self.setGeometry(200, 200, 1300, 700)
        self.setStyleSheet(styles.MAIN_STYLE)

        # Основной layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Левая панель (календарь и форма)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        # Заголовок
        header_label = QLabel("📅 Календарь собеседований")
        header_label.setObjectName("headerLabel")
        left_layout.addWidget(header_label)

        # Календарь
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.clicked.connect(self.date_selected)
        self.calendar.setMinimumHeight(250)
        left_layout.addWidget(self.calendar)

        # Информация о выбранной дате
        date_group = QGroupBox("Выбранная дата")
        date_layout = QVBoxLayout()

        self.selected_date_label = QLabel()
        self.selected_date_label.setStyleSheet(f"font-size: 14px; color: {styles.S7_GREEN};")
        date_layout.addWidget(self.selected_date_label)

        date_group.setLayout(date_layout)
        left_layout.addWidget(date_group)

        # Форма для добавления
        add_group = QGroupBox("➕ Добавить собеседование")
        add_layout = QVBoxLayout()

        # Кандидат
        cand_layout = QHBoxLayout()
        cand_layout.addWidget(QLabel("Кандидат:"))
        self.candidate_input = QLineEdit()
        self.candidate_input.setPlaceholderText("Введите ФИО кандидата")
        cand_layout.addWidget(self.candidate_input)
        add_layout.addLayout(cand_layout)

        # Интервьюер
        interviewer_layout = QHBoxLayout()
        interviewer_layout.addWidget(QLabel("Интервьюер:"))
        self.interviewer_input = QLineEdit()
        self.interviewer_input.setPlaceholderText("Кто проводит собеседование")
        self.interviewer_input.setText(self.user_data.get('username', ''))
        interviewer_layout.addWidget(self.interviewer_input)
        add_layout.addLayout(interviewer_layout)

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
        self.comment_input.setMaximumHeight(60)
        comment_layout.addWidget(self.comment_input)
        add_layout.addLayout(comment_layout)

        # Кнопка добавления
        add_btn = QPushButton("➕ Добавить собеседование")
        add_btn.clicked.connect(self.add_interview)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_layout.addWidget(add_btn)

        add_group.setLayout(add_layout)
        left_layout.addWidget(add_group)

        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(350)

        # Центральная панель (таблица собеседований)
        center_panel = QWidget()
        center_layout = QVBoxLayout()
        center_layout.setSpacing(10)

        # Заголовок таблицы
        table_header = QLabel("📋 Собеседования на выбранную дату")
        table_header.setObjectName("headerLabel")
        center_layout.addWidget(table_header)

        # Таблица
        self.interviews_table = QTableWidget()
        self.interviews_table.setColumnCount(7)  # +1 колонка для ID
        self.interviews_table.setHorizontalHeaderLabels(
            ["ID", "Время", "Кандидат", "Интервьюер", "Комментарий", "Статус", "Действия"]
        )

        header = self.interviews_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Время
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Кандидат
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Интервьюер
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Комментарий
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Статус
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Действия

        self.interviews_table.setAlternatingRowColors(True)
        center_layout.addWidget(self.interviews_table)

        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.update_interviews_list)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        center_layout.addWidget(refresh_btn)

        center_panel.setLayout(center_layout)

        # Правая панель (ИИ-ассистент и статистика)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        # ИИ-ассистент
        ai_group = QGroupBox("🤖 ИИ-ассистент")
        ai_layout = QVBoxLayout()

        # Статус ИИ
        self.ai_status = QLabel("✅ ИИ активен")
        self.ai_status.setStyleSheet(f"color: {styles.S7_GREEN};")
        ai_layout.addWidget(self.ai_status)

        # Кнопка авто-назначения
        self.auto_schedule_btn = QPushButton("🎯 Авто-назначение времени")
        self.auto_schedule_btn.clicked.connect(self.auto_schedule)
        self.auto_schedule_btn.setCursor(Qt.PointingHandCursor)
        ai_layout.addWidget(self.auto_schedule_btn)

        # Кнопка анализа конфликтов
        self.analyze_conflicts_btn = QPushButton("🔍 Найти конфликты")
        self.analyze_conflicts_btn.clicked.connect(self.analyze_conflicts)
        self.analyze_conflicts_btn.setCursor(Qt.PointingHandCursor)
        ai_layout.addWidget(self.analyze_conflicts_btn)

        ai_group.setLayout(ai_layout)
        right_layout.addWidget(ai_group)

        # Статистика
        stats_group = QGroupBox("📊 Статистика")
        stats_layout = QVBoxLayout()

        self.stats_label = QLabel("Загрузка...")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)

        stats_group.setLayout(stats_layout)
        right_layout.addWidget(stats_group)

        # Советы
        tips_group = QGroupBox("💡 Советы")
        tips_layout = QVBoxLayout()

        tips = [
            "• Лучшее время: 10:00-12:00",
            "• Оставляйте 30 мин между собес.",
            "• Учитывайте часовые пояса",
            "• Подтверждайте за день"
        ]

        for tip in tips:
            tips_layout.addWidget(QLabel(tip))

        tips_group.setLayout(tips_layout)
        right_layout.addWidget(tips_group)

        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        right_panel.setMaximumWidth(300)

        # Добавляем панели
        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel, 1)
        main_layout.addWidget(right_panel)

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
        """Обработка выбора даты"""
        date_str = date.toString("yyyy-MM-dd")
        self.selected_date_label.setText(f"Выбрана: {date.toString('dd.MM.yyyy')}")
        self.update_interviews_for_date(date_str)

    def update_interviews_for_date(self, date_str):
        """Обновление списка собеседований для выбранной даты"""
        self.interviews_table.setRowCount(0)

        interviews = self.interviews.get(date_str, [])
        interviews.sort(key=lambda x: x.get('time', ''))

        for row, interview in enumerate(interviews):
            self.interviews_table.insertRow(row)

            # ID (скрытая колонка)
            id_item = QTableWidgetItem(interview.get('id', ''))
            self.interviews_table.setItem(row, 0, id_item)

            # Время
            self.interviews_table.setItem(row, 1, QTableWidgetItem(interview.get('time', '')))

            # Кандидат
            self.interviews_table.setItem(row, 2, QTableWidgetItem(interview.get('candidate', '')))

            # Интервьюер
            interviewer = interview.get('interviewer', 'Не назначен')
            interviewer_item = QTableWidgetItem(interviewer)
            if interviewer == self.user_data.get('username'):
                interviewer_item.setForeground(QColor(styles.S7_GREEN))  # ❗ Теперь QColor определен
            self.interviews_table.setItem(row, 3, interviewer_item)

            # Комментарий
            comment_item = QTableWidgetItem(interview.get('comment', ''))
            comment_item.setToolTip(interview.get('comment', ''))
            self.interviews_table.setItem(row, 4, comment_item)

            # Статус
            status = interview.get('status', 'scheduled')
            status_text = {
                'scheduled': 'Запланировано',
                'rescheduled': 'Перенесено',
                'cancelled': 'Отменено',
                'completed': 'Завершено'
            }.get(status, status)

            status_item = QTableWidgetItem(status_text)
            if status == 'scheduled':
                status_item.setForeground(QColor(styles.S7_GREEN))
            elif status == 'rescheduled':
                status_item.setForeground(QColor("#FFA500"))
            elif status == 'cancelled':
                status_item.setForeground(QColor(styles.S7_RED))
            self.interviews_table.setItem(row, 5, status_item)

            # Кнопки действий
            widget = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(2)

            # Кнопка деталей
            details_btn = QPushButton("👁️")
            details_btn.setFixedSize(25, 25)
            details_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {styles.S7_LIGHT_GREEN};
                    color: white;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {styles.S7_GREEN};
                }}
            """)
            details_btn.clicked.connect(lambda checked, i=interview: self.show_interview_details(i))
            details_btn.setToolTip("Просмотреть детали")
            btn_layout.addWidget(details_btn)

            # Кнопка переноса
            reschedule_btn = QPushButton("🔄")
            reschedule_btn.setFixedSize(25, 25)
            reschedule_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFA500;
                    color: white;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: #FF8C00;
                }}
            """)
            reschedule_btn.clicked.connect(lambda checked, i=interview: self.request_reschedule(i))
            reschedule_btn.setToolTip("Запросить перенос")
            btn_layout.addWidget(reschedule_btn)

            # Кнопка удаления (только для своих)
            if interview.get('interviewer') == self.user_data.get('username') or self.user_data.get('role') == 'admin':
                delete_btn = QPushButton("✖")
                delete_btn.setFixedSize(25, 25)
                delete_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {styles.S7_RED};
                        color: white;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        background-color: {styles.S7_RED};
                        opacity: 0.8;
                    }}
                """)
                delete_btn.clicked.connect(lambda checked, d=date_str, i=interview: self.delete_interview(d, i))
                delete_btn.setToolTip("Удалить")
                btn_layout.addWidget(delete_btn)

            btn_layout.addStretch()
            widget.setLayout(btn_layout)
            self.interviews_table.setCellWidget(row, 6, widget)

    def update_interviews_list(self):
        """Обновление всего списка"""
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.update_interviews_for_date(date_str)

        # Получаем статистику от ИИ
        stats = self.ai_agent.get_schedule_statistics()

        stats_text = f"""
📈 ОБЩАЯ СТАТИСТИКА
━━━━━━━━━━━━━━━━
Всего собеседований: {stats.get('total_interviews', 0)}
Дней с собесед.: {stats.get('days_with_interviews', 0)}
Ср. в день: {stats.get('average_per_day', 0):.1f}

📊 СТАТУСЫ:
• Запланировано: {stats.get('status_stats', {}).get('scheduled', 0)}
• Перенесено: {stats.get('status_stats', {}).get('rescheduled', 0)}

📬 СООБЩЕНИЯ:
• Непрочитанных: {stats.get('message_stats', {}).get('unread', 0)}
• Ожидают: {stats.get('message_stats', {}).get('pending_requests', 0)}
"""
        self.stats_label.setText(stats_text)

    def add_interview(self):
        """Добавление нового собеседования"""
        date = self.calendar.selectedDate()
        date_str = date.toString("yyyy-MM-dd")

        candidate = self.candidate_input.text().strip()
        if not candidate:
            QMessageBox.warning(self, "Предупреждение", "Введите имя кандидата")
            return

        interviewer = self.interviewer_input.text().strip()
        if not interviewer:
            interviewer = self.user_data.get('username')

        time_str = self.time_input.time().toString("HH:mm")
        comment = self.comment_input.toPlainText().strip()

        # Проверка на конфликт
        existing = self.interviews.get(date_str, [])
        if any(i.get('time') == time_str for i in existing):
            QMessageBox.warning(self, "Конфликт", f"Время {time_str} уже занято!")
            return

        # Создаем ID для собеседования
        interview_id = f"int_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        new_interview = {
            'id': interview_id,
            'candidate': candidate,
            'time': time_str,
            'date': date_str,
            'comment': comment,
            'interviewer': interviewer,
            'created_by': self.user_data.get('username'),
            'created_at': datetime.now().isoformat(),
            'status': 'scheduled'
        }

        if date_str not in self.interviews:
            self.interviews[date_str] = []

        self.interviews[date_str].append(new_interview)
        self.save_interviews()

        # Отправляем уведомление
        self.ai_agent.send_interview_notification(new_interview)

        # Очистка формы
        self.candidate_input.clear()
        self.comment_input.clear()

        # Обновление
        self.update_interviews_for_date(date_str)
        self.update_interviews_list()

        QMessageBox.information(
            self,
            "Успех",
            f"✅ Собеседование добавлено\n📧 Уведомление отправлено"
        )

    def auto_schedule(self):
        """Автоматическое назначение времени для оффера"""
        candidate = self.candidate_input.text().strip()
        if not candidate:
            QMessageBox.warning(self, "Ошибка", "Введите имя кандидата")
            return

        # Простые данные кандидата
        candidate_data = {
            "name": candidate,
            "title": "Кандидат",
            "city": "Москва"
        }

        # Запрашиваем авто-назначение
        result = self.ai_agent.auto_schedule_offer(
            candidate,
            candidate_data,
            self.user_data.get('username')
        )

        if result.get('success'):
            # Автоматически добавляем в расписание
            reply = QMessageBox.question(
                self,
                "Рекомендация ИИ",
                f"🤖 ИИ рекомендует:\n\n"
                f"📅 Дата: {result['date']}\n"
                f"⏰ Время: {result['time']}\n"
                f"📊 Уверенность: {result.get('confidence', 0)}%\n"
                f"💬 Причина: {result.get('reason', '')}\n\n"
                f"Добавить в расписание?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Создаем собеседование
                interview_id = f"int_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                new_interview = {
                    'id': interview_id,
                    'candidate': candidate,
                    'time': result['time'],
                    'date': result['date'],
                    'comment': f"Авто-назначение от ИИ. {result.get('reason', '')}",
                    'interviewer': self.user_data.get('username'),
                    'created_by': 'AI Agent',
                    'created_at': datetime.now().isoformat(),
                    'status': 'scheduled'
                }

                if result['date'] not in self.interviews:
                    self.interviews[result['date']] = []

                self.interviews[result['date']].append(new_interview)
                self.save_interviews()
                self.ai_agent.send_interview_notification(new_interview)

                QMessageBox.information(self, "Успех", "Собеседование добавлено!")
                self.update_interviews_list()
        else:
            QMessageBox.warning(
                self,
                "Нет свободных слотов",
                f"Не удалось найти время.\n"
                f"Предложения: {', '.join(result.get('suggestions', []))}"
            )

    def request_reschedule(self, interview):
        """Запрос на перенос собеседования"""
        dialog = RescheduleRequestDialog(interview, self.ai_agent, self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_interviews_list()
            QMessageBox.information(
                self,
                "Запрос отправлен",
                "Запрос на перенос отправлен другой стороне"
            )

    def delete_interview(self, date_str, interview):
        """Удаление собеседования"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить собеседование с {interview.get('candidate')}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if date_str in self.interviews:
                self.interviews[date_str] = [
                    i for i in self.interviews[date_str]
                    if i.get('id') != interview.get('id')
                ]

                if not self.interviews[date_str]:
                    del self.interviews[date_str]

                self.save_interviews()
                self.update_interviews_for_date(date_str)
                self.update_interviews_list()

    def show_interview_details(self, interview):
        """Показывает детали собеседования"""
        details = f"""
📋 ДЕТАЛИ СОБЕСЕДОВАНИЯ
━━━━━━━━━━━━━━━━━━━━━━━

👤 Кандидат: {interview.get('candidate')}
👥 Интервьюер: {interview.get('interviewer', 'Не назначен')}
📅 Дата: {interview.get('date')}
⏰ Время: {interview.get('time')}
📊 Статус: {interview.get('status', 'scheduled')}

📝 Комментарий:
{interview.get('comment', 'Нет комментария')}

🆔 ID: {interview.get('id')}
📅 Создано: {interview.get('created_at', '')[:10]}
"""
        if 'previous_date' in interview:
            details += f"\n🔄 Перенесено с: {interview.get('previous_date')} {interview.get('previous_time')}"

        QMessageBox.information(self, "Детали собеседования", details)

    def analyze_conflicts(self):
        """Анализирует конфликты в расписании"""
        conflicts = []

        for date, interviews in self.interviews.items():
            times = {}
            for i in interviews:
                time = i.get('time')
                if time in times:
                    conflicts.append({
                        'date': date,
                        'time': time,
                        'interviews': [times[time], i]
                    })
                else:
                    times[time] = i

        if conflicts:
            text = "🔍 НАЙДЕНЫ КОНФЛИКТЫ:\n\n"
            for c in conflicts:
                text += f"📅 {c['date']} в {c['time']}:\n"
                for i in c['interviews']:
                    text += f"  • {i.get('candidate')} ({i.get('interviewer')})\n"
                text += "\n"
            QMessageBox.warning(self, "Конфликты", text)
        else:
            QMessageBox.information(self, "Анализ", "✅ Конфликтов не найдено")


class RescheduleRequestDialog(QDialog):
    """Диалог запроса на перенос"""

    def __init__(self, interview, ai_agent, parent=None):
        super().__init__(parent)
        self.interview = interview
        self.ai_agent = ai_agent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Запрос на перенос собеседования")
        self.setGeometry(300, 300, 400, 300)
        self.setStyleSheet(styles.MAIN_STYLE)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Информация
        info_group = QGroupBox("Собеседование")
        info_layout = QFormLayout()

        info_layout.addRow("Кандидат:", QLabel(self.interview.get('candidate', '')))
        info_layout.addRow("Текущее время:", QLabel(f"{self.interview.get('date')} {self.interview.get('time')}"))

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Причина
        reason_group = QGroupBox("Причина переноса")
        reason_layout = QVBoxLayout()

        self.reason_combo = QComboBox()
        self.reason_combo.addItems([
            "Кандидат просит перенести",
            "Интервьюер недоступен",
            "Технические проблемы",
            "Конфликт в расписании",
            "Другое"
        ])
        reason_layout.addWidget(self.reason_combo)

        self.reason_text = QTextEdit()
        self.reason_text.setPlaceholderText("Подробное описание...")
        self.reason_text.setMaximumHeight(80)
        reason_layout.addWidget(self.reason_text)

        reason_group.setLayout(reason_layout)
        layout.addWidget(reason_group)

        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.send_request)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def send_request(self):
        """Отправляет запрос на перенос"""
        reason = self.reason_combo.currentText()
        if self.reason_text.toPlainText().strip():
            reason += f": {self.reason_text.toPlainText().strip()}"

        result = self.ai_agent.request_reschedule(
            self.interview.get('id'),
            reason,
            "Кандидат"  # или интервьюер
        )

        if result.get('success'):
            QMessageBox.information(self, "Успех", result.get('message'))
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", result.get('message'))