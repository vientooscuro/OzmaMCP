# OzmaMCP — MCP server for OzmaDB (FunDB)

MCP-сервер для работы с OzmaDB через REST API. Подключается к Claude Code, Codex и любому другому MCP-совместимому клиенту.

## Возможности

| Tool | Описание |
|------|----------|
| `check_access` | Проверить доступность инстанса и валидность токена |
| `validate_funql` | Preflight-проверка FunQL (resolve/валидация без записи) |
| `funql_query` | Выполнить произвольный FunQL SELECT запрос |
| `named_view_query` | Получить данные из именованного user view |
| `named_view_info` | Получить метаданные (колонки, типы) именованного view |
| `list_user_views` | Показать доступные именованные user view (для диагностики 404) |
| `get_user_view_query` | Получить исходный FunQL-текст именованного user view (`limit`/`offset` поддерживаются) |
| `transaction` | Выполнить атомарную транзакцию (insert / update / delete) |
| `run_action` | Запустить серверный action |
| `list_schemas` | Список схем в базе |
| `list_entities` | Список сущностей (таблиц) в схеме |
| `list_entity_fields` | Список полей сущности (column + computed) |
| `search_in_metadata` | Поиск подстроки в метаданных схемы (expressions/defaults/role rules/views) |
| `where_used_field` | Точечный поиск использования поля по `schema/entity/field` в views/actions/triggers/metadata |
| `safe_update_view_query` | Безопасный replace в `public.user_views.query` с dry-run и валидацией |
| `upsert_computed_field` | Создание/обновление computed field с pre-check конфликтов в наследовании |

## Установка

```bash
cd /путь/к/OzmaMCP
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Конфигурация

Сервер читает настройки из переменных окружения:

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `OZMA_API_BASE` | `https://ozma.gogol.school/api/` | Базовый URL API |
| `OZMA_AUTH_URL` | `https://ozma.gogol.school/auth/realms/ozma/...` | URL получения токена |
| `OZMA_CLIENT_ID` | `ozmadb` | OIDC client_id |
| `OZMA_CLIENT_SECRET` | *(пусто)* | OIDC client_secret |
| `OZMA_USERNAME` | *(пусто)* | Логин пользователя |
| `OZMA_PASSWORD` | *(пусто)* | Пароль пользователя |

## Подключение к Claude Code

Добавить в `~/.claude.json` (или через `claude mcp add`):

```json
{
  "mcpServers": {
    "ozma": {
      "command": "/путь/к/OzmaMCP/.venv/bin/python",
      "args": ["-m", "ozma_mcp.server"],
      "env": {
        "OZMA_API_BASE": "https://ваш-инстанс.api.ozma.org/",
        "OZMA_AUTH_URL": "https://account.ozma.io/auth/realms/default/protocol/openid-connect/token",
        "OZMA_CLIENT_ID": "ваш-client-id",
        "OZMA_CLIENT_SECRET": "ваш-secret",
        "OZMA_USERNAME": "user@example.com",
        "OZMA_PASSWORD": "пароль"
      }
    }
  }
}
```

Или через CLI:

```bash
claude mcp add ozma \
  /путь/к/OzmaMCP/.venv/bin/python -m ozma_mcp.server \
  -e OZMA_API_BASE=https://ваш-инстанс.api.ozma.org/ \
  -e OZMA_CLIENT_ID=ваш-client-id \
  -e OZMA_CLIENT_SECRET=ваш-secret \
  -e OZMA_USERNAME=user@example.com \
  -e OZMA_PASSWORD=пароль
```

## Подключение к Codex (OpenAI)

В `.codex/config.yaml` или `codex.yaml`:

```yaml
mcp_servers:
  ozma:
    command: /путь/к/OzmaMCP/.venv/bin/python
    args: ["-m", "ozma_mcp.server"]
    env:
      OZMA_API_BASE: "https://ваш-инстанс.api.ozma.org/"
      OZMA_CLIENT_ID: "ваш-client-id"
      OZMA_CLIENT_SECRET: "ваш-secret"
      OZMA_USERNAME: "user@example.com"
      OZMA_PASSWORD: "пароль"
```

## Примеры использования

### FunQL запрос
```
Используй funql_query:
  query: "select id, name, email from usr.customers where active = true limit 10"
```

Важно: в FunQL не поддерживается `SELECT *`. Нужно перечислять колонки явно.

### Валидация FunQL перед сохранением
```
Используй validate_funql:
  query: "select id, name from base.contacts where id = $id"
  params: {id: 1}
```

### Вставка записи
```
Используй transaction:
  operations:
    - type: insert
      entity: {schema: usr, name: orders}
      entries: {customer_id: 42, amount: 1500, status: "new"}
```

### Обновление записи
```
Используй transaction:
  operations:
    - type: update
      entity: {schema: usr, name: orders}
      id: 101
      entries: {status: "paid"}
```

### Удаление
```
Используй transaction:
  operations:
    - type: delete
      entity: {schema: usr, name: orders}
      id: 101
```

### Запуск action
```
Используй run_action:
  schema: usr
  action_name: send_invoice
  args: {order_id: 101}
```

### Безопасная правка user view query
```
Используй safe_update_view_query:
  schema: crm
  view_name: announced_classes_table
  from_text: "contact=>desired_name"
  to_text: "contact=>desired_full_name"
  dry_run: true
```

### Upsert computed field
```
Используй upsert_computed_field:
  schema: base
  entity: contacts
  field_name: desired_full_name
  expression: "''"
  is_virtual: true
```

## Накопленные знания (Ozma schema specifics)

- Для computed field с одинаковым именем в родителе и потомке:
  - если поле в потомке `is_virtual = false`, Ozma может вернуть конфликт имён;
  - если поле в потомке `is_virtual = true`, одноимённые поля в `contacts` и `people` допускаются.
- Проверенный кейс `desired_full_name`:
  - `base.contacts.desired_full_name` можно держать как `expression = ''`, `is_virtual = true`;
  - `base.people.desired_full_name` можно переопределять своей формулой при `is_virtual = true`.
- При правках `public.user_views.query` Ozma валидирует выражения сразу: ссылка на несуществующее поле (например, `contact=>desired_full_name` при отсутствии поля у `base.contacts`) отклоняет миграцию.
