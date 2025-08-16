from . import command
from ..api import list_children
from ..display import normalize_display_name, clamp_to_terminal
from ..api import get_meta
from ..colors import load_colorizer, ensure_default_config
from ..utils import normalize_compact_flags

_colorizer = None

def _color_item_name(item, text: str) -> str:
    """Apply style for a Drive item to the already formatted text."""
    global _colorizer
    if _colorizer is None:
        ensure_default_config()
        _colorizer = load_colorizer()
    style = _colorizer.style_for_item(item)
    return _colorizer.colorize(text, style)

def _render_name(item, raw_text: str) -> str:
    """
    Normalize and clamp plain text to terminal width, then colorize.
    This ensures escape sequences don't break width calculation.
    """
    disp = clamp_to_terminal(normalize_display_name(raw_text), reserve=0)
    return _color_item_name(item, disp)

def _parse_args(args):
    """
    Flags:
      -L N  or  -L<N>        -> max depth
      -d                     -> directories only
      --follow-shortcuts     -> follow Drive shortcuts
      N  or  #N              -> start index from current listing (1-based)
    Returns: (opts_dict, target_index_zero_based_or_None)
    """
    opts = {"L": 2, "dirs_only": False, "follow_shortcuts": False}
    target_idx = None
    i = 0
    while i < len(args):
        a = args[i]

        # -L3 OR -L 3
        if a.startswith("-L"):
            if len(a) > 2:               # -L3
                num = a[2:]
                if not num.isdigit():
                    raise ValueError("tree: -L requires a positive integer")
                opts["L"] = max(0, int(num))
                i += 1
                continue
            # -L 3
            if i + 1 >= len(args) or not args[i + 1].isdigit():
                raise ValueError("tree: -L requires a positive integer")
            opts["L"] = max(0, int(args[i + 1]))
            i += 2
            continue

        if a == "-d":
            opts["dirs_only"] = True
            i += 1
            continue

        if a == "--follow-shortcuts":
            opts["follow_shortcuts"] = True
            i += 1
            continue

        # Start index: allow "#7" OR "7"
        if a.startswith("#") or a.isdigit():
            try:
                n = int(a[1:]) if a.startswith("#") else int(a)
            except ValueError:
                raise ValueError("tree: invalid index")
            if n < 1:
                raise ValueError("tree: index must be >= 1")
            target_idx = n - 1
            i += 1
            continue

        # Unknown token
        raise ValueError(f"tree: unknown option '{a}'")

    return opts, target_idx

def _is_folder(item):
    return item.get("mimeType") == "application/vnd.google-apps.folder"

def _is_shortcut(item):
    return item.get("mimeType") == "application/vnd.google-apps.shortcut"

def _fetch_children(svc, folder_id):
    rows, token = [], None
    while True:
        batch, token = list_children(svc, folder_id, page_token=token)
        rows.extend(batch)
        if not token:
            break
    # sort: dirs first, then files, case-insensitive names
    rows.sort(key=lambda it: (not _is_folder(it), (it.get("name") or "").lower()))
    return rows

def _resolve_shortcut_target(svc, shortcut_item):
    """Return (target_meta_or_None, type_str) without raising."""
    try:
        # Get shortcutDetails; this field is only on files().get()
        meta = svc.files().get(
            fileId=shortcut_item["id"],
            fields="id,name,mimeType,shortcutDetails(targetId,targetMimeType)",
            supportsAllDrives=True,
        ).execute()
        det = meta.get("shortcutDetails") or {}
        tid = det.get("targetId")
        if not tid:
            return None, None
        targ = svc.files().get(
            fileId=tid,
            fields="id,name,mimeType",
            supportsAllDrives=True,
        ).execute()
        return targ, targ.get("mimeType")
    except Exception:
        return None, None

def _print_line(prefix, is_last, rendered_text: str):
    """Print a single tree line. `rendered_text` should already be formatted & colored."""
    branch = "└── " if is_last else "├── "
    print(prefix + branch + rendered_text)

def _next_prefix(prefix, is_last):
    return prefix + ("    " if is_last else "│   ")

def _walk(svc, start_item, depth_left, opts, prefix="", visited=None):
    """
    Print children of start_item (assumed folder or shortcut-resolved folder).
    """
    if depth_left == 0:
        return

    children = _fetch_children(svc, start_item["id"])
    if opts["dirs_only"]:
        children = [c for c in children if _is_folder(c)]

    for idx, child in enumerate(children):
        is_last = (idx == len(children) - 1)

        # Shortcuts handling
        if _is_shortcut(child):
            if not opts["follow_shortcuts"]:
                # Show as leaf with '->' note, don't traverse
                txt = _render_name(child, f"{child.get('name','(unnamed)')} -> shortcut")
                _print_line(prefix, is_last, txt)
                continue
            # Follow the target, but avoid cycles
            target, t_mime = _resolve_shortcut_target(svc, child)
            if not target:
                txt = _render_name(child, f"{child.get('name','(unnamed)')} -> [broken shortcut]")
                _print_line(prefix, is_last, txt)
                continue
            if visited is not None and target["id"] in visited:
                txt = _render_name(child, f"{child.get('name','(unnamed)')} -> {target.get('name','(target)')}  ↪ (seen)")
                _print_line(prefix, is_last, txt)
                continue
            # Print the shortcut name pointing to target
            shown = _render_name(child, f"{child.get('name','(unnamed)')} -> {target.get('name','(target)')}")
            _print_line(prefix, is_last, shown)
            if t_mime == "application/vnd.google-apps.folder" and depth_left > 1:
                if visited is not None:
                    visited.add(target["id"])
                _walk(svc, target, depth_left - 1, opts, _next_prefix(prefix, is_last), visited)
            continue

        # Normal items
        txt = _render_name(child, child.get("name", "(unnamed)"))
        _print_line(prefix, is_last, txt)

        # Recurse into folders
        if _is_folder(child) and depth_left > 1:
            _walk(svc, child, depth_left - 1, opts, _next_prefix(prefix, is_last), visited)

@command("tree", "tree [-L#] [-d] [--follow-shortcuts] [#]  - print a directory tree, limit recursion with -L")
def handle(ctx, args):
    """
    Prints a directory/file tree like Linux `tree`.
    Does not alter ctx.cwd or ctx.items.
    """
    args = normalize_compact_flags(args, int_flags=("-L",), assign_flags=())
    try:
        opts, maybe_idx = _parse_args(args)
    except ValueError as e:
        print(e); return

    # Figure out starting point
    if maybe_idx is not None:
        if not ctx.items:
            print("(no items in current view; run ls to fill the view first)"); return
        if not (0 <= maybe_idx < len(ctx.items)):
            print(f"Index out of range (1-{len(ctx.items)})"); return
        start = ctx.items[maybe_idx]
        # If an indexed file is chosen: print its name only
        if not _is_folder(start):
            print(normalize_display_name(start.get("name","(unnamed)"))); return
    else:
        # current working directory (folder)
        start = {"id": ctx.cwd["id"], "name": ctx.breadcrumb[-1], "mimeType": "application/vnd.google-apps.folder"}

    # Root line (colorized as folder)
    print(_render_name(start, start.get("name","(unnamed)")))
    visited = set([start["id"]]) if opts["follow_shortcuts"] else None
    _walk(ctx.svc, start, opts["L"], opts, prefix="", visited=visited)
