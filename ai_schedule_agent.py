# -*- coding: utf-8 -*-
"""
ИИ-агент для управления расписанием собеседований с использованием Ollama.
Анализирует занятость, предлагает оптимальные слоты и помогает с переносом.
"""
import json
import re
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import requests
from PyQt5.QtCore import QDate


class AIScheduleAgent:
    """
    ИИ-агент для интеллектуального управления расписанием собеседований.
    Использует локальную Ollama модель для анализа и рекомендаций.
    """

    def __init__(self, model_name: str = "yandexgpt5:latest", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"

    def analyze_schedule_conflict(self,
                                  existing_interviews: List[Dict],
                                  new_candidate: Dict,
                                  proposed_time: str,
                                  proposed_date: str) -> Dict[str, Any]:
        """
        Анализирует потенциальный конфликт в расписании и предлагает альтернативы.

        Args:
            existing_interviews: Список существующих собеседований на эту дату
            new_candidate: Данные нового кандидата
            proposed_time: Предлагаемое время (HH:MM)
            proposed_date: Предлагаемая дата (YYYY-MM-DD)

        Returns:
            Dict с анализом и рекомендациями
        """

        # Проверяем, занято ли время
        is_time_taken = any(
            interview.get('time') == proposed_time
            for interview in existing_interviews
        )

        if not is_time_taken:
            return {
                "has_conflict": False,
                "message": "Время свободно",
                "suggestions": []
            }

        # Находим конфликтующее собеседование
        conflicting = next(
            (i for i in existing_interviews if i.get('time') == proposed_time),
            None
        )

        # Анализируем занятость и ищем альтернативы
        prompt = self._generate_conflict_prompt(
            existing_interviews,
            new_candidate,
            conflicting,
            proposed_date
        )

        try:
            response = self._query_ollama(prompt)
            return self._parse_conflict_response(response)
        except Exception as e:
            # Запасной вариант с простыми альтернативами
            return self._generate_fallback_suggestions(
                existing_interviews,
                proposed_time,
                proposed_date
            )

    def suggest_best_time(self,
                          existing_interviews: List[Dict],
                          candidate: Dict,
                          vacancy: Dict,
                          preferred_dates: List[str] = None) -> Dict[str, Any]:
        """
        Предлагает лучшее время для собеседования на основе анализа.

        Args:
            existing_interviews: Все существующие собеседования
            candidate: Данные кандидата
            vacancy: Данные вакансии
            preferred_dates: Список предпочтительных дат (опционально)

        Returns:
            Dict с рекомендациями
        """

        # Анализируем загруженность по дням
        busy_days = self._analyze_busy_days(existing_interviews)

        # Если нет предпочтительных дат, предлагаем ближайшие 5 дней
        if not preferred_dates:
            preferred_dates = self._generate_next_dates(5)

        prompt = self._generate_suggestion_prompt(
            existing_interviews,
            candidate,
            vacancy,
            preferred_dates,
            busy_days
        )

        try:
            response = self._query_ollama(prompt)
            return self._parse_suggestion_response(response)
        except Exception as e:
            return self._generate_fallback_suggestions_by_dates(
                existing_interviews,
                preferred_dates
            )

    def analyze_reschedule_request(self,
                                   interview: Dict,
                                   reason: str,
                                   existing_interviews: List[Dict],
                                   candidate_data: Dict = None) -> Dict[str, Any]:
        """
        Анализирует запрос на перенос собеседования.

        Args:
            interview: Текущее собеседование
            reason: Причина переноса
            existing_interviews: Все существующие собеседования
            candidate_data: Данные кандидата (опционально)

        Returns:
            Dict с анализом и рекомендациями по переносу
        """

        prompt = self._generate_reschedule_prompt(
            interview,
            reason,
            existing_interviews,
            candidate_data
        )

        try:
            response = self._query_ollama(prompt)
            return self._parse_reschedule_response(response)
        except Exception as e:
            return {
                "can_reschedule": True,
                "analysis": "Возможен перенос. Рекомендуется выбрать новое время.",
                "priority": "medium",
                "suggested_actions": [
                    "Связаться с кандидатом для согласования нового времени",
                    "Проверить ближайшие свободные слоты"
                ],
                "considerations": [
                    "Учитывайте срочность вакансии",
                    "Согласуйте новое время с интервьюером"
                ]
            }

    def generate_interview_summary(self,
                                   interviews: List[Dict],
                                   period_start: str,
                                   period_end: str) -> str:
        """
        Генерирует аналитическую сводку по расписанию.

        Args:
            interviews: Список собеседований за период
            period_start: Начало периода (YYYY-MM-DD)
            period_end: Конец периода (YYYY-MM-DD)

        Returns:
            Текстовая сводка с анализом
        """

        if not interviews:
            return f"На период с {period_start} по {period_end} собеседований не запланировано."

        # Группируем по дням
        by_day = {}
        for interview in interviews:
            date = interview.get('date', '')
            if date not in by_day:
                by_day[date] = []
            by_day[date].append(interview)

        prompt = f"""
Ты - HR-аналитик. Проанализируй расписание собеседований и составь краткую аналитическую сводку.

Период: с {period_start} по {period_end}
Всего собеседований: {len(interviews)}
Дней с собеседованиями: {len(by_day)}

Распределение по дням:
{self._format_interviews_by_day(by_day)}

Составь краткую аналитическую сводку (3-5 предложений), которая включает:
1. Общую нагрузку на период
2. Наиболее загруженные дни
3. Рекомендации по планированию
"""

        try:
            response = self._query_ollama(prompt, max_tokens=300)
            return response.get('response', '').strip()
        except:
            # Запасной вариант
            return (f"За период запланировано {len(interviews)} собеседований. "
                    f"Наиболее загруженный день: {max(by_day.items(), key=lambda x: len(x[1]))[0]} "
                    f"с {len(max(by_day.items(), key=lambda x: len(x[1]))[1])} собеседованиями.")

    def _generate_conflict_prompt(self,
                                  existing: List[Dict],
                                  new_candidate: Dict,
                                  conflicting: Dict,
                                  date: str) -> str:
        """Генерирует промпт для анализа конфликта"""

        # Форматируем существующие собеседования
        existing_str = "\n".join([
            f"- {i.get('time')}: {i.get('candidate')} ({i.get('comment', 'Нет комментария')})"
            for i in sorted(existing, key=lambda x: x.get('time', ''))
        ])

        # Формируем имя нового кандидата
        if 'first_name' in new_candidate and 'last_name' in new_candidate:
            new_name = f"{new_candidate.get('last_name', '')} {new_candidate.get('first_name', '')}"
        else:
            new_name = new_candidate.get('name', new_candidate.get('title', 'Кандидат'))

        prompt = f"""
Ты - ИИ-ассистент по управлению расписанием собеседований. Проанализируй конфликт в расписании.

Дата: {date}
Конфликтующее время: {conflicting.get('time')}

Текущее расписание на эту дату:
{existing_str}

Новый кандидат: {new_name}
Желаемая должность: {new_candidate.get('title', 'Не указана')}

Конфликтующее собеседование:
- Кандидат: {conflicting.get('candidate')}
- Комментарий: {conflicting.get('comment', 'Нет')}
- Создатель: {conflicting.get('created_by', 'Неизвестно')}

Проанализируй ситуацию и предложи оптимальное решение. Верни ТОЛЬКО JSON без пояснений.

Поля JSON:
- "has_conflict" (bool): true
- "conflict_with" (str): Имя кандидата, с которым конфликт
- "severity" (str): "high", "medium", "low" (насколько критичен конфликт)
- "suggestions" (list[str]): Список предложений по разрешению конфликта
- "alternative_times" (list[str]): Список альтернативных времен (в формате HH:MM), которые свободны
- "recommendation" (str): Краткая рекомендация (1 предложение)
- "priority_message" (str): Сообщение для пользователя о приоритетности

Пример ответа:
{{
    "has_conflict": true,
    "conflict_with": "Иванов Иван",
    "severity": "medium",
    "suggestions": [
        "Предложить кандидату время на 30 минут позже",
        "Перенести конфликтующее собеседование на другой день",
        "Провести собеседование в другом формате"
    ],
    "alternative_times": ["10:30", "11:30", "14:00"],
    "recommendation": "Рекомендуется предложить кандидату время 11:30, так как оно свободно и удобно для большинства",
    "priority_message": "Конфликт средней важности. Есть несколько альтернативных слотов."
}}
"""
        return prompt

    def _generate_suggestion_prompt(self,
                                    existing: List[Dict],
                                    candidate: Dict,
                                    vacancy: Dict,
                                    preferred_dates: List[str],
                                    busy_days: Dict) -> str:
        """Генерирует промпт для предложения лучшего времени"""

        # Формируем имя кандидата
        if 'first_name' in candidate and 'last_name' in candidate:
            candidate_name = f"{candidate.get('last_name', '')} {candidate.get('first_name', '')}"
        else:
            candidate_name = candidate.get('name', candidate.get('title', 'Кандидат'))

        # Форматируем предпочтительные даты
        dates_str = "\n".join([f"- {d}" for d in preferred_dates])

        # Форматируем загруженность по дням
        busy_days_str = self._format_busy_days(busy_days)

        prompt = f"""
Ты - ИИ-ассистент по планированию собеседований. Предложи лучшее время для собеседования.

Данные кандидата:
- Имя: {candidate_name}
- Желаемая должность: {candidate.get('title', 'Не указана')}
- Город: {candidate.get('area', candidate.get('city', 'Не указан'))}
- Опыт: {self._format_candidate_experience(candidate)}
- Навыки: {self._format_candidate_skills(candidate)}

Вакансия:
- Название: {vacancy.get('title', 'Не указано')}
- Город: {vacancy.get('area', 'Не указан')}
- Срочность: {vacancy.get('priority', 'medium')}

Предпочтительные даты для собеседования:
{dates_str}

Текущая загруженность по дням:
{busy_days_str}

Проанализируй ситуацию и предложи оптимальное время для собеседования. Верни ТОЛЬКО JSON без пояснений.

Поля JSON:
- "recommended_date" (str): Рекомендуемая дата в формате YYYY-MM-DD
- "recommended_time" (str): Рекомендуемое время в формате HH:MM
- "alternative_options" (list[dict]): Список альтернативных вариантов (каждый с полями "date", "time", "reason")
- "reasoning" (str): Обоснование рекомендации
- "confidence" (int): Уверенность в рекомендации от 0 до 100
- "considerations" (list[str]): Список факторов, которые стоит учесть

Пример ответа:
{{
    "recommended_date": "2026-03-15",
    "recommended_time": "11:00",
    "alternative_options": [
        {{"date": "2026-03-15", "time": "14:30", "reason": "Хороший слот после обеда"}},
        {{"date": "2026-03-16", "time": "10:00", "reason": "Утро следующего дня"}}
    ],
    "reasoning": "Дата 2026-03-15 наименее загружена, время 11:00 оптимально для концентрации внимания",
    "confidence": 85,
    "considerations": [
        "Учитывайте часовой пояс кандидата",
        "Проверьте доступность интервьюера"
    ]
}}
"""
        return prompt

    def _generate_reschedule_prompt(self,
                                    interview: Dict,
                                    reason: str,
                                    existing: List[Dict],
                                    candidate_data: Dict = None) -> str:
        """Генерирует промпт для анализа переноса"""

        prompt = f"""
Ты - ИИ-ассистент по управлению расписанием. Проанализируй запрос на перенос собеседования.

Текущее собеседование:
- Кандидат: {interview.get('candidate')}
- Дата: {interview.get('date', 'Не указана')}
- Время: {interview.get('time', 'Не указано')}
- Комментарий: {interview.get('comment', 'Нет')}
- Создатель: {interview.get('created_by', 'Неизвестно')}

Причина переноса: {reason}

Всего собеседований запланировано: {len(existing)}

Проанализируй ситуацию и дай рекомендации по переносу. Верни ТОЛЬКО JSON без пояснений.

Поля JSON:
- "can_reschedule" (bool): Возможен ли перенос
- "analysis" (str): Краткий анализ ситуации
- "priority" (str): "high", "medium", "low" - приоритетность переноса
- "suggested_actions" (list[str]): Список рекомендуемых действий
- "considerations" (list[str]): Что нужно учесть при переносе
- "estimated_impact" (str): Оценка влияния переноса на процесс найма

Пример ответа:
{{
    "can_reschedule": true,
    "analysis": "Перенос возможен, так как до собеседования есть достаточно времени",
    "priority": "medium",
    "suggested_actions": [
        "Связаться с кандидатом для согласования нового времени",
        "Освободить текущий слот в расписании",
        "Уведомить интервьюера об изменении"
    ],
    "considerations": [
        "Учитывайте срочность вакансии",
        "Проверьте доступность ключевых участников",
        "Предложите кандидату альтернативные слоты"
    ],
    "estimated_impact": "Низкое влияние на процесс найма при своевременном переносе"
}}
"""
        return prompt

    def _query_ollama(self, prompt: str, max_tokens: int = 800) -> Dict:
        """Отправляет запрос к Ollama"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": max_tokens
            }
        }

        response = requests.post(self.generate_url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()

    def _parse_conflict_response(self, response: Dict) -> Dict[str, Any]:
        """Парсит ответ на запрос о конфликте"""
        response_text = response.get('response', '')

        try:
            # Пробуем найти JSON в ответе
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        # Запасной вариант
        return {
            "has_conflict": True,
            "conflict_with": "Неизвестно",
            "severity": "medium",
            "suggestions": ["Попробуйте другое время"],
            "alternative_times": [],
            "recommendation": "Проверьте доступные слоты",
            "priority_message": "Рекомендуется выбрать другое время"
        }

    def _parse_suggestion_response(self, response: Dict) -> Dict[str, Any]:
        """Парсит ответ на запрос о рекомендации времени"""
        response_text = response.get('response', '')

        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        return {
            "recommended_date": "",
            "recommended_time": "",
            "alternative_options": [],
            "reasoning": "Не удалось получить рекомендацию",
            "confidence": 0,
            "considerations": []
        }

    def _parse_reschedule_response(self, response: Dict) -> Dict[str, Any]:
        """Парсит ответ на запрос о переносе"""
        response_text = response.get('response', '')

        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        return {
            "can_reschedule": True,
            "analysis": "Возможен перенос",
            "priority": "medium",
            "suggested_actions": ["Согласуйте новое время с кандидатом"],
            "considerations": [],
            "estimated_impact": "Не определено"
        }

    def _analyze_busy_days(self, interviews: List[Dict]) -> Dict[str, int]:
        """Анализирует загруженность по дням"""
        busy_days = {}
        for interview in interviews:
            date = interview.get('date', '')
            if date:
                busy_days[date] = busy_days.get(date, 0) + 1
        return busy_days

    def _generate_next_dates(self, count: int) -> List[str]:
        """Генерирует список следующих дат"""
        dates = []
        today = date.today()
        for i in range(1, count + 1):
            next_date = today + timedelta(days=i)
            dates.append(next_date.strftime("%Y-%m-%d"))
        return dates

    def _generate_fallback_suggestions(self,
                                       existing: List[Dict],
                                       proposed_time: str,
                                       date: str) -> Dict[str, Any]:
        """Запасной вариант предложений при ошибке"""

        # Получаем все занятые времена
        taken_times = [i.get('time') for i in existing]

        # Предлагаем стандартные слоты
        standard_times = ["09:00", "10:00", "11:00", "12:00", "13:00",
                          "14:00", "15:00", "16:00", "17:00", "18:00"]

        alternatives = [t for t in standard_times if t not in taken_times][:3]

        return {
            "has_conflict": True,
            "conflict_with": "Другой кандидат",
            "severity": "medium",
            "suggestions": [
                "Выберите другое время из предложенных",
                "Попробуйте другой день",
                "Свяжитесь с конфликтующим кандидатом для переноса"
            ],
            "alternative_times": alternatives,
            "recommendation": f"Рекомендуется выбрать одно из свободных времен: {', '.join(alternatives)}",
            "priority_message": "Есть несколько альтернативных слотов"
        }

    def _generate_fallback_suggestions_by_dates(self,
                                                existing: List[Dict],
                                                preferred_dates: List[str]) -> Dict[str, Any]:
        """Запасной вариант рекомендаций по датам"""

        # Группируем по датам
        by_date = {}
        for i in existing:
            date = i.get('date', '')
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(i)

        # Ищем наименее загруженную дату
        best_date = None
        min_load = float('inf')

        for date in preferred_dates:
            load = len(by_date.get(date, []))
            if load < min_load:
                min_load = load
                best_date = date

        if not best_date and preferred_dates:
            best_date = preferred_dates[0]

        return {
            "recommended_date": best_date,
            "recommended_time": "11:00",
            "alternative_options": [
                {"date": d, "time": "14:00", "reason": "Альтернативный слот"}
                for d in preferred_dates[1:3]
            ],
            "reasoning": f"Дата {best_date} имеет наименьшую загрузку",
            "confidence": 70,
            "considerations": [
                "Проверьте доступность интервьюера",
                "Уточните удобное время у кандидата"
            ]
        }

    def _format_candidate_experience(self, candidate: Dict) -> str:
        """Форматирует опыт кандидата для промпта"""
        exp = candidate.get('experience', [])
        if isinstance(exp, list):
            if not exp:
                return "Нет опыта"
            exp_strs = []
            for e in exp[:2]:  # Берем первые 2 места работы
                if isinstance(e, dict):
                    # ИСПРАВЛЕНО: правильное экранирование кавычек
                    exp_strs.append(
                        f"{e.get('position', '')} в {e.get('company', '')} ({e.get('start', '')}-{e.get('end', 'н.в.')})")
            return "; ".join(exp_strs)
        return str(exp) if exp else "Нет опыта"

    def _format_candidate_skills(self, candidate: Dict) -> str:
        """Форматирует навыки кандидата для промпта"""
        skills = candidate.get('skills', [])
        if isinstance(skills, list):
            return ", ".join(skills[:5])  # Берем первые 5 навыков
        return str(skills) if skills else "Не указаны"

    def _format_interviews_by_day(self, by_day: Dict) -> str:
        """Форматирует собеседования по дням"""
        lines = []
        for date, interviews in sorted(by_day.items()):
            lines.append(f"{date}: {len(interviews)} собеседований")
            for i in interviews:
                lines.append(f"  - {i.get('time')}: {i.get('candidate')}")
        return "\n".join(lines)

    def _format_busy_days(self, busy_days: Dict) -> str:
        """Форматирует загруженность по дням"""
        if not busy_days:
            return "Нет данных о загруженности"
        return "\n".join([f"{date}: {count} собеседований" for date, count in busy_days.items()])