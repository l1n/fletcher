import asyncio
from datetime import datetime
import discord
from sys import exc_info
import textwrap
# global conn set by reload_function

async def table_exec_function():
    try:
        global ch
        client = ch.client
        global conn
        cur = conn.cursor()
        now = datetime.utcnow()
        cur.execute("SELECT userid, guild, channel, message, content, created, trigger_type FROM reminders WHERE %s > scheduled;", [now])
        tabtuple = cur.fetchone()
        modes = {
                "table": "tabled a discussion",
                "unban": "snoozed a channel",
                }
        while tabtuple:
            user = await client.get_user_info(tabtuple[0])
            guild_id = tabtuple[1]
            channel_id = tabtuple[2]
            message_id = tabtuple[3]
            created = tabtuple[5]
            created_at = created.strftime("%B %d, %Y %I:%M%p UTC")
            content = tabtuple[4]
            mode = tabtuple[6]
            mode_desc = modes[mode]
            guild = client.get_guild(guild_id)
            if guild is None:
                print("PMF: Fletcher is not in guild ID "+str(guild_id))
                await user.send("You {} in a server that Fletcher no longer services. The content of the discussion prompt is reproduced below: {}".format(mode_desc, content))
                completed.append(tabtuple[:3])
                tabtuple = cur.fetchone()
                continue
            channel = guild.get_channel(channel_id)
            try:
                target_message = await channel.get_message(message_id)
                # created_at is naîve, but specified as UTC by Discord API docs
                content = target_message.content
            except discord.NotFound as e:
                pass
            if mode == "unban":
                permissions = channel.overwrites_for(user)
                if permissions.read_messages == False and permissions.send_messages == False and permissions.embed_links == False:
                    await channel.set_permissions(user, overwrite=None, reason="Unban triggered by schedule obo "+user.name)
                    await user.send("Unban triggered by schedule for {}#{} (`!part` to leave channel permanently)".format(guild.name, channel.name))
            elif mode == "table":
                msg_chunks = textwrap.wrap("You tabled a discussion at {}: want to pick that back up?\nDiscussion link: https://discordapp.com/channels/{}/{}/{}\nContent: {}".format(created_at, guild_id, channel_id, message_id, content), 2000, replace_whitespace=False)
                for hunk in msg_chunks:
                    await user.send(hunk)
            tabtuple = cur.fetchone()
        cur.execute("DELETE FROM reminders WHERE %s > scheduled;", [now])
        conn.commit()
        global reminder_timerhandle
        await asyncio.sleep(61)
        reminder_timerhandle = asyncio.create_task(table_exec_function())
    except asyncio.CancelledError:
        print('TXF: Interrupted, bailing out')
        raise
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
                interval = "1 day"
                cur.execute("INSERT INTO reminders (userid, guild, channel, message, content, scheduled) VALUES (%s, %s, %s, %s, %s, NOW() + INTERVAL '"+interval+"');", [args[1].id, message.guild.id, message.channel.id, message.id, message.content])
                conn.commit()
                return await args[1].send("Tabling conversation in #{} ({}) https://discordapp.com/channels/{}/{}/{} via reaction to {} for {}".format(message.channel.name, message.channel.guild.name, message.channel.guild.id, message.channel.id, message.id, message.content, interval))
    except Exception as e:
        if cur is not None:
            conn.rollback()
        exc_type, exc_obj, exc_tb = exc_info()
        print("TF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

# Register this module's commands
def autoload(ch):
    ch.add_command({
        'trigger': ['🏓'],
        'function': table_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'Table a discussion for later.',
        })
    global reminder_timerhandle
    try:
        reminder_timerhandle.cancel()
    except NameError:
        pass
    reminder_timerhandle = asyncio.create_task(table_exec_function())
