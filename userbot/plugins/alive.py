# CATXBot Combined Alive + Ping Plugin (Fixed for CAT Userbot)
# Uses CAT Userbot's catub.cat_cmd, edit_or_reply, gvarstatus/addgvar.
# UI styles adapted from CipherElite (blockquote-heavy, quote rotation).

import random
import time
from telethon import Button, version

from userbot import StartTime, catub, catversion
from userbot.core import PLG_INFO
from ..core.managers import edit_or_reply
from ..helpers.functions import get_readable_time
from ..sql_helper.globals import gvarstatus, addgvar, delgvar

plugin_category = "utils"

# ═══════════════════════════════════════════════════════════════
# Mentions (CAT Userbot's helper)
# ═══════════════════════════════════════════════════════════════
try:
    from userbot.plugins import mention as hmention
except ImportError:
    hmention = "User"

ALIVE_BUTTONS = [[
    Button.url("Support", "https://t.me/catuserbot_support"),
    Button.url("Channel", "https://t.me/catuserbot17"),
]]

QUOTES = [
    "Code is read far more often than it is written.",
    "Simplicity is the soul of efficiency.",
    "Every expert was once a beginner who refused to quit.",
    "Automation is redirecting effort toward better work.",
    "Uptime is a promise, not an accident.",
    "Ship it, measure it, improve it.",
    "A clean log file is a peaceful mind.",
    "Speed matters, but stability wins the long game.",
]

# ═══════════════════════════════════════════════════════════════
# ALIVE STYLES (CipherElite-inspired, HTML blockquotes)
# ═══════════════════════════════════════════════════════════════
ALIVE_STYLES = [
    """<blockquote><b>⚡ S Y S T E M  O N L I N E ⚡</b></blockquote>
<code>User     :</code> {mention}
<code>Core     :</code> v{version}
<code>Telethon :</code> {telethon}
<code>Modules  :</code> {plugins}
<code>Uptime   :</code> {uptime}

<blockquote><i>❝ {quote} ❞</i></blockquote>""",

    """✨ <b>{mention}</b> is currently <b>Active</b>.
<blockquote><b>⚙️ C A T  S T A T S</b>
├ <b>Version:</b> {version}
├ <b>Engine :</b> Telethon {telethon}
├ <b>Modules:</b> {plugins}
└ <b>Uptime :</b> {uptime}</blockquote>

💡 <i>{quote}</i>""",

    """👑 <b>C A T  U S E R B O T</b>
━━━━━━━━━━━━━━━━━━━━
<blockquote>👤 <b>Owner :</b> {mention}
⏳ <b>Uptime:</b> {uptime}
🔋 <b>Plugins:</b> {plugins} loaded
⚙️ <b>Build :</b> {version}</blockquote>
━━━━━━━━━━━━━━━━━━━━
✦ <i>{quote}</i> ✦""",

    """<blockquote>🌐 <b>N E T W O R K  A L I V E</b>
▰▰▰▰▰▰▰▰▰▰▰▰▰▰
► <b>User :</b> {mention}
► <b>Build:</b> {version}
► <b>Mods :</b> {plugins} active
► <b>Time :</b> {uptime}
▰▰▰▰▰▰▰▰▰▰▰▰▰▰</blockquote>
<code>> {quote}</code>""",

    """<blockquote>❝ <b>{quote}</b> ❞</blockquote>
🤖 <b>CAT Userbot is Running Smoothly!</b>
• <b>Owner:</b> {mention}
• <b>Status:</b> Online for {uptime}
• <b>Specs:</b> v{version} | {plugins} plugins""",
]

PING_STYLES = [
    """<blockquote><b>📡 P I N G  R E P O R T</b></blockquote>
<code>Latency:</code> <b>{speed} ms</b>
<code>Uptime :</code> <b>{uptime}</b>
<code>Status :</code> <b>ONLINE</b>""",

    """🏓 <b>P O N G !</b>
<blockquote>├ ⚡ <b>{speed} ms</b>
└ ⏱ <b>{uptime}</b></blockquote>""",

    """✨ <b>P O N G</b> ✨
━━━━━━━━━━━━━
<blockquote>🚀 <b>Speed:</b> {speed} ms
⏳ <b>Uptime:</b> {uptime}</blockquote>""",

    """<blockquote>🌐 <b>L A T E N C Y</b>
▰▰▰▰▰▰▰▰▰▰
► <b>{speed} ms</b>
► <b>{uptime}</b></blockquote>""",

    """<blockquote>💨 <i>Response time: <b>{speed} ms</b></i></blockquote>
⏱ <b>System up for:</b> {uptime}""",
]


def _get_int(key, default=0, maximum=4):
    try:
        value = int(gvarstatus(key) or default)
        return value if 0 <= value <= maximum else default
    except (TypeError, ValueError):
        return default


def _get_bool(key, default=True):
    value = gvarstatus(key)
    if value is None:
        return default
    return str(value).lower() in ("1", "true", "yes", "on")


def _set(key, value):
    addgvar(key, str(value))


def _uptime():
    return get_readable_time(time.time() - StartTime)


async def _get_photo(event, key):
    """Return a Telegram photo (from Saved Messages ID) or a URL."""
    toggle_key = "CAT_ALIVE_PIC_ON" if key == "CAT_ALIVE_PIC" else "CAT_PING_PIC_ON"
    if not _get_bool(toggle_key, True):
        return None
    value = gvarstatus(key)
    if not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        return value
    try:
        msg = await event.client.get_messages("me", ids=int(value))
        return msg.media if msg and msg.media else None
    except (TypeError, ValueError):
        return None


async def _show_card(event, caption, photo_key):
    """Show card with or without photo (HTML)."""
    photo = await _get_photo(event, photo_key)
    if not photo:
        await edit_or_reply(event, caption, parse_mode="html",
                            buttons=ALIVE_BUTTONS)
        return
    try:
        await event.edit(caption, file=photo, parse_mode="html",
                         buttons=ALIVE_BUTTONS)
    except Exception:
        try:
            await event.client.send_file(
                event.chat_id, photo, caption=caption,
                parse_mode="html", buttons=ALIVE_BUTTONS,
                reply_to=event.reply_to_msg_id,
            )
            await event.delete()
        except Exception:
            await edit_or_reply(event, caption, parse_mode="html",
                                buttons=ALIVE_BUTTONS)


async def _save_replied_photo(event, key, label):
    if not event.reply_to_msg_id:
        await edit_or_reply(event, f"Reply to a Telegram photo and use `.set{label}pic`.")
        return
    source = await event.get_reply_message()
    if not source or not source.photo:
        await edit_or_reply(event, "Please reply to a Telegram photo.")
        return
    try:
        saved_photo = await event.client.send_file(
            "me", source.media, caption=f"CAT {label.upper()} PHOTO")
        _set(key, saved_photo.id)
        await edit_or_reply(event, f"✅ {label.title()} photo saved in Saved Messages.")
    except Exception as exc:
        await edit_or_reply(event, f"❌ Could not save photo: `{type(exc).__name__}`")


@catub.cat_cmd(
    pattern="alive$",
    command=("alive", plugin_category),
    info={
        "header": "Alive status",
        "description": "Show status with photo and style.",
        "usage": "{tr}alive",
    },
)
async def alive(event):
    quote = random.choice(QUOTES) if _get_bool("CAT_SHOW_QUOTES", True) else "CAT Userbot"
    template = gvarstatus("CAT_ALIVE_TEXT") or ALIVE_STYLES[_get_int("CAT_ALIVE_STYLE")]
    caption = template.format(
        mention=hmention,
        version=catversion,
        telethon=version.__version__,
        plugins=len(PLG_INFO),
        uptime=_uptime(),
        quote=quote,
    )
    await _show_card(event, caption, "CAT_ALIVE_PIC")


@catub.cat_cmd(
    pattern="ping( -a|$)",
    command=("ping", plugin_category),
    info={
        "header": "Ping status",
        "description": "Show ping report with photo.",
        "flags": {"-a": "average ping"},
        "usage": ["{tr}ping", "{tr}ping -a"],
    },
)
async def ping(event):
    start = time.perf_counter()
    try:
        await event.edit("`Pinging...`")
    except Exception:
        pass
    elapsed = (time.perf_counter() - start) * 1000
    if event.pattern_match.group(1) == " -a":
        samples = []
        for _ in range(3):
            t0 = time.perf_counter()
            try:
                await event.client.get_me()
            except Exception:
                pass
            samples.append((time.perf_counter() - t0) * 1000)
        elapsed = sum(samples) / len(samples)
    template = gvarstatus("CAT_PING_TEXT") or PING_STYLES[_get_int("CAT_PING_STYLE")]
    caption = template.format(speed=round(elapsed, 2), uptime=_uptime())
    await _show_card(event, caption, "CAT_PING_PIC")


@catub.cat_cmd(
    pattern="setalivepic$",
    command=("setalivepic", plugin_category),
    info={"header": "Set alive photo", "description": "Reply to a Telegram photo.",
          "usage": "{tr}setalivepic"},
)
async def set_alive_pic(event):
    await _save_replied_photo(event, "CAT_ALIVE_PIC", "alive")


@catub.cat_cmd(
    pattern="setpingpic$",
    command=("setpingpic", plugin_category),
    info={"header": "Set ping photo", "description": "Reply to a Telegram photo.",
          "usage": "{tr}setpingpic"},
)
async def set_ping_pic(event):
    await _save_replied_photo(event, "CAT_PING_PIC", "ping")


@catub.cat_cmd(
    pattern="setalive ([1-5])$",
    command=("setalive", plugin_category),
    info={"header": "Set alive style", "usage": "{tr}setalive 1-5"},
)
async def set_alive_style(event):
    _set("CAT_ALIVE_STYLE", int(event.pattern_match.group(1)) - 1)
    delgvar("CAT_ALIVE_TEXT")
    await edit_or_reply(event, f"✅ Alive style set to #{event.pattern_match.group(1)}")


@catub.cat_cmd(
    pattern="setping ([1-5])$",
    command=("setping", plugin_category),
    info={"header": "Set ping style", "usage": "{tr}setping 1-5"},
)
async def set_ping_style(event):
    _set("CAT_PING_STYLE", int(event.pattern_match.group(1)) - 1)
    delgvar("CAT_PING_TEXT")
    await edit_or_reply(event, f"✅ Ping style set to #{event.pattern_match.group(1)}")


@catub.cat_cmd(
    pattern="setalivetext (.+)",
    command=("setalivetext", plugin_category),
    info={"header": "Custom alive text", "usage": "{tr}setalivetext <text>"},
)
async def set_alive_text(event):
    _set("CAT_ALIVE_TEXT", event.pattern_match.group(1))
    await edit_or_reply(
        event,
        "✅ Custom alive text saved. Placeholders: `{mention}`, `{version}`, "
        "`{telethon}`, `{plugins}`, `{uptime}`, `{quote}`",
    )


@catub.cat_cmd(
    pattern="setpingtext (.+)",
    command=("setpingtext", plugin_category),
    info={"header": "Custom ping text", "usage": "{tr}setpingtext <text>"},
)
async def set_ping_text(event):
    _set("CAT_PING_TEXT", event.pattern_match.group(1))
    await edit_or_reply(
        event, "✅ Custom ping text saved. Placeholders: `{speed}`, `{uptime}`")


@catub.cat_cmd(
    pattern="togglealivepic$",
    command=("togglealivepic", plugin_category),
    info={"header": "Toggle alive photo"},
)
async def toggle_alive_pic(event):
    state = not _get_bool("CAT_ALIVE_PIC_ON", True)
    _set("CAT_ALIVE_PIC_ON", state)
    await edit_or_reply(event, f"Alive photo: {'ON' if state else 'OFF'}")


@catub.cat_cmd(
    pattern="togglepingpic$",
    command=("togglepingpic", plugin_category),
    info={"header": "Toggle ping photo"},
)
async def toggle_ping_pic(event):
    state = not _get_bool("CAT_PING_PIC_ON", True)
    _set("CAT_PING_PIC_ON", state)
    await edit_or_reply(event, f"Ping photo: {'ON' if state else 'OFF'}")


@catub.cat_cmd(
    pattern="togglequotes$",
    command=("togglequotes", plugin_category),
    info={"header": "Toggle alive quotes"},
)
async def toggle_quotes(event):
    state = not _get_bool("CAT_SHOW_QUOTES", True)
    _set("CAT_SHOW_QUOTES", state)
    await edit_or_reply(event, f"Alive quotes: {'ON' if state else 'OFF'}")


@catub.cat_cmd(
    pattern="alivestyles$",
    command=("alivestyles", plugin_category),
    info={"header": "List alive styles"},
)
async def alive_styles(event):
    lines = ["<b>AVAILABLE ALIVE STYLES</b>"]
    for index, style in enumerate(ALIVE_STYLES, 1):
        lines.append(
            f"\n<b>STYLE #{index}</b>\n"
            f"{style.format(mention=hmention, version=catversion, "
            f"telethon=version.__version__, plugins=len(PLG_INFO), "
            f"uptime=_uptime(), quote='Your quote')}"
        )
    lines.append("\nUse <code>.setalive 1-5</code>")
    await event.reply("\n".join(lines), parse_mode="html")


@catub.cat_cmd(
    pattern="pingstyles$",
    command=("pingstyles", plugin_category),
    info={"header": "List ping styles"},
)
async def ping_styles(event):
    lines = ["<b>AVAILABLE PING STYLES</b>"]
    for index, style in enumerate(PING_STYLES, 1):
        lines.append(
            f"\n<b>STYLE #{index}</b>\n"
            f"{style.format(speed=42.5, uptime=_uptime())}"
        )
    lines.append("\nUse <code>.setping 1-5</code>")
    await event.reply("\n".join(lines), parse_mode="html")


@catub.cat_cmd(
    pattern="resetalive$",
    command=("resetalive", plugin_category),
    info={"header": "Reset alive settings"},
)
async def reset_alive(event):
    for key in ("CAT_ALIVE_STYLE", "CAT_ALIVE_TEXT", "CAT_ALIVE_PIC",
                "CAT_ALIVE_PIC_ON", "CAT_SHOW_QUOTES"):
        delgvar(key)
    await edit_or_reply(event, "✅ Alive settings reset.")


@catub.cat_cmd(
    pattern="resetping$",
    command=("resetping", plugin_category),
    info={"header": "Reset ping settings"},
)
async def reset_ping(event):
    for key in ("CAT_PING_STYLE", "CAT_PING_TEXT", "CAT_PING_PIC",
                "CAT_PING_PIC_ON"):
        delgvar(key)
    await edit_or_reply(event, "✅ Ping settings reset.")
