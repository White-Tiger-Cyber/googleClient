from . import command
from ..api import list_children, download_file
from ..utils import sanitize, normalize_compact_flags, parse_selection, select_by_glob
from collections import deque
from fnmatch import fnmatch
import os

@command(
    "mget",
    "mget <*|#|#-#|#,#,...|glob>... [-r] [-L <n>] [--follow-shortcuts] [--into <dir>]  - download selected items; optionally recurse into folders"
)
def handle(ctx, args):
    # Need a current listing for indices/globs
    if not ctx.items:
        print("(no items in current view; run ls to fill the view first)"); return
    if not args:
        print("Usage: mget <*|#|#-#|#,#,...|glob>... [-r] [-L <n>] [--follow-shortcuts] [--into <dir>]"); return

    # Normalize compact flags so -L1 == -L 1 and --into=/x == --into /x
    args = normalize_compact_flags(args, int_flags=("-L",), assign_flags=("--into",))

    # One-pass parse (flags can appear anywhere)
    selectors = []
    recursive = False
    max_depth = None    # None = unlimited; 0 = only the selected items
    follow_shortcuts = False
    out_root = os.getcwd()

    i = 0
    while i < len(args):
        tok = args[i]
        if tok in ("-r", "--recursive"):
            recursive = True; i += 1; continue
        if tok == "-L":
            if i + 1 >= len(args):
                print("(-L) requires a non-negative integer"); return
            try:
                max_depth = int(args[i+1])
                if max_depth < 0: raise ValueError
            except Exception:
                print("(-L) requires a non-negative integer"); return
            i += 2; continue
        if tok == "--follow-shortcuts":
            follow_shortcuts = True; i += 1; continue
        if tok == "--into":
            if i + 1 >= len(args):
                print("--into requires a directory path"); return
            out_root = args[i+1]; i += 2; continue
        if tok.startswith("-"):
            print(f"Unknown option: {tok}"); return
        # selector
        selectors.append(tok); i += 1

    if not selectors:
        print("Usage: mget <*|#|#-#|#,#,...|glob>... [-r] [-L <n>] [--follow-shortcuts] [--into <dir>]"); return

    os.makedirs(out_root, exist_ok=True)

    def is_folder(it):   return it.get("mimeType") == "application/vnd.google-apps.folder"
    def is_shortcut(it): return it.get("mimeType") == "application/vnd.google-apps.shortcut"

    # Resolve shortcut target meta (only when following)
    def resolve_shortcut_target(item):
        if not follow_shortcuts:
            return None
        try:
            meta = ctx.svc.files().get(
                fileId=item["id"],
                fields="shortcutDetails(targetId,targetMimeType)",
                supportsAllDrives=True,
            ).execute()
            det = meta.get("shortcutDetails") or {}
            tid, tmime = det.get("targetId"), det.get("targetMimeType")
            if not tid:
                return None
            return {"id": tid, "name": item.get("name","(unnamed)"), "mimeType": tmime}
        except Exception as e:
            print(f"   [!] failed to resolve shortcut for {item.get('name','(unnamed)')}: {e}")
            return None

    # Expand selectors against ctx.items
    selected = []

    for sel in selectors:
        sel = sel.strip()
        if sel == "*":
            selected.extend(ctx.items)
            continue
        # ranges / comma lists
        try:
            if any(ch in sel for ch in (",","-")) and all(c.isdigit() or c in ",-" for c in sel):
                for idx0 in parse_selection(sel, len(ctx.items)):   # returns 0-based indices
                    selected.append(ctx.items[idx0])
                continue
        except Exception:
            pass
        # single index
        if sel.isdigit():
            n = int(sel)
            if 1 <= n <= len(ctx.items):
                selected.append(ctx.items[n-1])
            else:
                print(f"Index out of range (1–{len(ctx.items)}): {n}")
            continue
        # glob by name
        idxs = select_by_glob(sel, ctx.items)
        if idxs:
            for i0 in idxs: selected.append(ctx.items[i0])
            continue
        print(f"(no matches for selector '{sel}')")

    if not selected:
        print("(no matching items)"); return

    # BFS queue entries: (id, display_name, relpath, depth, mime)
    q = deque()
    for it in selected:
        if is_shortcut(it) and follow_shortcuts:
            tgt = resolve_shortcut_target(it)
            if tgt: it = tgt
        q.append((it.get("id"), it.get("name") or "unnamed", "", 0, it.get("mimeType")))

    downloaded = skipped = 0

    while q:
        file_id, name, rel, depth, mime = q.popleft()
        safe_name = sanitize(name)
        outdir = os.path.join(out_root, rel)
        os.makedirs(outdir, exist_ok=True)

        # Folder handling
        if mime == "application/vnd.google-apps.folder":
            if not recursive:
                skipped += 1
                continue
            if max_depth is not None and depth >= max_depth:
                continue
            token = None
            while True:
                batch, token = list_children(ctx.svc, file_id, page_token=token)
                for child in batch:
                    cmime = child.get("mimeType")
                    cname = child.get("name") or "unnamed"
                    if is_shortcut(child) and follow_shortcuts:
                        tgt = resolve_shortcut_target(child)
                        if tgt:
                            child = tgt
                            cmime = child.get("mimeType")
                            cname = child.get("name") or "unnamed"
                    child_rel = os.path.join(rel, safe_name)
                    q.append((child.get("id"), cname, child_rel, depth+1, cmime))
                if not token: break
            continue

        # File (or exportable Google doc)
        try:
            download_file(ctx.svc, {"id": file_id, "name": name, "mimeType": mime}, outdir=outdir)
            downloaded += 1
            print(f"↓ {os.path.join(rel, safe_name)}")
        except Exception as e:
            print(f"   [!] failed {name}: {e}")

    print(f"[✓] Downloaded {downloaded} file(s).  Skipped folders: {skipped}.")
