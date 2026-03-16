# -*- coding: utf-8 -*-
"""
Генератор офферов с очисткой HTML тегов
"""
import re
import os
from datetime import datetime


class OfferGenerator:
    """Генератор офферов с очисткой HTML"""

    @staticmethod
    def clean_html(text):
        """Удаляет все HTML теги из текста"""
        if not text:
            return ""
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def generate_offer(candidate, vacancy, interview):
        """Генерирует текст оффера без HTML"""

        # Очищаем все поля от HTML
        candidate_name = OfferGenerator.clean_html(candidate)
        vacancy_title = OfferGenerator.clean_html(vacancy)

        offer = f"""
Уважаемый(ая) {candidate_name}!

Благодарим за интерес к вакансии "{vacancy_title}" в S7 Airlines.

Мы рады пригласить Вас на собеседование:

📅 Дата: {interview['date']}
⏰ Время: {interview['time']}
👥 Собеседующий: {interview['recruiter']}
📍 Место: {interview.get('place', 'Офис S7 Airlines')}

Пожалуйста, подтвердите Ваше участие ответным письмом.

С уважением,
Команда S7 Recruitment
"""
        return offer.strip()

    @staticmethod
    def save_offer(candidate_name, vacancy_title, interview):
        """Сохраняет оффер в файл"""
        os.makedirs('offers', exist_ok=True)

        # Очищаем имя для файла
        clean_name = re.sub(r'[^\w\s-]', '', candidate_name)
        clean_name = re.sub(r'[-\s]+', '_', clean_name)

        filename = f"offers/offer_{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"

        offer_text = OfferGenerator.generate_offer(candidate_name, vacancy_title, interview)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(offer_text)

        return filename