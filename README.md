# URL Shortener API

Сервис для сокращения ссылок с возможностью аналитики и управления. Проект разработан на FastAPI с использованием PostgreSQL и Redis.

### Деплой на Render
1. **Создать аккаунт** на [render.com](https://render.com)
2. **Создать новый Web Service** и подключить GitHub репозиторий
3. **Выбрать окружение** `Docker`
4. **Добавить переменные окружения:**
   - `DATABASE_URL` (получить после создания PostgreSQL)
   - `SECRET_KEY` (сгенерировать случайную строку)
   - `BASE_URL` (URL вашего сервиса)
5. **Создать PostgreSQL базу данных** в том же регионе
6. **Нажать "Create Web Service"**

### Обязательные функции

| Функция | Эндпоинт | Описание |
|---------|----------|----------|
| **Создание короткой ссылки** | `POST /links/shorten` | Создает короткую ссылку из оригинального URL |
| **Редирект по короткой ссылке** | `GET /links/{short_code}` | Перенаправляет на оригинальный URL |
| **Обновление ссылки** | `PUT /links/{short_code}` | Изменяет оригинальный URL для существующей короткой ссылки |
| **Удаление ссылки** | `DELETE /links/{short_code}` | Удаляет короткую ссылку (только для владельца) |
| **Статистика по ссылке** | `GET /links/{short_code}/stats` | Показывает клики, дату создания, последнее использование |
| **Кастомные ссылки** | `POST /links/shorten` | Создание ссылки с уникальным alias (поле `custom_alias`) |
| **Поиск по оригинальному URL** | `GET /links/search?original_url={url}` | Ищет ссылки по части URL |
| **Время жизни ссылки** | `POST /links/shorten` | Параметр `expires_at` для автоматического удаления |

### Дополнительные функции

| Функция | Эндпоинт | Описание |
|---------|----------|----------|
| **Удаление неиспользуемых ссылок** | `DELETE /links/cleanup/unused` | Деактивирует ссылки без переходов за N дней |
| **История истекших ссылок** | `GET /links/expired/history` | Показывает все ссылки с истекшим сроком |

### Кэширование

| Функция | Технология | Описание |
|---------|------------|----------|
| **Кэширование популярных ссылок** | Redis | TTL 1 час для быстрого доступа |
| **Кэширование статистики** | Redis | TTL 5 минут |
| **Очистка кэша** | Redis | Автоматически при обновлении/удалении |

### Регистрация и авторизация

| Функция | Эндпоинт | Описание |
|---------|----------|----------|
| **Регистрация** | `POST /register` | Создание нового пользователя |
| **Получение токена** | `POST /token` | JWT токен для авторизации |
| **Информация о себе** | `GET /users/me` | Данные текущего пользователя |
| **Тест авторизации** | `GET /test-auth` | Проверка работоспособности токена |

#### Регистрация нового пользователя
**Запрос:**
```bash
curl -X POST https://project3-e9y2.onrender.com/register \
  -H "Content-Type:application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

**Ответ:**

```json
{
  "email": "user@example.com",
  "username": "testuser",
  "id": 1,
  "created_at": "2026-03-15T16:55:16.197384+00:00"
}
```

#### Получение токена
**Запрос:**

```bash
curl -X POST https://project3-e9y2.onrender.com/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```
**Ответ:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc3MzU5NDY5OX0.ZujF33T-Guy9kRu0QdTiwlKvP103LcDkvXPFfQNPWio",
  "token_type": "bearer"
}
```

#### Создание обычной ссылки (без авторизации)
**Запрос:**

```bash
curl -X POST https://project3-e9y2.onrender.com/links/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://google.com"
  }'
```
**Ответ:**

```json
{
  "short_code": "Hnl7vi",
  "original_url": "https://google.com",
  "short_url": "https://project3-e9y2.onrender.com/Hnl7vi",
  "created_at": "2026-03-15T14:45:04.799540+00:00",
  "expires_at": null,
  "is_active": true
}
```

#### Создание кастомной ссылки (с авторизацией)
**Запрос:**

```bash
curl -X POST https://project3-e9y2.onrender.com/links/shorten \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc3MzU5NDY5OX0.ZujF33T-Guy9kRu0QdTiwlKvP103LcDkvXPFfQNPWio" \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://yandex.ru",
    "custom_alias": "myyandex"
  }'
```
**Ответ:**

```json
{
  "short_code": "myyandex",
  "original_url": "https://yandex.ru",
  "short_url": "https://project3-e9y2.onrender.com/myyandex",
  "created_at": "2026-03-15T14:48:46.158897+00:00",
  "expires_at": null,
  "is_active": true
}
```

#### Удаление ссылки
**Запрос:**

```bash
curl -X DELETE https://project3-e9y2.onrender.com/links/myyandex \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc3MzU5NDY5OX0.ZujF33T-Guy9kRu0QdTiwlKvP103LcDkvXPFfQNPWio"
```
**Ответ:** код 204 (No Content), без тела ответа
