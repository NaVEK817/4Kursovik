# -*- coding: utf-8 -*-
"""
Модуль для AI-анализа кандидатов с использованием локальной Ollama модели.
"""
import json
import requests
from typing import Dict, List, Any, Optional

class OllamaCandidateAnalyzer:
    """
    Класс для анализа кандидатов через локальную модель Ollama.
    """
    def __init__(self, model_name: str = "yandexgpt5:latest", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"

    def _generate_prompt(self, vacancy: Dict, candidate: Dict) -> str:
        """
        Формирует подробный промпт для модели на основе данных вакансии и кандидата.
        Поддерживает оба формата кандидатов:
        1. Плоский формат из generate_demo_candidates (experience, skills как строки)
        2. Вложенный формат из resume_file.json (experience как список словарей)
        """
        # Извлекаем требования вакансии или используем пустую строку
        requirements = vacancy.get('requirements', '') or vacancy.get('description', '')
        responsibilities = vacancy.get('responsibilities', '')
    
        # --- Универсальная обработка опыта кандидата ---
        experience_str = ""
        candidate_exp = candidate.get('experience', [])
    
        # Проверяем тип данных в поле experience
        if isinstance(candidate_exp, list):
            # Формат из resume_file.json (список словарей)
            for exp in candidate_exp:
                if isinstance(exp, dict):
                    company = exp.get('company', 'Компания не указана')
                    position = exp.get('position', 'Позиция не указана')
                    start = exp.get('start', '')
                    end = exp.get('end', 'н.в.')
                    description = exp.get('description', 'Описание отсутствует')
                
                    exp_desc = f"- {position} в {company} ({start} - {end})\n  {description}"
                    experience_str += exp_desc + "\n"
                elif isinstance(exp, str):
                    # На случай, если в списке оказались строки
                    experience_str += f"- {exp}\n"
        elif isinstance(candidate_exp, str):
            # Формат из generate_demo_candidates (опыт как строка)
            if candidate_exp and candidate_exp != 'Не указан':
                experience_str = f"- {candidate_exp}\n"
            else:
                experience_str = "Нет опыта\n"
        else:
            experience_str = "Информация об опыте отсутствует\n"
    
        # Если опыт пустой, добавляем заглушку
        if not experience_str.strip():
            experience_str = "Нет опыта\n"
    
        # --- Универсальная обработка навыков кандидата ---
        skills = candidate.get('skills', [])
        skills_str = ""
    
        if isinstance(skills, list):
            # Формат из resume_file.json (список строк)
            if skills:
                skills_str = ', '.join(skills)
            else:
                skills_str = 'Не указаны'
        elif isinstance(skills, str):
            # Формат из generate_demo_candidates (строка)
            skills_str = skills if skills else 'Не указаны'
        else:
            skills_str = str(skills) if skills else 'Не указаны'
    
        # --- Обработка имени кандидата (разные форматы) ---
        if 'first_name' in candidate and 'last_name' in candidate:
            # Формат из resume_file.json
            full_name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')} {candidate.get('middle_name', '')}".strip()
        else:
            # Формат из generate_demo_candidates (поле 'name')
            full_name = candidate.get('name', 'Не указано')
    
        # --- Обработка образования ---
        education_str = ""
        education = candidate.get('education', {})
        if isinstance(education, dict):
            # Формат из resume_file.json
            edu_level = education.get('level', 'Не указано')
            edu_spec = education.get('specialization', 'Не указано')
            edu_institution = education.get('institution', '')
            education_str = f"{edu_level} - {edu_spec} {edu_institution}".strip()
        else:
            # В плоском формате образование может отсутствовать
            education_str = "Не указано"
    
        # --- Обработка зарплатных ожиданий ---
        salary_exp = candidate.get('salary', 'Не указаны')
        if salary_exp and isinstance(salary_exp, (int, float)):
            salary_exp = f"{salary_exp} руб."
    
        # --- Обработка города ---
        city = candidate.get('area') or candidate.get('city', 'Не указан')
    
        # --- Обработка желаемого графика и занятости ---
        schedule = candidate.get('schedule', 'Не указан')
        employment = candidate.get('employment', 'Не указана')
    
    # Формируем промпт
        prompt = f"""
Ты — опытный HR-аналитик и рекрутер. Твоя задача — проанализировать кандидата на предмет его соответствия вакансии и дать объективную оценку.

**Вакансия:**
Название: {vacancy.get('title', 'Не указано')}
Город: {vacancy.get('area', 'Не указан')}
Требования: {requirements}
Обязанности: {responsibilities}
Зарплата: {vacancy.get('salary', 'Не указана')}
График: {vacancy.get('schedule', 'Не указан')}
Занятость: {vacancy.get('employment', 'Не указана')}
Опыт (требуемый): {vacancy.get('experience', 'Не указан')}

**Кандидат:**
Имя: {full_name}
Желаемая должность: {candidate.get('title', candidate.get('vacancy_title', 'Не указано'))}
Город: {city}
Опыт работы:
{experience_str}
Навыки: {skills_str}
Образование: {education_str}
Зарплатные ожидания: {salary_exp}
Желаемый график: {schedule}
Желаемая занятость: {employment}

Проанализируй кандидата по следующим критериям и верни ТОЛЬКО JSON-объект без каких-либо пояснений.
Поля JSON:
- "score" (int): Итоговая оценка соответствия от 0 до 100.
- "summary" (str): Краткое текстовое резюме анализа (2-3 предложения), почему кандидат подходит или не подходит.
- "details" (dict): Объект с детальной оценкой по ключевым параметрам:
    - "experience_match" (str): Анализ соответствия опыта кандидата требованиям вакансии (учти продолжительность и релевантность опыта).
    - "skills_match" (str): Анализ соответствия навыков (какие ключевые навыки совпадают, каких не хватает).
    - "location_match" (str): Анализ по городу и готовности к переезду/командировкам (если город различается, укажи это).
    - "salary_match" (str): Анализ соответствия зарплатных ожиданий (сравни с вилкой в вакансии).
    - "schedule_employment_match" (str): Анализ по графику и занятости.
    - "strengths" (list[str]): Список сильных сторон кандидата для этой вакансии.
    - "weaknesses" (list[str]): Список слабых сторон или несоответствий.
    - "recommendation" (str): Итоговая рекомендация ("Да", "Сомнительно", "Нет").

Пример ответа:
{{
  "score": 85,
  "summary": "Кандидат отлично подходит. Опыт работы в аэропорту полностью соответствует требованиям, навыки коммуникации на высоком уровне.",
  "details": {{
    "experience_match": "Опыт работы в аэропорту 2 года, что соответствует требованию 'Нет опыта' или 'От 1 года'.",
    "skills_match": "Навыки: коммуникабельность, работа с возражениями, английский язык. Полное соответствие.",
    "location_match": "Кандидат проживает в Уфе, готов к работе в аэропорту.",
    "salary_match": "Ожидания (45000) соответствуют предлагаемой зарплате (50000).",
    "schedule_employment_match": "Желаемый сменный график совпадает с условиями вакансии.",
    "strengths": ["Релевантный опыт в авиации", "Знание английского языка", "Опыт работы с пассажирами"],
    "weaknesses": [],
    "recommendation": "Да"
  }}
}}
"""
        return prompt

    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Пытается извлечь JSON из ответа LLM.
        """
        response_text = response_text.strip()
        # Ищем JSON в ответе, если модель добавила лишний текст
        try:
            # Попытка найти JSON между ```json и ``` или просто фигурные скобки
            if response_text.startswith("```json"):
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end != 0:
                    json_str = response_text[start:end]
                    return json.loads(json_str)
            else:
                return json.loads(response_text)
        except json.JSONDecodeError:
            # Если не удалось распарсить, пробуем найти JSON вручную
            try:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end != 0:
                    json_str = response_text[start:end]
                    return json.loads(json_str)
            except:
                pass
        return None

    def analyze(self, vacancy: Dict, candidate: Dict) -> Dict[str, Any]:
        """
        Основной метод анализа. Отправляет запрос в Ollama и возвращает результат.
        С повторными попытками при ошибках.
        """
        prompt = self._generate_prompt(vacancy, candidate)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 1024
            }
        }

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(self.generate_url, json=payload, timeout=120)
                response.raise_for_status()
                result = response.json()
                llm_response = result.get('response', '')

                parsed_result = self._parse_llm_response(llm_response)
                if parsed_result:
                    return parsed_result
                elif attempt < max_retries:
                    # Если не удалось распарсить, пробуем еще раз
                    continue
                else:
                    return self._create_error_result("Не удалось распарсить ответ модели")

            except requests.exceptions.ConnectionError:
                return self._create_error_result("Не удалось подключиться к Ollama. Убедитесь, что она запущена.")
            except Exception as e:
                if attempt < max_retries:
                    continue
                return self._create_error_result(f"Ошибка: {str(e)}")
    
        return self._create_error_result("Неизвестная ошибка")

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Создает структурированный ответ с ошибкой"""
        return {
            "score": 0,
            "summary": f"Ошибка анализа: {error_message}",
            "details": {
                "experience_match": "Ошибка",
                "skills_match": "Ошибка",
                "location_match": "Ошибка", 
                "salary_match": "Ошибка",
                "schedule_employment_match": "Ошибка",
                "strengths": [],
                "weaknesses": [error_message],
                "recommendation": "Нет"
            }
        }

# Для тестирования модуля, если нужно
if __name__ == '__main__':
    # Здесь можно добавить тестовый код
    pass