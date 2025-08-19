from googleapiclient.http import MediaIoBaseDownload
from .constants import EXPORT_MAP
import io, os
from .utils import sanitize

def list_children(svc, parent_id, page_token=None, query_extra=""):
    q = f"'{parent_id}' in parents and trashed=false"
    if query_extra:
        q = f"({q}) and ({query_extra})"
    resp = svc.files().list(
        q=q,
        fields="nextPageToken, files(id,name,mimeType,modifiedTime,size,owners(emailAddress,displayName),permissions(emailAddress,role,displayName,domain),driveId)",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        corpora="allDrives",
        pageSize=200,
        pageToken=page_token
    ).execute()
    return resp.get("files", []), resp.get("nextPageToken")

def get_meta(svc, file_id):
    return svc.files().get(
        fileId=file_id,
        fields=(
            "id,name,mimeType,modifiedTime,size,webViewLink,driveId,parents,"
            "owners(emailAddress,displayName),"
            "permissions(emailAddress,role,displayName,domain),"
            "shortcutDetails(targetId,targetMimeType,targetResourceKey)"
        ),
        supportsAllDrives=True
    ).execute()

def download_file(svc, item, outdir="."):
    """
    Download a Drive item to outdir. Handles Google-native docs via export.
    Guarantees: filename available, sanitized, and parent directory exists.
    """
    file_id = item["id"]

    # Ensure we have name & mimeType; fetch if missing
    name = item.get("name")
    mime = item.get("mimeType")
    if not name or not mime:
        meta = svc.files().get(
            fileId=file_id,
            fields="id,name,mimeType",
            supportsAllDrives=True,
        ).execute()
        name = name or meta.get("name") or "untitled"
        mime = mime or meta.get("mimeType") or "application/octet-stream"

    # Sanitize filename and ensure output dir exists
    safe_name = sanitize(name)
    os.makedirs(outdir, exist_ok=True)

    # Export vs binary download
    if mime in EXPORT_MAP:
        export_type, ext = EXPORT_MAP[mime]
        req = svc.files().export_media(fileId=file_id, mimeType=export_type)
        out_path = os.path.join(outdir, f"{safe_name}{ext}")
    else:
        req = svc.files().get_media(fileId=file_id)
        root, ext = os.path.splitext(safe_name)
        out_path = os.path.join(outdir, safe_name if ext else f"{safe_name}.bin")

    with io.FileIO(out_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, req)
        done = False
        while not done:
            status, done = downloader.next_chunk()

    return out_path
