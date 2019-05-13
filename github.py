import aiohttp
import discord
import os
from sys import exc_info

base_url = 'https://api.github.com'

async def github_report_function(message, client, args):
    try:
        if "Guild "+str(message.guild.id) in config:
            scoped_config = config["Guild "+str(message.guild.id)]
        else:
            raise Exception("No guild-specific configuration for moderation on guild "+str(message.guild))
        post_url = '/repos/'+scoped_config['github-repo']+'/issues'
        async with aiohttp.ClientSession(headers={'Authorization': 'token '+config['github']['personalAccessToken']}) as session:
            url = base_url + post_url
            content = "\n".join(message.content.splitlines(True)[1:])
            title = " ".join(message.content.splitlines()[0].split(" ")[1:])
            async with session.post(url, json={'title': title, 'body': content}) as response:
                response_body = await response.json()
            await message.channel.send(embed=discord.Embed(title="#"+str(response_body['number'])+": "+response_body['title'], url=response_body['html_url']).add_field(
                name="Status", value=response_body['state'].capitalize(), inline=True).add_field(
                name="Content", value=response_body['body']).set_footer(
                icon_url="https://download.nova.anticlack.com/fletcher/github.favicon.png",text="On behalf of {}".format(message.author.display_name)))
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        print("GRF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))

def autoload(ch):
    ch.add_command({
        'trigger': ['!ghreport'],
        'function': github_report_function,
        'async': True, 'args_num': 1, 'args_name': [], 'description': 'GitHub Issue Reporter'
        })
