# bot.py
import discord

# command handler class

class CommandHandler:

    # constructor
    def __init__(self, client):
        self.client = client
        self.commands = []

    def add_command(self, command):
        self.commands.append(command)

    async def command_handler(self, message):
        for command in self.commands:
            if message.content.startswith(command['trigger']):
                args = message.content.split(' ')
                if args[0] == command['trigger']:
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
                            return await message.channel.send('command "{}" requires {} argument(s) "{}"'.format(command['trigger'], command['args_num'], ', '.join(command['args_name'])))
                            break
                else:
                    break

# create discord client
client = discord.Client()

# token from https://discordapp.com/developers
token = 'INSERTMEHERE'

ch = CommandHandler(client)

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
ch.add_command({
    'trigger': '!portal',
    'function': teleport_function,
    'async': True,
    'args_num': 1,
    'args_name': ['string'],
    'description': 'Will create a link bridge to another channel'
})
ch.add_command({
    'trigger': '!teleport',
    'function': teleport_function,
    'async': True,
    'args_num': 1,
    'args_name': ['string'],
    'description': 'Will create a link bridge to another channel'
})
ch.add_command({
    'trigger': '!message',
    'function': messagelink_function,
    'async': True,
    'args_num': 1,
    'args_name': ['string'],
    'description': 'Will create a link to the message with ID `!message XXXXXX`'
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
            print(message)
            print(message.content)
            await ch.command_handler(message)

        # message doesn't contain a command trigger
        except TypeError as e:
            pass

        # generic python error
        except Exception as e:
            print(e)

# start bot
client.run(token)
