import io
import aiohttp

async def simple_get_image(url):
    async with aiohttp.ClientSession(headers={
        'User-Agent': 'Fletcher/0.1 (operator@noblejury.com)'
        }) as session:
        async with session.get(url) as resp:
            buffer = io.BytesIO(await resp.read())
            if resp.status != 200:
                raise Exception('HttpProcessingError: '+str(resp.status)+" Retrieving image failed!")
            return buffer
