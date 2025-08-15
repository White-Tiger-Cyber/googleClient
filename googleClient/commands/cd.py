from . import command
from ..api import get_meta

@command("cd", "cd <#|..|/>  - enter folder by number, go up, or root")
def handle(ctx, args):
    if not args or args[0] == "/":
        ctx.cwd = {"id": "root", "name": "My Drive"}
        ctx.breadcrumb = ["My Drive"]
        ctx.items = []
        return
    if args[0] == "..":
        if len(ctx.breadcrumb) > 1:
            meta = get_meta(ctx.svc, ctx.cwd["id"])
            parents = meta.get("parents") or []
            if parents:
                parent_id = parents[0]
                ctx.cwd = {"id": parent_id, "name": "(parent)"}
                ctx.breadcrumb.pop()
            else:
                ctx.cwd = {"id": "root", "name": "My Drive"}
                ctx.breadcrumb = ["My Drive"]
        ctx.items = []
        return
    idx = int(args[0]) - 1
    if not ctx.items:
        print("(no items in current view)"); return
    if not (0 <= idx < len(ctx.items)):
        print(f"Index out of range (1-{len(ctx.items)})"); return
    target = ctx.items[idx]
    if target.get("mimeType") != "application/vnd.google-apps.folder":
        print("Not a folder."); return
    ctx.cwd = {"id": target["id"], "name": target["name"]}
    ctx.breadcrumb.append(target["name"])
    ctx.items = []
