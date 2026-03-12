# -*- coding: utf-8 -*-
"""
Главный файл приложения S7 Recruitment
"""
import sys
import os
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