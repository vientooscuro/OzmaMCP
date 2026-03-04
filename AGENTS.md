# AGENTS.md — OzmaDB (FunDB) / FunQL / REST API (wiki.ozma.io)

> Этот файл — «памятка для агента»: как устроена OzmaDB (FunDB), как писать FunQL, и как безопасно/эффективно работать с REST API.
> Основано на публичной документации wiki.ozma.io (ссылки — в конце каждого раздела).
> 
> ⚠️ Важно: это **не** копия «всей документации слово-в-слово» (она слишком объёмная и регулярно меняется). Это **полное по покрытию** описание возможностей и интерфейсов, в формате, который удобно скармливать LLM‑агенту.

---

## 0) Термины и «карта мира»

- **FunDB** — база данных ozma.io. Она выполняет запросы, хранит данные, проверяет права доступа и т.д. Метаданные (схемы/сущности/поля/роли) тоже хранятся как данные в системных таблицах. citeturn0search0
- **FunQL** — язык запросов (DQL‑часть SQL на базе PostgreSQL `SELECT` + расширения: функции/атрибуты/доп.операторы). citeturn6view0
- **FunDB API** — публичный **REST API** для чтения, транзакций (insert/update/delete), запуска экшнов и служебных операций (check_access, layouts). citeturn5view0
- **User view (отображение)** — сохранённый (именованный) FunQL‑запрос в `public.user_views`, либо «анонимный» запрос, переданный в API на лету. citeturn1view0turn5view0
- **Экшны (actions)** — серверные JS‑процедуры в транзакции, с доступом к FunDB API, ограниченным ролью вызывающего пользователя. citeturn7view0turn1view0
- **Триггеры (triggers)** — серверные JS‑обработчики до/после insert/update/delete, могут менять `args` операции или отменять операцию. citeturn8view0turn1view0

---

## 1) Архитектура FunDB: метаданные как данные

### 1.1 Системные поля каждой записи
- `id` — числовой PK (есть всегда).
- `sub_entity` — служебное поле для наследования/подтипов (запрос значения может быть «медленным», лучше использовать `OFTYPE`/`INHERITED FROM` или виртуальные поля). citeturn0search0turn6view0

### 1.2 Системные таблицы (схема `public`)
Ключевые таблицы конфигурации (упрощённо):
- `public.schemas` — список схем.
- `public.entities` — сущности (таблицы), включая наследование (`parent_id`), «главное поле» (`main_field`), абстрактность (`is_abstract`), заморозка (`is_frozen`), `save_restore_key`. citeturn0search0
- `public.column_fields` — реальные поля (тип, nullable, default на FunQL, immutable). citeturn0search0
- `public.computed_fields` — вычисляемые поля (expression на FunQL, virtual/materialized). citeturn0search0
- `public.unique_constraints`, `public.check_constraints`, `public.indexes` — ограничения/индексы. citeturn0search0
- `public.user_views`, `public.user_view_generators` — именованные запросы и генераторы (JS). citeturn0search0
- `public.fields_attributes` — атрибуты по умолчанию для полей (подмешиваются в запросы). citeturn0search0
- `public.actions`, `public.triggers` — экшны и триггеры (JS‑код). citeturn1view0turn7view0turn8view0
- `public.roles`, `public.role_parents`, `public.role_entities`, `public.role_column_fields` — модель ролей и ограничений. citeturn1view0
- `public.users` — пользователи и их роли. citeturn1view0
- `public.events` — журнал событий (операции, ошибки, пользователь, источник api/trigger и т.д.). citeturn1view0

### 1.3 Наследование сущностей
- `entities.parent_id` задаёт «таблицу‑родителя»: запросы по родителю видят записи детей; дети имеют поля родителя + свои. citeturn0search0
- Для проверки типа — FunQL выражения `INHERITED FROM` и `OFTYPE` (см. раздел FunQL). citeturn6view0

---

## 2) FunQL: что реально поддерживается и как писать запросы

### 2.1 Структура FunQL запроса
FunQL запрос может начинаться с объявления аргументов:

```sql
{ $id reference(usr.orders) }:
select ...
```

и затем обычный `select` + опционально `for insert into ...` для выбора «главной сущности». citeturn6view0

**Ключевые правила:**
- FunQL — это в основном PostgreSQL‑подобный `select`, но поддержка SQL неполная (язык развивается). citeturn6view0
- Схему по умолчанию указать нельзя — таблицы всегда со схемой (`public.entities`, `usr.orders` и т.п.). citeturn6view0

### 2.2 Типы данных
Поддержаны (в документации): `string`, `int` (32‑бит), `decimal`, `bool`, `date`, `datetime` (в запросах UTC), `interval`, `array(...)` (без вложенности), `json` (литералы с выражениями), `uuid`, `reference(entity)`, `enum(...)`. citeturn6view0

### 2.3 Аргументы (params) и безопасность
- Аргументы объявляются в `{ ... }:` и используются как `$arg_name`. Можно задавать `DEFAULT` и `NULL` (опциональность). citeturn6view0
- **Рекомендация для агента:** всегда передавайте значения через аргументы (а не строковой конкатенацией в `__query`) — это даёт кэширование и защищает от инъекций. citeturn5view0
- Есть **глобальные аргументы** `$$lang`, `$$user`, `$$user_id`, `$$transaction_time`. citeturn6view0

### 2.4 SELECT: поддерживаемый синтаксис (вкратце)
Поддержаны:
- `select ... from ... where ...`
- `union/intersect/except` (с `all/distinct`)
- `group by`, `order by`, `limit`, `offset`
- `join`: `join`, `left join`, `right join`
- `values (...)` как источник
- Подзапросы `(...) as alias` citeturn6view0

### 2.5 Атрибуты (самое «озмовское»)
Атрибуты управляют отображением результатов (в FunApp и в API‑метаданных).

- **Атрибуты строки / запроса:** `@name = expr` (если expr не использует значения ячеек — это атрибут всего запроса). citeturn6view0
- **Атрибуты ячейки / колонки:** `col @{ name = expr, ... }` (без ссылок на ячейки — «атрибуты колонки»). citeturn6view0
- **Чистые атрибуты:** при `info` (и при создании новых записей) вычисляются только атрибуты без ссылок на реальные данные/аргументы. Поэтому UI «для new» может отличаться от UI «для existing». citeturn6view0

### 2.6 «Отслеживание источников» и редактирование из результата
FunQL отслеживает, какие колонки результата соответствуют реальным полям, чтобы FunApp мог редактировать значения прямо из таблицы результата.
- Если колонка выбрана «как есть», её можно редактировать; если над ней есть выражение (`foo + 0`), она неотслеживаемая. citeturn6view0
- Вычисляемые поля (computed_fields) не редактируются. citeturn6view0turn0search0

### 2.7 Главная сущность и `for insert into`
`for insert into schema.entity` позволяет UI (и API‑метаданным) понимать, что это «форма/таблица для сущности», и включать режим создания записей.
Сущность считается «выделяемой», если она одна в `from`, либо в правильной позиции `left/right join`, либо единственная в подзапросе. citeturn6view0

### 2.8 Операторы и функции
Поддержаны основные логические/арифметические/сравнения/`case`, `coalesce`, `::`, JSON `->`/`->>` и т.д. citeturn6view0  
Агрегаты: `sum`, `avg`, `min`, `max`, `count`, `bool_and`. citeturn6view0  
Есть список «разрешённых» функций (математика, строки, дата/время, форматирование) — ориентируйтесь на раздел FunQL. citeturn6view0

### 2.9 Расширения FunQL, важные для агента
- **Ссылки на user view:** `&schema.view_name` (валидируются). citeturn6view0
- **Разыменование reference:** оператор `=>` позволяет идти по связям (`field=>other_field=>name`). Ограничение: нельзя в `join ... on`. citeturn6view0
- **Привилегированный доступ:** `FROM ... WITH SUPERUSER ROLE` и `!` для колонок — отключают ограничения ролей (опасно, можно утечь данными). citeturn6view0
- **Наследование и типизация:** `INHERITED FROM` и `OFTYPE` (в доке рядом ещё упоминается `TYPEOF`). Используйте `INHERITED FROM` как более устойчивый вариант при расширении иерархий. citeturn6view0
- **Чтение атрибутов:** `.@` (из поля/значения) и `.@@` (из сущности/таблицы). citeturn6view0

---

## 3) REST API FunDB: как общаться с базой

### 3.1 Базовый URL и формат
- Базовый адрес: `https://ИМЯ_БАЗЫ.api.ozma.org` citeturn5view0
- Тело (когда нужно) — JSON + `Content-type: application/json`. citeturn5view0
- Ошибки возвращаются JSON’ом с полями `type` и `message`. citeturn5view0

### 3.2 Авторизация (OIDC)
- Авторизация по OIDC; чтобы получить `client_id`/`client_secret`, в доке предлагается писать на support email. citeturn5view0
- Конфиг: `.../.well-known/openid-configuration`
- Токен: `.../protocol/openid-connect/token` (password grant), затем `Authorization: Bearer <token>` в запросах к API. citeturn5view0
- Проверка доступа: `GET /check_access` (200 — доступ есть; 404 — инстанса нет). citeturn5view0

### 3.3 Чтение данных: views (именованные и анонимные)
**Пути:**
- Именованное: `/views/by_name/<schema>/<view_name>`
- Анонимное: `/views/anonymous?__query=<funql>` citeturn5view0

**Данные:**
- `GET <view_path>/entries` → `IViewExprResult` (данные + метаданные). citeturn5view0
- Аргументы передаются как query params и **кодируются JSON’ом** (пример: строка как `foo="value"`). citeturn5view0

**Метаданные:**
- `GET <view_path>/info` → `IViewInfoResult`. citeturn5view0

Документация приводит TS‑типы результата (domains/columns/valueType/attributes/entityIds и т.д.) — это важно для клиентов, которые хотят:
- рендерить UI сами,
- понимать типы,
- понимать, какие колонки редактируемы/откуда происходят. citeturn5view0

### 3.4 Изменение данных: транзакции
- `POST /transaction` с телом `ITransaction { operations: [...] }` citeturn5view0
- Операции:
  - `insert` (`entity`, `entries`)
  - `update` (`entity`, `id`, `entries`)
  - `delete` (`entity`, `id`) citeturn5view0
- Ответ: `ITransactionResult { results: [...] }` (insert возвращает `id`). citeturn5view0

**Семантика:**
- Всё исполняется атомарно «в одной транзакции». citeturn5view0
- Триггеры `BEFORE/AFTER` могут модифицировать `args` или отменять операцию (см. раздел триггеров). citeturn8view0

### 3.5 Запуск экшнов (server-side procedures)
- `POST /actions/<schema>/<action_name>/run` + JSON‑args → в ответе `{ result: ... }`. citeturn5view0
- Экшн может вернуть:
  - `{ ok: true }`,
  - ссылку на user view / навигационный объект (для UI),
  - вызов другого экшна (в другой транзакции). citeturn7view0turn5view0

### 3.6 Экспорт/импорт схем (layouts)
- `GET /layouts` (в доке — zip) и `PUT /layouts` для загрузки схем на другой инстанс. citeturn5view0

---

## 4) Серверная логика: экшны и триггеры

### 4.1 Экшны (actions)
- Хранятся в `public.actions`.
- Это ECMAScript‑модуль с `export default async function ...`.
- Работает внутри транзакции; доступ к данным через API FunDB (`FunDB.getUserView`, `insertEntity`, `updateEntity`, `deleteEntity`, и т.д. — см. примеры). citeturn7view0
- Права экшна ограничены ролью пользователя, который его вызвал. citeturn7view0turn1view0

**Практические паттерны для агента:**
- Для чтения внутри экшна используйте `getUserView` с анонимным запросом и аргументами.
- Для массовых изменений делайте несколько операций insert/update/delete — всё откатится при исключении. citeturn7view0

### 4.2 Триггеры (triggers)
- Хранятся в `public.triggers`, настраиваются по сущности и операциям insert/update/delete, с `BEFORE/AFTER`, приоритетом, и списком полей для `on_update_fields`. citeturn8view0
- Аргументы триггера:
  - `event` (сущность, время, источник и id/newId),
  - `args` (новые/изменённые значения). citeturn8view0
- Возвращаемое значение:
  - `args` (чтобы модифицировать значения),
  - `true` (ничего не менять),
  - `false` (отменить операцию, но транзакция продолжится). citeturn8view0

**Важно для агента:**
- `BEFORE INSERT`: `newId` ещё нет.
- `AFTER INSERT`: `newId` доступен в `event.source.newId`. citeturn8view0
- Триггер может создавать/обновлять/удалять связанные записи (пример с созданием people и communication_ways). citeturn8view0

---

## 5) Модель доступа (roles) и ограничения

FunDB ограничивает доступ на уровне:
- сущности (таблицы): `role_entities` с правилами `select/update/delete` как выражения FunQL + `insert` флаг + `check` проверка изменений,
- поля: `role_column_fields` с ограничениями `select` и `change`. citeturn1view0

**Наследование ролей** возможно через `role_parents`. citeturn1view0

**Агенту важно:**
- Ошибки «нет прав» могут проявляться как пустые выборки, ошибки транзакций, невозможность изменить поле.
- В FunQL есть механизм «привилегированных» таблиц/полей (`WITH SUPERUSER ROLE`, `!`), но это должно использоваться только администратором и осознанно. citeturn6view0

---

## 6) Логи событий и диагностика

- `public.events` логирует транзакции/операции: время, user, источник (`api`/`trigger`), тип события, сущность, id, детали, ошибки. citeturn1view0
- Для отладки часто полезно:
  - воспроизвести запрос через анонимный view,
  - проверить роль пользователя,
  - посмотреть события по `transaction_time/transaction_id`. citeturn1view0

---

## 7) Рекомендации для LLM‑агента: как работать «правильно»

### 7.1 Минимальный безопасный алгоритм чтения
1) Если view известен и часто используется → предпочесть **именованный view** (`/views/by_name/...`) ради кэширования. citeturn5view0  
2) Передавать параметры только как аргументы view (query params, JSON‑кодирование), не инлайнить значения в FunQL строку. citeturn5view0  
3) Если нужен только UI/типы/атрибуты без данных → `GET .../info`.

### 7.2 Минимальный безопасный алгоритм записи
1) Все изменения группировать в `POST /transaction` (atomic). citeturn5view0  
2) Учитывать, что триггеры могут:
   - добавить/переопределить значения (`BEFORE`),
   - выполнить дополнительную логику (`AFTER`),
   - отменить операцию. citeturn8view0  
3) Обрабатывать ошибки как JSON `{ type, message }`. citeturn5view0

### 7.3 Производительность
- Индексы задаются в `public.indexes`, поддержаны `btree/gist/gin` и класс операторов `trgm` (pg_trgm) для строк. citeturn0search0
- Если query используется часто — сделать именованный view и использовать аргументы (кэширование). citeturn5view0
- `sub_entity` напрямую читать не рекомендуется (может быть «медленно»); лучше типовые операторы. citeturn0search0turn6view0

### 7.4 Предсказуемость UI (атрибуты)
- Если агент генерирует запрос для FunApp: держите в голове «чистые атрибуты» — иначе `info/new` режим может визуально «сломаться». citeturn6view0

---

## 8) Шпаргалка: ключевые эндпоинты

- **Проверка доступа / существования инстанса:** `GET /check_access` citeturn5view0  
- **Named view:** `/views/by_name/<schema>/<view>` citeturn5view0  
- **Anonymous view:** `/views/anonymous?__query=<funql>` citeturn5view0  
- **Получить данные:** `GET <view>/entries` citeturn5view0  
- **Получить метаданные:** `GET <view>/info` citeturn5view0  
- **Транзакция:** `POST /transaction` citeturn5view0  
- **Запуск экшна:** `POST /actions/<schema>/<name>/run` citeturn5view0  
- **Layouts export/import:** `GET /layouts`, `PUT /layouts` citeturn5view0  

---

## 9) Источники (основные страницы wiki.ozma.io)

- FunDB (структура системных таблиц, роли, events и т.д.) citeturn0search0turn1view0  
- FunDB API интерфейс (OIDC, views, transaction, actions, check_access, layouts) citeturn5view0  
- FunQL (синтаксис, типы, атрибуты, глобальные args, операторы/функции, =>, inherited, .@/.@@, superuser) citeturn6view0  
- Экшны (actions) citeturn7view0  
- Триггеры (triggers) citeturn8view0  
