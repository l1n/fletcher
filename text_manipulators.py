import asyncio
import codecs
from datetime import datetime, timedelta
import discord
import io
import math
import random
from PIL import Image
from sys import exc_info

def smallcaps(text=False):
    if text:
        return text.translate(str.maketrans({'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'}))
    return None

def swapcasealpha(text=False):
    if text:
        return text.translate(str.maketrans({'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 'f': 'F', 'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J', 'k': 'K', 'l': 'L', 'm': 'M', 'n': 'N', 'o': 'O', 'p': 'P', 'q': 'Q', 'r': 'R', 's': 'S', 't': 'T', 'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X', 'y': 'Y', 'z': 'Z', 'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f', 'G': 'g', 'H': 'h', 'I': 'i', 'J': 'j', 'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n', 'O': 'o', 'P': 'p', 'Q': 'q', 'R': 'r', 'S': 's', 'T': 't', 'U': 'u', 'V': 'v', 'W': 'w', 'X': 'x', 'Y': 'y', 'Z': 'z'}))
    return None

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])

def convert_hex_to_ascii(h):
    chars_in_reverse = []
    while h != 0x0:
        chars_in_reverse.append(chr(h & 0xFF))
        h = h >> 8

    chars_in_reverse.reverse()
    return ''.join(chars_in_reverse)


async def scramble_function(message, client, args):
    try:
        input_image_blob = io.BytesIO()
        await message.attachments[0].save(input_image_blob)
        if len(args) != 2 or type(args[1]) is not discord.User or (type(message.channel) == discord.DMChannel and message.author.id == client.user.id):
            try:
                await message.delete()
            except discord.Forbidden as e:
                print("Forbidden to delete message in "+str(message.channel))
                pass
        if len(args) == 2 and type(args[1]) is discord.User:
            output_message = await args[1].send(content='Scrambling image... ('+str(input_image_blob.getbuffer().nbytes)+' bytes loaded)')
        else:
            output_message = await message.channel.send(content='Scrambling image...('+str(input_image_blob.getbuffer().nbytes)+' bytes loaded)')
        input_image_blob.seek(0)
        input_image = Image.open(input_image_blob)
        if input_image.size == (1, 1):
            raise ValueError("input image must contain more than 1 pixel")
        number_of_regions = 1 # number_of_colours(input_image)
        key_image = None
        region_lists = create_region_lists(input_image, key_image,
                                           number_of_regions)
        random.seed(input_image.size)
        print('Shuffling scramble blob')
        shuffle(region_lists)
        output_image = swap_pixels(input_image, region_lists)
        output_image_blob = io.BytesIO()
        print('Saving scramble blob')
        output_image.save(output_image_blob, format="PNG", optimize=True)
        output_image_blob.seek(0)
        await output_message.delete()
        output_message = await output_message.channel.send(content='Scrambled for '+message.author.display_name, files=[discord.File(output_image_blob, message.attachments[0].filename)])
        await output_message.add_reaction('🔎')
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("SIF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

def number_of_colours(image):
    return len(set(list(image.getdata())))


def create_region_lists(input_image, key_image, number_of_regions):
    template = create_template(input_image, key_image, number_of_regions)
    number_of_regions_created = len(set(template))
    region_lists = [[] for i in range(number_of_regions_created)]
    for i in range(len(template)):
        region = template[i]
        region_lists[region].append(i)
    odd_region_lists = [region_list for region_list in region_lists
                        if len(region_list) % 2]
    for i in range(len(odd_region_lists) - 1):
        odd_region_lists[i].append(odd_region_lists[i + 1].pop())
    return region_lists


def create_template(input_image, key_image, number_of_regions):
    width, height = input_image.size
    return [0] * (width * height)

def no_small_pixel_regions(pixel_regions, number_of_regions_created):
    counts = [0 for i in range(number_of_regions_created)]
    for value in pixel_regions:
        counts[value] += 1
    if all(counts[i] >= 256 for i in range(number_of_regions_created)):
        return True


def shuffle(region_lists):
    for region_list in region_lists:
        length = len(region_list)
        for i in range(length):
            j = random.randrange(length)
            region_list[i], region_list[j] = region_list[j], region_list[i]


def measure(pixel):
    '''Return a single value roughly measuring the brightness.

    Not intended as an accurate measure, simply uses primes to prevent two
    different colours from having the same measure, so that an image with
    different colours of similar brightness will still be divided into
    regions.
    '''
    if type(pixel) is int:
        return pixel
    else:
        r, g, b = pixel[:3]
        return r * 2999 + g * 5869 + b * 1151


def swap_pixels(input_image, region_lists):
    pixels = list(input_image.getdata())
    for region in region_lists:
        for i in range(0, len(region) - 1, 2):
            pixels[region[i]], pixels[region[i+1]] = (pixels[region[i+1]],
                                                      pixels[region[i]])
    scrambled_image = Image.new(input_image.mode, input_image.size)
    scrambled_image.putdata(pixels)
    return scrambled_image


def memfrob(plain=""):
    plain = list(plain)
    xok = 0x2a
    length = len(plain)
    kek = []
    for x in range(0,length):
            kek.append(hex(ord(plain[x])))
    for x in range(0,length):
            kek[x] = hex(int(kek[x], 16) ^ int(hex(xok), 16))
    
    cipher = ""
    for x in range(0,length):
        cipher = cipher + convert_hex_to_ascii(int(kek[x], 16))
    return cipher

def rot32768(s):
    y = ''
    for x in s:
            y += chr(ord(x) ^ 0x8000)
    return y

def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.utcnow()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(int(second_diff)) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"

async def rot13_function(message, client, args):
    global config
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            if message.author.id == 429368441577930753:
                if message.content.startswith("Mod Report"):
                    return await args[1].send(codecs.encode(message.content.split("\n", 1)[1], 'rot_13'))
                else:
                    return await args[1].send("Spoiler from conversation in <#{}> ({}) <https://discordapp.com/channels/{}/{}/{}>\n{}: {}".format(message.channel.id, message.channel.guild.name, message.channel.guild.id, message.channel.id, message.id, message.content.split(': ', 1)[0], codecs.encode(message.content.split(': ', 1)[1], 'rot_13')))
            else:
                return await args[1].send("Spoiler from conversation in <#{}> ({}) <https://discordapp.com/channels/{}/{}/{}>\n{}: {}".format(message.channel.id, message.channel.guild.name, message.channel.guild.id, message.channel.id, message.id, message.author.display_name, codecs.encode(message.content, 'rot_13')))
        elif len(args) == 2 and args[1] == 'INTPROC':
            return codecs.encode(args[0], 'rot_13')
        else:
            messageContent = "**"+message.author.display_name+"**: "+codecs.encode(" ".join(args), 'rot_13')
            botMessage = await message.channel.send(messageContent)
            await botMessage.add_reaction(client.get_emoji(int(config['discord']['rot13'])))
            try: 
                await message.delete()
            except discord.Forbidden as e:
                print("Forbidden to delete message in "+str(message.channel))
                pass
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("R13F[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

async def spoiler_function(message, client, args):
    try:
        rotate_function = memfrob
        if message.author.id == 429368441577930753:
            if len(message.clean_content.split(': ', 1)[1]) != len(message.clean_content.split(': ', 1)[1].encode()):
                rotate_function = rot32768
        else:
            if len(message.clean_content) != len(message.clean_content.encode()):
                rotate_function = rot32768
        if len(args) == 2 and type(args[1]) is discord.User:
            if message.author.id == 429368441577930753:
                if type(message.channel) == discord.DMChannel:
                    return await args[1].send("Spoiler from DM {}**: {}".format(message.clean_content.split('**: ', 1)[0], rotate_function(swapcasealpha(message.clean_content.split('**: ', 1)[1])).replace("\n"," ")))
                else:
                    return await args[1].send("Spoiler from conversation in <#{}> ({}) <https://discordapp.com/channels/{}/{}/{}>\n{}**: {}".format(message.channel.id, message.channel.guild.name, message.channel.guild.id, message.channel.id, message.id, message.clean_content.split('**: ', 1)[0], rotate_function(swapcasealpha(message.clean_content.split('**: ', 1)[1])).replace("\n"," ")))
            else:
                print("MFF: Backing out, not my message.")
        else:
            messageContent = "**"+message.author.display_name+"**: "+swapcasealpha(rotate_function(message.clean_content.split(' ', 1)[1].replace(' ',"\n")))
            botMessage = await message.channel.send(messageContent)
            await botMessage.add_reaction('🙈')
            try: 
                await message.delete()
            except discord.Forbidden as e:
                print("Forbidden to delete message in "+str(message.channel))
                pass
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("MFF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

async def reaction_request_function(message, client, args):
    try:
        emoji_query = args[0].strip(':')
        emoji = list(filter(lambda m: m.name == emoji_query, client.emojis))
        if len(args) >= 2:
            emoji = emoji[int(args[1])]
        else:
            emoji = emoji[0]
        # FIXME if used in empty channel this breaks
        if emoji:
            target = await message.channel.history(before=message, limit=1).flatten()
            target = target[0]
            await target.add_reaction(emoji)
            await asyncio.sleep(1)
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=6000.0, check=lambda reaction, user: str(reaction.emoji) == str(emoji))
            except asyncio.TimeoutError:
                pass
            await target.remove_reaction(emoji, client.user)
        try:
            if 'snappy' in config['discord'] and config['discord']['snappy']:
                await message.delete()
        except discord.Forbidden:
            print("XRF: Couldn't delete message but snappy mode is on")
            pass
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("XRF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

async def blockquote_embed_function(message, client, args):
    try:
        title = None
        if len(args) >= 1 and args[0][0:2] == '<<':
            limit = int(args[0][2:])
            title = " ".join(args[1:])
        else:
            limit = None
        if len(args) == 0 or limit and limit <= 0:
            limit = 1
        if limit:
            historical_messages = []
            async for historical_message in message.channel.history(before=message, limit=None):
                if historical_message.author == message.author:
                    historical_messages.append(historical_message)
                    limit -= 1
                if limit == 0:
                    break
            rollup = ''
            for message in historical_messages:
                rollup += message.clean_content
                rollup += '\n'
        else:
            if "\n" in message.content:
                title = message.content.split("\n", 1)[0].split(" ", 1)[1]
                rollup = message.content.split("\n", 1)[1]
            else:
                rollup = message.content.split(" ", 1)[1]
        quoted_by = f'{message.author.name}#{message.author.discriminator}'
        if message.author.nick:
            quoted_by = f'{message.author.nick} ({quoted_by})'
        quoted_by = f'On behalf of {quoted_by}'
        embed = discord.Embed().set_footer(icon_url=message.author.avatar_url,text=quoted_by)
        if title:
            embed.title = title
        if len(rollup) < 2048:
            embed.description = rollup
            rollup = None
        # 25 fields * 1024 characters
        # https://discordapp.com/developers/docs/resources/channel#embed-object-embed-field-structure
        elif len(rollup) <= 25 * 1024:
            msg_chunks = textwrap.wrap(rollup, 1024, replace_whitespace=False)
            for hunk in msg_chunks:
                embed.add_field(None, hunk, inline=True)
            rollup = None
        else:
            # TODO send multiple embeds instead
            await message.author.send('Message too long, maximum quotable character count is 25 * 1024')
        if not rollup:
            await message.channel.send(embed=embed)
            try:
                if 'snappy' in config['discord'] and config['discord']['snappy']:
                    for message in historical_messages:
                        await message.delete()
                    await message.delete()
            except discord.Forbidden:
                print("BEF: Couldn't delete messages but snappy mode is on")
                pass
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("BEF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

def autoload(ch):
    ch.add_command({
        'trigger': ['!rot13', '🕜', '<:rot13:539568301861371905>', '<:rot13:527988322879012894>'],
        'function': rot13_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'Send contents of message rot13 flipped'
        })

    ch.add_command({
        'trigger': ['!spoiler', '🙈', '!memfrob', '🕦'],
        'function': spoiler_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'Send contents of message thoroughly scrambled'
        })

    ch.add_command({
        'trigger': ['!scramble', '🔎', '🔞'],
        'function': scramble_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'Send contents of image deep fried'
        })

    ch.add_command({
        'trigger': ['!blockquote'],
        'function': blockquote_embed_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'Blockquote last message as embed'
        })

    ch.add_command({
        'trigger': ['!xreact'],
        'function': reaction_request_function,
        'async': True,
        'args_num': 1,
        'args_name': [],
        'description': 'Request reaction (x-server)'
        })
