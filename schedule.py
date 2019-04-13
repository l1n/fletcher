import asyncio
from datetime import datetime
import discord
from sys import exc_info
# global conn set by reload_function

async def table_exec_function():
    try:
        print("TXF: audit")
        global ch
        client = ch.client
        global conn
        cur = conn.cursor()
        now = datetime.utcnow()
        cur.execute("SELECT userid, guild, channel, message, content, created FROM reminders WHERE %s > scheduled;", [now])
        tabtuple = cur.fetchone()
        while tabtuple:
            user = await client.get_user_info(tabtuple[0])
            guild_id = tabtuple[1]
            channel_id = tabtuple[2]
            message_id = tabtuple[3]
            created = tabtuple[5]
            created_at = created.strftime("%B %d, %Y %I:%M%p UTC")
            content = tabtuple[4]
            guild = client.get_guild(guild_id)
            if guild is None:
                print("PMF: Fletcher is not in guild ID "+str(guild_id))
                await user.send("You tabled a discussion in a server that Fletcher no longer services. The content of the discussion prompt is reproduced below: {}".format(content))
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
            await user.send("You tabled a discussion at {}: want to pick that back up?\nDiscussion link: https://discordapp.com/channels/{}/{}/{}\nContent:".format(created_at, guild_id, channel_id, message_id))
            await user.send(content)
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
