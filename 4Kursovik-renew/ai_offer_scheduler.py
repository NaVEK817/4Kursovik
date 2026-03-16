# -*- coding: utf-8 -*-
"""
ИИ-агент для назначения собеседований при создании оффера.
Интегрирует логику расписания, проверки слотов и генерации оффера.
"""
import json
import os
import re
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Импортируем вспомогательные модули
try:
    from candidate_enricher import CandidateEnricher
    from offer_generator import OfferGenerator
except ImportError:
    # Заглушки, если модули не найдены
    class CandidateEnricher:
        @staticmethod
        def enrich_candidate(data): return data

        @staticmethod
        def get_full_name(data): return data.get('name', 'Кандидат')


    class OfferGenerator:
        @staticmethod
        def clean_html(text): return text

        @staticmethod
        def generate_offer(candidate, vacancy, interview): return f"Оффер для {candidate}"

        @staticmethod
        def save_offer(candidate, vacancy, interview): return "offers/offer.txt"


class AIOfferScheduler:
    """
    ИИ-агент для автоматического назначения собеседований при создании оффера.
    """

    def __init__(self, schedule_file: str = "interviews_schedule.json",
                 messages_file: str = "interview_messages.json"):
        """
        Инициализация агента.

        Args:
            schedule_file: Путь к файлу с расписанием.
            messages_file: Путь к файлу с сообщениями.
        """
        self.schedule_file = Path(schedule_file)
        self.messages_file = Path(messages_file)
        self.enricher = CandidateEnricher()
        self.generator = OfferGenerator()

    # ==================== ЗАГРУЗКА/СОХРАНЕНИЕ ДАННЫХ ====================

    def _load_schedule(self) -> Dict[str, List[Dict]]:
        """Загружает расписание из JSON-файла."""
        if not self.schedule_file.exists():
            return {}
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_schedule(self, schedule: Dict[str, List[Dict]]):
        """Сохраняет расписание в JSON-файл."""
        try:
            # Создаем директорию, если нужно
            self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(schedule, f, ensure_ascii=False, indent=2, default=str)
        except IOError as e:
            print(f"Ошибка сохранения расписания: {e}")

    def _load_messages(self) -> List[Dict]:
        """Загружает сообщения из JSON-файла."""
        if not self.messages_file.exists():
            return []
        try:
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_messages(self, messages: List[Dict]):
        """Сохраняет сообщения в JSON-файл."""
        try:
            self.messages_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.messages_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2, default=str)
        except IOError as e:
            print(f"Ошибка сохранения сообщений: {e}")

    # ==================== ОСНОВНАЯ ЛОГИКА ПЛАНИРОВАНИЯ ====================

    def schedule_interview_for_offer(self,
                                     candidate_data: Dict,
                                     vacancy_data: Dict,
                                     recruiter_name: str = "Агент-рекрутер",
                                     days_ahead: int = 14) -> Dict[str, Any]:
        """
        Главный метод: назначает собеседование на основе данных кандидата и вакансии.

        Args:
            candidate_data: Данные кандидата (из resume_file.json или от другого агента).
            vacancy_data: Данные вакансии (из vacancy_test_file.json).
            recruiter_name: Имя рекрутера (интервьюера).
            days_ahead: На сколько дней вперед искать слоты.

        Returns:
            Dict с результатом операции.
        """
        print(f"🤖 AIOfferScheduler: Начинаю планирование для {candidate_data.get('name', 'кандидата')}")

        # 1. Обогащаем данные кандидата (заполняем ФИО, телефон и т.д., если их нет)
        enriched_candidate = self.enricher.enrich_candidate(candidate_data)
        candidate_name = self.enricher.get_full_name(enriched_candidate)

        # 2. Загружаем текущее расписание
        schedule = self._load_schedule()

        # 3. Анализируем предпочтения кандидата (город -> часовой пояс)
        preferences = self._analyze_preferences(enriched_candidate, vacancy_data)

        # 4. Находим оптимальный слот
        best_slot = self._find_optimal_slot(schedule, preferences, days_ahead)

        if not best_slot:
            return {
                "success": False,
                "message": "Не удалось найти подходящий слот для собеседования.",
                "candidate": candidate_name
            }

        # 5. Создаем запись о собеседовании
        interview_record = self._create_interview_record(
            candidate_name,
            best_slot,
            recruiter_name,
            vacancy_data
        )

        # 6. Сохраняем в расписание
        date_str = best_slot['date']
        if date_str not in schedule:
            schedule[date_str] = []
        schedule[date_str].append(interview_record)
        self._save_schedule(schedule)

        # 7. Генерируем и сохраняем текст оффера (приглашения)
        offer_text = self.generator.generate_offer(
            candidate_name,
            vacancy_data.get('title', 'Вакансия'),
            interview_record
        )
        offer_filename = self.generator.save_offer(
            candidate_name,
            vacancy_data.get('title', 'vacancy'),
            interview_record
        )

        # 8. Отправляем уведомление
        self._send_notification(interview_record)

        print(f"✅ AIOfferScheduler: Собеседование назначено на {date_str} в {best_slot['time']}")

        return {
            "success": True,
            "message": f"Собеседование успешно назначено на {date_str} в {best_slot['time']}",
            "candidate": candidate_name,
            "interview": interview_record,
            "offer_file": offer_filename,
            "offer_text": offer_text
        }

    def _analyze_preferences(self, candidate: Dict, vacancy: Dict) -> Dict:
        """
        Анализирует данные для определения предпочтений по времени.
        """
        preferences = {
            "timezone_offset": 3,  # По умолчанию Москва (UTC+3)
            "preferred_time_range": (10, 17),  # Рабочее время с 10 до 17
            "urgency": "medium"
        }

        # Определяем часовой пояс по городу кандидата
        city = candidate.get('city', vacancy.get('area', '')).lower()
        if any(word in city for word in ['москва', 'moscow', 'домодедово']):
            preferences["timezone_offset"] = 3
        elif any(word in city for word in ['новосибирск', 'novosibirsk', 'обь']):
            preferences["timezone_offset"] = 7
        elif any(word in city for word in ['владивосток', 'vladivostok']):
            preferences["timezone_offset"] = 10
        elif any(word in city for word in ['иркутск', 'irkutsk']):
            preferences["timezone_offset"] = 8
        elif any(word in city for word in ['екатеринбург', 'yekaterinburg']):
            preferences["timezone_offset"] = 5

        # Определяем срочность по тексту вакансии
        vacancy_text = (vacancy.get('title', '') + ' ' +
                        vacancy.get('requirements', '') + ' ' +
                        vacancy.get('conditions', '')).lower()

        urgent_words = ['срочно', 'urgent', 'немедленно', 'asap', 'hot']
        if any(word in vacancy_text for word in urgent_words):
            preferences["urgency"] = "high"
            preferences["preferred_time_range"] = (9, 18)  # Более широкий диапазон

        return preferences

    def _find_optimal_slot(self,
                           schedule: Dict,
                           preferences: Dict,
                           days_ahead: int) -> Optional[Dict]:
        """
        Ищет оптимальный слот для собеседования.
        """
        today = date.today()
        timezone_offset = preferences.get("timezone_offset", 3)
        preferred_start, preferred_end = preferences.get("preferred_time_range", (10, 17))

        # Все возможные временные слоты с шагом 30 минут
        all_possible_times = []
        for hour in range(9, 19):  # С 9:00 до 19:00
            all_possible_times.append(f"{hour:02d}:00")
            all_possible_times.append(f"{hour:02d}:30")

        for day in range(1, days_ahead + 1):
            current_date = today + timedelta(days=day)
            date_str = current_date.strftime("%Y-%m-%d")

            # Получаем занятые слоты на этот день
            busy_times = []
            if date_str in schedule:
                busy_times = [item['time'] for item in schedule[date_str]]

            # Проверяем каждый возможный слот
            for time_str in all_possible_times:
                # Проверка на занятость
                if time_str in busy_times:
                    continue

                # Проверка минимального интервала 30 минут
                if not self._check_min_interval(date_str, time_str, busy_times):
                    continue

                # Анализируем, подходит ли время по предпочтениям
                hour = int(time_str.split(':')[0])

                # Проверка, входит ли час в предпочтительный диапазон
                if preferred_start <= hour <= preferred_end:
                    confidence = 90
                    reason = "Время соответствует рабочему графику"
                elif hour < 9 or hour > 18:
                    # Слишком рано или поздно
                    continue
                else:
                    confidence = 70
                    reason = "Ближайший доступный слот"

                return {
                    "date": date_str,
                    "time": time_str,
                    "confidence": confidence,
                    "reason": reason
                }

        return None

    def _check_min_interval(self, date: str, new_time: str, busy_times: List[str]) -> bool:
        """
        Проверяет, соблюдается ли минимальный интервал в 30 минут.
        """
        new_h, new_m = map(int, new_time.split(':'))
        new_minutes = new_h * 60 + new_m

        for time_str in busy_times:
            busy_h, busy_m = map(int, time_str.split(':'))
            busy_minutes = busy_h * 60 + busy_m

            if abs(new_minutes - busy_minutes) < 30:
                return False
        return True

    def _create_interview_record(self,
                                 candidate_name: str,
                                 slot: Dict,
                                 recruiter: str,
                                 vacancy: Dict) -> Dict:
        """
        Создает запись о собеседовании.
        """
        # Очищаем название вакансии от HTML для читаемости
        clean_title = self.generator.clean_html(vacancy.get('title', 'Вакансия'))

        return {
            "id": f"int_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "candidate": candidate_name,
            "time": slot['time'],
            "date": slot['date'],
            "vacancy": clean_title,
            "vacancy_id": vacancy.get('id', ''),
            "recruiter": recruiter,
            "status": "scheduled",
            "comment": f"Авто-назначение от ИИ. {slot.get('reason', '')}",
            "created_by": "AI Offer Scheduler",
            "created_at": datetime.now().isoformat()
        }

    def _send_notification(self, interview: Dict):
        """
        Отправляет уведомление о новом собеседовании.
        """
        messages = self._load_messages()

        # Текст уведомления для кандидата
        notification_text = f"""
Здравствуйте, {interview['candidate']}!

Вам назначено собеседование на вакансию "{interview['vacancy']}".

📅 Дата: {interview['date']}
⏰ Время: {interview['time']}
👥 Интервьюер: {interview['recruiter']}

Пожалуйста, подтвердите своё участие или сообщите, если время неудобно.

С уважением,
Команда S7 Recruitment
"""
        notification = {
            "id": f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "type": "notification",
            "candidate": interview['candidate'],
            "interviewer": interview['recruiter'],
            "interview_id": interview['id'],
            "date": interview['date'],
            "time": interview['time'],
            "message": notification_text.strip(),
            "status": "sent",
            "created_at": datetime.now().isoformat(),
            "read": False
        }

        messages.append(notification)
        self._save_messages(messages)

    # ==================== УПРАВЛЕНИЕ ПЕРЕНОСАМИ ====================

    def request_reschedule(self, interview_id: str, reason: str, requested_by: str) -> Dict:
        """
        Создает запрос на перенос собеседования.
        """
        schedule = self._load_schedule()
        interview, old_date = self._find_interview_by_id(interview_id, schedule)

        if not interview:
            return {"success": False, "message": "Собеседование не найдено"}

        # Находим альтернативные слоты
        alternatives = self._find_free_slots(schedule, days_ahead=7)[:3]

        messages = self._load_messages()
        request = {
            "id": f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "type": "reschedule_request",
            "interview_id": interview_id,
            "interview_data": interview,
            "requested_by": requested_by,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "suggested_alternatives": alternatives
        }
        messages.append(request)
        self._save_messages(messages)

        return {
            "success": True,
            "message": "Запрос на перенос отправлен",
            "request_id": request['id']
        }

    def confirm_reschedule(self, request_id: str, new_date: str, new_time: str) -> Dict:
        """
        Подтверждает перенос собеседования.
        """
        messages = self._load_messages()
        request = None
        for msg in messages:
            if msg.get('id') == request_id:
                request = msg
                break

        if not request or request.get('status') != 'pending':
            return {"success": False, "message": "Запрос не найден или уже обработан"}

        interview = request['interview_data']
        schedule = self._load_schedule()
        old_date = interview.get('date')

        # Удаляем из старой даты
        if old_date in schedule:
            schedule[old_date] = [i for i in schedule[old_date] if i.get('id') != interview.get('id')]
            if not schedule[old_date]:
                del schedule[old_date]

        # Обновляем данные
        interview['date'] = new_date
        interview['time'] = new_time
        interview['status'] = 'rescheduled'
        interview['previous_date'] = old_date
        interview['previous_time'] = interview.get('time')
        interview['rescheduled_at'] = datetime.now().isoformat()

        # Добавляем в новую дату
        if new_date not in schedule:
            schedule[new_date] = []
        schedule[new_date].append(interview)
        self._save_schedule(schedule)

        # Обновляем статус запроса
        request['status'] = 'confirmed'
        request['resolved_at'] = datetime.now().isoformat()
        request['new_date'] = new_date
        request['new_time'] = new_time
        self._save_messages(messages)

        return {
            "success": True,
            "message": f"Собеседование перенесено на {new_date} {new_time}"
        }

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def _find_interview_by_id(self, interview_id: str, schedule: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """Ищет собеседование по ID во всем расписании."""
        for date_str, interviews in schedule.items():
            for interview in interviews:
                if interview.get('id') == interview_id:
                    return interview, date_str
        return None, None

    def _find_free_slots(self, schedule: Dict, days_ahead: int = 7) -> List[Dict]:
        """Находит свободные слоты в расписании на указанное количество дней вперед."""
        free_slots = []
        today = date.today()

        for day in range(1, days_ahead + 1):
            current_date = today + timedelta(days=day)
            date_str = current_date.strftime("%Y-%m-%d")

            busy_times = []
            if date_str in schedule:
                busy_times = [item['time'] for item in schedule[date_str]]

            for hour in range(9, 19):
                for minute in [0, 30]:
                    time_str = f"{hour:02d}:{minute:02d}"
                    if time_str not in busy_times:
                        free_slots.append({
                            "date": date_str,
                            "time": time_str,
                            "available": True
                        })
        return free_slots


# ==================== ПРИМЕР ИСПОЛЬЗОВАНИЯ ====================
if __name__ == "__main__":
    # Этот блок можно запустить для тестирования агента

    # Пример данных кандидата (как из resume_file.json)
    example_candidate = {
        "name": "Иванов Петр Сидорович",  # Будет распарсено enricher-ом
        "city": "Новосибирск",
        "experience": "От 3 до 6 лет",
        "skills": "Python, SQL, Excel"
    }

    # Пример данных вакансии (как из vacancy_test_file.json)
    example_vacancy = {
        "id": "130376893",
        "title": "Специалист call-центра (чат)",
        "area": "Новосибирск",
        "requirements": "Коммуникабельность, грамотная речь",
        "conditions": "График 5/2, ДМС"
    }

    # Создаем агента и запускаем планирование
    scheduler = AIOfferScheduler()
    result = scheduler.schedule_interview_for_offer(
        candidate_data=example_candidate,
        vacancy_data=example_vacancy,
        recruiter_name="Иванова Е. (HR)",
        days_ahead=10
    )

    if result['success']:
        print("\n" + "=" * 50)
        print("✅ РЕЗУЛЬТАТ РАБОТЫ АГЕНТА")
        print("=" * 50)
        print(f"Кандидат: {result['candidate']}")
        print(f"Дата: {result['interview']['date']} в {result['interview']['time']}")
        print(f"Вакансия: {result['interview']['vacancy']}")
        print(f"Интервьюер: {result['interview']['recruiter']}")
        print(f"Файл с оффером: {result.get('offer_file', 'Не сохранен')}")
        print("=" * 50)
    else:
        print(f"❌ Ошибка: {result['message']}")