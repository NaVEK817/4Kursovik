# -*- coding: utf-8 -*-
"""
Модуль для AI-анализа кандидатов с использованием локальной Ollama модели.
Оптимизированная версия с таймаутами и уменьшенными промптами.
"""
import json
import requests
from typing import Dict, List, Any, Optional
import time

class OllamaCandidateAnalyzer:
    """
    Класс для анализа кандидатов через локальную модель Ollama.
    """
    def __init__(self, model_name: str = "yandexgpt5:latest", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        self.timeout = 30  # Таймаут в секундах

    def _generate_prompt(self, vacancy: Dict, candidate: Dict) -> str:
        """
        Формирует оптимизированный промпт для модели.
        """
        # Быстрое извлечение ключевой информации
        vacancy_title = vacancy.get('title', 'Не указано')[:100]
        vacancy_area = vacancy.get('area', 'Не указан')
        vacancy_exp = vacancy.get('experience', 'Не указан')
        
        # Формируем краткое описание кандидата
        if 'first_name' in candidate:
            candidate_name = f"{candidate.get('last_name', '')} {candidate.get('first_name', '')}"
        else:
            candidate_name = candidate.get('name', 'Кандидат')[:50]
        
        candidate_title = candidate.get('title', candidate.get('vacancy_title', 'Не указана'))[:100]
        candidate_area = candidate.get('area', candidate.get('city', 'Не указан'))
        
        # Быстрая обработка опыта
        experience_text = ""
        exp_data = candidate.get('experience', [])
        if isinstance(exp_data, list) and exp_data:
            # Берем только последнее место работы для краткости
            last_exp = exp_data[0] if exp_data else {}
            if isinstance(last_exp, dict):
                company = last_exp.get('company', '')[:50]
                position = last_exp.get('position', '')[:50]
                if company and position:
                    experience_text = f"{position} в {company}"
                elif position:
                    experience_text = position
        elif isinstance(exp_data, str):
            experience_text = exp_data[:100]
        
        if not experience_text:
            experience_text = "Опыт не указан"
        
        # Быстрая обработка навыков
        skills_text = ""
        skills = candidate.get('skills', [])
        if isinstance(skills, list):
            skills_text = ', '.join(skills[:5])  # Только первые 5 навыков
        elif isinstance(skills, str):
            skills_text = skills[:100]
        
        if not skills_text:
            skills_text = "Навыки не указаны"
        
        # Максимально короткий промпт
        prompt = f"""Ты HR. Оцени кандидата для вакансии.

ВАКАНСИЯ:
{ vacancy_title }
Город: { vacancy_area }
Требуемый опыт: { vacancy_exp }

КАНДИДАТ:
{ candidate_name }
Должность: { candidate_title }
Город: { candidate_area }
Опыт: { experience_text }
Навыки: { skills_text }

Верни ТОЛЬКО JSON:
{{
  "score": (0-100),
  "summary": "2-3 слова о соответствии",
  "details": {{
    "experience_match": "1 фраза",
    "skills_match": "1 фраза",
    "location_match": "ok/нет",
    "strengths": ["1-2 пункта"],
    "weaknesses": ["1-2 пункта"],
    "recommendation": "Да/Нет/Сомнительно"
  }}
}}"""
        return prompt

    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Быстрый парсинг JSON из ответа"""
        try:
            # Очищаем ответ от возможного мусора
            text = response_text.strip()
            
            # Ищем JSON
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass
        return None

    def analyze(self, vacancy: Dict, candidate: Dict) -> Dict[str, Any]:
        """
        Быстрый анализ кандидата с таймаутом.
        """
        prompt = self._generate_prompt(vacancy, candidate)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Минимальная температура для быстрых ответов
                "num_predict": 256,   # Ограничиваем длину ответа
                "stop": ["}"]  # Останавливаемся на закрывающей скобке JSON
            }
        }

        # Пробуем подключиться с таймаутом
        try:
            start_time = time.time()
            
            response = requests.post(
                self.generate_url, 
                json=payload, 
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            llm_response = result.get('response', '')
            
            # Логируем время ответа для отладки
            elapsed = time.time() - start_time
            print(f"Анализ кандидата занял {elapsed:.1f} сек")
            
            parsed_result = self._parse_llm_response(llm_response)
            
            if parsed_result:
                return parsed_result
            else:
                # Если не удалось распарсить, возвращаем упрощенный результат
                return self._get_fallback_result(candidate)
                
        except requests.exceptions.Timeout:
            print("Таймаут при запросе к Ollama")
            return self._get_fallback_result(candidate)
            
        except requests.exceptions.ConnectionError:
            print("Ошибка подключения к Ollama")
            return self._get_fallback_result(candidate)
            
        except Exception as e:
            print(f"Ошибка при запросе: {str(e)}")
            return self._get_fallback_result(candidate)

    def _get_fallback_result(self, candidate: Dict) -> Dict[str, Any]:
        """
        Быстрый упрощенный анализ без AI (на случай ошибок).
        """
        score = 50  # Базовый score
        
        # Проверяем наличие ключевых полей
        if candidate.get('experience'):
            score += 10
        
        skills = candidate.get('skills', [])
        if isinstance(skills, list):
            if len(skills) > 3:
                score += 10
        elif isinstance(skills, str) and skills:
            score += 10
        
        # Ограничиваем score
        score = min(100, max(0, score))
        
        return {
            "score": score,
            "summary": "Базовый анализ (AI недоступен)",
            "details": {
                "experience_match": "Оценка по наличию опыта",
                "skills_match": f"Навыки: {len(skills) if isinstance(skills, list) else 'есть'}",
                "location_match": "Проверено",
                "strengths": ["Есть опыт"] if candidate.get('experience') else [],
                "weaknesses": ["Нет опыта"] if not candidate.get('experience') else [],
                "recommendation": "Сомнительно" if score < 60 else "Да"
            }
        }

    def analyze_batch(self, vacancy: Dict, candidates: List[Dict]) -> List[Dict]:
        """
        Пакетный анализ кандидатов (для будущего улучшения).
        """
        results = []
        for candidate in candidates:
            results.append(self.analyze(vacancy, candidate))
        return results