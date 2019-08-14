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
        params = {
                'random': 'true',
                'limit': 1,
                'tags': f'{args[0]} rating:safe'
                }
        async with session.get(f'{base_url}/posts.json', params=params) as resp:
            response_body = await resp.json()
            logger.debug(resp.url)
            if len(response_body) == 0:
                return await message.channel.send('No images found for query')
            async with session.get(response_body[0]['file_url']) as resp:
                buffer = io.BytesIO(await resp.read())
                if resp.status != 200:
                    raise Exception('HttpProcessingError: '+str(resp.status)+" Retrieving image failed!")
                await message.channel.send(f"<{base_url}/posts/{response_body[0]['md5']}>", files=[discord.File(buffer, response_body[0]["md5"]+"."+response_body[0]["file_ext"])])
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
        'admin': False,
        'hidden': False,
        'args_num': 1,
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
