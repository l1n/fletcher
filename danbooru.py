import aiohttp
import messagefuncs
from base64 import b64encode
from asyncache import cached
from cachetools import TTLCache
from random import shuffle
import discord
import io
from sys import exc_info

import logging

logger = logging.getLogger("fletcher")


session = None
search_results_cache = None
base_url = "https://danbooru.donmai.us"


async def posts_search_function(message, client, args):
    global config
    global session
    try:
        tags = " ".join(args)

        if type(message.channel) is not discord.DMChannel:
            channel_config = ch.scope_config(
                guild=message.guild, channel=message.channel
            )
        else:
            channel_config = dict()
        if type(message.channel) is not discord.DMChannel and channel_config.get(
            "danbooru_default_filter"
        ):
            tags += " " + channel_config.get("danbooru_default_filter")

        if type(message.channel) is not discord.DMChannel and message.channel.is_nsfw():
            tags += " -loli -shota -toddlercon"
        else:
            # Implies the above
            tags += " rating:safe"

        post_count = await count_search_function(tags)
        if not post_count or post_count == 0:
            return await messagefuncs.sendWrappedMessage(
                "No images found for query", message.channel
            )
        search_results = await warm_post_cache(tags)
        if len(search_results) == 0:
            return await messagefuncs.sendWrappedMessage(
                "No images found for query", message.channel
            )
        search_result = search_results.pop()
        if search_result["file_size"] > 8000000:
            url = search_result["preview_file_url"]
        else:
            url = search_result["file_url"]
        async with session.get(url) as resp:
            buffer = io.BytesIO(await resp.read())
            if resp.status != 200:
                raise Exception(
                    "HttpProcessingError: "
                    + str(resp.status)
                    + " Retrieving image failed!"
                )
            await messagefuncs.sendWrappedMessage(
                f"{post_count} results\n<{base_url}/posts/?md5={search_result['md5']}>",
                message.channel,
                files=[
                    discord.File(
                        buffer, f"{search_result['md5']}.{search_result['file_ext']}"
                    )
                ],
            )
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f"PSF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}")


@cached(TTLCache(1024, 86400))
async def count_search_function(tags):
    global session
    async with session.get(
        f"{base_url}/counts/posts.json", params={"tags": tags}
    ) as resp:
        response_body = await resp.json()
        logger.debug(resp.url)
        if len(response_body) == 0:
            return None
        post_count = response_body["counts"]["posts"]
        return post_count


async def warm_post_cache(tags):
    global search_results_cache
    global session
    params = {"tags": tags, "random": "true", "limit": 100}
    try:
        if search_results_cache.get(tags) and len(search_results_cache[tags]):
            return search_results_cache[tags]
        async with session.get(f"{base_url}/posts.json", params=params) as resp:
            response_body = await resp.json()
            logger.debug(resp.url)
            if len(response_body) == 0:
                return []
            shuffle(response_body)
            search_results_cache[tags] = response_body
            return search_results_cache[tags]
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f"WPC[{exc_tb.tb_lineno}]: {type(e).__name__} {e}")


async def autounload(ch):
    global session
    if session:
        await session.close()


def autoload(ch):
    global config
    global search_results_cache
    global session
    ch.add_command(
        {
            "trigger": ["!dan"],
            "function": posts_search_function,
            "async": True,
            "long_run": True,
            "admin": False,
            "hidden": False,
            "args_num": 0,
            "args_name": ["tag"],
            "description": "Search Danbooru for an image tagged as argument",
        }
    )
    if not search_results_cache:
        search_results_cache = TTLCache(1024, 86400)
    if session:
        session.close()
    bauth = b64encode(
        bytes(
            config.get("danbooru", dict()).get("user")
            + ":"
            + config.get("danbooru", dict()).get("api_key"),
            "utf-8",
        )
    ).decode("ascii")
    session = aiohttp.ClientSession(
        headers={
            "User-Agent": "Fletcher/0.1 (operator@noblejury.com)",
            "Authorization": f"Basic {bauth}",
        }
    )
