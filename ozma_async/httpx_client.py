import asyncio
from typing import Optional
import httpx

_client: Optional[httpx.AsyncClient] = None
_client_loop: Optional[asyncio.AbstractEventLoop] = None

async def _safe_aclose(client: httpx.AsyncClient):
    try:
        await client.aclose()
    except Exception:
        pass

def get_client() -> httpx.AsyncClient:
    global _client, _client_loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Fallback for sync contexts if ever called
        import helpers
        return httpx.AsyncClient(timeout=30.0, verify=not helpers.is_debug)

    if _client is None or _client.is_closed or _client_loop != loop:
        if _client and not _client.is_closed:
            # Only try to close if it's the same loop and it's still running.
            if _client_loop == loop and not loop.is_closed():
                try:
                    loop.create_task(_safe_aclose(_client))
                except Exception:
                    pass
        import helpers
        _client = httpx.AsyncClient(timeout=30.0, verify=not helpers.is_debug)
        _client_loop = loop
    return _client
