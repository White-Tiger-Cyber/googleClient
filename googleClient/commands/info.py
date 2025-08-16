# googleClient/commands/info.py
import json
from . import command
from ..api import get_meta

@command("info", "info <#>  - show detailed metadata for a file/folder by index")
def handle(ctx, args):
    # Require an index and a current listing
    if not args:
        print("Usage: info <#>"); return
    if not ctx.items:
        print("(no items in current view)"); return

    # Parse 1-based index safely and bounds-check
    try:
        idx_1based = int(args[0].strip())
    except Exception:
        print("Invalid index"); return

    if not (1 <= idx_1based <= len(ctx.items)):
        print(f"Invalid index (valid: 1–{len(ctx.items)})"); return

    target = ctx.items[idx_1based - 1]

    # Ask Drive for full metadata
    meta = get_meta(ctx.svc, target["id"])

    # Pretty-print stable, readable JSON
    print(json.dumps(meta, indent=2, sort_keys=True))
