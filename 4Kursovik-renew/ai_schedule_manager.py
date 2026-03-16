# -*- coding: utf-8 -*-
"""
ИИ-менеджер для автоматического назначения собеседований и управления офферами
"""
import json
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import requests
from PyQt5.QtCore import QDate


class AIScheduleManager:
    """
    ИИ-менеджер для автоматического назначения собеседований и управления офферами.
    Интегрирован с Ollama для умного планирования.
    """

    def __init__(self, model_name: str = "yandexgpt5:latest", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        self.schedule_file = "interviews_schedule.json"
        self.messages_file = "interview_messages.json"

    # ==================== АВТОМАТИЧЕСКОЕ НАЗНАЧЕНИЕ ОФФЕРА ====================

    def auto_schedule_offer(self,
                            candidate_name: str,
                            candidate_data: Dict,
                            interviewer_name: str,
                            preferred_days: List[str] = None) -> Dict[str, Any]:
        """
        Автоматически назначает собеседование при создании оффера.

        Args:
            candidate_name: Имя кандидата
            candidate_data: Данные кандидата (город, опыт, навыки)
            interviewer_name: Имя интервьюера
            preferred_days: Предпочтительные дни (если есть)

        Returns:
            Dict с предложенным временем
        """
        # Загружаем текущее расписание
        schedule = self._load_schedule()

        # Анализируем свободные слоты
        free_slots = self._find_free_slots(schedule, next_days=14)

        # Анализируем предпочтения кандидата
        candidate_preferences = self._analyze_candidate_preferences(candidate_data)

        # Получаем предпочтения интервьюера (можно расширить)
        interviewer_preferences = self._get_interviewer_preferences(interviewer_name)

        # Ищем оптимальное время
        best_slot = self._find_optimal_slot(
            free_slots,
            candidate_preferences,
            interviewer_preferences,
            preferred_days
        )

        if best_slot:
            return {
                "success": True,
                "date": best_slot["date"],
                "time": best_slot["time"],
                "candidate": candidate_name,
                "interviewer": interviewer_name,
                "confidence": best_slot.get("confidence", 80),
                "reason": best_slot.get("reason", "Оптимальное время")
            }
        else:
            return {
                "success": False,
                "message": "Не удалось найти подходящее время",
                "suggestions": self._get_alternative_suggestions(schedule)
            }

    def _find_free_slots(self, schedule: Dict, next_days: int = 14) -> List[Dict]:
        """Находит свободные слоты в расписании"""
        free_slots = []
        today = date.today()

        # Стандартные временные слоты
        time_slots = ["09:00", "10:00", "11:00", "12:00", "13:00",
                      "14:00", "15:00", "16:00", "17:00", "18:00"]

        for i in range(1, next_days + 1):
            current_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            day_slots = []

            # Получаем занятые времена на эту дату
            busy_times = [item["time"] for item in schedule.get(current_date, [])]

            # Добавляем свободные слоты
            for time in time_slots:
                if time not in busy_times:
                    day_slots.append({
                        "date": current_date,
                        "time": time,
                        "available": True
                    })

            free_slots.extend(day_slots)

        return free_slots

    def _analyze_candidate_preferences(self, candidate_data: Dict) -> Dict:
        """Анализирует предпочтения кандидата на основе его данных"""
        preferences = {
            "preferred_time": "day",  # day, morning, evening
            "timezone_offset": 0,
            "urgency": "medium",  # high, medium, low
            "notes": []
        }

        # Определяем по городу часовой пояс
        city = candidate_data.get('area', candidate_data.get('city', ''))
        if 'Москва' in city:
            preferences["timezone_offset"] = 3
        elif 'Новосибирск' in city:
            preferences["timezone_offset"] = 7
        elif 'Владивосток' in city:
            preferences["timezone_offset"] = 10

        # Определяем срочность по вакансии
        vacancy_title = candidate_data.get('title', '').lower()
        if any(word in vacancy_title for word in ['срочно', ' urgent', 'немедленно']):
            preferences["urgency"] = "high"

        return preferences

    def _get_interviewer_preferences(self, interviewer_name: str) -> Dict:
        """Получает предпочтения интервьюера"""
        # Здесь можно загружать из отдельного файла
        return {
            "preferred_days": ["monday", "wednesday", "friday"],
            "preferred_time": "morning",  # morning, afternoon, evening
            "busy_times": []  # Можно загружать из календаря
        }

    def _find_optimal_slot(self,
                           free_slots: List[Dict],
                           candidate_prefs: Dict,
                           interviewer_prefs: Dict,
                           preferred_days: List[str] = None) -> Optional[Dict]:
        """Находит оптимальный слот с помощью ИИ или правил"""

        # Если есть предпочтительные дни, фильтруем
        if preferred_days:
            free_slots = [s for s in free_slots if s["date"] in preferred_days]

        if not free_slots:
            return None

        # Простая эвристика для быстрого выбора
        for slot in free_slots[:5]:  # Проверяем первые 5 слотов
            hour = int(slot["time"].split(":")[0])

            # Учитываем предпочтения кандидата
            if candidate_prefs["preferred_time"] == "morning" and 9 <= hour <= 11:
                slot["confidence"] = 90
                slot["reason"] = "Утреннее время, удобное для кандидата"
                return slot
            elif candidate_prefs["preferred_time"] == "evening" and 16 <= hour <= 18:
                slot["confidence"] = 90
                slot["reason"] = "Вечернее время, удобное для кандидата"
                return slot
            elif 10 <= hour <= 15:  # Дневное время по умолчанию
                slot["confidence"] = 80
                slot["reason"] = "Стандартное рабочее время"
                return slot

        # Если ничего не подошло, берем первый
        free_slots[0]["confidence"] = 70
        free_slots[0]["reason"] = "Ближайший доступный слот"
        return free_slots[0]

    # ==================== УПРАВЛЕНИЕ СООБЩЕНИЯМИ ====================

    def send_interview_notification(self, interview_data: Dict) -> Dict:
        """
        Отправляет уведомление о назначенном собеседовании
        """
        message = self._generate_notification_message(interview_data)

        # Сохраняем сообщение
        messages = self._load_messages()

        new_message = {
            "id": self._generate_message_id(),
            "type": "notification",
            "candidate": interview_data.get("candidate"),
            "interviewer": interview_data.get("interviewer"),
            "date": interview_data.get("date"),
            "time": interview_data.get("time"),
            "message": message,
            "status": "sent",
            "created_at": datetime.now().isoformat(),
            "read": False
        }

        messages.append(new_message)
        self._save_messages(messages)

        return new_message

    def request_reschedule(self,
                           interview_id: str,
                           reason: str,
                           requested_by: str) -> Dict:
        """
        Запрос на перенос собеседования от кандидата или интервьюера
        """
        # Находим собеседование
        schedule = self._load_schedule()
        interview = self._find_interview_by_id(interview_id, schedule)

        if not interview:
            return {
                "success": False,
                "message": "Собеседование не найдено"
            }

        # Создаем запрос на перенос
        messages = self._load_messages()

        reschedule_request = {
            "id": self._generate_message_id(),
            "type": "reschedule_request",
            "interview_id": interview_id,
            "interview_data": interview,
            "requested_by": requested_by,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "suggested_alternatives": self._find_free_slots(schedule, next_days=7)[:3]
        }

        messages.append(reschedule_request)
        self._save_messages(messages)

        # Отправляем уведомление другой стороне
        self._notify_reschedule_request(reschedule_request)

        return {
            "success": True,
            "request_id": reschedule_request["id"],
            "message": "Запрос на перенос отправлен",
            "alternatives": reschedule_request["suggested_alternatives"]
        }

    def confirm_reschedule(self,
                           request_id: str,
                           new_date: str,
                           new_time: str) -> Dict:
        """
        Подтверждение переноса собеседования
        """
        messages = self._load_messages()

        # Находим запрос
        request = None
        for msg in messages:
            if msg.get("id") == request_id:
                request = msg
                break

        if not request:
            return {"success": False, "message": "Запрос не найден"}

        # Обновляем расписание
        schedule = self._load_schedule()
        interview = request["interview_data"]
        old_date = interview.get("date")
        old_time = interview.get("time")

        # Удаляем из старой даты
        if old_date in schedule:
            schedule[old_date] = [i for i in schedule[old_date]
                                  if i.get("id") != interview.get("id")]
            if not schedule[old_date]:
                del schedule[old_date]

        # Добавляем в новую дату
        interview["date"] = new_date
        interview["time"] = new_time
        interview["status"] = "rescheduled"
        interview["previous_date"] = old_date
        interview["previous_time"] = old_time
        interview["rescheduled_at"] = datetime.now().isoformat()

        if new_date not in schedule:
            schedule[new_date] = []
        schedule[new_date].append(interview)

        self._save_schedule(schedule)

        # Обновляем статус запроса
        request["status"] = "confirmed"
        request["resolved_at"] = datetime.now().isoformat()
        request["new_date"] = new_date
        request["new_time"] = new_time
        self._save_messages(messages)

        # Отправляем уведомления
        self._send_reschedule_confirmation(interview, old_date, old_time)

        return {
            "success": True,
            "message": "Собеседование успешно перенесено",
            "new_date": new_date,
            "new_time": new_time
        }

    def get_user_messages(self, user_name: str) -> List[Dict]:
        """
        Получает все сообщения для пользователя
        """
        messages = self._load_messages()

        user_messages = []
        for msg in messages:
            if (msg.get("candidate") == user_name or
                    msg.get("interviewer") == user_name or
                    msg.get("requested_by") == user_name):
                user_messages.append(msg)

        return sorted(user_messages, key=lambda x: x.get("created_at", ""), reverse=True)

    def mark_message_read(self, message_id: str):
        """Отмечает сообщение как прочитанное"""
        messages = self._load_messages()
        for msg in messages:
            if msg.get("id") == message_id:
                msg["read"] = True
                msg["read_at"] = datetime.now().isoformat()
                break
        self._save_messages(messages)

    # ==================== СТАТИСТИКА ====================

    def get_schedule_statistics(self) -> Dict:
        """
        Возвращает общую статистику по расписанию
        """
        schedule = self._load_schedule()
        messages = self._load_messages()

        total_interviews = sum(len(v) for v in schedule.values())

        # Статистика по дням
        daily_stats = {}
        for date, interviews in schedule.items():
            daily_stats[date] = {
                "count": len(interviews),
                "times": [i["time"] for i in interviews],
                "interviewers": list(set(i.get("interviewer", "Неизвестно") for i in interviews))
            }

        # Статистика по статусам
        status_stats = {
            "scheduled": 0,
            "rescheduled": 0,
            "cancelled": 0,
            "completed": 0
        }

        for interviews in schedule.values():
            for i in interviews:
                status = i.get("status", "scheduled")
                if status in status_stats:
                    status_stats[status] += 1

        # Статистика сообщений
        message_stats = {
            "total": len(messages),
            "unread": sum(1 for m in messages if not m.get("read", False)),
            "pending_requests": sum(1 for m in messages if m.get("status") == "pending")
        }

        # Анализ загрузки
        busy_days = sorted([(date, len(interviews)) for date, interviews in schedule.items()],
                           key=lambda x: x[1], reverse=True)

        return {
            "total_interviews": total_interviews,
            "days_with_interviews": len(schedule),
            "daily_stats": daily_stats,
            "status_stats": status_stats,
            "message_stats": message_stats,
            "busiest_days": busy_days[:5],
            "average_per_day": total_interviews / max(len(schedule), 1),
            "upcoming_interviews": self._get_upcoming_interviews(schedule)
        }

    def get_interviewer_stats(self, interviewer_name: str) -> Dict:
        """
        Статистика для конкретного интервьюера
        """
        schedule = self._load_schedule()

        interviewer_interviews = []
        for date, interviews in schedule.items():
            for i in interviews:
                if i.get("interviewer") == interviewer_name:
                    i_copy = i.copy()
                    i_copy["date"] = date
                    interviewer_interviews.append(i_copy)

        return {
            "total": len(interviewer_interviews),
            "upcoming": [i for i in interviewer_interviews if i["date"] >= date.today().strftime("%Y-%m-%d")],
            "by_day": self._group_by_day(interviewer_interviews)
        }

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def _load_schedule(self) -> Dict:
        """Загружает расписание из файла"""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_schedule(self, schedule: Dict):
        """Сохраняет расписание"""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(schedule, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения расписания: {e}")

    def _load_messages(self) -> List:
        """Загружает сообщения из файла"""
        if os.path.exists(self.messages_file):
            try:
                with open(self.messages_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_messages(self, messages: List):
        """Сохраняет сообщения"""
        try:
            with open(self.messages_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения сообщений: {e}")

    def _generate_message_id(self) -> str:
        """Генерирует уникальный ID сообщения"""
        return f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    def _find_interview_by_id(self, interview_id: str, schedule: Dict) -> Optional[Dict]:
        """Находит собеседование по ID"""
        for date, interviews in schedule.items():
            for i in interviews:
                if i.get("id") == interview_id:
                    i_copy = i.copy()
                    i_copy["date"] = date
                    return i_copy
        return None

    def _generate_notification_message(self, interview_data: Dict) -> str:
        """Генерирует текст уведомления"""
        return f"""
Здравствуйте, {interview_data.get('candidate')}!

Вам назначено собеседование на вакансию.

📅 Дата: {interview_data.get('date')}
⏰ Время: {interview_data.get('time')}
👥 Интервьюер: {interview_data.get('interviewer')}

Пожалуйста, подтвердите своё участие или сообщите, если время неудобно.

С уважением,
Команда S7 Recruitment
"""

    def _notify_reschedule_request(self, request: Dict):
        """Отправляет уведомление о запросе переноса"""
        # Здесь можно добавить отправку email или push-уведомления
        print(f"Запрос на перенос: {request}")

    def _send_reschedule_confirmation(self, interview: Dict, old_date: str, old_time: str):
        """Отправляет подтверждение переноса"""
        print(f"Собеседование перенесено с {old_date} {old_time} на {interview['date']} {interview['time']}")

    def _get_upcoming_interviews(self, schedule: Dict) -> List:
        """Получает предстоящие собеседования"""
        upcoming = []
        today = date.today().strftime("%Y-%m-%d")

        for date_str, interviews in schedule.items():
            if date_str >= today:
                for i in interviews:
                    i_copy = i.copy()
                    i_copy["date"] = date_str
                    upcoming.append(i_copy)

        return sorted(upcoming, key=lambda x: (x["date"], x["time"]))

    def _group_by_day(self, interviews: List) -> Dict:
        """Группирует собеседования по дням"""
        grouped = {}
        for i in interviews:
            day = i.get("date", "unknown")
            if day not in grouped:
                grouped[day] = []
            grouped[day].append(i)
        return grouped

    def _get_alternative_suggestions(self, schedule: Dict) -> List[str]:
        """Предлагает альтернативные варианты"""
        suggestions = []
        free_slots = self._find_free_slots(schedule, next_days=7)

        for slot in free_slots[:3]:
            suggestions.append(f"{slot['date']} в {slot['time']}")

        return suggestions