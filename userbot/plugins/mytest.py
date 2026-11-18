# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Custom Test Plugin for CAT Userbot
# Location: userbot/plugins/mytest.py
# Purpose: MVP test to verify custom plugin loading works
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from userbot import catub
from ..core.managers import edit_or_reply

plugin_category = "utility"


@catub.cat_cmd(
    pattern="mytest$",
    command=("mytest", plugin_category),
    info={
        "header": "Test custom plugin",
        "description": "Confirms that custom plugin system is working.",
        "usage": "{tr}mytest",
    },
)
async def mytest(event):
    "Says hello from custom plugin"
    await edit_or_reply(
        event,
        "✅ **Custom Plugin Working!**\n\n"
        "This reply is coming from `userbot/plugins/mytest.py`.",
    )


@catub.cat_cmd(
    pattern="myecho(?: |$)(.*)",
    command=("myecho", plugin_category),
    info={
        "header": "Echo test command",
        "description": "Repeats back whatever text you provide.",
        "usage": "{tr}myecho <text>",
    },
)
async def myecho(event):
    "Echo back the provided text"
    text = event.pattern_match.group(1)
    if not text:
        return await edit_or_reply(
            event, "❌ **Usage:** `.myecho hello world`"
        )
    await edit_or_reply(event, f"🔊 **Echo:** `{text}`")
