"""
OzmaDB MCP Server
Provides tools for interacting with OzmaDB (FunDB) via its REST API.
"""

import asyncio
import json
import os
import re
import time
from typing import Any, Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ---------------------------------------------------------------------------
# Configuration
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
OZMA_READONLY = os.environ.get("OZMA_READONLY", "").lower() in ("1", "true", "yes")

# Metadata cache TTL in seconds (5 minutes)
CACHE_TTL = int(os.environ.get("OZMA_CACHE_TTL", "300"))

if not OZMA_API_BASE.endswith("/"):
    OZMA_API_BASE += "/"

# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

_http_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


# ---------------------------------------------------------------------------
# Auth: JWT-based token expiry check (no extra HTTP round-trip)
# ---------------------------------------------------------------------------

_access_token: Optional[str] = None
_token_exp: float = 0.0  # unix timestamp when token expires


def _jwt_exp(token: str) -> float:
    """Decode JWT payload (no verification) and return exp as unix timestamp."""
    try:
        import base64
        parts = token.split(".")
        if len(parts) < 2:
            return 0.0
        # Add padding
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return float(data.get("exp", 0))
    except Exception:
        return 0.0


def _token_valid() -> bool:
    """Return True if current token exists and has >30s left."""
    if not _access_token:
        return False
    return time.time() < (_token_exp - 30)


async def _fetch_token() -> Optional[str]:
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
    global _access_token, _token_exp
    if _token_valid():
        return _access_token
    _access_token = await _fetch_token()
    if _access_token:
        _token_exp = _jwt_exp(_access_token)
    return _access_token


def _auth_headers() -> dict:
    if not _access_token:
        return {}
    return {"Authorization": f"Bearer {_access_token}"}


# ---------------------------------------------------------------------------
# Metadata cache
# ---------------------------------------------------------------------------

class _Cache:
    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry and time.time() < entry[0]:
            return entry[1]
        return None

    def set(self, key: str, value: Any, ttl: int = CACHE_TTL):
        self._store[key] = (time.time() + ttl, value)

    def invalidate(self, prefix: str = ""):
        if prefix:
            self._store = {k: v for k, v in self._store.items() if not k.startswith(prefix)}
        else:
            self._store.clear()


_cache = _Cache()


# ---------------------------------------------------------------------------
# Low-level HTTP helpers
# ---------------------------------------------------------------------------

def _ozma_error(r: httpx.Response) -> dict:
    try:
        err = r.json()
        return {"error": err.get("message", r.text), "status": r.status_code, "type": err.get("type", "generic")}
    except Exception:
        return {"error": r.text, "status": r.status_code, "type": "generic"}


def _exception_payload(e: Exception) -> dict:
    """Unwrap nested JSON errors raised from tool helpers."""
    msg = str(e)
    try:
        parsed = json.loads(msg)
        if isinstance(parsed, dict):
            if "type" not in parsed:
                parsed["type"] = "internal"
            return parsed
    except Exception:
        pass
    return {"error": msg, "type": "internal"}


async def _get(url: str, params: dict | None = None) -> httpx.Response:
    await _ensure_token()
    r = await _get_client().get(url, params=params, headers=_auth_headers())
    if r.status_code == 401:
        # Token rejected despite our local check — force refresh
        global _access_token, _token_exp
        _access_token = await _fetch_token()
        if _access_token:
            _token_exp = _jwt_exp(_access_token)
        r = await _get_client().get(url, params=params, headers=_auth_headers())
    return r


async def _post(url: str, body: dict) -> httpx.Response:
    await _ensure_token()
    headers = {**_auth_headers(), "Content-Type": "application/json"}
    r = await _get_client().post(url, json=body, headers=headers)
    if r.status_code == 401:
        global _access_token, _token_exp
        _access_token = await _fetch_token()
        if _access_token:
            _token_exp = _jwt_exp(_access_token)
        r = await _get_client().post(url, json=body, headers={**_auth_headers(), "Content-Type": "application/json"})
    return r


# ---------------------------------------------------------------------------
# FunDB response parser
# ---------------------------------------------------------------------------

def _parse_rows(data: dict) -> list[dict]:
    info = data.get("info", {})
    columns = info.get("columns", [])
    rows = data.get("result", {}).get("rows", [])
    out = []
    for row in rows:
        record: dict[str, Any] = {}
        if "mainId" in row:
            record["_id"] = row["mainId"]
        values = row.get("values", [])
        for i, col in enumerate(columns):
            name = col.get("name")
            if name is None or i >= len(values):
                continue
            cell = values[i]
            if "value" in cell:
                val = cell["value"]
                if "pun" in cell:
                    val = {"id": val, "pun": cell["pun"]}
                record[name] = val
        out.append(record)
    return out


def _json_params(params: dict) -> dict:
    return {k: json.dumps(v) for k, v in params.items()}


# ---------------------------------------------------------------------------
# Excerpt helper
# ---------------------------------------------------------------------------

def _excerpt(code: str, needle: str, context: int = 120) -> str:
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


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

app = Server("ozma-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    readonly_note = " ⚠️ Disabled (OZMA_READONLY=true)." if OZMA_READONLY else ""
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
                    "query": {"type": "string", "description": "FunQL SELECT statement"},
                    "params": {"type": "object", "description": "Optional query parameters (JSON-encoded)", "additionalProperties": True},
                    "limit": {"type": "integer", "description": "Max rows to return (appended to query as LIMIT)", "minimum": 1},
                    "offset": {"type": "integer", "description": "Skip first N rows (appended as OFFSET)", "minimum": 0},
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
                    "params": {"type": "object", "description": "Optional view parameters", "additionalProperties": True},
                    "limit": {"type": "integer", "description": "Max rows to return", "minimum": 1},
                    "offset": {"type": "integer", "description": "Skip first N rows", "minimum": 0},
                },
                "required": ["schema", "view_name"],
            },
        ),
        types.Tool(
            name="named_view_info",
            description="Fetch metadata (column types, attributes, entity info) for a named user view.",
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
            name="list_user_views",
            description=(
                "List named user views from `public.user_views` with optional filters by schema and view name substring. "
                "Useful to discover valid inputs for `named_view_query` / `named_view_info`."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema_name": {"type": "string", "description": "Optional schema filter, e.g. `usr`"},
                    "view_name_like": {"type": "string", "description": "Optional case-insensitive substring for view names"},
                },
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
                + readonly_note
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "operations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["insert", "update", "delete"]},
                                "entity": {
                                    "type": "object",
                                    "properties": {"schema": {"type": "string"}, "name": {"type": "string"}},
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
                + readonly_note
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string"},
                    "action_name": {"type": "string"},
                    "args": {"type": "object", "additionalProperties": True},
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
            name="validate_funql",
            description=(
                "Validate a FunQL query by resolving it through anonymous view metadata endpoint. "
                "Optionally passes query params (JSON-encoded). Returns `ok`, HTTP status, and backend error details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "FunQL query to validate"},
                    "params": {"type": "object", "description": "Optional query parameters", "additionalProperties": True},
                },
                "required": ["query"],
            },
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
                "properties": {"schema_name": {"type": "string", "description": "Schema name, e.g. `usr`"}},
                "required": ["schema_name"],
            },
        ),
        types.Tool(
            name="list_entity_fields",
            description="List column and computed fields of a specific entity.",
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
            name="search_field",
            description=(
                "Search for a field (column or computed) by name across ALL schemas and entities in the database. "
                "Case-insensitive substring match. "
                "Returns schema, entity, field name, type, and whether it is computed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "field_name": {"type": "string", "description": "Substring to search for, e.g. `customer_id`"},
                },
                "required": ["field_name"],
            },
        ),
        types.Tool(
            name="get_action_code",
            description="Get the full JavaScript source code of a specific OzmaDB action.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string"},
                    "action_name": {"type": "string"},
                },
                "required": ["schema", "action_name"],
            },
        ),
        types.Tool(
            name="get_trigger_code",
            description="Get the full JavaScript source code of a specific OzmaDB trigger.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string"},
                    "trigger_name": {"type": "string"},
                },
                "required": ["schema", "trigger_name"],
            },
        ),
        types.Tool(
            name="search_in_modules",
            description=(
                "Search for a substring inside the JavaScript code of all modules in `admin.modules_table`. "
                "Modules contain reusable utility functions imported by actions and triggers. "
                "Case-insensitive. Returns module name and excerpt around the match."
            ),
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        ),
        types.Tool(
            name="get_module_code",
            description="Get the full JavaScript source code of a specific module from `admin.modules_table`.",
            inputSchema={
                "type": "object",
                "properties": {"module_name": {"type": "string"}},
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
                "Case-insensitive. Returns schema, action name, and excerpt around the match."
            ),
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Substring to search for, e.g. `usr.orders`"}},
                "required": ["text"],
            },
        ),
        types.Tool(
            name="search_in_triggers",
            description=(
                "Search for a substring inside the JavaScript code of all OzmaDB triggers (`public.triggers`). "
                "Case-insensitive. Returns schema, trigger name, entity, and excerpt around the match."
            ),
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        ),
        types.Tool(
            name="query_events",
            description=(
                "Query the OzmaDB event log (`public.events`). "
                "Useful for debugging: find recent errors, track what happened to a specific entity/row, "
                "see what a user did, or inspect action/trigger side-effects.\n\n"
                "Returned fields: id, timestamp, transaction_timestamp, source, type, "
                "request, response, error (coalesced from request details and error), "
                "user_name, schema_name, entity_name, row_id.\n\n"
                "All filters are optional and combinable. Default limit is 50."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "ISO datetime, e.g. `2024-01-01 00:00`"},
                    "date_to": {"type": "string", "description": "ISO datetime, e.g. `2024-12-31 23:59`"},
                    "is_error": {"type": "boolean", "description": "true — only errors, false — only successful events"},
                    "type": {"type": "string", "description": "Event type filter, e.g. `insert`, `update`, `delete`, `action`"},
                    "schema_name": {"type": "string", "description": "Filter by entity schema, e.g. `usr`"},
                    "entity_name": {"type": "string", "description": "Filter by entity name, e.g. `orders`"},
                    "row_id": {"type": "integer", "description": "Filter by specific record id"},
                    "user_name": {"type": "string", "description": "Filter by user name (exact match)"},
                    "limit": {"type": "integer", "description": "Max rows to return (default 50)", "minimum": 1, "maximum": 500},
                    "offset": {"type": "integer", "description": "Skip first N rows", "minimum": 0},
                },
            },
        ),
        types.Tool(
            name="search_in_all",
            description=(
                "Search for a substring across ALL JavaScript code in the database: "
                "actions (`public.actions`), triggers (`public.triggers`), and modules (`admin.modules_table`). "
                "Runs all three searches in parallel. Case-insensitive. "
                "Returns a dict with keys `actions`, `triggers`, `modules`, each containing matches with excerpts."
            ),
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Substring to search for"}},
                "required": ["text"],
            },
        ),
        types.Tool(
            name="search_in_metadata",
            description=(
                "Search for a substring inside OzmaDB metadata 'code' fields: "
                "computed field expressions, column defaults, check constraints, role rules, "
                "entity main_field, user view queries, and user view generators scripts. "
                "Case-insensitive. Returns grouped matches."
            ),
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Substring to search for"}},
                "required": ["text"],
            },
        ),
        types.Tool(
            name="where_used_field",
            description=(
                "Find where a field is used across OzmaDB code and metadata. "
                "Searches user views, actions, triggers, and metadata expressions "
                "using several field-aware patterns (e.g. `desired_name`, `=>desired_name`, "
                "`\"desired_name\"`, and optional `schema.entity` qualifiers)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Entity schema, e.g. `base`"},
                    "entity": {"type": "string", "description": "Entity name, e.g. `contacts`"},
                    "field": {"type": "string", "description": "Field name, e.g. `desired_name`"},
                    "schema_filter": {"type": "string", "description": "Optional result filter by schema name"},
                    "include_views": {"type": "boolean", "description": "Include matches from `public.user_views.query`"},
                    "include_actions": {"type": "boolean", "description": "Include matches from `public.actions.function`"},
                    "include_triggers": {"type": "boolean", "description": "Include matches from `public.triggers.procedure`"},
                    "include_modules": {"type": "boolean", "description": "Include matches from `admin.modules_table` JS code"},
                    "include_metadata": {"type": "boolean", "description": "Include matches from metadata expressions/defaults/rules"},
                },
                "required": ["schema", "entity", "field"],
            },
        ),
        types.Tool(
            name="safe_update_view_query",
            description=(
                "Safely update `public.user_views.query` by replacing text in a named view query. "
                "Supports dry-run and preflight FunQL validation before commit."
                + readonly_note
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "View schema, e.g. `crm`"},
                    "view_name": {"type": "string", "description": "View name"},
                    "from_text": {"type": "string", "description": "Exact text to replace"},
                    "to_text": {"type": "string", "description": "Replacement text"},
                    "replace_count": {"type": "integer", "description": "Optional max replacement count", "minimum": 1},
                    "dry_run": {"type": "boolean", "description": "If true, do not persist changes"},
                    "validate_before_commit": {"type": "boolean", "description": "Validate resulting query before write"},
                },
                "required": ["schema", "view_name", "from_text", "to_text"],
            },
        ),
        types.Tool(
            name="upsert_computed_field",
            description=(
                "Create or update a computed field in `public.computed_fields` for a target entity. "
                "Performs hierarchy conflict pre-check and can auto-fallback to `is_virtual=true` when needed."
                + readonly_note
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Entity schema, e.g. `base`"},
                    "entity": {"type": "string", "description": "Entity name, e.g. `contacts`"},
                    "field_name": {"type": "string", "description": "Computed field name"},
                    "expression": {"type": "string", "description": "FunQL expression"},
                    "is_virtual": {"type": "boolean", "description": "Computed field virtual flag (default: true)"},
                    "is_materialized": {"type": "boolean", "description": "Materialized flag (default: false)"},
                    "allow_broken": {"type": "boolean", "description": "Allow broken expression (default: false)"},
                    "description": {"type": "string", "description": "Field description (default: empty string)"},
                    "metadata": {"type": "object", "description": "Field metadata JSON (default: {})"},
                    "auto_virtual_fallback": {
                        "type": "boolean",
                        "description": "If hierarchy conflict is detected and is_virtual=false, retry with is_virtual=true",
                    },
                },
                "required": ["schema", "entity", "field_name", "expression"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool call dispatcher
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        result = await _dispatch(name, arguments)
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    except PermissionError as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e), "type": "readonly"}))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps(_exception_payload(e), ensure_ascii=False))]


def _require_write():
    if OZMA_READONLY:
        raise PermissionError("This MCP server is running in read-only mode (OZMA_READONLY=true). Mutations are disabled.")


async def _dispatch(name: str, args: dict) -> Any:
    match name:
        case "check_access":
            return await _tool_check_access()
        case "validate_funql":
            return await _tool_validate_funql(args["query"], args.get("params", {}))
        case "funql_query":
            return await _tool_funql_query(args["query"], args.get("params", {}), args.get("limit"), args.get("offset"))
        case "named_view_query":
            return await _tool_named_view_query(args["schema"], args["view_name"], args.get("params", {}), args.get("limit"), args.get("offset"))
        case "named_view_info":
            return await _tool_named_view_info(args["schema"], args["view_name"])
        case "list_user_views":
            return await _tool_list_user_views(args.get("schema_name"), args.get("view_name_like"))
        case "transaction":
            _require_write()
            return await _tool_transaction(args["operations"])
        case "run_action":
            _require_write()
            return await _tool_run_action(args["schema"], args["action_name"], args.get("args", {}))
        case "list_schemas":
            return await _tool_list_schemas()
        case "list_entities":
            return await _tool_list_entities(args["schema_name"])
        case "list_entity_fields":
            return await _tool_list_entity_fields(args["schema_name"], args["entity_name"])
        case "search_field":
            return await _tool_search_field(args["field_name"])
        case "get_action_code":
            return await _tool_get_action_code(args["schema"], args["action_name"])
        case "get_trigger_code":
            return await _tool_get_trigger_code(args["schema"], args["trigger_name"])
        case "search_in_modules":
            return await _tool_search_in_modules(args["text"])
        case "get_module_code":
            return await _tool_get_module_code(args["module_name"])
        case "list_modules":
            return await _tool_list_modules()
        case "search_in_actions":
            return await _tool_search_in_js("actions", args["text"])
        case "search_in_triggers":
            return await _tool_search_in_js("triggers", args["text"])
        case "query_events":
            return await _tool_query_events(args)
        case "search_in_all":
            return await _tool_search_in_all(args["text"])
        case "search_in_metadata":
            return await _tool_search_in_metadata(args["text"])
        case "where_used_field":
            return await _tool_where_used_field(
                args["schema"],
                args["entity"],
                args["field"],
                schema_filter=args.get("schema_filter"),
                include_views=args.get("include_views", True),
                include_actions=args.get("include_actions", True),
                include_triggers=args.get("include_triggers", True),
                include_modules=args.get("include_modules", True),
                include_metadata=args.get("include_metadata", True),
            )
        case "safe_update_view_query":
            _require_write()
            return await _tool_safe_update_view_query(
                schema=args["schema"],
                view_name=args["view_name"],
                from_text=args["from_text"],
                to_text=args["to_text"],
                replace_count=args.get("replace_count"),
                dry_run=args.get("dry_run", False),
                validate_before_commit=args.get("validate_before_commit", True),
            )
        case "upsert_computed_field":
            _require_write()
            return await _tool_upsert_computed_field(
                schema=args["schema"],
                entity=args["entity"],
                field_name=args["field_name"],
                expression=args["expression"],
                is_virtual=args.get("is_virtual", True),
                is_materialized=args.get("is_materialized", False),
                allow_broken=args.get("allow_broken", False),
                description=args.get("description", ""),
                metadata=args.get("metadata", {}),
                auto_virtual_fallback=args.get("auto_virtual_fallback", True),
            )
        case _:
            return {"error": f"Unknown tool: {name}", "type": "not_found"}


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def _tool_check_access() -> dict:
    await _ensure_token()
    try:
        r = await _get(f"{OZMA_API_BASE}check_access")
        return {"ok": r.status_code == 200, "status": r.status_code, "readonly": OZMA_READONLY}
    except httpx.RequestError as e:
        return {"ok": False, "error": str(e), "type": "network"}


async def _tool_validate_funql(query: str, params: dict | None = None) -> dict:
    qp = {"__query": query.rstrip()}
    qp.update(_json_params(params or {}))
    r = await _get(f"{OZMA_API_BASE}views/anonymous/info", params=qp)
    if r.status_code == 200:
        return {"ok": True, "status": 200}
    err = _ozma_error(r)
    return {"ok": False, "status": r.status_code, "error": err.get("error"), "type": err.get("type")}


def _apply_pagination(query: str, limit: Optional[int], offset: Optional[int]) -> str:
    if limit is not None:
        query += f" limit {limit}"
    if offset is not None:
        query += f" offset {offset}"
    return query


async def _tool_funql_query(query: str, params: dict, limit: Optional[int] = None, offset: Optional[int] = None) -> list[dict]:
    if re.search(r"(?is)^\s*select\s+\*", query):
        raise ValueError(
            "FunQL does not support wildcard SELECT (`SELECT *`). "
            "List columns explicitly, for example: `select id, name from public.column_fields`."
        )
    query = _apply_pagination(query.rstrip(), limit, offset)
    qp = {"__query": query}
    qp.update(_json_params(params))
    r = await _get(f"{OZMA_API_BASE}views/anonymous/entries", params=qp)
    if r.status_code != 200:
        raise RuntimeError(json.dumps(_ozma_error(r)))
    return _parse_rows(r.json())


async def _tool_named_view_query(schema: str, view_name: str, params: dict, limit: Optional[int] = None, offset: Optional[int] = None) -> list[dict] | dict:
    url = f"{OZMA_API_BASE}views/by_name/{schema}/{view_name}/entries"
    qp = _json_params({k: v for k, v in params.items() if v is not None})
    if limit is not None:
        qp["__limit"] = str(limit)
    if offset is not None:
        qp["__offset"] = str(offset)
    r = await _get(url, params=qp)
    if r.status_code != 200:
        raise RuntimeError(json.dumps(_ozma_error(r)))
    return _parse_rows(r.json())


async def _tool_named_view_info(schema: str, view_name: str) -> dict:
    r = await _get(f"{OZMA_API_BASE}views/by_name/{schema}/{view_name}/info")
    if r.status_code != 200:
        raise RuntimeError(json.dumps(_ozma_error(r)))
    return r.json()


async def _tool_list_user_views(schema_name: Optional[str] = None, view_name_like: Optional[str] = None) -> list[dict]:
    conditions = []
    if schema_name:
        schema_name_esc = schema_name.replace("'", "''")
        conditions.append(f"s.name = '{schema_name_esc}'")
    if view_name_like:
        view_name_like_esc = view_name_like.replace("'", "''")
        conditions.append(f"lower(uv.name) like lower('%{view_name_like_esc}%')")
    where = (" where " + " and ".join(conditions)) if conditions else ""
    query = (
        "select s.name as schema_name, uv.name as view_name "
        "from public.user_views as uv "
        "join public.schemas as s on uv.schema_id = s.id "
        f"{where} "
        "order by s.name, uv.name"
    )
    return await _tool_funql_query(query, {})


async def _tool_transaction(operations: list[dict]) -> dict:
    r = await _post(f"{OZMA_API_BASE}transaction", {"operations": operations})
    if r.status_code != 200:
        raise RuntimeError(json.dumps(_ozma_error(r)))
    _cache.invalidate()
    return r.json()


async def _tool_run_action(schema: str, action_name: str, action_args: dict) -> Any:
    r = await _post(f"{OZMA_API_BASE}actions/{schema}/{action_name}/run", action_args)
    if r.status_code != 200:
        raise RuntimeError(json.dumps(_ozma_error(r)))
    _cache.invalidate()
    return r.json()


# --- Metadata with cache ---

async def _cached_funql(cache_key: str, query: str) -> list[dict]:
    hit = _cache.get(cache_key)
    if hit is not None:
        return hit
    result = await _tool_funql_query(query, {})
    _cache.set(cache_key, result)
    return result


async def _tool_list_schemas() -> list[dict]:
    return await _cached_funql(
        "schemas",
        "select id, name from public.schemas order by name",
    )


async def _tool_list_entities(schema_name: str) -> list[dict]:
    return await _cached_funql(
        f"entities:{schema_name}",
        f"select e.id, e.name, e.is_abstract "
        f"from public.entities as e "
        f"join public.schemas as s on e.schema_id = s.id "
        f"where s.name = '{schema_name}' order by e.name",
    )


async def _tool_list_entity_fields(schema_name: str, entity_name: str) -> dict:
    cache_key = f"fields:{schema_name}.{entity_name}"
    hit = _cache.get(cache_key)
    if hit is not None:
        return hit
    col_query = (
        f"select cf.name as field_name, cf.type as field_type, cf.is_nullable, cf.is_immutable "
        f"from public.column_fields as cf "
        f"join public.entities as e on cf.entity_id = e.id "
        f"join public.schemas as s on e.schema_id = s.id "
        f"where s.name = '{schema_name}' and e.name = '{entity_name}' order by cf.name"
    )
    comp_query = (
        f"select cf.name as field_name, cf.expression, cf.is_virtual "
        f"from public.computed_fields as cf "
        f"join public.entities as e on cf.entity_id = e.id "
        f"join public.schemas as s on e.schema_id = s.id "
        f"where s.name = '{schema_name}' and e.name = '{entity_name}' order by cf.name"
    )
    columns, computed = await asyncio.gather(
        _tool_funql_query(col_query, {}),
        _tool_funql_query(comp_query, {}),
    )
    result = {"columns": columns, "computed": computed}
    _cache.set(cache_key, result)
    return result


async def _tool_search_field(field_name: str) -> list[dict]:
    col_query = (
        f"select s.name as schema_name, e.name as entity_name, "
        f"cf.name as field_name, cf.type as field_type, false as is_computed "
        f"from public.column_fields as cf "
        f"join public.entities as e on cf.entity_id = e.id "
        f"join public.schemas as s on e.schema_id = s.id "
        f"where lower(cf.name) like lower('%{field_name}%') "
        f"order by s.name, e.name, cf.name"
    )
    comp_query = (
        f"select s.name as schema_name, e.name as entity_name, "
        f"cf.name as field_name, 'computed' as field_type, true as is_computed "
        f"from public.computed_fields as cf "
        f"join public.entities as e on cf.entity_id = e.id "
        f"join public.schemas as s on e.schema_id = s.id "
        f"where lower(cf.name) like lower('%{field_name}%') "
        f"order by s.name, e.name, cf.name"
    )
    columns, computed = await asyncio.gather(
        _tool_funql_query(col_query, {}),
        _tool_funql_query(comp_query, {}),
    )
    return (columns or []) + (computed or [])


async def _tool_get_action_code(schema: str, action_name: str) -> dict:
    rows = await _tool_funql_query(
        f"select a.name as action_name, s.name as schema_name, a.function as code "
        f"from public.actions as a "
        f"join public.schemas as s on a.schema_id = s.id "
        f"where s.name = '{schema}' and a.name = '{action_name}'",
        {},
    )
    if not rows:
        return {"error": f"Action '{schema}.{action_name}' not found", "type": "not_found"}
    return rows[0]


async def _tool_get_trigger_code(schema: str, trigger_name: str) -> dict:
    rows = await _tool_funql_query(
        f"select t.name as trigger_name, s.name as schema_name, "
        f"e.name as entity_name, t.procedure as code "
        f"from public.triggers as t "
        f"join public.schemas as s on t.schema_id = s.id "
        f"join public.entities as e on t.trigger_entity_id = e.id "
        f"where s.name = '{schema}' and t.name = '{trigger_name}'",
        {},
    )
    if not rows:
        return {"error": f"Trigger '{schema}.{trigger_name}' not found", "type": "not_found"}
    return rows[0]


# --- Modules ---

async def _modules_code_field() -> str:
    """Detect JS code field name in admin.modules_table (cached)."""
    hit = _cache.get("modules_code_field")
    if hit:
        return hit
    fields = await _tool_list_entity_fields("admin", "modules_table")
    col_names = {c.get("field_name") or c.get("name") for c in (fields.get("columns") or [])}
    for candidate in ("code", "function", "source", "body", "content"):
        if candidate in col_names:
            _cache.set("modules_code_field", candidate, ttl=3600)
            return candidate
    _cache.set("modules_code_field", "code", ttl=3600)
    return "code"


async def _fetch_all_modules() -> list[dict]:
    """Fetch all modules with code (cached)."""
    hit = _cache.get("all_modules")
    if hit is not None:
        return hit
    code_field = await _modules_code_field()
    rows = await _tool_funql_query(
        f"select id, name, {code_field} as code from admin.modules_table order by name", {}
    )
    _cache.set("all_modules", rows or [])
    return rows or []


async def _tool_list_modules() -> list[dict]:
    modules = await _fetch_all_modules()
    return [{"id": m.get("_id") or m.get("id"), "name": m.get("name")} for m in modules]


async def _tool_search_in_modules(text: str) -> list[dict]:
    modules = await _fetch_all_modules()
    needle_lower = text.lower()
    return [
        {"module_name": m.get("name"), "excerpt": _excerpt(m.get("code") or "", text)}
        for m in modules
        if needle_lower in (m.get("code") or "").lower()
    ]


async def _tool_get_module_code(module_name: str) -> dict:
    modules = await _fetch_all_modules()
    for m in modules:
        if m.get("name") == module_name:
            return {"name": m.get("name"), "code": m.get("code")}
    return {"error": f"Module '{module_name}' not found", "type": "not_found"}


# --- Search in actions / triggers ---

async def _fetch_all_actions() -> list[dict]:
    hit = _cache.get("all_actions")
    if hit is not None:
        return hit
    rows = await _tool_funql_query(
        "select s.name as schema_name, a.name as action_name, a.function as code "
        "from public.actions as a "
        "join public.schemas as s on a.schema_id = s.id "
        "order by s.name, a.name",
        {},
    )
    _cache.set("all_actions", rows or [])
    return rows or []


async def _fetch_all_triggers() -> list[dict]:
    hit = _cache.get("all_triggers")
    if hit is not None:
        return hit
    rows = await _tool_funql_query(
        "select s.name as schema_name, t.name as trigger_name, "
        "e.name as entity_name, t.procedure as code "
        "from public.triggers as t "
        "join public.schemas as s on t.schema_id = s.id "
        "join public.entities as e on t.trigger_entity_id = e.id "
        "order by s.name, t.name",
        {},
    )
    _cache.set("all_triggers", rows or [])
    return rows or []


def _search_rows(rows: list[dict], text: str, name_key: str) -> list[dict]:
    needle_lower = text.lower()
    results = []
    for row in rows:
        code = row.get("code") or ""
        if needle_lower not in code.lower():
            continue
        match = {k: v for k, v in row.items() if k != "code"}
        match["excerpt"] = _excerpt(code, text)
        results.append(match)
    return results


async def _tool_search_in_js(kind: str, text: str) -> list[dict]:
    if kind == "actions":
        rows = await _fetch_all_actions()
        return _search_rows(rows, text, "action_name")
    else:
        rows = await _fetch_all_triggers()
        return _search_rows(rows, text, "trigger_name")


async def _tool_query_events(args: dict) -> list[dict]:
    conditions = []

    date_from = args.get("date_from")
    date_to = args.get("date_to")
    is_error = args.get("is_error")
    event_type = args.get("type")
    schema_name = args.get("schema_name")
    entity_name = args.get("entity_name")
    row_id = args.get("row_id")
    user_name = args.get("user_name")
    limit = args.get("limit", 50)
    offset = args.get("offset")

    if date_from:
        conditions.append(f"timestamp >= '{date_from}'::datetime")
    if date_to:
        conditions.append(f"timestamp <= '{date_to}'::datetime")
    if is_error is True:
        conditions.append("error is not null")
    elif is_error is False:
        conditions.append("error is null")
    if event_type:
        conditions.append(f"type = '{event_type}'")
    if schema_name:
        conditions.append(f"request->'entity'->>'schema' = '{schema_name}'")
    if entity_name:
        conditions.append(f"request->'entity'->>'name' = '{entity_name}'")
    if row_id is not None:
        conditions.append(f"(details->>'id')::int = {row_id}")
    if user_name:
        conditions.append(f"user_name = '{user_name}'")

    where = ("where " + " and ".join(conditions)) if conditions else ""

    query = (
        "select "
        "id, timestamp, transaction_timestamp, source, type, "
        "request, response, "
        "coalesce(request->>'details', error->>'error' || ':\\n' || (error->>'message')) as error, "
        "user_name, "
        "request->'entity'->>'schema' as schema_name, "
        "request->'entity'->>'name' as entity_name, "
        "(details->>'id')::int as row_id "
        f"from public.events {where} order by timestamp desc"
    )

    return await _tool_funql_query(query, {}, limit=limit, offset=offset)


async def _tool_search_in_all(text: str) -> dict:
    actions, triggers, modules = await asyncio.gather(
        _fetch_all_actions(),
        _fetch_all_triggers(),
        _fetch_all_modules(),
        return_exceptions=True,
    )
    action_error = _exception_payload(actions) if isinstance(actions, Exception) else None
    trigger_error = _exception_payload(triggers) if isinstance(triggers, Exception) else None
    module_error = _exception_payload(modules) if isinstance(modules, Exception) else None
    if isinstance(actions, Exception):
        actions = []
    if isinstance(triggers, Exception):
        triggers = []
    if isinstance(modules, Exception):
        modules = []
    return {
        "actions": _search_rows(actions, text, "action_name"),
        "triggers": _search_rows(triggers, text, "trigger_name"),
        "modules": [
            {"module_name": m.get("name"), "excerpt": _excerpt(m.get("code") or "", text)}
            for m in modules
            if text.lower() in (m.get("code") or "").lower()
        ],
        "errors": {
            "actions": action_error,
            "triggers": trigger_error,
            "modules": module_error,
        },
    }


async def _safe_funql(query: str, params: dict | None = None) -> list[dict]:
    try:
        return await _tool_funql_query(query, params or {})
    except Exception:
        return []


async def _tool_search_in_metadata(text: str) -> dict:
    needle = f"%{text}%"
    entities_main_field_q = (
        "{ $needle string }: "
        "select s.name as schema_name, e.name as entity_name, e.main_field "
        "from public.entities as e "
        "join public.schemas as s on e.schema_id = s.id "
        "where e.main_field is not null and e.main_field ilike $needle "
        "order by s.name, e.name"
    )
    column_defaults_q = (
        "{ $needle string }: "
        "select s.name as schema_name, e.name as entity_name, cf.name as field_name, cf.\"default\" as expression "
        "from public.column_fields as cf "
        "join public.entities as e on cf.entity_id = e.id "
        "join public.schemas as s on e.schema_id = s.id "
        "where cf.\"default\" is not null and cf.\"default\" ilike $needle "
        "order by s.name, e.name, cf.name"
    )
    computed_expressions_q = (
        "{ $needle string }: "
        "select s.name as schema_name, e.name as entity_name, cf.name as field_name, cf.expression "
        "from public.computed_fields as cf "
        "join public.entities as e on cf.entity_id = e.id "
        "join public.schemas as s on e.schema_id = s.id "
        "where cf.expression ilike $needle "
        "order by s.name, e.name, cf.name"
    )
    check_constraints_q = (
        "{ $needle string }: "
        "select s.name as schema_name, e.name as entity_name, c.name as constraint_name, c.expression "
        "from public.check_constraints as c "
        "join public.entities as e on c.entity_id = e.id "
        "join public.schemas as s on e.schema_id = s.id "
        "where c.expression ilike $needle "
        "order by s.name, e.name, c.name"
    )
    role_rules_q = (
        "{ $needle string }: "
        "select r.name as role_name, s.name as schema_name, e.name as entity_name, "
        "re.\"select\" as select_expr, re.\"update\" as update_expr, re.\"delete\" as delete_expr, re.\"check\" as check_expr "
        "from public.role_entities as re "
        "join public.roles as r on re.role_id = r.id "
        "join public.entities as e on re.entity_id = e.id "
        "join public.schemas as s on e.schema_id = s.id "
        "where "
        "(re.\"select\" is not null and re.\"select\" ilike $needle) or "
        "(re.\"update\" is not null and re.\"update\" ilike $needle) or "
        "(re.\"delete\" is not null and re.\"delete\" ilike $needle) or "
        "(re.\"check\" is not null and re.\"check\" ilike $needle) "
        "order by r.name, s.name, e.name"
    )
    user_views_q = (
        "{ $needle string }: "
        "select s.name as schema_name, uv.name as view_name, uv.query as expression "
        "from public.user_views as uv "
        "join public.schemas as s on uv.schema_id = s.id "
        "where uv.query ilike $needle "
        "order by s.name, uv.name"
    )
    user_view_generators_q = (
        "{ $needle string }: "
        "select s.name as schema_name, s.name as generator_name, uvg.script as expression "
        "from public.user_view_generators as uvg "
        "join public.schemas as s on uvg.schema_id = s.id "
        "where uvg.script ilike $needle "
        "order by s.name"
    )

    (
        entities_main_field,
        column_defaults,
        computed_expressions,
        check_constraints,
        role_rules,
        user_views,
        user_view_generators,
    ) = await asyncio.gather(
        _safe_funql(entities_main_field_q, {"needle": needle}),
        _safe_funql(column_defaults_q, {"needle": needle}),
        _safe_funql(computed_expressions_q, {"needle": needle}),
        _safe_funql(check_constraints_q, {"needle": needle}),
        _safe_funql(role_rules_q, {"needle": needle}),
        _safe_funql(user_views_q, {"needle": needle}),
        _safe_funql(user_view_generators_q, {"needle": needle}),
    )

    return {
        "entities_main_field": entities_main_field,
        "column_defaults": column_defaults,
        "computed_expressions": computed_expressions,
        "check_constraints": check_constraints,
        "role_rules": role_rules,
        "user_views": user_views,
        "user_view_generators": user_view_generators,
    }


def _field_usage_patterns(schema: str, entity: str, field: str) -> list[str]:
    schema = schema.strip()
    entity = entity.strip()
    field = field.strip()
    return [
        field,
        f"=>{field}",
        f"\"{field}\"",
        f"'{field}'",
        f"{schema}.{entity}",
        f"\"{schema}\".\"{entity}\"",
        f"{schema}.{entity}.{field}",
        f"\"{schema}\".\"{entity}\".\"{field}\"",
    ]


def _dedupe_by_keys(rows: list[dict], keys: list[str]) -> list[dict]:
    seen: set[tuple] = set()
    out: list[dict] = []
    for row in rows:
        sig = tuple(row.get(k) for k in keys)
        if sig in seen:
            continue
        seen.add(sig)
        out.append(row)
    return out


def _filter_by_schema(rows: list[dict], schema_filter: Optional[str]) -> list[dict]:
    if not schema_filter:
        return rows
    return [row for row in rows if row.get("schema_name") == schema_filter]


async def _tool_where_used_field(
    schema: str,
    entity: str,
    field: str,
    *,
    schema_filter: Optional[str] = None,
    include_views: bool = True,
    include_actions: bool = True,
    include_triggers: bool = True,
    include_modules: bool = True,
    include_metadata: bool = True,
) -> dict:
    patterns = _field_usage_patterns(schema, entity, field)
    errors: list[dict] = []

    metadata_acc: dict[str, list[dict]] = {
        "entities_main_field": [],
        "column_defaults": [],
        "computed_expressions": [],
        "check_constraints": [],
        "role_rules": [],
        "user_views": [],
        "user_view_generators": [],
    }
    if include_metadata:
        for p in patterns:
            try:
                hit = await _tool_search_in_metadata(p)
                for key in metadata_acc:
                    metadata_acc[key].extend(hit.get(key, []))
            except Exception as e:
                errors.append({"area": "metadata", "pattern": p, "error": _exception_payload(e)})
        for key in metadata_acc:
            metadata_acc[key] = _dedupe_by_keys(
                _filter_by_schema(
                    metadata_acc[key],
                    schema_filter,
                ),
                ["schema_name", "entity_name", "field_name", "constraint_name", "role_name", "view_name", "generator_name"],
            )

    js_actions: list[dict] = []
    js_triggers: list[dict] = []
    js_modules: list[dict] = []
    for p in patterns:
        if include_actions:
            try:
                js_actions.extend(await _tool_search_in_js("actions", p))
            except Exception as e:
                errors.append({"area": "actions", "pattern": p, "error": _exception_payload(e)})
        if include_triggers:
            try:
                js_triggers.extend(await _tool_search_in_js("triggers", p))
            except Exception as e:
                errors.append({"area": "triggers", "pattern": p, "error": _exception_payload(e)})
        if include_modules:
            try:
                js_modules.extend(await _tool_search_in_modules(p))
            except Exception as e:
                errors.append({"area": "modules", "pattern": p, "error": _exception_payload(e)})

    js_actions = _filter_by_schema(js_actions, schema_filter)
    js_triggers = _filter_by_schema(js_triggers, schema_filter)

    user_views_rows: list[dict] = []
    if include_views:
        for p in patterns:
            try:
                rows = await _tool_funql_query(
                    "{ $needle string, $schema_name string null }: "
                    "select s.name as schema_name, uv.name as view_name, uv.query as query "
                    "from public.user_views as uv "
                    "join public.schemas as s on uv.schema_id = s.id "
                    "where uv.query ilike $needle and ($schema_name is null or s.name = $schema_name) "
                    "order by s.name, uv.name",
                    {"needle": f"%{p}%", "schema_name": schema_filter},
                )
                user_views_rows.extend(rows)
            except Exception as e:
                errors.append({"area": "user_views", "pattern": p, "error": _exception_payload(e)})
    user_views_rows = _dedupe_by_keys(user_views_rows, ["schema_name", "view_name"])

    return {
        "input": {"schema": schema, "entity": entity, "field": field},
        "patterns_used": patterns,
        "summary": {
            "user_views_count": len(user_views_rows),
            "actions_count": len(_dedupe_by_keys(js_actions, ["schema_name", "action_name"])),
            "triggers_count": len(_dedupe_by_keys(js_triggers, ["schema_name", "trigger_name", "entity_name"])),
            "modules_count": len(_dedupe_by_keys(js_modules, ["module_name"])),
            "metadata_matches_count": sum(len(v) for v in metadata_acc.values()),
        },
        "user_views": user_views_rows,
        "actions": _dedupe_by_keys(js_actions, ["schema_name", "action_name"]),
        "triggers": _dedupe_by_keys(js_triggers, ["schema_name", "trigger_name", "entity_name"]),
        "modules": _dedupe_by_keys(js_modules, ["module_name"]),
        "metadata": metadata_acc,
        "errors": errors,
    }


async def _tool_safe_update_view_query(
    *,
    schema: str,
    view_name: str,
    from_text: str,
    to_text: str,
    replace_count: Optional[int] = None,
    dry_run: bool = False,
    validate_before_commit: bool = True,
) -> dict:
    rows = await _tool_funql_query(
        "{ $schema_name string, $view_name string }: "
        "select uv.id, uv.query "
        "from public.user_views as uv "
        "join public.schemas as s on uv.schema_id = s.id "
        "where s.name = $schema_name and uv.name = $view_name",
        {"schema_name": schema, "view_name": view_name},
    )
    if not rows:
        return {"error": f"User view '{schema}.{view_name}' not found", "type": "not_found"}
    view_id = rows[0]["id"]
    old_query = rows[0].get("query") or ""
    occurrences = old_query.count(from_text)
    if occurrences == 0:
        return {
            "error": "No occurrences found in view query",
            "type": "no_match",
            "schema": schema,
            "view_name": view_name,
            "from_text": from_text,
        }
    effective_count = replace_count if replace_count is not None else occurrences
    new_query = old_query.replace(from_text, to_text, replace_count or -1)

    validation: dict[str, Any] = {"ok": True, "skipped": not validate_before_commit}
    if validate_before_commit:
        validation = await _tool_validate_funql(new_query, {})
        if not validation.get("ok", False):
            return {
                "error": "Replacement produced invalid FunQL query",
                "type": "validation_failed",
                "schema": schema,
                "view_name": view_name,
                "occurrences": occurrences,
                "planned_replacements": effective_count,
                "validation": validation,
            }

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "schema": schema,
            "view_name": view_name,
            "view_id": view_id,
            "occurrences": occurrences,
            "planned_replacements": effective_count,
            "validation": validation,
        }

    result = await _tool_transaction(
        [
            {
                "type": "update",
                "entity": {"schema": "public", "name": "user_views"},
                "id": view_id,
                "entries": {"query": new_query},
            }
        ]
    )
    return {
        "ok": True,
        "dry_run": False,
        "schema": schema,
        "view_name": view_name,
        "view_id": view_id,
        "occurrences": occurrences,
        "applied_replacements": effective_count,
        "validation": validation,
        "transaction": result,
    }


async def _entity_id(schema: str, entity: str) -> Optional[int]:
    rows = await _tool_funql_query(
        "{ $schema_name string, $entity_name string }: "
        "select e.id "
        "from public.entities as e "
        "join public.schemas as s on e.schema_id = s.id "
        "where s.name = $schema_name and e.name = $entity_name",
        {"schema_name": schema, "entity_name": entity},
    )
    if not rows:
        return None
    return rows[0]["id"]


async def _computed_field_row(entity_id: int, field_name: str) -> Optional[dict]:
    rows = await _tool_funql_query(
        "{ $entity_id int, $field_name string }: "
        "select id, name, expression, is_virtual, is_materialized, allow_broken, description, metadata "
        "from public.computed_fields "
        "where entity_id = $entity_id and name = $field_name",
        {"entity_id": entity_id, "field_name": field_name},
    )
    return rows[0] if rows else None


async def _hierarchy_field_conflicts(schema: str, entity: str, field_name: str) -> list[dict]:
    entities = await _tool_funql_query(
        "{ $schema_name string }: "
        "select e.id, e.name, e.parent_id=>id as parent_id "
        "from public.entities as e "
        "join public.schemas as s on e.schema_id = s.id "
        "where s.name = $schema_name",
        {"schema_name": schema},
    )
    fields = await _tool_funql_query(
        "{ $schema_name string, $field_name string }: "
        "select e.id as entity_id, e.name as entity_name, cf.is_virtual "
        "from public.computed_fields as cf "
        "join public.entities as e on cf.entity_id = e.id "
        "join public.schemas as s on e.schema_id = s.id "
        "where s.name = $schema_name and cf.name = $field_name",
        {"schema_name": schema, "field_name": field_name},
    )
    by_id = {e["id"]: e for e in entities}
    name_to_id = {e["name"]: e["id"] for e in entities}
    target_id = name_to_id.get(entity)
    if not target_id:
        return []

    children: dict[int, list[int]] = {}
    for e in entities:
        pid = e.get("parent_id")
        if pid is None:
            continue
        children.setdefault(pid, []).append(e["id"])

    ancestors: set[int] = set()
    cur = by_id[target_id].get("parent_id")
    while cur is not None and cur not in ancestors:
        ancestors.add(cur)
        cur = by_id.get(cur, {}).get("parent_id")

    descendants: set[int] = set()
    stack = list(children.get(target_id, []))
    while stack:
        cid = stack.pop()
        if cid in descendants:
            continue
        descendants.add(cid)
        stack.extend(children.get(cid, []))

    conflicts = []
    for row in fields:
        eid = row["entity_id"]
        if eid == target_id:
            continue
        if eid in ancestors:
            scope = "ancestor"
        elif eid in descendants:
            scope = "descendant"
        else:
            scope = "unrelated"
        conflicts.append(
            {
                "scope": scope,
                "entity_id": eid,
                "entity_name": row.get("entity_name"),
                "is_virtual": row.get("is_virtual"),
            }
        )
    return conflicts


async def _tool_upsert_computed_field(
    *,
    schema: str,
    entity: str,
    field_name: str,
    expression: str,
    is_virtual: bool = True,
    is_materialized: bool = False,
    allow_broken: bool = False,
    description: str = "",
    metadata: Optional[dict] = None,
    auto_virtual_fallback: bool = True,
) -> dict:
    metadata = metadata or {}
    entity_id = await _entity_id(schema, entity)
    if entity_id is None:
        return {"error": f"Entity '{schema}.{entity}' not found", "type": "not_found"}

    existing = await _computed_field_row(entity_id, field_name)
    conflicts = await _hierarchy_field_conflicts(schema, entity, field_name)
    hierarchy_conflicts = [c for c in conflicts if c["scope"] in ("ancestor", "descendant")]

    effective_is_virtual = is_virtual
    fallback_reason = None
    if hierarchy_conflicts and not is_virtual and auto_virtual_fallback:
        effective_is_virtual = True
        fallback_reason = "Hierarchy has same-name computed field in ancestor/descendant; switched to is_virtual=true"

    entries = {
        "name": field_name,
        "expression": expression,
        "is_virtual": effective_is_virtual,
        "is_materialized": is_materialized,
        "allow_broken": allow_broken,
        "description": description,
        "metadata": metadata,
        "entity_id": entity_id,
    }

    try:
        if existing:
            tx = await _tool_transaction(
                [
                    {
                        "type": "update",
                        "entity": {"schema": "public", "name": "computed_fields"},
                        "id": existing["id"],
                        "entries": {
                            "expression": expression,
                            "is_virtual": effective_is_virtual,
                            "is_materialized": is_materialized,
                            "allow_broken": allow_broken,
                            "description": description,
                            "metadata": metadata,
                        },
                    }
                ]
            )
            op = "update"
            result_id = existing["id"]
        else:
            tx = await _tool_transaction(
                [
                    {
                        "type": "insert",
                        "entity": {"schema": "public", "name": "computed_fields"},
                        "entries": entries,
                    }
                ]
            )
            op = "insert"
            result_id = tx.get("results", [{}])[0].get("id")
    except Exception as e:
        payload = _exception_payload(e)
        if auto_virtual_fallback and not effective_is_virtual and "Computed field names clash" in (payload.get("error") or ""):
            if existing:
                tx = await _tool_transaction(
                    [
                        {
                            "type": "update",
                            "entity": {"schema": "public", "name": "computed_fields"},
                            "id": existing["id"],
                            "entries": {
                                "expression": expression,
                                "is_virtual": True,
                                "is_materialized": is_materialized,
                                "allow_broken": allow_broken,
                                "description": description,
                                "metadata": metadata,
                            },
                        }
                    ]
                )
                op = "update"
                result_id = existing["id"]
            else:
                entries["is_virtual"] = True
                tx = await _tool_transaction(
                    [
                        {
                            "type": "insert",
                            "entity": {"schema": "public", "name": "computed_fields"},
                            "entries": entries,
                        }
                    ]
                )
                op = "insert"
                result_id = tx.get("results", [{}])[0].get("id")
            fallback_reason = "Retry succeeded with is_virtual=true after clash error"
            effective_is_virtual = True
        else:
            raise

    return {
        "ok": True,
        "operation": op,
        "schema": schema,
        "entity": entity,
        "field_name": field_name,
        "field_id": result_id,
        "requested_is_virtual": is_virtual,
        "effective_is_virtual": effective_is_virtual,
        "hierarchy_conflicts": hierarchy_conflicts,
        "fallback_reason": fallback_reason,
        "transaction": tx,
    }


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
