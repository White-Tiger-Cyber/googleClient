import argparse, sys
from .auth import build_service
from .repl import loop, Ctx

def main():
    ap = argparse.ArgumentParser(description="Google Drive impersonation shell (Domain-wide Delegation)")
    ap.add_argument("--key", required=False, help="Path to service_account.json (omit if using SA_JSON_B64/SA_JSON)")
    ap.add_argument("--user", required=True, help="User to impersonate (email)")
    args = ap.parse_args()

    try:
        svc = build_service(args.key, args.user)
        about = svc.about().get(fields="user(emailAddress,displayName)").execute()
        print(f"Connected as: {about['user']['emailAddress']} ({about['user']['displayName']})")
        loop(Ctx(svc, args.user))
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)
