# -*- coding: utf-8 -*-
"""
Окно сообщений и уведомлений для пользователей
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem,
                             QGroupBox, QMessageBox, QTextEdit, QDialog,
                             QFormLayout, QComboBox, QDateEdit, QTimeEdit,
                             QDialogButtonBox)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QColor  # ❗ ВАЖНО: добавить этот импорт
import styles
from datetime import datetime


class MessagesWindow(QWidget):
    """Окно сообщений и уведомлений"""

    def __init__(self, user_data, schedule_manager):
        super().__init__()
        self.user_data = user_data
        self.manager = schedule_manager
        self.init_ui()
        self.load_messages()

    def init_ui(self):
        self.setWindowTitle("S7 Recruitment - Сообщения и уведомления")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet(styles.MAIN_STYLE)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Заголовок
        header = QLabel("📬 Сообщения и уведомления")
        header.setObjectName("headerLabel")
        layout.addWidget(header)

        # Статистика сообщений
        stats_group = QGroupBox("📊 Статистика")
        stats_layout = QHBoxLayout()

        self.stats_label = QLabel("Загрузка...")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()

        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.load_messages)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        stats_layout.addWidget(refresh_btn)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Список сообщений
        messages_group = QGroupBox("Сообщения")
        messages_layout = QVBoxLayout()

        self.messages_list = QListWidget()
        self.messages_list.itemClicked.connect(self.on_message_clicked)
        self.messages_list.itemDoubleClicked.connect(self.on_message_double_clicked)
        messages_layout.addWidget(self.messages_list)

        messages_group.setLayout(messages_layout)
        layout.addWidget(messages_group)

        # Кнопка действий
        buttons_layout = QHBoxLayout()

        self.mark_read_btn = QPushButton("✓ Отметить как прочитанное")
        self.mark_read_btn.clicked.connect(self.mark_selected_read)
        self.mark_read_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.mark_read_btn)

        self.respond_btn = QPushButton("✏️ Ответить на запрос")
        self.respond_btn.clicked.connect(self.respond_to_request)
        self.respond_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.respond_btn)

        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def load_messages(self):
        """Загружает сообщения пользователя"""
        self.messages_list.clear()

        messages = self.manager.get_user_messages(self.user_data.get('username'))

        # Обновляем статистику
        stats = self.manager.get_schedule_statistics()
        msg_stats = stats.get('message_stats', {})

        self.stats_label.setText(
            f"Всего сообщений: {msg_stats.get('total', 0)} | "
            f"Непрочитанных: {msg_stats.get('unread', 0)} | "
            f"Ожидают ответа: {msg_stats.get('pending_requests', 0)}"
        )

        for msg in messages:
            self.add_message_to_list(msg)

    def add_message_to_list(self, message: dict):
        """Добавляет сообщение в список"""
        msg_type = message.get('type', 'notification')
        created = message.get('created_at', '')[:10]
        read = message.get('read', False)

        if msg_type == 'notification':
            prefix = "📢 Уведомление"
            color = styles.S7_GREEN
        elif msg_type == 'reschedule_request':
            prefix = "🔄 Запрос на перенос"
            color = "#FFA500"
        else:
            prefix = "📝 Сообщение"
            color = styles.S7_BLACK

        if not read:
            prefix = "🔴 " + prefix
            color = styles.S7_RED

        # Формируем текст сообщения
        if msg_type == 'notification':
            text = f"{prefix} - {created}\n{message.get('message', '')[:100]}..."
        elif msg_type == 'reschedule_request':
            interview = message.get('interview_data', {})
            text = (f"{prefix} - {created}\n"
                    f"От: {message.get('requested_by')}\n"
                    f"Причина: {message.get('reason', '')[:100]}...")
        else:
            text = f"{prefix} - {created}"

        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, message)
        item.setForeground(QColor(color))

        # ИСПРАВЛЕНИЕ: setSizeHint ожидает QSize, а не int
        from PyQt5.QtCore import QSize
        current_size = item.sizeHint()
        item.setSizeHint(QSize(current_size.width(), current_size.height() + 30))

        self.messages_list.addItem(item)

    def on_message_clicked(self, item):
        """Обработка клика по сообщению"""
        message = item.data(Qt.UserRole)

        # Показываем полный текст
        if message.get('type') == 'reschedule_request':
            self.show_request_details(message)

    def on_message_double_clicked(self, item):
        """Обработка двойного клика"""
        message = item.data(Qt.UserRole)

        if message.get('type') == 'reschedule_request' and message.get('status') == 'pending':
            # Открываем диалог подтверждения переноса
            self.open_reschedule_dialog(message)

    def show_request_details(self, message):
        """Показывает детали запроса"""
        interview = message.get('interview_data', {})
        alternatives = message.get('suggested_alternatives', [])

        alt_text = "\n".join([f"  • {a['date']} в {a['time']}" for a in alternatives[:3]])

        details = f"""
📋 ДЕТАЛИ ЗАПРОСА НА ПЕРЕНОС
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Запросил: {message.get('requested_by')}
📅 Дата запроса: {message.get('created_at', '')[:10]}
📊 Статус: {message.get('status', 'pending')}

📝 Причина:
{message.get('reason', 'Не указана')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Текущее собеседование:
   Дата: {interview.get('date')}
   Время: {interview.get('time')}
   Кандидат: {interview.get('candidate')}
   Интервьюер: {interview.get('interviewer')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Предлагаемые альтернативы:
{alt_text if alt_text else "  Нет предложений"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Действия:
   • Двойной клик для подтверждения переноса
   • Кнопка "Ответить" для отказа
"""
        QMessageBox.information(self, "Детали запроса", details)

    def open_reschedule_dialog(self, message):
        """Открывает диалог подтверждения переноса"""
        dialog = RescheduleConfirmDialog(message, self.manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_messages()

    def mark_selected_read(self):
        """Отмечает выбранное сообщение как прочитанное"""
        current = self.messages_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Ошибка", "Выберите сообщение")
            return

        message = current.data(Qt.UserRole)
        self.manager.mark_message_read(message.get('id'))
        self.load_messages()

    def respond_to_request(self):
        """Отвечает на запрос"""
        current = self.messages_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Ошибка", "Выберите запрос")
            return

        message = current.data(Qt.UserRole)
        if message.get('type') != 'reschedule_request':
            QMessageBox.warning(self, "Ошибка", "Это не запрос на перенос")
            return

        self.open_reschedule_dialog(message)


class RescheduleConfirmDialog(QDialog):
    """Диалог подтверждения переноса"""

    def __init__(self, request, manager, parent=None):
        super().__init__(parent)
        self.request = request
        self.manager = manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Подтверждение переноса собеседования")
        self.setGeometry(300, 300, 500, 400)
        self.setStyleSheet(styles.MAIN_STYLE)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Информация о запросе
        info_group = QGroupBox("Информация о запросе")
        info_layout = QFormLayout()

        interview = self.request.get('interview_data', {})
        info_layout.addRow("Кандидат:", QLabel(interview.get('candidate', '')))
        info_layout.addRow("Текущая дата:", QLabel(f"{interview.get('date')} {interview.get('time')}"))
        info_layout.addRow("Причина:", QLabel(self.request.get('reason', '')))

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Выбор новой даты
        date_group = QGroupBox("Выберите новое время")
        date_layout = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate().addDays(1))
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumDate(QDate.currentDate())
        date_layout.addRow("Новая дата:", self.date_edit)

        self.time_combo = QComboBox()
        self.time_combo.addItems(["09:00", "10:00", "11:00", "12:00", "13:00",
                                  "14:00", "15:00", "16:00", "17:00", "18:00"])
        date_layout.addRow("Новое время:", self.time_combo)

        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.confirm_btn = QPushButton("✅ Подтвердить перенос")
        self.confirm_btn.clicked.connect(self.confirm_reschedule)
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.confirm_btn)

        self.reject_btn = QPushButton("❌ Отклонить запрос")
        self.reject_btn.clicked.connect(self.reject_request)
        self.reject_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.reject_btn)

        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def confirm_reschedule(self):
        """Подтверждает перенос"""
        new_date = self.date_edit.date().toString("yyyy-MM-dd")
        new_time = self.time_combo.currentText()

        result = self.manager.confirm_reschedule(
            self.request.get('id'),
            new_date,
            new_time
        )

        if result.get('success'):
            QMessageBox.information(self, "Успех", result.get('message'))
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", result.get('message'))

    def reject_request(self):
        """Отклоняет запрос"""
        reply = QMessageBox.question(
            self,
            "Отклонение запроса",
            "Вы уверены, что хотите отклонить запрос на перенос?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Информация", "Запрос отклонен")
            self.reject()