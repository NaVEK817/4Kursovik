# -*- coding: utf-8 -*-
"""
Окно управления пользователями
"""
import json
import bcrypt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QLineEdit,
                             QComboBox, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt
import styles

class UserDialog(QDialog):
    """Диалог добавления/редактирования пользователя"""
    
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Добавление пользователя" if not self.user_data else "Редактирование пользователя")
        self.setFixedSize(400, 300)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # Имя пользователя
        self.username_input = QLineEdit()
        if self.user_data:
            self.username_input.setText(self.user_data.get('username', ''))
            self.username_input.setEnabled(False)
        form_layout.addRow("Имя пользователя:", self.username_input)
        
        # Пароль (только для нового пользователя)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        if not self.user_data:
            form_layout.addRow("Пароль:", self.password_input)
        
        # Подтверждение пароля
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        if not self.user_data:
            form_layout.addRow("Подтверждение:", self.confirm_input)
        
        # Роль
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        if self.user_data:
            role = self.user_data.get('role', 'user')
            index = self.role_combo.findText(role)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
        form_layout.addRow("Роль:", self.role_combo)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Получение данных из формы"""
        return {
            'username': self.username_input.text().strip(),
            'password': self.password_input.text(),
            'role': self.role_combo.currentText()
        }

class UsersWindow(QWidget):
    """Окно управления пользователями"""
    
    USERS_FILE = "users.json"
    
    def __init__(self):
        super().__init__()
        self.users = self.load_users()
        self.init_ui()
        self.update_table()
        
    def load_users(self):
        """Загрузка пользователей из файла"""
        try:
            with open(self.USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_users(self):
        """Сохранение пользователей в файл"""
        try:
            with open(self.USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить пользователей: {str(e)}")
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("S7 Recruitment - Управление пользователями")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Заголовок
        header_label = QLabel("👥 Управление пользователями")
        header_label.setObjectName("headerLabel")
        layout.addWidget(header_label)
        
        # Таблица пользователей
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Имя пользователя", "Роль", "Действия"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Кнопка добавления
        add_btn = QPushButton("➕ Добавить пользователя")
        add_btn.clicked.connect(self.add_user)
        add_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(add_btn)
        
        self.setLayout(layout)
    
    def update_table(self):
        """Обновление таблицы пользователей"""
        self.table.setRowCount(len(self.users))
        
        for row, (username, data) in enumerate(self.users.items()):
            # Имя пользователя
            self.table.setItem(row, 0, QTableWidgetItem(username))
            
            # Роль
            self.table.setItem(row, 1, QTableWidgetItem(data.get('role', 'user')))
            
            # Кнопки действий
            widget = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(5, 2, 5, 2)
            btn_layout.setSpacing(5)
            
            # Кнопка редактирования
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {styles.S7_LIGHT_GREEN};
                    color: white;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {styles.S7_GREEN};
                }}
            """)
            edit_btn.clicked.connect(lambda checked, u=username: self.edit_user(u))
            edit_btn.setCursor(Qt.PointingHandCursor)
            btn_layout.addWidget(edit_btn)
            
            # Кнопка удаления (не для текущего пользователя и не для admin)
            if username != 'admin':
                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(30, 30)
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
                delete_btn.clicked.connect(lambda checked, u=username: self.delete_user(u))
                delete_btn.setCursor(Qt.PointingHandCursor)
                btn_layout.addWidget(delete_btn)
            
            btn_layout.addStretch()
            widget.setLayout(btn_layout)
            self.table.setCellWidget(row, 2, widget)
    
    def add_user(self):
        """Добавление нового пользователя"""
        dialog = UserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            
            if not data['username']:
                QMessageBox.warning(self, "Ошибка", "Введите имя пользователя")
                return
            
            if data['username'] in self.users:
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким именем уже существует")
                return
            
            if not data['password']:
                QMessageBox.warning(self, "Ошибка", "Введите пароль")
                return
            
            # Хеширование пароля
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), salt)
            
            # Добавление пользователя
            self.users[data['username']] = {
                'username': data['username'],
                'password_hash': password_hash.decode('utf-8'),
                'role': data['role']
            }
            
            self.save_users()
            self.update_table()
            
            QMessageBox.information(self, "Успех", "Пользователь успешно добавлен")
    
    def edit_user(self, username):
        """Редактирование пользователя"""
        user_data = self.users.get(username, {})
        dialog = UserDialog(self, user_data)
        
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            
            # Обновление только роли
            self.users[username]['role'] = data['role']
            
            self.save_users()
            self.update_table()
            
            QMessageBox.information(self, "Успех", "Роль пользователя обновлена")
    
    def delete_user(self, username):
        """Удаление пользователя"""
        if username == 'admin':
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить администратора")
            return
        
        reply = QMessageBox.question(
            self, 
            "Подтверждение",
            f"Удалить пользователя {username}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.users[username]
            self.save_users()
            self.update_table()
            QMessageBox.information(self, "Успех", "Пользователь удален")