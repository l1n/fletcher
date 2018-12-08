# bot.py
import asyncio
import codecs
import configparser
from datetime import datetime, timedelta
import discord
import io
import math
import psycopg2
import re
import textwrap
from sys import exc_info

"""fletcher=# \d parlay
                                      Table "public.parlay"
    Column    |            Type             | Collation | Nullable |           Default            
--------------+-----------------------------+-----------+----------+------------------------------
 id           | integer                     |           | not null | generated always as identity
 name         | character varying(255)      |           |          | 
 description  | text                        |           |          | 
 lastmodified | timestamp without time zone |           |          | 
 members      | bigint[]                    |           |          | 
 channel      | bigint                      |           |          | 
 guild        | bigint                      |           |          | 
 created      | timestamp without time zone |           |          | CURRENT_TIMESTAMP
 ttl          | interval                    |           |          | 
Indexes:
    "parlay_name_must_be_guild_unique" UNIQUE CONSTRAINT, btree (name, guild)

fletcher=# \d sentinel
                                     Table "public.sentinel"
    Column    |            Type             | Collation | Nullable |           Default            
--------------+-----------------------------+-----------+----------+------------------------------
 id           | integer                     |           | not null | generated always as identity
 name         | character varying(255)      |           |          | 
 description  | text                        |           |          | 
 lastmodified | timestamp without time zone |           |          | 
 subscribers  | bigint[]                    |           |          | 
 triggercount | integer                     |           |          | 
 created      | timestamp without time zone |           |          | CURRENT_TIMESTAMP
 triggered    | timestamp without time zone |           |          | 
Indexes:
    "sentinel_name_must_be_globally_unique" UNIQUE CONSTRAINT, btree (name)

fletcher=# \d messagemap
               Table "public.messagemap"
   Column    |  Type  | Collation | Nullable | Default 
-------------+--------+-----------+----------+---------
 fromguild   | bigint |           |          | 
 toguild     | bigint |           |          | 
 fromchannel | bigint |           |          | 
 tochannel   | bigint |           |          | 
 frommessage | bigint |           |          | 
 tomessage   | bigint |           |          | 
Indexes:
    "messagemap_idx" btree (fromguild, fromchannel, frommessage)

"""

FLETCHER_CONFIG = '/home/lin/fletcher/.fletcherrc'

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])

def smallcaps(text=False):
    if text:
        return text.translate(str.maketrans({'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'}))
    return None

def convert_hex_to_ascii(h):
    chars_in_reverse = []
    while h != 0x0:
        chars_in_reverse.append(chr(h & 0xFF))
        h = h >> 8

    chars_in_reverse.reverse()
    return ''.join(chars_in_reverse)

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

def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now()
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

def expand_guild_name(guild, prefix='', suffix=':', global_replace=False):
    acro_mapping = [ ('acn', 'a compelling narrative'), ('ACN', 'a compelling narrative') ]
    for k, v in acro_mapping:
        new_guild = guild.replace(prefix+k+suffix, prefix+v+suffix)
        if not global_replace:
            return new_guild

# command handler class

class CommandHandler:

    # constructor
    def __init__(self, client):
        self.client = client
        self.commands = []

    def add_command(self, command):
        self.commands.append(command)

    async def reaction_handler(self, reaction):
        messageContent = str(reaction.emoji)
        for command in self.commands:
            if messageContent.startswith(tuple(command['trigger'])) and (('admin' in command and user.guild_permissions.manage_webhooks) or 'admin' not in command):
                if command['args_num'] == 0:
                    channel = self.client.get_channel(reaction.channel_id)
                    message = await channel.get_message(reaction.message_id)
                    user = await self.client.get_user_info(reaction.user_id)
                    if command['async']:
                        return await command['function'](message, self.client, [reaction, user])
                        break
                    else:
                        return await message.channel.send(str(command['function'](message, self.client, [reaction, user])))
                        break

    async def command_handler(self, message):
        print(message.content)
        if extract_identifiers_messagelink.search(message.content):
            return await preview_messagelink_function(message, self.client, None)
        for command in self.commands:
            if message.content.startswith(tuple(command['trigger'])) and (('admin' in command and message.author.guild_permissions.manage_webhooks) or 'admin' not in command):
                print(command)
                args = message.content.split(' ')
                args.pop(0)
                if command['args_num'] == 0:
                    if command['async']:
                        return await command['function'](message, self.client, args)
                        break
                    else:
                        return await message.channel.send(str(command['function'](message, self.client, args)))
                        break
                else:
                    if len(args) >= command['args_num']:
                        if command['async']:
                            return await command['function'](message, self.client, args)
                            break
                        else:
                            return await message.channel.send(str(command['function'](message, self.client, args)))
                            break
                    else:
                        return await message.channel.send('command "{}" requires {} argument(s) "{}"'.format(command['trigger'][0], command['args_num'], ', '.join(command['args_name'])))
                        break

config = configparser.ConfigParser()
config.read(FLETCHER_CONFIG)

client = discord.Client()
conn = psycopg2.connect(host=config['database']['host'],database=config['database']['tablespace'], user=config['database']['user'], password=config['database']['password'])


# token from https://discordapp.com/developers
token = config['discord']['botToken']

ch = CommandHandler(client)

def listbanners_function(message, client, args):
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, created, triggered, lastmodified, subscribers, triggercount FROM sentinel WHERE lastmodified > NOW() - INTERVAL '30 days';")
        sentuple = cur.fetchone()
        bannerMessage = "Banner List:\n"
        while sentuple:
            bannerName = smallcaps(sentuple[1])
            if bannerName is None or bannerName.strip() == "" or " " in bannerName:
                bannerName = "Banner {}".format(str(sentuple[0]))
            bannerMessage = bannerMessage + "**{}** ".format(bannerName)
            if sentuple[2]:
                bannerMessage = bannerMessage + sentuple[2]
            supporterPluralized = "supporters"
            if len(sentuple[6]) == 1:
                supporterPluralized = "supporter"
            goalAchievedVerb = "is"
            if sentuple[4]:
                goalAchievedVerb = "was"
            bannerMessage = bannerMessage + "\n{} {}, goal {} {}\nMᴀᴅᴇ: {}\n".format(str(len(sentuple[6])), supporterPluralized, goalAchievedVerb, str(sentuple[7]), sentuple[3].strftime("%Y-%m-%d %H:%M") + " (" + pretty_date(sentuple[3]) + ")")
            if sentuple[4]:
                bannerMessage = bannerMessage + "Mᴇᴛ: {}\n".format(sentuple[4].strftime("%Y-%m-%d %H:%M") +  " (" + pretty_date(sentuple[4]) + ")")
            sentuple = cur.fetchone()
            if sentuple:
                bannerMessage = bannerMessage + "──────────\n"
        conn.commit()
        bammerMessage = bannerMessage.rstrip()
        if bannerMessage:
            return bannerMessage
        else:
            return "No banners modified within the last 30 days. Raise a sentinel with `!assemble`"
    except Exception as e:
        if cur is not None:
            conn.rollback()
        return e

def help_function(message, client, args):
    if len(args) > 0 and args[0] == "verbose":
        helpMessageBody = "\n".join(["`{}`: {}\nArguments ({}): {}".format("` or `".join(command['trigger']), command['description'], command['args_num'], " ".join(command['args_name'])) for command in ch.commands])
    else:
        helpMessageBody = "\n".join(["`{}`: {}".format("` or `".join(command['trigger']), command['description']) for command in ch.commands])
    return helpMessageBody

async def teleport_function(message, client, args):
    try:
        if args[0] == "to":
            args.pop(0)
        fromChannel = message.channel
        if fromChannel.id in [int(s) for s in config['teleport']['fromchannel-ban'].split(',')] and not message.author.guild_permissions.manage_webhooks:
            print('Forbidden teleport')
            await fromChannel.send('Portals out of this channel have been disabled.', delete_after=60)
            return
        targetChannel = args[0].strip()
        channelLookupBy = "Name"
        toChannel = None
        toGuild = None
        if targetChannel.startswith('<#'):
            targetChannel= targetChannel[2:-1].strip()
            channelLookupBy = "ID"
        elif targetChannel.startswith('#'):
            targetChannel= targetChannel[1:].strip()
        print('Target Channel '+channelLookupBy+': '+targetChannel)
        if channelLookupBy == "Name":
            if ":" not in targetChannel:
                toChannel = discord.utils.get(fromChannel.guild.text_channels, name=targetChannel)
            else:
                targetChannel = expand_guild_name(targetChannel)
                toTule = targetChannel.split(":")
                toGuild = discord.utils.get(client.guilds, name=toTuple[0].replace("_", " "))
                toChannel = discord.utils.get(toGuild.text_channels, name=toTuple[1])
        elif channelLookupBy == "ID":
            toChannel = client.get_channel(int(targetChannel))
        print('Opening From '+str(fromChannel))
        fromMessage = await fromChannel.send('Opening Portal To <#{}> ({})'.format(toChannel.id, toChannel.guild.name))
        print('Opening To '+str(toChannel))
        toMessage = await toChannel.send('Opening Portal To <#{}> ({})'.format(fromChannel.id, fromChannel.guild.name))
        print('Editing From')
        embedTitle = "Portal opened to #{}".format(toChannel.name)
        if toGuild:
            embedTitle = embedTitle+" ({})".format(toChannel.guild.name)
        embedPortal = discord.Embed(title=embedTitle, description="https://discordapp.com/channels/{}/{}/{} {}".format(toChannel.guild.id, toChannel.id, toMessage.id, " ".join(args[1:]))).set_footer(icon_url="https://download.lin.anticlack.com/fletcher/blue-portal.png",text="On behalf of {}".format(message.author.nick or message.author))
        tmp = await fromMessage.edit(content=None,embed=embedPortal)
        print('Editing To')
        embedTitle = "Portal opened from #{}".format(fromChannel.name)
        if toGuild:
            embedTitle = embedTitle+" ({})".format(fromChannel.guild.name)
        embedPortal = discord.Embed(title=embedTitle, description="https://discordapp.com/channels/{}/{}/{} {}".format(fromChannel.guild.id, fromChannel.id, fromMessage.id, " ".join(args[1:]))).set_footer(icon_url="https://download.lin.anticlack.com/fletcher/orange-portal.png",text="On behalf of {}".format(message.author.nick or message.author))
        tmp = await toMessage.edit(content=None,embed=embedPortal)
        print('Portal Opened')
        try:
            await message.delete()
        except discord.Forbidden:
            print("Couldn't delete portal request message")
        return 'Portal opened on behalf of {} to {}'.format(message.author, args[0])
    except Exception as e:
        return e

extract_identifiers_messagelink = re.compile('https://discordapp.com/channels/(\d+)/(\d+)/(\d+)', re.IGNORECASE)
async def preview_messagelink_function(message, client, args):
    try:
        # 'https://discordapp.com/channels/{}/{}/{}'.format(message.channel.guild.id, message.channel.id, message.id)
        urlParts = extract_identifiers_messagelink.search(message.content).groups()
        if len(urlParts) == 3:
            guild_id = int(urlParts[0])
            channel_id = int(urlParts[1])
            message_id = int(urlParts[2])
            guild = client.get_guild(guild_id)
            channel = guild.get_channel(channel_id)
            target_message = await channel.get_message(message_id)
            sent_at = target_message.created_at
            if message.guild.id == guild_id and message.channel.id == channel_id:
                return await message.channel.send("Message from <@{}> sent at {}:\n{}".format(target_message.author.id, sent_at, target_message.content))
            elif message.guild.id == guild_id:
                return await message.channel.send("Message from <@{}> sent in <#{}> at {}:\n{}".format(target_message.author.id, channel_id, sent_at, target_message.content))
            else:
                return await message.channel.send("Message from <@{}> sent in #{} ({}) at {}:\n{}".format(target_message.author.id, channel.name, guild.name, sent_at, target_message.content))
    except Exception as e:
        await message.channel.send(e)
        pass # better for there to be no response in that case


async def messagelink_function(message, client, args):
    try:
        msg = None
        for channel in message.channel.guild.text_channels:
            try:
                msg = await channel.get_message(int(args[0]))
                break
            except discord.NotFound as e:
                pass
        if msg:
            await message.channel.send('Message link on behalf of {}: https://discordapp.com/channels/{}/{}/{}'.format(message.author, message.channel.guild.id, message.channel.id, message.id))
            return await message.delete()
        return await message.channel.send('Message not found', delete_after=60)
    except Exception as e:
        await message.channel.send(e)

async def assemble_function(message, client, args):
    try:
        bannerId = None
        bannerName = None
        triggerCount = None
        bannerDescription = None
        nameAutoGenerated = True
        cur = conn.cursor()
        try:
            triggerCount = int(args[0])
            bannerName = " ".join(args[1:])
            bannerDescription = bannerName
        except ValueError:
            triggerCount = int(args[1])
            bannerName = args[0]
            nameAutoGenerated = False
            bannerDescription =  " ".join(args[2:])
            pass
        cur.execute("INSERT INTO sentinel (name, description, lastModified, triggerCount) VALUES (%s, %s, %s, %s);", [bannerName, bannerDescription, datetime.now(), triggerCount])
        cur.execute("SELECT id FROM sentinel WHERE name = %s", [bannerName])
        bannerId = cur.fetchone()[0]
        conn.commit()
        if nameAutoGenerated:
            return await message.channel.send('Banner created! `!pledge {}` to commit to this pledge.'.format(str(bannerId)))
        else:
            return await message.channel.send('Banner created! `!pledge {}` to commit to this pledge.'.format(bannerName))
    except Exception as e:
        if cur is not None:
            conn.rollback()
        await message.channel.send(e)

async def pledge_function(message, client, args):
    try:
        bannerId = None
        sentuple = None
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM sentinel WHERE id = %s LIMIT 1;", [int(args[0])])
            sentuple = cur.fetchone()
        except ValueError:
            pass
        if sentuple == None:
            cur.execute("SELECT COUNT(id) FROM sentinel WHERE name ILIKE %s;", [" ".join(args)])
            availableSentinels = cur.fetchone()[0]
            if availableSentinels == 0:
                conn.commit()
                return await message.channel.send('No banner "{}" available. Try `!assemble [critical number of subscribers] {}` to create one.'.format(args[0], " ".join(args)))
            elif availableSentinels == 1:
                cur.execute("SELECT id FROM sentinel WHERE name ILIKE %s;", [" ".join(args)])
                sentuple = cur.fetchone()
            elif availableSentinels > 1:
                conn.commit()
                return await message.channel.send('Not sure what you want to do: {} banners found containing {} in the name.'.format(str(availableSentinels), " ".join(args)))
        bannerId = sentuple[0]
        cur.execute("SELECT COUNT(id) FROM sentinel WHERE id = %s AND %s = ANY (subscribers);", [bannerId, message.author.id])
        if cur.fetchone()[0]:
            conn.commit()
            return await message.channel.send('You already committed to this banner. `!defect {}` to defect.'.format(" ".join(args)))
        else:
            cur.execute("UPDATE sentinel SET subscribers = array_append(subscribers, %s), lastmodified = CURRENT_TIMESTAMP WHERE id = %s;", [message.author.id, bannerId])
            cur.execute("SELECT array_length(subscribers, 1), triggercount, name, subscribers, triggered FROM sentinel WHERE id = %s;", [bannerId])
            bannerInfo = cur.fetchone()
            if bannerInfo[0] == bannerInfo[1]: # Triggered banner! Yay!
                cur.execute("UPDATE sentinel SET triggered = CURRENT_TIMESTAMP WHERE id = %s;", [bannerId])
                conn.commit()
                return await message.channel.send('Critical mass reached for banner {}! Paging supporters: <@{}>. Now it\'s up to you to fulfill your goal :)'.format(bannerInfo[2], ">, <@".join([str(userId) for userId in bannerInfo[3]])))
            elif bannerInfo[0] > bannerInfo[1]:
                conn.commit()
                return await message.channel.send('Critical mass was reached for banner {} at {}! You are the {} supporter.'.format(bannerInfo[2], bannerInfo[4].strftime("%Y-%m-%d %H:%M:%S"), ordinal(bannerInfo[0])))
            else:
                conn.commit()
                return await message.channel.send('You pledged your support for banner {} (one of {} supporters). It needs {} more supporters to reach its goal.'.format(bannerInfo[2], bannerInfo[0], str(bannerInfo[1] - bannerInfo[0])))
    except Exception as e:
        if cur is not None:
            conn.rollback()
        await message.channel.send(e)

async def defect_function(message, client, args):
    try:
        bannerId = None
        sentuple = None
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM sentinel WHERE id = %s LIMIT 1;", [int(args[0])])
            sentuple = cur.fetchone()
        except ValueError:
            pass
        if sentuple == None:
            cur.execute("SELECT COUNT(id) FROM sentinel WHERE name ILIKE %s;", [" ".join(args)])
            availableSentinels = cur.fetchone()[0]
            if availableSentinels == 0:
                conn.commit()
                return await message.channel.send('No banner "{}" available. Try `!assemble [critical number of subscribers] {}` to create one.'.format(args[0], " ".join(args)))
            elif availableSentinels == 1:
                cur.execute("SELECT id FROM sentinel WHERE name ILIKE %s;", [" ".join(args)])
                sentuple = cur.fetchone()
            elif availableSentinels > 1:
                conn.commit()
                return await message.channel.send('Not sure what you want to do: {} banners found containing {} in the name.'.format(str(availableSentinels), " ".join(args)))
        bannerId = sentuple[0]
        cur.execute("SELECT COUNT(id) FROM sentinel WHERE id = %s AND %s = ANY (subscribers);", [bannerId, message.author.id])
        if cur.fetchone()[0]:
            cur.execute("SELECT array_length(subscribers, 1), triggercount, name, subscribers FROM sentinel WHERE id = %s;", [bannerId])
            bannerInfo = cur.fetchone()
            if bannerInfo[0] >= bannerInfo[1]: # Triggered banner, can't go back now
                conn.commit()
                return await message.channel.send('Critical mass reached for banner {}! You can\'t defect anymore.'.format(bannerInfo[2]))
            else:
                cur.execute("UPDATE sentinel SET subscribers = array_remove(subscribers, %s), lastmodified = CURRENT_TIMESTAMP WHERE id = %s;", [message.author.id, bannerId])
                conn.commit()
                return await message.channel.send('You defected from banner {}. It now needs {} more supporters to reach its goal.'.format(bannerInfo[2], str(bannerInfo[1] - bannerInfo[0])))
        else:
            conn.commit()
            return await message.channel.send('You have not committed to this banner. `!pledge {}` to pledge support.'.format(" ".join(args)))
    except Exception as e:
        if cur is not None:
            conn.rollback()
        await message.channel.send(e)

async def lastactive_function(message, client, args):
    try:
        lastMonth = None
        before = True
        try:
            if args[0]:
                try:
                    lastMonth = datetime.utcnow().date() - timedelta(days=int(args[0]))
                except ValueError:
                    if args[1]:
                        if args[0].startswith("a"):
                            before = False
                        lastMonth = datetime.utcnow().date() - timedelta(days=int(args[1]))
                    pass
        except IndexError:
                    pass
        msg = ""
        for channel in message.channel.guild.text_channels:
            try:
                category_pretty = ""
                if channel.category_id:
                    category_pretty = " [{}]".format(client.get_channel(channel.category_id).name)
                created_at = (await channel.history(limit=1).flatten())[0].created_at
                created_pretty = pretty_date(created_at)
                if created_pretty:
                    created_pretty = " ({})".format(created_pretty)
                if lastMonth:
                    if (before and lastMonth < created_at.date()) or (not before and lastMonth > created_at.date()):
                        msg = "{}\n<#{}>{}: {}{}".format(msg, channel.id, category_pretty, created_at.isoformat(timespec='minutes'), created_pretty)
                else:
                        msg = "{}\n<#{}>{}: {}{}".format(msg, channel.id, category_pretty, created_at.isoformat(timespec='minutes'), created_pretty)
            except discord.NotFound as e:
                pass
            except discord.Forbidden as e:
                msg = "{}\n<#{}>{}: Forbidden".format(msg, channel.id, category_pretty)
                pass
        msg = '**Channel Activity:**{}'.format(msg)
        msg_chunks = textwrap.wrap(msg, 2000, replace_whitespace=False)
        for chunk in msg_chunks:
            await message.channel.send(chunk)
    except Exception as e:
        print(e)

async def bookmark_function(message, client, args):
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            print("bookmarking via reaction")
            return await args[1].send("Bookmark to conversation in #{} ({}) https://discordapp.com/channels/{}/{}/{} via reaction to {}".format(message.channel.name, message.channel.guild.name, message.channel.guild.id, message.channel.id, message.id, message.content))
        else:
            print("bookmarking via command")
            await message.author.send("Bookmark to conversation in #{} ({}) https://discordapp.com/channels/{}/{}/{} {}".format(message.channel.name, message.channel.guild.name, message.channel.guild.id, message.channel.id, message.id, " ".join(args)))
            return await message.add_reaction('✅')
    except Exception as e:
        return e

async def rot13_function(message, client, args):
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            return await args[1].send(codecs.encode(message.content, 'rot_13'))
        else:
            messageContent = codecs.encode(" ".join(args), 'rot_13')
            botMessage = await message.channel.send(messageContent)
            await botMessage.add_reaction('🕜')
            try: 
                await message.delete()
            except discord.Forbidden as e:
                print("Forbidden to delete message in "+str(message.channel))
    except Exception as e:
        return e

async def memfrob_function(message, client, args):
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            return await args[1].send(memfrob(message.content))
        else:
            messageContent = memfrob(" ".join(args))
            botMessage = await message.channel.send(messageContent)
            await botMessage.add_reaction('🕦')
            try: 
                await message.delete()
            except discord.Forbidden as e:
                print("Forbidden to delete message in "+str(message.channel))
    except Exception as e:
        return e

async def reload_function(message, client, args):
    try:
        config.read(FLETCHER_CONFIG)
        await load_webhooks()
        message.add_reaction('✓')
    except Exception as e:
        return e

ch.add_command({
    'trigger': ['!help'],
    'function': help_function,
    'async': False,
    'args_num': 0,
    'args_name': [],
    'description': 'List commands and arguments'
})
ch.add_command({
    'trigger': ['!assemble', '!canvas'],
    'function': assemble_function,
    'async': True,
    'args_num': 2,
    'args_name': ['int', 'string'],
    'description': 'Create a sentinel for assembling groups'
})
ch.add_command({
    'trigger': ['!pledge', '!join'],
    'function': pledge_function,
    'async': True,
    'args_num': 1,
    'args_name': ['int'],
    'description': 'Salute a sentinel'
})
ch.add_command({
    'trigger': ['!defect'],
    'function': defect_function,
    'async': True,
    'args_num': 1,
    'args_name': ['int'],
    'description': 'Turn away from a sentinel'
})
ch.add_command({
    'trigger': ['!banners'],
    'function': listbanners_function,
    'async': False,
    'args_num': 0,
    'args_name': [],
    'description': 'List sentinels'
})
ch.add_command({
    'trigger': ['!teleport', '!portal'],
    'function': teleport_function,
    'async': True,
    'args_num': 1,
    'args_name': ['string'],
    'description': 'Create a link bridge to another channel'
})
ch.add_command({
    'trigger': ['!bookmark', '🔖'],
    'function': bookmark_function,
    'async': True,
    'args_num': 0,
    'args_name': [],
    'description': 'DM the user a bookmark to the current place in conversation',
})
ch.add_command({
    'trigger': ['!message'],
    'function': messagelink_function,
    'async': True,
    'args_num': 1,
    'args_name': ['string'],
    'description': 'Create a link to the message with ID `!message XXXXXX`'
})
ch.add_command({
    'trigger': ['!preview'],
    'function': preview_messagelink_function,
    'async': True,
    'args_num': 1,
    'args_name': ['string'],
    'description': 'Retrieve message body by link (used internally to unwrap message links in chat)'
})
ch.add_command({
    'trigger': ['!lastactive', '!lastactivity', '!ls'],
    'function': lastactive_function,
    'async': True,
    'admin': True,
    'args_num': 0,
    'args_name': [],
    'description': 'List all available channels and time of last message'
})
ch.add_command({
    'trigger': ['!rot13', '🕜'],
    'function': rot13_function,
    'async': True,
    'args_num': 0,
    'args_name': [],
    'description': 'Send contents of message rot13 flipped (deprecated)'
})

ch.add_command({
    'trigger': ['!memfrob', '!spoiler', '🕦'],
    'function': memfrob_function,
    'async': True,
    'args_num': 0,
    'args_name': [],
    'description': 'Send contents of message to memfrob flipped'
})

ch.add_command({
    'trigger': ['!reload <@429368441577930753>'],
    'function': reload_function,
    'async': True,
    'admin': True,
    'args_num': 0,
    'args_name': [],
    'description': 'Reload config (admin only)'
})

webhook_sync_registry = {
        'FromGuild:FromChannelName': {
            'fromChannelObject': None,
            'fromWebhook': None,
            'toChannelObject': None,
            'toWebhook': None
            }
        }

# bot is ready
@client.event
async def on_ready():
    try:
        # print bot information
        print(client.user.name)
        print(client.user.id)
        print('Discord.py Version: {}'.format(discord.__version__))
        await client.change_presence(activity=discord.Game(name='liberapay.com/novalinium'))
        # Webhook handlers
        await load_webhooks()
        doissetep_omega = await client.get_guild(int(config['audio']['guild'])).get_channel(int(config['audio']['channel'])).connect();
        doissetep_omega.play(discord.FFmpegPCMAudio(config['audio']['instreamurl']))

    except Exception as e:
        print(e)

async def load_webhooks():
    webhook_sync_registry = {}
    for guild in client.guilds:
        try:
            for webhook in await guild.webhooks():
                # discord.py/rewrite issue #1242, PR #1745 workaround
                if webhook.name.startswith(config['discord']['botNavel']+' ('):
                    fromChannelName = guild.name+':'+str(guild.get_channel(webhook.channel_id))
                    webhook_sync_registry[fromChannelName] = {
                            'fromChannelObject': guild.get_channel(webhook.channel_id),
                            'fromWebhook': webhook,
                            'toChannelObject': None,
                            'toWebhook': None
                            }
                    toTuple = webhook.name.split("(")[1].split(")")[0].split(":")
                    toTuple[0] = expand_guild_name(toTuple[0])
                    toGuild = discord.utils.get(client.guilds, name=toTuple[0].replace("_", " "))
                    webhook_sync_registry[fromChannelName]['toChannelObject'] = discord.utils.get(toGuild.text_channels, name=toTuple[1])
                    webhook_sync_registry[fromChannelName]['toWebhook'] = discord.utils.get(await toGuild.webhooks(), channel__name=toTuple[1])
        except discord.Forbidden as e:
            print('Couldn\'t load webhooks for '+str(guild)+', ask an admin to grant additional permissions (https://novalinium.com/go/3/fletcher)')
    print("Webhooks loaded:")
    print("\n".join(list(webhook_sync_registry)))

# on new message
@client.event
async def on_message(message):
    # if the message is from the bot itself or sent via webhook, which is usually done by a bot, ignore it other than sync processing
    if message.webhook_id:
        pass
    elif message.author == client.user:
        try:
            if message.guild.name+':'+message.channel.name in webhook_sync_registry:
                attachments = []
                for attachment in message.attachments:
                    print("Syncing "+attachment.filename)
                    attachment_blob = io.BytesIO()
                    await attachment.save(attachment_blob)
                    attachments.append(discord.File(attachment_blob, attachment.filename))
                # wait=True: blocking call for messagemap insertions to work
                syncMessage = await webhook_sync_registry[message.guild.name+':'+message.channel.name]['toWebhook'].send(content=message.content, username=message.author.name, avatar_url=message.author.avatar_url, embeds=message.embeds, tts=message.tts, files=attachments, wait=True)
                cur = conn.cursor()
                cur.execute("INSERT INTO messagemap (fromguild, fromchannel, frommessage, toguild, tochannel, tomessage) VALUES (%s, %s, %s, %s, %s, %s);", [message.guild.id, message.channel.id, message.id, syncMessage.guild.id, syncMessage.channel.id, syncMessage.id])
                conn.commit()
        except AttributeError as e:
            # Eat from PMs
            pass
    else:
        try:
            if message.guild.name+':'+message.channel.name in webhook_sync_registry:
                attachments = []
                for attachment in message.attachments:
                    print("Syncing "+attachment.filename)
                    attachment_blob = io.BytesIO()
                    await attachment.save(attachment_blob)
                    attachments.append(discord.File(attachment_blob, attachment.filename))
                # wait=True: blocking call for messagemap insertions to work
                syncMessage = await webhook_sync_registry[message.guild.name+':'+message.channel.name]['toWebhook'].send(content=message.content, username=message.author.name, avatar_url=message.author.avatar_url, embeds=message.embeds, tts=message.tts, files=attachments, wait=True)
                cur = conn.cursor()
                cur.execute("INSERT INTO messagemap (fromguild, fromchannel, frommessage, toguild, tochannel, tomessage) VALUES (%s, %s, %s, %s, %s, %s);", [message.guild.id, message.channel.id, message.id, syncMessage.guild.id, syncMessage.channel.id, syncMessage.id])
                conn.commit()
        except AttributeError as e:
            # Eat from PMs
            pass

        # try to evaluate with the command handler
        try:
            await ch.command_handler(message)

        # message doesn't contain a command trigger
        except TypeError as e:
            pass

        # generic python error
        except Exception as e:
            exc_type, exc_obj, exc_tb = exc_info()
            print("OMR[{}]: {}".format(exc_tb.tb_lineno, e))

# on message update (for webhooks only for now)
@client.event
async def on_raw_message_edit(payload):
    try:
        message_id = payload.message_id
        message = payload.data
        fromGuild = client.get_guild(int(message['guild_id']))
        fromChannel = fromGuild.get_channel(int(message['channel_id']))
        if fromGuild.name+':'+fromChannel.name in webhook_sync_registry:
            cur = conn.cursor()
            cur.execute("SELECT toguild, tochannel, tomessage FROM messagemap WHERE fromguild = %s AND fromchannel = %s AND frommessage = %s LIMIT 1;", [int(message['guild_id']), int(message['channel_id']), message_id])
            metuple = cur.fetchone()
            conn.commit()
            if metuple is not None:
                toGuild = client.get_guild(metuple[0])
                toChannel = toGuild.get_channel(metuple[1])
                toMessage = await toChannel.get_message(metuple[2])
                fromMessage = await fromChannel.get_message(message_id)
                await toMessage.delete()
                attachments = []
                for attachment in fromMessage.attachments:
                    print("Syncing "+attachment.filename)
                    attachment_blob = io.BytesIO()
                    await attachment.save(attachment_blob)
                    attachments.append(discord.File(attachment_blob, attachment.filename))
                syncMessage = await webhook_sync_registry[fromMessage.guild.name+':'+fromMessage.channel.name]['toWebhook'].send(content=fromMessage.content, username=fromMessage.author.name, avatar_url=fromMessage.author.avatar_url, embeds=fromMessage.embeds, tts=fromMessage.tts, files=attachments, wait=True)
                cur = conn.cursor()
                cur.execute("UPDATE messagemap SET toguild = %s, tochannel = %s, tomessage = %s WHERE fromguild = %s AND fromchannel = %s AND frommessage = %s;", [syncMessage.guild.id, syncMessage.channel.id, syncMessage.id, int(message['guild_id']), int(message['channel_id']), message_id])
                conn.commit()
    except discord.Forbidden as e:
        print("Forbidden to edit synced message from "+str(fromGuild.name)+":"+str(fromChannel.name))
    # except KeyError as e:
    #     # Eat keyerrors from non-synced channels
    #     pass
    # except AttributeError as e:
    #     # Eat from PMs
    #     pass
    # generic python error
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("ORMU[{}]: {}".format(exc_tb.tb_lineno, e))

# on message deletion (for webhooks only for now)
@client.event
async def on_raw_message_delete(message):
    try:
        fromGuild = client.get_guild(message.guild_id)
        fromChannel = fromGuild.get_channel(message.channel_id)
        if fromGuild.name+':'+fromChannel.name in webhook_sync_registry:
            cur = conn.cursor()
            cur.execute("SELECT toguild, tochannel, tomessage FROM messagemap WHERE fromguild = %s AND fromchannel = %s AND frommessage = %s LIMIT 1;", [message.guild_id, message.channel_id, message.message_id])
            metuple = cur.fetchone()
            if metuple is not None:
                cur.execute("DELETE FROM messageMap WHERE fromGuild = %s AND fromChannel = %s AND fromMessage = %s", [fromGuild.id, fromChannel.id, message.message_id])
            conn.commit()
            if metuple is not None:
                toGuild = client.get_guild(metuple[0])
                toChannel = toGuild.get_channel(metuple[1])
                toMessage = await toChannel.get_message(metuple[2])
                print("Deleting synced message {}:{}:{}".format(metuple[0], metuple[1], metuple[2]))
                await toMessage.delete()
    except discord.Forbidden as e:
        print("Forbidden to delete synced message from "+str(fromGuild.name)+":"+str(fromChannel.name))
    except KeyError as e:
        # Eat keyerrors from non-synced channels
        pass
    except AttributeError as e:
        # Eat from PMs
        pass
    # generic python error
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("ORMD[{}]: {}".format(exc_tb.tb_lineno, e))

# on new rxn
@client.event
async def on_raw_reaction_add(reaction):
    # if the reaction is from the bot itself ignore it
    if reaction.user_id == client.user.id:
        pass
    else:
        # try to evaluate with the command handler
        try:
            print(reaction.emoji)
            await ch.reaction_handler(reaction)

        # message doesn't contain a command trigger
        except TypeError as e:
            pass

        # generic python error
        except Exception as e:
            exc_type, exc_obj, exc_tb = exc_info()
            print("ORRA[{}]: {}".format(exc_tb.tb_lineno, e))


# on vox change
@client.event
async def on_voice_state_update(member, before, after):
    print('Vox update in '+str(member.guild))
    # Notify only if: 
    # Doissetep
    # New joins only, no transfers
    # Not me
    if member.guild.id == int(config['audio']['guild']) and \
       after.channel is not None and before.channel is None and \
       member.id != client.user.id:
        # used to be #canticum, moved to #autochthonia due to spamminess
        canticum = client.get_channel(int(config['audio']['notificationchannel']))
        # bleet = client.get_user(191367077565562880)
        # nova = client.get_user(382984420321263617)
        await canticum.send("<@&"+str(config['audio']['notificationrole'])+">: "+str(member.name)+" is in voice ("+str(after.channel.name)+") in "+str(member.guild.name))

## on new member
#@client.event
#async def on_member_join(member):
#    # if the message is from the bot itself ignore it
#    if member == client.user:
#        pass
#    else:
#        yield # check if the guild requires containment and contain if so

# start bot
client.run(token)
