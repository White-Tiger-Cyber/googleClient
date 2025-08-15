from . import command
from ..api import get_meta

@command("info", "info <#>  - show metadata for item")
def handle(ctx, args):
    if not args: print("Usage: info <#>"); return
    idx = int(args[0]) - 1
    if not ctx.items:
        print("(no items in current view)"); return
    target = ctx.items[idx]
    meta = get_meta(ctx.svc, target["id"])
    print(meta)
