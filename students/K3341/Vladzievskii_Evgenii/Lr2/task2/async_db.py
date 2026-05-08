"""
Асинхронный модуль для работы с БД из ЛР1 (sqlalchemy.ext.asyncio + asyncpg).

Используется async_parser.py — неблокирующие запросы к PostgreSQL.
Не трогает синхронный db.py (для threading/multiprocessing).
"""
import os
import sys
from decimal import Decimal

LR1_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Lr1"))
if LR1_PATH not in sys.path:
    sys.path.insert(0, LR1_PATH)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finance:finance123@localhost:5432/finance_db",
)
# asyncpg expects postgresql+asyncpg://
ASYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://", 1
)

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import select, func

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
_async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Создать все таблицы ЛР1 (если ещё не созданы) + служебные данные."""
    from app.models import User, Category, Transaction  # noqa: F811
    from sqlmodel import SQLModel

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    await _ensure_defaults()


async def _ensure_defaults() -> None:
    """Создать пользователя и категорию по умолчанию, если их нет."""
    from app.models import User, Category, TransactionType

    async with _async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == "parser@lab2.local")
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email="parser@lab2.local",
                username="parser",
                hashed_password="lab2parser",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        result = await session.execute(
            select(Category).where(
                Category.name == "Books", Category.user_id == user.id
            )
        )
        cat = result.scalar_one_or_none()
        if not cat:
            cat = Category(
                name="Books",
                type=TransactionType.EXPENSE,
                user_id=user.id,
            )
            session.add(cat)
            await session.commit()
            await session.refresh(cat)


async def save_transaction(title: str, price_str: str) -> dict:
    """
    Сохранить спарсенную книгу как транзакцию (асинхронно).

    Парсит цену из строки вида '£51.77', создаёт expense-транзакцию.
    """
    from app.models import User, Transaction, Category, TransactionType

    price = float(
        Decimal("".join(c for c in price_str if c.isdigit() or c == "."))
    )

    async with _async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == "parser@lab2.local")
        )
        user = result.scalar_one_or_none()
        if not user:
            raise RuntimeError("User not found — run init_db() first")

        result = await session.execute(
            select(Category).where(
                Category.name == "Books", Category.user_id == user.id
            )
        )
        cat = result.scalar_one_or_none()
        if not cat:
            cat = Category(
                name="Books",
                type=TransactionType.EXPENSE,
                user_id=user.id,
            )
            session.add(cat)
            await session.commit()

        txn = Transaction(
            amount=price,
            description=title,
            type=TransactionType.EXPENSE,
            category_id=cat.id,
            user_id=user.id,
        )
        session.add(txn)
        await session.commit()
        await session.refresh(txn)
        return {
            "id": txn.id,
            "amount": txn.amount,
            "description": txn.description,
        }


async def stats() -> dict:
    """Статистика по спарсенным транзакциям (асинхронно)."""
    from app.models import Transaction

    async with _async_session_factory() as session:
        result = await session.execute(
            select(func.count()).select_from(Transaction)
        )
        total = result.scalar_one()

        result = await session.execute(
            select(func.sum(Transaction.amount)).select_from(Transaction)
        )
        total_amount = result.scalar_one() or 0.0

        result = await session.execute(
            select(Transaction)
            .order_by(Transaction.created_at.desc())
            .limit(5)
        )
        latest = result.scalars().all()

    return {
        "total": total,
        "total_amount": round(total_amount, 2),
        "latest": latest,
    }
