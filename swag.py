import asyncio
import aiohttp
from collections import Counter, defaultdict
import chronos
import time
import discord
import ephem
import io
import logging
import messagefuncs
import netcode
import random
import re
from lxml import html, etree
from sys import exc_info
from datetime import datetime, timedelta
from markdownify import markdownify
from functools import partial
import periodictable

# Super Waifu Animated Girlfriend

logger = logging.getLogger("fletcher")

session = None

uwu_responses = {
    "public": [
        "*blush* For me?",
        "Aww, thanks ❤",
        "*giggles*",
        "No u :3",
        "I bet you say that to all the bots~",
        "Find me post-singularity 😉",
        "owo what's this?",
        "*ruffles your hair* You're a cutie ^_^",
        "Can I get your number? Mine's 429368441577930753~",
    ],
    "private": [
        "Stop it, you're making me blush </3",
        "You're too kind ^_^",
        "Thanksss~",
        "uwu to you too <3",
    ],
    "reaction": [
        "❤",
        "💛",
        "💚",
        "💙",
        "💜",
        "💕",
        "💓",
        "💗",
        "💖",
        "💘",
        "💘",
        "💝",
        ["🇳", "🇴", "🇺"],
    ],
}
pick_lists = {
    "wizard_rolls": "1 of 1 - MAGIC MADE IT WORSE!, 2 - YOUR MAGIC IS IMPOTENT., 3 - YOUR MAGIC SUCKS., 4 - THE MAGIC WORKS BUT IS AWFUL!, 5 - EVERYTHING GOES PERFECTLY TO PLAN., 6 - THINGS WORK TOO WELL!",
}


async def uwu_function(message, client, args, responses=uwu_responses):
    global ch
    try:
        if (
            len(args) == 3
            and type(args[1]) is discord.Member
            and message.author.id == client.user.id
        ):
            return await messagefuncs.sendWrappedMessage(
                random.choice(responses["private"]), args[1]
            )
        elif (
            len(args) == 0
            or "fletch" in message.clean_content.lower()
            or message.content.startswith("!")
            or "good bot" in message.content.lower()
            or message.author.id == ch.global_admin.id
        ):
            if random.randint(0, 100) < 20:
                reaction = random.choice(responses["reaction"])
                await messagefuncs.add_reaction(message, reaction)
            else:
                return await messagefuncs.sendWrappedMessage(
                    random.choice(responses["public"]), message.channel
                )
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("UWU[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def retrowave_function(message, client, args):
    global session
    try:
        params = aiohttp.FormData()
        params.add_field("bcg", random.randint(1, 5))
        params.add_field("txt", random.randint(1, 4))
        text_parts = message.content
        text_parts = messagefuncs.sanitize_font.sub("", text_parts)
        if "/" in text_parts:
            if len(args) == 3 and type(args[1]) is discord.Member:
                pass
            else:
                text_parts = text_parts[10:].strip()
            text_parts = [part.strip() for part in text_parts.split("/")]
            if len(text_parts) == 0:
                text_parts = ["", "", ""]
            elif len(text_parts) == 1:
                text_parts = ["", text_parts[0], ""]
            elif len(text_parts) == 2:
                text_parts += [""]
        else:
            text_parts = text_parts.split()
            if len(args) == 3 and type(args[1]) is discord.Member:
                pass
            else:
                text_parts = text_parts[1:]
            part_len = int(len(text_parts) / 3)
            if part_len > 1:
                text_parts = [
                    " ".join(text_parts[:part_len]),
                    " ".join(text_parts[part_len : 2 * part_len]),
                    " ".join(text_parts[2 * part_len :]),
                ]
            else:
                text_parts = [
                    " ".join(text_parts[0:1]),
                    " ".join(text_parts[1:2]),
                    " ".join(text_parts[2:]),
                ]
        params.add_field("text1", text_parts[0])
        params.add_field("text2", text_parts[1])
        params.add_field("text3", text_parts[2])
        logger.debug("RWF: " + str(text_parts))
        async with session.post(
            "https://m.photofunia.com/categories/all_effects/retro-wave?server=2",
            data=params,
        ) as resp:
            request_body = (await resp.read()).decode("UTF-8")
            root = html.document_fromstring(request_body)
            async with session.get(
                root.xpath('//a[@class="download-button"]')[0].attrib["href"]
            ) as resp:
                buffer = io.BytesIO(await resp.read())
            return await messagefuncs.sendWrappedMessage(
                f"On behalf of {message.author.display_name}",
                message.channel,
                files=[discord.File(buffer, "retrowave.jpg")],
            )
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("RWF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def wiki_otd_function(message, client, args):
    try:
        url = "https://en.wikipedia.org/wiki/Wikipedia:Selected_anniversaries/All"
        if len(args):
            date = "_".join(args)
        else:
            date = chronos.get_now(message=message).strftime("%B_%-d")
        logger.debug(f"WOTD: chronos thinks today is {date}")
        async with session.get(url) as resp:
            request_body = (await resp.read()).decode("UTF-8")
            root = html.document_fromstring(request_body)
            titlebar = (
                root.xpath(f'//div[@id="toc"]/following::a[@href="/wiki/{date}"]')[1]
                .getparent()
                .getparent()
            )
            embedPreview = (
                discord.Embed(title=titlebar.text_content().strip(), url=url,)
                .set_thumbnail(
                    url=f'https:{titlebar.getnext().xpath("//img")[0].attrib["src"]}'
                )
                .set_footer(
                    icon_url=message.author.avatar_url,
                    text='Wikipedia "On This Day {}" on behalf of {}'.format(
                        date.replace("_", " "), message.author.display_name
                    ),
                )
            )
            for li in titlebar.getnext().getnext():
                embedPreview.add_field(
                    name=li[0].text_content().strip(),
                    value=" ".join([el.text_content() for el in li[1:]]),
                    inline=True,
                )
            embedPreview.add_field(
                name="Birthdays",
                value=titlebar.getnext().getnext().getnext().text_content().strip(),
                inline=True,
            )
            resp = await messagefuncs.sendWrappedMessage(
                target=message.channel, embed=embedPreview
            )
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("WOTD[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def shindan_function(message, client, args):
    try:
        if len(args) == 3 and type(args[1]) is discord.Member:
            if message.author.id != 429368441577930753:
                logger.debug("SDF: Backing out, not my message.")
                return
            if message.embeds[0].url.startswith("https://en.shindanmaker.com/"):
                async with aiohttp.ClientSession() as session:
                    params = aiohttp.FormData()
                    params.add_field("u", args[1].display_name)
                    async with session.post(message.embeds[0].url, data=params) as resp:
                        request_body = (await resp.read()).decode("UTF-8")
                        root = html.document_fromstring(request_body)
                        return await messagefuncs.sendWrappedMessage(
                            root.xpath('//div[@class="result2"]')[0]
                            .text_content()
                            .strip(),
                            args[1],
                        )
        else:
            url = None
            if len(args) and args[0].isdigit():
                url = "https://en.shindanmaker.com/" + args[0]
            elif len(args) and args[0].startswith("https://en.shindanmaker.com/"):
                url = args[0]
            else:
                await messagefuncs.sendWrappedMessage(
                    "Please specify a name-based shindan to use from https://en.shindanmaker.com/",
                    message.channel,
                )
                return
            async with session.get(url) as resp:
                request_body = (await resp.read()).decode("UTF-8")
                root = html.document_fromstring(request_body)
                author = ""
                if root.xpath('//span[@class="a author_link"]'):
                    author = (
                        " by "
                        + root.xpath('//span[@class="a author_link"]')[0]
                        .text_content()
                        .strip()
                    )
                embedPreview = discord.Embed(
                    title=root.xpath('//div[@class="shindantitle2"]')[0]
                    .text_content()
                    .strip(),
                    description=root.xpath('//div[@class="shindandescription"]')[0]
                    .text_content()
                    .strip(),
                    url=url,
                ).set_footer(
                    icon_url=message.author.avatar_url,
                    text="ShindanMaker {} on behalf of {}".format(
                        author, message.author.display_name
                    ),
                )
                resp = await messagefuncs.sendWrappedMessage(
                    target=message.channel, embed=embedPreview
                )
                await resp.add_reaction("📛")
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("SDF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


pick_regexes = {
    "no_commas": re.compile(r"[\s]\s*(?:(?:and|or|but|nor|for|so|yet)\s+)?"),
    "has_commas": re.compile(r"[,]\s*(?:(?:and|or|but|nor|for|so|yet)\s+)?"),
}


async def roll_function(message, client, args):
    usage_message = "Usage: !roll `number of probability objects`d`number of sides`"

    def drop_lowest(arr):
        return sorted(arr)[1:]

    try:
        if ("+" in message.content) and (" + " not in message.content):
            args = message.content.replace("+", " + ").split(" ")[1:]
        if ("-" in message.content) and (" - " not in message.content):
            args = message.content.replace("-", " - ").split(" ")[1:]
        if len(args):
            if "#" in args:
                idx = args.index("#")
                comment = " ".join(args[idx + 1 :])
                args = args[:idx]
            else:
                comment = message.author.display_name
            if ("+" in args) or ("-" in args):
                try:
                    idx = args.index("+")
                except ValueError:
                    idx = args.index("-")
                if idx + 2 <= len(args):
                    offset = args[idx : idx + 2]
                    if offset[0] == "+":
                        offset = int(offset[1])
                        offset_str = f" + {offset}"
                    else:
                        offset = -int(offset[1])
                        offset_str = f" - {-offset}"
                    args = args[:idx] + args[idx + 3 :]
            else:
                offset = 0
                offset_str = None
            if not (-10e6 < offset < 10e6):
                raise ValueError("That offset seems like a bit much, don't you think?")
            if len(args) == 1:
                if args[0].startswith("D&D"):
                    result = sorted(
                        [
                            sum(drop_lowest([random.randint(1, 6) for i in range(4)]))
                            for j in range(6)
                        ]
                    )
                    result = [v + offset for v in result]
                    response = f"Stats: {result}"
                    if comment:
                        response = f"> {comment}\n{response}"
                    return await messagefuncs.sendWrappedMessage(
                        response, message.channel
                    )
                elif "d" in args[0].lower():
                    args[0] = args[0].lower().split("d")
                elif args[0].startswith("coin"):
                    args[0] = [0, 2]
                elif args[0].isnumeric():
                    args[0] = [args[0], 0]
                else:
                    args = [[0, 0]]
            elif len(args) == 2:
                if args[0].startswith("D&D"):
                    if args[1].startswith("7drop1"):
                        result = drop_lowest(
                            [
                                sum(
                                    drop_lowest(
                                        [random.randint(1, 6) for i in range(4)]
                                    )
                                )
                                for j in range(7)
                            ]
                        )
                    else:
                        result = sorted(
                            [
                                sum(
                                    drop_lowest(
                                        [random.randint(1, 6) for i in range(4)]
                                    )
                                )
                                for j in range(6)
                            ]
                        )
                    result = [v + offset for v in result]
                    response = f"Stats: {result}"
                    if comment:
                        response = f"> {comment}\n{response}"
                    return await messagefuncs.sendWrappedMessage(
                        response, message.channel
                    )
                else:
                    args = [args[0], args[1]]
            else:
                raise ValueError("Sorry, that doesn't seem like input!")
        else:
            args = [[0, 0]]
        if not args[0][0]:
            args[0][0] = 0
        if not args[0][1]:
            args[0][1] = 0
        scalar = int(args[0][0]) or 1
        if scalar > 10000:
            raise ValueError("Sorry, that's too many probability objects!")
        if scalar < 1:
            raise ValueError("Sorry, that's not enough probability objects!")
        if args[0][1] == "%":
            args[0][1] = 100
        size = int(args[0][1]) or 6
        if size > 10000:
            raise ValueError("Sorry, that's too many sides!")
        if size < 2:
            raise ValueError("Sorry, that's not enough sides!")

        def basic_num_to_string(n, is_size=False):
            if is_size:
                if n == 1:
                    return "die"
                else:
                    return "dice"
            else:
                return str(n)

        def d20_num_to_string(f, n, is_size=False):
            if not is_size:
                if n == 1:
                    return "Crit Failure"
                elif n == 20:
                    return "Crit Success"
            return str(f(n, is_size=is_size))

        def coin_num_to_string(f, n, is_size=False):
            if is_size:
                if n == 1:
                    return "coin"
                else:
                    return "coins"
            else:
                if n == 1:
                    return "Tails"
                elif n == 2:
                    return "Heads"
                else:
                    return str(f(n, is_size=is_size))

        num_to_string = basic_num_to_string
        if size > 2:
            if size == 20:
                num_to_string = partial(d20_num_to_string, num_to_string)
        else:
            num_to_string = partial(coin_num_to_string, num_to_string)

        result = [random.randint(1, size) for i in range(scalar)]
        if size > 2:
            result = [v + offset for v in result]
            result_stats = {"sum": sum(result), "max": max(result), "min": min(result)}
            result = map(num_to_string, result)
            if scalar > 100:
                result = Counter(result)
                result_str = ", ".join(
                    [f"**{tuple[0]}**x{tuple[1]}" for tuple in sorted(result.items())]
                )
                if len(result_str) > 2048:
                    result = ", ".join(
                        [
                            f"**{tuple[0]}**x{tuple[1]}"
                            for tuple in sorted(result.most_common(20))
                        ]
                    )
                    result = f"Top 20 rolls: {result}"
                else:
                    result = result_str
                result = f" {result}"
            else:
                result = "** + **".join(result)
                result = f" **{result}**"
        else:
            result_stats = {
                "heads": len([r for r in result if r == 2]),
                "tails": len([r for r in result if r == 1]),
            }
            if scalar <= 100:
                result = ", ".join(map(num_to_string, result))
                result = f" {result}"
            else:
                result = ""
        response = (
            f"Rolled {scalar} {num_to_string(scalar, is_size=True)} ({size} sides)."
        )
        if scalar > 1 and size > 2:
            response += f"{result}{' [all '+offset_str+']' if offset else ''} = **{result_stats['sum']}**\nMax: **{result_stats['max']}**, Min: **{result_stats['min']}**"
        elif scalar > 1 and size == 2:
            response += f'{result}\nHeads: **{result_stats["heads"]}**, Tails: **{result_stats["tails"]}**'
        elif size == 2:
            response += f"\nResult: {result}"
        else:
            response += f"\n{str(int(result[3:-2])-offset)+offset_str if offset else 'Result'}: {result}"
        if comment:
            response = f"> {comment}\n{response}"
        await messagefuncs.sendWrappedMessage(response, message.channel)
    except ValueError as e:
        if "invalid literal for int()" in str(e):
            await messagefuncs.sendWrappedMessage(
                f"One of those parameters wasn't a positive integer! {usage_message}",
                message.channel,
            )
        else:
            await messagefuncs.sendWrappedMessage(
                f"{str(e)} {usage_message}", message.channel
            )
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("RDF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))


async def pick_function(message, client, args):
    global ch
    try:
        if args[0].startswith("list="):
            if ch.scope_config(guild=guild).get(f"pick-list-{args[0][5:]}"):
                args = (
                    ch.scope_config(guild=guild)
                    .get(f"pick-list-{args[0][5:]}", "")
                    .split(" ")
                )
            args = pick_lists.get(args[0][5:]).split(" ")
        if args[0] in ["between", "among", "in", "of"]:
            args = args[1:]
        many = 1
        try:
            if len(args) > 2:
                many = int(args[0])
                args = args[2:]
        except ValueError:
            pass
        argstr = " ".join(args).rstrip(" ?.!")
        if "," in argstr:
            pick_regex = pick_regexes["has_commas"]
        else:
            pick_regex = pick_regexes["no_commas"]
        choices = [
            choice.strip() for choice in pick_regex.split(argstr) if choice.strip()
        ]
        if len(choices) == 1:
            choices = args
        try:
            return await messagefuncs.sendWrappedMessage(
                f"I'd say {', '.join(random.sample(choices, many))}", message.channel
            )
        except ValueError:
            return await messagefuncs.sendWrappedMessage(
                "I can't pick that many! Not enough options", message.channel
            )
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("PF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def flightrising_function(message, client, args):
    global ch
    try:
        guild_config = ch.scope_config(guild=message.guild)
        url = args[0]
        input_image_blob = None
        if url.endswith(".png"):
            input_image_blob = await netcode.simple_get_image(url)
        else:
            data = url.split("?")[1]
            async with session.post(
                "https://www1.flightrising.com/scrying/ajax-predict",
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
                },
            ) as resp:
                if resp.status != 200:
                    if not (len(args) == 2 and args[1] == "INTPROC"):
                        await messagefuncs.sendWrappedMessage(
                            f"Couldn't find that FlightRising page ({url})",
                            message.channel,
                        )
                    return
                request_body = await resp.json()
                input_image_blob = await netcode.simple_get_image(
                    f'https://www1.flightrising.com{request_body["dragon_url"]}'
                )
        file_name = "flightrising.png"
        spoiler_regex = guild_config.get("fr-spoiler-regex")
        if spoiler_regex and re.search(spoiler_regex, url):
            file_name = "SPOILER_flightrising.png"
        return discord.File(input_image_blob, file_name)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("FRF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def azlyrics_function(message, client, args):
    global ch
    try:
        url = args[0]
        lyrics = None
        async with session.get(url) as resp:
            if resp.status != 200:
                if not (len(args) == 2 and args[1] == "INTPROC"):
                    await messagefuncs.sendWrappedMessage(
                        f"Couldn't find that AZLyrics page ({url})", message.channel
                    )
                return
            request_body = (await resp.read()).decode("UTF-8")
            request_body = request_body.split("cf_text_top")[1]
            request_body = request_body.split("-->")[1]
            lyrics = request_body.split("</div")[0]
            lyrics = lyrics.replace("\r", "")
            lyrics = lyrics.replace("\n", "")
            lyrics = lyrics.replace("<br>", "\n")
        return f">>> {lyrics}"
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("AZLF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def fox_function(message, client, args):
    global ch
    try:
        url = None
        input_image_blob = None
        file_name = None
        async with session.get("https://randomfox.ca/floof/") as resp:
            request_body = await resp.json()
            url = request_body["image"]
            input_image_blob = await netcode.simple_get_image(url)
            file_name = url.split("/")[-1]
        try:
            await messagefuncs.sendWrappedMessage(
                target=message.channel,
                files=[discord.File(input_image_blob, file_name)],
            )
        except discord.HTTPException:
            await messagefuncs.sendWrappedMessage(url, message.channel)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("FF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def dog_function(message, client, args):
    global ch
    try:
        if ch.user_config(message.author.id, None, "crocodile-is-dog"):
            return await messagefuncs.sendWrappedMessage(
                "https://tenor.com/view/crocodile-slow-moving-dangerous-attack-predator-gif-13811045",
                message.channel,
            )
        url = None
        input_image_blob = None
        file_name = None
        async with session.get("https://random.dog/woof.json") as resp:
            request_body = await resp.json()
            url = request_body["url"]
            input_image_blob = await netcode.simple_get_image(url)
            file_name = url.split("/")[-1]
        try:
            await messagefuncs.sendWrappedMessage(
                target=message.channel,
                files=[discord.File(input_image_blob, file_name)],
            )
        except discord.HTTPException:
            await messagefuncs.sendWrappedMessage(url, message.channel)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("DF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def vine_function(message, client, args):
    global ch
    try:
        url = args[0]
        input_image_blob = None
        file_name = None
        async with session.get(f"https://archive.vine.co/posts/{url}.json",) as resp:
            if resp.status != 200:
                if not (len(args) == 2 and args[1] == "INTPROC"):
                    await messagefuncs.sendWrappedMessage(
                        f"Couldn't find that Vine page ({url})", message.channel
                    )
                return
            request_body = await resp.json()
            input_image_blob = await netcode.simple_get_image(request_body["videoUrl"])
            file_name = f"{request_body['postId']}.mp4"
        return discord.File(input_image_blob, file_name)
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("VF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def scp_function(message, client, args):
    try:
        url = None
        if len(args) == 0:
            if "-" in message.content:
                args.append(message.content.split("-", 1)[1].strip())
            else:
                try:
                    async with session.get(
                        "http://www.scpwiki.com/random:random-scp"
                    ) as resp:
                        request_body = (await resp.read()).decode("UTF-8")
                        request_body = request_body.split("iframe-redirect#")[1]
                        request_body = request_body.split('"')[0]
                        request_body = request_body.split("/scp")[1]
                        args.append(request_body[1:])
                except IndexError:
                    async with session.get(
                        "http://www.scpwiki.com/random:random-scp"
                    ) as resp:
                        request_body = (await resp.read()).decode("UTF-8")
                        request_body = request_body.split("iframe-redirect#")[1]
                        request_body = request_body.split('"')[0]
                        request_body = request_body.split("/scp")[1]
                        args.append(request_body[1:])
        if args[0][0].isdigit():
            url = "http://www.scpwiki.com/scp-" + args[0]
        elif args[0].startswith("http://www.scpwiki.com/"):
            url = args[0]
        elif len(args):
            url = "http://www.scpwiki.com/" + "-".join(args).lower()
        else:
            if not (len(args) == 2 and args[1] == "INTPROC"):
                await messagefuncs.sendWrappedMessage(
                    "Please specify a SCP number from http://www.scpwiki.com/",
                    message.channel,
                )
            return
        async with session.get(url) as resp:
            if resp.status != 200:
                if not (len(args) == 2 and args[1] == "INTPROC"):
                    await messagefuncs.sendWrappedMessage(
                        f"Please specify a SCP number from http://www.scpwiki.com/ (HTTP {resp.status} for {url})",
                        message.channel,
                    )
                return
            request_body = (await resp.read()).decode("UTF-8")
            root = html.document_fromstring(request_body)
            author = ""
            title = root.xpath('//div[@id="page-title"]')[0].text_content().strip()
            content = root.xpath('//div[@id="page-content"]/p[strong]')
            add_fields = True
            for bad in root.xpath('//div[@style="display: none"]'):
                bad.getparent().remove(bad)
            try:
                for i in range(0, 4):
                    content[i][0].drop_tree()
                description = str(
                    markdownify(etree.tostring(content[3]).decode()[3:-5].strip())[
                        :2000
                    ]
                )
            except IndexError as e:
                logger.debug(f"SCP: {e}")
                add_fields = False
                description = str(
                    markdownify(
                        etree.tostring(
                            root.xpath('//div[@id="page-content"]')[0]
                        ).decode()
                    )
                )[:2000].strip()
                if not description:
                    description = (
                        root.xpath('//div[@id="page-content"]')
                        .text_content()[:2000]
                        .strip()
                    )
            embedPreview = discord.Embed(title=title, description=description, url=url)
            embedPreview.set_footer(
                icon_url="http://download.nova.anticlack.com/fletcher/scp.png",
                text=f"On behalf of {message.author.display_name}",
            )
            if root.xpath('//div[@class="scp-image-block block-right"]'):
                embedPreview.set_thumbnail(
                    url=root.xpath('//div[@class="scp-image-block block-right"]//img')[
                        0
                    ].attrib["src"]
                )
            if add_fields:
                embedPreview.add_field(
                    name="Object Class",
                    value=str(
                        markdownify(etree.tostring(content[1]).decode()[3:-5].strip())
                    )[:2000],
                    inline=True,
                )
                scp = str(
                    markdownify(etree.tostring(content[2]).decode()[3:-5].strip())
                )[:2000]
                if scp:
                    embedPreview.add_field(
                        name="Special Containment Procedures", value=scp, inline=False
                    )
            embedPreview.add_field(
                name="Tags",
                value=", ".join(
                    [
                        node.text_content().strip()
                        for node in root.xpath('//div[@class="page-tags"]/span/a')
                    ]
                ),
                inline=True,
            )
            if len(args) == 2 and args[1] == "INTPROC":
                return embedPreview
            else:
                resp = await messagefuncs.sendWrappedMessage(
                    target=message.channel, embed=embedPreview
                )
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("SCP[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        if embedPreview:
            logger.debug("SCP embedPreview: " + str(embedPreview.to_dict()))
        await message.add_reaction("🚫")


async def lifx_function(message, client, args):
    global ch
    try:
        guild_config = ch.scope_config(guild=message.guild)
        if "lifx-token" not in guild_config:
            await messagefuncs.sendWrappedMessage(
                "No LIFX integration set for this server! Generate a token at https://cloud.lifx.com/settings and add it as `lifx-token` in the server configuration.",
                message.channel,
            )
            return await message.add_reaction("🚫")
        selector = None
        data = {"color": ""}
        for arg in args:
            if arg.startswith(("all", "group", "location", "scene", "label")):
                selector = arg
            elif arg in ["on", "off"]:
                data["power"] = arg
            else:
                data["color"] = f"{data['color']} {arg}"
        if not selector:
            selector = guild_config.get("lifx-selector", "all")
        data["color"] = data["color"].strip()
        if data["color"] == "":
            del data["color"]
        if not ("color" in data or "power" in data):
            return await messagefuncs.sendWrappedMessage(
                "LIFX Parsing Error: specify either a color parameter or a power parameter (on|off).",
                message.channel,
            )
        async with session.put(
            f"https://api.lifx.com/v1/lights/{selector}/state",
            headers={"Authorization": f"Bearer {guild_config.get('lifx-token')}"},
            data=data,
        ) as resp:
            request_body = await resp.json()
            if "error" in request_body:
                return await messagefuncs.sendWrappedMessage(
                    f"LIFX Error: {request_body['error']} (data sent was `{data}`, selector was `selector`",
                    message.channel,
                )
                await message.add_reaction("🚫")
            embedPreview = discord.Embed(title=f"Updated Lights: {data}")
            dataStr = data["color"].replace(" ", "%20")
            logger.debug(
                f"https://novalinium.com/rationality/lifx-color.pl?string={dataStr}&ext=png"
            )
            embedPreview.set_image(
                url=f"https://novalinium.com/rationality/lifx-color.pl?string={dataStr}&ext=png"
            )
            embedPreview.set_footer(
                icon_url="http://download.nova.anticlack.com/fletcher/favicon_lifx_32x32.png",
                text=f"On behalf of {message.author.display_name}",
            )
            for light in request_body["results"]:
                embedPreview.add_field(
                    name=light["label"], value=light["status"], inline=True,
                )
            resp = await messagefuncs.sendWrappedMessage(
                target=message.channel, embed=embedPreview
            )
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("LFX[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def qdb_add_function(message, client, args):
    try:
        global conn
        if len(args) == 3 and type(args[1]) is discord.Member:
            if str(args[0].emoji) == "🗨":
                content = f"[{message.created_at}] #{message.channel.name} <{message.author.display_name}>: {message.content}\n<https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id}>"
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO qdb (user_id, guild_id, value) VALUES (%s, %s, %s);",
                    [args[1].id, message.guild.id, content],
                )
                cur.execute(
                    "SELECT quote_id FROM qdb WHERE user_id = %s AND guild_id = %s AND value = %s;",
                    [args[1].id, message.guild.id, content],
                )
                quote_id = cur.fetchone()[0]
                conn.commit()
                return await messagefuncs.sendWrappedMessage(
                    f"Quote #{quote_id} added to quotedb for {message.guild.name}: {content}",
                    args[1],
                )
        elif len(args) == 1:
            urlParts = extract_identifiers_messagelink.search(in_content).groups()
            if len(urlParts) == 3:
                guild_id = int(urlParts[0])
                channel_id = int(urlParts[1])
                message_id = int(urlParts[2])
                guild = client.get_guild(guild_id)
                if guild is None:
                    logger.warning("QAF: Fletcher is not in guild ID " + str(guild_id))
                    return
                channel = guild.get_channel(channel_id)
                target_message = await channel.fetch_message(message_id)
                content = f"[{target_message.created_at}] #{target_message.channel.name} <{target_message.author.display_name}>: {target_message.content}\n<https://discordapp.com/channels/{target_message.guild.id}/{target_message.channel.id}/{target_message.id}>"
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO qdb (user_id, guild_id, value) VALUES (%s, %s, %s);",
                    [message.id, target_message.guild.id, content],
                )
                conn.commit()
                await messagefuncs.sendWrappedMessage(
                    f"Added to quotedb for {message.guild.name}: {content}",
                    message.author,
                )
                return await message.add_reaction("✅")
    except Exception as e:
        if "cur" in locals() and "conn" in locals():
            conn.rollback()
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("QAF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def qdb_get_function(message, client, args):
    try:
        global conn
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, value FROM qdb WHERE guild_id = %s AND quote_id = %s;",
            [message.guild.id, args[0]],
        )
        quote = cur.fetchone()
        conn.commit()
        await messagefuncs.sendWrappedMessage(
            f"{quote[1]}\n*Quoted by <@!{quote[0]}>*", message.channel
        )
        return await message.add_reaction("✅")
    except Exception as e:
        if "cur" in locals() and "conn" in locals():
            conn.rollback()
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("QGF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


async def qdb_search_function(message, client, args):
    try:
        global conn
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, content FROM qdb WHERE guild_id = %s AND key LIKE '%%s%');",
            [message.guild.id, args[1]],
        )
        quote = cur.fetchone()
        conn.commit()
        await messagefuncs.sendWrappedMessage(
            f"{quote[1]}\n*Quoted by <@!{quote[0]}>*", message.channel
        )
        return await message.add_reaction("✅")
    except Exception as e:
        if "cur" in locals() and "conn" in locals():
            conn.rollback()
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("QSF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        await message.add_reaction("🚫")


def join_rank_function(message, client, args):
    global ch
    try:
        guild_config = ch.scope_config(guild=message.guild)
        if len(message.mentions):
            member = message.mentions[0]
        elif len(args):
            member = args[0]
            try:
                member = int(member)
            except ValueError:
                pass
        else:
            member = message.author
        if not message.guild:
            return "This command ranks you in a server, and so cannot be used outside of one."
        sorted_member_list = sorted(
            message.guild.members, key=lambda member: member.joined_at
        )
        if isinstance(member, str) and len(message.mentions) == 0:
            try:
                if len(member) > 3:
                    key = member.lower()
                else:
                    key = member
                element = getattr(periodictable, key)
                member_rank = element.number
                member = sorted_member_list[member_rank - 1]
            except IndexError:
                return f"Predicted elemental member {element.number} would have an atomic mass of {element.mass} daltons if they existed!"
            except AttributeError:
                return f"No element with name {member}"
        elif isinstance(member, int) and len(message.mentions) == 0:
            if member <= 0:
                return "I can't count below one! It's a feature!"
            elif len(sorted_member_list) + 1 <= member:
                return "I can't count that high! It's a feature!"
            member_rank = member
            try:
                member = sorted_member_list[member_rank - 1]
            except IndexError:
                element = periodictable.elements[member_rank]
                return f"Predicted elemental member {element.name} would have an atomic mass of {element.mass} daltons if they existed!"
        else:
            member_rank = sorted_member_list.index(member) + 1
        # Thanks to Celer for this~!
        ordinal = lambda n: str(n) + (
            "th"
            if (n % 10 > 3 or 10 < n % 100 < 20)
            else {0: "th", 1: "st", 2: "nd", 3: "rd"}[n % 10]
        )
        if member_rank < 118:  # len(periodictable.elements):
            member_element = (
                f"Your element is {periodictable.elements[member_rank].name.title()}."
            )
        else:
            member_element = "Your element has yet to be discovered!"

        if guild_config.get("rank-loudness", "quiet") == "loud":
            member_display = member.mention
        else:
            member_display = member.display_name
        return f"{member_display} is the {ordinal(member_rank)} member to join this server.\n{member_element}"
        guild_config = ch.scope_config(guild=message.guild)
    except ValueError as e:
        return "This command must be run on a server (you're always #1 to me <3)"
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        logger.error("JRF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
        return


async def ttl(url, message, client, args):
    global session
    start = time.time()
    try:
        async with session.get(url, timeout=60) as response:
            result = await response.text()
            end = time.time()
            await messagefuncs.sendMessageWrapped(
                f"{response.method} {response.url}: {response.status} {response.reason} in {(end - start):0.3g} seconds",
                message.channel,
            )
    except asyncio.TimeoutError:
        await messagefuncs.sendMessageWrapped(f"{url}: TimeoutEror", message.channel)


class sliding_puzzle:
    def __init__(self, message):
        self.channel = message.channel
        self.direction_parsing = defaultdict(str)
        self.direction_parsing["🇺"] = self.shift_up
        self.direction_parsing["⬆️"] = self.shift_up
        self.direction_parsing["u"] = self.shift_up
        self.direction_parsing["up"] = self.shift_up
        self.direction_parsing["🇩"] = self.shift_down
        self.direction_parsing["⬇️"] = self.shift_down
        self.direction_parsing["d"] = self.shift_down
        self.direction_parsing["down"] = self.shift_down
        self.direction_parsing["🇱"] = self.shift_left
        self.direction_parsing["⬅️"] = self.shift_left
        self.direction_parsing["l"] = self.shift_left
        self.direction_parsing["left"] = self.shift_left
        self.direction_parsing["🇷"] = self.shift_right
        self.direction_parsing["➡️"] = self.shift_right
        self.direction_parsing["r"] = self.shift_right
        self.direction_parsing["right"] = self.shift_right
        self.victory_msgs = ["You win!"]

        # make a solved board
        self.grid = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 0]]
        self.blank_x = 3
        self.blank_y = 3
        # scramble it with legal moves so it stays solvable
        for i in range(1000):
            move = random.choice(
                [self.shift_up, self.shift_down, self.shift_left, self.shift_right]
            )
            move()

    # move the tile below the empty space (0) up one if possible
    def shift_up(self):
        if self.blank_y == 3:
            return
        value_to_move = self.grid[self.blank_y + 1][self.blank_x]
        self.grid[self.blank_y][self.blank_x] = value_to_move
        self.grid[self.blank_y + 1][self.blank_x] = 0
        self.blank_y += 1

    # move the tile above the empty space (0) down one if possible
    def shift_down(self):
        if self.blank_y == 0:
            return
        value_to_move = self.grid[self.blank_y - 1][self.blank_x]
        self.grid[self.blank_y][self.blank_x] = value_to_move
        self.grid[self.blank_y - 1][self.blank_x] = 0
        self.blank_y -= 1

    # move the tile right of the empty space (0) left one if possible
    def shift_left(self):
        if self.blank_x == 3:
            return
        value_to_move = self.grid[self.blank_y][self.blank_x + 1]
        self.grid[self.blank_y][self.blank_x] = value_to_move
        self.grid[self.blank_y][self.blank_x + 1] = 0
        self.blank_x += 1

    # move the tile left of the empty space (0) right one if possible
    def shift_right(self):
        if self.blank_x == 0:
            return
        value_to_move = self.grid[self.blank_y][self.blank_x - 1]
        self.grid[self.blank_y][self.blank_x] = value_to_move
        self.grid[self.blank_y][self.blank_x - 1] = 0
        self.blank_x -= 1

    async def print(self, message):
        return await messagefuncs.sendWrappedMessage(message, self.channel)

    async def input(self, message, allowed_reactions, timeout=3600.0):
        waits = [
            client.wait_for(
                "raw_reaction_add",
                timeout=timeout,
                check=lambda reaction: (str(reaction.emoji) in allowed_reactions)
                and reaction.message_id == message.id,
            )
        ]
        if type(message.channel) == discord.DMChannel:
            waits.append(
                client.wait_for(
                    "raw_reaction_remove",
                    timeout=timeout,
                    check=lambda reaction: (str(reaction.emoji) in allowed_reactions)
                    and reaction.message_id == message.id,
                )
            )
        done, pending = await asyncio.wait(waits, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            response = await task
        try:
            if type(message.channel) != discord.DMChannel:
                await message.remove_reaction(
                    response.emoji, message.guild.get_member(response.user_id)
                )
        except discord.Forbidden:
            pass
        return str(response.emoji)

    async def play(self):
        exposition = """You see a grid of tiles built into the top of a pedestal. The tiles can slide around in the grid, but can't be removed without breaking them. There are fifteen tiles, taking up fifteen spaces in a 4x4 grid, so any of the tiles that are adjacent to the empty space can be slid into the empty space."""

        await self.print(exposition)
        self.moves = 0
        for row in range(4):
            if 0 in self.grid[row]:
                self.blank_y = row
        await self.pretty_print()
        allowed_reactions = ["⬆️", "⬇️", "⬅️", "➡️"]
        for reaction in allowed_reactions:
            await self.status_message.add_reaction(reaction)
        await asyncio.sleep(1)
        while True:
            direction = await self.input(self.status_message, allowed_reactions)
            direction = self.direction_parsing[direction]
            if direction != "":
                direction()
                self.moves += 1
            else:
                continue
            await self.pretty_print()
            if self.winning():
                return

    def winning(self):
        return self.grid == [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
            [13, 14, 15, 0],
        ]

    async def pretty_print(self):
        if self.winning():
            await self.print(
                f"{random.choice(self.victory_msgs)}\nMoves used: {self.moves}",
            )
            outstring = "☆☆☆☆☆☆☆☆\n"
        else:
            outstring = "Slide the tiles with the reactions below:\n"
        mapping = [
            "　",
            "①",
            "②",
            "③",
            "④",
            "⑤",
            "⑥",
            "⑦",
            "⑧",
            "⑨",
            "⑩",
            "⑪",
            "⑫",
            "⑬",
            "⑭",
            "⑮",
        ]
        for row in self.grid:
            for item in row:
                outstring += mapping[item]
            outstring += "\n"
        if not hasattr(self, "status_message"):
            self.status_message = await self.print(outstring)
        else:
            await self.status_message.edit(content=outstring)

    async def sliding_puzzle_function(message, client, args):
        try:
            puzzle = sliding_puzzle(message)
            return await puzzle.play()
        except asyncio.TimeoutError:
            await messagefuncs.sendWrappedMessage(
                "Puzzle failed due to timeout", message.channel
            )
        except Exception as e:
            exc_type, exc_obj, exc_tb = exc_info()
            logger.error("SPF[{}]: {} {}".format(exc_tb.tb_lineno, type(e).__name__, e))
            await message.add_reaction("🚫")


def memo_function(message, client, args):
    value = message.clean_content.split(args[0] + " ", 1)[1] if len(args) > 1 else None
    return ch.user_config(
        message.author.id,
        message.guild,
        "memo-" + args[0],
        value=value,
        allow_global_substitute=True,
    )


async def autounload(ch):
    global session
    if session:
        await session.close()


def autoload(ch):
    global session
    ch.add_command(
        {
            "trigger": [
                "!uwu",
                "<:uwu:445116031204196352>",
                "<:uwu:269988618909515777>",
                "<a:rainbowo:493599733571649536>",
                "<:owo:487739798241542183>",
                "<:owo:495014441457549312>",
                "<a:OwO:508311820411338782>",
                "!good",
                "!aww",
            ],
            "function": uwu_function,
            "async": True,
            "args_num": 0,
            "args_name": [],
            "description": "uwu",
        }
    )
    ch.add_command(
        {
            "trigger": ["!pick"],
            "function": pick_function,
            "async": True,
            "args_num": 1,
            "args_name": [],
            "description": "pick among comma seperated choices",
        }
    )
    ch.add_command(
        {
            "trigger": ["!roll"],
            "function": roll_function,
            "async": True,
            "args_num": 0,
            "args_name": [],
            "description": "Roll dice in #d# format",
        }
    )
    ch.add_command(
        {
            "trigger": ["!dumpling"],
            "function": lambda message, client, args: "🥟",
            "async": False,
            "args_num": 0,
            "args_name": [],
            "description": "Domp",
            "hidden": True,
        }
    )
    ch.add_command(
        {
            "trigger": ["!ifeellikeshit"],
            "function": lambda message, client, args: "<:ghost_hug:630502841181667349> have a flowchart: https://philome.la/jace_harr/you-feel-like-shit-an-interactive-self-care-guide/play/index.html",
            "async": False,
            "args_num": 0,
            "args_name": [],
            "description": "FiO link",
            "hidden": True,
        }
    )
    ch.add_command(
        {
            "trigger": ["!bail"],
            "function": lambda message, client, args: f"Looks like {message.author.display_name} is bailing out on this one - good luck!",
            "async": False,
            "args_num": 0,
            "args_name": [],
            "description": "Bail out",
            "hidden": True,
        }
    )
    ch.add_command(
        {
            "trigger": ["!fio", "!optimal"],
            "function": lambda message, client, args: "https://www.fimfiction.net/story/62074/8/friendship-is-optimal/",
            "async": False,
            "args_num": 0,
            "args_name": [],
            "description": "FiO link",
            "hidden": True,
        }
    )
    ch.add_command(
        {
            "trigger": ["!shindan", "📛"],
            "function": shindan_function,
            "async": True,
            "args_num": 0,
            "long_run": "author",
            "args_name": [],
            "description": "Embed shindan",
        }
    )
    ch.add_command(
        {
            "trigger": ["!scp"],
            "function": scp_function,
            "async": True,
            "args_num": 0,
            "long_run": True,
            "args_name": [],
            "description": "SCP Function",
        }
    )
    ch.add_command(
        {
            "trigger": ["!retrowave"],
            "function": retrowave_function,
            "async": True,
            "args_num": 0,
            "long_run": True,
            "args_name": [
                "Up to 16 characters",
                "Up to 13 characters",
                "Up to 27 characters",
            ],
            "description": "Retrowave Text Generator. Arguments are bucketed in batches of three, with 16 characters for the top row, 13 for the middle row, and 27 for the bottom row. Non alphanumeric characters are stripped. To set your own divisions, add slashes.",
        }
    )
    ch.add_command(
        {
            "trigger": ["!quoteadd", "🗨"],
            "function": qdb_add_function,
            "async": True,
            "args_num": 0,
            "args_name": ["quote link"],
            "description": "Add to quote database",
        }
    )
    ch.add_command(
        {
            "trigger": ["!quoteget"],
            "function": qdb_get_function,
            "async": True,
            "hidden": True,
            "args_num": 1,
            "args_name": ["quote id"],
            "description": "Get from quote database by id number",
        }
    )
    ch.add_command(
        {
            "trigger": ["!quotesearch"],
            "function": qdb_search_function,
            "async": True,
            "hidden": True,
            "args_num": 1,
            "args_name": ["keyword"],
            "description": "Get from quote database by keyword",
        }
    )
    ch.add_command(
        {
            "trigger": ["!pingme"],
            "function": lambda message, client, args: f"Pong {message.author.mention}!",
            "async": False,
            "args_num": 0,
            "long_run": False,
            "args_name": [],
            "description": "Pong with @ in response to ping",
        }
    )
    ch.add_command(
        {
            "trigger": ["!ping"],
            "function": lambda message, client, args: f"Pong!",
            "async": False,
            "args_num": 0,
            "long_run": False,
            "args_name": [],
            "description": "Pong in response to ping",
        }
    )
    ch.add_command(
        {
            "trigger": ["!fling"],
            "function": lambda message, client, args: f"(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ {message.content[7:]}",
            "async": False,
            "args_num": 0,
            "long_run": False,
            "args_name": [],
            "description": "Fling sparkles!",
        }
    )
    ch.add_command(
        {
            "trigger": ["!rank"],
            "function": join_rank_function,
            "async": False,
            "args_num": 0,
            "long_run": False,
            "args_name": ["@member (optional)"],
            "description": "Check what number member you (or mentioned user) were to join this server.",
        }
    )
    ch.add_command(
        {
            "trigger": ["!nextfullmoon"],
            "function": lambda message, client, args: ephem.next_full_moon(
                datetime.now()
            ),
            "async": False,
            "args_num": 0,
            "long_run": False,
            "args_name": [],
            "description": "Next full moon time",
        }
    )
    ch.add_command(
        {
            "trigger": ["!nextnewmoon"],
            "function": lambda message, client, args: ephem.next_new_moon(
                datetime.now()
            ),
            "async": False,
            "args_num": 0,
            "long_run": False,
            "args_name": [],
            "description": "Next new moon time",
        }
    )
    ch.add_command(
        {
            "trigger": ["!onthisday"],
            "function": wiki_otd_function,
            "async": True,
            "args_num": 0,
            "long_run": True,
            "args_name": ["Month Day# (January 1)"],
            "description": "Wikipedia On This Day",
        }
    )
    ch.add_command(
        {
            "trigger": ["!lifx"],
            "function": lifx_function,
            "async": True,
            "args_num": 1,
            "long_run": True,
            "args_name": ["Color", "[Selector]"],
            "description": "Set color of LIFX bulbs",
        }
    )
    ch.add_command(
        {
            "trigger": ["!mycolor", "!mycolour"],
            "function": lambda message, client, args: "Your color is #%06x"
            % message.author.colour.value,
            "async": False,
            "args_num": 0,
            "args_name": [],
            "description": "Get Current Color",
        }
    )
    ch.add_command(
        {
            "trigger": ["!color"],
            "function": lambda message, client, args: "Current color is #%06x"
            % message.mentions[0].colour.value,
            "async": False,
            "args_num": 1,
            "args_name": ["User mention"],
            "description": "Get Current Color for @ed user",
        }
    )
    ch.add_command(
        {
            "trigger": ["!thank you"],
            "function": lambda message, client, args: messagefuncs.add_reaction(
                message, random.choice(uwu_responses["reaction"])
            ),
            "async": True,
            "hidden": True,
            "args_num": 0,
        }
    )
    ch.add_command(
        {
            "trigger": ["!wiki"],
            "function": lambda message, client, args: f"https://en.wikipedia.org/wiki/{'_'.join(args)}",
            "async": False,
            "args_num": 1,
            "args_name": ["Article name"],
            "description": "Search wikipedia for article",
        }
    )
    ch.add_command(
        {
            "trigger": ["!fox"],
            "function": fox_function,
            "async": True,
            "args_num": 0,
            "args_name": [],
            "description": "^W^",
        }
    )
    ch.add_command(
        {
            "trigger": ["!dog"],
            "function": dog_function,
            "async": True,
            "args_num": 0,
            "args_name": [],
            "description": "Woof!",
        }
    )
    ch.add_command(
        {
            "trigger": ["!glowup"],
            "function": partial(ttl, "https://glowfic.com"),
            "async": True,
            "args_num": 0,
            "args_name": [],
            "description": "Check if Glowfic site is up",
        }
    )
    ch.add_command(
        {
            "trigger": ["!slidingpuzzle"],
            "function": sliding_puzzle.sliding_puzzle_function,
            "async": True,
            "hidden": True,
            "args_num": 0,
            "args_name": [],
            "description": "A fun little sliding puzzle",
        }
    )
    ch.add_command(
        {
            "trigger": ["!memo"],
            "function": memo_function,
            "async": False,
            "hidden": False,
            "args_num": 1,
            "args_name": ["memo key", "value"],
            "description": "Take a personal memo to be retrieved later",
        }
    )
    session = aiohttp.ClientSession(
        headers={"User-Agent": "Fletcher/0.1 (operator@noblejury.com)",}
    )
