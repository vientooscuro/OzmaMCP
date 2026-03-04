import os
import asyncio
import traceback
import httpx
import aiofiles
from ozma_async import httpx_client
from ozma_async.background_loop import run_in_background

REFRESH_TOKEN_PATH = "refresh_token"
ACCESS_TOKEN_PATH = "access_token"
CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
USERNAME = "username"
PASSWORD = "password"
GRAND_TYPE = "grant_type"
REFRESH_TOKEN = "refresh_token"
ACCESS_TOKEN = "access_token"
# client_id = "tinkoffozmasync"
# client_secret = "b9e5f47a-bc97-4146-abe1-048d95d396d5"
# auth_url = "https://account.ozma.io/auth/realms/default/protocol/openid-connect/token"
# api_path = "https://gogolschool.api.ozma.org/"

client_id = "ozmadb"
client_secret = "cKIu9citwiEBBJjZkMaKVoinzxGOb37h"
auth_url = "https://ozma.gogol.school/auth/realms/ozma/protocol/openid-connect/token"
api_path = "https://ozma.gogol.school/api/"

# In-memory access token
access_token: str | None = ""


async def init_token():
    """Initialize or refresh access token asynchronously."""
    global access_token
    try:
        if access_token:
            ok = await check_token(access_token)
            if ok:
                return

        # Try read previously stored access token
        if os.path.exists(ACCESS_TOKEN_PATH) and os.path.getsize(ACCESS_TOKEN_PATH) > 0:
            async with aiofiles.open(ACCESS_TOKEN_PATH, "r") as f:
                data = await f.read()
            if data:
                ok = await check_token(data)
                if ok:
                    access_token = data
                    return

        # Try refresh token
        if os.path.exists(REFRESH_TOKEN_PATH) and os.path.getsize(REFRESH_TOKEN_PATH) > 0:
            async with aiofiles.open(REFRESH_TOKEN_PATH, "r") as f:
                stored_refresh = await f.read()
            token = await get_token_by_refresh_token(stored_refresh)
            if token is None:
                access_token = await get_token_by_password()
            else:
                access_token = token
        else:
            access_token = await get_token_by_password()

        if not access_token:
            run_in_background(_retry_init_token())
    except Exception:
        run_in_background(_retry_init_token())


async def _retry_init_token():
    await asyncio.sleep(60.0)
    await init_token()


async def get_token_by_password():
    grant_type = "password"
    username = "api@gogol.school"
    password = "Qomcos-8dowxy-zemjav"
    try:
        client = httpx_client.get_client()
        r = await client.post(auth_url, data={
            CLIENT_ID: client_id,
            CLIENT_SECRET: client_secret,
            USERNAME: username,
            PASSWORD: password,
            GRAND_TYPE: grant_type
        })
        return await parse_token_request(r)
    except httpx.RequestError:
        return None


async def get_token_by_refresh_token(refresh_token: str):
    grant_type = "refresh_token"
    try:
        client = httpx_client.get_client()
        r = await client.post(auth_url, data={
            CLIENT_ID: client_id,
            CLIENT_SECRET: client_secret,
            GRAND_TYPE: grant_type,
            REFRESH_TOKEN: refresh_token
        })
        return await parse_token_request(r)
    except httpx.RequestError:
        return None


async def parse_token_request(r: httpx.Response):
    try:
        if r.status_code == 200:
            data = r.json()
            if ACCESS_TOKEN in data:
                token = data[ACCESS_TOKEN]
            else:
                return None
            if REFRESH_TOKEN in data:
                refresh_token = data[REFRESH_TOKEN]
            else:
                return None

            async with aiofiles.open(REFRESH_TOKEN_PATH, "w") as f:
                await f.write(refresh_token)
            async with aiofiles.open(ACCESS_TOKEN_PATH, "w") as f:
                await f.write(token)
            return token
        else:
            return None
    except Exception:
        return None


async def check_token(token: str) -> bool:
    """Return True if token is valid, False otherwise."""
    url = api_path + "check_access"
    try:
        client = httpx_client.get_client()
        r = await client.get(url, headers={"Authorization": "Bearer " + token})
        if r.status_code == 200:
            return True
        else:
            if r.status_code != 401:
                telegram_bot.send_error(r.text)
            return False
    except httpx.TimeoutException:
        telegram_bot.send_error(traceback.format_exc())
    except httpx.TooManyRedirects:
        telegram_bot.send_error(traceback.format_exc())
    except httpx.RequestError:
        telegram_bot.send_error(traceback.format_exc())
    return False
