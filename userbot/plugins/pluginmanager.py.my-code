# CATXBot Log Group Plugin Manager
# Commands: reply to a .py file with .install / .uninstall
# Supports CATXBot's catub.cat_cmd plugins and owner + configured SUDO users.

import ast
import importlib
import importlib.metadata
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from telethon import events

from .. import BOTLOG_CHATID
from ..Config import Config
from ..core.data import _sudousers_list
from ..core import CMD_INFO, LOADED_CMDS, PLG_INFO
from . import CMD_HELP
from ..core.logger import logging
from ..core.session import catub
from ..utils.pluginmanager import load_module, remove_plugin

LOGS = logging.getLogger("CatUserbot.PluginManager")
PLUGIN_DIR = Path("userbot/plugins")
DEPENDENCY_DB = PLUGIN_DIR / ".plugin_dependencies.json"
DOCUMENT_DB = PLUGIN_DIR / ".plugin_documents.json"
MAX_PLUGIN_SIZE = 512 * 1024
PROTECTED = {
    "__init__", "__main__", "sudo", "externalplugins", "pluginmanager"
}
BLOCKED_IMPORTS = {
    "subprocess", "socket", "ctypes", "pickle", "marshal", "pty",
    "telnetlib", "ftplib", "multiprocessing"
}
BLOCKED_CALLS = {"eval", "exec", "__import__"}
BLOCKED_OS_CALLS = {"system", "popen", "spawnl", "spawnv", "spawnve"}
MODULE_ALIASES = {
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "yaml": "PyYAML",
    "Crypto": "pycryptodome",
    "dotenv": "python-dotenv",
    "google": "google",
    "sklearn": "scikit-learn",
    "dateutil": "python-dateutil",
    "telegram": "python-telegram-bot",
    "serial": "pyserial",
    "fitz": "PyMuPDF",
    "magic": "python-magic",
}

def _log_chat():
    try:
        return int(BOTLOG_CHATID)
    except Exception:
        return None

def _ids(values):
    result = set()
    for value in values or []:
        try:
            result.add(int(value))
        except Exception:
            pass
    return result

def _authorized(event):
    sender = getattr(event, "sender_id", None)
    if not sender:
        return False
    owners = set()
    for value in (getattr(Config, "OWNER_ID", None), getattr(catub, "uid", None)):
        try:
            if value:
                owners.add(int(value))
        except Exception:
            pass
    return sender in owners or sender in _ids(_sudousers_list())

def _command_pattern(prefixes, command):
    prefixes = prefixes or [".", "!"]
    if isinstance(prefixes, str):
        prefixes = [prefixes]
    p = "|".join(re.escape(x) for x in prefixes if x)
    return rf"(?i)^(?:{p}){command}(?:\s|$)"

def _db_read():
    try:
        data = json.loads(DEPENDENCY_DB.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _db_write(data):
    temp = DEPENDENCY_DB.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True))
    os.replace(temp, DEPENDENCY_DB)

def _document_db_read():
    try:
        data = json.loads(DOCUMENT_DB.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _document_db_write(data):
    temp = DOCUMENT_DB.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True))
    os.replace(temp, DOCUMENT_DB)

def _document_filename(message):
    """Read the real uploaded filename from Telegram document attributes."""
    document = getattr(message, "document", None)
    for attr in getattr(document, "attributes", []) or []:
        filename = getattr(attr, "file_name", None)
        if filename:
            return Path(str(filename).replace("\\", "/")).name
    file_obj = getattr(message, "file", None)
    filename = getattr(file_obj, "name", None) if file_obj else None
    if filename:
        return Path(str(filename).replace("\\", "/")).name
    return ""

def _document_id(message):
    document = getattr(message, "document", None)
    value = getattr(document, "id", None)
    return str(value) if value is not None else None

def _unique_plugin_stem(stem):
    """Keep an existing plugin intact and allocate stem1, stem2, ..."""
    candidate = stem
    index = 1
    while (PLUGIN_DIR / f"{candidate}.py").exists():
        candidate = f"{stem}{index}"
        index += 1
    return candidate

async def _send_result(event, message):
    """Send a visible result, with a client-level fallback if event.reply fails."""
    try:
        return await event.reply(message)
    except Exception:
        LOGS.exception("event.reply failed; trying direct send_message")
    try:
        return await catub.send_message(
            int(event.chat_id), message, reply_to=getattr(event, "id", None)
        )
    except Exception:
        LOGS.exception("Could not send plugin-manager result by either method")
        return None

def _distribution_map():
    result = {}
    try:
        for module, distributions in importlib.metadata.packages_distributions().items():
            if distributions:
                result[module.split(".")[0]] = distributions[0]
    except Exception:
        pass
    return result

def _requirements_baseline():
    baseline = set()
    req = Path("requirements.txt")
    if req.exists():
        for line in req.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(("-", "http:", "https:")):
                continue
            name = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip()
            if name:
                baseline.add(re.sub(r"[-_.]+", "-", name).lower())
    return baseline

def _installed_distributions():
    return {
        re.sub(r"[-_.]+", "-", d.metadata.get("Name", d.name)).lower()
        for d in importlib.metadata.distributions()
    }

def _scan_source(source):
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
                raise ValueError(f"Blocked dangerous call: {node.func.id}()")
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and node.func.attr in BLOCKED_OS_CALLS:
                    raise ValueError(f"Blocked dangerous call: os.{node.func.attr}()")
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                    raise ValueError("Blocked subprocess API")
    return tree, imports

def _plugin_imports(source):
    _, imports = _scan_source(source)
    stdlib = getattr(sys, "stdlib_module_names", set())
    local_roots = {"userbot", "config", "plugins"}
    dist_map = _distribution_map()
    packages = set()
    for module in imports:
        if module in stdlib or module in local_roots or module == "__future__":
            continue
        dist = dist_map.get(module)
        if dist:
            packages.add(dist)
        elif importlib.util.find_spec(module) is None:
            packages.add(MODULE_ALIASES.get(module, module))
    return packages

def _pip_install(packages):
    packages = sorted(set(packages))
    if not packages:
        return set()
    before = _installed_distributions()
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", *packages],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=600
    )
    if proc.returncode:
        raise RuntimeError((proc.stdout or "pip install failed")[-2500:])
    importlib.invalidate_caches()
    after = _installed_distributions()
    return after - before

def _pip_uninstall(packages):
    if not packages:
        return []
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", *sorted(packages)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=600
    )
    return (proc.stdout or "")[-1800:]

def _safe_plugin_name(filename):
    name = Path(filename).name
    if not name.lower().endswith(".py"):
        raise ValueError("Reply to a .py plugin file.")
    stem = Path(name).stem
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", stem):
        raise ValueError("Invalid plugin filename.")
    if stem in PROTECTED or stem.startswith("__"):
        raise ValueError("This core plugin name is protected.")
    return stem

def _cleanup_metadata(stem):
    sys.modules.pop(f"userbot.plugins.{stem}", None)
    commands = list(PLG_INFO.get(stem, []) or [])
    for command in commands:
        CMD_INFO.pop(command, None)
    CMD_HELP.pop(stem, None)
    PLG_INFO.pop(stem, None)
    for command, handlers in list(LOADED_CMDS.items()):
        if not handlers:
            LOADED_CMDS.pop(command, None)

def _entry_packages(entry):
    if isinstance(entry, dict):
        return set(entry.get("packages", []))
    return set(entry or [])

def _entry_owned(entry):
    if isinstance(entry, dict):
        return set(entry.get("owned", []))
    return set(entry or [])

def _remove_plugin_dependencies(stem):
    db = _db_read()
    entry = db.pop(stem, [])
    owned = _entry_owned(entry)
    shared = set()
    for other_entry in db.values():
        shared.update(_entry_packages(other_entry))
    keep = _requirements_baseline() | shared
    removable = owned - keep
    installed = {}
    for dist in importlib.metadata.distributions():
        name = re.sub(r"[-_.]+", "-", dist.metadata.get("Name", dist.name)).lower()
        for requirement in dist.requires or []:
            dep = re.split(r"[<>=!~;\[]", requirement, maxsplit=1)[0].strip()
            if dep:
                installed.setdefault(re.sub(r"[-_.]+", "-", dep).lower(), set()).add(name)
    for package in list(removable):
        dependents = installed.get(package, set())
        if dependents - owned:
            removable.discard(package)
    _db_write(db)
    return _pip_uninstall(removable) if removable else "No exclusive dependencies to remove."

async def _reply(event, message):
    try:
        await event.edit(message)
    except Exception:
        try:
            await event.reply(message)
        except Exception:
            pass

async def _install(event):
    if not _authorized(event) or event.chat_id != _log_chat():
        return
    reply = await event.get_reply_message()
    if not reply or not getattr(reply, "document", None):
        return await _send_result(event, "Reply to a Python plugin (.py) file with .install.")
    try:
        filename = _document_filename(reply)
        original_stem = _safe_plugin_name(filename)
        if reply.file and reply.file.size and reply.file.size > MAX_PLUGIN_SIZE:
            raise ValueError("Plugin exceeds the 512 KB limit.")
        raw = await reply.download_media(file=bytes)
        if not raw:
            raise ValueError("Could not download the plugin.")
        source = raw.decode("utf-8-sig")
        packages = _plugin_imports(source)
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

        # Never replace an installed plugin: use plugin1.py, plugin2.py, etc.
        stem = _unique_plugin_stem(original_stem)
        target = PLUGIN_DIR / f"{stem}.py"
        db = _db_read()
        newly_installed = _pip_install(packages)
        fd, temp_name = tempfile.mkstemp(prefix=f".{stem}_", suffix=".py", dir=str(PLUGIN_DIR))
        os.close(fd)
        temp_path = Path(temp_name)
        temp_path.write_bytes(raw)
        try:
            os.replace(temp_path, target)
            load_module(stem)
        except Exception:
            try:
                remove_plugin(stem)
                _cleanup_metadata(stem)
            except Exception:
                pass
            target.unlink(missing_ok=True)
            raise

        db[stem] = {
            "packages": sorted(packages),
            "owned": sorted(newly_installed),
            "updated_at": int(time.time()),
        }
        _db_write(db)
        doc_id = _document_id(reply)
        if doc_id:
            documents = _document_db_read()
            documents[doc_id] = stem
            _document_db_write(documents)
        await _send_result(event, f"**Plugin manager**\n\nPlugin Installed: \n```\n{stem}.py\n```\nStatus: Active!")
    except Exception as exc:
        LOGS.exception("Plugin install failed")
        await _send_result(event, f"Install failed: {exc}")

async def _uninstall(event):
    if not _authorized(event) or event.chat_id != _log_chat():
        return

    # Supports reply-based uninstall and .uninstall plugin_name[.py].
    raw = (getattr(event, "raw_text", "") or "").strip()
    parts = raw.split(maxsplit=1)
    requested_name = parts[1].strip() if len(parts) > 1 else ""

    if requested_name:
        try:
            filename = Path(requested_name.replace("\\", "/")).name
            if not filename.lower().endswith(".py"):
                filename += ".py"
            stem = _safe_plugin_name(filename)
        except Exception as exc:
            return await _send_result(event, "Invalid plugin name: " + str(exc))
    else:
        try:
            reply = await event.get_reply_message()
        except Exception:
            LOGS.exception("Could not read uninstall reply")
            reply = None

        if not reply or not getattr(reply, "document", None):
            return await _send_result(
                event,
                "Usage: reply to a plugin .py file with .uninstall, "
                "or use .uninstall plugin_name / .uninstall plugin_name.py"
            )

        doc_id = _document_id(reply)
        documents = _document_db_read()
        stem = documents.get(doc_id) if doc_id else None
        if not stem:
            try:
                stem = _safe_plugin_name(_document_filename(reply))
            except Exception as exc:
                return await _send_result(event, "Could not identify plugin: " + str(exc))

    if stem in PROTECTED or stem.startswith("__"):
        return await _send_result(event, "This core plugin is protected.")

    target = PLUGIN_DIR / (stem + ".py")
    if not target.is_file():
        return await _send_result(
            event, f"{stem}.py is not installed. Use .plugins to see installed plugin names."
        )

    help_entries = list(PLG_INFO.get(stem, []) or [])
    handler_ids = set()
    for command in help_entries:
        for handler in LOADED_CMDS.get(command, []) or []:
            if getattr(handler, "__module__", "") == f"userbot.plugins.{stem}":
                handler_ids.add(id(handler))
    if not handler_ids:
        for handlers in LOADED_CMDS.values():
            for handler in handlers or []:
                if getattr(handler, "__module__", "") == f"userbot.plugins.{stem}":
                    handler_ids.add(id(handler))

    unload_warning = None
    try:
        remove_plugin(stem)
    except Exception as exc:
        unload_warning = f"{type(exc).__name__}: {exc}"
        LOGS.exception("remove_plugin failed for %s; continuing file cleanup", stem)

    _cleanup_metadata(stem)
    try:
        target.unlink()
    except Exception as exc:
        LOGS.exception("Could not delete plugin file %s", target)
        return await _send_result(
            event, f"Could not delete {stem}.py: {type(exc).__name__}: {exc}"
        )

    # Dependency cleanup is separate: it must not undo/report failure after
    # the plugin file itself has already been removed.
    try:
        dependency_note = "Dependency cleanup: " + _remove_plugin_dependencies(stem)
    except Exception as exc:
        LOGS.exception("Dependency cleanup failed for %s", stem)
        dependency_note = "Dependency cleanup warning: " + type(exc).__name__ + ": " + str(exc)

    documents = _document_db_read()
    documents = {key: value for key, value in documents.items() if value != stem}
    try:
        _document_db_write(documents)
    except Exception:
        LOGS.exception("Could not update plugin document mapping")

    result = (
        f"Plugin uninstalled: {stem}.py\n"
        f"Event handlers detected: {len(handler_ids)}\n"
        f"Help entries removed: {len(help_entries)}\n"
        f"{dependency_note}"
    )
    if unload_warning:
        result += "\nUnload warning: " + unload_warning
    await _send_result(event, result)


async def _list_plugins(event):
    if not _authorized(event) or event.chat_id != _log_chat():
        return
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(p.name for p in PLUGIN_DIR.glob("*.py") if p.name != "__init__.py")
    await _reply(event, "Installed plugins:\n" + ("\n".join(f"• {x}" for x in files) if files else "None"))

def _register(pattern, callback, incoming=False, sudo_ids=None):
    chat = _log_chat()
    if chat is None:
        LOGS.warning("Plugin manager disabled: BOTLOG_CHATID is not a numeric Log Group.")
        return
    if incoming:
        catub.add_event_handler(callback, events.NewMessage(
            incoming=True, chats=chat, from_users=list(sudo_ids or []), pattern=pattern
        ))
    else:
        catub.add_event_handler(callback, events.NewMessage(
            outgoing=True, chats=chat, pattern=pattern
        ))

def _register_all():
    if _log_chat() is None:
        return
    command_handlers = getattr(Config, "COMMAND_HAND_LER", ["."])
    sudo_handlers = getattr(Config, "SUDO_COMMAND_HAND_LER", command_handlers)
    sudo_ids = _ids(_sudousers_list())
    for prefix in (command_handlers if isinstance(command_handlers, (list, tuple)) else [command_handlers]):
        _register(_command_pattern([prefix], "install"), _install, incoming=False)
        _register(_command_pattern([prefix], "uninstall"), _uninstall, incoming=False)
        _register(_command_pattern([prefix], "plugins"), _list_plugins, incoming=False)
    for prefix in (sudo_handlers if isinstance(sudo_handlers, (list, tuple)) else [sudo_handlers]):
        if sudo_ids:
            _register(_command_pattern([prefix], "install"), _install, incoming=True, sudo_ids=sudo_ids)
            _register(_command_pattern([prefix], "uninstall"), _uninstall, incoming=True, sudo_ids=sudo_ids)
            _register(_command_pattern([prefix], "plugins"), _list_plugins, incoming=True, sudo_ids=sudo_ids)

# ❌ CAT Userbot-s import-times register not possible — init() function move
# _register_all()  ←  init()-

def init(client):
    _register_all()
