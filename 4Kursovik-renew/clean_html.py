# -*- coding: utf-8 -*-
"""
Скрипт для очистки HTML тегов из output_file.json
"""

import json
import re
import html
from pathlib import Path

def clean_html_tags(text: str) -> str:
    """Удаляет все HTML теги из текста и декодирует HTML entities."""
    if not text or not isinstance(text, str):
        return text
    
    # Удаляем все HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Декодируем HTML entities (&quot; -> ", &nbsp; -> пробел и т.д.)
    text = html.unescape(text)
    
    # Очищаем множественные пробелы и переносы строк
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
    return text.strip()

def clean_json_file(input_file: str, output_file: str = None):
    """Очищает HTML теги из JSON файла."""
    if output_file is None:
        output_file = input_file
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Файл {input_file} не найден!")
        return
    
    print(f"Чтение файла {input_file}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Поля, которые нужно очистить от HTML
    text_fields = ['requirements', 'conditions', 'responsibilities', 'title']
    
    cleaned_count = 0
    for item in data:
        if isinstance(item, dict):
            for field in text_fields:
                if field in item and item[field]:
                    original = item[field]
                    cleaned = clean_html_tags(original)
                    if original != cleaned:
                        item[field] = cleaned
                        cleaned_count += 1
    
    print(f"Очищено полей: {cleaned_count}")
    print(f"Сохранение в {output_file}...")
    
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Готово!")

if __name__ == "__main__":
    clean_json_file("output_file.json")
