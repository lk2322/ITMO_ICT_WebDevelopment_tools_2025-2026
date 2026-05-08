"""
Модуль для работы с базой данных из ЛР1 (finance_db).
Использует существующие таблицы user, category, transaction.
Наполняет transaction данными, спарсенными с веб-страниц.

Перед запуском необходимо:
  docker compose up db -d   # в папке Lr1
"""
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

# Добавляем путь к ЛР1 для импорта моделей
LR1_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Lr1"))
if LR1_PATH not in sys.path:
    sys.path.insert(0, LR1_PATH)

# Импортируем engine из ЛР1 (или создаём свой с тем же URL)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finance:finance123@localhost:5432/finance_db",
)

from sqlmodel import Session, create_engine, SQLModel

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Создать все таблицы ЛР1 (если ещё не созданы) + служебные данные."""
    from app.models import User, Category, Transaction  # noqa: F811
    SQLModel.metadata.create_all(engine)
    _ensure_defaults()


def _ensure_defaults() -> None:
    """Создать пользователя и категорию по умолчанию, если их нет."""
    from app.models import User, Category, TransactionType
    from sqlmodel import select

    with Session(engine) as s:
        user = s.exec(select(User).where(User.email == "parser@lab2.local")).first()
        if not user:
            user = User(
                email="parser@lab2.local",
                username="parser",
                hashed_password="lab2parser",
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
            cat = Category(name="Books", type=TransactionType.EXPENSE, user_id=user.id)
            s.add(cat)
            s.commit()
            s.refresh(cat)


def save_transaction(title: str, price_str: str) -> dict:
    """
    Сохранить спарсенную книгу как транзакцию в таблицу transaction.

    Парсит цену из строки вида '£51.77', создаёт expense-транзакцию.
    Находит пользователя parser@lab2.local и категорию Books.
    """
    from app.models import User, Transaction, Category, TransactionType
    from sqlmodel import select

    # Извлечь число из строки цены (убрать £ и прочие символы)
    price = float(
        Decimal("".join(c for c in price_str if c.isdigit() or c == "."))
    )

    with Session(engine) as s:
        user = s.exec(
            select(User).where(User.email == "parser@lab2.local")
        ).first()
        if not user:
            raise RuntimeError("User not found — run init_db() first")

        cat = s.exec(
            select(Category).where(
                Category.name == "Books", Category.user_id == user.id
            )
        ).first()
        if not cat:
            cat = Category(
                name="Books", type=TransactionType.EXPENSE, user_id=user.id
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
        return {
            "id": txn.id,
            "amount": txn.amount,
            "description": txn.description,
        }


def stats() -> dict:
    """Статистика по спарсенным транзакциям."""
    from app.models import Transaction
    from sqlmodel import select, func

    with Session(engine) as s:
        total = s.exec(
            select(func.count()).select_from(Transaction)
        ).one()
        total_amount = s.exec(
            select(func.sum(Transaction.amount)).select_from(Transaction)
        ).one() or 0.0
        latest = s.exec(
            select(Transaction)
            .order_by(Transaction.created_at.desc())
            .limit(5)
        ).all()
    return {
        "total": total,
        "total_amount": round(total_amount, 2),
        "latest": latest,
    }
