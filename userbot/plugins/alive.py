# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# CatUserBot #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Copyright (C) 2020-2023 by TgCatUB@Github.
# This file is part of: https://github.com/TgCatUB/catuserbot
# and is released under the "GNU v3.0 License Agreement".
# Please see: https://github.com/TgCatUB/catuserbot/blob/master/LICENSE
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import random
import time
from platform import python_version

from telethon import Button, version

from userbot import StartTime, catub, catversion
from userbot.core import PLG_INFO
from ..core.managers import edit_or_reply
from ..helpers.functions import check_data_base_heal_th, get_readable_time
from ..sql_helper.globals import gvarstatus
from . import mention

plugin_category = "utils"

# ─── CipherElite-style quotes ────────────────────────────────────────────────
QUOTES = [
    "Code is read far more often than it is written.",
    "Simplicity is the soul of efficiency.",
    "Every expert was once a beginner who refused to quit.",
    "Automation isn't about replacing effort — it's about redirecting it.",
    "Uptime is a promise, not an accident.",
]

# ─── CipherElite-style alive templates (with blockquotes) ───────────────────
ALIVE_STYLES = [
    # Style 1: Terminal / Hacker
    """
> ⚡ **S Y S T E M  O N L I N E** ⚡

`User    :` {mention}
`Core    :` v{catver}
`Telethon:` {telever}
`Modules :` {modules}
`Uptime  :` {uptime}

> " {quote} "
""",
    # Style 2: Elegant Minimalist
    """
✨ **{mention} is currently Active.**

> ⚙️ **C I P H E R  S T A T S**
> ├ Version: {catver}
> ├ Engine : Telethon {telever}
> ├ Arsenal: {modules} plugins
> └ Uptime : {uptime}

> " {quote} "
""",
    # Style 3: Royal Card
    """
**C I P H E R  E L I T E  V {catver}**
━━━━━━━━━━━━━━━━━━━━

> Master : {mention}
> ⏳ Uptime : {uptime}
> Plugins : {modules} Loaded

━━━━━━━━━━━━━━━━━━━━
✦ *{quote}* ✦
""",
    # Style 4: Cyberpunk Box
    """
> **N E T W O R K  A L I V E**
> ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰
> ► Pilot : {mention}
> ► Build : v{catver}
> ► Mods  : {modules} active
> ► Time  : {uptime}
> ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰

`> {quote}`""",
    # Style 5: Quote-Centric
    """
> ❝ *{quote}* ❞

**CipherElite is Running Smoothly!**
• Owner: {mention}
• Status: Online for {uptime}
• Specs: v{catver} | {modules} Plugins
""",
]

# ─── Buttons (CipherElite style) ─────────────────────────────────────────────
ALIVE_BUTTONS = [
    [
        Button.url("Support", "https://t.me/catuserbot_support"),
        Button.url("Channel", "https://t.me/catuserbot17"),
    ]
]


@catub.cat_cmd(
    pattern="alive$",
    command=("alive", plugin_category),
    info={
        "header": "Show Userbot status",
        "description": "Shows the current status of the userbot with an image.",
        "usage": "{tr}alive",
    },
)
async def amireallyalive(event):
    "CipherElite-style .alive — sends an image card with status."

    # ── 1. Gather data ──────────────────────────────────────────────────────
    uptime = await get_readable_time(time.time() - StartTime)
    try:
        _, db_health = check_data_base_heal_th()
    except Exception:
        db_health = "Unknown"

    # ── 2. Choose template ─────────────────────────────────────────────────
    style_idx = 0
    try:
        style_idx = int(gvarstatus("ALIVE_STYLE") or 0) % len(ALIVE_STYLES)
    except (ValueError, TypeError):
        style_idx = 0
    template = ALIVE_STYLES[style_idx]

    # ── 3. Format caption ──────────────────────────────────────────────────
    caption = template.format(
        mention=mention,
        uptime=uptime,
        catver=catversion,
        telever=version.__version__,
        modules=len(PLG_INFO),
        dbhealth=db_health,
        quote=random.choice(QUOTES),
    )

    # ── 4. Handle image ────────────────────────────────────────────────────
    #    Priority: gvar ALIVE_PIC → default image → text only
    alive_pic = gvarstatus("ALIVE_PIC")

    if alive_pic:
        # Send photo with caption and buttons
        try:
            await event.client.send_file(
                event.chat_id,
                random.choice(alive_pic.split()),
                caption=caption,
                reply_to=event.reply_to_msg_id,
                buttons=ALIVE_BUTTONS,
            )
            # Delete the original command message for a clean look
            await event.delete()
        except Exception as e:
            # If photo fails, fall back to text edit
            await edit_or_reply(
                event,
                f"⚠️ **Photo failed:** `{type(e).__name__}`\n\n{caption}",
            )
    else:
        # No image configured — edit the command message (clean, no new msg)
        await edit_or_reply(
            event,
            f"{caption}\n\n"
            "> ℹ️ *Set an image with* `.setgvar ALIVE_PIC <url>`",
        )
