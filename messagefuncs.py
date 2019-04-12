import asyncio
import discord
import io
import re
from sys import exc_info
# global conn set by reload_function

def expand_guild_name(guild, prefix='', suffix=':', global_replace=False):
    # TODO refactor into config file
    acro_mapping = [ ('acn', 'a compelling narrative'), ('ACN', 'a compelling narrative'), ('EAC', 'EA Corner'), ('D', 'Doissetep'), ('bocu', 'Book of Creation Undone'), ('abcal', 'Abandoned Castle') ]
    new_guild = guild
    for k, v in acro_mapping:
        new_guild = new_guild.replace(prefix+k+suffix, prefix+v+suffix)
        if not global_replace and new_guild != guild:
            return new_guild
        if k == new_guild:
            return v
    return new_guild

extract_identifiers_messagelink = re.compile('(?<!<)https://(?:ptb\.)?discordapp.com/channels/(\d+)/(\d+)/(\d+)', re.IGNORECASE)
async def teleport_function(message, client, args):
    global config
    try:
        if args[0] == "to":
            args.pop(0)
        fromChannel = message.channel
        fromGuild = message.guild
        if str(fromChannel.id) in config['teleport']['fromchannel-ban'].split(',') and not message.author.guild_permissions.manage_webhooks:
            await fromChannel.send('Portals out of this channel have been disabled.', delete_after=60)
            raise Exception('Forbidden teleport')
        targetChannel = args[0].strip()
        channelLookupBy = "Name"
        toChannel = None
        toGuild = None
        if targetChannel.startswith('<#'):
            targetChannel = targetChannel[2:-1].strip()
            channelLookupBy = "ID"
        elif targetChannel.startswith('#'):
            targetChannel = targetChannel[1:].strip()
        print('Target Channel '+channelLookupBy+': '+targetChannel)
        if channelLookupBy == "Name":
            if ":" not in targetChannel:
                toChannel = discord.utils.get(fromGuild.text_channels, name=targetChannel)
                toGuild = fromGuild
            else:
                targetChannel = expand_guild_name(targetChannel)
                toTuple = targetChannel.split(":")
                toGuild = discord.utils.get(client.guilds, name=toTuple[0].replace("_", " "))
                toChannel = discord.utils.get(toGuild.text_channels, name=toTuple[1])
        elif channelLookupBy == "ID":
            toChannel = client.get_channel(int(targetChannel))
            toGuild = toChannel.guild
        if fromChannel.id == toChannel.id:
            await fromChannel.send('You cannot open an overlapping portal! Access denied.')
            raise Exception('Attempt to open overlapping portal')
        print('Entering in '+str(fromChannel))
        fromMessage = await fromChannel.send('Opening Portal To <#{}> ({})'.format(toChannel.id, toGuild.name))
        try:
            print('Exiting in '+str(toChannel))
            toMessage = await toChannel.send('Portal Opening From <#{}> ({})'.format(fromChannel.id, fromGuild.name))
        except discord.Forbidden as e:
            await fromMessage.edit(content='Failed to open portal due to missing permissions! Access denied.')
            raise Exception('Portal collaped half-open!')
        embedTitle = "Portal opened to #{}".format(toChannel.name)
        if toGuild != fromGuild:
            embedTitle = embedTitle+" ({})".format(toGuild.name)
        if toChannel.name == "hell":
            inPortalColor = ["red", discord.Colour.from_rgb(194,0,11)]
        else:
            inPortalColor = ["blue", discord.Colour.from_rgb(62,189,236)]
        behest = localizeName(message.author, fromGuild)
        embedPortal = discord.Embed(title=embedTitle, description="https://discordapp.com/channels/{}/{}/{} {}".format(toGuild.id, toChannel.id, toMessage.id, " ".join(args[1:])), color=inPortalColor[1]).set_footer(icon_url="https://download.lin.anticlack.com/fletcher/"+inPortalColor[0]+"-portal.png",text="On behalf of {}".format(behest))
        if config['teleport']['embeds'] == "on":
            tmp = await fromMessage.edit(content=None,embed=embedPortal)
        else:
            tmp = await fromMessage.edit(content="**{}** <https://discordapp.com/channels/{}/{}/{}>\nOn behalf of {}\n{}".format(embedTitle, toGuild.id, toChannel.id, toMessage.id, behest, " ".join(args[1:])))
        embedTitle = "Portal opened from #{}".format(fromChannel.name)
        behest = localizeName(message.author, toGuild)
        if toGuild != fromGuild:
            embedTitle = embedTitle+" ({})".format(fromGuild.name)
        embedPortal = discord.Embed(title=embedTitle, description="https://discordapp.com/channels/{}/{}/{} {}".format(fromGuild.id, fromChannel.id, fromMessage.id, " ".join(args[1:])), color=discord.Colour.from_rgb(194,64,11)).set_footer(icon_url="https://download.lin.anticlack.com/fletcher/orange-portal.png",text="On behalf of {}".format(behest))
        if config['teleport']['embeds'] == "on":
            tmp = await toMessage.edit(content=None,embed=embedPortal)
        else:
            tmp = await toMessage.edit(content="**{}** <https://discordapp.com/channels/{}/{}/{}>\nOn behalf of {}\n{}".format(embedTitle, fromGuild.id, fromChannel.id, fromMessage.id, behest, " ".join(args[1:])))
        try:
            if 'snappy' in config['discord'] and config['discord']['snappy']:
                await message.delete()
            return
        except discord.Forbidden:
            raise Exception("Couldn't delete portal request message")
        return 'Portal opened on behalf of {} to {}'.format(message.author, args[0])
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("TPF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

async def preview_messagelink_function(message, client, args):
    try:
        in_content = None
        if args is not None and args[0].isdigit():
            in_content = await messagelink_function(message, client, [args[0], 'INTPROC'])
        else:
            in_content = message.content
        # 'https://discordapp.com/channels/{}/{}/{}'.format(message.channel.guild.id, message.channel.id, message.id)
        urlParts = extract_identifiers_messagelink.search(in_content).groups()
        if len(urlParts) == 3:
            guild_id = int(urlParts[0])
            channel_id = int(urlParts[1])
            message_id = int(urlParts[2])
            guild = client.get_guild(guild_id)
            if guild is None:
                print("PMF: Fletcher is not in guild ID "+str(guild_id))
                return
            channel = guild.get_channel(channel_id)
            target_message = await channel.get_message(message_id)
            # created_at is naîve, but specified as UTC by Discord API docs
            sent_at = target_message.created_at.strftime("%B %d, %Y %I:%M%p UTC")
            content = target_message.content
            if content == "":
                content = "*No Text*"
            if message.guild and message.guild.id == guild_id and message.channel.id == channel_id:
                content = "Message from {} sent at {}:\n{}".format(target_message.author.name, sent_at, content)
            elif message.guild and message.guild.id == guild_id:
                content = "Message from {} sent in <#{}> at {}:\n{}".format(target_message.author.name, channel_id, sent_at, content)
            else:
                content = "Message from {} sent in #{} ({}) at {}:\n{}".format(target_message.author.name, channel.name, guild.name, sent_at, content)
            attachments = []
            if len(target_message.attachments) > 0:
                plural = ""
                if len(target_message.attachments) > 1:
                    plural = "s"
                content = content + "\n "+str(len(target_message.attachments))+" file"+plural+" attached"
                if target_message.channel.is_nsfw() and not message.channel.is_nsfw():
                    content = content + " from an R18 channel."
                    for attachment in target_message.attachments:
                        content = content + "\n• <"+attachment.url+">"
                else:
                    for attachment in target_message.attachments:
                        print("Syncing "+attachment.filename)
                        attachment_blob = io.BytesIO()
                        await attachment.save(attachment_blob)
                        attachments.append(discord.File(attachment_blob, attachment.filename))

            if args is not None and args[0].isdigit():
                content = content + f'\nSource: https://discordapp.com/channels/{guild_id}/{channel_id}/{message_id}'
            # TODO 🔭 to preview?
            return await message.channel.send(content, files=attachments)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("PMF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        # better for there to be no response in that case

async def messagelink_function(message, client, args):
    global config
    try:
        msg = None
        for channel in message.channel.guild.text_channels:
            try:
                msg = await channel.get_message(int(args[0]))
                break
            except discord.Forbidden as e:
                pass
            except discord.NotFound as e:
                pass
        if msg and not (len(args) == 2 and args[1] == 'INTPROC'):
            await message.channel.send('Message link on behalf of {}: https://discordapp.com/channels/{}/{}/{}'.format(message.author, msg.channel.guild.id, msg.channel.id, msg.id))
            if 'snappy' in config['discord'] and config['discord']['snappy']:
                await message.delete()
            return
        elif msg:
            return 'https://discordapp.com/channels/{}/{}/{}'.format(msg.channel.guild.id, msg.channel.id, msg.id)
        else:
            return await message.channel.send('Message not found', delete_after=60)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("MLF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

async def bookmark_function(message, client, args):
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            if str(args[0].emoji) == "🔖":
                return await args[1].send("Bookmark to conversation in #{} ({}) https://discordapp.com/channels/{}/{}/{} via reaction to {}".format(message.channel.name, message.channel.guild.name, message.channel.guild.id, message.channel.id, message.id, message.content))
            elif str(args[0].emoji) == "🔗":
                return await args[1].send("https://discordapp.com/channels/{}/{}/{}".format(message.channel.guild.id, message.channel.id, message.id))
        else:
            await message.author.send("Bookmark to conversation in #{} ({}) https://discordapp.com/channels/{}/{}/{} {}".format(message.channel.name, message.channel.guild.name, message.channel.guild.id, message.channel.id, message.id, " ".join(args)))
            return await message.add_reaction('✅')
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("BMF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

reminder_timerhandle = None
async def table_exec_function(client):
    try:
        global conn
        cur = conn.cursor()
        cur.execute("SELECT userid, guild, channel, message, content, created FROM reminders WHERE scheduled > NOW();")
        tabtuple = cur.fetchone()
        completed = []
        while tabtuple:
            user = await client.get_user_info(tabtuple[0])
            guild_id = tabtuple[1]
            channel_id = tabtuple[2]
            message_id = tabtuple[3]
            guild = client.get_guild(guild_id)
            if guild is None:
                print("PMF: Fletcher is not in guild ID "+str(guild_id))
                await user.send("You tabled a discussion in a server that Fletcher no longer services. The content of the discussion prompt is reproduced below: {}".format(tabtuple[4]))
                completed[-1] = tabtuple[:3]
                tabtuple = cur.fetchone()
                continue
            channel = guild.get_channel(channel_id)
            sent_at = created.strftime("%B %d, %Y %I:%M%p UTC")
            content = tabtuple[4]
            try:
                target_message = await channel.get_message(message_id)
                # created_at is naîve, but specified as UTC by Discord API docs
                content = target_message.content
            except discord.NotFound as e:
                pass
            await user.send("You tabled a discussion at {}: want to pick that back up?\nDiscussion link: https://discordapp.com/channels/{}/{}/{}\nContent:".format(created_at, guild_id, channel_id, message_id))
            await user.send(content)
            completed[-1] = tabtuple[:3]
            tabtuple = cur.fetchone()
        for complete in completed:
            cur.execute("DELETE FROM reminders WHERE userid = %s AND guild = %s AND channel = %s AND message = %s;", complete)
        conn.commit()
        loop = asyncio.get_running_loop()
        reminder_timerhandle = loop.call_later(61, table_exec_function, client)
    except Exception as e:
        if cur is not None:
            conn.rollback()
        exc_type, exc_obj, exc_tb = exc_info()
        print("TXF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

async def table_function(message, client, args):
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            if str(args[0].emoji) == "🏓":
                global conn
                cur = conn.cursor()
                interval = "1 minute"
                cur.execute("INSERT INTO reminders (userid, guild, channel, message, content, scheduled) VALUES (%s, %s, %s, %s, %s, NOW() + INTERVAL '"+interval+"');", [args[1].id, message.guild.id, message.channel.id, message.id, message.content])
                return await args[1].send("Tabling conversation in #{} ({}) https://discordapp.com/channels/{}/{}/{} via reaction to {} for {}".format(message.channel.name, message.channel.guild.name, message.channel.guild.id, message.channel.id, message.id, message.content, interval))
    except Exception as e:
        if cur is not None:
            conn.rollback()
        exc_type, exc_obj, exc_tb = exc_info()
        print("TF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

def localizeName(user, guild):
    localized = guild.get_member(user.id)
    if localized is None:
        localizeName = user.name
    else:
        localized = localized.display_name
    return localized

# Register this module's commands
def autoload(ch):
    ch.add_command({
        'trigger': ['!teleport', '!portal'],
        'function': teleport_function,
        'async': True,
        'args_num': 1,
        'args_name': ['string'],
        'description': 'Create a link bridge to another channel'
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
        'trigger': ['🔖', '🔗', '!bookmark'],
        'function': bookmark_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'DM the user a bookmark to the current place in conversation',
        })
    ch.add_command({
        'trigger': ['🏓'],
        'function': table_function,
        'async': True,
        'hidden': True,
        'args_num': 0,
        'args_name': [],
        'description': 'Table a discussion for later.',
        })
    loop = asyncio.get_running_loop()
    if reminder_timerhandle:
        reminder_timerhandle.cancel()
    reminder_timerhandle = loop.call_later(61, table_exec_function, client)
