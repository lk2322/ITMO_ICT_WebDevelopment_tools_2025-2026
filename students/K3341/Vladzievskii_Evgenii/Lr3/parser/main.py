"""
Сервис парсера — отдельное FastAPI приложение.
Принимает URL, загружает HTML-страницу, извлекает заголовок и возвращает результат.

Запуск:
    uvicorn parser.main:app --host 0.0.0.0 --port 8001
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import requests
from bs4 import BeautifulSoup


app = FastAPI(
    title="Web Parser Service",
    description="Сервис для парсинга заголовков веб-страниц",
    version="1.0.0",
)


class ParseRequest(BaseModel):
    url: HttpUrl


class ParseResponse(BaseModel):
    url: str
    title: str | None = None
    status_code: int


@app.post("/parse", response_model=ParseResponse)
def parse_url(request: ParseRequest) -> ParseResponse:
    """
    Загружает HTML-страницу по указанному URL и извлекает заголовок (<title>).
    """
    url = str(request.url)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else None
        status = response.status_code
    except requests.RequestException as e:
        status = getattr(e.response, "status_code", 502) if hasattr(e, "response") else 502
        title = None

    return ParseResponse(url=url, title=title, status_code=status)


@app.get("/health")
def health():
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "service": "parser"}
