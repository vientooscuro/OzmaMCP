# OzmaMCP — MCP server for OzmaDB (FunDB)

MCP-сервер для работы с OzmaDB через REST API. Подключается к Claude Code, Codex и любому другому MCP-совместимому клиенту.

Также сервер публикует MCP resource с документацией по OzmaDB/FunQL из `AGENTS.md`, чтобы агент мог читать её напрямую через MCP.

Дополнительно сервер публикует разделы wiki.ozma.io как MCP resources из локального snapshot (`docs/wiki/*.md`), чтобы не делать HTTP-запросы к wiki при каждом чтении.

## Возможности

| Tool | Описание |
|------|----------|
| `check_access` | Проверить доступность инстанса и валидность токена |
| `validate_funql` | Preflight-проверка FunQL (resolve/валидация без записи) |
| `funql_query` | Выполнить произвольный FunQL SELECT запрос |
| `named_view_query` | Получить данные из именованного user view |
| `named_view_info` | Получить метаданные (колонки, типы) именованного view |
| `list_view_columns` | Получить фактический список колонок user view (рекомендуется перед запросами к `admin.*`) |
| `list_user_views` | Показать доступные именованные user view (для диагностики 404) |
| `get_user_view_query` | Получить исходный FunQL-текст именованного user view (`limit`/`offset` поддерживаются) |
| `transaction` | Выполнить атомарную транзакцию (insert / update / delete) |
| `run_action` | Запустить серверный action |
| `list_schemas` | Список схем в базе |
| `list_entities` | Список сущностей (таблиц) в схеме |
| `list_actions` | Список actions с `id/schema_name/action_name` |
| `list_triggers` | Список triggers с `id/schema_name/entity_name/trigger_name` |
| `list_entity_fields` | Список полей сущности (column + computed) |
| `search_in_metadata` | Поиск подстроки в метаданных схемы (expressions/defaults/role rules/views) |
| `where_used_field` | Точечный поиск использования поля по `schema/entity/field` в views/actions/triggers/metadata |
| `safe_update_view_query` | Безопасный replace в `public.user_views.query` с dry-run и валидацией |
| `safe_update_action_function` | Безопасный replace в `public.actions.function` с dry-run |
| `upsert_computed_field` | Создание/обновление computed field с pre-check конфликтов в наследовании |
| `analyze_module_performance` | Авто-анализ производительности JS-модуля из `admin.modules_table` |
| `analyze_action_performance` | Авто-анализ производительности OzmaDB action |
| `analyze_trigger_performance` | Авто-анализ производительности OzmaDB trigger |
| `analyze_user_view_performance` | Авто-анализ производительности FunQL-запроса именованного user view |

Примечание по модулям: module-tools (`list_modules`, `search_in_modules`, `get_module_code`) читают модули из user view `admin.modules_table` (`/views/by_name/admin/modules_table`), с fallback на entity-путь для старых схем.

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
| `OZMA_BRIEF_TOOL_META` | `true` | Сжимает `list_tools` (короткие описания, без `description` в inputSchema) |
| `OZMA_COMPACT_JSON` | `true` | Возвращает minified JSON в tool responses (меньше токенов) |
| `OZMA_TRIM_LONG_FIELDS` | `true` | Обрезает длинные строки и большие массивы в tool responses |
| `OZMA_MAX_ITEMS` | `50` | Максимум элементов массива в ответе tool |
| `OZMA_MAX_STRING_CHARS` | `1500` | Лимит символов для обычных строковых полей |
| `OZMA_MAX_CODE_CHARS` | `4000` | Лимит символов для длинных полей `code/query/expression/...` |
| `OZMA_DOC_COMPACT` | `true` | Обрезает длинные `read_resource` документы |
| `OZMA_DOC_MAX_CHARS` | `24000` | Лимит символов для одного resource документа |

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

### Прочитать документацию через MCP resource
```
Используй MCP resource:
  uri: ozma://docs/agents
```

URI ресурса фиксированный: `ozma://docs/agents` (mime type: `text/markdown`).

### Прочитать wiki-разделы через MCP resource
```
Используй MCP resource:
  uri: ozma://docs/wiki
```

Доступные URI:
- `ozma://docs/wiki` — индекс разделов
- `ozma://docs/wiki/full` — агрегированный bundle всех разделов
- `ozma://docs/wiki/funql`
- `ozma://docs/wiki/fundb`
- `ozma://docs/wiki/fundb-api`
- `ozma://docs/wiki/funapp/menu`
- `ozma://docs/wiki/funapp/table`
- `ozma://docs/wiki/funapp/form`
- `ozma://docs/wiki/funapp/board`
- `ozma://docs/wiki/funapp/tree`
- `ozma://docs/wiki/funapp/timeline`
- `ozma://docs/wiki/funapp/settings`
- `ozma://docs/wiki/color-variants`

Совместимость: также поддерживаются алиасы `funapp-menu`, `funapp-table`, `funapp-form`, `funapp-board`, `funapp-tree`, `funapp-timeline`, `funapp-settings`.

### Обновить локальный snapshot wiki
```bash
.venv/bin/python scripts/export_wiki_docs.py
```

После обновления snapshot MCP начнет отдавать новые тексты сразу (после рестарта сервера/сессии клиента).

### FunQL запрос
```
Используй funql_query:
  query: "select id, name, email from usr.customers where active = true limit 10"
```

Важно: в FunQL не поддерживается `SELECT *`. Нужно перечислять колонки явно.
И для алиасов используй `AS`: `from public.actions as a` (не `from public.actions a`).

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

`transaction` принимает и более свободные формы payload (для клиентов, которые не могут строго уложиться в схему):  
`{operations:[...]}`, `{payload:{operations:[...]}}`, `{"raw":"{\"operations\":[...]}"}`.

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

### Получить полный код action/trigger/view (без обрезки)
```
Используй get_action_code:
  schema: usr
  action_name: send_invoice
  full: true
```

Важно: в `public.actions` исходник action хранится в поле `function` (не `code`).

### Избежать ошибок по полям в `admin` user views
```
Используй list_view_columns:
  schema: admin
  view_name: user_views
```

Затем в последующих запросах используй только имена из `columns[].name`.

```
Используй get_trigger_code:
  trigger_id: 123
  full: true
```

```
Используй get_user_view_query:
  view_id: 456
  full: true
```

### Получить полный код модуля (`pl_report.mjs`)
```
Используй get_module_code:
  module_name: pl_report.mjs
  full: true
```

Или надёжно через id:
```
Используй list_modules
Используй get_module_code:
  module_id: <id>
  full: true
```

### Проанализировать модуль на производительность
```
Используй analyze_module_performance:
  module_name: pl_report.mjs
  include_snippets: true
  max_findings: 20
```

### Проанализировать action на производительность
```
Используй analyze_action_performance:
  schema: usr
  action_name: send_invoice
  include_snippets: true
  max_findings: 20
```

### Проанализировать trigger на производительность
```
Используй analyze_trigger_performance:
  schema: usr
  trigger_name: orders_before_insert
  include_snippets: true
  max_findings: 20
```

### Проанализировать user view на производительность
```
Используй analyze_user_view_performance:
  schema: usr
  view_name: orders_table
  include_snippets: true
  max_findings: 20
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

### Безопасная правка кода action (`public.actions.function`)
```
Используй safe_update_action_function:
  schema: sales
  action_name: publish_actions
  from_text: "const limit = 100"
  to_text: "const limit = 200"
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
