# -*- coding: utf-8 -*-
"""
ИИ-агент парсера вакансий S7.
Читает ссылки из Links.txt, собирает вакансии с требований и условий, сохраняет в output_file.json.
"""
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse, parse_qs

import requests

# Константы
LINKS_FILE = "Links.txt"
OUTPUT_FILE = "vacancy_test_file.json"
HH_API_BASE = "https://api.hh.ru"
USER_AGENT = "S7VacancyParser/1.0 (educational project)"


def _find_section_start(text: str, after: int, header: str) -> int:
    """Найти начало контента после заголовка (пропустить заголовок и пробелы/переносы)."""
    idx = text.lower().find(header.lower(), after)
    if idx == -1:
        return -1
    idx += len(header)
    while idx < len(text) and text[idx] in " \t\n·•":
        idx += 1
    return idx


def parse_description_blocks(description: str) -> dict[str, str]:
    """Извлекает из текста вакансии блоки: обязанности, требования, условия."""
    if not description or not description.strip():
        return {"responsibilities": "", "requirements": "", "conditions": ""}

    text = description.strip()
    result = {"responsibilities": "", "requirements": "", "conditions": ""}
    lower = text.lower()
    headers = [
        ("обязанности", "responsibilities"),
        ("требования", "requirements"),
        ("условия", "conditions"),
        ("мы предлагаем", "conditions"),
    ]
    positions = []
    for h, key in headers:
        idx = lower.find(h)
        if idx != -1:
            positions.append((idx, key, h))
    positions.sort(key=lambda x: x[0])

    for i, (start, key, header) in enumerate(positions):
        content_start = _find_section_start(text, start, header)
        if content_start == -1:
            continue
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        block = text[content_start:end].strip()
        if key == "conditions" and result["conditions"]:
            result["conditions"] += "\n" + block
        else:
            result[key] = block

    if not any(result.values()):
        result["requirements"] = re.sub(r"\s+", " ", text).strip()
    for key in result:
        result[key] = re.sub(r"\s+", " ", result[key]).strip()
    return result


def extract_employer_id_from_hh_url(url: str) -> str | None:
    """Извлекает employer_id из ссылки hh.ru/employer/766468."""
    parsed = urlparse(url)
    if "hh.ru" not in parsed.netloc:
        return None
    path = parsed.path.strip("/")
    parts = path.split("/")
    if len(parts) >= 2 and parts[0] == "employer":
        return parts[1].split("?")[0]
    qs = parse_qs(parsed.query)
    if "employer_id" in qs:
        return qs["employer_id"][0]
    return None


class VacancyParserAgent:
    """Агент: загрузка ссылок -> определение источника -> сбор вакансий -> сохранение."""

    def __init__(self, links_path: str = LINKS_FILE, output_path: str = OUTPUT_FILE):
        self.links_path = Path(links_path)
        self.output_path = Path(output_path)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
        self.collected: list[dict[str, Any]] = []

    @staticmethod
    def _make_key(item: dict[str, Any]) -> str:
        """Ключ для идентификации вакансии (учитываем источник и id)."""
        vid = str(item.get("id") or "")
        source = (item.get("source") or "").strip()
        return f"{source}::{vid}" if source else vid

    def _load_existing_index(self) -> dict[str, dict[str, Any]]:
        """Загрузить уже сохранённые вакансии из файла и построить индекс по ключу."""
        index: dict[str, dict[str, Any]] = {}
        if not self.output_path.exists():
            return index

        try:
            raw = self.output_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except Exception:
            # Если файл повреждён или в неверном формате — начинаем с нуля
            return index

        if not isinstance(data, list):
            return index

        for item in data:
            if not isinstance(item, dict):
                continue
            key = self._make_key(item)
            if key:
                index[key] = item

        return index

    def step_load_links(self) -> list[str]:
        """Шаг 1: загрузить ссылки из файла."""
        if not self.links_path.exists():
            raise FileNotFoundError(f"Файл ссылок не найден: {self.links_path}")
        lines = self.links_path.read_text(encoding="utf-8").strip().splitlines()
        return [u.strip() for u in lines if u.strip().startswith("http")]

    def step_detect_sources(self, urls: list[str]) -> list[tuple[str, str]]:
        """Шаг 2: для каждой ссылки определить (url, source). source: 'hh' | 's7'."""
        result = []
        for url in urls:
            if "hh.ru" in url:
                result.append((url, "hh"))
            elif "s7.ru" in url:
                result.append((url, "s7"))
            else:
                result.append((url, "unknown"))
        return result

    def step_fetch_hh_vacancies(self, employer_id: str) -> list[dict]:
        """Шаг 3a: получить список вакансий работодателя с hh.ru API."""
        all_items = []
        page = 0
        per_page = 50
        while True:
            r = self.session.get(
                f"{HH_API_BASE}/vacancies",
                params={"employer_id": employer_id, "per_page": per_page, "page": page},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            items = data.get("items", [])
            if not items:
                break
            all_items.extend(items)
            if page >= data.get("pages", 1) - 1:
                break
            page += 1
            time.sleep(0.3)
        return all_items

    def step_fetch_hh_vacancy_details(self, vacancy_id: str) -> dict | None:
        """Получить полное описание одной вакансии с hh.ru."""
        r = self.session.get(f"{HH_API_BASE}/vacancies/{vacancy_id}", timeout=15)
        if r.status_code != 200:
            return None
        return r.json()

    def step_parse_and_normalize(self, raw: dict, source: str) -> dict[str, Any]:
        """Нормализовать вакансию в единый формат для output_file.json."""
        if source == "hh":
            desc = raw.get("description") or ""
            blocks = parse_description_blocks(desc)
            salary = raw.get("salary")
            salary_str = ""
            if salary:
                parts = []
                if salary.get("from"):
                    parts.append(f"от {salary['from']}")
                if salary.get("to"):
                    parts.append(f"до {salary['to']}")
                if salary.get("currency"):
                    parts.append(salary["currency"])
                salary_str = " ".join(parts)
            area = (raw.get("area") or {}).get("name") or ""
            key_skills = raw.get("key_skills") or []
            # Число откликов (если доступно в API hh.ru)
            responses = ""
            counters = raw.get("counters") or {}
            if isinstance(counters, dict):
                resp_val = counters.get("responses") or counters.get("responses_total")
                if resp_val is not None:
                    responses = str(resp_val)
            skills_str_parts = []
            for skill in key_skills:
                name = (skill or {}).get("name")
                if name:
                    skills_str_parts.append(name)
            skills_str = ", ".join(skills_str_parts)
            return {
                "id": raw.get("id"),
                "source": "hh.ru",
                "title": raw.get("name", ""),
                "link": raw.get("alternate_url", ""),
                "requirements": blocks["requirements"] or (raw.get("snippet") or {}).get("requirement") or "",
                "conditions": blocks["conditions"],
                "responsibilities": blocks["responsibilities"] or (raw.get("snippet") or {}).get("responsibility") or "",
                "salary": salary_str,
                "area": area,
                "experience": (raw.get("experience") or {}).get("name", ""),
                "schedule": (raw.get("schedule") or {}).get("name", ""),
                "employment": (raw.get("employment") or {}).get("name", ""),
                "published_at": raw.get("published_at"),
                "skills": skills_str,
                "responses": responses,
            }
        return {}

    def step_fetch_s7_vacancies(self, _url: str) -> list[dict]:
        """Шаг 3b: попытка получить вакансии с сайта s7.ru (часто те же, что на hh)."""
        # S7 на своей странице часто ведёт на hh или дублирует; без стабильного API оставляем пустой список
        # при необходимости можно добавить парсинг HTML через BeautifulSoup
        return []

    def run(
        self, progress_callback: Callable[[int, int], None] | None = None
    ) -> list[dict]:
        """Запуск агента: загрузка ссылок -> сбор с hh -> сохранение в output_file.json.

        progress_callback(done, total) — опциональный колбэк для отслеживания прогресса.
        """
        # Загружаем уже сохранённые вакансии, чтобы не дублировать и обновлять их при изменениях
        existing_index = self._load_existing_index()

        links = self.step_load_links()
        sources = self.step_detect_sources(links)

        # Сначала собираем списки вакансий, чтобы знать общее количество для прогресса
        hh_batches: list[tuple[str, list[dict]]] = []
        total_items = 0

        for url, source in sources:
            if source == "hh":
                employer_id = extract_employer_id_from_hh_url(url)
                if not employer_id:
                    continue
                items = self.step_fetch_hh_vacancies(employer_id)
                hh_batches.append((url, items))
                total_items += len(items)
            elif source == "s7":
                # Для потенциального будущего расширения можно также учитывать вакансии S7
                s7_items = self.step_fetch_s7_vacancies(url)
                for item in s7_items:
                    if not isinstance(item, dict):
                        continue
                    if "id" not in item or not item["id"]:
                        continue
                    item.setdefault("source", "s7.ru")
                    key = self._make_key(item)
                    existing_index[key] = item

        processed = 0

        # Теперь обходим все hh-вакансии, получаем детали и обновляем прогресс
        for _url, items in hh_batches:
            for item in items:
                vid = item.get("id")
                if not vid:
                    continue
                full = self.step_fetch_hh_vacancy_details(vid)
                if full:
                    normalized = self.step_parse_and_normalize(full, "hh")
                else:
                    normalized = self.step_parse_and_normalize(item, "hh")
                if not normalized:
                    continue
                key = self._make_key(normalized)
                # Если вакансия уже есть, старая версия будет перезаписана новой
                existing_index[key] = normalized
                processed += 1
                if progress_callback and total_items:
                    try:
                        progress_callback(processed, total_items)
                    except Exception:
                        # Прогресс не должен ломать основной процесс
                        pass
                time.sleep(0.25)

        # Преобразуем индекс обратно в список для сохранения
        self.collected = list(existing_index.values())

        self.step_save()
        return self.collected

    def step_save(self) -> None:
        """Сохранить собранные вакансии в output_file.json."""
        self.output_path.write_text(
            json.dumps(self.collected, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def main():
    # Работаем в директории скрипта (где лежит Links.txt)
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    agent = VacancyParserAgent()
    print("Запуск агента парсера вакансий S7...")
    vacancies = agent.run()
    print(f"Собрано вакансий: {len(vacancies)}. Результат сохранён в {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
