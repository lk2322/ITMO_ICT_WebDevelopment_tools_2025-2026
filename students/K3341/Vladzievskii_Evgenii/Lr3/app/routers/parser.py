"""
Роутер для парсинга веб-страниц.
Предоставляет синхронный (через HTTP к parser-сервису) и асинхронный (через Celery) эндпоинты.
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
import requests

# Celery импортируется опционально — только если настроен
try:
    from celery_app import parse_url_task, celery_app
    from celery.result import AsyncResult

    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

router = APIRouter(prefix="/parse", tags=["Parser"])

# Адрес parser-сервиса (из переменной окружения)
PARSER_URL = os.getenv("PARSER_URL", "http://parser:8001")


class ParseRequest(BaseModel):
    url: HttpUrl


class ParseResponse(BaseModel):
    url: str
    title: str | None = None
    price: float | None = None
    status_code: int
    method: str


class TaskResponse(BaseModel):
    task_id: str
    status: str
    url: str
    message: str


@router.post("", response_model=ParseResponse)
def parse_sync(request: ParseRequest) -> ParseResponse:
    """
    Синхронный вызов парсера.
    FastAPI отправляет HTTP-запрос сервису parser (контейнер parser:8001)
    и возвращает результат клиенту.
    """
    url = str(request.url)
    try:
        resp = requests.post(
            f"{PARSER_URL}/parse",
            json={"url": url},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return ParseResponse(
            url=data["url"],
            title=data.get("title"),
            price=data.get("price"),
            status_code=data.get("status_code", 200),
            method="sync",
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Parser service unavailable: {e}",
        )


@router.post("/async", response_model=TaskResponse)
def parse_async(request: ParseRequest) -> TaskResponse:
    """
    Асинхронный вызов парсера через очередь Celery.
    Задача ставится в очередь Redis, Celery worker обрабатывает её в фоне.
    Клиент получает task_id и может отслеживать статус через /parse/status/{task_id}.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Celery is not configured. Use /parse endpoint for synchronous parsing.",
        )

    url = str(request.url)
    task = parse_url_task.delay(url)

    return TaskResponse(
        task_id=task.id,
        status="queued",
        url=url,
        message=f"Task {task.id} queued. Check status at /parse/status/{task.id}",
    )


@router.get("/status/{task_id}")
def parse_status(task_id: str) -> dict:
    """
    Проверка статуса Celery-задачи по её ID.
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Celery is not configured.",
        )

    task = AsyncResult(task_id, app=celery_app)
    response = {
        "task_id": task_id,
        "status": task.state,
    }

    if task.state == "SUCCESS":
        response["result"] = task.result
    elif task.state == "FAILURE":
        response["error"] = str(task.info)
    elif task.state == "PROGRESS":
        response["meta"] = task.info

    return response
