from . import command

@command("rawname", "rawname <#>  - show exact underlying name (repr)")
def handle(ctx, args):
    if not args: print("Usage: rawname <#>"); return
    idx = int(args[0]) - 1
    if not ctx.items:
        print("(no items in current view)"); return
    target = ctx.items[idx]
    print(repr(target.get("name","")))
