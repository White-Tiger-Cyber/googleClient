from . import command
from ..api import list_children
from ..display import print_table

@command("search", "search \"<namepart>\"  - search under current folder by name")
def handle(ctx, args):
    q = " ".join(args).strip()
    if not (q.startswith('"') and q.endswith('"') and len(q) >= 2):
        print('Usage: search "namepart"'); return
    term = q[1:-1]
    safe = term.replace("'", "\\'")
    extra = f"name contains '{safe}'"
    results, token = [], None
    while True:
        batch, token = list_children(ctx.svc, ctx.cwd["id"], page_token=token, query_extra=extra)
        results.extend(batch)
        if not token: break
    if not results:
        print("(no matches)"); return
    print_table(results)
    ctx.items = results
