from . import command
from datetime import datetime, timedelta, timezone

@command("recent", "recent [hours]  - list files modified in last N hours (default 48)")
def handle(ctx, args):
    hours = int(args[0]) if args else 48
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    q = f"modifiedTime >= '{since}' and trashed=false"
    resp = ctx.svc.files().list(
        q=q,
        fields="files(id,name,mimeType,modifiedTime,size)",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        corpora="allDrives",
        pageSize=200,
    ).execute()
    res = resp.get("files", [])
    res.sort(key=lambda x: x.get("modifiedTime",""), reverse=True)
    from ..display import print_table
    print_table(res)
    ctx.items = res
