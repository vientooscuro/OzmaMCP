"""
OzmaDB MCP Server
Provides tools for interacting with OzmaDB (FunDB) via its REST API.
"""

import asyncio
import json
import os
from typing import Any, Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ---------------------------------------------------------------------------
# Configuration — read from env with fallback to defaults
# ---------------------------------------------------------------------------

OZMA_API_BASE = os.environ.get("OZMA_API_BASE", "https://ozma.gogol.school/api/")
OZMA_AUTH_URL = os.environ.get(
    "OZMA_AUTH_URL",
    "https://ozma.gogol.school/auth/realms/ozma/protocol/openid-connect/token",
)
OZMA_CLIENT_ID = os.environ.get("OZMA_CLIENT_ID", "ozmadb")
OZMA_CLIENT_SECRET = os.environ.get("OZMA_CLIENT_SECRET", "")
OZMA_USERNAME = os.environ.get("OZMA_USERNAME", "")
OZMA_PASSWORD = os.environ.get("OZMA_PASSWORD", "")

# Ensure base URL ends with /
if not OZMA_API_BASE.endswith("/"):
    OZMA_API_BASE += "/"

# ---------------------------------------------------------------------------
# Token cache (in-memory)
# ---------------------------------------------------------------------------

_access_token: Optional[str] = None
_http_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def _fetch_token() -> Optional[str]:
    """Obtain a new access token via password grant."""
    data = {
        "client_id": OZMA_CLIENT_ID,
        "client_secret": OZMA_CLIENT_SECRET,
        "grant_type": "password",
        "username": OZMA_USERNAME,
        "password": OZMA_PASSWORD,
    }
    try:
        r = await _get_client().post(OZMA_AUTH_URL, data=data)
        if r.status_code == 200:
            return r.json().get("access_token")
    except httpx.RequestError:
        pass
    return None


async def _ensure_token() -> Optional[str]:
    global _access_token
    if _access_token:
        # Quick validity check
        try:
            r = await _get_client().get(
                f"{OZMA_API_BASE}check_access",
                headers={"Authorization": f"Bearer {_access_token}"},
            )
            if r.status_code == 200:
                return _access_token
        except httpx.RequestError:
            pass
    _access_token = await _fetch_token()
    return _access_token


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_access_token or ''}"}


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


async def _get_with_retry(url: str, params: dict | None = None) -> httpx.Response:
    await _ensure_token()
    r = await _get_client().get(url, params=params, headers=_auth_headers())
    if r.status_code == 401:
        await _fetch_token()
        r = await _get_client().get(url, params=params, headers=_auth_headers())
    return r


async def _post_with_retry(url: str, body: dict) -> httpx.Response:
    await _ensure_token()
    r = await _get_client().post(
        url, json=body, headers={**_auth_headers(), "Content-Type": "application/json"}
    )
    if r.status_code == 401:
        await _fetch_token()
        r = await _get_client().post(
            url,
            json=body,
            headers={**_auth_headers(), "Content-Type": "application/json"},
        )
    return r


def _fmt_error(r: httpx.Response) -> str:
    try:
        err = r.json()
        return f"HTTP {r.status_code}: {err.get('message', r.text)}"
    except Exception:
        return f"HTTP {r.status_code}: {r.text}"


# ---------------------------------------------------------------------------
# MCP server setup
# ---------------------------------------------------------------------------

app = Server("ozma-mcp")


# ---------------------------------------------------------------------------
# Tool: funql_query
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="funql_query",
            description=(
                "Execute a raw FunQL SELECT query against OzmaDB (anonymous view). "
                "FunQL is PostgreSQL-like SELECT only — all tables must have explicit schema prefix, e.g. `usr.orders`. "
                "Pass parameters as a JSON dict — they will be sent as query string args (values JSON-encoded). "
                "Returns parsed rows as a list of dicts."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "FunQL SELECT statement, e.g. `select id, name from usr.customers where active = true`",
                    },
                    "params": {
                        "type": "object",
                        "description": "Optional query parameters (will be JSON-encoded and passed as query string)",
                        "additionalProperties": True,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="named_view_query",
            description=(
                "Fetch entries from a named user view stored in OzmaDB (`public.user_views`). "
                "Preferred over funql_query for frequently used queries (cached by server). "
                "Parameters are JSON-encoded and passed as query string."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name, e.g. `usr`"},
                    "view_name": {"type": "string", "description": "User view name"},
                    "params": {
                        "type": "object",
                        "description": "Optional view parameters",
                        "additionalProperties": True,
                    },
                },
                "required": ["schema", "view_name"],
            },
        ),
        types.Tool(
            name="named_view_info",
            description=(
                "Fetch metadata (column types, attributes, entity info) for a named user view. "
                "Useful to understand structure before querying."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string"},
                    "view_name": {"type": "string"},
                },
                "required": ["schema", "view_name"],
            },
        ),
        types.Tool(
            name="transaction",
            description=(
                "Execute an atomic transaction containing one or more insert/update/delete operations. "
                "All operations succeed or all are rolled back.\n\n"
                "Each operation object must have:\n"
                "- `type`: `\"insert\"` | `\"update\"` | `\"delete\"`\n"
                "- `entity`: `{\"schema\": str, \"name\": str}`\n"
                "- `entries`: dict of field values (for insert/update)\n"
                "- `id`: int record id (for update/delete)\n\n"
                "Returns list of results; insert results include the new `id`."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "operations": {
                        "type": "array",
                        "description": "List of insert/update/delete operations",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["insert", "update", "delete"]},
                                "entity": {
                                    "type": "object",
                                    "properties": {
                                        "schema": {"type": "string"},
                                        "name": {"type": "string"},
                                    },
                                    "required": ["schema", "name"],
                                },
                                "entries": {"type": "object"},
                                "id": {"type": "integer"},
                            },
                            "required": ["type", "entity"],
                        },
                    }
                },
                "required": ["operations"],
            },
        ),
        types.Tool(
            name="run_action",
            description=(
                "Run a server-side OzmaDB action (ECMAScript module stored in `public.actions`). "
                "Actions execute within a transaction under the caller's role. "
                "Returns the action result (usually `{ok: true}` or a navigation object)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "action_name": {"type": "string", "description": "Action name"},
                    "args": {
                        "type": "object",
                        "description": "Arguments to pass to the action",
                        "additionalProperties": True,
                    },
                },
                "required": ["schema", "action_name"],
            },
        ),
        types.Tool(
            name="check_access",
            description="Verify that the configured credentials are valid and the OzmaDB instance is reachable.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_schemas",
            description="List all schemas in the OzmaDB instance (queries `public.schemas`).",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_entities",
            description="List entities (tables) in a given schema (queries `public.entities`).",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema_name": {
                        "type": "string",
                        "description": "Schema name to filter by, e.g. `usr`",
                    }
                },
                "required": ["schema_name"],
            },
        ),
        types.Tool(
            name="list_entity_fields",
            description="List column fields of a specific entity (queries `public.column_fields` and `public.computed_fields`).",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema_name": {"type": "string"},
                    "entity_name": {"type": "string"},
                },
                "required": ["schema_name", "entity_name"],
            },
        ),
        types.Tool(
            name="get_action_code",
            description=(
                "Get the full JavaScript source code of a specific OzmaDB action. "
                "Use this after search_in_actions to read the complete implementation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "action_name": {"type": "string", "description": "Action name"},
                },
                "required": ["schema", "action_name"],
            },
        ),
        types.Tool(
            name="get_trigger_code",
            description=(
                "Get the full JavaScript source code of a specific OzmaDB trigger. "
                "Use this after search_in_triggers to read the complete implementation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "trigger_name": {"type": "string", "description": "Trigger name"},
                },
                "required": ["schema", "trigger_name"],
            },
        ),
        types.Tool(
            name="search_in_modules",
            description=(
                "Search for a substring inside the JavaScript code of all modules in `admin.modules_table`. "
                "Modules contain reusable utility functions imported by actions and triggers. "
                "Search is case-insensitive. Returns module name and an excerpt around the match."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Substring to search for in module JS code",
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="get_module_code",
            description=(
                "Get the full JavaScript source code of a specific module from `admin.modules_table`. "
                "Use this after search_in_modules to read the complete module implementation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "module_name": {"type": "string", "description": "Module name"},
                },
                "required": ["module_name"],
            },
        ),
        types.Tool(
            name="list_modules",
            description="List all modules available in `admin.modules_table` (names only, no code).",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="search_in_actions",
            description=(
                "Search for a substring inside the JavaScript code of all OzmaDB actions (`public.actions`). "
                "Useful for finding which actions use a particular function, variable, entity, or API call. "
                "Search is case-insensitive. Returns schema, action name, and a short excerpt around the match."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Substring to search for in action JS code, e.g. `usr.orders` or `sendEmail`",
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="search_in_triggers",
            description=(
                "Search for a substring inside the JavaScript code of all OzmaDB triggers (`public.triggers`). "
                "Useful for finding which triggers reference a particular entity, field, or logic. "
                "Search is case-insensitive. Returns schema, trigger name, entity, and a short excerpt around the match."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Substring to search for in trigger JS code",
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="search_field",
            description=(
                "Search for a field (column or computed) by name across ALL schemas and entities in the database. "
                "Useful for questions like 'where does field X appear?', 'which tables have a column called Y?'. "
                "The search is case-insensitive and supports partial match (substring). "
                "Returns a list of matches with schema, entity, field name, type, and whether it is computed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "field_name": {
                        "type": "string",
                        "description": "Field name to search for (substring, case-insensitive), e.g. `customer_id` or `email`",
                    },
                },
                "required": ["field_name"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool call handler
# ---------------------------------------------------------------------------

def _parse_rows(data: dict) -> list[dict]:
    """Convert FunDB IViewExprResult into a list of plain dicts."""
    info = data.get("info", {})
    columns = info.get("columns", [])
    result = data.get("result", {})
    rows = result.get("rows", [])

    out = []
    for row in rows:
        record: dict[str, Any] = {}
        if "mainId" in row:
            record["_id"] = row["mainId"]
        for i, col in enumerate(columns):
            name = col.get("name")
            if name is None:
                continue
            cell = row.get("values", [])[i] if i < len(row.get("values", [])) else {}
            if "value" in cell:
                val = cell["value"]
                if "pun" in cell:
                    val = {"id": val, "pun": cell["pun"]}
                record[name] = val
        out.append(record)
    return out


def _json_params(params: dict) -> dict:
    """JSON-encode param values as required by FunDB API."""
    return {k: json.dumps(v) for k, v in params.items()}


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        result = await _dispatch(name, arguments)
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def _dispatch(name: str, args: dict) -> Any:
    if name == "check_access":
        return await _tool_check_access()
    elif name == "funql_query":
        return await _tool_funql_query(args["query"], args.get("params", {}))
    elif name == "named_view_query":
        return await _tool_named_view_query(args["schema"], args["view_name"], args.get("params", {}))
    elif name == "named_view_info":
        return await _tool_named_view_info(args["schema"], args["view_name"])
    elif name == "transaction":
        return await _tool_transaction(args["operations"])
    elif name == "run_action":
        return await _tool_run_action(args["schema"], args["action_name"], args.get("args", {}))
    elif name == "list_schemas":
        return await _tool_list_schemas()
    elif name == "list_entities":
        return await _tool_list_entities(args["schema_name"])
    elif name == "list_entity_fields":
        return await _tool_list_entity_fields(args["schema_name"], args["entity_name"])
    elif name == "search_field":
        return await _tool_search_field(args["field_name"])
    elif name == "get_action_code":
        return await _tool_get_action_code(args["schema"], args["action_name"])
    elif name == "get_trigger_code":
        return await _tool_get_trigger_code(args["schema"], args["trigger_name"])
    elif name == "search_in_modules":
        return await _tool_search_in_modules(args["text"])
    elif name == "get_module_code":
        return await _tool_get_module_code(args["module_name"])
    elif name == "list_modules":
        return await _tool_list_modules()
    elif name == "search_in_actions":
        return await _tool_search_in_js("actions", args["text"])
    elif name == "search_in_triggers":
        return await _tool_search_in_js("triggers", args["text"])
    else:
        raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def _tool_check_access() -> dict:
    await _ensure_token()
    try:
        r = await _get_client().get(
            f"{OZMA_API_BASE}check_access", headers=_auth_headers()
        )
        return {"ok": r.status_code == 200, "status": r.status_code}
    except httpx.RequestError as e:
        return {"ok": False, "error": str(e)}


async def _tool_funql_query(query: str, params: dict) -> list[dict]:
    qp = {"__query": query}
    qp.update(_json_params(params))
    r = await _get_with_retry(f"{OZMA_API_BASE}views/anonymous/entries", params=qp)
    if r.status_code != 200:
        raise RuntimeError(_fmt_error(r))
    return _parse_rows(r.json())


async def _tool_named_view_query(schema: str, view_name: str, params: dict) -> list[dict]:
    url = f"{OZMA_API_BASE}views/by_name/{schema}/{view_name}/entries"
    r = await _get_with_retry(url, params=_json_params(params))
    if r.status_code != 200:
        raise RuntimeError(_fmt_error(r))
    return _parse_rows(r.json())


async def _tool_named_view_info(schema: str, view_name: str) -> dict:
    url = f"{OZMA_API_BASE}views/by_name/{schema}/{view_name}/info"
    r = await _get_with_retry(url)
    if r.status_code != 200:
        raise RuntimeError(_fmt_error(r))
    return r.json()


async def _tool_transaction(operations: list[dict]) -> dict:
    r = await _post_with_retry(f"{OZMA_API_BASE}transaction", {"operations": operations})
    if r.status_code != 200:
        raise RuntimeError(_fmt_error(r))
    return r.json()


async def _tool_run_action(schema: str, action_name: str, action_args: dict) -> Any:
    url = f"{OZMA_API_BASE}actions/{schema}/{action_name}/run"
    r = await _post_with_retry(url, action_args)
    if r.status_code != 200:
        raise RuntimeError(_fmt_error(r))
    return r.json()


async def _tool_list_schemas() -> list[dict]:
    query = "select id, name from public.schemas order by name"
    return await _tool_funql_query(query, {})


async def _tool_list_entities(schema_name: str) -> list[dict]:
    query = (
        "select e.id, e.name, e.is_abstract, e.is_frozen, e.main_field "
        "from public.entities as e "
        "join public.schemas as s on e.schema_id = s.id "
        f"where s.name = '{schema_name}' "
        "order by e.name"
    )
    return await _tool_funql_query(query, {})


async def _tool_list_entity_fields(schema_name: str, entity_name: str) -> dict:
    # column fields
    col_query = (
        "select cf.name, cf.field_type, cf.is_nullable, cf.is_immutable "
        "from public.column_fields as cf "
        "join public.entities as e on cf.entity_id = e.id "
        "join public.schemas as s on e.schema_id = s.id "
        f"where s.name = '{schema_name}' and e.name = '{entity_name}' "
        "order by cf.name"
    )
    # computed fields
    comp_query = (
        "select cf.name, cf.expression, cf.is_virtual "
        "from public.computed_fields as cf "
        "join public.entities as e on cf.entity_id = e.id "
        "join public.schemas as s on e.schema_id = s.id "
        f"where s.name = '{schema_name}' and e.name = '{entity_name}' "
        "order by cf.name"
    )
    columns, computed = await asyncio.gather(
        _tool_funql_query(col_query, {}),
        _tool_funql_query(comp_query, {}),
    )
    return {"columns": columns, "computed": computed}


async def _tool_get_action_code(schema: str, action_name: str) -> dict:
    query = (
        "select a.name as action_name, s.name as schema_name, a.function as code "
        "from public.actions as a "
        "join public.schemas as s on a.schema_id = s.id "
        f"where s.name = '{schema}' and a.name = '{action_name}'"
    )
    rows = await _tool_funql_query(query, {})
    if not rows:
        return {"error": f"Action '{schema}.{action_name}' not found"}
    return rows[0]


async def _tool_get_trigger_code(schema: str, trigger_name: str) -> dict:
    query = (
        "select t.name as trigger_name, s.name as schema_name, "
        "e.name as entity_name, t.procedure as code "
        "from public.triggers as t "
        "join public.schemas as s on t.schema_id = s.id "
        "join public.entities as e on t.trigger_entity_id = e.id "
        f"where s.name = '{schema}' and t.name = '{trigger_name}'"
    )
    rows = await _tool_funql_query(query, {})
    if not rows:
        return {"error": f"Trigger '{schema}.{trigger_name}' not found"}
    return rows[0]


async def _modules_code_field() -> str:
    """Detect the JS code field name in admin.modules_table."""
    # Try to read column_fields for admin.modules_table
    fields = await _tool_list_entity_fields("admin", "modules_table")
    col_names = {c.get("field_name") or c.get("name") for c in (fields.get("columns") or [])}
    for candidate in ("code", "function", "source", "body", "content"):
        if candidate in col_names:
            return candidate
    # fallback — just try 'code'
    return "code"


async def _tool_list_modules() -> list[dict]:
    code_field = await _modules_code_field()
    query = f"select id, name from admin.modules_table order by name"
    return await _tool_funql_query(query, {})


async def _tool_search_in_modules(text: str) -> list[dict]:
    code_field = await _modules_code_field()
    query = f"select id, name, {code_field} as code from admin.modules_table order by name"
    rows = await _tool_funql_query(query, {})
    if not rows:
        return []
    needle_lower = text.lower()
    results = []
    for row in rows:
        code = row.get("code") or ""
        if needle_lower not in code.lower():
            continue
        results.append({
            "module_name": row.get("name"),
            "excerpt": _excerpt(code, text),
        })
    return results


async def _tool_get_module_code(module_name: str) -> dict:
    code_field = await _modules_code_field()
    query = (
        f"select id, name, {code_field} as code "
        f"from admin.modules_table "
        f"where name = '{module_name}'"
    )
    rows = await _tool_funql_query(query, {})
    if not rows:
        return {"error": f"Module '{module_name}' not found"}
    return rows[0]


def _excerpt(code: str, needle: str, context: int = 120) -> str:
    """Return a short excerpt around the first case-insensitive match of needle in code."""
    idx = code.lower().find(needle.lower())
    if idx == -1:
        return ""
    start = max(0, idx - context)
    end = min(len(code), idx + len(needle) + context)
    snippet = code[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(code):
        snippet = snippet + "…"
    return snippet


async def _tool_search_in_js(kind: str, text: str) -> list[dict]:
    """Fetch all actions or triggers and filter by text in their JS code."""
    if kind == "actions":
        # public.actions: schema_id -> schemas.name, name, function
        query = (
            "select s.name as schema_name, a.name as action_name, a.function as code "
            "from public.actions as a "
            "join public.schemas as s on a.schema_id = s.id "
            "order by s.name, a.name"
        )
    else:
        # public.triggers: schema_id, name, trigger_entity_id -> entities.name, procedure
        query = (
            "select s.name as schema_name, t.name as trigger_name, "
            "e.name as entity_name, t.procedure as code "
            "from public.triggers as t "
            "join public.schemas as s on t.schema_id = s.id "
            "join public.entities as e on t.trigger_entity_id = e.id "
            "order by s.name, t.name"
        )

    rows = await _tool_funql_query(query, {})
    if not rows:
        return []

    results = []
    needle_lower = text.lower()
    for row in rows:
        code = row.get("code") or ""
        if needle_lower not in code.lower():
            continue
        match = {k: v for k, v in row.items() if k != "code"}
        match["excerpt"] = _excerpt(code, text)
        results.append(match)
    return results


async def _tool_search_field(field_name: str) -> list[dict]:
    # Search in column_fields (real columns)
    col_query = (
        "select s.name as schema_name, e.name as entity_name, "
        "cf.name as field_name, cf.field_type, false as is_computed "
        "from public.column_fields as cf "
        "join public.entities as e on cf.entity_id = e.id "
        "join public.schemas as s on e.schema_id = s.id "
        f"where lower(cf.name) like lower('%{field_name}%') "
        "order by s.name, e.name, cf.name"
    )
    # Search in computed_fields
    comp_query = (
        "select s.name as schema_name, e.name as entity_name, "
        "cf.name as field_name, 'computed' as field_type, true as is_computed "
        "from public.computed_fields as cf "
        "join public.entities as e on cf.entity_id = e.id "
        "join public.schemas as s on e.schema_id = s.id "
        f"where lower(cf.name) like lower('%{field_name}%') "
        "order by s.name, e.name, cf.name"
    )
    columns, computed = await asyncio.gather(
        _tool_funql_query(col_query, {}),
        _tool_funql_query(comp_query, {}),
    )
    return (columns or []) + (computed or [])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
