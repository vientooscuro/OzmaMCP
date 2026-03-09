# Author Change Log (Daniil Nuzhdin)

Generated on: 2026-03-09
Author filter: Daniil Nuzhdin <vientooscuro@vientooscuro.ru>

## Repository: `/Users/vientooscuro/SyncFolder/ozmadb`

Total commits by author: 67

### Full commit log (hash | date | subject)

```text
2f6d5c1 | 2026-03-09 22:44:25 +0100 | Format F# files with fantomas
e988dd0 | 2026-03-09 22:39:39 +0100 | Improve JS bulk ops and event logging stability
b978e49 | 2026-03-09 22:21:58 +0100 | Fix request_lines_number empty chunk main id regression
ec73b82 | 2026-03-09 22:14:57 +0100 | Format Query.fs after request_lines_number fix
da87b19 | 2026-03-09 21:58:50 +0100 | Fix request_lines_number for empty filtered chunks
1ff7292 | 2026-03-09 19:48:20 +0100 | Format UserViews and Query with fantomas
93b6ac9 | 2026-03-09 19:41:28 +0100 | Add request_lines_number total semantics for chunked views
54b8036 | 2026-03-09 19:22:06 +0100 | Format OzmaQL files with fantomas
1bd4aaf | 2026-03-09 19:21:04 +0100 | Fix lock files for locked-mode restore in CI
aa7065d | 2026-03-09 19:18:13 +0100 | Improve OzmaQL compile/query/resolve/typecheck pipeline
1c9d434 | 2026-03-09 14:46:39 +0100 | Handle missing sequence drops and fix fired trigger table name
56aaf81 | 2026-03-09 14:35:40 +0100 | Format Compile.fs with fantomas
1e0ca3f | 2026-03-09 14:28:46 +0100 | Improve view_reference rendering metadata and pun propagation
e451605 | 2026-03-09 12:55:16 +0100 | Fix view_reference attribute to work without explicit const
415ba3c | 2026-03-08 23:46:02 +0100 | Fix postViewInfo handler binding
e686bf9 | 2026-03-08 23:38:37 +0100 | Format F# sources with fantomas
7ea901b | 2026-03-08 23:36:41 +0100 | Add ROUND(x, N) function overload
6ea94e6 | 2026-03-08 23:29:52 +0100 | Enforce exactly-once semantics for time triggers
4b3341f | 2026-03-08 23:06:12 +0100 | Add BETWEEN/NOT BETWEEN operator to OzmaQL
73172e3 | 2026-03-08 22:50:22 +0100 | Fix time trigger rescheduling for stale datetime updates
4286e79 | 2026-03-08 18:55:37 +0100 | Remove non-trivial default from outbox due_at
f171594 | 2026-03-08 18:51:35 +0100 | Fix outbox created_at default to avoid layout resolve failure
6ac2e62 | 2026-03-08 18:48:50 +0100 | Make time trigger enqueue task statically compilable
60d05f6 | 2026-03-08 18:44:50 +0100 | Format outbox and JS API files with Fantomas
7c5a920 | 2026-03-08 18:42:42 +0100 | Add outbound HTTP API and outbox delivery pipeline
b9899f6 | 2026-03-08 18:09:33 +0100 | Fix task CE static compilability in time trigger enqueue
86b1f4d | 2026-03-08 18:06:11 +0100 | Format time trigger and schedule F# files
338ecf9 | 2026-03-08 18:03:59 +0100 | Fix a crash
8a4f858 | 2026-03-08 14:31:48 +0100 | Add flexible time offsets and one-shot datetime action schedules
a2f06a3 | 2026-03-08 13:34:04 +0100 | Format F# sources with fantomas
b2182b7 | 2026-03-08 13:25:47 +0100 | Add FunQL wildcard select support
35976bd | 2026-03-08 08:37:59 +0100 | Discover all instances for time trigger worker after restart
cba82e2 | 2026-03-08 08:32:09 +0100 | Add scalable datetime-based time triggers with queue worker
6ef6fc8 | 2026-03-08 07:23:44 +0100 | Format updated F# files with fantomas
34b48ed | 2026-03-08 07:08:14 +0100 | Cache compiled reference-argument subqueries
fee7903 | 2026-03-08 07:06:02 +0100 | Lower per-query execution logs to Debug
98d5f62 | 2026-03-08 07:05:55 +0100 | Use case-insensitive host lookup to leverage lower(name) index
ae7c5ef | 2026-03-08 07:05:41 +0100 | Use ReadCommitted for context cache version check transaction
3d9de35 | 2026-03-08 07:04:21 +0100 | Add trigram GIN index for root string main fields
5806e75 | 2026-03-08 07:02:37 +0100 | Apply UPDATE/DELETE permission filters via FROM/USING joins
6d18a0d | 2026-03-08 07:00:36 +0100 | Stabilize SQL comments to improve plan cache hit rate
6a2b137 | 2026-03-07 17:47:02 +0100 | Fix CTE in { ... }
c6ec9a7 | 2026-03-07 16:20:54 +0100 | add array operations
05e3f01 | 2026-03-07 15:54:58 +0100 | fix formatting
d6c2fd7 | 2026-03-07 15:52:41 +0100 | array_agg(... order by ...) and fix filter for sum
1545623 | 2026-03-07 15:20:25 +0100 | fix a bug
9e3df1e | 2026-03-07 14:19:13 +0100 | Merge branch 'tmp' into master
86001a2 | 2026-03-07 14:18:10 +0100 | fix lock files for locked-mode restore
a7bbb26 | 2026-03-07 11:48:20 +0100 | fix internal server error
3875d4f | 2026-03-07 09:06:48 +0100 | add extraction a part of a date
bdd824b | 2026-03-07 08:55:51 +0100 | format fix
c5533e5 | 2026-03-07 08:53:35 +0100 | add filter operator: select sum(..) filter (where ..)
00fab11 | 2026-03-07 08:47:47 +0100 | Add mod operator
b4668d5 | 2026-03-07 08:41:15 +0100 | format fix
1e25499 | 2026-03-07 08:37:25 +0100 | format fix
1e186d8 | 2026-03-07 08:34:55 +0100 | add row_number() function
aca237c | 2026-03-07 08:28:34 +0100 | Fix format
a4166aa | 2026-03-07 08:23:04 +0100 | Remove obsolete check
244d1be | 2026-03-07 08:22:07 +0100 | Add generate_series
4133e53 | 2026-03-07 00:03:41 +0100 | Handle VEExists in local SQL expression normalization
f8cf336 | 2026-03-07 00:00:45 +0100 | fix building
eb52576 | 2026-03-06 23:52:58 +0100 | fix building
321534f | 2026-03-06 21:04:53 +0100 | fix building
95287f5 | 2026-03-06 20:57:24 +0100 | add cross join
f370a0d | 2026-03-06 20:50:45 +0100 | add exists operator
d1614e2 | 2026-03-06 20:43:39 +0100 | workflow
bda95c4 | 2026-03-06 20:40:17 +0100 | select distinct
```

### Key additions for new JS runtime methods

- `e988dd0` (2026-03-09): added/extended JS runtime API in `OzmaDB/src/API/JavaScript.fs`:
  - `runTransaction(operations)`
  - `updateEntries(entity, updates, chunkSize=200)`
  - `deleteEntries(entity, ids, chunkSize=200)`
  - `getEntriesByIds(entity, ids, columns)`
  - `muteEvents(muted=true)`
  - `withMutedEvents(func)`
  - guarded `writeEvent` / `writeEventSync`
- `e988dd0` also introduced event logger hardening/configuration:
  - bounded queue + drop policy
  - payload truncation
  - sampling controls
- `2f6d5c1` (2026-03-09): formatting cleanup for touched F# files.

## Repository: `/Users/vientooscuro/PythonProjects/OzmaMCP`

Total commits by author: 12

### Full commit log (hash | date | subject)

```text
75ea598 | 2026-03-08 18:42:19 +0100 | Add MCP tools for OzmaDB HTTP API usage and outbox diagnostics
0abea8d | 2026-03-05 02:13:09 +0100 | улучшил MCP
eddcf19 | 2026-03-04 22:52:07 +0100 | добавил новые инструменты для анализа производительности
c86071d | 2026-03-04 22:15:45 +0100 | пофиксил transaction
f273c12 | 2026-03-04 21:59:33 +0100 | убрал ограничения
52fa485 | 2026-03-04 21:26:02 +0100 | добавил новые тулы
cd0cd6b | 2026-03-04 19:37:16 +0100 | Улучшил MCP
6f25dc7 | 2026-03-04 16:28:53 +0100 | Улучшил локальную документацию и добавил компрессию ответов от mcp для экономии токенов
d93fa1d | 2026-03-04 14:27:46 +0100 | Добавил get_user_view_query
37c0fbf | 2026-03-04 12:51:01 +0100 | Обновил MCP, добавил новые методы
d34d144 | 2026-03-04 12:23:14 +0100 | обновил MCP и улучшил его
af075d6 | 2026-03-04 11:30:59 +0100 | initial
```

### Key additions already in MCP history

- `75ea598` (2026-03-08): tools for HTTP API usage and outbox diagnostics.
- `eddcf19` (2026-03-04): performance analysis tools.
- `d93fa1d` (2026-03-04): `get_user_view_query`.

## Local (uncommitted) updates in OzmaMCP made now

- Added new tool `search_js_api_usage` to audit all new OzmaDB JS API methods in actions/triggers/modules.
- Kept backward compatibility: `search_http_api_usage` now reuses common JS API scan logic.
- Updated `README.md` tool list with `search_js_api_usage`.
