# -*- coding: utf-8 -*-
"""
Главный файл приложения S7 Recruitment
"""
import sys
import os
import json
import bcrypt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from auth_window import AuthWindow
from main_window import MainWindow

class S7RecruitmentApp:
    """Основной класс приложения"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        self.app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        
        self.auth_window = None
        self.main_window = None
        
        # Проверка наличия файла с пользователями
        self.ensure_default_user()
        
    def ensure_default_user(self):
        """Создание пользователя по умолчанию, если файл не существует"""
        if not os.path.exists('users.json'):
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(b'admin', salt)
            
            default_users = {
                "admin": {
                    "username": "admin",
                    "password_hash": password_hash.decode('utf-8'),
                    "role": "admin"
                }
            }
            
            try:
                with open('users.json', 'w', encoding='utf-8') as f:
                    json.dump(default_users, f, ensure_ascii=False, indent=2)
                print("Создан пользователь по умолчанию: admin / admin")
            except Exception as e:
                print(f"Ошибка при создании users.json: {e}")
        
    def run(self):
        """Запуск приложения"""
        # Создание окна авторизации
        self.auth_window = AuthWindow()
        self.auth_window.login_successful.connect(self.on_login_success)
        self.auth_window.show()
        
        return self.app.exec_()
    
    def on_login_success(self, user_data):
        """Обработка успешной авторизации"""
        self.main_window = MainWindow(user_data)
        self.main_window.show()

def main():
    """Точка входа в приложение"""
    # Установка кодировки для Windows
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('s7.recruitment.app')
    
    app = S7RecruitmentApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()