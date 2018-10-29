# bot.py
import configparser
from datetime import datetime
import discord
import psycopg2

# command handler class

class CommandHandler:

    # constructor
    def __init__(self, client):
        self.client = client
        self.commands = []

    def add_command(self, command):
        self.commands.append(command)

    async def command_handler(self, message):
        print(message.content)
        for command in self.commands:
            if message.content.startswith(tuple(command['trigger'])):
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
config.read('/home/lin/fletcher/.fletcherrc')

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
        bannerMessage = ""
        while sentuple:
            bannerName = sentuple[1]
            if bannerName is None or bannerName.strip() == "" or " " in bannerName:
                bannerName = "Banner {}".format(str(sentuple[0]))
            bannerMessage = bannerMessage + "**{}**".format(bannerName)
            if sentuple[2]:
                bannerMessage = bannerMessage + ": " + sentuple[2]
            bannerMessage = bannerMessage + " ({} pledgers)\nCreated at {}\n".format(str(sentuple[7]), sentuple[3].strftime("%Y-%m-%d %H:%M:%S"))
            if sentuple[4]:
                bannerMessage = bannerMessage + "Goal reached at {}\n".format(sentuple[4].strftime("%Y-%m-%d %H:%M:%S"))
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
            print("to syntax, dropping arg[0]")
        fromChannel = message.channel
        targetChannel = args[0].strip()
        channelLookupBy = "Name"
        toChannel = None
        if targetChannel.startswith('<#'):
            targetChannel= targetChannel[2:-1].strip()
            channelLookupBy = "ID"
        elif targetChannel.startswith('#'):
            targetChannel= targetChannel[1:].strip()
        print('Target Channel '+channelLookupBy+': '+targetChannel)
        if channelLookupBy == "Name":
            toChannel = discord.utils.get(fromChannel.guild.text_channels, name=targetChannel)
        elif channelLookupBy == "ID":
            toChannel = client.get_channel(int(targetChannel))
        print('Opening From '+str(fromChannel))
        fromMessage = await fromChannel.send('Opening Portal To <#{}>'.format(toChannel.id))
        print('Opening To '+str(toChannel))
        toMessage = await toChannel.send('Opening Portal To <#{}>'.format(fromChannel.id))
        print('Editing From')
        embedPortal = discord.Embed(title="Portal opened to #{}".format(toChannel.name), description="https://discordapp.com/channels/{}/{}/{} {}".format(toChannel.guild.id, toChannel.id, toMessage.id, " ".join(args[1:]))).set_footer(icon_url="https://download.lin.anticlack.com/fletcher/blue-portal.png",text="On behalf of {}".format(message.author.nick or message.author))
        tmp = await fromMessage.edit(content=None,embed=embedPortal)
        print('Editing To')
        embedPortal = discord.Embed(title="Portal opened from #{}".format(fromChannel.name), description="https://discordapp.com/channels/{}/{}/{} {}".format(fromChannel.guild.id, fromChannel.id, fromMessage.id, " ".join(args[1:]))).set_footer(icon_url="https://download.lin.anticlack.com/fletcher/orange-portal.png",text="On behalf of {}".format(message.author.nick or message.author))
        tmp = await toMessage.edit(content=None,embed=embedPortal)
        print('Portal Opened')
        return 'Portal opened on behalf of {} to {}'.format(message.author, args[0])
    except Exception as e:
        return e

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
            return await message.channel.send('Message link on behalf of {}: https://discordapp.com/channels/{}/{}/{}'.format(message.author, message.channel.guild.id, message.channel.id, message.id))
        return await message.channel.send('Message not found')
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
            cur.execute("SELECT array_length(subscribers, 1), triggercount, name, subscribers FROM sentinel WHERE id = %s;", [bannerId])
            bannerInfo = cur.fetchone()
            if bannerInfo[0] == bannerInfo[1]: # Triggered banner! Yay!
                cur.execute("UPDATE sentinel SET triggered = CURRENT_TIMESTAMP WHERE id = %s;", [bannerId])
                conn.commit()
                return await message.channel.send('Critical mass reached for banner {}! Paging supporters: <@{}>. Now it\'s up to you to fulfill your goal :)'.format(bannerInfo[2], ">, <@".join([str(userId) for userId in bannerInfo[3]])))
            elif bannerInfo[0] > bannerInfo[1]:
                conn.commit()
                return await message.channel.send('Critical mass has already been reached for banner {}!'.format(bannerInfo[2]))
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
    'trigger': ['!message'],
    'function': messagelink_function,
    'async': True,
    'args_num': 1,
    'args_name': ['string'],
    'description': 'Create a link to the message with ID `!message XXXXXX`'
})
## end hello command

# bot is ready
@client.event
async def on_ready():
    try:
        # print bot information
                print(client.user.name)
                print(client.user.id)
                print('Discord.py Version: {}'.format(discord.__version__))

    except Exception as e:
        print(e)

# on new message
@client.event
async def on_message(message):
    # print message content
    # if the message is from the bot itself ignore it
    if message.author == client.user:
        pass
    else:

        # try to evaluate with the command handler
        try:
            await ch.command_handler(message)

        # message doesn't contain a command trigger
        except TypeError as e:
            pass

        # generic python error
        except Exception as e:
            print(e)

# start bot
client.run(token)
