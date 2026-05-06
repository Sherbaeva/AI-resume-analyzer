# Frontend Integration Checklist — ATS Resume Analyzer

Пройтись по каждому пункту перед сдачей фичи.

---

## 🔐 Аутентификация (НОВОЕ в v2)

- [ ] При старте приложения проверять наличие токена в `localStorage`
- [ ] Если токен есть — сделать `GET /auth/me` для проверки валидности
- [ ] При `401` от любого запроса — перенаправить на `/login`
- [ ] **Никогда не хранить** токен в `sessionStorage` или cookies без `httpOnly`

### Логин
```ts
const { access_token } = await api.login(email, password);
localStorage.setItem("ats_token", access_token);
```

### Подключение к каждому запросу
```ts
headers: { "Authorization": `Bearer ${token}` }
```
- [ ] Вывести ошибку `"Неверный email или пароль"` при `401` на `/auth/login`
- [ ] При `403` — показать `"Недостаточно прав"` (не перенаправлять на логин)

### RBAC guard в UI
```ts
const me = await api.me();
if (!me.permissions.includes("taxonomy.manage")) {
  // скрыть/дизейблить кнопку "Создать скилл"
}
```
- [ ] Скрывать элементы UI на основе `me.permissions[]` (не только на основе `role`)
- [ ] Роли: `admin` · `hr` — не хардкодить логику только по role

### Токен и время жизни
- [ ] `expires_in` возвращается в секундах (по умолчанию 3600 = 1 час)
- [ ] Реализовать **тихий ре-логин**: если `GET /auth/me` вернул `401` — показать форму логина
- [ ] При явном logout — `POST /auth/logout` + удалить токен из storage

---

## ✅ Конфигурация

- [ ] `BASE_URL` вынесен в env-переменную (`.env.local` или аналог)
  ```
  VITE_API_URL=http://localhost:8000
  # или для прода:
  VITE_API_URL=https://api.yourapp.com
  ```
- [ ] CORS: backend уже разрешает все origins; в проде — ограничить до домена фронта

---

## ✅ Загрузка резюме

- [ ] Использовать `FormData` + `fetch` **без** ручного задания `Content-Type`
  (браузер сам выставит `multipart/form-data` с boundary)
- [ ] Валидировать тип файла на фронте перед отправкой: `.pdf`, `.docx`, `.txt`
- [ ] Показывать ошибку при `413` (слишком большой файл, >10MB)
- [ ] Показывать ошибку при `415` (неподдерживаемый тип)
- [ ] При повторной загрузке того же файла — база вернёт тот же `resume_id` (дедупликация по SHA-256)

---

## ✅ Создание анализа

- [ ] `POST /analyses` — **идемпотентный**: повторный вызов вернёт тот же `analysis_id`
- [ ] После `201` — немедленно начать поллинг `GET /analyses/{id}`

---

## ✅ Поллинг статуса

- [ ] Поллить `GET /analyses/{analysis_id}` каждые **1–2 секунды**
- [ ] Остановить поллинг при `status == "done"` или `status == "failed"`
- [ ] Обязательно реализовать **timeout** — если за N секунд статус не изменился, показать ошибку
- [ ] Использовать `clearInterval` / `clearTimeout` при размонтировании компонента
- [ ] Рекомендуемый паттерн:
  ```js
  const poll = setInterval(async () => {
    const res = await getAnalysis(analysisId)
    if (res.status === 'done' || res.status === 'failed') {
      clearInterval(poll)
      handleResult(res)
    }
  }, 2000)
  // Таймаут: отменить через 5 минут
  setTimeout(() => clearInterval(poll), 5 * 60 * 1000)
  ```

---

## ✅ Обработка статуса `failed`

- [ ] При `status == "failed"` — показать `error_message` пользователю
- [ ] `error_message` может быть `null` — обработать gracefully:
  ```js
  const msg = analysis.error_message ?? 'Анализ завершился с ошибкой'
  ```

---

## ⚠️ Парсинг JSON-полей (КРИТИЧНО)

Три поля приходят как **строки**, а не объекты. Их нужно явно парсить:

- [ ] `matched_skills_json` → `JSON.parse(analysis.matched_skills_json)`
- [ ] `missing_skills_json` → `JSON.parse(analysis.missing_skills_json)`
- [ ] `explanations_json`   → `JSON.parse(analysis.explanations_json)`

```js
// Безопасный хелпер:
function parseJsonField(value) {
  if (!value) return null
  try { return JSON.parse(value) } catch { return null }
}
```

- [ ] Все три поля могут быть `null` (когда `status != "done"`)

---

## ✅ Отображение результатов

- [ ] Сортировать результаты по `score` по убыванию (DESC):
  ```js
  results.sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
  ```
- [ ] `score` — число от 0 до 100 (например, `85.5`)
- [ ] `score` может быть `null` если анализ ещё не завершён

---

## ✅ Обработка 422 Validation Error

- [ ] API возвращает массив ошибок валидации:
  ```json
  { "detail": [{ "loc": ["body", "title"], "msg": "...", "type": "..." }] }
  ```
- [ ] Показывать поле `msg` для каждой ошибки

---

## ✅ Soft Delete резюме

- [ ] Удалённое резюме (`deleted_at != null`) → `GET /resumes/{id}` вернёт `404`
- [ ] После удаления — убрать резюме из UI

---

## 🔒 Внутренний endpoint — НЕ для фронта

- [ ] `/api/internal/analysis-callback` — только для n8n
- [ ] Требует `X-N8N-SECRET` заголовок
- [ ] **Фронт никогда не должен вызывать этот endpoint**
