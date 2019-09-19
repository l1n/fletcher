import asyncio
from datetime import datetime, timedelta
import discord
import logging
import messagefuncs
from sys import exc_info
import textwrap
import text_manipulators
# global conn set by reload_function

logger = logging.getLogger('fletcher')

async def addrole_function(message, client, args):
    global config
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            pass # Reaction
        else:
            role_list = message.channel.guild.roles
            argString = " ".join(args)
            roleProperties = {
                    "name": None,
                    "colour": None,
                    "mentionable": True
                    }
            if " with " in argString:
                roleProperties["name"] = argString.split(" with")[0]
                argString = argString.split(" with")[1].lower().replace("color", "colour").replace("pingable", "mentionable")
                it = iter(argString.trim().replace(" and ", "").replace(", ", "").split(" "))
                for prop, val in zip(it, it):
                    if prop == "colour":
                        roleProperties["colour"] = discord.Colour.from_rgb(int(val[0-1]), int(val[2-3]), int(val[4-5]))
                    elif (prop == "mentionable" and val in ["no", "false"]) or (prop == "not" and val == "mentionable"):
                        roleProperties["mentionable"] = False
            else:
                roleProperties["name"] = argString

            role = discord.utils.get(role_list, name=roleProperties["name"])
            if role is not None:
                err = "Role already exists!"
                if not role.mentionable or message.channel.permissions_for(message.author).manage_messages:
                    if role in message.author.roles:
                        err = err + " `!revoke "+role.name+" from me` to remove this role from yourself."
                    else:
                        err = err + " `!assign "+role.name+" to me` to add this role to yourself."
                else:
                    if role in message.author.roles:
                        err = err + " An administrator can `!revoke "+role.name+" from @"+str(message.author.id)+"` to remove this role from you."
                    else:
                        err = err + " An administrator can `!assign "+role.name+" to @"+str(message.author.id)+"` to add this role to you."
                return await message.channel.send(err)
            else:
                role = await message.channel.guild.create_role(
                        name   = roleProperties["name"],
                        colour = roleProperties["colour"],
                        mentionable = True,
                        reason="Role added on behalf of "+str(message.author.id))
                await message.channel.send("Role "+role.mention+" successfully created.")
                await role.edit(mentionable=roleProperties["mentionable"])
                if 'snappy' in config['discord'] and config['discord']['snappy']:
                    await message.delete()
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'ARF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def assignrole_function(message, client, args):
    global config
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            pass # Reaction
        else:
            role_list = message.channel.guild.roles
            argString = " ".join(args)
            if argString.endswith(" to me"):
                argString = argString[:-6]
            roleProperties = {
                    "name": None
                    }
            roleProperties["name"] = argString

            role = discord.utils.get(role_list, name=roleProperties["name"])
            if role is not None:
                if not role.mentionable or message.channel.permissions_for(message.author).manage_messages:
                    if role in message.author.roles:
                        return await message.channel.send("You already have that role, `!revoke "+role.name+" from me` to remove this role from yourself.")
                    else:
                        if 'snappy' in config['discord'] and config['discord']['snappy']:
                            await message.delete()
                        await message.author.add_roles(role, reason="Self-assigned", atomic=False)
                        return await message.channel.send("Role assigned, `!revoke "+role.name+" from me` to remove this role from yourself.")
                else:
                    # TODO unimplemented
                    pass;
                    if role in message.author.roles:
                        err = err + " An administrator can `!revoke "+role.name+" from @"+str(message.author.id)+"` to remove this role from you."
                    else:
                        err = err + " An administrator can `!assign "+role.name+" to @"+str(message.author.id)+"` to add this role to you."
                return await message.channel.send(err)
            else:
                await message.channel.send("Role "+roleProperties["name"]+" does not exist, use the addrole command to create it.")
                if 'snappy' in config['discord'] and config['discord']['snappy']:
                    await message.delete()
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'ASRF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def revokerole_function(message, client, args):
    global config
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            pass # Reaction
        else:
            role_list = message.channel.guild.roles
            argString = " ".join(args)
            if argString.endswith(" from me"):
                argString = argString[:-8]
            roleProperties = {
                    "name": None
                    }
            roleProperties["name"] = argString

            role = discord.utils.get(role_list, name=roleProperties["name"])
            if role is not None:
                if not role.mentionable or message.channel.permissions_for(message.author).manage_messages:
                    if role in message.author.roles:
                        if 'snappy' in config['discord'] and config['discord']['snappy']:
                            await message.delete()
                        await message.author.remove_roles(role, reason="Self-assigned", atomic=False)
                        return await message.channel.send("Role revoked, `!assign "+role.name+" to me` to add this role to yourself.")
                    else:
                        return await message.channel.send("You don't have that role, `!assign "+role.name+" to me` to assign this role to yourself.")
                else:
                    # TODO unimplemented
                    pass;
                    if role in message.author.roles:
                        err = err + " An administrator can `!revoke "+role.name+" from @"+str(message.author.id)+"` to remove this role from you."
                    else:
                        err = err + " An administrator can `!assign "+role.name+" to @"+str(message.author.id)+"` to add this role to you."
                return await message.channel.send(err)
            else:
                await message.channel.send("Role "+roleProperties["name"]+" does not exist, use the addrole command to create it.")
                if 'snappy' in config['discord'] and config['discord']['snappy']:
                    await message.delete()
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'RSRF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def delrole_function(message, client, args):
    global config
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            pass # Reaction
        else:
            role_list = message.channel.guild.roles
            argString = " ".join(args)
            roleProperties = {
                    "name": None
                    }
            roleProperties["name"] = argString

            role = discord.utils.get(role_list, name=roleProperties["name"])
            if role is not None:
                if message.channel.permissions_for(message.author).manage_messages:
                    await role.delete(reason="On behalf of "+str(message.author))
                    await message.channel.send("Role `@"+roleProperties["name"]+"` deleted.")
                else:
                    await message.channel.send("You do not have permission to delete role `@"+roleProperties["name"]+"`.")
            else:
                err = "Role `@"+roleProperties["name"]+"` does not exist!"
                if message.channel.permissions_for(message.author).manage_messages:
                    err = err + " `!addrole "+role.name+"` to add this role."
                else:
                    err = err + " An administrator can `!addrole "+role.name+"` to add this role."
                await message.channel.send(err)
                if 'snappy' in config['discord'] and config['discord']['snappy']:
                    await message.delete()
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'DRF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def modping_function(message, client, args):
    global config
    try:
        if len(args) == 2 and type(args[1]) is discord.User:
            pass # Reaction
        else:
            if not message.channel.permissions_for(message.author).manage_messages:
                def gaveled_by_admin_check(reaction, user):
                    return user.guild_permissions.manage_webhooks and str(reaction.emoji) == '<:gavel:430638348189827072>'
                try: 
                    await modreport_function(message, client, ("\nRole ping requested for "+" ".join(args).lstrip("@")).split(' '))
                    reaction, user = await client.wait_for('reaction_add', timeout=6000.0, check=gaveled_by_admin_check)
                except asyncio.TimeoutError:
                    raise Exception('Timed out waiting for approval')
            role_list = message.channel.guild.roles
            role = discord.utils.get(role_list, name=" ".join(args).lstrip("@"))
            lay_mentionable = role.mentionable
            if not lay_mentionable:
                await role.edit(mentionable=True)
            mentionPing = await message.channel.send(message.author.name+' pinging '+role.mention)
            if not lay_mentionable:
                await role.edit(mentionable=False)
            if 'snappy' in config['discord'] and config['discord']['snappy']:
                mentionPing.delete()
            logger.debug(f'MPF: pinged {mentionPing.id} for guild {message.guild.name}')
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'MPF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def modreport_function(message, client, args):
    global config
    try:
        report_content = None
        plaintext = None
        automod = None
        if len(args) == 2 and type(args[1]) is discord.User:
            try:
                await message.remove_reaction('👁‍🗨', args[1])
            except discord.Forbidden as e:
                logger.warning("MRF: Forbidden from removing modreport reaction")
                pass
            plaintext = message.content
            report_content = f'Mod Report: #{message.channel.name} ({message.channel.guild.name}) {message.jump_url} via reaction to '
            automod = False
        else:
            plaintext = " ".join(args)
            report_content = f'Mod Report: #{message.channel.name} ({message.channel.guild.name}) {message.jump_url} '
            automod = True
        if message.channel.is_nsfw():
            report_content = report_content + await text_manipulators.rot13_function(message, client, [plaintext, 'INTPROC'])
        else:
            report_content = report_content + plaintext
        if "Guild "+str(message.guild.id) in config:
            scoped_config = config["Guild "+str(message.guild.id)]
        else:
            raise Exception("No guild-specific configuration for moderation on guild "+str(message.guild))
        if "moderation" in scoped_config and scoped_config["moderation"] == "On":
            if "mod-message-prefix" in scoped_config:
                report_content = scoped_config["mod-message-prefix"] + "\n" + report_content
            if "mod-message-suffix" in scoped_config:
                report_content = report_content + "\n" + scoped_config["mod-message-suffix"]
            if automod:
                users = scoped_config['mod-users'].split(',')
            else:
                users = scoped_config['manual-mod-users'].split(',')
            users = list(expand_target_list(users, message.guild))
            for target in users:
                modmail = await messagefuncs.sendWrappedMessage(report_content, target)
                if message.channel.is_nsfw():
                    await modmail.add_reaction('🕜')
        else:
            raise Exception("Moderation disabled on guild "+str(message.guild))
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'MRF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

def expand_target_list(targets, guild):
    inputs = list(targets)
    targets = set()
    for target in inputs:
        if target.startswith('r:'):
            members = guild.get_role(int(target[2:])).members
            targets.update(set(members))
        elif target.startswith('c:'):
            channel = guild.get_channel(int(target[2:]))
            targets.add(channel)
        else:
            # ID asssumed to be targets
            targets.add(guild.get_member(int(target)))
    return targets

async def lastactive_channel_function(message, client, args):
    try:
        lastMonth = None
        before = True
        now = datetime.utcnow()
        try:
            if args[0]:
                try:
                    lastMonth = now.date() - timedelta(days=int(args[0]))
                except ValueError:
                    if args[1]:
                        if args[0].startswith("a"):
                            before = False
                        lastMonth = now.date() - timedelta(days=int(args[1]))
                    pass
        except IndexError:
                    pass
        msg = ""
        for channel in message.channel.guild.text_channels:
            try:
                category_pretty = ""
                if channel.category_id:
                    category_pretty = f' [{client.get_channel(channel.category_id).name}]'
                created_at = (await channel.history(limit=1).flatten())[0].created_at
                created_pretty = text_manipulators.pretty_date(created_at)
                if created_pretty:
                    created_pretty = f' ({created_pretty})'
                if lastMonth:
                    if (before and lastMonth < created_at.date()) or (not before and lastMonth > created_at.date()):
                        msg = f'{msg}\n<#{channel.id}>{category_pretty}: {created_at.isoformat(timespec="minutes")}{created_pretty}'
                    else:
                        # filtered out
                        pass
                else:
                    msg = f'{msg}\n<#{channel.id}>{category_pretty}: {created_at.isoformat(timespec="minutes")}{created_pretty}'
            except discord.NotFound as e:
                pass
            except IndexError as e:
                msg = f'{msg}\n<#{channel.id}>{category_pretty}: Bad History'
                pass
            except discord.Forbidden as e:
                msg = f'{msg}\n<#{channel.id}>{category_pretty}: Forbidden'
                pass
        msg = f'**Channel Activity:**{msg}'
        await messagefuncs.sendWrappedMessage(msg, message.channel)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'LACF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def lastactive_user_function(message, client, args):
    try:
        lastMonth = None
        before = True
        now = datetime.utcnow()
        try:
            if args[0]:
                try:
                    lastMonth = now.date() - timedelta(days=int(args[0]))
                except ValueError:
                    if args[1]:
                        if args[0].startswith("a"):
                            before = False
                        lastMonth = now.date() - timedelta(days=int(args[1]))
                    pass
        except IndexError:
                    pass
        if message.guild.large:
            client.request_offline_members(message.guild)
        users = {}
        tomorrow = datetime.today() + timedelta(days=1)
        for m in message.guild.members:
            users[m.id] = tomorrow
        for channel in message.channel.guild.text_channels:
            async for message in channel.history(limit=None):
                try:
                    logger.debug(f'[{message.created_at} <#{channel.id}>] <@{message.author.id}>: {message.content}')
                    if message.created_at < users[message.author.id]:
                        users[message.author.id] = message.created_at
                except discord.NotFound as e:
                    pass
                except discord.Forbidden as e:
                    pass
        msg = f'**User Activity:**{msg}'
        for user_id, last_active in users:
            if last_active == datetime.today() + timedelta(days=1):
                last_active = "None"
            else:
                last_active = text_manipulators.pretty_date(last_active)
            msg = f'{msg}\n<@{user_id}>: {last_active}'
        await messagefuncs.sendWrappedMessage(msg, message.channel)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'LSU[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def kick_user_function(message, client, args):
    try:
        if len(message.mentions) >= 1:
            member = message.mentions[0]
        else:
            member = message.guild.get_member(int(args[0]))
        logMessage = " ".join(args[1:]).strip()
        if not len(logMessage):
            logMessage = "A message was not provided."
        logMessage = f'You have been kicked from {message.guild.name}. If you have questions, please contact a moderator for that guild.\nReason: {logMessage}'
        logger.info(f'KUF: <@{message.author.id}> kicked <@{member.id}> from {message.guild.id} for {logMessage}')
        try:
            await messagefuncs.sendWrappedMessage(logMessage, member)
        # TODO make this a more specific catch block
        except Exception as e:
            exc_type, exc_obj, exc_tb = exc_info()
            logger.error(f'KUF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')
            # Ignore blocks etc
            pass
        await member.kick(reason=f'{logMessage} obo {message.author.name}')
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'KUF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def lockout_user_function(message, client, args):
    try:
        if len(message.mentions) >= 1:
            member = message.mentions[0]
        else:
            member = message.guild.get_member(int(args[0]))
        if len(args) >= 2 and args[1] == "reset":
            mode = "reset"
        else:
            mode = "hide"
        if len(args) >= 3 and args[2] == "thorough":
            thorough = True
        else:
            thorough = False
        if len(args) >= 4:
            filter_id = int(args[3])
        else:
            filter_id = None
        log = "Lockout "+mode+" completed for "+member.name
        for category, channels in member.guild.by_category():
            if category is not None and ((filter_id and category.id == filter_id) or not filter_id):
                logMessage = str(member)+" from category "+str(category)+" in "+str(member.guild)
                logger.debug("LUF: "+logMessage)
                log = log + "\n" + logMessage
                if mode == "reset":
                    await category.set_permissions(member, overwrite=None, reason="Admin reset lockout obo "+message.author.name)
                else:
                    await category.set_permissions(member, read_messages=False, read_message_history=False, send_messages=False, reason="Admin requested lockout obo "+message.author.name)
            if (category is None) or (thorough and category is not None and ((filter_id and category.id == filter_id)) or not filter_id):
                for channel in channels:
                    logMessage = str(member)+" from non-category channel "+str(channel)+" in "+str(member.guild)
                    logger.debug("LUF: "+logMessage)
                    log = log + "\n" + logMessage
                    if mode == "reset":
                        await channel.set_permissions(member, overwrite=None, reason="Admin reset lockout obo "+message.author.name)
                    else:
                        await channel.set_permissions(member, read_messages=False, read_message_history=False, send_messages=False, reason="Admin requested lockout obo "+message.author.name)
        await messagefuncs.sendWrappedMessage(log, message.author)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'LUF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def part_channel_function(message, client, args):
    try:
        if len(message.channel_mentions) > 0:
            channel = message.channel_mentions[0]
        else:
            channel = messagefuncs.xchannel(args[0].strip(), message.guild)
            if channel is None:
                channel = message.channel
        await channel.set_permissions(message.author, read_messages=False, read_message_history=False, send_messages=False, reason="User requested part "+message.author.name)
        await message.add_reaction('✅')
        await message.author.send("Parted from channel #"+channel.name)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'PCF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def optin_channel_function(message, client, args):
    try:
        pass
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'OICF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

# Requires schedule.py to clear reminders
async def snooze_channel_function(message, client, args):
    try:
        global conn
        if len(message.channel_mentions) > 0:
            channels = message.channel_mentions
        elif args[0].strip()[-2:] == ':*':
            guild = discord.utils.get(client.guilds, name=messagefuncs.expand_guild_name(args[0]).strip()[:-2].replace("_", " "))
            channels = guild.text_channels
        else:
            channel = messagefuncs.xchannel(args[0].strip(), message.guild)
            if channel is None:
                channel = message.channel
            channels = [channel]
        if len(channels) > 0:
            channel = channels[0]
        else:
            channel = None
        if message.guild is not None:
            guild = message.guild
        elif hasattr(channel, 'guild'):
            guild = channel.guild
        else:
            await message.add_reaction('🚫')
            return await message.channel.send('Failed to locate channel, please check spelling.')
        cur = conn.cursor()
        if len(args) > 1:
            interval = float(args[1])
        else:
            interval = 24
        cur.execute("INSERT INTO reminders (userid, guild, channel, message, content, scheduled, trigger_type) VALUES (%s, %s, %s, %s, %s, NOW() + INTERVAL '"+str(interval)+" hours', 'unban');", [message.author.id, guild.id, message.channel.id, message.id, message.content])
        channel_names = ""
        for channel in channels:
            await channel.set_permissions(message.author, read_messages=False, read_message_history=False, send_messages=False, embed_links=False, reason="User requested snooze "+message.author.name)
            channel_names += f'{guild.name}:{channel.name}, '
        channel_names = channel_names[:-2]
        if args[0].strip()[-2:] == ':*':
            channel_names = channels[0].guild.name
        conn.commit()
        await message.add_reaction('✅')
        await message.author.send(f'Snoozed {channel_names} for {interval} hours (`!part` to leave channel permanently)')
    except discord.Forbidden as e:
        if "cur" in locals() and "conn" in locals():
            conn.rollback()
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'SNCF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')
        await message.channel.send("Snooze forbidden! I don't have the authority to do that.")
    except Exception as e:
        if "cur" in locals() and "conn" in locals():
            conn.rollback()
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'SNCF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def sudo_function(message, client, args):
    try:
        guild_config = ch.scope_config(guild=message.guild)
        if 'wheel-role' not in guild_config:
            raise Exception("No guild-specific configuration for wheel on guild "+str(message.guild))
        now = datetime.utcnow()
        role = message.guild.get_role(int(guild_config['wheel-role']))
        if not role:
            raise Exception("Wheel role not found")
        await message.author.add_roles(role, reason="Sudo escalation", atomic=False)
        await message.add_reaction('✅')
        tries = 0
        while tries < 600:
            await asyncio.sleep(1)
            try:
                # Discord audit log has an after parameter which hasn't worked in ages :(
                entry = await message.guild.audit_logs(limit=None, user=message.author, oldest_first=False).next()
            except discord.NoMoreItems:
                entry = None
                pass
            if entry.created_at > now:
                logger.info("SUDOF: "+str(entry))
                await message.author.remove_roles(role, reason="Sudo deescalation (commanded)", atomic=False)
                return
            tries = tries + 1
        logger.info("SUDOF: timeout")
        await message.author.remove_roles(role, reason="Sudo deescalation (timeout)", atomic=False)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'SUDOF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')

async def role_message_function(message, client, args):
    try:
        guild_config = ch.scope_config(guild=message.guild)
        role = discord.utils.get(message.guild.roles, name=guild_config.get('role-message-'+args[0].emoji))
        if not role:
            raise Exception("Matching role not found for reaction to role-message")
        await message.author.add_roles(role, reason="Self-assigned via reaction to role-message", atomic=False)
        if guild_config[args[0].emoji] in guild_config.get('role-message-autodelete', list()):
            await message.remove_reaction(args[0].emoji, args[1])
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'RMF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')


async def chanlog_function(message, client, args):
    try:
        await message.add_reaction('🔜')
        content = f'Log for {message.guild.name}:{message.channel.name} as of {datetime.utcnow()}\n'
        async for historical_message in message.channel.history(limit=None, oldest_first=True):
            content += f'{historical_message.id} {historical_message.created_at} <{historical_message.author.display_name}:{historical_message.author.id}> {historical_message.system_content}\n'
            for attachment in historical_message.attachments:
                content += f'{historical_message.id} {historical_message.created_at} <{historical_message.author.display_name}:{historical_message.author.id}> {attachment.url}\n'
            for reaction in historical_message.reactions:
                async for user in reaction.users():
                    content += f'Reaction to {historical_message.id}: {reaction.emoji} from {user.display_name} ({user.id})\n'
        link = text_manipulators.fiche_function(content)
        await message.author.send(link)
        await message.remove_reaction('🔜', client.user)
        await message.add_reaction('✅')
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error(f'CLF[{exc_tb.tb_lineno}]: {type(e).__name__} {e}')


def autoload(ch):
    ch.add_command({
        'trigger': ['!roleadd', '!addrole'],
        'function': addrole_function,
        'async': True,
        'admin': 'server',
        'args_num': 1,
        'args_name': [],
        'description': 'Add role (self-assignable by default)'
        })
    ch.add_command({
        'trigger': ['!roledel', '!delrole'],
        'function': delrole_function,
        'async': True,
        'admin': 'server',
        'args_num': 1,
        'args_name': [],
        'description': 'Delete role'
        })
    ch.add_command({
        'trigger': ['!revoke'],
        'function': revokerole_function,
        'async': True,
        'admin': 'server',
        'args_num': 1,
        'args_name': [],
        'description': 'Revoke role `!revoke rolename from me`'
        })
    ch.add_command({
        'trigger': ['!assign'],
        'function': assignrole_function,
        'async': True,
        'admin': 'server',
        'args_num': 1,
        'args_name': [],
        'description': 'Assign role `!assign rolename to me`'
        })
    ch.add_command({
        'trigger': ['!modping'],
        'function': modping_function,
        'async': True,
        'admin': 'server',
        'args_num': 1,
        'args_name': [],
        'description': 'Ping unpingable roles (Admin)'
        })
    ch.add_command({
        'trigger': ['!modreport', '👁‍🗨'],
        'function': modreport_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'Report message to mods. Removed immediately after (if reaction).'
        })
    ch.add_command({
        'trigger': ['!lastactive_channel', '!lastactivity_channel', '!lsc'],
        'function': lastactive_channel_function,
        'async': True,
        'admin': 'server',
        'args_num': 0,
        'long_run': 'author',
        'args_name': [],
        'description': 'List all available channels and time of last message (Admin)'
        })
    ch.add_command({
        'trigger': ['!lastactive_user', '!lastactivity_user', '!lsu'],
        'function': lastactive_user_function,
        'async': True,
        'admin': 'server',
        'args_num': 0,
        'args_name': [],
        'description': 'List all available users and time of last message (Admin)'
        })
    ch.add_command({
        'trigger': ['!kick'],
        'function': kick_user_function,
        'async': True,
        'admin': 'server',
        'args_num': 1,
        'args_name': ['@user', 'reason'],
        'description': 'Kick user from server, and send them a message with the reason.'
        })
    ch.add_command({
        'trigger': ['!lockout'],
        'function': lockout_user_function,
        'async': True,
        'admin': 'server',
        'args_num': 1,
        'long_run': 'author',
        'args_name': ['@user', 'reset|hide'],
        'description': 'Lockout or reset user permissions'
        })
    ch.add_command({
        'trigger': ['!optin'],
        'function': optin_channel_function,
        'async': True,
        'hidden': True,
        'admin': 'global',
        'args_num': 0,
        'args_name': ['#channel'],
        'description': 'Join a channel, no arguments to list available channels.'
        })
    ch.add_command({
        'trigger': ['!part', '!optout'],
        'function': part_channel_function,
        'async': True,
        'args_num': 1,
        'args_name': ['#channel'],
        'description': 'Leave a channel. Cannot be reversed except by admin.'
        })
    ch.add_command({
        'trigger': ['!snooze'],
        'function': snooze_channel_function,
        'async': True,
        'args_num': 0,
        'args_name': ['#channel'],
        'description': 'Leave a channel. Reversed in 24 hours.'
        })
    ch.add_command({
        'trigger': ['!sudo'],
        'function': sudo_function,
        'async': True,
        'admin': 'server',
        'args_num': 0,
        'args_name': [],
        'description': 'Elevate permissions for one command', # by assigning a temporary admin-grant role
        })
    ch.add_command({
        'trigger': ['!chanlog'],
        'function': chanlog_function,
        'async': True,
        'admin': 'server',
        'long_run': 'author',
        'args_num': 0,
        'args_name': [],
        'description': 'Dump channel logs to a pastebin',
        })

    for guild in ch.client.guilds:
        if ch.scope_config(guild=guild).get('role-message'):
            logger.debug(f'Adding role emoji handler for {guild}')
            ch.add_message_reaction_handler(ch.scope_config(guild=guild).get('role-message'), {
                'trigger': [''], # Empty string: a special catch-all trigger
                'function': role_message_function,
                'async': True,
                'args_num': 0,
                'args_name': [],
                'description': 'Assign roles based on emoji for a given message',
                })
