# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# CatUserBot #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Copyright (C) 2020-2023 by TgCatUB@Github.

# This file is part of: https://github.com/TgCatUB/catuserbot
# and is released under the "GNU v3.0 License Agreement".

# Please see: https://github.com/TgCatUB/catuserbot/blob/master/LICENSE
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

import signal
import sys
import time

import heroku3

from .Config import Config
from .core.logger import logging
from .core.session import catub
from .helpers.functions.converter import Convert
from .helpers.functions.musictool import *
from .helpers.utils.utils import runasync
from .sql_helper.globals import addgvar, delgvar, gvarstatus

__version__ = "3.3.0"
__license__ = "GNU Affero General Public License v3.0"
__author__ = "CatUserBot <https://github.com/TgCatUB/catuserbot>"
__copyright__ = f"Copyright (C) 2020 - 2023  {__author__}"

catub.version = __version__
catub.tgbot.version = __version__
LOGS = logging.getLogger("CatUserbot")
bot = catub

StartTime = time.time()
catversion = "3.3.0"


def _safe_int(value, default=0):
    """Convert value to int safely; return default on ValueError/TypeError."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def close_connection(*_):
    print("Closing Userbot connection.")
    runasync(catub.disconnect())
    sys.exit(143)


signal.signal(signal.SIGTERM, close_connection)

UPSTREAM_REPO_URL = Config.UPSTREAM_REPO

# ---------- Safe BOTLOG_CHATID resolution ----------
# Never crash if the DB contains an invalid value (e.g. spam-report error message).
if Config.PRIVATE_GROUP_BOT_API_ID == 0:
    _botlog_raw = gvarstatus("PRIVATE_GROUP_BOT_API_ID")
    if _botlog_raw is None:
        Config.BOTLOG = False
        Config.BOTLOG_CHATID = "me"
    else:
        _botlog_id = _safe_int(_botlog_raw, default=0)
        if _botlog_id == 0:
            print(
                "[WARN] Invalid PRIVATE_GROUP_BOT_API_ID in database; "
                "falling back to Saved Messages for BOTLOG."
            )
            Config.BOTLOG = False
            Config.BOTLOG_CHATID = "me"
        else:
            Config.BOTLOG_CHATID = _botlog_id
            Config.PRIVATE_GROUP_BOT_API_ID = _botlog_id
            Config.BOTLOG = True
else:
    if str(Config.PRIVATE_GROUP_BOT_API_ID)[0] != "-":
        Config.BOTLOG_CHATID = int(f"-{str(Config.PRIVATE_GROUP_BOT_API_ID)}")
    else:
        Config.BOTLOG_CHATID = Config.PRIVATE_GROUP_BOT_API_ID
    Config.BOTLOG = True

# ---------- Safe PM_LOGGER_GROUP_ID ----------
if Config.PM_LOGGER_GROUP_ID == 0:
    _pm_raw = gvarstatus("PM_LOGGER_GROUP_ID")
    if _pm_raw is None:
        Config.PM_LOGGER_GROUP_ID = -100
    else:
        _pm_id = _safe_int(_pm_raw, default=-100)
        Config.PM_LOGGER_GROUP_ID = _pm_id if _pm_id != 0 else -100
elif str(Config.PM_LOGGER_GROUP_ID)[0] != "-":
    Config.PM_LOGGER_GROUP_ID = int(f"-{str(Config.PM_LOGGER_GROUP_ID)}")

try:
    if Config.HEROKU_API_KEY is not None or Config.HEROKU_APP_NAME is not None:
        HEROKU_APP = heroku3.from_key(Config.HEROKU_API_KEY).apps()[
            Config.HEROKU_APP_NAME
        ]
    else:
        HEROKU_APP = None
except Exception:
    HEROKU_APP = None


# Global Configiables
COUNT_MSG = 0
USERS = {}
COUNT_PM = {}
LASTMSG = {}
CMD_HELP = {}
ISAFK = False
AFKREASON = None
CMD_LIST = {}
SUDO_LIST = {}
# for later purposes
INT_PLUG = ""
LOAD_PLUG = {}

# Variables
BOTLOG = Config.BOTLOG
BOTLOG_CHATID = Config.BOTLOG_CHATID
PM_LOGGER_GROUP_ID = Config.PM_LOGGER_GROUP_ID
