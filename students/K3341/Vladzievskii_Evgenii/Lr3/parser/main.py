"""
Сервис парсера — отдельное FastAPI приложение.
Принимает URL, загружает HTML-страницу, извлекает заголовок и цену (для книг),
возвращает результат.

Запуск:
    uvicorn parser.main:app --host 0.0.0.0 --port 8001
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import requests
from bs4 import BeautifulSoup
from decimal import Decimal


app = FastAPI(
    title="Web Parser Service",
    description="Сервис для парсинга книг с books.toscrape.com",
    version="1.0.0",
)


class ParseRequest(BaseModel):
    url: HttpUrl


class ParseResponse(BaseModel):
    url: str
    title: str | None = None
    price: float | None = None
    status_code: int


@app.post("/parse", response_model=ParseResponse)
def parse_url(request: ParseRequest) -> ParseResponse:
    """
    Загружает HTML-страницу, извлекает название (h1) и цену (.price_color).
    Для обычных страниц (без цены) возвращает title + price=None.
    """
    url = str(request.url)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.find("h1").text.strip() if soup.find("h1") else None

        # Пытаемся извлечь цену книги
        price = None
        price_el = soup.find("p", class_="price_color")
        if price_el:
            price_text = price_el.text.strip()
            price = float(
                Decimal("".join(c for c in price_text if c.isdigit() or c == "."))
            )

        status = response.status_code
    except requests.RequestException as e:
        status = getattr(e.response, "status_code", 502) if hasattr(e, "response") else 502
        title = None
        price = None

    return ParseResponse(url=url, title=title, price=price, status_code=status)


@app.get("/health")
def health():
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "service": "parser"}
