import json
import os
import random


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "output_file.json")
    output_path = os.path.join(base_dir, "vacancy_test_file.json")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Файл output_file.json должен содержать JSON-массив объектов.")

    count = min(25, len(data))

    # Берём 25 (или меньше, если объектов меньше) случайных объектов в случайном порядке
    sample = random.sample(data, count)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

