from datetime import datetime
import discord
import messagefuncs
import janissary
import re
from sys import exc_info
import textwrap

class CommandHandler:

    # constructor
    def __init__(self, client):
        self.client = client
        self.commands = []
        self.join_handlers = {}
        self.remove_handlers = {}
        self.reload_handlers = {}
        self.tag_id_as_command = re.compile('(?:^(?:Oh)?\s*(?:<@'+str(client.user.id)+'>|Fletch[er]*)[, .]*)|(?:[, .]*(?:<@'+str(client.user.id)+'>|Fletch[er]*)[, .]*$)', re.IGNORECASE)
        self.bang_remover = re.compile('^!+')

    def add_command(self, command):
        self.commands.append(command)

    def add_remove_handler(self, func_name, func):
        self.remove_handlers[func_name] = func

    def add_join_handler(self, func_name, func):
        self.join_handlers[func_name] = func

    def add_reload_handler(self, func_name, func):
        self.reload_handlers[func_name] = func

    async def reaction_handler(self, reaction):
        global config
        messageContent = str(reaction.emoji)
        user = await self.client.get_user_info(reaction.user_id)
        channel = self.client.get_channel(reaction.channel_id)
        message = await channel.get_message(reaction.message_id)
        if type(channel) is discord.TextChannel:
            print("#"+channel.guild.name+":"+channel.name+" <"+user.name+":"+str(user.id)+"> reacting with "+messageContent+" to "+str(message.id))
        elif type(message.channel) is discord.DMChannel:
            print("@"+channel.recipient.name+" <"+user.name+":"+str(user.id)+"> reacting with "+messageContent+" to "+str(message.id))
        else:
            # Group Channels don't support bots so neither will we
            pass
        for command in self.commands:
            if messageContent.startswith(tuple(command['trigger'])) and (('admin' in command and command['admin'] and hasattr(user, 'guild_permissions') and user.guild_permissions.manage_webhooks) or 'admin' not in command or not command['admin']):
                print(command)
                if command['args_num'] == 0:
                    if str(user.id) in config['moderation']['blacklist-user-usage'].split(','):
                        raise Exception('Blacklisted command attempt by user')
                    print(command['function'])
                    if command['async']:
                        return await command['function'](message, self.client, [reaction, user])
                    else:
                        return await message.channel.send(str(command['function'](message, self.client, [reaction, user])))

    async def remove_handler(self, member):
        if "Guild "+str(member.guild.id) in config and 'on_member_remove' in config["Guild "+str(member.guild.id)]:
            member_remove_actions = config["Guild "+str(member.guild.id)]['on_member_remove'].split(',')
            for member_remove_action in member_remove_actions:
                if member_remove_action in self.remove_handlers.keys():
                    await self.remove_handlers[member_remove_action](member, self.client, config["Guild "+str(member.guild.id)])

    async def join_handler(self, member):
        if "Guild "+str(member.guild.id) in config and 'on_member_join' in config["Guild "+str(member.guild.id)]:
            member_join_actions = config["Guild "+str(member.guild.id)]['on_member_join'].split(',')
            for member_join_action in member_join_actions:
                if member_join_action in self.join_handlers.keys():
                    await self.join_handlers[member_join_action](member, self.client, config["Guild "+str(member.guild.id)])

    async def reload_handler(self):
        try:
            # Trigger reload handlers
            for guild in self.client.guilds:
                if "Guild "+str(guild.id) in config and 'on_reload' in config["Guild "+str(guild.id)]:
                    reload_actions = config["Guild "+str(guild.id)]['on_reload'].split(',')
                    for reload_action in reload_actions:
                        if reload_action in self.reload_handlers.keys():
                            await self.reload_handlers[reload_action](guild, self.client, config["Guild "+str(guild.id)])
        except Exception as e:
            exc_type, exc_obj, exc_tb = exc_info()
            print("RH[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

    async def command_handler(self, message):
        global config
        global sid
        try:
            if "Guild "+str(message.guild.id) in config and 'automod-blacklist-category' in config["Guild "+str(message.guild.id)]:
                blacklist_category = [int(i) for i in config["Guild "+str(message.guild.id)]['automod-blacklist-category'].split(',')]
            else:
                blacklist_category = []
            if "Guild "+str(message.guild.id) in config and 'automod-blacklist-channel' in config["Guild "+str(message.guild.id)]:
                blacklist_channel = [int(i) for i in config["Guild "+str(message.guild.id)]['automod-blacklist-channel'].split(',')]
            else:
                blacklist_channel = []
            if type(message.channel) is discord.TextChannel and message.channel.category_id not in blacklist_category and message.channel.id not in blacklist_channel:
                sent_com_score = sid.polarity_scores(message.content)['compound']
                if message.content == "VADER NEUTRAL":
                    sent_com_score = 0
                elif message.content == "VADER GOOD":
                    sent_com_score = 1
                elif message.content == "VADER BAD":
                    sent_com_score = -1
                print(str(message.id)+" #"+message.guild.name+":"+message.channel.name+" <"+message.author.name+":"+str(message.author.id)+"> ["+str(sent_com_score)+"] "+message.content)
                if 'Guild '+str(message.guild.id) in config and 'sent-com-score-threshold' in config['Guild '+str(message.guild.id)] and sent_com_score <= float(config['Guild '+str(message.guild.id)]['sent-com-score-threshold']) and message.webhook_id is None and message.guild.name in config['moderation']['guilds'].split(','):
                    await janissary.modreport_function(message, self.client, ("\n[Sentiment Analysis Combined Score "+str(sent_com_score)+'] '+message.content).split(' '))
            else:
                if type(message.channel) is discord.TextChannel:
                    print(str(message.id)+" #"+message.guild.name+":"+message.channel.name+" <"+message.author.nam+":"+str(message.author.id)+"> [Nil] "+message.content)
                elif type(message.channel) is discord.DMChannel:
                    print(str(message.id)+" @"+message.channel.recipient.name+" <"+message.author.nam+":"+str(message.author.id)+"> [Nil] "+message.content)
                else:
                    # Group Channels don't support bots so neither will we
                    pass
        except AttributeError as e:
            if type(message.channel) is discord.TextChannel:
                print("#"+message.channel.name+" <"+message.author.name+":"+str(message.author.id)+"> [Nil] "+message.content)
            elif type(message.channel) is discord.DMChannel:
                        print("@"+message.channel.recipient.name+" <"+message.author.name+":"+str(message.author.id)+"> [Nil] "+message.content)
            else:
                # Group Channels don't support bots so neither will we
                pass
            pass
        if messagefuncs.extract_identifiers_messagelink.search(message.content) and "!preview" not in message.content:
            if str(message.author.id) not in config['moderation']['blacklist-user-usage'].split(','):
                await messagefuncs.preview_messagelink_function(message, self.client, None)
        if 'rot13' in message.content:
            if str(message.author.id) not in config['moderation']['blacklist-user-usage'].split(','):
                await message.add_reaction(self.client.get_emoji(int(config['discord']['rot13'])))
        searchString = message.content
        searchString = self.tag_id_as_command.sub('!', searchString)
        if config['interactivity']['enhanced-command-finding'] == "on":
            if len(searchString) and searchString[-1] == "!":
                searchString = "!"+searchString[:-1]
            searchString = self.bang_remover.sub('!', searchString)
        searchString = searchString.rstrip()
        if not searchString.startswith("!"):
            return
        for command in self.commands:
            if searchString.lower().startswith(tuple(command['trigger'])) and (('admin' in command and command['admin'] and hasattr(message.author, 'guild_permissions') and message.author.guild_permissions.manage_webhooks) or 'admin' not in command or not command['admin']):
                print("[CH] Triggered "+str(command))
                args = searchString.split(' ')
                args = [item for item in args if item]
                args.pop(0)
                if str(message.author.id) in config['moderation']['blacklist-user-usage'].split(','):
                    await message.add_reaction('💔')
                    await message.channel.send("I'll only talk to you when you stop being mean to me, "+message.author.display_name+"!")
                    raise Exception('Blacklisted command attempt by user')
                if command['args_num'] == 0:
                    if command['async']:
                        return await command['function'](message, self.client, args)
                    else:
                        return await message.channel.send(str(command['function'](message, self.client, args)))
                else:
                    if len(args) >= command['args_num']:
                        if command['async']:
                            return await command['function'](message, self.client, args)
                        else:
                            return await message.channel.send(str(command['function'](message, self.client, args)))
                    else:
                        return await message.channel.send('command "{}" requires {} argument(s) "{}"'.format(command['trigger'][0], command['args_num'], ', '.join(command['args_name'])))

async def help_function(message, client, args):
    global ch
    try:
        arg = None
        verbose = False
        public = False
        while len(args) > 0:
            arg = args[0]
            arg = arg.strip().lower()
            if   arg == "verbose":
                verbose = True
                arg = None
                args = args[1:]
            elif arg == "public":
                public = True
                arg = None
                args = args[1:]
            else:
                arg = args[0]
                break
        if len(args) == 0:
            arg = None
        if hasattr(message.author, 'guild_permissions') and message.author.guild_permissions.manage_webhooks and len(args) > 0 and verbose:
            def command_filter(c):
                return ('hidden' not in c.keys() or c['hidden'] == False)
        else:
            def command_filter(c):
                return ('admin' not in c.keys() or c['admin'] == False) and ('hidden' not in c.keys() or c['hidden'] == False)
        accessible_commands = filter(command_filter, ch.commands)
        if arg:
            keyword = " ".join(args).strip().lower()
            if keyword.startswith('!'):
                def query_filter(c):
                    for trigger in c['trigger']:
                        if keyword in trigger:
                            return True
                    return False
            else:
                def query_filter(c):
                    for trigger in c['trigger']:
                        if keyword in trigger:
                            return True
                    if keyword in c['description'].lower():
                        return True
                    return False
            accessible_commands = list(filter(query_filter, accessible_commands))
            # Set verbose if filtered list
            if len(accessible_commands) < 5:
                verbose = True
        if len(args) > 0 and verbose:
            helpMessageBody = "\n".join(["`{}`: {}\nArguments ({}): {}".format("` or `".join(command['trigger']), command['description'], command['args_num'], " ".join(command['args_name'])) for command in accessible_commands])
        else:
            helpMessageBody = "\n".join(["`{}`: {}".format("` or `".join(command['trigger'][:2]), command['description']) for command in accessible_commands])
        if (not hasattr(message.author, 'guild_permissions')) or (message.author.guild_permissions.manage_webhooks and not public):
            target = message.author
            await message.add_reaction('✅')
        else:
            target = message.channel
        await messagefuncs.sendWrappedMessage(helpMessageBody, target)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("HF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

def dumpconfig_function(message, client, args):
    print("Channels Loaded:")
    for channel in client.get_all_channels():
        print(str(channel.guild)+" "+str(channel))

def autoload(ch):
    global tag_id_as_command
    global client
    ch.add_command({
        'trigger': ['!dumpconfig'],
        'function': dumpconfig_function,
        'async': False,
        'admin': True,
        'args_num': 0,
        'args_name': [],
        'description': 'Output current config'
        })
    ch.add_command({
        'trigger': ['!help', '!man'],
        'function': help_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'List commands and arguments'
        })
