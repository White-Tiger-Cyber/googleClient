from . import command
from ..api import list_children
from ..display import print_table

@command("ls", "ls [#]  - list current folder or list folder by index")
def handle(ctx, args):
    if not args:
        rows = ctx.cache.get(ctx.cwd["id"])
        if rows is None:
            rows, token = [], None
            while True:
                batch, token = list_children(ctx.svc, ctx.cwd["id"], page_token=token)
                rows += batch
                if not token: break
            ctx.cache[ctx.cwd["id"]] = rows
        print_table(rows)
        ctx.items = rows
        return
    # ls # (peek subfolder without changing cwd)
    idx = int(args[0]) - 1
    if not ctx.items:
        print("(no items in current view)"); return
    if not (0 <= idx < len(ctx.items)):
        print(f"Index out of range (1-{len(ctx.items)})"); return
    target = ctx.items[idx]
    if target.get("mimeType") != "application/vnd.google-apps.folder":
        print("That’s not a folder."); return
    rows, token = [], None
    while True:
        batch, token = list_children(ctx.svc, target["id"], page_token=token)
        rows += batch
        if not token: break
    print(f"[Listing: {target['name']}]")
    print_table(rows)
