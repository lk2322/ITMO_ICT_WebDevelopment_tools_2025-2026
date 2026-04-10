# Аутентификация

## Обзор

Приложение использует JWT (JSON Web Tokens) для аутентификации пользователей. Реализация основана на `python-jose` для создания/верификации токенов и `passlib[bcrypt]` для хеширования паролей.

!!! note "Важно"
    Сторонние библиотеки для аутентификации (например, fastapi-users) не используются — JWT реализован вручную, как требуется в задании.

## Архитектура

```
Регистрация → Хеширование пароля → Сохранение в БД
Логин        → Проверка пароля   → Генерация JWT
Запрос       → Извлечение токена → Декодирование JWT → Получение пользователя
```

## Компоненты

### auth.py

Модуль отвечает за хеширование паролей и работу с JWT:

```python
# Хеширование пароля
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

```python
# JWT токены
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### dependencies.py

Зависимость FastAPI для получения текущего пользователя из JWT-токена:

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    username = payload.get("sub")
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

## Поток аутентификации

### 1. Регистрация

```
POST /auth/register
Body: {"email": "...", "username": "...", "password": "..."}
```

- Проверка уникальности email и username
- Хеширование пароля через bcrypt
- Сохранение пользователя в БД
- Возврат данных пользователя (без пароля)

### 2. Вход

```
POST /auth/login
Body (form-data): username=...&password=...
```

- Поиск пользователя по username
- Проверка пароля через `verify_password()`
- Генерация JWT-токена с `sub: username` и сроком действия
- Возврат `{"access_token": "...", "token_type": "bearer"}`

### 3. Защищённые запросы

```
GET /categories/
Headers: Authorization: Bearer <token>
```

- Извлечение токена из заголовка
- Декодирование JWT → получение `sub` (username)
- Поиск пользователя в БД
- Если пользователь найден — доступ разрешён
- Если нет — `401 Unauthorized`

## Переменные окружения

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `SECRET_KEY` | Секретный ключ для подписи JWT | — |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена (минуты) | 30 |
