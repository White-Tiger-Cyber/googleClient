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
- Colorized output based on filetype. 

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

## Colorized Output

`googleClient` colorizes CLI output based on file type for easier scanning.
Colors are fully configurable via the tool’s config file.

### Config File Location
On first run, `googleClient` will automatically create a config file if it doesn’t exist.

Default path:
```
~/.config/gC/colors.toml
```

Override the path by setting the `GC_CONFIG` environment variable to any file path you prefer.

### Configuration Structure
Example `colors.toml`:
```toml
[general]
enabled = true

[colors]
folder = "bold_cyan"
shortcut = "bright_magenta"
google_doc = "bright_blue"
google_sheet = "bright_green"
google_slide = "bright_yellow"
google_drawing = "yellow"
pdf = "red"
msoffice = "blue"
image = "yellow"
text = "bright_black"
unknown = "white"

# Add rules (precedence top to bottom)
[[rule]]
ext = ".docx"
style = "blue"

[[rule]]
mime_prefix = "image/"
style = "yellow"

[[rule]]
mime_exact = "application/pdf"
style = "red"
```

### Supported Color Names
You can use any of:
```
black, red, green, yellow, blue, magenta, cyan, white
bright_black, bright_red, bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan, bright_white
```
Add `bold_` in front (e.g., `bold_cyan`) to make it bold.

### Notes
- Changes take effect the next time you run `googleClient`.
- If the config file is missing or invalid, it will be created/recreated with defaults.
- Delete the config file to reset to defaults.
- Set `NO_COLOR` to disable colors, or `FORCE_COLOR` to enable colors even when stdout isn’t a TTY.

## Future Features

The following features are planned for future releases of `googleClient`:

1. **`search` command enhancements**  
   - Add recursive search (`-r`) to search subfolders instead of only the current folder.  
   - Add recursion depth limit (`-L <n>`).  
   - Add MIME type filter support (e.g., only PDFs) via additional query logic or CLI options.

2. **`get` command enhancements**  
   - Add recursive mode (`-r`) to allow downloading from folders.  
   - Add recursion depth limit (`-L <n>`).  
   - Enable folders in recursive mode (currently skipped).

3. **Enhanced `help` command**  
   - Basic `help` shows minimal usage for each command (no switches).  
   - Display a note about `help <command>` for detailed usage.  
   - `help <command>` displays extended help including all switches/options and examples.

4. **`info` command enhancement**  
   - Request and display `shortcutDetails` from Google Drive API so it shows the target ID, MIME type, and other relevant information for shortcuts.

5. **`mimeType` display improvement in `print_table()`**  
   - Add `short_mime_types` toggle in config to optionally strip the `application/` or `application/vnd.google-apps.` prefix for better readability.  
   - When disabled, display full MIME type.  
   - Widen or dynamically size the column so more of the type is visible without truncation.
