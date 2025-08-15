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
gC --user someone@yourdomain.com
```

---

## Setup

### 1. Create a Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new **Project** (or use an existing one).
3. Navigate to **IAM & Admin → Service Accounts**.
4. Click **Create Service Account** and give it a name.
5. Assign the role `Google Drive Viewer` (or required scope for your script).
6. Click **Done**.

### 2. Create and Download the Key
1. In the Service Accounts list, click your new account.
2. Go to the **Keys** tab.
3. Click **Add Key → Create New Key**.
4. Choose **JSON** and click **Create**.
5. Save this file as `service_account.json` in your project directory.

**Security note:**  
If stored on disk, restrict permissions:
```bash
chmod 600 service_account.json
```
Alternatively, store it securely in an environment variable:
```bash
export SA_JSON_B64="$(base64 -w0 service_account.json)"
```

### 3. Enable APIs
1. In Google Cloud Console, go to **APIs & Services → Library**.
2. Enable the **Google Drive API**.

---

## Troubleshooting
- Ensure your `service_account.json` is valid and has the correct scope.
- Double-check API is enabled for the project.
- Confirm environment variables are correctly set.

---

## Usage Examples
```bash
gC --user alice@yourdomain.com
ls
get *.pdf
search projectX
recent
```
