import aiohttp
import discord
import io
import messagefuncs
import random
import re
from lxml import html, etree
from sys import exc_info
from datetime import datetime, timedelta
from markdownify import markdownify
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

async def retrowave_function(message, client, args):
    try:
        async with aiohttp.ClientSession() as session:
            params = aiohttp.FormData()
            params.add_field('bcg',random.randint(1, 5))
            params.add_field('txt',random.randint(1, 4))
            text_parts = message.content
            text_parts = messagefuncs.sanitize_font.sub('', text_parts)
            if '/' in text_parts:
                if len(args) == 2 and type(args[1]) is discord.User:
                    pass
                else:
                    text_parts = text_parts[10:].strip()
                text_parts = [part.strip() for part in text_parts.split('/')]
                if len(text_parts) == 0:
                    text_parts = ['', '', '']
                elif len(text_parts) == 1:
                    text_parts = ['', text_parts[0], '']
                elif len(text_parts) == 2:
                    text_parts += ['']
            else:
                text_parts = text_parts.split()
                if len(args) == 2 and type(args[1]) is discord.User:
                    pass
                else:
                    text_parts = text_parts[1:]
                part_len = int(len(text_parts)/3)
                if part_len > 1:
                    text_parts = [" ".join(text_parts[:part_len]), " ".join(text_parts[part_len:2*part_len]), " ".join(text_parts[2*part_len:])]
                else:
                    text_parts = [" ".join(text_parts[0:1]), " ".join(text_parts[1:2]), " ".join(text_parts[2:])]
            params.add_field('text1',text_parts[0])
            params.add_field('text2',text_parts[1])
            params.add_field('text3',text_parts[2])
            print("RWF: "+str(text_parts))
            async with session.post('https://m.photofunia.com/categories/all_effects/retro-wave?server=2', data=params) as resp:
                request_body = (await resp.read()).decode('UTF-8')
                root = html.document_fromstring(request_body)
                async with session.get(root.xpath('//a[@class="download-button"]')[0].attrib['href']) as resp:
                    buffer = io.BytesIO(await resp.read())
                return await message.channel.send(files=[discord.File(buffer, 'retrowave.jpg')])
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("RWF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

async def shindan_function(message, client, args):
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            if message.author.id != 429368441577930753:
                print("SDF: Backing out, not my message.")
                return
            if message.embeds[0].url.startswith("https://en.shindanmaker.com/"):
                async with aiohttp.ClientSession() as session:
                    params = aiohttp.FormData()
                    params.add_field('u',args[1].display_name)
                    async with session.post(message.embeds[0].url, data=params) as resp:
                        request_body = (await resp.read()).decode('UTF-8')
                        root = html.document_fromstring(request_body)
                        return await args[1].send(root.xpath('//div[@class="result2"]')[0].text_content().strip())
        else:
            url = None
            if args[0].isdigit():
                url = "https://en.shindanmaker.com/"+args[0]
            elif args[0].startswith("https://en.shindanmaker.com/"):
                url = args[0]
            else:
                await message.channel.send('Please specify a name-based shindan to use from https://en.shindanmaker.com/')
                return
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    request_body = (await resp.read()).decode('UTF-8')
                    root = html.document_fromstring(request_body)
                    author = ""
                    if root.xpath('//span[@class="a author_link"]'):
                        author = " by "+root.xpath('//span[@class="a author_link"]')[0].text_content().strip()
                    embedPreview = discord.Embed(
                            title=root.xpath('//div[@class="shindantitle2"]')[0].text_content().strip(),
                            description=root.xpath('//div[@class="shindandescription"]')[0].text_content().strip(),
                            url=url
                            ).set_footer(
                                    icon_url=message.author.avatar_url,
                                    text="ShindanMaker {} on behalf of {}".format(
                                        author,
                                        message.author.display_name
                                        ))
                    resp = await message.channel.send(embed=embedPreview)
                    await resp.add_reaction('📛')
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("SDF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

pick_regex = re.compile(r'[,\s]\s*(?:and|or|but|nor|for|so|yet)?\s*')

async def pick_function(message, client, args):
    try:
        if args[0] in ["between", "among", "in", "of"]:
            args = args[1:]
        many = 1
        try:
            if len(args) > 2:
                many = int(args[0])
                args = args[2:]
        except ValueError:
            pass
        choices = [choice.strip() for choice in pick_regex.split(" ".join(args).rstrip(" ?.!")) if choice.strip()]
        if len(choices) == 1:
            choices = args
        try:
            return await message.channel.send("I'd say "+", ".join(random.sample(choices, many)))
        except ValueError:
            return await message.channel.send("I can't pick that many! Not enough options")
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("PF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

async def scp_function(message, client, args):
    try:
        url = None
        if len(args) == 0:
            if '-' in message.content:
                args.append(message.content.split('-')[1].strip())
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://www.scp-wiki.net/random:random-scp') as resp:
                        request_body = (await resp.read()).decode('UTF-8')
                        args.append(request_body.split('iframe-redirect#')[1].split('"')[0].split('-')[2])
        if args[0].isdigit():
             url = "http://www.scp-wiki.net/scp-"+args[0]
        elif args[0].startswith("http://www.scp-wiki.net/"):
            url = args[0]
        else:
            await message.channel.send('Please specify a SCP number from http://www.scp-wiki.net/')
            return
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                request_body = (await resp.read()).decode('UTF-8')
                root = html.document_fromstring(request_body)
                author = ""
                title = root.xpath('//div[@id="page-title"]')[0].text_content().strip()
                content = root.xpath('//div[@id="page-content"]/p[strong]')
                add_fields = True
                try:
                    for i in range(0, 4):
                        content[i][0].drop_tree()
                    description = str(markdownify(etree.tostring(content[3]).decode()[3:-5].strip())[:2000])
                except IndexError as e:
                    print(f'SCP: {e}')
                    add_fields = False
                    description = str(markdownify(etree.tostring(root.xpath('//div[@id="page-content"]')[0]).decode()))[:2000].strip()
                    if not description:
                        description = root.xpath('//div[@id="page-content"]').text_content()[:2000].strip()
                embedPreview = discord.Embed(
                        title=title,
                        description=description,
                        url=url
                        )
                embedPreview.set_footer(
                        icon_url='http://download.nova.anticlack.com/fletcher/scp.png',
                        text=f'On behalf of {message.author.display_name}'
                        )
                if root.xpath('//div[@class="scp-image-block block-right"]'):
                    embedPreview.set_thumbnail(url=root.xpath('//div[@class="scp-image-block block-right"]/img')[0].attrib['src'])
                if add_fields:
                    embedPreview.add_field(name='Object Class', value=str(markdownify(etree.tostring(content[1]).decode()[3:-5].strip()))[:2000], inline=True)
                    scp = str(markdownify(etree.tostring(content[2]).decode()[3:-5].strip()))[:2000]
                    if scp:
                        embedPreview.add_field(name='Special Containment Procedures', value=scp, inline=False)
                embedPreview.add_field(name='Tags', value=', '.join([node.text_content().strip() for node in root.xpath('//div[@class="page-tags"]/span/a')]), inline=True)
                resp = await message.channel.send(embed=embedPreview)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("SCP[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        if embedPreview:
            print('SCP embedPreview: '+str(embedPreview.to_dict()))
        await message.add_reaction('🚫')


def autoload(ch):
    ch.add_command({
        'trigger': ['!uwu', '<:uwu:445116031204196352>', '<:uwu:269988618909515777>', '<a:rainbowo:493599733571649536>', '<:owo:487739798241542183>', '<:owo:495014441457549312>', '<a:OwO:508311820411338782>', '!good', '!aww'],
        'function': uwu_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'uwu'
        })
    ch.add_command({
        'trigger': ['!pick'],
        'function': pick_function,
        'async': True,
        'args_num': 1,
        'args_name': [],
        'description': 'pick among comma seperated choices'
        })
    ch.add_command({
        'trigger': ['!fio', '!optimal'],
        'function': lambda message, client, args: 'https://www.fimfiction.net/story/62074/8/friendship-is-optimal/',
        'async': False, 'args_num': 0, 'args_name': [], 'description': 'FiO link',
        'hidden': True
        })
    ch.add_command({
        'trigger': ['!shindan', '📛'],
        'function': shindan_function,
        'async': True,
        'args_num': 0,
        'long_run': 'author',
        'args_name': [],
        'description': 'Embed shindan'
        })
    ch.add_command({
        'trigger': ['!scp'],
        'function': scp_function,
        'async': True,
        'args_num': 0,
        'long_run': True,
        'args_name': [],
        'description': 'SCP Function'
        })
    ch.add_command({
        'trigger': ['!retrowave'],
        'function': retrowave_function,
        'async': True,
        'args_num': 0,
        'long_run': True,
        'args_name': [],
        'description': 'Retrowave Text Generator'
        })
