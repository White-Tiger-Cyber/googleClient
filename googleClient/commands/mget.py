from . import command
from ..api import download_file

@command("mget", "mget *  - download all files (not folders) in current list")
def handle(ctx, args):
    if not args or args[0] != "*":
        print("Usage: mget *"); return
    if not ctx.items:
        print("(no items in current view)"); return
    count = 0
    for it in ctx.items:
        if it.get("mimeType") != "application/vnd.google-apps.folder":
            try:
                print(f"↓ {it['name']}")
                download_file(ctx.svc, it)
                count += 1
            except Exception as e:
                print(f"   [!] {e}")
    print(f"[✓] Downloaded {count} file(s).")
