# -*- coding: utf-8 -*-
"""
Парсер вакансий с hh.ru. Читает ссылки из Links.txt, сохраняет в output_file.json.
"""
import json
import re
import time
import html
from pathlib import Path
from urllib.parse import urlparse

import requests

LINKS_FILE = "Links.txt"
OUTPUT_FILE = "output_file.json"
HH_API = "https://api.hh.ru"
HEADERS = {"User-Agent": "S7Parser/1.0", "Accept": "application/json"}


def clean_html(text):
    """Удаляет HTML теги и декодирует entities."""
    if not text or not isinstance(text, str):
        return text
    return html.unescape(re.sub(r'<[^>]+>', '', text)).strip()


def extract_blocks(desc):
    """Извлекает требования, обязанности и условия из описания."""
    if not desc:
        return {"requirements": "", "responsibilities": "", "conditions": ""}
    
    text = desc.lower()
    res = {"requirements": "", "responsibilities": "", "conditions": ""}
    headers = [("обязанности", "responsibilities"), ("требования", "requirements"), 
               ("условия", "conditions"), ("мы предлагаем", "conditions")]
    
    positions = [(text.find(h), k) for h, k in headers if text.find(h) != -1]
    positions.sort()
    
    for i, (pos, key) in enumerate(positions):
        start = pos + len(key)
        end = positions[i+1][0] if i+1 < len(positions) else len(desc)
        res[key] = desc[start:end].strip()
    
    if not any(res.values()):
        res["requirements"] = re.sub(r'\s+', ' ', desc).strip()
    return {k: clean_html(v) for k, v in res.items()}


def get_employer_id(url):
    """Извлекает employer_id из ссылки hh.ru."""
    if "hh.ru" not in url:
        return None
    parts = urlparse(url).path.strip('/').split('/')
    return parts[1] if len(parts) >= 2 and parts[0] == "employer" else None


def fetch_vacancies(employer_id):
    """Получает все вакансии работодателя."""
    items, page = [], 0
    while True:
        data = requests.get(f"{HH_API}/vacancies", params={"employer_id": employer_id, "page": page}, 
                           headers=HEADERS, timeout=15).json()
        if not data.get("items"):
            break
        items.extend(data["items"])
        if page >= data.get("pages", 1) - 1:
            break
        page += 1
        time.sleep(0.3)
    return items


def parse_vacancy(raw):
    """Приводит вакансию к единому формату."""
    blocks = extract_blocks(raw.get("description", ""))
    salary = raw.get("salary")
    salary_str = ""
    if salary and isinstance(salary, dict):
        salary_str = " ".join(filter(None, [
            f"от {salary.get('from')}" if salary.get('from') else "",
            f"до {salary.get('to')}" if salary.get('to') else "",
            salary.get("currency", "")
        ]))
    
    skills = ", ".join([s.get("name", "") for s in raw.get("key_skills", []) if s.get("name")])
    responses = str(raw.get("counters", {}).get("responses", ""))
    
    return {
        "id": raw.get("id"),
        "source": "hh.ru",
        "title": raw.get("name", ""),
        "link": raw.get("alternate_url", ""),
        "requirements": blocks["requirements"] or raw.get("snippet", {}).get("requirement", ""),
        "conditions": blocks["conditions"],
        "responsibilities": blocks["responsibilities"] or raw.get("snippet", {}).get("responsibility", ""),
        "salary": salary_str,
        "area": raw.get("area", {}).get("name", ""),
        "experience": raw.get("experience", {}).get("name", ""),
        "schedule": raw.get("schedule", {}).get("name", ""),
        "employment": raw.get("employment", {}).get("name", ""),
        "published_at": raw.get("published_at"),
        "skills": skills,
        "responses": responses,
    }


def main():
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Чтение ссылок
    if not Path(LINKS_FILE).exists():
        print(f"Файл {LINKS_FILE} не найден!")
        return
    
    urls = [u.strip() for u in Path(LINKS_FILE).read_text(encoding="utf-8").splitlines() if u.strip().startswith("http")]
    print(f"Найдено ссылок: {len(urls)}")
    
    # Загрузка существующих данных
    vacancies = {}
    if Path(OUTPUT_FILE).exists():
        try:
            for v in json.loads(Path(OUTPUT_FILE).read_text(encoding="utf-8")):
                if isinstance(v, dict) and v.get("id"):
                    vacancies[f"hh.ru::{v['id']}"] = v
        except:
            pass
    
    # Сбор вакансий
    for url in urls:
        if "hh.ru" not in url:
            continue
        emp_id = get_employer_id(url)
        if not emp_id:
            continue
        
        items = fetch_vacancies(emp_id)
        print(f"Найдено вакансий: {len(items)}")
        
        for i, item in enumerate(items):
            vid = item.get("id")
            if not vid:
                continue
            
            # Получаем полные данные
            full = requests.get(f"{HH_API}/vacancies/{vid}", headers=HEADERS, timeout=15)
            if full.status_code == 200:
                parsed = parse_vacancy(full.json())
            else:
                parsed = parse_vacancy(item)
            
            vacancies[f"hh.ru::{vid}"] = parsed
            print(f"Обработано: {i+1}/{len(items)}")
            time.sleep(0.25)
    
    # Сохранение
    Path(OUTPUT_FILE).write_text(
        json.dumps(list(vacancies.values()), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Сохранено вакансий: {len(vacancies)}")


if __name__ == "__main__":
    import os
    main()