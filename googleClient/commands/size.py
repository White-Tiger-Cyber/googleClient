from . import command
from ..api import list_children
from ..api import get_meta

def _parse_args(args):
    """
    size [-L#] [-B|-K|-M|-G] [--follow-shortcuts] [N]
      -L N or -L#       recursion depth (default: full depth)
      -B                force bytes
      -K                force kilobytes
      -M                force megabytes
      -G                force gigabytes
      --follow-shortcuts follow Drive shortcuts when encountered
      N                 start at item index N from current listing (1-based)
    """
    opts = {"L": None, "unit": None, "follow_shortcuts": False}
    target_idx = None
    i = 0
    while i < len(args):
        a = args[i]

        # depth
        if a.startswith("-L"):
            if len(a) > 2:
                num = a[2:]
                if not num.isdigit():
                    raise ValueError("size: -L requires a positive integer")
                opts["L"] = max(0, int(num))
                i += 1
                continue
            if i + 1 >= len(args) or not args[i+1].isdigit():
                raise ValueError("size: -L requires a positive integer")
            opts["L"] = max(0, int(args[i+1]))
            i += 2
            continue

        # units
        if a in ("-B", "-K", "-M", "-G"):
            unit_map = {"-B": "b", "-K": "k", "-M": "m", "-G": "g"}
            opts["unit"] = unit_map[a]
            i += 1
            continue

        if a == "--follow-shortcuts":
            opts["follow_shortcuts"] = True
            i += 1
            continue

        # numeric index (#N or N)
        if a.startswith("#") or a.isdigit():
            n = int(a[1:]) if a.startswith("#") else int(a)
            if n < 1:
                raise ValueError("size: index must be >= 1")
            target_idx = n - 1
            i += 1
            continue

        raise ValueError(f"size: unknown option '{a}'")

    return opts, target_idx

def _is_folder(item):
    return item.get("mimeType") == "application/vnd.google-apps.folder"

def _is_shortcut(item):
    return item.get("mimeType") == "application/vnd.google-apps.shortcut"

def _resolve_shortcut_target(svc, shortcut_item):
    try:
        meta = svc.files().get(
            fileId=shortcut_item["id"],
            fields="id,name,mimeType,shortcutDetails(targetId,targetMimeType)",
            supportsAllDrives=True,
        ).execute()
        det = meta.get("shortcutDetails") or {}
        tid = det.get("targetId")
        if not tid:
            return None
        targ = svc.files().get(
            fileId=tid,
            fields="id,name,mimeType,size",
            supportsAllDrives=True,
        ).execute()
        return targ
    except Exception:
        return None

def _walk_sum(svc, folder_id, depth_left, follow_shortcuts, visited=None):
    """
    Return (total_bytes, file_count, folder_count, skipped_native_count)
    """
    total = 0
    files = 0
    folders = 0
    skipped_native = 0

    token = None
    while True:
        batch, token = list_children(svc, folder_id, page_token=token)
        # sort not required for sum, but keeps traversal stable if you log later
        batch.sort(key=lambda it: (not _is_folder(it), (it.get("name") or "").lower()))
        for it in batch:
            if _is_shortcut(it):
                if not follow_shortcuts:
                    continue
                target = _resolve_shortcut_target(svc, it)
                if not target:
                    continue
                tid = target["id"]
                if visited is not None and tid in visited:
                    continue
                if visited is not None:
                    visited.add(tid)
                if _is_folder(target):
                    # respect depth if set
                    if depth_left is None or depth_left > 1:
                        subt = _walk_sum(
                            svc,
                            target["id"],
                            (None if depth_left is None else depth_left - 1),
                            follow_shortcuts,
                            visited,
                        )
                        t2, f2, d2, s2 = subt
                        total += t2; files += f2; folders += d2; skipped_native += s2
                    else:
                        folders += 1
                else:
                    size = target.get("size")
                    if size is not None:
                        total += int(size)
                        files += 1
                    else:
                        # Native file without size
                        skipped_native += 1
                continue

            if _is_folder(it):
                folders += 1
                if depth_left is None or depth_left > 1:
                    t2, f2, d2, s2 = _walk_sum(
                        svc,
                        it["id"],
                        (None if depth_left is None else depth_left - 1),
                        follow_shortcuts,
                        visited,
                    )
                    total += t2; files += f2; folders += d2; skipped_native += s2
            else:
                size = it.get("size")
                if size is not None:
                    total += int(size)
                    files += 1
                else:
                    skipped_native += 1
        if not token:
            break

    return total, files, folders, skipped_native

def _fmt_bytes(n, unit=None):
    if unit == "b":
        return f"{n} B"
    kb = 1024.0
    if unit == "k":
        return f"{n / kb:.2f} KB"
    if unit == "m":
        return f"{n / (kb**2):.2f} MB"
    if unit == "g":
        return f"{n / (kb**3):.2f} GB"
    # auto (human)
    if n < kb:
        return f"{n} B"
    if n < kb**2:
        return f"{n/kb:.2f} KB"
    if n < kb**3:
        return f"{n/(kb**2):.2f} MB"
    return f"{n/(kb**3):.2f} GB"

@command("size", "size [-L#] [-B|K|M|G] [--follow-shortcuts] [#]  - sum file sizes recursively")
def handle(ctx, args):
    try:
        opts, idx = _parse_args(args)
    except ValueError as e:
        print(e); return

    # starting node
    if idx is not None:
        if not ctx.items:
            print("(no items in current view)"); return
        if not (0 <= idx < len(ctx.items)):
            print(f"Index out of range (1-{len(ctx.items)})"); return
        start = ctx.items[idx]
        if not _is_folder(start):
            # Just a single file: report its size (if any)
            size = int(start.get("size") or 0)
            print(_fmt_bytes(size, opts["unit"]))
            if start.get("size") is None:
                print("(note: Google-native file size not reported by Drive API)")
            return
        start_id = start["id"]
        label = start.get("name","(unnamed)")
    else:
        start_id = ctx.cwd["id"]
        label = ctx.breadcrumb[-1]

    visited = set([start_id]) if opts["follow_shortcuts"] else None
    total, files, folders, skipped_native = _walk_sum(
        ctx.svc,
        start_id,
        opts["L"],  # None = full depth, int = levels
        opts["follow_shortcuts"],
        visited,
    )
    print(f"{label}")
    print(f"  Folders: {folders}  Files: {files}  (native-without-size: {skipped_native})")
    print(f"  Total:   {_fmt_bytes(total, opts['unit'])}")
