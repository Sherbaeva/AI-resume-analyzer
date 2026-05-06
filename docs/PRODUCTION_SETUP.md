# ATS — Production Setup Guide

Сервер: `46.225.184.221` · Ubuntu 24.04 · Docker + Nginx

---

## 1. Первый деплой

```bash
# Клонируем репозиторий
git clone https://gitlab.com/bratskayapomosh/resume-analyzer-for-efficient-hiring.git
cd resume-analyzer-for-efficient-hiring

# Создаём конфиг продакшена
cp .env.prod.example .env.prod
nano .env.prod          # заполнить все CHANGE_ME

# Поднимаем сервисы
docker-compose -f docker-compose.prod.yml up --build -d

# Проверяем
docker ps
curl http://localhost:8000/health
```

Миграции + bootstrap (создание admin + permissions) запускаются **автоматически** через `entrypoint.sh`.

---

## 2. .env.prod — обязательные переменные

```env
# ─── БД ───────────────────────────────────────────
POSTGRES_USER=ats_user
POSTGRES_PASSWORD=<сильный пароль>
POSTGRES_DB=ats_db
DATABASE_URL=postgresql+asyncpg://ats_user:<пароль>@postgres:5432/ats_db

# ─── JWT ──────────────────────────────────────────
JWT_SECRET=<openssl rand -hex 32>
JWT_ALG=HS256
JWT_EXPIRES_MIN=60

# ─── Admin ────────────────────────────────────────
ADMIN_BOOTSTRAP_EMAIL=admin@company.com
ADMIN_BOOTSTRAP_PASSWORD=<сильный пароль>

# ─── MinIO ────────────────────────────────────────
S3_BUCKET_NAME=ats-resumes
S3_ACCESS_KEY=<логин>
S3_SECRET_KEY=<сильный пароль>
S3_ENDPOINT_URL=http://minio:9000
S3_REGION=us-east-1

# ─── n8n ──────────────────────────────────────────
N8N_WEBHOOK_URL=http://n8n:5678/webhook/resume-analyze
N8N_SECRET=<секрет для callback>
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<сильный пароль>

# ─── App ──────────────────────────────────────────
ENVIRONMENT=production
BACKEND_URL=http://46.225.184.221
ALLOWED_ORIGINS=http://46.225.184.221,https://yourfrontend.com
MAX_UPLOAD_MB=10
```

Сгенерировать `JWT_SECRET`:
```bash
openssl rand -hex 32
```

---

## 3. Nginx

Конфиг уже есть в `nginx/ats.conf`. Подключить:

```bash
sudo cp nginx/ats.conf /etc/nginx/sites-available/ats
sudo ln -s /etc/nginx/sites-available/ats /etc/nginx/sites-enabled/ats
sudo rm -f /etc/nginx/sites-enabled/default   # убрать дефолтный
sudo nginx -t                                  # проверить конфиг
sudo systemctl reload nginx
```

Проверить что API теперь только через Nginx:
```bash
curl http://46.225.184.221/health        # ✅ должен отвечать
curl http://46.225.184.221:8000/health   # ❌ должен timeout
```

---

## 4. PostgreSQL

Всё запускается внутри Docker — снаружи порт не открыт.

```bash
# Войти в psql
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U ats_user -d ats_db

# Проверить миграции
docker-compose -f docker-compose.prod.yml exec api alembic current
# Ожидаемый вывод: 002_auth_rbac (head)

# Смотреть таблицы
\dt
```

Сбросить и пересоздать БД (осторожно!):
```bash
docker-compose -f docker-compose.prod.yml down
docker volume rm resume-analyzer-for-efficient-hiring_postgres_data
docker-compose -f docker-compose.prod.yml up -d
```

---

## 5. MinIO

**Консоль:** `http://46.225.184.221:9101`  
Логин = `S3_ACCESS_KEY`, пароль = `S3_SECRET_KEY` из `.env.prod`

Бакет `ats-resumes` создаётся автоматически при первой загрузке. Чтобы создать вручную:
1. Открыть консоль → **Buckets → Create Bucket**
2. Имя: `ats-resumes`
3. Нажать **Create**

> ⚠️ Порт 9101 (консоль) доступен снаружи. После настройки закрой его через UFW:
> ```bash
> sudo ufw deny 9101
> ```
> Дальше заходить через SSH-туннель:
> ```bash
> ssh -L 9101:localhost:9101 root@46.225.184.221
> # Потом открыть http://localhost:9101
> ```

---

## 6. n8n

**Адрес:** `http://46.225.184.221:5678`  
Логин/пароль = `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD`

### Настройка workflow

1. Открыть существующий workflow (или создать новый)
2. **Webhook узел:**
   - Method: `POST`
   - Path: `resume-analyze`
   - После сохранения нажать **Activate** — переключатель сверху справа
3. **HTTP Request узел** (callback в backend):
   ```
   Method:  POST
   URL:     http://api:8000/api/internal/analysis-callback
   Headers: X-N8N-SECRET: <значение N8N_SECRET из .env.prod>
   ```
4. Убедиться что workflow **активен** (зелёный индикатор)

> ⚠️ На проде webhook URL: `/webhook/resume-analyze` (без `-test`)  
> В `.env.prod` это уже прописано: `N8N_WEBHOOK_URL=http://n8n:5678/webhook/resume-analyze`

---

## 7. Обновление (git pull → rebuild)

```bash
cd /root/resume-analyzer-for-efficient-hiring

# Подтянуть изменения
git pull origin develop

# Пересобрать только api (без downtime для БД/MinIO/n8n)
docker-compose -f docker-compose.prod.yml up --build -d api worker

# Проверить логи
docker-compose -f docker-compose.prod.yml logs api --tail=30
```

---

## 8. Полезные команды

```bash
# Статус контейнеров
docker ps

# Логи в реальном времени
docker-compose -f docker-compose.prod.yml logs -f api

# Перезапустить api
docker-compose -f docker-compose.prod.yml restart api

# Bootstrap вручную (если нужно пересоздать admin/permissions)
docker-compose -f docker-compose.prod.yml exec api python tools/bootstrap.py

# Войти в bash контейнера
docker-compose -f docker-compose.prod.yml exec api bash

# Удалить всё (БЕЗ volumes — данные останутся)
docker-compose -f docker-compose.prod.yml down

# Удалить всё ВМЕСТЕ с данными (опасно!)
docker-compose -f docker-compose.prod.yml down -v
```

---

## 9. Чеклист перед сдачей

- [ ] `.env.prod` заполнен, нет `CHANGE_ME`
- [ ] `JWT_SECRET` сгенерирован через `openssl rand -hex 32`
- [ ] `docker ps` — все контейнеры `Up (healthy)`
- [ ] `curl http://46.225.184.221/health` → `{"status":"ok"}`
- [ ] Вход в API: `POST /auth/login` возвращает токен
- [ ] MinIO консоль открывается, бакет `ats-resumes` существует
- [ ] n8n workflow активирован (зелёный)
- [ ] n8n callback URL: `http://api:8000/api/internal/analysis-callback`
- [ ] Порт `:8000` снаружи недоступен (только через Nginx)
