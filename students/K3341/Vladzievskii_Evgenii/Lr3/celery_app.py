"""
Celery-приложение и задачи для асинхронного парсинга.

Использует Redis как брокер сообщений и хранилище результатов.
Celery worker вызывает parser-сервис (http://parser:8001/parse),
получает результат и сохраняет его в таблицу transaction БД из ЛР1.
"""
import os
from datetime import datetime, timezone

from celery import Celery
import requests

# Redis URL из переменной окружения
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

# Адрес parser-сервиса
PARSER_URL = os.getenv("PARSER_URL", "http://parser:8001")


@celery_app.task(bind=True, name="parse_url")
def parse_url_task(self, url: str) -> dict:
    """
    Celery-задача: вызывает parser-сервис для парсинга URL,
    сохраняет результат в таблицу transaction БД из ЛР1.

    Args:
        url: URL веб-страницы для парсинга

    Returns:
        dict с полями url, title, price, status_code, transaction_id
    """
    self.update_state(state="PROGRESS", meta={"status": "calling parser service"})

    # 1. Вызываем parser-сервис
    try:
        resp = requests.post(
            f"{PARSER_URL}/parse",
            json={"url": url},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return {
            "url": url,
            "title": None,
            "price": None,
            "status_code": 502,
            "error": str(e)[:200],
        }

    title = data.get("title")
    price = data.get("price")
    status_code = data.get("status_code", 200)

    # 2. Сохраняем в БД (transaction), если есть цена (книга)
    txn_id = None
    if title and price:
        try:
            import sys
            sys.path.insert(0, "/app")
            from app.database import engine, init_db
            from app.models import User, Category, Transaction, TransactionType
            from sqlmodel import Session, select

            with Session(engine) as s:
                user = s.exec(
                    select(User).where(User.email == "parser@lab3.local")
                ).first()
                if not user:
                    from app.auth import get_password_hash
                    user = User(
                        email="parser@lab3.local",
                        username="parser",
                        hashed_password=get_password_hash("lab3parser"),
                    )
                    s.add(user)
                    s.commit()
                    s.refresh(user)

                cat = s.exec(
                    select(Category).where(
                        Category.name == "Books", Category.user_id == user.id
                    )
                ).first()
                if not cat:
                    cat = Category(
                        name="Books",
                        type=TransactionType.EXPENSE,
                        user_id=user.id,
                    )
                    s.add(cat)
                    s.commit()

                txn = Transaction(
                    amount=price,
                    description=title,
                    type=TransactionType.EXPENSE,
                    category_id=cat.id,
                    user_id=user.id,
                )
                s.add(txn)
                s.commit()
                s.refresh(txn)
                txn_id = txn.id
        except Exception as e:
            txn_id = None

    result = {
        "url": url,
        "title": title,
        "price": price,
        "status_code": status_code,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
    }
    if txn_id:
        result["transaction_id"] = txn_id

    return result
