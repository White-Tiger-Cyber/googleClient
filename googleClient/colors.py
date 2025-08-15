# googleClient/colors.py
from __future__ import annotations
import os, sys, tomllib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Optional Windows nicety if user has colorama
try:
    import colorama  # type: ignore
    colorama.just_fix_windows_console()
except Exception:
    pass

ANSI = {
    "reset": "\x1b[0m",
    "bold": "\x1b[1m",
    "black": "\x1b[30m","red":"\x1b[31m","green":"\x1b[32m","yellow":"\x1b[33m",
    "blue":"\x1b[34m","magenta":"\x1b[35m","cyan":"\x1b[36m","white":"\x1b[37m",
    "bright_black":"\x1b[90m","bright_red":"\x1b[91m","bright_green":"\x1b[92m",
    "bright_yellow":"\x1b[93m","bright_blue":"\x1b[94m","bright_magenta":"\x1b[95m",
    "bright_cyan":"\x1b[96m","bright_white":"\x1b[97m",
}

DEFAULT_STYLES = {
    "folder": "bold_cyan",
    "shortcut": "bright_magenta",
    "google_doc": "bright_blue",
    "google_sheet": "bright_green",
    "google_slide": "bright_yellow",
    "google_drawing": "yellow",
    "pdf": "red",
    "msoffice": "blue",
    "image": "yellow",
    "text": "bright_black",
    "unknown": "white",
}

GOOGLE_NATIVE = {
    "application/vnd.google-apps.document": "google_doc",
    "application/vnd.google-apps.spreadsheet": "google_sheet",
    "application/vnd.google-apps.presentation": "google_slide",
    "application/vnd.google-apps.drawing": "google_drawing",
}

@dataclass
class Rule:
    kind: str               # "mime_prefix" | "mime_exact" | "ext"
    value: str
    style: str

def _config_path() -> str:
    if os.environ.get("GC_CONFIG"):
        return os.path.expanduser(os.environ["GC_CONFIG"])
    base = os.path.join(os.path.expanduser("~"), ".config", "gC")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "colors.toml")

def _isatty() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

class Colorizer:
    def __init__(self, enabled: bool, styles: Dict[str, str], rules: List[Rule]):
        self.enabled = enabled
        self.styles = styles
        self.rules = rules

    def colorize(self, text: str, style_name: Optional[str]) -> str:
        if not self.enabled or not style_name:
            return text
        bold = style_name.startswith("bold_")
        key = style_name[5:] if bold else style_name
        code = ANSI.get(key)
        if not code:
            return text
        return (ANSI["bold"] if bold else "") + code + text + ANSI["reset"]

    def style_for_item(self, item: Dict[str, Any]) -> str:
        mt = (item.get("mimeType") or "").lower()
        name = (item.get("name") or "")

        if mt == "application/vnd.google-apps.folder":
            return self.styles.get("folder", "bold_cyan")
        if mt == "application/vnd.google-apps.shortcut":
            return self.styles.get("shortcut", "bright_magenta")
        if mt in GOOGLE_NATIVE:
            key = GOOGLE_NATIVE[mt]
            return self.styles.get(key, DEFAULT_STYLES[key])

        for r in self.rules:
            if r.kind == "mime_exact" and mt == r.value:
                return r.style
            if r.kind == "mime_prefix" and mt.startswith(r.value):
                return r.style
            if r.kind == "ext" and name.lower().endswith(r.value):
                return r.style

        if mt == "application/pdf" or name.lower().endswith(".pdf"):
            return self.styles.get("pdf", "red")
        if mt.startswith("image/"):
            return self.styles.get("image", "yellow")
        if name.lower().endswith((".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx")):
            return self.styles.get("msoffice", "blue")
        if mt.startswith("text/"):
            return self.styles.get("text", "bright_black")

        return self.styles.get("unknown", "white")

def _load_toml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)

DEFAULT_CONFIG_TEXT = """# gC color configuration (TOML)
[general]
enabled = true

[colors]
folder = "bold_cyan"
shortcut = "bright_magenta"
google_doc = "bright_blue"
google_sheet = "bright_green"
google_slide = "bright_yellow"
google_drawing = "yellow"
pdf = "red"
msoffice = "blue"
image = "yellow"
text = "bright_black"
unknown = "white"

# Add rules (precedence top to bottom)
[[rule]]
ext = ".docx"
style = "blue"

[[rule]]
mime_prefix = "image/"
style = "yellow"

[[rule]]
mime_exact = "application/pdf"
style = "red"
"""

def ensure_default_config():
    p = _config_path()
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_TEXT)

def load_colorizer(disable_flag: bool = False) -> Colorizer:
    ensure_default_config()
    cfg = _load_toml(_config_path())
    general = (cfg.get("general") or {})
    user_styles = (cfg.get("colors") or {})
    rules_cfg = (cfg.get("rule") or [])

    styles = DEFAULT_STYLES.copy()
    styles.update({k: str(v) for k, v in user_styles.items()})

    rules: List[Rule] = []
    for r in rules_cfg:
        if "mime_prefix" in r:
            rules.append(Rule("mime_prefix", r["mime_prefix"].lower(), str(r["style"])))
        elif "mime_exact" in r:
            rules.append(Rule("mime_exact", r["mime_exact"].lower(), str(r["style"])))
        elif "ext" in r:
            v = str(r["ext"]).lower()
            if not v.startswith("."):
                v = "." + v
            rules.append(Rule("ext", v, str(r["style"])))

    enabled = not disable_flag
    if os.environ.get("NO_COLOR"):
        enabled = False
    if not _isatty() and not os.environ.get("FORCE_COLOR"):
        enabled = False
    if isinstance(general.get("enabled"), bool):
        enabled = enabled and general["enabled"]

    return Colorizer(enabled=enabled, styles=styles, rules=rules)
