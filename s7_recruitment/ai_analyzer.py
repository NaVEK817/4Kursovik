# -*- coding: utf-8 -*-
"""
Модуль для AI-анализа кандидатов с использованием локальной Ollama модели.
Улучшенная версия с приоритизацией соответствия вакансии.
"""
import json
import requests
import re
from typing import Dict, List, Any, Optional

class OllamaCandidateAnalyzer:
    """
    Класс для анализа кандидатов через локальную модель Ollama.
    Улучшенная версия с более точным анализом соответствия вакансии.
    """
    
    # Веса для разных критериев (сумма = 100)
    WEIGHTS = {
        'experience': 35,  # Опыт работы - самый важный
        'skills': 30,      # Навыки - очень важны
        'education': 15,   # Образование
        'location': 10,    # Локация
        'schedule': 5,     # График работы
        'salary': 5        # Зарплатные ожидания
    }
    
    def __init__(self, model_name: str = "yandexgpt5:latest", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"

    def _extract_salary_range(self, salary_str: str) -> tuple:
        """Извлекает минимальную и максимальную зарплату из строки."""
        if not salary_str or salary_str == 'Не указаны':
            return (None, None)
        
        # Парсим строки типа "от 50000 RUR" или "65000" или "от 85000 до 100000 RUR"
        numbers = re.findall(r'\d+', str(salary_str))
        if not numbers:
            return (None, None)
        
        if len(numbers) == 1:
            return (int(numbers[0]), int(numbers[0]))
        else:
            return (int(numbers[0]), int(numbers[1]))

    def _calculate_base_score(self, vacancy: Dict, candidate: Dict) -> Dict[str, Any]:
        """
        Рассчитывает базовый рейтинг на основе объективных критериев.
        Возвращает словарь с оценками и комментариями.
        """
        base_scores = {}
        comments = {}
        
        # 1. Оценка опыта (базовая: 30-100)
        exp_score = 30
        exp_comment = "Базовый уровень"
        
        candidate_exp = candidate.get('experience', [])
        total_years = 0
        relevant_exp = False
        
        if isinstance(candidate_exp, list):
            for exp in candidate_exp:
                if isinstance(exp, dict):
                    # Расчет лет
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
                        years = end_year - start_year
                        total_years += years
                        
                        # Проверка релевантности (по ключевым словам в должности и описании)
                        position = exp.get('position', '').lower()
                        description = exp.get('description', '').lower()
                        vacancy_title = vacancy.get('title', '').lower()
                        
                        # Ключевые слова из вакансии
                        keywords = re.findall(r'\w+', vacancy_title)
                        for keyword in keywords:
                            if len(keyword) > 3 and (keyword in position or keyword in description):
                                relevant_exp = True
                                break
        
        # Оценка на основе лет опыта
        required_exp = vacancy.get('experience', '').lower()
        if 'нет опыта' in required_exp:
            if total_years >= 0:
                exp_score = 70
                exp_comment = f"Опыт {total_years} лет (подходит для начинающих)"
        elif 'от 1 года' in required_exp or '1-3' in required_exp:
            if total_years >= 1:
                exp_score = min(70 + total_years * 5, 95)
                exp_comment = f"Опыт {total_years} лет (соответствует требованиям)"
            else:
                exp_score = 40
                exp_comment = f"Опыт {total_years} лет (меньше требуемого)"
        elif 'от 3 до 6' in required_exp or '3-6' in required_exp:
            if total_years >= 3:
                exp_score = min(70 + (total_years - 3) * 5, 95)
                exp_comment = f"Опыт {total_years} лет (соответствует требованиям)"
            else:
                exp_score = 35
                exp_comment = f"Опыт {total_years} лет (меньше требуемого)"
        elif 'более 6' in required_exp:
            if total_years >= 6:
                exp_score = 90
                exp_comment = f"Опыт {total_years} лет (большой опыт)"
            else:
                exp_score = 45
                exp_comment = f"Опыт {total_years} лет (меньше требуемого)"
        
        # Бонус за релевантный опыт
        if relevant_exp:
            exp_score = min(exp_score + 15, 100)
            exp_comment += " + релевантный опыт"
        
        base_scores['experience'] = exp_score
        comments['experience'] = exp_comment
        
        # 2. Оценка навыков (базовая: 30-100)
        skills_score = 30
        skills_comment = "Базовый уровень"
        
        candidate_skills = candidate.get('skills', [])
        if isinstance(candidate_skills, list):
            # Простая оценка по количеству навыков
            if len(candidate_skills) >= 5:
                skills_score = 70
                skills_comment = f"{len(candidate_skills)} навыков (хороший набор)"
            elif len(candidate_skills) >= 3:
                skills_score = 55
                skills_comment = f"{len(candidate_skills)} навыков (достаточно)"
            elif len(candidate_skills) > 0:
                skills_score = 40
                skills_comment = f"{len(candidate_skills)} навыков (базовый набор)"
        elif isinstance(candidate_skills, str) and candidate_skills:
            skills_score = 45
            skills_comment = "Навыки указаны строкой"
        
        base_scores['skills'] = skills_score
        comments['skills'] = skills_comment
        
        # 3. Оценка образования (базовая: 30-100)
        edu_score = 30
        edu_comment = "Базовый уровень"
        
        education = candidate.get('education', {})
        if isinstance(education, dict):
            level = education.get('level', '').lower()
            if 'высшее' in level:
                edu_score = 70
                edu_comment = "Высшее образование"
            elif 'среднее профессиональное' in level:
                edu_score = 55
                edu_comment = "Среднее профессиональное образование"
            
            # Бонус за релевантную специализацию
            spec = education.get('specialization', '').lower()
            vacancy_title = vacancy.get('title', '').lower()
            if spec and any(word in spec for word in vacancy_title.split() if len(word) > 3):
                edu_score = min(edu_score + 15, 100)
                edu_comment += " (релевантная специализация)"
        
        base_scores['education'] = edu_score
        comments['education'] = edu_comment
        
        # 4. Оценка локации (базовая: 30-100)
        loc_score = 30
        loc_comment = "Базовый уровень"
        
        candidate_city = candidate.get('area', '').lower()
        vacancy_city = vacancy.get('area', '').lower()
        
        if candidate_city and vacancy_city:
            if candidate_city == vacancy_city:
                loc_score = 100
                loc_comment = f"Город совпадает: {candidate_city}"
            elif vacancy_city in candidate_city or candidate_city in vacancy_city:
                loc_score = 80
                loc_comment = f"Города связаны: {candidate_city} -> {vacancy_city}"
            else:
                loc_score = 40
                loc_comment = f"Город отличается: {candidate_city} (требуется {vacancy_city})"
        
        base_scores['location'] = loc_score
        comments['location'] = loc_comment
        
        # 5. Оценка графика (базовая: 30-100)
        schedule_score = 50
        schedule_comment = "График не проверен"
        
        candidate_schedule = candidate.get('schedule', '').lower()
        vacancy_schedule = vacancy.get('schedule', '').lower()
        
        if candidate_schedule and vacancy_schedule:
            if candidate_schedule == vacancy_schedule:
                schedule_score = 100
                schedule_comment = f"График совпадает: {candidate_schedule}"
            elif 'сменный' in vacancy_schedule and ('сменный' in candidate_schedule or 'гибкий' in candidate_schedule):
                schedule_score = 80
                schedule_comment = "График совместим (сменный)"
            else:
                schedule_score = 50
                schedule_comment = f"График отличается: {candidate_schedule} (требуется {vacancy_schedule})"
        
        base_scores['schedule'] = schedule_score
        comments['schedule'] = schedule_comment
        
        # 6. Оценка зарплаты (базовая: 30-100)
        salary_score = 50
        salary_comment = "Зарплата не проверена"
        
        candidate_salary = candidate.get('salary', '')
        vacancy_salary = vacancy.get('salary', '')
        
        if candidate_salary and candidate_salary != 'Не указаны':
            cand_min, cand_max = self._extract_salary_range(str(candidate_salary))
            vac_min, vac_max = self._extract_salary_range(vacancy_salary)
            
            if cand_min and vac_min:
                if vac_max and cand_min <= vac_max:
                    if cand_min >= vac_min:
                        salary_score = 90
                        salary_comment = f"Ожидания {cand_min} вписываются в вилку {vac_min}-{vac_max}"
                    else:
                        salary_score = 70
                        salary_comment = f"Ожидания {cand_min} ниже вилки {vac_min}-{vac_max}"
                elif not vac_max and cand_min <= vac_min * 1.2:  # Если нет верхней границы
                    salary_score = 80
                    salary_comment = f"Ожидания {cand_min} приемлемы"
                else:
                    salary_score = 40
                    salary_comment = f"Ожидания {cand_min} выше предложения"
        
        base_scores['salary'] = salary_score
        comments['salary'] = salary_comment
        
        return {
            'scores': base_scores,
            'comments': comments,
            'total_years': total_years
        }

    def _generate_prompt(self, vacancy: Dict, candidate: Dict, base_data: Dict) -> str:
        """
        Формирует подробный промпт для модели на основе данных вакансии и кандидата.
        Включает базовые оценки как отправную точку.
        """
        # Извлекаем требования вакансии
        requirements = vacancy.get('requirements', '') or vacancy.get('description', '')
        responsibilities = vacancy.get('responsibilities', '')
        
        # --- Обработка опыта кандидата ---
        experience_str = ""
        candidate_exp = candidate.get('experience', [])
        
        if isinstance(candidate_exp, list):
            for exp in candidate_exp:
                if isinstance(exp, dict):
                    company = exp.get('company', 'Компания не указана')
                    position = exp.get('position', 'Позиция не указана')
                    start = exp.get('start', '')
                    end = exp.get('end', 'н.в.')
                    description = exp.get('description', 'Описание отсутствует')
                    
                    exp_desc = f"- {position} в {company} ({start} - {end})\n  {description}"
                    experience_str += exp_desc + "\n"
        elif isinstance(candidate_exp, str):
            experience_str = f"- {candidate_exp}\n"
        
        # --- Обработка навыков ---
        skills = candidate.get('skills', [])
        skills_str = ""
        if isinstance(skills, list):
            skills_str = ', '.join(skills) if skills else 'Не указаны'
        else:
            skills_str = str(skills) if skills else 'Не указаны'
        
        # --- Обработка образования ---
        education = candidate.get('education', {})
        education_str = ""
        if isinstance(education, dict):
            edu_level = education.get('level', 'Не указано')
            edu_spec = education.get('specialization', 'Не указано')
            edu_institution = education.get('institution', '')
            edu_year = education.get('year', '')
            education_str = f"{edu_level} - {edu_spec}\n{edu_institution}, {edu_year}".strip()
        
        # Формируем базовые оценки для промпта
        base_scores = base_data['scores']
        base_comments = base_data['comments']

        prompt = f"""Ты — опытный HR-аналитик и рекрутер в авиакомпании S7. Твоя задача — провести глубокий анализ кандидата на предмет его соответствия вакансии.

=== ВАКАНСИЯ ===
Название: {vacancy.get('title', 'Не указано')}
ID вакансии: {vacancy.get('id', 'Не указан')}
Город: {vacancy.get('area', 'Не указан')}
Требуемый опыт: {vacancy.get('experience', 'Не указан')}
График работы: {vacancy.get('schedule', 'Не указан')}
Занятость: {vacancy.get('employment', 'Не указана')}
Зарплата: {vacancy.get('salary', 'Не указана')}

ТРЕБОВАНИЯ:
{requirements}

ОБЯЗАННОСТИ:
{responsibilities}

=== КАНДИДАТ ===
ФИО: {candidate.get('last_name', '')} {candidate.get('first_name', '')} {candidate.get('middle_name', '')}
Желаемая должность: {candidate.get('title', 'Не указано')}
Город: {candidate.get('area', 'Не указан')}
Общий опыт работы: {base_data['total_years']} лет

ОПЫТ РАБОТЫ:
{experience_str if experience_str else 'Нет опыта'}

НАВЫКИ:
{skills_str}

ОБРАЗОВАНИЕ:
{education_str}

Зарплатные ожидания: {candidate.get('salary', 'Не указаны')}
Желаемый график: {candidate.get('schedule', 'Не указан')}
Желаемая занятость: {candidate.get('employment', 'Не указана')}

=== БАЗОВЫЕ ОЦЕНКИ (для ориентира) ===
Опыт: {base_scores['experience']}% - {base_comments['experience']}
Навыки: {base_scores['skills']}% - {base_comments['skills']}
Образование: {base_scores['education']}% - {base_comments['education']}
Локация: {base_scores['location']}% - {base_comments['location']}
График: {base_scores['schedule']}% - {base_comments['schedule']}
Зарплата: {base_scores['salary']}% - {base_comments['salary']}

=== ИНСТРУКЦИИ ПО ОЦЕНКЕ ===
Проведи анализ по следующим критериям. Для каждого критерия дай оценку от 30 до 100 (МИНИМУМ 30, МАКСИМУМ 100) и пояснение.
Базовые оценки уже рассчитаны - используй их как отправную точку, но можешь корректировать на основе более глубокого анализа.

1. ОПЫТ (вес 35%): Оцени релевантность и продолжительность опыта
2. НАВЫКИ (вес 30%): Оцени соответствие навыков требованиям
3. ОБРАЗОВАНИЕ (вес 15%): Оцени соответствие образования
4. ЛОКАЦИЯ (вес 10%): Оцени соответствие города
5. ГРАФИК (вес 5%): Оцени соответствие графика
6. ЗАРПЛАТА (вес 5%): Оцени соответствие зарплатных ожиданий

ВАЖНО: Все оценки ДОЛЖНЫ быть между 30 и 100. Никаких оценок ниже 30!

Верни ТОЛЬКО JSON-объект без пояснений в следующем формате:
{{
  "score": <итоговая оценка 30-100>,
  "weighted_score": <оценка с учетом весов>,
  "summary": "<краткое резюме анализа 2-3 предложения>",
  "criterion_scores": {{
    "experience": {{"score": 30-100, "comment": "<пояснение>"}},
    "skills": {{"score": 30-100, "comment": "<пояснение>"}},
    "education": {{"score": 30-100, "comment": "<пояснение>"}},
    "location": {{"score": 30-100, "comment": "<пояснение>"}},
    "schedule": {{"score": 30-100, "comment": "<пояснение>"}},
    "salary": {{"score": 30-100, "comment": "<пояснение>"}}
  }},
  "details": {{
    "experience_match": "<детальный анализ опыта>",
    "skills_match": "<детальный анализ навыков>",
    "education_match": "<анализ образования>",
    "location_match": "<анализ локации>",
    "salary_match": "<анализ зарплаты>",
    "schedule_employment_match": "<анализ графика>",
    "strengths": ["<сильная сторона 1>", "<сильная сторона 2>", ...],
    "weaknesses": ["<слабая сторона 1>", "<слабая сторона 2>", ...],
    "key_findings": ["<ключевой вывод 1>", "<ключевой вывод 2>", ...],
    "recommendation": "<Да/Сомнительно/Нет>",
    "recommendation_reason": "<почему такая рекомендация>"
  }}
}}
"""
        return prompt

    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Пытается извлечь JSON из ответа LLM."""
        response_text = response_text.strip()
        
        # Очищаем ответ от возможных markdown-маркеров
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Ищем JSON объект
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
        
        return None

    def _calculate_weighted_score(self, criterion_scores: Dict) -> int:
        """Вычисляет взвешенную оценку на основе весов критериев."""
        total = 0
        for criterion, score_data in criterion_scores.items():
            if isinstance(score_data, dict):
                score = score_data.get('score', 30)
            else:
                score = score_data
            # Убеждаемся, что оценка не ниже 30
            score = max(30, min(100, score))
            weight = self.WEIGHTS.get(criterion, 0)
            total += score * weight
        return int(total / 100)

    def analyze(self, vacancy: Dict, candidate: Dict) -> Dict[str, Any]:
        """Основной метод анализа с улучшенной обработкой."""
        
        # Базовая проверка на валидность кандидата
        if not candidate or not isinstance(candidate, dict):
            return self._create_error_result("Некорректные данные кандидата")

        # Сначала рассчитываем базовые оценки
        base_data = self._calculate_base_score(vacancy, candidate)
        
        # Рассчитываем базовый взвешенный рейтинг (как запасной вариант)
        base_weighted = 0
        for criterion, score in base_data['scores'].items():
            base_weighted += score * self.WEIGHTS.get(criterion, 0)
        base_weighted = int(base_weighted / 100)
        base_weighted = max(30, base_weighted)  # Минимум 30%

        # Генерируем промпт с базовыми оценками
        prompt = self._generate_prompt(vacancy, candidate, base_data)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 2048,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = requests.post(self.generate_url, json=payload, timeout=180)
                response.raise_for_status()
                result = response.json()
                llm_response = result.get('response', '')

                parsed_result = self._parse_llm_response(llm_response)
                if parsed_result:
                    # Убеждаемся, что все оценки не ниже 30
                    if 'criterion_scores' in parsed_result:
                        for criterion in parsed_result['criterion_scores']:
                            if isinstance(parsed_result['criterion_scores'][criterion], dict):
                                score = parsed_result['criterion_scores'][criterion].get('score', 30)
                                parsed_result['criterion_scores'][criterion]['score'] = max(30, min(100, score))
                            else:
                                parsed_result['criterion_scores'][criterion] = max(30, min(100, parsed_result['criterion_scores'][criterion]))
                    
                    # Вычисляем взвешенную оценку
                    if 'criterion_scores' in parsed_result:
                        parsed_result['weighted_score'] = self._calculate_weighted_score(
                            parsed_result['criterion_scores']
                        )
                    
                    # Убеждаемся, что финальный score не ниже 30
                    if 'score' in parsed_result:
                        parsed_result['score'] = max(30, min(100, parsed_result['score']))
                    elif 'weighted_score' in parsed_result:
                        parsed_result['score'] = parsed_result['weighted_score']
                    
                    return parsed_result
                    
            except Exception as e:
                print(f"Попытка {attempt + 1} не удалась: {e}")
                continue
        
        # Если все попытки не удались, возвращаем базовый рейтинг
        return {
            "score": base_weighted,
            "weighted_score": base_weighted,
            "summary": f"Анализ выполнен по базовым критериям. Общий опыт: {base_data['total_years']} лет.",
            "criterion_scores": {
                criterion: {"score": score, "comment": base_data['comments'][criterion]}
                for criterion, score in base_data['scores'].items()
            },
            "details": {
                "experience_match": base_data['comments']['experience'],
                "skills_match": base_data['comments']['skills'],
                "education_match": base_data['comments']['education'],
                "location_match": base_data['comments']['location'],
                "salary_match": base_data['comments']['salary'],
                "schedule_employment_match": base_data['comments']['schedule'],
                "strengths": [f"Опыт работы {base_data['total_years']} лет"] if base_data['total_years'] > 0 else [],
                "weaknesses": [],
                "key_findings": [f"Базовый рейтинг: {base_weighted}%"],
                "recommendation": "Сомнительно" if base_weighted < 50 else "Да" if base_weighted >= 70 else "Сомнительно",
                "recommendation_reason": f"Оценка на основе базовых критериев"
            }
        }

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Создает структурированный ответ с ошибкой, но с базовым рейтингом 30%."""
        return {
            "score": 30,
            "weighted_score": 30,
            "summary": f"Базовый анализ (ошибка: {error_message})",
            "criterion_scores": {
                "experience": {"score": 30, "comment": "Оценка по умолчанию"},
                "skills": {"score": 30, "comment": "Оценка по умолчанию"},
                "education": {"score": 30, "comment": "Оценка по умолчанию"},
                "location": {"score": 30, "comment": "Оценка по умолчанию"},
                "schedule": {"score": 30, "comment": "Оценка по умолчанию"},
                "salary": {"score": 30, "comment": "Оценка по умолчанию"}
            },
            "details": {
                "experience_match": "Базовый анализ",
                "skills_match": "Базовый анализ",
                "education_match": "Базовый анализ",
                "location_match": "Базовый анализ",
                "salary_match": "Базовый анализ",
                "schedule_employment_match": "Базовый анализ",
                "strengths": [],
                "weaknesses": [error_message],
                "key_findings": ["Базовый рейтинг: 30%"],
                "recommendation": "Сомнительно",
                "recommendation_reason": error_message
            }
        }