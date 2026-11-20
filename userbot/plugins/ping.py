# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# CatUserBot #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Copyright (C) 2020-2023 by TgCatUB@Github.

# This file is part of: https://github.com/TgCatUB/catuserbot
# and is released under the "GNU v3.0 License Agreement".

# Please see: https://github.com/TgCatUB/catuserbot/blob/master/LICENSE
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import asyncio
import time
from datetime import datetime

from ..Config import Config
from ..core.managers import edit_or_reply
from ..helpers.functions import get_readable_time
from ..sql_helper.globals import gvarstatus
from . import StartTime, catub

plugin_category = "tools"


@catub.cat_cmd(
    pattern="ping( -a|$)",
    command=("ping", plugin_category),
    info={
        "header": "Check response latency",
        "flags": {"-a": "average ping"},
        "usage": ["{tr}ping", "{tr}ping -a"],
    },
)
async def pingme(event):
    "Check CAT Userbot latency — edits the command message."
    start = datetime.now()
    if event.pattern_match.group(1) == " -a":
        catevent = await edit_or_reply(event, "`!....`")
        await asyncio.sleep(0.3)
        await edit_or_reply(catevent, "`..!..`")
        await asyncio.sleep(0.3)
        await edit_or_reply(catevent, "`....!`")
        end = datetime.now()
        tms = (end - start).microseconds / 1000
        ms = round((tms - 0.6) / 3, 3)
        await edit_or_reply(catevent, f"🏓 **PONG!**\n`{ms} ms`")
        return

    # Edit command message immediately
    catevent = await edit_or_reply(event, "`PONG!`")
    end = datetime.now()
    tms = (end - start).microseconds / 1000
    ms = round(tms, 3)
    uptime = await get_readable_time(time.time() - StartTime)
    pingtemp = gvarstatus("PING_TEMPLATE") or (
        "🏓 **PONG!**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "◉ **Latency:** `{} ms`\n"
        "◉ **Uptime:** `{uptime}`\n"
        "◉ **Status:** `ONLINE`\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    try:
        caption = pingtemp.format(ms, uptime=uptime)
    except (KeyError, IndexError):
        caption = pingtemp.format(ms)

    # Always edit the same message — clean UI (like cipherelite)
    # To use a picture, set gvar PING_PIC; but note: text→media cannot be edited,
    # so we stay text-only for clean UI.
    await edit_or_reply(catevent, caption)
