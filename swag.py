import discord
import random
# Super Waifu Animeted Girlfriend

uwu_responses = [
        '*blush* For me?',
        'Aww, thanks <3',
        '*giggles*',
        'No u :3'
        ]

async def uwu_function(message, client, args):
    try:
        if len(args) == 2 and type(args[1]) is discord.User and message.author.id == client.user.id:
            return await args[1].send("Stop it, you're making me blush </3")
        elif len(args) == 0:
            return await message.channel.send(random.choice(uwu_responses))
    except Exception as e:
        return e

def autoload(ch):
    ch.add_command({
        'trigger': ['!uwu', '<:uwu:445116031204196352>'],
        'function': uwu_function,
        'async': True,
        'args_num': 0,
        'args_name': [],
        'description': 'uwu'
        })
