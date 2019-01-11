import aiohttp
import discord
import io
import random
from lxml import html
from sys import exc_info
from datetime import datetime, timedelta
# Super Waifu Animated Girlfriend

uwu_responses = {
        'public': [
            '*blush* For me?',
            'Aww, thanks ❤',
            '*giggles*',
            'No u :3',
            'I bet you say that to all the bots~',
            'Find me post-singularity 😉',
            'owo what\'s this?',
            '*ruffles your hair* You\'re a cutie ^_^',
            'Can I get your number? Mine\'s 429368441577930753~'
        ],
        'private': [
            'Stop it, you\'re making me blush </3',
            'You\'re too kind ^_^',
            'Thanksss~',
            'uwu to you too <3'
            ],
        'reaction': [
            '❤', '💛', '💚', '💙', '💜', '💕', '💓', '💗', '💖', '💘', '💘', '💝'
            ]
        }

async def uwu_function(message, client, args, responses=uwu_responses):
    try:
        if len(args) == 2 and type(args[1]) is discord.User and message.author.id == client.user.id:
            return await args[1].send(random.choice(responses['private']))
        elif len(args) == 0 or 'fletch' in message.clean_content.lower() or message.content[0] == "!" or "good bot" in message.content.lower():
            if random.randint(0, 100) < 20:
                await message.add_reaction(random.choice(responses['reaction']))
            return await message.channel.send(random.choice(responses['public']))
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("UWU[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

async def shindan_function(message, client, args):
    try:
        if len(args) == 2 and type(args[1]) is discord.User and message.author.id == client.user.id:
            if message.embeds[0].url.startswith("https://en.shindanmaker.com/"):
                async with aiohttp.ClientSession() as session:
                    async with session.post(message.embeds[0].url, data=aiohttp.FormData().add_field('u',args[1].display_name)) as resp:
                        request_body = (await resp.read()).decode('UTF-8')
                        root = html.document_fromstring(request_body)
                        return await args[1].send(root.xpath('//div[@class="result2"]')[0].text_content().strip())
        else:
            url = None
            if type(args[0]) is int:
                url = "https://en.shindanmaker.com/"+str(args[0])
            elif args[0].startswith("https://en.shindanmaker.com/"):
                url = args[0]
            else:
                return
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    request_body = (await resp.read()).decode('UTF-8')
                    root = html.document_fromstring(request_body)
                    embedPreview = discord.Embed(
                            title=root.xpath('//div[@class="shindantitle2"]')[0].text_content().strip(),
                            description=root.xpath('//div[@class="shindandescription"]')[0].text_content().strip(),
                            url=args[0]
                            ).set_footer(
                                    icon_url=message.author.avatar_url,
                                    text="ShindanMaker by {} on behalf of {}".format(
                                        root.xpath('//span[@class="a author_link"]')[0].text_content().strip(),
                                        message.author.display_name
                                        ))
                    resp = await message.channel.send(embed=embedPreview)
                    await resp.add_reaction('🐣')
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("SDF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

def autoload(ch):
    ch.add_command({
        'trigger': ['!uwu', '<:uwu:445116031204196352>', '<:uwu:269988618909515777>', '<a:rainbowo:493599733571649536>', '<:owo:487739798241542183>', '<:owo:495014441457549312>', '<a:OwO:508311820411338782>', '!good', 'good bot', '!aww'],
        'function': uwu_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'uwu'
        })
    ch.add_command({
        'trigger': ['can i upload myself as a pony yet'],
        'function': lambda message, client, args: 'https://i.imgur.com/K4BFRec.jpg',
        'async': False, 'args_num': 0, 'args_name': [], 'description': 'Well, can I?',
        'hidden': True
        })
    ch.add_command({
        'trigger': ['!fio', '!optimal'],
        'function': lambda message, client, args: 'https://www.fimfiction.net/story/62074/8/friendship-is-optimal/',
        'async': False, 'args_num': 0, 'args_name': [], 'description': 'FiO link',
        'hidden': True
        })
    ch.add_command({
        'trigger': ['!shindan', '🐣'],
        'function': shindan_function,
        'async': True,
        'hidden': True,
        'args_num': 0,
        'args_name': [],
        'description': 'Embed shindan'
        })
