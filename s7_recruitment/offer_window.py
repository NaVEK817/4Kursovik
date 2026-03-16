# -*- coding: utf-8 -*-
"""
Окно создания оффера для кандидата
"""
import json
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, 
                             QMessageBox, QFileDialog, QGroupBox, QDateEdit,
                             QSpinBox, QFormLayout)
from PyQt5.QtCore import Qt, QDate
import styles

class OfferWindow(QWidget):
    """Окно создания оффера для кандидата"""
    
    def __init__(self, vacancy, candidate):
        super().__init__()
        self.vacancy = vacancy
        self.candidate = candidate
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("S7 Recruitment - Создание оффера")
        self.setGeometry(200, 200, 600, 700)
        self.setStyleSheet(styles.MAIN_STYLE)
        
        # Основной layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        header_label = QLabel("📄 Создание оффера для кандидата")
        header_label.setObjectName("headerLabel")
        layout.addWidget(header_label)
        
        # Информация о кандидате (только для просмотра)
        candidate_group = QGroupBox("Информация о кандидате")
        candidate_layout = QFormLayout()
        
        # Формируем ФИО
        full_name = f"{self.candidate.get('last_name', '')} {self.candidate.get('first_name', '')} {self.candidate.get('middle_name', '')}".strip()
        if not full_name:
            full_name = "Кандидат"
        
        name_label = QLabel(full_name)
        name_label.setStyleSheet(f"font-weight: bold; color: {styles.S7_GREEN};")
        candidate_layout.addRow("👤 ФИО:", name_label)
        
        # Желаемая должность
        desired_title = self.candidate.get('title', 'Не указана')
        candidate_layout.addRow("💼 Желаемая должность:", QLabel(desired_title))
        
        # Город
        city = self.candidate.get('area', 'Не указан')
        candidate_layout.addRow("🏙️ Город:", QLabel(city))
        
        # Опыт
        total_years = 0
        experience = self.candidate.get('experience', [])
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
        
        candidate_layout.addRow("📊 Опыт работы:", QLabel(f"{total_years} лет"))
        
        candidate_group.setLayout(candidate_layout)
        layout.addWidget(candidate_group)
        
        # Информация о вакансии (только для просмотра)
        vacancy_group = QGroupBox("Информация о вакансии")
        vacancy_layout = QFormLayout()
        
        vacancy_title = QLabel(self.vacancy.get('title', 'Не указана'))
        vacancy_title.setStyleSheet(f"font-weight: bold; color: {styles.S7_GREEN};")
        vacancy_layout.addRow("📋 Вакансия:", vacancy_title)
        
        vacancy_city = self.vacancy.get('area', 'Не указан')
        vacancy_layout.addRow("🏙️ Город работы:", QLabel(vacancy_city))
        
        vacancy_salary = self.vacancy.get('salary', 'Не указана')
        vacancy_layout.addRow("💰 Зарплата:", QLabel(vacancy_salary))
        
        vacancy_schedule = self.vacancy.get('schedule', 'Не указан')
        vacancy_layout.addRow("⏰ График:", QLabel(vacancy_schedule))
        
        vacancy_group.setLayout(vacancy_layout)
        layout.addWidget(vacancy_group)
        
        # Параметры оффера
        offer_group = QGroupBox("Параметры оффера")
        offer_layout = QFormLayout()
        
        # Дата начала работы
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(14))  # Через 2 недели
        self.start_date.setCalendarPopup(True)
        offer_layout.addRow("📅 Предполагаемая дата выхода:", self.start_date)
        
        # Испытательный срок
        self.probation_period = QSpinBox()
        self.probation_period.setRange(1, 6)
        self.probation_period.setValue(3)
        self.probation_period.setSuffix(" месяца")
        offer_layout.addRow("⏱️ Испытательный срок:", self.probation_period)
        
        # Зарплатное предложение
        self.salary_offer = QLineEdit()
        self.salary_offer.setPlaceholderText("Например: 80 000 руб.")
        # Пытаемся извлечь зарплату из вакансии
        vacancy_salary = self.vacancy.get('salary', '')
        if vacancy_salary:
            self.salary_offer.setText(vacancy_salary)
        offer_layout.addRow("💰 Предложение по зарплате:", self.salary_offer)
        
        offer_group.setLayout(offer_layout)
        layout.addWidget(offer_group)
        
        # Дополнительные условия
        conditions_group = QGroupBox("Дополнительные условия")
        conditions_layout = QVBoxLayout()
        
        self.conditions_text = QTextEdit()
        self.conditions_text.setMaximumHeight(100)
        self.conditions_text.setPlaceholderText("ДМС, бонусы, дополнительные льготы...")
        conditions_layout.addWidget(self.conditions_text)
        
        conditions_group.setLayout(conditions_layout)
        layout.addWidget(conditions_group)
        
        # Комментарий
        comment_group = QGroupBox("Комментарий для кандидата")
        comment_layout = QVBoxLayout()
        
        self.comment_text = QTextEdit()
        self.comment_text.setMaximumHeight(80)
        self.comment_text.setPlaceholderText("Персональное обращение к кандидату...")
        comment_layout.addWidget(self.comment_text)
        
        comment_group.setLayout(comment_layout)
        layout.addWidget(comment_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("📄 Создать оффер")
        self.create_btn.clicked.connect(self.create_offer)
        self.create_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.create_btn)
        
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("✖ Отмена")
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def create_offer(self):
        """Создание документа-оффера"""
        # Проверка заполнения
        if not self.salary_offer.text().strip():
            QMessageBox.warning(self, "Предупреждение", "Укажите зарплатное предложение")
            return
        
        # Формируем ФИО кандидата
        full_name = f"{self.candidate.get('last_name', '')} {self.candidate.get('first_name', '')} {self.candidate.get('middle_name', '')}".strip()
        if not full_name:
            full_name = "Кандидат"
        
        # Выбор места сохранения
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить оффер",
            f"Оффер_{full_name}_{self.vacancy.get('title', '')[:30]}.docx",
            "Word Documents (*.docx)"
        )
        
        if not filename:
            return
        
        try:
            # Создание документа
            doc = Document()
            
            # Установка стилей
            style = doc.styles['Normal']
            style.font.name = 'Calibri'
            style.font.size = Pt(11)
            
            # Заголовок
            title = doc.add_heading('ПРЕДЛОЖЕНИЕ О РАБОТЕ (JOB OFFER)', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            title.runs[0].font.color.rgb = RGBColor(0, 166, 81)  # S7 Green
            
            doc.add_paragraph()
            
            # Дата
            date_para = doc.add_paragraph(f'г. Москва, {datetime.now().strftime("%d.%m.%Y")}')
            date_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            
            doc.add_paragraph()
            
            # Обращение
            doc.add_paragraph(f'Уважаемый(ая) {full_name}!')
            doc.add_paragraph()
            
            # Основной текст
            doc.add_paragraph(
                'Мы рады предложить Вам присоединиться к команде S7 Airlines в качестве '
                f'**{self.vacancy.get("title", "сотрудника")}**.'
            )
            doc.add_paragraph()
            
            # Условия работы
            doc.add_heading('Условия работы:', level=1)
            
            conditions_table = doc.add_table(rows=4, cols=2)
            conditions_table.style = 'Light Grid Accent 1'
            
            # Заполняем таблицу
            cells = conditions_table.rows[0].cells
            cells[0].text = 'Должность'
            cells[0].paragraphs[0].runs[0].font.bold = True
            cells[1].text = self.vacancy.get('title', 'Не указана')
            
            cells = conditions_table.rows[1].cells
            cells[0].text = 'Место работы'
            cells[0].paragraphs[0].runs[0].font.bold = True
            cells[1].text = self.vacancy.get('area', 'Не указано')
            
            cells = conditions_table.rows[2].cells
            cells[0].text = 'График работы'
            cells[0].paragraphs[0].runs[0].font.bold = True
            cells[1].text = self.vacancy.get('schedule', 'Не указан')
            
            cells = conditions_table.rows[3].cells
            cells[0].text = 'Предполагаемая дата выхода'
            cells[0].paragraphs[0].runs[0].font.bold = True
            cells[1].text = self.start_date.date().toString("dd.MM.yyyy")
            
            doc.add_paragraph()
            
            # Компенсация
            doc.add_heading('Компенсационный пакет:', level=1)
            
            salary_text = f'• Ежемесячная заработная плата: {self.salary_offer.text()} до вычета НДФЛ'
            doc.add_paragraph(salary_text, style='List Bullet')
            
            probation_text = f'• Испытательный срок: {self.probation_period.value()} месяца'
            doc.add_paragraph(probation_text, style='List Bullet')
            
            # Дополнительные условия
            conditions = self.conditions_text.toPlainText().strip()
            if conditions:
                doc.add_paragraph()
                doc.add_heading('Дополнительные льготы и преимущества:', level=1)
                for line in conditions.split('\n'):
                    if line.strip():
                        doc.add_paragraph(f'• {line.strip()}', style='List Bullet')
            
            # Стандартные условия S7
            doc.add_paragraph()
            doc.add_heading('Стандартные условия для сотрудников S7:', level=1)
            doc.add_paragraph('• ДМС после испытательного срока (диагностика, лечение, стоматология со скидкой до 75%)', style='List Bullet')
            doc.add_paragraph('• Корпоративные тарифы на авиабилеты для Вас и членов семьи', style='List Bullet')
            doc.add_paragraph('• Программа корпоративных скидок PrimeZone (скидки до 80% у 1500+ партнеров)', style='List Bullet')
            doc.add_paragraph('• Программа психологической, финансовой и юридической поддержки "Понимаю"', style='List Bullet')
            doc.add_paragraph('• Программа здорового образа жизни S7 Impulse (бесплатные тренировки)', style='List Bullet')
            
            # Комментарий
            comment = self.comment_text.toPlainText().strip()
            if comment:
                doc.add_paragraph()
                doc.add_heading('Дополнительно:', level=1)
                doc.add_paragraph(comment)
            
            doc.add_paragraph()
            doc.add_paragraph()
            
            # Подпись
            doc.add_paragraph('С уважением,')
            doc.add_paragraph('Команда S7 Recruitment')
            doc.add_paragraph()
            doc.add_paragraph('______________________          ______________________')
            doc.add_paragraph('      (подпись)                              (дата)')
            
            # Сохранение документа
            doc.save(filename)
            
            QMessageBox.information(
                self, 
                "Успех", 
                f"Оффер успешно создан и сохранен:\n{filename}\n\n"
                "Не забудьте отправить его кандидату и обсудить детали."
            )
            
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать оффер: {str(e)}")