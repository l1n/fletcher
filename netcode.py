import io
import aiohttp
from sys import exc_info
import logging

logger = logging.getLogger('fletcher')

async def simple_get_image(url):
    try:
        async with aiohttp.ClientSession(headers={
            'User-Agent': 'Fletcher/0.1 (operator@noblejury.com)'
            }) as session:
            async with session.get(url) as resp:
                buffer = io.BytesIO(await resp.read())
                if resp.status != 200:
                    raise Exception('HttpProcessingError: '+str(resp.status)+" Retrieving image failed!")
                return buffer
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("SGI[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
