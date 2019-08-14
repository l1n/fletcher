import aiohttp
import discord
import io
from sys import exc_info

import logging
logger = logging.getLogger('fletcher')


session = None
base_url = "https://testbooru.donmai.us"

async def posts_search_function(message, client, args):
    global config
    try:
        params = {
                'random': 'true',
                'limit': 1,
                'tags': f'{args[0]}+rating:safe'
                }
        async with session.get(f'{base_url}/posts.json', params=params) as resp:
            response_body = await resp.json()
            logger.debug(resp.status)
            logger.debug(response_body)
            async with session.get(response_body[0]['file_url']) as resp:
                buffer = io.BytesIO(await resp.read())
                if resp.status != 200:
                    raise Exception('HttpProcessingError: '+str(resp.status)+" Retrieving image failed!")
                await message.channel.send(files=[discord.File(buffer, image.get("filename"))])
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
        'hidden': True,
        'args_num': 1,
        'args_name': ['tag'],
        'description': 'Search Danbooru for an image tagged as argument'
        })
    if session:
        session.close()
    session = aiohttp.ClientSession(auth=aiohttp.BasicAuth(login=config['danbooru']['user'], password=config['danbooru']['api_key']), headers={'User-Agent': 'Fletcher/0.1 (operator@noblejury.com)'})
