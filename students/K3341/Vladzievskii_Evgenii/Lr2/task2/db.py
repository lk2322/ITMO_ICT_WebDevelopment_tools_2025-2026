"""
Модель базы данных для хранения результатов парсинга веб-страниц.
Расширяет базу данных из ЛР1 новой таблицей parsed_page.

Поля:
- id: первичный ключ
- url: URL спаршенной страницы
- title: заголовок страницы (<title>)
- status_code: HTTP-статус ответа
- parsed_at: временная метка парсинга
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session

DB_PATH = "lab2_parsed.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)


class ParsedPage(SQLModel, table=True):
    """Таблица для хранения результатов парсинга веб-страниц."""
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    title: Optional[str] = None
    status_code: int = Field(default=200)
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


def init_db() -> None:
    """Создать таблицы в БД."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Получить сессию БД."""
    return Session(engine)


def save_page(url: str, title: str, status_code: int = 200) -> ParsedPage:
    """Сохранить результат парсинга в БД."""
    page = ParsedPage(url=url, title=title, status_code=status_code)
    with Session(engine) as session:
        session.add(page)
        session.commit()
        session.refresh(page)
    return page


def stats() -> dict:
    """Статистика по спарсенным страницам."""
    from sqlmodel import select, func
    with Session(engine) as session:
        total = session.exec(select(func.count()).select_from(ParsedPage)).one()
        empty = session.exec(
            select(func.count()).where(ParsedPage.title == None)
        ).one()
        # Последние 5 страниц
        latest = session.exec(
            select(ParsedPage).order_by(ParsedPage.parsed_at.desc()).limit(5)
        ).all()
    return {
        "total": total,
        "with_title": total - empty,
        "without_title": empty,
        "latest": latest,
    }
