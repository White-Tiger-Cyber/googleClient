from . import command
from ..api import get_meta

@command("perms", "perms <#>  - show permissions for item")
def handle(ctx, args):
    if not args: print("Usage: perms <#>"); return
    idx = int(args[0]) - 1
    if not ctx.items:
        print("(no items in current view; run ls to fill the view first)"); return
    target = ctx.items[idx]
    meta = get_meta(ctx.svc, target["id"])
    perms = meta.get("permissions") or []
    if not perms:
        print(" - (no explicit permissions listed)"); return
    for p in perms:
        who = p.get("emailAddress") or p.get("domain") or p.get("displayName") or "(link)"
        print(f" - {p.get('role','?'):10s} {who}")
