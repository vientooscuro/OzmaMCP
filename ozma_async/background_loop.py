import asyncio
import threading
from typing import Coroutine

_loop: asyncio.AbstractEventLoop | None = None
_lock = threading.Lock()


def _start_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is not None and _loop.is_running():
        return _loop
    with _lock:
        if _loop is not None and _loop.is_running():
            return _loop
        _loop = asyncio.new_event_loop()
        t = threading.Thread(target=_start_loop, args=(_loop,), daemon=True)
        t.start()
        while not _loop.is_running():
            pass
    return _loop


def run_in_background(coro: Coroutine) -> None:
    """Запускает корутину в постоянном фоновом event loop.

    Безопасно вызывать из любого контекста (sync/async, любой поток).
    Event loop не привязан к Flask request lifecycle — задача гарантированно выполнится.
    """
    asyncio.run_coroutine_threadsafe(coro, _get_loop())
