from . import command
from ..api import download_file
from ..utils import parse_selection, select_by_glob
from ..api import get_meta

@command("get", "get <#|#-#|#,#,...|glob>  - download by index/range/list or glob")
def handle(ctx, args):
    if not args:
        print("Usage: get <#|#-#|#,#,...|glob>"); return
    if not ctx.items:
        print("(no items in current view; run ls to fill the view first)"); return
    sel = " ".join(args)
    if any(ch in sel for ch in "*?[]"):
        idx_list = select_by_glob(sel, ctx.items)
        if not idx_list:
            print(f"(no matches for pattern '{sel}')"); return
    else:
        idx_list = parse_selection(sel, len(ctx.items))
    ok = skipped = failed = 0
    for idx in idx_list:
        target = ctx.items[idx]
        if target.get("mimeType") == "application/vnd.google-apps.folder":
            print(f"↷ Skipping folder: {target['name']}"); skipped += 1; continue
        try:
            print(f"↓ {target['name']}")
            path = download_file(ctx.svc, target)
            ok += 1
        except Exception as e:
            print(f"   [!] Failed: {e}"); failed += 1
    print(f"[✓] Completed: {ok} file(s).  Skipped folders: {skipped}.  Failed: {failed}.")
