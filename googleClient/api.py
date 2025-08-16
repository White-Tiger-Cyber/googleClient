from googleapiclient.http import MediaIoBaseDownload
from .constants import EXPORT_MAP
import io, os

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
    name = item["name"]
    mime = item["mimeType"]
    if mime in EXPORT_MAP:
        export_type, ext = EXPORT_MAP[mime]
        req = svc.files().export_media(fileId=item["id"], mimeType=export_type)
        out_path = os.path.join(outdir, f"{name}{ext}")
    else:
        req = svc.files().get_media(fileId=item["id"])
        root, ext = os.path.splitext(name)
        out_path = os.path.join(outdir, name if ext else f"{name}.bin")
    with io.FileIO(out_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, req)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return out_path
