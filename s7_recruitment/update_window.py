# -*- coding: utf-8 -*-
"""
Окно обновления данных через парсер
"""
import subprocess
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import styles

class ParserThread(QThread):
    """Поток для выполнения парсера"""
    
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        """Запуск парсера в отдельном потоке"""
        try:
            self.output_signal.emit("🚀 Запуск парсера вакансий...\n")
            
            # Получение пути к текущей директории
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parser_path = os.path.join(current_dir, 'parcer.py')
            
            self.output_signal.emit(f"📁 Директория: {current_dir}\n")
            self.output_signal.emit(f"📄 Файл парсера: {parser_path}\n")
            
            # Проверка существования файла
            if not os.path.exists(parser_path):
                self.output_signal.emit("❌ Ошибка: Файл parcer.py не найден!\n")
                self.finished_signal.emit(False, "Файл парсера не найден")
                return
            
            # Проверка наличия Links.txt
            links_path = os.path.join(current_dir, 'Links.txt')
            if not os.path.exists(links_path):
                self.output_signal.emit("⚠️ Файл Links.txt не найден. Будут использованы существующие данные.\n")
            
            # Запуск парсера
            self.output_signal.emit("⏳ Выполнение парсера...\n")
            
            # Запуск процесса
            process = subprocess.Popen(
                [sys.executable, parser_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                cwd=current_dir
            )
            
            # Чтение вывода
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_signal.emit(output)
            
            # Получение ошибок
            stderr = process.stderr.read()
            if stderr:
                self.output_signal.emit(f"\n⚠️ Ошибки:\n{stderr}\n")
            
            # Проверка результата
            if process.returncode == 0:
                self.output_signal.emit("\n✅ Парсер успешно завершил работу!\n")
                
                # Проверка создания выходного файла
                output_file = os.path.join(current_dir, 'output_file.json')
                if os.path.exists(output_file):
                    self.output_signal.emit(f"📊 Данные сохранены в: {output_file}\n")
                    self.finished_signal.emit(True, "Данные успешно обновлены")
                else:
                    self.output_signal.emit("⚠️ Выходной файл не создан\n")
                    self.finished_signal.emit(False, "Выходной файл не создан")
            else:
                self.output_signal.emit(f"\n❌ Ошибка выполнения парсера (код: {process.returncode})\n")
                self.finished_signal.emit(False, f"Ошибка выполнения (код: {process.returncode})")
                
        except Exception as e:
            self.output_signal.emit(f"\n❌ Критическая ошибка: {str(e)}\n")
            self.finished_signal.emit(False, str(e))

class UpdateWindow(QWidget):
    """Окно обновления данных"""
    
    update_completed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.parser_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("S7 Recruitment - Обновление данных")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        # Основной layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header_label = QLabel("🔄 Обновление данных вакансий")
        header_label.setObjectName("headerLabel")
        layout.addWidget(header_label)
        
        # Информационная группа
        info_group = QGroupBox("Информация")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "Парсер загружает актуальные вакансии с hh.ru.\n"
            "Ссылки на работодателей берутся из файла Links.txt.\n"
            "Результат сохраняется в output_file.json."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {styles.S7_GRAY}; padding: 5px;")
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Запустить обновление")
        self.start_btn.clicked.connect(self.start_update)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.start_btn)
        
        self.clear_btn = QPushButton("🧹 Очистить вывод")
        self.clear_btn.clicked.connect(self.clear_output)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setEnabled(False)
        buttons_layout.addWidget(self.clear_btn)
        
        buttons_layout.addStretch()
        
        self.close_btn = QPushButton("✖ Закрыть")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Область вывода
        output_group = QGroupBox("Вывод парсера")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFontFamily("Consolas, Monospace")
        self.output_text.setStyleSheet(f"""
            background-color: {styles.S7_BLACK};
            color: {styles.S7_LIGHT_GREEN};
            font-size: 12px;
            border: none;
        """)
        output_layout.addWidget(self.output_text)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        self.setLayout(layout)
        
    def start_update(self):
        """Запуск обновления данных"""
        self.start_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)
        self.output_text.clear()
        
        self.output_text.append(f"🕒 {datetime.now().strftime('%H:%M:%S')} - Начало обновления\n")
        
        # Создание и запуск потока парсера
        self.parser_thread = ParserThread()
        self.parser_thread.output_signal.connect(self.append_output)
        self.parser_thread.finished_signal.connect(self.update_finished)
        self.parser_thread.start()
    
    def append_output(self, text):
        """Добавление текста в вывод"""
        self.output_text.insertPlainText(text)
        # Прокрутка вниз
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.End)
        self.output_text.setTextCursor(cursor)
    
    def update_finished(self, success, message):
        """Обработка завершения обновления"""
        self.start_btn.setEnabled(True)
        
        if success:
            self.output_text.append(f"\n✅ {datetime.now().strftime('%H:%M:%S')} - Обновление завершено")
            QMessageBox.information(self, "Успех", "Данные успешно обновлены!")
            self.update_completed.emit()
        else:
            self.output_text.append(f"\n❌ {datetime.now().strftime('%H:%M:%S')} - Ошибка: {message}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить данные:\n{message}")
    
    def clear_output(self):
        """Очистка области вывода"""
        self.output_text.clear()
        self.clear_btn.setEnabled(False)