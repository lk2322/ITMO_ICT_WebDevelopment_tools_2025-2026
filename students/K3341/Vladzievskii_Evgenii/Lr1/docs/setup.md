# Установка и запуск

## Предварительные требования

- Python 3.9+
- Docker и Docker Compose
- Git

## 1. Клонирование репозитория

```bash
git clone <repo-url>
cd students/K3341/Vladzievskii_Evgenii/Lr1
```

## 2. Запуск PostgreSQL

Через Docker Compose:

```bash
docker compose up -d
```

Или вручную:

```bash
docker run -d --name finance-postgres \
  -e POSTGRES_USER=finance \
  -e POSTGRES_PASSWORD=finance123 \
  -e POSTGRES_DB=finance_db \
  -p 5432:5432 \
  postgres:16-alpine
```

## 3. Виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## 4. Настройка окружения

Скопируйте `.env.example` в `.env` и при необходимости измените значения:

```bash
cp .env.example .env
```

Содержимое `.env`:

```ini
DATABASE_URL=postgresql://finance:finance123@localhost:5432/finance_db
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 5. Миграции базы данных

```bash
# Применить все миграции
alembic upgrade head

# Создать новую миграцию (после изменения моделей)
alembic revision --autogenerate -m "description"

# Откатить последнюю миграцию
alembic downgrade -1
```

## 6. Запуск сервера

```bash
uvicorn app.main:app --reload
```

Сервер запустится на `http://localhost:8000`.

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 7. Остановка PostgreSQL

```bash
docker compose down
# С удалением данных:
docker compose down -v
```

## Зависимости (requirements.txt)

```
fastapi==0.128.8
sqlmodel==0.0.14
alembic==1.12.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
bcrypt==4.1.2
passlib==1.7.4
email-validator==2.3.0
python-multipart==0.0.20
httpx==0.25.1
pytest==7.4.3
pytest-asyncio==0.21.1
uvicorn[standard]==0.24.0
mkdocs==1.6.1
mkdocs-material==9.7.6
```
