import aiohttp
from base64 import b64encode
import discord
import io
from sys import exc_info

import logging
logger = logging.getLogger('fletcher')


session = None
base_url = "https://danbooru.donmai.us"

async def posts_search_function(message, client, args):
    global config
    try:
        params = {}
        params['tags'] = " ".join(args)

        channel_config = ch.config(guild=message.guild, channel=message.channel)
        if type(message.channel) is not discord.DMChannel and channel_config and channel_config.get('danbooru_default_filter'):
            params['tags'] += " "+channel_config.get('danbooru_default_filter')

        if type(message.channel) is not discord.DMChannel and message.channel.is_nsfw():
            params['tags'] += ' -loli -shota -toddlercon'
        else:
            params['tags'] += ' rating:safe'

        async with session.get(f'{base_url}/counts/posts.json', params=params) as resp:
            response_body = await resp.json()
            logger.debug(resp.url)
            if len(response_body) == 0:
                return await message.channel.send('No images found for query')
            post_count = response_body['counts']['posts']
            if post_count == 0:
                return await message.channel.send('No images found for query')
            params['random'] = 'true'
            params['limit'] = 1
            async with session.get(f'{base_url}/posts.json', params=params) as resp:
                response_body = await resp.json()
                logger.debug(resp.url)
                if len(response_body) == 0:
                    return await message.channel.send('No images found for query')
                async with session.get(response_body[0]['file_url']) as resp:
                    buffer = io.BytesIO(await resp.read())
                    if resp.status != 200:
                        raise Exception('HttpProcessingError: '+str(resp.status)+" Retrieving image failed!")
                    await message.channel.send(f"{post_count} results\n<{base_url}/posts/?md5={response_body[0]['md5']}>", files=[discord.File(buffer, response_body[0]["md5"]+"."+response_body[0]["file_ext"])])
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f"PSF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}")

def autoload(ch):
    global config 
    global session
    ch.add_command({
        'trigger': ['!dan'],
        'function': posts_search_function,
        'async': True,
        'long_run': True,
        'admin': False,
        'hidden': False,
        'args_num': 0,
        'args_name': ['tag'],
        'description': 'Search Danbooru for an image tagged as argument'
        })
    if session:
        session.close()
    bauth = b64encode(bytes(config['danbooru']['user']+":"+config['danbooru']['api_key'], "utf-8")).decode("ascii")
    session = aiohttp.ClientSession(headers={
        'User-Agent': 'Fletcher/0.1 (operator@noblejury.com)',
        'Authorization': f'Basic {bauth}'
        })
