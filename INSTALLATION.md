# 🚀 Установка и Запуск iGaming Anti-Fraud Platform

## 📋 Системные Требования

### Минимальные:
- **OS:** Ubuntu 20.04+ / macOS 11+ / Windows 10+ (с WSL2)
- **RAM:** 4 GB
- **CPU:** 2 cores
- **Disk:** 10 GB свободного места

### Рекомендуемые:
- **RAM:** 8 GB+
- **CPU:** 4+ cores
- **Disk:** 20 GB+ SSD

### Необходимое ПО:
- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **Git:** 2.30+
- **Python:** 3.11+ (для локальной разработки)
- **Node.js:** 18+ (для локальной разработки)
- **npm:** 9+ (для локальной разработки)

---

## 🎯 Быстрый Старт (Docker - Рекомендуется)

### Шаг 1: Клонирование репозитория

```bash
# Клонируйте репозиторий
git clone https://github.com/azdevteam1-prog/igaming-antifraud-platform.git

# Перейдите в директорию проекта
cd igaming-antifraud-platform
```

### Шаг 2: ⚠️ ВАЖНО - Удалите дублирующую директорию

```bash
# Удалите неиспользуемую директорию routers
cd backend/app
rm -rf routers/
cd ../..

# Закоммитьте изменения
git add -A
git commit -m "fix: remove duplicate routers directory"
```

### Шаг 3: Настройка окружения

```bash
# Создайте .env файл (опционально)
cp .env.example .env

# Отредактируйте .env если нужно
nano .env  # или используйте ваш редактор
```

### Шаг 4: Запуск с Docker Compose

```bash
# Запустите все сервисы
docker-compose up -d

# Проверьте статус контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### Шаг 5: Инициализация базы данных

```bash
# Примените миграции
docker-compose exec backend alembic upgrade head

# Загрузите начальные данные (правила fraud detection)
docker-compose exec backend python -m app.services.rules_engine
```

### Шаг 6: Доступ к приложению

✅ **Готово! Откройте в браузере:**

- 🌐 **Frontend:** http://localhost:5173
- 🔧 **Backend API:** http://localhost:8000
- 📚 **API Docs (Swagger):** http://localhost:8000/docs
- 📖 **API Redoc:** http://localhost:8000/redoc
- 🐘 **PostgreSQL:** localhost:5432 (user: `fraud`, password: `fraud123`, db: `frauddb`)
- 🗄️ **Redis:** localhost:6379

---

## 💻 Локальная Разработка (без Docker)

### Backend

```bash
# 1. Перейдите в директорию backend
cd backend

# 2. Создайте виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# 3. Установите зависимости
pip install --upgrade pip
pip install -r requirements.txt

# 4. Запустите PostgreSQL и Redis локально
# Вариант 1: Docker
docker run -d -p 5432:5432 -e POSTGRES_USER=fraud -e POSTGRES_PASSWORD=fraud123 -e POSTGRES_DB=frauddb postgres:15
docker run -d -p 6379:6379 redis:7-alpine

# Вариант 2: Установите PostgreSQL и Redis нативно
# Ubuntu/Debian:
sudo apt install postgresql redis-server
# macOS:
brew install postgresql@15 redis

# 5. Настройте переменные окружения
export DATABASE_URL="postgresql+asyncpg://fraud:fraud123@localhost:5432/frauddb"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-secret-key-here"

# 6. Примените миграции
alembic upgrade head

# 7. Загрузите начальные данные
python -m app.services.rules_engine

# 8. Запустите сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
# 1. Перейдите в директорию frontend
cd frontend

# 2. Установите зависимости
npm install

# 3. Запустите dev сервер
npm run dev

# Frontend будет доступен на http://localhost:5173
```

---

## 🧪 Тестирование

### Backend тесты

```bash
cd backend

# Запустите все тесты
pytest

# Запустите с coverage
pytest --cov=app --cov-report=html

# Откройте отчет
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Frontend тесты

```bash
cd frontend

# Запустите тесты
npm test

# E2E тесты
npm run test:e2e
```

---

## 🔧 Полезные Команды

### Docker

```bash
# Остановить все сервисы
docker-compose down

# Остановить и удалить volumes (все данные будут потеряны!)
docker-compose down -v

# Пересобрать контейнеры
docker-compose build

# Пересобрать и запустить
docker-compose up -d --build

# Просмотр логов конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Войти в контейнер
docker-compose exec backend bash
docker-compose exec db psql -U fraud -d frauddb
```

### Database

```bash
# Создать новую миграцию
docker-compose exec backend alembic revision --autogenerate -m "migration name"

# Применить миграции
docker-compose exec backend alembic upgrade head

# Откатить последнюю миграцию
docker-compose exec backend alembic downgrade -1

# Подключиться к БД
docker-compose exec db psql -U fraud -d frauddb
```

### Мониторинг

```bash
# Просмотр использования ресурсов
docker stats

# Проверка состояния контейнеров
docker-compose ps

# Проверка health check
curl http://localhost:8000/health
```

---

## 🐛 Устранение Неполадок

### Проблема: Backend не запускается

```bash
# Проверьте логи
docker-compose logs backend

# Убедитесь что БД запущена
docker-compose ps db

# Проверьте подключение к БД
docker-compose exec db psql -U fraud -d frauddb -c "SELECT 1;"
```

### Проблема: Frontend не собирается

```bash
# Очистите node_modules
cd frontend
rm -rf node_modules package-lock.json
npm install

# Пересоберите контейнер
docker-compose build frontend
```

### Проблема: Порты заняты

```bash
# Найдите процессы на портах
# Linux/macOS:
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Windows:
netstat -ano | findstr :5432

# Остановите процессы или измените порты в docker-compose.yml
```

### Проблема: Ошибки импорта ML библиотек

```bash
# Переустановите зависимости
cd backend
pip install --force-reinstall -r requirements.txt

# Или пересоберите Docker образ
docker-compose build --no-cache backend
```

---

## 📊 Мониторинг и Метрики

### Grafana + Prometheus (опционально)

```bash
# Запустите мониторинг
cd monitoring
docker-compose up -d

# Доступ:
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

---

## 🔐 Безопасность

### Для Production:

1. **Измените пароли БД** в `docker-compose.yml`
2. **Сгенерируйте SECRET_KEY:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. **Используйте HTTPS** (настройте reverse proxy: Nginx/Traefik)
4. **Настройте firewall**
5. **Включите аутентификацию** для всех endpoints

---

## 📚 Дополнительные Ресурсы

- **Документация API:** http://localhost:8000/docs
- **Анализ проекта:** [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 💡 Демо Данные

После запуска автоматически создаются:
- ✅ Тестовые правила fraud detection
- ✅ Симулятор транзакций (запускается в фоне)
- ✅ Примеры игроков и транзакций

Для остановки симулятора:
```bash
# Закомментируйте в backend/app/main.py:
# asyncio.create_task(run_simulator(broadcast_transaction))
```

---

## 🎉 Готово!

Теперь платформа запущена и готова к использованию!

**Логин:** admin@example.com  
**Пароль:** admin123

---

**Автор:** AI Team  
**Дата:** 22 апреля 2026  
**Локация:** Rīga, LV
