# -*- coding: utf-8 -*-
"""
Окно авторизации пользователей
"""
import json
import bcrypt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
import styles

class AuthWindow(QWidget):
    """Окно авторизации"""
    
    login_successful = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.users = self.load_users()
        self.init_ui()
        
    def load_users(self):
        """Загрузка пользователей из users.json"""
        try:
            with open('users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {}
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("S7 Recruitment - Авторизация")
        self.setFixedSize(400, 500)
        self.setStyleSheet(styles.AUTH_STYLE)
        
        # Основной layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Логотип (текстовый, так как нет изображения)
        logo_label = QLabel("S7 RECRUITMENT")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {styles.S7_GREEN};
            margin-bottom: 20px;
        """)
        layout.addWidget(logo_label)
        
        # Заголовок
        title_label = QLabel("Вход в систему")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; color: #666; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # Поле для имени пользователя
        layout.addWidget(QLabel("Имя пользователя:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя пользователя")
        layout.addWidget(self.username_input)
        
        # Поле для пароля
        layout.addWidget(QLabel("Пароль:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.check_credentials)
        layout.addWidget(self.password_input)
        
        layout.addStretch()
        
        # Кнопка входа
        self.login_button = QPushButton("ВОЙТИ")
        self.login_button.clicked.connect(self.check_credentials)
        self.login_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.login_button)
        
        # Информация для демо
        info_label = QLabel("Демо-доступ: пользователь '1', пароль '1'")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet(f"color: {styles.S7_GRAY}; font-size: 11px; margin-top: 10px;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
        
    def check_credentials(self):
        """Проверка учетных данных"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя и пароль")
            return
        
        user_data = self.users.get(username)
        
        if user_data:
            # Проверка пароля с использованием bcrypt
            try:
                if bcrypt.checkpw(password.encode('utf-8'), 
                                  user_data['password_hash'].encode('utf-8')):
                    self.login_successful.emit(user_data)
                    self.close()
                    return
            except:
                pass
        
        QMessageBox.warning(self, "Ошибка", "Неверное имя пользователя или пароль")
        self.password_input.clear()