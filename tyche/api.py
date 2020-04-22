import os
import json
import aiohttp
from contextlib import AsyncExitStack

API_ROOT = os.environ.get("API_ROOT", "http://localhost:8000/api/")
API_KEY = os.environ.get("API_KEY", "invalid key")


async def fetch(url, guild_id):
    headers = {
        "Authorization": f"Token {API_KEY}",
    }
    params = {
        "server_id": guild_id,
    }
    full_url = f"{API_ROOT}{url}/"
    async with AsyncExitStack() as stack:
        session = await stack.enter_async_context(aiohttp.ClientSession())
        response = await stack.enter_async_context(
            session.get(full_url, headers=headers, params=params)
        )
        return await response.text()


async def get_prefix(bot, message):
    guild_id = getattr(message.guild, "id", None)
    if guild_id:
        payload = await fetch("prefix", guild_id)
        return json.loads(payload)["prefix"]
    return ""
