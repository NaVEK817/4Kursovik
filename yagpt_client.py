from __future__ import annotations

import warnings

# Если в окружении включён режим "warnings -> errors", то импорты LangChain
# могут падать на предупреждениях. Здесь глушим только известные "шумные"
# предупреждения, которые не должны блокировать запуск приложения.
warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"The class `Ollama` was deprecated.*",
    category=DeprecationWarning,
)

try:
    # Новый пакет-интеграция для Ollama (рекомендуется LangChain).
    from langchain_ollama import OllamaLLM as Ollama  # type: ignore
except Exception:  # noqa: BLE001
    # Фолбэк для старых окружений (может показывать DeprecationWarning).
    from langchain_community.llms import Ollama

# Настройки модели Ollama (предустановленная YandexGPT‑5‑Lite‑8B‑instruct‑GGUF).
OLLAMA_MODEL = "YandexGPT-5-Lite-8B-instruct-GGUF"

_llm: Ollama | None = None


def _get_llm() -> Ollama:
    global _llm
    if _llm is None:
        _llm = Ollama(model=OLLAMA_MODEL)
    return _llm


def generate_vacancy(prompt: str) -> str:
    """Сгенерировать текст вакансии с помощью локальной модели через Ollama."""
    try:
        text = _get_llm().invoke(prompt)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Ошибка при обращении к модели Ollama {OLLAMA_MODEL}. "
            f"Убедитесь, что Ollama запущен и модель установлена. Детали: {exc}"
        ) from exc

    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("Ответ модели через Ollama не содержит текста вакансии.")

    return text.strip()

