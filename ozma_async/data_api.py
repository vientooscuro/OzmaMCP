import time
from typing import Optional, Any
from prometheus_client import Counter, Histogram

import httpx

from ozma_async import async_auth_api, httpx_client

import asyncio
import traceback

API_PATH = async_auth_api.api_path

OZMA_REQUESTS_TOTAL = Counter('ozma_api_requests_total', 'Total Ozma API requests', ['method', 'endpoint', 'status'])
OZMA_REQUEST_DURATION = Histogram('ozma_api_request_duration_seconds', 'Ozma API request duration', ['method', 'endpoint'])
OZMA_DB_OPERATIONS = Counter('ozma_db_operations_total', 'Total database operations', ['type', 'schema', 'table_name'])

_insert_lock: Optional[asyncio.Lock] = None
_insert_lock_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_client() -> httpx.AsyncClient:
    return httpx_client.get_client()


def _get_insert_lock() -> asyncio.Lock:
    global _insert_lock, _insert_lock_loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.Lock()

    if _insert_lock is None or _insert_lock_loop != loop or (loop and loop.is_closed()):
        _insert_lock = asyncio.Lock()
        _insert_lock_loop = loop
    return _insert_lock


async def get_user_view_info(schema: str, user_view: str, params: dict) -> Optional[str]:
    """Async version of user view info fetch."""
    if not async_auth_api.access_token:
        await async_auth_api.init_token()
    url = f"{API_PATH}views/by_name/{schema}/{user_view}/info"
    endpoint = f"views/by_name/{schema}/{user_view}/info"
    start_time = time.time()
    try:
        r = await _get_client().get(url, params=params, headers={"Authorization": "Bearer " + (async_auth_api.access_token or "")})
        OZMA_REQUEST_DURATION.labels(method='GET', endpoint=endpoint).observe(time.time() - start_time)
        OZMA_REQUESTS_TOTAL.labels(method='GET', endpoint=endpoint, status=r.status_code).inc()
        return r.text
    except httpx.RequestError as e:
        OZMA_REQUESTS_TOTAL.labels(method='GET', endpoint=endpoint, status='error').inc()
        return None


class AsyncOzmaApi:
    async def _ensure_token(self):
        if not async_auth_api.access_token:
            await async_auth_api.init_token()

    async def simple_query(self, query: str, parse_data: bool = False, _retry: bool = True) -> Optional[Any]:
        await self._ensure_token()
        url = f"{API_PATH}views/anonymous/entries"
        endpoint = "views/anonymous/entries"
        start_time = time.time()
        try:
            r = await _get_client().get(
                    url,
                    params={"__query": query},
                    headers={"Authorization": "Bearer " + (async_auth_api.access_token or "")},
                )
            OZMA_REQUEST_DURATION.labels(method='GET', endpoint=endpoint).observe(time.time() - start_time)
            OZMA_REQUESTS_TOTAL.labels(method='GET', endpoint=endpoint, status=r.status_code).inc()
            if r.status_code == 401 and _retry:
                await async_auth_api.init_token()
                return await self.simple_query(query, parse_data=parse_data, _retry=False)
            if parse_data:
                data = r.json()
                return self.parse_data_to_dictionary(data, True)
            else:
                return r.text
        except (httpx.TimeoutException, httpx.TooManyRedirects, httpx.RequestError) as e:
            OZMA_REQUESTS_TOTAL.labels(method='GET', endpoint=endpoint, status='error').inc()
            print(e)

    async def query(self, columns: list[str], table_name: str, conditions: Optional[str]):
        query = "select " + ",".join(columns) + " from " + table_name
        if conditions is not None:
            query += " where " + conditions
        return await self.simple_query(query, parse_data=True)

    async def get_user_view(
        self,
        schema: str,
        user_view: str,
        params: dict,
        parse_data: bool = False,
        parse_pun: bool = False,
        _retry: bool = True,
    ):
        await self._ensure_token()
        url = f"{API_PATH}views/by_name/{schema}/{user_view}/entries"
        endpoint = f"views/by_name/{schema}/{user_view}/entries"
        params = {k: v for k, v in params.items() if v is not None}
        start_time = time.time()
        try:
            r = await _get_client().get(url, params=params, headers={"Authorization": "Bearer " + (async_auth_api.access_token or "")})
            OZMA_REQUEST_DURATION.labels(method='GET', endpoint=endpoint).observe(time.time() - start_time)
            OZMA_REQUESTS_TOTAL.labels(method='GET', endpoint=endpoint, status=r.status_code).inc()
            if r.status_code == 401 and _retry:
                await async_auth_api.init_token()
                return await self.get_user_view(
                    schema, user_view, params, parse_data=parse_data, parse_pun=parse_pun, _retry=False
                )
            else:
                data = r.json()
                if parse_data:
                    return self.parse_data_to_dictionary(data, parse_pun)
                return data
        except (httpx.TimeoutException, httpx.TooManyRedirects, httpx.RequestError) as e:
            OZMA_REQUESTS_TOTAL.labels(method='GET', endpoint=endpoint, status='error').inc()
            print(e)

    async def insert(self, params: dict, _retry: bool = True):
        await self._ensure_token()
        url = f"{API_PATH}transaction"
        endpoint = "transaction"
        start_time = time.time()
        try:
            async with _get_insert_lock():
                r = await _get_client().post(url, json=params, headers={"Authorization": "Bearer " + (async_auth_api.access_token or "")})
            
            OZMA_REQUEST_DURATION.labels(method='POST', endpoint=endpoint).observe(time.time() - start_time)
            OZMA_REQUESTS_TOTAL.labels(method='POST', endpoint=endpoint, status=r.status_code).inc()

            if r.status_code == 200:
                # Track granular operations
                ops = params.get('operations', [])
                for op in ops:
                    op_type = op.get('type')
                    entity = op.get('entity', {})
                    schema_name = entity.get('schema', 'unknown')
                    table_name = entity.get('name', 'unknown')
                    OZMA_DB_OPERATIONS.labels(type=op_type, schema=schema_name, table_name=table_name).inc()

            if r.status_code == 401 and _retry:
                await async_auth_api.init_token()
                return await self.insert(params, _retry=False)
            else:
                if r.status_code != 200:
                    return None
                data = r.json()
                return data
        except (httpx.TimeoutException, httpx.TooManyRedirects, httpx.RequestError, Exception) as e:
            OZMA_REQUESTS_TOTAL.labels(method='POST', endpoint=endpoint, status='error').inc()
            print(e)

    async def run_action(self, schema: str, action_name: str, params: dict, _retry: bool = True):
        await self._ensure_token()
        url = f"{API_PATH}actions/{schema}/{action_name}/run"
        endpoint = f"actions/{schema}/{action_name}/run"
        start_time = time.time()
        try:
            r = await _get_client().post(url, json=params, headers={"Authorization": "Bearer " + (async_auth_api.access_token or "")})
            OZMA_REQUEST_DURATION.labels(method='POST', endpoint=endpoint).observe(time.time() - start_time)
            OZMA_REQUESTS_TOTAL.labels(method='POST', endpoint=endpoint, status=r.status_code).inc()
            if r.status_code == 401 and _retry:
                await async_auth_api.init_token()
                return await self.run_action(schema, action_name, params, _retry=False)
            else:
                data = r.json()
                if r.status_code == 200:
                    return data
                return None
        except (httpx.TimeoutException, httpx.TooManyRedirects, httpx.RequestError) as e:
            OZMA_REQUESTS_TOTAL.labels(method='POST', endpoint=endpoint, status='error').inc()
            print(e)

    def parse_data_to_dictionary(self, data, parse_pun):
        if "info" not in data:
            return None
        info = data["info"]
        if "columns" not in info:
            return None

        if "result" not in data:
            return None

        result = data["result"]
        if "rows" not in result:
            return None

        rows = result["rows"]
        columns = info["columns"]

        entities = []
        for index in range(len(rows)):
            entity = {}

            row = rows[index]
            if "mainId" in row:
                entity["mainId"] = row["mainId"]

            values = row["values"]

            for column_index in range(len(columns)):
                column = columns[column_index]
                if "name" in column:
                    name = column["name"]
                else:
                    continue
                if "value" in values[column_index]:
                    value = values[column_index]["value"]
                    if parse_pun and "pun" in values[column_index]:
                        value = {"id": value, "data": values[column_index]["pun"]}
                else:
                    continue

                entity[name] = value

            entities.append(entity)

        return entities
