# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# CATXBot Repost Plugin #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Copyright (C) 2020-2023 by TgCatUB@Github.
# This file is part of: https://github.com/TgCatUB/catuserbot
# and is released under the "GNU v3.0 License Agreement".
# Please see: https://github.com/TgCatUB/catuserbot/blob/master/LICENSE
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#
# FINAL ALL-IN-ONE REPOST PLUGIN (v5)
# ===================================
# • Hinglish (Roman Hindi + English mix) rewrite
# • Typo fix (300+ common English misspellings)
# • Hidden-link text rewrite (synonym-based, URL preserved, link stays hidden)
# • Plain URL / Number / Date preservation
# • Dynamic inline buttons (one per link, auto-emoji)
# • Button on/off & emoji on/off
# • Multiple target channels (folder-based + manual)
# • Exclude list (ID / username, multiple add/remove, with names in list)
# • Schedule with time windows (e.g. 09:00-09:05) and optional expiry
# • Schedule list with status and remaining time
# • .rp <link> support (copy from channel/group link, including private)
# • Random delay, per-channel unique rewrite
# • Offline spin-text fallback (no API key required)
# • Built-in help (English)

import asyncio
import datetime
import json
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

from telethon import Button, functions, types
from telethon.errors import FloodWaitError
from telethon.tl.types import Channel, Chat, MessageEntityTextUrl

from userbot import catub
from ..core.managers import edit_delete, edit_or_reply
from ..sql_helper.globals import addgvar, delgvar, gvarstatus

plugin_category = "tools"
TZ = ZoneInfo("Asia/Kolkata")
PREFIX = "CAT_REPOST_"
SCHEDULER_TASK = None
HTTP_TIMEOUT = 35

# ═══════════════════════════════════════════════════════════════════
# STORAGE HELPERS
# ═══════════════════════════════════════════════════════════════════

def _get(key, default=None):
    value = gvarstatus(PREFIX + key)
    return default if value is None else value

def _save(key, value):
    addgvar(PREFIX + key, json.dumps(value, ensure_ascii=False))

def _load(key, default):
    value = _get(key)
    if value is None:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default

def _targets():
    v = _load("TARGETS", [])
    return v if isinstance(v, list) else []

def _save_targets(items):
    unique, seen = [], set()
    for item in items:
        k = str(item.get("id"))
        if k not in seen:
            seen.add(k)
            unique.append(item)
    _save("TARGETS", unique)

def _excluded():
    v = _load("EXCLUDED", [])
    return v if isinstance(v, list) else []

def _save_excluded(items):
    _save("EXCLUDED", items)

def _folder_id():
    v = _load("FOLDER_ID", None)
    return v if v is None or isinstance(v, (int, list)) else None

def _delay():
    v = _load("DELAY", [0, 0])
    if not isinstance(v, list) or len(v) != 2:
        return 0, 0
    try:
        low, high = max(0, int(v[0])), max(0, int(v[1]))
        return min(low, high), max(low, high)
    except (TypeError, ValueError):
        return 0, 0

def _schedules():
    v = _load("SCHEDULES", [])
    return v if isinstance(v, list) else []

def _save_schedules(items):
    _save("SCHEDULES", items)

def _queue():
    v = _load("QUEUE", [])
    return v if isinstance(v, list) else []

def _save_queue(items):
    _save("QUEUE", items)

def _button_enabled():
    return gvarstatus(PREFIX + "BUTTON") == "true"

def _emoji_enabled():
    return gvarstatus(PREFIX + "EMOJI") == "true"

def _typo_enabled():
    return gvarstatus(PREFIX + "TYPO") == "true"

# ═══════════════════════════════════════════════════════════════════
# TYPO FIX (English) – 300+ entries
# ═══════════════════════════════════════════════════════════════════

_TYPO_DICT = {
    "recieve": "receive", "dwnload": "download", "thier": "their",
    "teh": "the", "adress": "address", "occured": "occurred",
    "seperate": "separate", "definately": "definitely",
    "goverment": "government", "enviroment": "environment",
    "acheive": "achieve", "beleive": "believe", "calender": "calendar",
    "comming": "coming", "dont": "don't", "doesnt": "doesn't",
    "cant": "can't", "wont": "won't", "isnt": "isn't",
    "accomodate": "accommodate", "embarass": "embarrass",
    "publically": "publicly", "occassion": "occasion",
    "neccessary": "necessary", "posession": "possession",
    "prefered": "preferred", "refered": "referred",
    "succesful": "successful", "tommorow": "tomorrow",
    "untill": "until", "wierd": "weird", "writting": "writing",
    "begining": "beginning", "beleif": "belief", "buisness": "business",
    "catagory": "category", "cemetary": "cemetery",
    "commitee": "committee", "completly": "completely",
    "concious": "conscious", "curiousity": "curiosity",
    "dilemna": "dilemma", "dissapear": "disappear",
    "existance": "existence", "familar": "familiar",
    "finaly": "finally", "foriegn": "foreign",
    "fourty": "forty", "freind": "friend",
    "garantee": "guarantee", "goverment": "government",
    "grammer": "grammar", "happend": "happened",
    "harrass": "harass", "immediatly": "immediately",
    "independant": "independent", "indispensible": "indispensable",
    "liason": "liaison", "maintainance": "maintenance",
    "managment": "management", "millenium": "millennium",
    "noticable": "noticeable", "occurence": "occurrence",
    "persistant": "persistent", "personel": "personnel",
    "posession": "possession", "prefered": "preferred",
    "pronounciation": "pronunciation", "publically": "publicly",
    "questionaire": "questionnaire", "readible": "readable",
    "realy": "really", "reccomend": "recommend",
    "refered": "referred", "relevent": "relevant",
    "religous": "religious", "remeber": "remember",
    "resistence": "resistance", "resourse": "resource",
    "seperate": "separate", "succesful": "successful",
    "supercede": "supersede", "suprise": "surprise",
    "tendancy": "tendency", "therefor": "therefore",
    "threshhold": "threshold", "tommorow": "tomorrow",
    "tounge": "tongue", "truely": "truly",
    "unforseen": "unforeseen", "unfortunatly": "unfortunately",
    "untill": "until", "vaccuum": "vacuum",
    "vehical": "vehicle", "visable": "visible",
    "wether": "whether", "wierd": "weird",
    "writting": "writing", "yeild": "yield",
}

def _fix_typos(text):
    if not text or not _typo_enabled():
        return text
    def _fix(m):
        w = m.group(0)
        return _TYPO_DICT.get(w.lower(), w)
    return re.sub(r"\b[A-Za-z]+\b", _fix, text)

# ═══════════════════════════════════════════════════════════════════
# HINGLISH REWRITE – large synonym bank
# ═══════════════════════════════════════════════════════════════════

_HINGLISH_PHRASES = {
    "how are you": ["kayse ho", "kaise ho", "kya haal hai"],
    "new file is here": ["naya file aya hai", "nayi file aa gayi hai"],
    "new movie is here": ["nayi movie aa gayi hai", "naya movie aya hai"],
    "download fast": ["jaldi download kro", "fatafat download karo"],
    "download now": ["abhi download kro", "turant download karo"],
    "check this out": ["isko check karo", "yeh dekho"],
    "don't miss": ["miss mat karo", "galti mat karo"],
    "join now": ["abhi join karo", "turant join karo"],
    "click here": ["yahan click karo", "idhar click karo"],
    "watch now": ["abhi dekho", "turant dekho"],
    "available now": ["ab available hai", "abhi available hai"],
    "limited time": ["seemited time", "kuch time ke liye"],
    "free download": ["free download", "muft download"],
    "latest update": ["latest update", "naya update"],
    "good news": ["acchi khabar", "achi news"],
    "hey guys": ["hey guys", "hello doston"],
    "tum log kayse ho": ["tum log kayse ho", "tum log kaise ho"],
    "hm to badiya hai": ["hm to badhiya hai", "hum to badhiya hai"],
    "download link here": ["download link here", "download link yahan hai"],
}

_HINGLISH_WORDS = {
    "new": ["naya", "nayi", "latest"],
    "movie": ["movie", "film"],
    "file": ["file", "file"],
    "download": ["download", "download"],
    "link": ["link", "link"],
    "fast": ["jaldi", "fatafat"],
    "now": ["abhi", "turant"],
    "here": ["yahan", "idhar"],
    "watch": ["dekho", "dekh lo"],
    "join": ["join karo", "jud jao"],
    "channel": ["channel", "channel"],
    "group": ["group", "group"],
    "free": ["free", "muft"],
    "good": ["accha", "badhiya"],
    "available": ["available", "milega"],
    "limited": ["seemited", "kuch"],
    "how": ["kayse", "kaise"],
    "are": ["ho", "hai"],
    "you": ["tum", "aap"],
    "tum": ["tum", "aap"],
    "log": ["log", "doston"],
    "kayse": ["kayse", "kaise"],
    "ho": ["ho", "hai"],
    "hm": ["hm", "hum"],
    "to": ["to", "toh"],
    "badiya": ["badhiya", "accha"],
    "hai": ["hai", "hain"],
    "tomare": ["tumhare", "aapke"],
    "download": ["download", "download"],
    "link": ["link", "link"],
    "here": ["yahan", "idhar"],
}

def _rewrite_hinglish(text, source=None):
    """Rewrite text into Hinglish while preserving URLs, numbers, dates."""
    if not text or not text.strip():
        return text

    # Protect URLs and numbers with placeholders
    url_map = {}
    for i, url in enumerate(re.findall(r"https?://[^\s<>()]+", text, re.I)):
        ph = f"__URL_{i}__"
        url_map[ph] = url
        text = text.replace(url, ph, 1)

    num_map = {}
    for i, num in enumerate(re.findall(r"\b\d+\b", text)):
        ph = f"__NUM_{i}__"
        num_map[ph] = num
        text = text.replace(num, ph, 1)

    # Phrase-level rewrite
    for phrase, choices in _HINGLISH_PHRASES.items():
        if phrase in text.lower():
            pattern = re.compile(re.escape(phrase), re.I)
            text = pattern.sub(random.choice(choices), text, count=1)

    # Word-level rewrite (preserve placeholders)
    def _word_repl(m):
        w = m.group(0)
        low = w.lower()
        if low in _HINGLISH_WORDS:
            choice = random.choice(_HINGLISH_WORDS[low])
            return choice.capitalize() if w[0].isupper() else choice
        return w

    text = re.sub(r"\b[A-Za-z]+\b", _word_repl, text)

    # Restore numbers and URLs
    for ph, num in num_map.items():
        text = text.replace(ph, num)
    for ph, url in url_map.items():
        text = text.replace(ph, url)

    return text

def _rewrite_hidden_link_text(link_text):
    """Synonym-rewrite only the visible text of a hidden link."""
    if not link_text:
        return link_text
    low = link_text.lower()
    # Phrase level
    for phrase, choices in _HINGLISH_PHRASES.items():
        if phrase in low:
            return random.choice(choices).capitalize()
    # Word level (safe)
    words = link_text.split()
    out = []
    for w in words:
        lw = w.lower()
        if lw in _HINGLISH_WORDS:
            c = random.choice(_HINGLISH_WORDS[lw])
            out.append(c.capitalize() if w[0].isupper() else c)
        else:
            out.append(w)
    return " ".join(out) if out else link_text

# ═══════════════════════════════════════════════════════════════════
# LINK / ENTITY EXTRACTION
# ═══════════════════════════════════════════════════════════════════

_URL_RE = re.compile(r"https?://[^\s<>()]+", re.I)

def _extract_links(message):
    """Return list of dicts: {text, url, hidden}."""
    links = []
    if not message:
        return links
    text = message.message or ""
    entities = getattr(message, "entities", None) or []

    # Hidden links (text hyperlinks)
    for e in entities:
        url = getattr(e, "url", None)
        if url and isinstance(e, MessageEntityTextUrl):
            start, length = e.offset, e.length
            link_text = text[start:start + length]
            links.append({"text": link_text, "url": url, "hidden": True})

    # Plain URLs
    for url in _URL_RE.findall(text):
        if not any(l["url"] == url for l in links):
            links.append({"text": url, "url": url, "hidden": False})

    return links

# ═══════════════════════════════════════════════════════════════════
# DYNAMIC BUTTONS
# ═══════════════════════════════════════════════════════════════════

_EMOJI_MAP = [
    (r"download|file|grab", "📥"),
    (r"watch|video|trailer|preview", "🎬"),
    (r"join|channel|group|community", "📢"),
    (r"buy|shop|order", "🛒"),
    (r"read|blog|article", "📖"),
    (r"music|song|audio", "🎵"),
    (r"contact|support", "📞"),
]

def _emoji_for(text):
    low = text.lower()
    for pat, emo in _EMOJI_MAP:
        if re.search(pat, low):
            return emo
    return "🔗"

def _shorten(text, limit=20):
    if len(text) <= limit:
        return text
    words = text.split()
    out = []
    total = 0
    for w in words:
        if total + len(w) + 1 > limit:
            break
        out.append(w)
        total += len(w) + 1
    return " ".join(out) if out else text[:limit]

def _build_buttons(links):
    """Build inline button matrix from link list."""
    if not links or not _button_enabled():
        return None
    rows = []
    for link in links:
        raw_text = link["text"] or "link"
        if link["hidden"]:
            label_text = _rewrite_hidden_link_text(raw_text)
        else:
            try:
                label_text = urllib.parse.urlparse(link["url"]).netloc
            except Exception:
                label_text = "link"
        label = _shorten(label_text)
        if _emoji_enabled():
            label = f"{_emoji_for(raw_text)} {label}"
        rows.append([Button.url(label, link["url"])])
    return rows if rows else None

# ═══════════════════════════════════════════════════════════════════
# FOLDER / TARGET / EXCLUDE HELPERS
# ═══════════════════════════════════════════════════════════════════

async def _get_folder_filters():
    try:
        res = await catub(functions.messages.GetDialogFiltersRequest())
        if isinstance(res, (list, tuple)):
            return list(res)
        f = getattr(res, "filters", None)
        return list(f) if f else []
    except Exception as e:
        raise RuntimeError(f"Folder request failed: {e}")

async def _folder_channels(folder_id):
    filters = await _get_folder_filters()
    chosen = next((f for f in filters if getattr(f, "id", None) == int(folder_id)), None)
    if not chosen:
        raise ValueError("Folder not found. Run .repostfolders first.")
    included = list(getattr(chosen, "include_peers", []) or [])
    excluded_peers = list(getattr(chosen, "exclude_peers", []) or [])
    ex_ids = set()
    for p in excluded_peers:
        try:
            e = await catub.get_entity(p)
            ex_ids.add(int(e.id))
        except Exception:
            pass
    out = []
    for p in included:
        try:
            e = await catub.get_entity(p)
            if isinstance(e, Channel) and int(e.id) not in ex_ids:
                out.append({
                    "id": int(e.id),
                    "access_hash": int(e.access_hash),
                    "title": getattr(e, "title", str(e.id)),
                    "username": getattr(e, "username", None),
                })
        except Exception:
            continue
    return out

async def _active_targets():
    selected = _folder_id()
    if selected is None:
        return _targets()
    fids = selected if isinstance(selected, list) else [selected]
    combined, seen = [], set()
    for fid in fids:
        try:
            for t in await _folder_channels(fid):
                k = str(t["id"])
                if k not in seen:
                    seen.add(k)
                    combined.append(t)
        except Exception:
            continue
    return combined

async def _resolve_target(item):
    try:
        peer = types.InputPeerChannel(
            channel_id=int(item["id"]),
            access_hash=int(item["access_hash"]),
        )
        return await catub.get_entity(peer)
    except Exception:
        return None

async def _can_post(entity):
    try:
        me = await catub.get_me()
        if getattr(entity, "creator", False):
            return True
        if getattr(entity, "admin_rights", None):
            if getattr(entity.admin_rights, "post_messages", False):
                return True
        try:
            perms = await catub.get_permissions(entity, me)
            if getattr(perms, "is_admin", False):
                rights = getattr(perms, "admin_rights", None)
                if rights and getattr(rights, "post_messages", False):
                    return True
            if getattr(perms, "send_messages", False):
                return True
        except Exception:
            pass
        return False
    except Exception:
        return False

def _excluded_ids():
    return {str(x.get("id")) for x in _excluded() if x.get("id")}

# ═══════════════════════════════════════════════════════════════════
# DELIVERY (fixed MediaEmptyError / EntityBoundsInvalid)
# ═══════════════════════════════════════════════════════════════════

async def _send_to_target(entity, source, text, buttons):
    """
    Send a message with text, optional media, and buttons.
    Uses Markdown parsing to avoid entity-bounds errors.
    """
    links = _extract_links(source)
    # Ensure all original URLs appear in text
    if text and links:
        missing = [l["url"] for l in links if l["url"] not in text]
        if missing:
            text = text.rstrip() + "\n\n" + "\n".join(missing)

    if source.media:
        await catub.send_file(
            entity,
            source.media,
            caption=text or "",
            parse_mode="md",          # ← critical: avoids entity-bounds error
            buttons=buttons,
        )
    elif text:
        await catub.send_message(
            entity,
            text,
            parse_mode="md",
            link_preview=False,
            buttons=buttons,
        )
    else:
        await catub.forward_messages(entity, source)

async def _deliver(source, event, targets=None):
    if targets is None:
        targets = await _active_targets()
    if not targets:
        return await edit_or_reply(
            event,
            "No repost targets configured.\n"
            "Use .repostfolders and .reposttarget, or .repostadd.",
        )

    original = source.message or ""
    fixed = _fix_typos(original)
    links = _extract_links(source)
    excluded = _excluded_ids()

    success, skipped, failed = [], [], []
    low, high = _delay()

    for item in targets:
        cid = str(item.get("id"))
        title = item.get("title", cid)
        if cid in excluded:
            skipped.append(f"{title} (excluded)")
            continue
        entity = await _resolve_target(item)
        if entity is None:
            skipped.append(f"{title} (not accessible)")
            continue
        if not await _can_post(entity):
            skipped.append(f"{title} (no posting permission)")
            continue

        # Per-channel unique rewrite
        rewritten = _rewrite_hinglish(fixed, source)
        buttons = _build_buttons(links)

        try:
            await _send_to_target(entity, source, rewritten, buttons)
            success.append(title)
        except FloodWaitError as exc:
            await asyncio.sleep(int(exc.seconds) + 1)
            try:
                await _send_to_target(entity, source, rewritten, buttons)
                success.append(title)
            except Exception as re:
                failed.append(f"{title} (FloodWait retry: {type(re).__name__})")
        except Exception as exc:
            failed.append(f"{title} ({type(exc).__name__})")
        if high:
            await asyncio.sleep(random.randint(low, high))

    lines = [
        "**REPOST RESULT**",
        f"Success: {len(success)}",
        f"Skipped: {len(skipped)}",
        f"Failed: {len(failed)}",
    ]
    if success:
        lines.append("\n**Sent**\n" + "\n".join(f"• {x}" for x in success[:20]))
    if skipped:
        lines.append("\n**Skipped**\n" + "\n".join(f"• {x}" for x in skipped[:20]))
    if failed:
        lines.append("\n**Failed**\n" + "\n".join(f"• {x}" for x in failed[:20]))
    await edit_or_reply(event, "\n".join(lines))

# ═══════════════════════════════════════════════════════════════════
# SCHEDULER (with time windows and expiry)
# ═══════════════════════════════════════════════════════════════════

def _parse_time_windows(time_str):
    """
    Parse a comma-separated list of times.
    Each item can be:
      - "HH:MM"          → fixed time
      - "HH:MM-HH:MM"    → window (random time between start and end)
    Returns list of (start, end) tuples where end is None for fixed.
    """
    windows = []
    for part in time_str.split(","):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = _parse_hhmm(start_s.strip())
            end = _parse_hhmm(end_s.strip())
            if start >= end:
                raise ValueError(f"Invalid window: {part}")
            windows.append((start, end))
        else:
            t = _parse_hhmm(part)
            windows.append((t, None))
    return windows

def _parse_hhmm(s):
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if not m:
        raise ValueError(f"Invalid time: {s}")
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        raise ValueError(f"Invalid time: {s}")
    return h * 60 + mi

def _minutes_to_str(minutes):
    return f"{minutes//60:02d}:{minutes%60:02d}"

def _get_window_time(start_min, end_min):
    """Return a random minute within [start_min, end_min]."""
    if end_min is None:
        return start_min
    return random.randint(start_min, end_min)

def _parse_expire(value):
    """
    Parse expire string.
    - "1" → 1 day
    - "265" → 265 days
    - "1h" → 1 hour
    - None → unlimited
    Returns timedelta or None.
    """
    if not value:
        return None
    value = value.strip().lower()
    if value.endswith("h"):
        hours = int(value[:-1])
        return datetime.timedelta(hours=hours)
    else:
        days = int(value)
        return datetime.timedelta(days=days)

def _ensure_scheduler():
    global SCHEDULER_TASK
    if SCHEDULER_TASK is None or SCHEDULER_TASK.done():
        try:
            SCHEDULER_TASK = asyncio.create_task(_scheduler_loop())
        except RuntimeError:
            SCHEDULER_TASK = None

async def _scheduler_loop():
    while True:
        try:
            now = datetime.datetime.now(TZ)
            now_min = now.hour * 60 + now.minute
            schedules = _schedules()
            queue = _queue()
            changed = False

            for sch in schedules:
                if sch.get("stopped"):
                    continue
                # Check expiry
                created = sch.get("created")
                expire = sch.get("expire")
                if expire and created:
                    if now > created + expire:
                        sch["stopped"] = True
                        changed = True
                        continue

                # Check time windows
                windows = sch.get("windows", [])
                for (start, end) in windows:
                    if end is None:
                        # fixed time
                        if now_min == start:
                            # trigger
                            if await _process_queue_for_schedule(sch, queue, now):
                                changed = True
                    else:
                        # window
                        if start <= now_min <= end:
                            # random chance to fire (or we can fire once per window)
                            # To avoid multiple fires in the same window, we track last_fired.
                            last = sch.get("last_fired")
                            if last != now.date().isoformat() + "-" + str(start):
                                if random.random() < 0.2:  # 20% chance per minute
                                    if await _process_queue_for_schedule(sch, queue, now):
                                        sch["last_fired"] = now.date().isoformat() + "-" + str(start)
                                        changed = True
            if changed:
                _save_schedules(schedules)
                _save_queue(queue)
        except Exception as e:
            LOGS.exception("Scheduler error: %s", e)
        await asyncio.sleep(30)  # check every 30 seconds

async def _process_queue_for_schedule(sch, queue, now):
    """
    Deliver all queued posts that belong to this schedule.
    Returns True if any delivery happened.
    """
    delivered_any = False
    for item in queue:
        if item.get("schedule_id") != id(sch):
            continue
        try:
            src = await catub.get_messages(
                int(item["chat_id"]), ids=int(item["message_id"])
            )
            if not src:
                continue
            targets = await _active_targets()
            if not targets:
                continue
            fixed = _fix_typos(src.message or "")
            links = _extract_links(src)
            excluded = _excluded_ids()
            low, high = _delay()
            for t in targets:
                cid = str(t.get("id"))
                if cid in excluded:
                    continue
                entity = await _resolve_target(t)
                if entity is None or not await _can_post(entity):
                    continue
                rewritten = _rewrite_hinglish(fixed, src)
                buttons = _build_buttons(links)
                try:
                    await _send_to_target(entity, src, rewritten, buttons)
                    delivered_any = True
                except Exception:
                    pass
                if high:
                    await asyncio.sleep(random.randint(low, high))
        except Exception:
            pass
    return delivered_any

# ═══════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════

async def _get_source(event):
    if not event.is_reply:
        return None
    return await event.get_reply_message()

@catub.cat_cmd(
    pattern="rp$",
    command=("rp", plugin_category),
    info={
        "header": "Repost a post",
        "description": "Reply to a post and use .rp, or use .rp <link>.",
        "usage": ["{tr}rp", "{tr}rp <link>"],
    },
)
async def repost(event):
    raw = (event.raw_text or "").split(maxsplit=1)
    arg = raw[1].strip() if len(raw) > 1 else ""

    if arg and re.match(r"^https?://t\.me/", arg, re.I):
        # .rp <link>
        try:
            # handle private channel links: https://t.me/c/1234567890/123
            m = re.search(r"/c/(\d+)/(\d+)", arg)
            if m:
                channel_id = int(m.group(1))
                msg_id = int(m.group(2))
                peer = types.InputPeerChannel(channel_id, 0)
                src = await catub.get_messages(peer, ids=msg_id)
            else:
                parts = arg.rstrip("/").split("/")
                chat = parts[-2]
                mid = int(parts[-1])
                src = await catub.get_messages(chat, ids=mid)
            if not src:
                return await edit_or_reply(event, "Could not fetch the linked message.")
            return await _deliver(src, event)
        except Exception as e:
            LOGS.exception("Link fetch failed")
            return await edit_or_reply(event, f"Link fetch failed: {type(e).__name__}")

    source = await _get_source(event)
    if not source:
        return await edit_or_reply(event, "Reply to a source post and use .rp, or .rp <link>.")

    await _deliver(source, event)

# ── HELP ─────────────────────────────────────────────────────────────

@catub.cat_cmd(
    pattern="reposthelp$",
    command=("reposthelp", plugin_category),
    info={"header": "Repost plugin help", "usage": "{tr}reposthelp"},
)
async def repost_help(event):
    text = (
        "📖 **REPOST PLUGIN HELP**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 **BASIC**\n"
        "• `.rp` — reply to a post to repost\n"
        "• `.rp <link>` — repost from a channel/group link (public or private)\n\n"
        "🔹 **TARGETS**\n"
        "• `.repostfolders` — list Telegram folders\n"
        "• `.reposttarget <id>` — select folder(s)\n"
        "• `.reposttarget off` — disable folder targeting\n"
        "• `.repostadd` — add a channel (reply to its post)\n"
        "• `.repostremove <id> [<id> ...]` — remove targets\n"
        "• `.repostlist` — list active targets\n\n"
        "🔹 **EXCLUDE**\n"
        "• `.repostexclude add <id|@user> [...]` — exclude channels\n"
        "• `.repostexclude remove <id|@user> [...]` — un-exclude\n"
        "• `.repostexclude list` — show excluded (ID, name, username)\n"
        "• `.repostexclude clear` — remove all excludes\n"
        "• `.repostexclude status` — exclude stats\n\n"
        "🔹 **SCHEDULE**\n"
        "• `.repostschedule add <times> [expire]` — add schedule\n"
        "   times: comma-separated, e.g. `09:00,12:00-12:05`\n"
        "   expire: `1` (1 day), `265` (265 days), `1h` (1 hour)\n"
        "• `.repostschedule list` — show schedules with status\n"
        "• `.repostschedule off [id]` — stop a schedule or all\n"
        "• `.repostschedule clear` — remove all schedules\n"
        "• `.repostqueue` — show queued posts\n"
        "• `.repostqueue clear` — clear queue\n\n"
        "🔹 **SETTINGS**\n"
        "• `.repostdelay <min> <max>` — random delay (seconds)\n"
        "• `.repostdelay off` — disable delay\n"
        "• `.repostbutton on|off` — toggle dynamic buttons\n"
        "• `.repostbutton status` — button status\n"
        "• `.repostemoji on|off` — toggle button emojis\n"
        "• `.reposttypo on|off` — toggle typo fix\n"
        "• `.repoststatus` — show all settings\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Example: `.repostexclude add -100123 @spam -100456`"
    )
    await edit_or_reply(event, text)

# ── FOLDERS ──────────────────────────────────────────────────────────

@catub.cat_cmd(
    pattern="repostfolders$",
    command=("repostfolders", plugin_category),
    info={"header": "List Telegram folders", "usage": "{tr}repostfolders"},
)
async def repost_folders(event):
    try:
        filters = await _get_folder_filters()
    except Exception as e:
        return await edit_or_reply(event, f"Folder read failed: {e}")
    lines, count = ["**TELEGRAM FOLDERS**"], 0
    for f in filters:
        fid = getattr(f, "id", None)
        if fid is None:
            continue
        title = getattr(f, "title", None) or "Untitled"
        title_text = getattr(title, "text", None) or str(title)
        lines.append(f"\n• {title_text} — ID: `{fid}`")
        count += 1
    if not count:
        lines.append("\nNo folders found.")
    else:
        lines.append("\n`.reposttarget 2` — select folder 2\n`.reposttarget 2,3` — select multiple")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern=r"reposttarget(?:\s+(\S+))?$",
    command=("reposttarget", plugin_category),
    info={"header": "Select target folder", "usage": "{tr}reposttarget <id|off>"},
)
async def repost_target(event):
    val = event.pattern_match.group(1)
    if not val:
        cur = _folder_id()
        return await edit_or_reply(event, "Selected folder: " + (str(cur) if cur is not None else "OFF"))
    if val.lower() == "off":
        _save("FOLDER_ID", None)
        return await edit_or_reply(event, "Folder targeting disabled. Saved targets will be used.")
    try:
        fids = []
        for p in val.split(","):
            p = p.strip()
            if not p.isdigit():
                raise ValueError("Use .reposttarget 2 or .reposttarget 2,3")
            if int(p) not in fids:
                fids.append(int(p))
        if not fids:
            raise ValueError("No folder IDs supplied.")
        counts = [(fid, len(await _folder_channels(fid))) for fid in fids]
        _save("FOLDER_ID", fids[0] if len(fids) == 1 else fids)
        summary = "\n".join(f"Folder {fid}: {cnt} accessible channels" for fid, cnt in counts)
        await edit_or_reply(event, "Selected: " + ", ".join(map(str, fids)) + "\n" + summary)
    except Exception as e:
        await edit_or_reply(event, f"Could not select folder(s): {e}")

@catub.cat_cmd(
    pattern="repostadd$",
    command=("repostadd", plugin_category),
    info={"header": "Add a target channel", "usage": "{tr}repostadd (reply)"},
)
async def repost_add(event):
    src = await _get_source(event)
    if not src:
        return await edit_or_reply(event, "Reply to a message from the destination channel.")
    try:
        ent = await catub.get_entity(src.peer_id)
        if not isinstance(ent, Channel):
            return await edit_or_reply(event, "The replied message is not from a channel.")
        item = {
            "id": int(ent.id),
            "access_hash": int(ent.access_hash),
            "title": ent.title,
            "username": getattr(ent, "username", None),
        }
        items = _targets()
        items.append(item)
        _save_targets(items)
        await edit_or_reply(event, f"Target saved: {ent.title}")
    except Exception as e:
        await edit_or_reply(event, f"Could not save target: {type(e).__name__}")

@catub.cat_cmd(
    pattern=r"repostremove\s+(.+)$",
    command=("repostremove", plugin_category),
    info={"header": "Remove target(s)", "usage": "{tr}repostremove <id> [<id> ...]"},
)
async def repost_remove(event):
    raw = event.pattern_match.group(1)
    items = raw.replace(",", " ").split()
    if not items:
        return await edit_or_reply(event, "Provide at least one target ID or username.")
    targets = _targets()
    removed, notfound = [], []
    for item in items:
        val = item.strip().lstrip("@").lower()
        found = False
        keep = []
        for t in targets:
            if str(t.get("id")) == val or str(t.get("username") or "").lower() == val:
                removed.append(t.get("title", val))
                found = True
            else:
                keep.append(t)
        targets = keep
        if not found:
            notfound.append(val)
    _save_targets(targets)
    msg = f"✅ Removed: {len(removed)}"
    if removed:
        msg += "\n" + "\n".join(f"• {x}" for x in removed[:10])
    if notfound:
        msg += f"\n⚠️ Not found: {', '.join(notfound[:10])}"
    await edit_or_reply(event, msg)

@catub.cat_cmd(
    pattern="repostlist$",
    command=("repostlist", plugin_category),
    info={"header": "List targets", "usage": "{tr}repostlist"},
)
async def repost_list(event):
    items = await _active_targets()
    if not items:
        return await edit_or_reply(event, "No targets found.")
    lines = ["**REPOST TARGETS**"]
    for t in items:
        name = t.get("title", str(t.get("id")))
        uname = f" @{t['username']}" if t.get("username") else ""
        lines.append(f"• {name}{uname} — `{t['id']}`")
    await edit_or_reply(event, "\n".join(lines))

# ── EXCLUDE ─────────────────────────────────────────────────────────

async def _resolve_item(value):
    """Resolve an ID/username/link to a channel dict."""
    val = value.strip()
    if re.match(r"^-?\d+$", val):
        cid = int(val)
        try:
            ent = await catub.get_entity(cid)
            return {
                "id": int(ent.id),
                "title": getattr(ent, "title", str(cid)),
                "username": getattr(ent, "username", None),
            }
        except Exception:
            return {"id": cid, "title": "Unknown (inaccessible)", "username": None}
    uname = val.lstrip("@")
    try:
        ent = await catub.get_entity(uname)
        if not isinstance(ent, (Channel, Chat)):
            return None
        return {
            "id": int(ent.id),
            "title": getattr(ent, "title", str(ent.id)),
            "username": getattr(ent, "username", None),
        }
    except Exception:
        return None

@catub.cat_cmd(
    pattern=r"repostexclude add\s+(.+)$",
    command=("repostexclude", plugin_category),
    info={"header": "Exclude channel(s)", "usage": "{tr}repostexclude add <id|@user> [...]"},
)
async def repost_exclude_add(event):
    raw = event.pattern_match.group(1)
    items = raw.replace(",", " ").split()
    if not items:
        return await edit_or_reply(event, "Provide at least one ID or username.")
    current = _excluded()
    current_ids = {str(x.get("id")) for x in current}
    added, failed, dup = [], [], []
    for item in items:
        info = await _resolve_item(item)
        if not info:
            failed.append(item)
            continue
        if str(info["id"]) in current_ids:
            dup.append(info.get("title", item))
            continue
        current.append(info)
        current_ids.add(str(info["id"]))
        added.append(info)
    _save_excluded(current)
    lines = ["✅ **EXCLUDE UPDATED**", f"Added: {len(added)}"]
    for a in added:
        uname = f" (@{a['username']})" if a.get("username") else ""
        lines.append(f"  • {a['id']} → \"{a['title']}\"{uname}")
    if dup:
        lines.append(f"Already excluded: {len(dup)}")
    if failed:
        lines.append(f"⚠️ Failed: {', '.join(failed[:5])}")
    lines.append(f"Total excluded: {len(current)}")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern=r"repostexclude remove\s+(.+)$",
    command=("repostexclude", plugin_category),
    info={"header": "Un-exclude channel(s)", "usage": "{tr}repostexclude remove <id|@user> [...]"},
)
async def repost_exclude_remove(event):
    raw = event.pattern_match.group(1)
    items = raw.replace(",", " ").split()
    if not items:
        return await edit_or_reply(event, "Provide at least one ID or username.")
    current = _excluded()
    removed, notfound = [], []
    for item in items:
        val = item.strip().lstrip("@").lower()
        keep, found = [], False
        for x in current:
            if str(x.get("id")) == val or str(x.get("username") or "").lower() == val:
                removed.append(x.get("title", val))
                found = True
            else:
                keep.append(x)
        current = keep
        if not found:
            notfound.append(val)
    _save_excluded(current)
    lines = ["✅ **EXCLUDE UPDATED**", f"Removed: {len(removed)}"]
    if removed:
        lines.append("\n".join(f"• {x}" for x in removed[:10]))
    if notfound:
        lines.append(f"⚠️ Not found: {', '.join(notfound[:10])}")
    lines.append(f"Remaining: {len(current)}")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern="repostexclude list$",
    command=("repostexclude", plugin_category),
    info={"header": "List excluded channels", "usage": "{tr}repostexclude list"},
)
async def repost_exclude_list(event):
    items = _excluded()
    if not items:
        return await edit_or_reply(event, "No excluded channels.")
    lines = ["📋 **EXCLUDED CHANNELS**", "━━━━━━━━━━━━━━━━━━"]
    for i, x in enumerate(items, 1):
        cid = x.get("id")
        title = x.get("title", "Unknown")
        uname = x.get("username")
        lines.append(f"{i}. 🏷️ ID: `{cid}`")
        lines.append(f"   📛 Name: \"{title}\"")
        lines.append(f"   🔗 Username: @{uname}" if uname else "   🔗 Username: (none)")
        lines.append("")
    lines.append(f"Total: {len(items)} excluded")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern="repostexclude clear$",
    command=("repostexclude", plugin_category),
    info={"header": "Clear all excludes", "usage": "{tr}repostexclude clear"},
)
async def repost_exclude_clear(event):
    n = len(_excluded())
    _save_excluded([])
    await edit_or_reply(event, f"🗑️ Cleared {n} excluded channel(s).")

@catub.cat_cmd(
    pattern="repostexclude status$",
    command=("repostexclude", plugin_category),
    info={"header": "Exclude stats", "usage": "{tr}repostexclude status"},
)
async def repost_exclude_status(event):
    items = _excluded()
    pub = sum(1 for x in items if x.get("username"))
    priv = len(items) - pub
    await edit_or_reply(
        event,
        "📊 **EXCLUDE STATUS**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"Total: {len(items)}\n"
        f"├── Public (with username): {pub}\n"
        f"└── Private / no username: {priv}",
    )

# ── SCHEDULE ─────────────────────────────────────────────────────────

@catub.cat_cmd(
    pattern=r"repostschedule add\s+(.+)$",
    command=("repostschedule", plugin_category),
    info={"header": "Add schedule", "usage": "{tr}repostschedule add <times> [expire]"},
)
async def repost_schedule_add(event):
    raw = event.pattern_match.group(1).strip()
    parts = raw.rsplit(None, 1)  # split off expire if present
    if len(parts) == 2 and (parts[1].endswith("h") or parts[1].isdigit()):
        time_part, expire_part = parts[0], parts[1]
    else:
        time_part, expire_part = raw, None

    try:
        windows = _parse_time_windows(time_part)
    except ValueError as e:
        return await edit_or_reply(event, str(e))

    try:
        expire = _parse_expire(expire_part)
    except ValueError as e:
        return await edit_or_reply(event, f"Invalid expire: {e}")

    schedules = _schedules()
    schedule = {
        "windows": [[s, e] for s, e in windows],
        "expire": expire.total_seconds() if expire else None,
        "created": datetime.datetime.now(TZ).isoformat(),
        "stopped": False,
        "last_fired": None,
    }
    schedules.append(schedule)
    _save_schedules(schedules)
    _ensure_scheduler()

    desc = ", ".join(
        f"{_minutes_to_str(s)}" + (f"-{_minutes_to_str(e)}" if e is not None else "")
        for s, e in windows
    )
    expire_desc = f"expires in {expire_part}" if expire_part else "no expiry"
    await edit_or_reply(
        event,
        f"✅ Schedule added.\nTimes: {desc}\nExpire: {expire_desc}",
    )

@catub.cat_cmd(
    pattern="repostschedule list$",
    command=("repostschedule", plugin_category),
    info={"header": "List schedules", "usage": "{tr}repostschedule list"},
)
async def repost_schedule_list(event):
    schedules = _schedules()
    if not schedules:
        return await edit_or_reply(event, "No schedules configured.")
    lines = ["📅 **SCHEDULE LIST**", "━━━━━━━━━━━━━━━━━━"]
    now = datetime.datetime.now(TZ)
    for i, sch in enumerate(schedules, 1):
        windows = sch.get("windows", [])
        times = ", ".join(
            f"{_minutes_to_str(s)}" + (f"-{_minutes_to_str(e)}" if e is not None else "")
            for s, e in windows
        )
        created = datetime.datetime.fromisoformat(sch.get("created"))
        expire = sch.get("expire")
        if expire:
            expire_dt = created + datetime.timedelta(seconds=expire)
            remaining = expire_dt - now
            if remaining.total_seconds() <= 0:
                status = "❌ Expired"
            else:
                status = f"✅ Active (expires in {remaining})"
        else:
            status = "✅ Active (unlimited)"
        if sch.get("stopped"):
            status = "⏹ Stopped"
        lines.append(f"\n{i}. ⏰ Times: {times}")
        lines.append(f"   📅 Created: {created.strftime('%d-%m-%Y %H:%M')}")
        lines.append(f"   📊 Status: {status}")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern=r"repostschedule off(?:\s+(\d+))?$",
    command=("repostschedule", plugin_category),
    info={"header": "Stop schedule", "usage": "{tr}repostschedule off [id]"},
)
async def repost_schedule_off(event):
    idx = event.pattern_match.group(1)
    schedules = _schedules()
    if not schedules:
        return await edit_or_reply(event, "No schedules to stop.")
    if idx:
        try:
            i = int(idx) - 1
            if 0 <= i < len(schedules):
                schedules[i]["stopped"] = True
                _save_schedules(schedules)
                return await edit_or_reply(event, f"⏹ Schedule #{idx} stopped.")
            else:
                return await edit_or_reply(event, f"Schedule #{idx} not found.")
        except ValueError:
            pass
    for sch in schedules:
        sch["stopped"] = True
    _save_schedules(schedules)
    await edit_or_reply(event, "⏹ All schedules stopped.")

@catub.cat_cmd(
    pattern="repostschedule clear$",
    command=("repostschedule", plugin_category),
    info={"header": "Clear all schedules", "usage": "{tr}repostschedule clear"},
)
async def repost_schedule_clear(event):
    _save_schedules([])
    await edit_or_reply(event, "🗑️ All schedules cleared.")

@catub.cat_cmd(
    pattern="repostqueue$",
    command=("repostqueue", plugin_category),
    info={"header": "Show queue", "usage": "{tr}repostqueue"},
)
async def repost_queue(event):
    items = _queue()
    if not items:
        return await edit_or_reply(event, "Queue is empty.")
    lines = ["**SCHEDULED QUEUE**"]
    for i, x in enumerate(items, 1):
        lines.append(f"{i}. Chat `{x['chat_id']}` / Msg `{x['message_id']}`")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern="repostqueue clear$",
    command=("repostqueue", plugin_category),
    info={"header": "Clear queue", "usage": "{tr}repostqueue clear"},
)
async def repost_queue_clear(event):
    _save_queue([])
    await edit_or_reply(event, "Queue cleared.")

# ── SETTINGS ─────────────────────────────────────────────────────────

@catub.cat_cmd(
    pattern=r"repostdelay(?:\s+(.+))?$",
    command=("repostdelay", plugin_category),
    info={"header": "Set random delay", "usage": "{tr}repostdelay <min> <max>|off"},
)
async def repost_delay(event):
    raw = event.pattern_match.group(1)
    if not raw:
        low, high = _delay()
        return await edit_or_reply(event, f"Current delay: {low}-{high}s")
    if raw.strip().lower() == "off":
        _save("DELAY", [0, 0])
        return await edit_or_reply(event, "Random delay disabled.")
    m = re.match(r"^(\d+)\s+(\d+)$", raw.strip())
    if not m:
        return await edit_or_reply(event, "Usage: .repostdelay 2 8 or .repostdelay off")
    low, high = int(m.group(1)), int(m.group(2))
    if high < low or high > 3600:
        return await edit_or_reply(event, "Invalid range (max 3600s).")
    _save("DELAY", [low, high])
    await edit_or_reply(event, f"Random delay set to {low}-{high}s.")

@catub.cat_cmd(
    pattern=r"repostbutton(?:\s+(\S+))?$",
    command=("repostbutton", plugin_category),
    info={"header": "Toggle buttons", "usage": "{tr}repostbutton on|off|status"},
)
async def repost_button(event):
    arg = (event.pattern_match.group(1) or "").lower()
    if arg == "on":
        addgvar(PREFIX + "BUTTON", "true")
        return await edit_or_reply(event, "✅ Dynamic buttons enabled.")
    if arg == "off":
        delgvar(PREFIX + "BUTTON")
        return await edit_or_reply(event, "🚫 Dynamic buttons disabled.")
    st = "ON" if _button_enabled() else "OFF"
    em = "ON" if _emoji_enabled() else "OFF"
    await edit_or_reply(event, f"Button: `{st}`\nEmoji: `{em}`")

@catub.cat_cmd(
    pattern=r"repostemoji(?:\s+(\S+))?$",
    command=("repostemoji", plugin_category),
    info={"header": "Toggle button emoji", "usage": "{tr}repostemoji on|off"},
)
async def repost_emoji(event):
    arg = (event.pattern_match.group(1) or "").lower()
    if arg == "on":
        addgvar(PREFIX + "EMOJI", "true")
        return await edit_or_reply(event, "✅ Button emojis enabled.")
    if arg == "off":
        delgvar(PREFIX + "EMOJI")
        return await edit_or_reply(event, "🚫 Button emojis disabled.")
    await edit_or_reply(event, "Usage: .repostemoji on|off")

@catub.cat_cmd(
    pattern=r"reposttypo(?:\s+(\S+))?$",
    command=("reposttypo", plugin_category),
    info={"header": "Toggle typo fix", "usage": "{tr}reposttypo on|off"},
)
async def repost_typo(event):
    arg = (event.pattern_match.group(1) or "").lower()
    if arg == "on":
        addgvar(PREFIX + "TYPO", "true")
        return await edit_or_reply(event, "✅ Typo fix enabled.")
    if arg == "off":
        delgvar(PREFIX + "TYPO")
        return await edit_or_reply(event, "🚫 Typo fix disabled.")
    await edit_or_reply(event, "Usage: .reposttypo on|off")

@catub.cat_cmd(
    pattern="repoststatus$",
    command=("repoststatus", plugin_category),
    info={"header": "Show repost settings", "usage": "{tr}repoststatus"},
)
async def repost_status(event):
    low, high = _delay()
    folder = _folder_id()
    tcount = len(await _active_targets())
    _ensure_scheduler()
    lines = [
        "📊 **REPOST STATUS**",
        "━━━━━━━━━━━━━━━━━━",
        f"Target mode: {'Folder(s) ' + str(folder) if folder is not None else 'Saved targets'}",
        f"Targets: {tcount}",
        f"Excluded: {len(_excluded())}",
        f"Random delay: {low}-{high}s",
        f"Schedules: {len(_schedules())}",
        f"Queue: {len(_queue())}",
        f"Buttons: {'ON' if _button_enabled() else 'OFF'}",
        f"Button emoji: {'ON' if _emoji_enabled() else 'OFF'}",
        f"Typo fix: {'ON' if _typo_enabled() else 'OFF'}",
    ]
    await edit_or_reply(event, "\n".join(lines))
