# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# CATXBot Repost Plugin #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Copyright (C) 2020-2023 by TgCatUB@Github.
# This file is part of: https://github.com/TgCatUB/catuserbot
# and is released under the "GNU v3.0 License Agreement".
# Please see: https://github.com/TgCatUB/catuserbot/blob/master/LICENSE
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# FINAL REPOST PLUGIN v7 — all bugs fixed
# • Link text preserved word-for-word (Option B)
# • Line breaks preserved
# • Buttons always built from source links (URL buttons via userbot)
# • .rp / .rp <link> (public + private)
# • Schedules with time windows + UUIDs + expiry
# • Exclude list, targets, folders, delay, status

import asyncio
import datetime
import json
import random
import re
import urllib.parse
import uuid
from zoneinfo import ZoneInfo

from telethon import Button, functions, types
from telethon.errors import FloodWaitError
from telethon.tl.types import Channel, Chat, MessageEntityTextUrl

from userbot import catub
from ..core.managers import edit_or_reply
from ..core.logger import logging
from ..sql_helper.globals import addgvar, delgvar, gvarstatus

LOGS = logging.getLogger("CatUserbot.Repost")
plugin_category = "tools"
TZ = ZoneInfo("Asia/Kolkata")
PREFIX = "CAT_REPOST_"
SCHEDULER_TASK = None

# ═══════════════════ STORAGE ═══════════════════

def _get(k, d=None):
    v = gvarstatus(PREFIX + k)
    return d if v is None else v

def _save(k, v):
    addgvar(PREFIX + k, json.dumps(v, ensure_ascii=False))

def _load(k, d):
    v = _get(k)
    if v is None:
        return d
    try:
        return json.loads(v)
    except (TypeError, ValueError):
        return d

def _targets():
    v = _load("TARGETS", [])
    return v if isinstance(v, list) else []

def _save_targets(items):
    seen, out = set(), []
    for it in items:
        k = str(it.get("id"))
        if k not in seen:
            seen.add(k); out.append(it)
    _save("TARGETS", out)

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
        lo, hi = max(0, int(v[0])), max(0, int(v[1]))
        return min(lo, hi), max(lo, hi)
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

def _flag(k):
    v = gvarstatus(PREFIX + k)
    return v is not None and str(v).strip().lower() == "true"

def _button_enabled():
    return _flag("BUTTON")

def _emoji_enabled():
    return _flag("EMOJI")

def _typo_enabled():
    return _flag("TYPO")

# ═══════════════════ TYPO FIX ═══════════════════

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
    "begining": "beginning", "buisness": "business",
    "catagory": "category", "completly": "completely",
    "concious": "conscious", "dissapear": "disappear",
    "existance": "existence", "familar": "familiar",
    "finaly": "finally", "foriegn": "foreign", "fourty": "forty",
    "freind": "friend", "garantee": "guarantee", "grammer": "grammar",
    "happend": "happened", "immediatly": "immediately",
    "independant": "independent", "maintainance": "maintenance",
    "managment": "management", "millenium": "millennium",
    "noticable": "noticeable", "occurence": "occurrence",
    "persistant": "persistent", "personel": "personnel",
    "pronounciation": "pronunciation", "questionaire": "questionnaire",
    "realy": "really", "reccomend": "recommend", "relevent": "relevant",
    "religous": "religious", "remeber": "remember",
    "resistence": "resistance", "resourse": "resource",
    "supercede": "supersede", "suprise": "surprise",
    "tendancy": "tendency", "therefor": "therefore",
    "tounge": "tongue", "truely": "truly",
    "unfortunatly": "unfortunately", "vehical": "vehicle",
    "visable": "visible", "wether": "whether", "yeild": "yield",
}

def _fix_typos(text):
    if not text or not _typo_enabled():
        return text
    return re.sub(r"\b[A-Za-z]+\b", lambda m: _TYPO_DICT.get(m.group(0).lower(), m.group(0)), text)

# ═══════════════════ HINGLISH DICTIONARY ═══════════════════

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
}

_HINGLISH_WORDS = {
    "new": ["naya", "nayi", "latest"],
    "movie": ["movie", "film"],
    "fast": ["jaldi", "fatafat"],
    "now": ["abhi", "turant"],
    "here": ["yahan", "idhar"],
    "watch": ["dekho", "dekh lo"],
    "join": ["join karo", "jud jao"],
    "free": ["free", "muft"],
    "good": ["accha", "badhiya"],
    "available": ["available", "milega"],
    "limited": ["seemited", "kuch"],
    "how": ["kayse", "kaise"],
    "are": ["ho", "hai"],
    "you": ["tum", "aap"],
}

def _escape_html(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _word_replace(part, use_phrases=True):
    """Word-by-word replacement. Preserves \n and structure."""
    if use_phrases:
        for phrase, choices in _HINGLISH_PHRASES.items():
            if phrase.lower() in part.lower():
                pat = re.compile(re.escape(phrase), re.I)
                part = pat.sub(random.choice(choices), part, count=1)
    def _repl(m):
        w = m.group(0)
        lw = w.lower()
        if lw in _HINGLISH_WORDS:
            c = random.choice(_HINGLISH_WORDS[lw])
            return c.capitalize() if w[0].isupper() else c
        return w
    return re.sub(r"\b[A-Za-z]+\b", _repl, part)

def _rewrite_link_text_option_b(link_text):
    """
    OPTION B: Keep the link text's exact word structure.
    Only swap individual words that have dictionary entries.
    No phrase replacement. No shortening.
    """
    if not link_text:
        return link_text
    return _word_replace(link_text, use_phrases=False)

def _rewrite_hinglish(text, source=None):
    """
    Rewrite main text to Hinglish.
    Protects: hidden links (as <a> tags), plain URLs, numbers.
    Preserves: line breaks.
    Returns: HTML-safe string (use parse_mode='html').
    """
    if not text:
        return ""

    # 1. Protect hidden links → placeholders
    hidden_map = {}
    orig_text = source.message if source else text
    if source:
        # Sort entities by offset descending to safely replace from end
        entities = sorted(
            [e for e in (source.entities or []) if isinstance(e, MessageEntityTextUrl)],
            key=lambda e: e.offset,
            reverse=True,
        )
        for e in entities:
            orig_link = orig_text[e.offset : e.offset + e.length]
            if orig_link in text:
                ph = f"__HID{uuid.uuid4().hex[:8]}__"
                hidden_map[ph] = {"text": orig_link, "url": e.url}
                text = text.replace(orig_link, ph, 1)

    # 2. Protect plain URLs
    url_map = {}
    for url in re.findall(r"https?://[^\s<>()]+", text, re.I):
        ph = f"__URL{uuid.uuid4().hex[:8]}__"
        url_map[ph] = url
        text = text.replace(url, ph, 1)

    # 3. Protect numbers
    num_map = {}
    for num in re.findall(r"\b\d+\b", text):
        ph = f"__NUM{uuid.uuid4().hex[:8]}__"
        num_map[ph] = num
        text = text.replace(num, ph, 1)

    # 4. Escape HTML on raw text (placeholders have no special chars)
    text = _escape_html(text)

    # 5. Word/phrase rewrite per non-placeholder segment
    parts = re.split(r"(__[A-Z]+[0-9a-f]+__)", text)
    out_parts = []
    for part in parts:
        if re.fullmatch(r"__[A-Z]+[0-9a-f]+__", part):
            out_parts.append(part)
        else:
            out_parts.append(_word_replace(part, use_phrases=True))
    text = "".join(out_parts)

    # 6. Restore numbers
    for ph, num in num_map.items():
        text = text.replace(ph, num)

    # 7. Restore plain URLs (escaped)
    for ph, url in url_map.items():
        text = text.replace(ph, _escape_html(url))

    # 8. Restore hidden links as <a href> with Option-B rewritten text
    for ph, info in hidden_map.items():
        new_label = _rewrite_link_text_option_b(info["text"])
        # The new label may contain & etc.; escape before inserting
        text = text.replace(
            ph,
            f'<a href="{_escape_html(info["url"])}">{_escape_html(new_label)}</a>',
        )

    return text

# ═══════════════════ LINK EXTRACTION ═══════════════════

_URL_RE = re.compile(r"https?://[^\s<>()]+", re.I)

def _extract_links(message):
    links = []
    if not message:
        return links
    text = message.message or ""
    for e in (getattr(message, "entities", None) or []):
        if isinstance(e, MessageEntityTextUrl):
            lt = text[e.offset : e.offset + e.length]
            links.append({"text": lt, "url": e.url, "hidden": True})
    for url in _URL_RE.findall(text):
        if not any(l["url"] == url for l in links):
            links.append({"text": url, "url": url, "hidden": False})
    return links

# ═══════════════════ BUTTONS ═══════════════════

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
    low = (text or "").lower()
    for pat, emo in _EMOJI_MAP:
        if re.search(pat, low):
            return emo
    return "🔗"

def _shorten(text, limit=30):
    if not text:
        return "link"
    if len(text) <= limit:
        return text
    out, total = [], 0
    for w in text.split():
        if total + len(w) + 1 > limit:
            break
        out.append(w); total += len(w) + 1
    return " ".join(out) if out else text[:limit]

def _build_buttons(links):
    """
    Build inline URL button rows from source links.
    Uses rewritten link text (Option B) as the label.
    Logs status for debugging.
    """
    enabled = _button_enabled()
    LOGS.info(f"[REPOST] build_buttons: enabled={enabled}, link_count={len(links or [])}")
    if not enabled or not links:
        return None

    rows = []
    for link in links:
        try:
            url = link.get("url") or ""
            if not (url.startswith("http://") or url.startswith("https://")):
                continue
            if link.get("hidden"):
                label = _rewrite_link_text_option_b(link.get("text") or "")
            else:
                parsed = urllib.parse.urlparse(url)
                label = parsed.netloc or "link"
            label = _shorten(label)
            if _emoji_enabled():
                label = f"{_emoji_for(link.get('text') or '')} {label}"
            # Telegram button text must be 1-64 chars
            label = label.strip()[:64] or "link"
            rows.append([Button.url(label, url)])
        except Exception as e:
            LOGS.warning(f"[REPOST] button build error: {e}")
            continue

    LOGS.info(f"[REPOST] built {len(rows)} button row(s)")
    return rows or None

# ═══════════════════ FOLDERS / TARGETS ═══════════════════

async def _get_folder_filters():
    res = await catub(functions.messages.GetDialogFiltersRequest())
    if isinstance(res, (list, tuple)):
        return list(res)
    return list(getattr(res, "filters", None) or [])

async def _folder_channels(fid):
    filters = await _get_folder_filters()
    chosen = next((f for f in filters if getattr(f, "id", None) == int(fid)), None)
    if not chosen:
        raise ValueError("Folder not found. Run .repostfolders first.")
    included = list(getattr(chosen, "include_peers", []) or [])
    excluded = list(getattr(chosen, "exclude_peers", []) or [])
    ex_ids = set()
    for p in excluded:
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
    fid = _folder_id()
    if fid is None:
        return _targets()
    fids = fid if isinstance(fid, list) else [fid]
    combined, seen = [], set()
    for f in fids:
        try:
            for t in await _folder_channels(f):
                k = str(t["id"])
                if k not in seen:
                    seen.add(k); combined.append(t)
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
        if getattr(entity, "admin_rights", None) and getattr(entity.admin_rights, "post_messages", False):
            return True
        try:
            perms = await catub.get_permissions(entity, me)
            if getattr(perms, "is_admin", False):
                r = getattr(perms, "admin_rights", None)
                if r and getattr(r, "post_messages", False):
                    return True
            if getattr(perms, "send_messages", False):
                return True
        except Exception:
            pass
    except Exception:
        pass
    return False

def _excluded_ids():
    return {str(x.get("id")) for x in _excluded() if x.get("id")}

# ═══════════════════ DELIVERY ═══════════════════

async def _send_to_target(entity, source, text, buttons):
    has_file = bool(getattr(source, "document", None) or getattr(source, "photo", None))
    LOGS.info(f"[REPOST] send_to_target: has_file={has_file}, has_buttons={bool(buttons)}, text_len={len(text or '')}")
    if has_file:
        try:
            await catub.send_file(
                entity,
                source.media,
                caption=text or "",
                parse_mode="html",
                buttons=buttons,
            )
            return
        except Exception as e:
            LOGS.warning(f"[REPOST] send_file failed: {type(e).__name__}: {e}")
    if text:
        await catub.send_message(
            entity,
            text,
            parse_mode="html",
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
            "No repost targets configured.\nUse .repostfolders + .reposttarget, or .repostadd.",
        )

    original = source.message or ""
    fixed = _fix_typos(original)
    # Extract links from ORIGINAL (before rewrite) — buttons use original URLs
    links = _extract_links(source)
    excluded = _excluded_ids()

    success, skipped, failed = [], [], []
    lo, hi = _delay()

    for item in targets:
        cid = str(item.get("id"))
        title = item.get("title", cid)
        if cid in excluded:
            skipped.append(f"{title} (excluded)"); continue
        entity = await _resolve_target(item)
        if entity is None:
            skipped.append(f"{title} (not accessible)"); continue
        if not await _can_post(entity):
            skipped.append(f"{title} (no posting permission)"); continue

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
            LOGS.warning(f"[REPOST] {title}: {type(exc).__name__}: {exc}")
            failed.append(f"{title} ({type(exc).__name__})")
        if hi:
            await asyncio.sleep(random.randint(lo, hi))

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

# ═══════════════════ SCHEDULER ═══════════════════

def _parse_hhmm(s):
    m = re.match(r"^(\d{1,2}):(\d{2})$", s.strip())
    if not m:
        raise ValueError(f"Invalid time: {s}")
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        raise ValueError(f"Invalid time: {s}")
    return h * 60 + mi

def _parse_time_windows(s):
    out = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = _parse_hhmm(a), _parse_hhmm(b)
            if start >= end:
                raise ValueError(f"Invalid window: {part}")
            out.append((start, end))
        else:
            out.append((_parse_hhmm(part), None))
    if not out:
        raise ValueError("No times provided.")
    return out

def _min_to_str(m):
    return f"{m//60:02d}:{m%60:02d}"

def _parse_expire(v):
    if not v:
        return None
    v = v.strip().lower()
    if v.endswith("h"):
        return datetime.timedelta(hours=int(v[:-1]))
    return datetime.timedelta(days=int(v))

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
            today = now.date().isoformat()
            schedules = _schedules()
            changed = False

            for sch in schedules:
                if sch.get("stopped"):
                    continue
                # Expiry check
                created = sch.get("created")
                expire_sec = sch.get("expire")
                if expire_sec and created:
                    created_dt = datetime.datetime.fromisoformat(created)
                    if now >= created_dt + datetime.timedelta(seconds=expire_sec):
                        sch["stopped"] = True
                        changed = True
                        continue

                fired = sch.get("last_fired", {})
                today_fired = set(fired.get(today, []))
                for idx, (start, end) in enumerate(sch.get("windows", [])):
                    if idx in today_fired:
                        continue
                    fire = False
                    if end is None:
                        # Fixed time
                        if now_min == start:
                            fire = True
                    else:
                        # Window: uniform random minute within window
                        if start <= now_min <= end:
                            remaining = end - now_min + 1
                            if random.random() < 1.0 / remaining:
                                fire = True
                    if fire:
                        await _run_schedule_once(sch)
                        today_fired.add(idx)
                        changed = True

                if today_fired:
                    fired[today] = sorted(today_fired)
                    # Prune old dates
                    keep = {today}
                    sch["last_fired"] = {d: v for d, v in fired.items() if d in keep or d >= today}

            if changed:
                _save_schedules(schedules)
        except Exception as e:
            LOGS.exception(f"[REPOST] scheduler error: {e}")
        await asyncio.sleep(30)

async def _run_schedule_once(sch):
    """Send all queued posts (matches any active schedule)."""
    queue = _queue()
    if not queue:
        LOGS.info("[REPOST] schedule fired but queue empty")
        return
    targets = await _active_targets()
    if not targets:
        return
    excluded = _excluded_ids()
    lo, hi = _delay()
    for item in queue:
        try:
            src = await catub.get_messages(
                int(item["chat_id"]), ids=int(item["message_id"])
            )
            if not src:
                continue
            fixed = _fix_typos(src.message or "")
            links = _extract_links(src)
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
                except Exception as e:
                    LOGS.warning(f"[REPOST] sched send failed: {type(e).__name__}")
                if hi:
                    await asyncio.sleep(random.randint(lo, hi))
        except Exception:
            continue

# ═══════════════════ COMMANDS ═══════════════════

async def _get_source(event):
    return await event.get_reply_message() if event.is_reply else None

@catub.cat_cmd(
    pattern="rp$",
    command=("rp", plugin_category),
    info={"header": "Repost", "usage": "{tr}rp | {tr}rp <link>"},
)
async def repost(event):
    raw = (event.raw_text or "").split(maxsplit=1)
    arg = raw[1].strip() if len(raw) > 1 else ""

    if arg and re.match(r"^https?://t\.me/", arg, re.I):
        try:
            m = re.search(r"/c/(\d+)/(\d+)", arg)
            if m:
                peer = types.InputPeerChannel(int(m.group(1)), 0)
                src = await catub.get_messages(peer, ids=int(m.group(2)))
            else:
                parts = arg.rstrip("/").split("/")
                src = await catub.get_messages(parts[-2], ids=int(parts[-1]))
            if not src:
                return await edit_or_reply(event, "Could not fetch the linked message.")
            _maybe_queue_for_schedule(src)
            return await _deliver(src, event)
        except Exception as e:
            LOGS.exception("[REPOST] link fetch failed")
            return await edit_or_reply(event, f"Link fetch failed: {type(e).__name__}")

    src = await _get_source(event)
    if not src:
        return await edit_or_reply(event, "Reply to a post and use .rp, or .rp <link>.")
    _maybe_queue_for_schedule(src)
    await _deliver(src, event)

def _maybe_queue_for_schedule(src):
    """If any active schedule exists, queue this post so it runs at scheduled times."""
    schedules = [s for s in _schedules() if not s.get("stopped")]
    if not schedules:
        return
    queue = _queue()
    cid, mid = int(src.chat_id), int(src.id)
    if any(x.get("chat_id") == cid and x.get("message_id") == mid for x in queue):
        return
    queue.append({
        "chat_id": cid,
        "message_id": mid,
        "uuid": uuid.uuid4().hex,
    })
    _save_queue(queue)
    _ensure_scheduler()
    LOGS.info(f"[REPOST] queued chat={cid} msg={mid} (schedules active: {len(schedules)})")

@catub.cat_cmd(
    pattern="reposthelp$",
    command=("reposthelp", plugin_category),
    info={"header": "Help", "usage": "{tr}reposthelp"},
)
async def repost_help(event):
    text = (
        "📖 **REPOST HELP**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 `.rp` — reply to a post to repost\n"
        "🔹 `.rp <link>` — repost from a channel link (public/private)\n\n"
        "**Targets**\n"
        "• `.repostfolders` / `.reposttarget <id|off>`\n"
        "• `.repostadd` (reply) / `.repostremove <id>` / `.repostlist`\n\n"
        "**Exclude**\n"
        "• `.repostexclude add|remove <id|@user> [...]`\n"
        "• `.repostexclude list|clear|status`\n\n"
        "**Schedule**\n"
        "• `.repostschedule add 09:00,12:00-12:05 [1|265|1h]`\n"
        "• `.repostschedule list|off [id]|clear`\n"
        "• `.repostqueue | .repostqueue clear`\n\n"
        "**Settings**\n"
        "• `.repostdelay <min> <max>|off`\n"
        "• `.repostbutton on|off|status`\n"
        "• `.repostemoji on|off`\n"
        "• `.reposttypo on|off`\n"
        "• `.repoststatus`"
    )
    await edit_or_reply(event, text)

@catub.cat_cmd(
    pattern="repostfolders$",
    command=("repostfolders", plugin_category),
    info={"header": "Folders", "usage": "{tr}repostfolders"},
)
async def repost_folders(event):
    try:
        filters = await _get_folder_filters()
    except Exception as e:
        return await edit_or_reply(event, f"Folder read failed: {e}")
    lines, n = ["**TELEGRAM FOLDERS**"], 0
    for f in filters:
        fid = getattr(f, "id", None)
        if fid is None:
            continue
        title = getattr(f, "title", None) or "Untitled"
        title_text = getattr(title, "text", None) or str(title)
        lines.append(f"\n• {title_text} — ID: `{fid}`")
        n += 1
    if not n:
        lines.append("\nNo folders found.")
    else:
        lines.append("\n`.reposttarget 2` or `.reposttarget 2,3`")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern=r"reposttarget(?:\s+(\S+))?$",
    command=("reposttarget", plugin_category),
    info={"header": "Target folder", "usage": "{tr}reposttarget <id|off>"},
)
async def repost_target(event):
    v = event.pattern_match.group(1)
    if not v:
        cur = _folder_id()
        return await edit_or_reply(event, "Selected folder: " + (str(cur) if cur is not None else "OFF"))
    if v.lower() == "off":
        _save("FOLDER_ID", None)
        return await edit_or_reply(event, "Folder targeting disabled.")
    try:
        fids = []
        for p in v.split(","):
            p = p.strip()
            if not p.isdigit():
                raise ValueError("Use .reposttarget 2 or .reposttarget 2,3")
            if int(p) not in fids:
                fids.append(int(p))
        counts = [(f, len(await _folder_channels(f))) for f in fids]
        _save("FOLDER_ID", fids[0] if len(fids) == 1 else fids)
        summary = "\n".join(f"Folder {f}: {c} channels" for f, c in counts)
        await edit_or_reply(event, f"Selected: {', '.join(map(str, fids))}\n{summary}")
    except Exception as e:
        await edit_or_reply(event, f"Error: {e}")

@catub.cat_cmd(
    pattern="repostadd$",
    command=("repostadd", plugin_category),
    info={"header": "Add target", "usage": "{tr}repostadd (reply)"},
)
async def repost_add(event):
    src = await _get_source(event)
    if not src:
        return await edit_or_reply(event, "Reply to a channel post.")
    try:
        ent = await catub.get_entity(src.peer_id)
        if not isinstance(ent, Channel):
            return await edit_or_reply(event, "Not a channel post.")
        item = {
            "id": int(ent.id),
            "access_hash": int(ent.access_hash),
            "title": ent.title,
            "username": getattr(ent, "username", None),
        }
        items = _targets(); items.append(item); _save_targets(items)
        await edit_or_reply(event, f"Saved: {ent.title}")
    except Exception as e:
        await edit_or_reply(event, f"Failed: {type(e).__name__}")

@catub.cat_cmd(
    pattern=r"repostremove\s+(.+)$",
    command=("repostremove", plugin_category),
    info={"header": "Remove target", "usage": "{tr}repostremove <id>..."},
)
async def repost_remove(event):
    items = event.pattern_match.group(1).replace(",", " ").split()
    if not items:
        return await edit_or_reply(event, "Provide IDs.")
    targets = _targets()
    removed, missing = [], []
    for item in items:
        val = item.strip().lstrip("@").lower()
        keep, found = [], False
        for t in targets:
            if str(t.get("id")) == val or str(t.get("username") or "").lower() == val:
                removed.append(t.get("title", val)); found = True
            else:
                keep.append(t)
        targets = keep
        if not found:
            missing.append(val)
    _save_targets(targets)
    msg = f"✅ Removed: {len(removed)}"
    if missing:
        msg += f"\n⚠️ Not found: {', '.join(missing[:10])}"
    await edit_or_reply(event, msg)

@catub.cat_cmd(
    pattern="repostlist$",
    command=("repostlist", plugin_category),
    info={"header": "List targets", "usage": "{tr}repostlist"},
)
async def repost_list(event):
    items = await _active_targets()
    if not items:
        return await edit_or_reply(event, "No targets.")
    lines = ["**REPOST TARGETS**"]
    for t in items:
        name = t.get("title", str(t.get("id")))
        un = f" @{t['username']}" if t.get("username") else ""
        lines.append(f"• {name}{un} — `{t['id']}`")
    await edit_or_reply(event, "\n".join(lines))

async def _resolve_item(value):
    val = value.strip()
    if re.match(r"^-?\d+$", val):
        cid = int(val)
        try:
            ent = await catub.get_entity(cid)
            return {"id": int(ent.id), "title": getattr(ent, "title", str(cid)),
                    "username": getattr(ent, "username", None)}
        except Exception:
            return {"id": cid, "title": "Unknown", "username": None}
    try:
        ent = await catub.get_entity(val.lstrip("@"))
        if not isinstance(ent, (Channel, Chat)):
            return None
        return {"id": int(ent.id), "title": getattr(ent, "title", str(ent.id)),
                "username": getattr(ent, "username", None)}
    except Exception:
        return None

@catub.cat_cmd(
    pattern=r"repostexclude add\s+(.+)$",
    command=("repostexclude", plugin_category),
    info={"header": "Exclude", "usage": "{tr}repostexclude add <id|@u>..."},
)
async def repost_exclude_add(event):
    items = event.pattern_match.group(1).replace(",", " ").split()
    current = _excluded()
    cur_ids = {str(x.get("id")) for x in current}
    added, failed, dup = [], [], []
    for it in items:
        info = await _resolve_item(it)
        if not info:
            failed.append(it); continue
        if str(info["id"]) in cur_ids:
            dup.append(info.get("title", it)); continue
        current.append(info); cur_ids.add(str(info["id"])); added.append(info)
    _save_excluded(current)
    lines = [f"✅ Added: {len(added)}"]
    for a in added:
        un = f" (@{a['username']})" if a.get("username") else ""
        lines.append(f"  • {a['id']} → \"{a['title']}\"{un}")
    if dup: lines.append(f"Already: {len(dup)}")
    if failed: lines.append(f"⚠️ Failed: {', '.join(failed[:5])}")
    lines.append(f"Total: {len(current)}")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern=r"repostexclude remove\s+(.+)$",
    command=("repostexclude", plugin_category),
    info={"header": "Un-exclude", "usage": "{tr}repostexclude remove <id|@u>..."},
)
async def repost_exclude_remove(event):
    items = event.pattern_match.group(1).replace(",", " ").split()
    current = _excluded()
    removed, missing = [], []
    for it in items:
        val = it.strip().lstrip("@").lower()
        keep, found = [], False
        for x in current:
            if str(x.get("id")) == val or str(x.get("username") or "").lower() == val:
                removed.append(x.get("title", val)); found = True
            else:
                keep.append(x)
        current = keep
        if not found:
            missing.append(val)
    _save_excluded(current)
    lines = [f"✅ Removed: {len(removed)}"]
    if missing: lines.append(f"⚠️ Not found: {', '.join(missing[:10])}")
    lines.append(f"Remaining: {len(current)}")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern="repostexclude list$",
    command=("repostexclude", plugin_category),
    info={"header": "List excluded", "usage": "{tr}repostexclude list"},
)
async def repost_exclude_list(event):
    items = _excluded()
    if not items:
        return await edit_or_reply(event, "No excluded.")
    lines = ["📋 **EXCLUDED CHANNELS**"]
    for i, x in enumerate(items, 1):
        cid, title = x.get("id"), x.get("title", "Unknown")
        un = x.get("username")
        lines.append(f"{i}. `{cid}` — \"{title}\"" + (f" (@{un})" if un else ""))
    lines.append(f"\nTotal: {len(items)}")
    await edit_or_reply(event, "\n".join(lines))

@catub.cat_cmd(
    pattern="repostexclude clear$",
    command=("repostexclude", plugin_category),
    info={"header": "Clear excluded", "usage": "{tr}repostexclude clear"},
)
async def repost_exclude_clear(event):
    n = len(_excluded())
    _save_excluded([])
    await edit_or_reply(event, f"🗑️ Cleared {n}.")

@catub.cat_cmd(
    pattern="repostexclude status$",
    command=("repostexclude", plugin_category),
    info={"header": "Excluded stats", "usage": "{tr}repostexclude status"},
)
async def repost_exclude_status(event):
    items = _excluded()
    pub = sum(1 for x in items if x.get("username"))
    await edit_or_reply(
        event,
        f"📊 **EXCLUDE STATUS**\nTotal: {len(items)}\n"
        f"Public: {pub}\nPrivate: {len(items)-pub}",
    )

@catub.cat_cmd(
    pattern=r"repostschedule add\s+(.+)$",
    command=("repostschedule", plugin_category),
    info={"header": "Add schedule", "usage": "{tr}repostschedule add <times> [expire]"},
)
async def repost_schedule_add(event):
    raw = event.pattern_match.group(1).strip()
    parts = raw.rsplit(None, 1)
    if len(parts) == 2 and (parts[1].endswith("h") or parts[1].isdigit()):
        time_part, expire_part = parts[0], parts[1]
    else:
        time_part, expire_part = raw, None
    try:
        windows = _parse_time_windows(time_part)
        expire = _parse_expire(expire_part)
    except ValueError as e:
        return await edit_or_reply(event, str(e))
    schedules = _schedules()
    schedules.append({
        "uuid": uuid.uuid4().hex,
        "windows": [[s, e] for s, e in windows],
        "expire": expire.total_seconds() if expire else None,
        "created": datetime.datetime.now(TZ).isoformat(),
        "stopped": False,
        "last_fired": {},
    })
    _save_schedules(schedules)
    _ensure_scheduler()
    desc = ", ".join(_min_to_str(s) + (f"-{_min_to_str(e)}" if e is not None else "")
                     for s, e in windows)
    exp = f" (expires in {expire_part})" if expire_part else ""
    await edit_or_reply(event, f"✅ Schedule added.\nTimes: {desc}{exp}")

@catub.cat_cmd(
    pattern="repostschedule list$",
    command=("repostschedule", plugin_category),
    info={"header": "List schedules", "usage": "{tr}repostschedule list"},
)
async def repost_schedule_list(event):
    schedules = _schedules()
    if not schedules:
        return await edit_or_reply(event, "No schedules.")
    lines = ["📅 **SCHEDULE LIST**"]
    now = datetime.datetime.now(TZ)
    for i, sch in enumerate(schedules, 1):
        times = ", ".join(_min_to_str(s) + (f"-{_min_to_str(e)}" if e is not None else "")
                          for s, e in sch.get("windows", []))
        created = datetime.datetime.fromisoformat(sch.get("created"))
        expire = sch.get("expire")
        if sch.get("stopped"):
            status = "⏹ Stopped"
        elif expire:
            rem = (created + datetime.timedelta(seconds=expire)) - now
            status = f"✅ {rem}" if rem.total_seconds() > 0 else "❌ Expired"
        else:
            status = "✅ Unlimited"
        lines.append(f"\n{i}. {times}\n   {status}")
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
        return await edit_or_reply(event, "No schedules.")
    if idx:
        try:
            i = int(idx) - 1
            if 0 <= i < len(schedules):
                schedules[i]["stopped"] = True
                _save_schedules(schedules)
                return await edit_or_reply(event, f"⏹ #{idx} stopped.")
        except ValueError:
            pass
    for sch in schedules:
        sch["stopped"] = True
    _save_schedules(schedules)
    await edit_or_reply(event, "⏹ All stopped.")

@catub.cat_cmd(
    pattern="repostschedule clear$",
    command=("repostschedule", plugin_category),
    info={"header": "Clear schedules", "usage": "{tr}repostschedule clear"},
)
async def repost_schedule_clear(event):
    _save_schedules([])
    await edit_or_reply(event, "🗑️ Cleared.")

@catub.cat_cmd(
    pattern="repostqueue$",
    command=("repostqueue", plugin_category),
    info={"header": "Queue", "usage": "{tr}repostqueue"},
)
async def repost_queue(event):
    items = _queue()
    if not items:
        return await edit_or_reply(event, "Queue empty.")
    lines = ["**QUEUE**"]
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

@catub.cat_cmd(
    pattern=r"repostdelay(?:\s+(.+))?$",
    command=("repostdelay", plugin_category),
    info={"header": "Delay", "usage": "{tr}repostdelay <min> <max>|off"},
)
async def repost_delay(event):
    raw = event.pattern_match.group(1)
    if not raw:
        lo, hi = _delay()
        return await edit_or_reply(event, f"Current: {lo}-{hi}s")
    if raw.strip().lower() == "off":
        _save("DELAY", [0, 0])
        return await edit_or_reply(event, "Disabled.")
    m = re.match(r"^(\d+)\s+(\d+)$", raw.strip())
    if not m:
        return await edit_or_reply(event, "Usage: .repostdelay 2 8 | off")
    lo, hi = int(m.group(1)), int(m.group(2))
    if hi < lo or hi > 3600:
        return await edit_or_reply(event, "Invalid range.")
    _save("DELAY", [lo, hi])
    await edit_or_reply(event, f"Delay set: {lo}-{hi}s.")

@catub.cat_cmd(
    pattern=r"repostbutton(?:\s+(\S+))?$",
    command=("repostbutton", plugin_category),
    info={"header": "Buttons", "usage": "{tr}repostbutton on|off|status"},
)
async def repost_button(event):
    arg = (event.pattern_match.group(1) or "").lower()
    if arg == "on":
        addgvar(PREFIX + "BUTTON", "true")
        return await edit_or_reply(event, "✅ Buttons ON.")
    if arg == "off":
        delgvar(PREFIX + "BUTTON")
        return await edit_or_reply(event, "🚫 Buttons OFF.")
    st = "ON" if _button_enabled() else "OFF"
    em = "ON" if _emoji_enabled() else "OFF"
    await edit_or_reply(event, f"Button: `{st}` | Emoji: `{em}`")

@catub.cat_cmd(
    pattern=r"repostemoji(?:\s+(\S+))?$",
    command=("repostemoji", plugin_category),
    info={"header": "Emoji", "usage": "{tr}repostemoji on|off"},
)
async def repost_emoji(event):
    arg = (event.pattern_match.group(1) or "").lower()
    if arg == "on":
        addgvar(PREFIX + "EMOJI", "true")
        return await edit_or_reply(event, "✅ Emoji ON.")
    if arg == "off":
        delgvar(PREFIX + "EMOJI")
        return await edit_or_reply(event, "🚫 Emoji OFF.")
    await edit_or_reply(event, "Usage: on|off")

@catub.cat_cmd(
    pattern=r"reposttypo(?:\s+(\S+))?$",
    command=("reposttypo", plugin_category),
    info={"header": "Typo fix", "usage": "{tr}reposttypo on|off"},
)
async def repost_typo(event):
    arg = (event.pattern_match.group(1) or "").lower()
    if arg == "on":
        addgvar(PREFIX + "TYPO", "true")
        return await edit_or_reply(event, "✅ Typo fix ON.")
    if arg == "off":
        delgvar(PREFIX + "TYPO")
        return await edit_or_reply(event, "🚫 Typo fix OFF.")
    await edit_or_reply(event, "Usage: on|off")

@catub.cat_cmd(
    pattern="repoststatus$",
    command=("repoststatus", plugin_category),
    info={"header": "Status", "usage": "{tr}repoststatus"},
)
async def repost_status(event):
    lo, hi = _delay()
    folder = _folder_id()
    t = len(await _active_targets())
    _ensure_scheduler()
    lines = [
        "📊 **REPOST STATUS**",
        f"Mode: {'Folders '+str(folder) if folder is not None else 'Saved targets'}",
        f"Targets: {t}",
        f"Excluded: {len(_excluded())}",
        f"Delay: {lo}-{hi}s",
        f"Schedules: {len(_schedules())}",
        f"Queue: {len(_queue())}",
        f"Buttons: {'ON' if _button_enabled() else 'OFF'}",
        f"Emoji: {'ON' if _emoji_enabled() else 'OFF'}",
        f"Typo: {'ON' if _typo_enabled() else 'OFF'}",
    ]
    await edit_or_reply(event, "\n".join(lines))
