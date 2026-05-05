"""
Celery-приложение и задачи для асинхронного парсинга.

Использует Redis как брокер сообщений и хранилище результатов.
Задачи ставятся в очередь через HTTP-эндпоинт /parse/async,
Celery worker обрабатывает их в фоновом режиме.
"""
import os
from celery import Celery
import requests
from bs4 import BeautifulSoup


# Redis URL из переменной окружения (или localhost по умолчанию)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "finance_parser",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name="parse_url")
def parse_url_task(self, url: str) -> dict:
    """
    Celery-задача: парсинг URL в фоновом режиме.

    Загружает HTML-страницу, извлекает заголовок и возвращает результат.
    Результат сохраняется в Redis и доступен через task_id.

    Args:
        url: URL веб-страницы для парсинга

    Returns:
        dict с полями url, title, status_code, parsed_at
    """
    self.update_state(state="PROGRESS", meta={"status": "downloading"})

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else None
        status = response.status_code
    except requests.RequestException as e:
        title = None
        status = getattr(e.response, "status_code", 502) if hasattr(e, "response") else 502

    from datetime import datetime

    return {
        "url": url,
        "title": title,
        "status_code": status,
        "parsed_at": datetime.utcnow().isoformat(),
    }
