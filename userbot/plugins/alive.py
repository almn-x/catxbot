# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# CatUserBot #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Copyright (C) 2020-2023 by TgCatUB@Github.
#
# This file is part of: https://github.com/TgCatUB/catuserbot
# and is released under the "GNU v3.0 License Agreement".
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import os
import random
import re
import time
from platform import python_version

import requests
from telethon import Button, version
from telethon.errors.rpcerrorlist import (
    MediaEmptyError,
    WebpageCurlFailedError,
    WebpageMediaEmptyError,
)
from telethon.events import CallbackQuery

from userbot import StartTime, catub, catversion
from userbot.core import PLG_INFO

from ..Config import Config
from ..core.managers import edit_or_reply
from ..helpers.functions import catalive, check_data_base_heal_th, get_readable_time
from ..helpers.utils import reply_id
from ..sql_helper.globals import gvarstatus
from . import mention

plugin_category = "utils"


@catub.cat_cmd(
    pattern="alive$",
    command=("alive", plugin_category),
    info={
        "header": "Show CAT Userbot system status",
        "options": "Set ALIVE_PIC to override the built-in CAT artwork.",
        "usage": ["{tr}alive"],
    },
)
async def amireallyalive(event):
    "Show the live status and runtime information of CAT Userbot."
    reply_to_id = await reply_id(event)
    cat_caption = gvarstatus("ALIVE_TEMPLATE") or temp
    ANIME = None
    if "ANIME" in cat_caption:
        data = requests.get("https://animechan.vercel.app/api/random", timeout=8).json()
        ANIME = f"**“{data['quote']}” - {data['character']} ({data['anime']})**"

    uptime = await get_readable_time(time.time() - StartTime)
    start = time.perf_counter()
    catevent = await edit_or_reply(event, "`Checking CAT system...`")
    ms = round((time.perf_counter() - start) * 1000, 3)
    _, db_health = check_data_base_heal_th()

    EMOJI = gvarstatus("ALIVE_EMOJI") or "◉"
    ALIVE_TEXT = gvarstatus("ALIVE_TEXT") or "◆ **SYSTEM ONLINE** ◆"
    CAT_IMG = gvarstatus("ALIVE_PIC")
    caption = cat_caption.format(
        ALIVE_TEXT=ALIVE_TEXT,
        ANIME=ANIME,
        EMOJI=EMOJI,
        mention=mention,
        uptime=uptime,
        telever=version.__version__,
        catver=catversion,
        pyver=python_version(),
        dbhealth=db_health,
        ping=ms,
        modules=len(PLG_INFO),
    )

    asset = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "assets", "alive_card.jpg"
    )
    if CAT_IMG:
        media = random.choice(CAT_IMG.split())
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
            # Keep .alive available even if Telegram cannot fetch the selected media.
            await edit_or_reply(catevent, caption)
    else:
        await edit_or_reply(catevent, caption)


temp = """{ALIVE_TEXT}
━━━━━━━━━━━━━━━━━━
◉ **User:** {mention}
◉ **Core:** `{catver}`
◉ **Telethon:** `{telever}`
◉ **Python:** `{pyver}`
◉ **Modules:** `{modules}` loaded
◉ **Database:** `{dbhealth}`
◉ **Uptime:** `{uptime}`
◉ **Response:** `{ping} ms`
━━━━━━━━━━━━━━━━━━
_“A clean log file is a peaceful mind.”_"""


def catalive_text():
    EMOJI = gvarstatus("ALIVE_EMOJI") or "  ✥ "
    cat_caption = "**Catuserbot is Up and Running**\n"
    cat_caption += f"**{EMOJI} Telethon version :** `{version.__version__}\n`"
    cat_caption += f"**{EMOJI} Catuserbot Version :** `{catversion}\n`"
    cat_caption += f"**{EMOJI} Python Version :** `{python_version()}\n`"
    cat_caption += f"**{EMOJI} Master:** {mention}\n"
    return cat_caption


@catub.cat_cmd(
    pattern="ialive$",
    command=("ialive", plugin_category),
    info={
        "header": "To check bot's alive status via inline mode",
        "options": "To show media in this cmd set ALIVE_PIC or IALIVE_PIC.",
        "usage": ["{tr}ialive"],
    },
)
async def amireallyalive_inline(event):
    "Show bot details via the inline bot."
    reply_to_id = await reply_id(event)
    results = await event.client.inline_query(Config.TG_BOT_USERNAME, "ialive")
    await results[0].click(event.chat_id, reply_to=reply_to_id, hide_via=True)
    await event.delete()


@catub.tgbot.on(CallbackQuery(data=re.compile(b"stats")))
async def on_plug_in_callback_query_handler(event):
    statstext = await catalive(StartTime)
    await event.answer(statstext, cache_time=0, alert=True)
