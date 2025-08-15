# googleClient

Interactive, read-only Google Drive shell for Google Workspace admins using **Domain-wide Delegation**.

## Features
- Impersonate any user (with DWD).
- `ls`, `ls #`, `cd`, `pwd`.
- `get` with **ranges** and **globs** (e.g. `get 5-9,11` or `get *.pdf`).
- `mget *` to download all files in the current list.
- `search`, `recent`, `info`, `perms`, `rawname`.
- History (last 50 commands) per user.
- Hardened secret loading from `SA_JSON_B64` / `SA_JSON` env or `--key` (0600).

## Quick start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
export SA_JSON_B64="$(base64 -w0 path/to/service_account.json)"
drive-dwd --user someone@yourdomain.com
```
