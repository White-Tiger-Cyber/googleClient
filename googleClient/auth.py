import os, sys, json, base64, stat
from google.oauth2 import service_account
from googleapiclient.discovery import build
from .constants import SCOPES

def build_service(key_file: str | None, user: str):
    info = None
    if os.environ.get("SA_JSON_B64"):
        info = json.loads(base64.b64decode(os.environ["SA_JSON_B64"]))
    elif os.environ.get("SA_JSON"):
        info = json.loads(os.environ["SA_JSON"])
    elif key_file:
        try:
            mode = os.stat(key_file).st_mode
            if mode & (stat.S_IRWXG | stat.S_IRWXO):
                print(f"[!] Refusing insecure key file perms on {key_file}. Run: chmod 600 {key_file}", file=sys.stderr)
                sys.exit(1)
        except FileNotFoundError:
            print(f"[!] Key file not found: {key_file}", file=sys.stderr)
            sys.exit(1)
    else:
        print("[!] Provide credentials via SA_JSON_B64 / SA_JSON env, or pass --key path", file=sys.stderr)
        sys.exit(1)

    if info:
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)

    delegated = creds.with_subject(user)
    return build("drive", "v3", credentials=delegated)
