import shutil, re, unicodedata
from .utils import sanitize

def normalize_display_name(name: str) -> str:
    s = name.replace("\r", "").replace("\n", "␠").replace("\t", "␠")
    s = "".join(ch for ch in s if ch.isprintable() and not unicodedata.category(ch).startswith("C"))
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

def clamp_to_terminal(s: str, reserve: int = 60) -> str:
    cols = shutil.get_terminal_size(fallback=(120, 24)).columns
    maxw = max(10, cols - reserve)
    return s if len(s) <= maxw else (s[:maxw-1] + "…")

def print_table(items):
    if not items:
        print("(empty)"); return
    for i, it in enumerate(items, start=1):
        typ = "DIR " if it.get("mimeType") == "application/vnd.google-apps.folder" else it.get("mimeType","")[:28]
        mod = it.get("modifiedTime","")[:19].replace("T"," ")
        disp = clamp_to_terminal(normalize_display_name(it.get("name","")))
        print(f"{i:>3}. {typ:<32} {mod:<19} {disp}")
