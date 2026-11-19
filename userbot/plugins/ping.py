# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# CatUserBot #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Copyright (C) 2020-2023 by TgCatUB@Github.
#
# This file is part of: https://github.com/TgCatUB/catuserbot
# and is released under the "GNU v3.0 License Agreement".
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import asyncio
import os
import random
import time
from datetime import datetime

import requests
from telethon import Button
from telethon.errors.rpcerrorlist import (
    MediaEmptyError,
    WebpageCurlFailedError,
    WebpageMediaEmptyError,
)

from ..Config import Config
from ..core.managers import edit_or_reply
from ..helpers.functions import get_readable_time
from ..sql_helper.globals import gvarstatus
from . import StartTime, catub, mention, reply_id

plugin_category = "tools"

temp_ = "◆ **PONG!**"
temp = (
    "◆ **CAT PING REPORT**\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "◉ **Latency:** `{ping} ms`\n"
    "◉ **Uptime:** `{uptime}`\n"
    "◉ **Status:** `ONLINE`\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "✓ **CAT Userbot is alive and responding.**"
)
if Config.BADCAT:
    temp_ = "__**☞ PONG!**__"
    temp = (
        "__**☞ CAT PING REPORT**__\n"
        "➥ **Latency:** `{ping} ms`\n"
        "➥ **Uptime:** `{uptime}`\n"
        "➥ __**Bot of **__{mention}"
    )


@catub.cat_cmd(
    pattern="ping( -a|$)",
    command=("ping", plugin_category),
    info={
        "header": "Check the response latency of your userbot",
        "flags": {"-a": "average ping"},
        "usage": ["{tr}ping", "{tr}ping -a"],
    },
)
async def _(event):
    "Check CAT Userbot response latency."
    flag = event.pattern_match.group(1)
    reply_to_id = await reply_id(event)
    uptime = await get_readable_time(time.time() - StartTime)
    start = datetime.now()

    # Preserve the existing average-ping mode and its text-only response.
    if flag == " -a":
        catevent = await edit_or_reply(event, "`!....`")
        await asyncio.sleep(0.3)
        await edit_or_reply(catevent, "`..!..`")
        await asyncio.sleep(0.3)
        await edit_or_reply(catevent, "`....!`")
        end = datetime.now()
        tms = (end - start).microseconds / 1000
        ms = round((tms - 0.6) / 3, 3)
        await edit_or_reply(catevent, f"◆ **AVERAGE PING**\n`{ms} ms`")
        return

    catevent = await edit_or_reply(event, temp_)
    end = datetime.now()
    ms = round((end - start).microseconds / 1000, 3)
    ping_temp = gvarstatus("PING_TEMPLATE") or temp
    PING_PIC = gvarstatus("PING_PIC")
    ANIME = None
    if "ANIME" in ping_temp:
        data = requests.get("https://animechan.vercel.app/api/random", timeout=8).json()
        ANIME = f"**“{data['quote']}” - {data['character']} ({data['anime']})**"
    caption = ping_temp.format(
        ANIME=ANIME,
        mention=mention,
        uptime=uptime,
        ping=ms,
    )

    asset = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "assets", "ping_card.jpg"
    )
    if PING_PIC:
        media_list = PING_PIC.split()
        media = random.choice(media_list)
    else:
        media = asset if os.path.isfile(asset) else None

    buttons = [
        [
            Button.url("Support", "https://t.me/catuserbot_support"),
            Button.url("Channel", "https://t.me/catuserbot17"),
        ]
    ]
    if media:
        try:
            await event.client.send_file(
                event.chat_id,
                media,
                caption=caption,
                reply_to=reply_to_id,
                buttons=buttons,
            )
            await catevent.delete()
        except (WebpageMediaEmptyError, MediaEmptyError, WebpageCurlFailedError):
            await edit_or_reply(catevent, caption)
        except Exception:
            # A media failure must not make the existing .ping command unusable.
            await edit_or_reply(catevent, caption)
    else:
        await edit_or_reply(catevent, caption)
