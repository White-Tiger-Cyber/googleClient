import atexit, os, re
try:
    import readline
except ImportError:
    readline = None

from .commands import REGISTRY
from .display import print_table

class Ctx:
    def __init__(self, svc, user_email):
        self.svc = svc
        self.user_email = user_email
        self.cwd = {"id": "root", "name": "My Drive"}
        self.breadcrumb = ["My Drive"]
        self.items = []
        self.cache = {}

from .commands import REGISTRY

def show_help():
    # Build rows of (usage, desc) and compute column width
    rows = []
    for name in sorted(REGISTRY):
        hl = REGISTRY[name].get("help", "").strip()
        # Normalize: ensure usage starts with the command name
        if not hl or not hl.lower().startswith(name.lower()):
            usage = name if not hl else f"{name} {hl}"
        else:
            usage = hl
        # Split usage and description on the first ' - '
        if " - " in usage:
            left, right = usage.split(" - ", 1)
        else:
            left, right = usage, ""
        rows.append((left.strip(), right.strip()))

    # Compute left column width and print
    width = min(40, max(len(u) for u, _ in rows) if rows else 0)  # cap to keep tidy
    print("Commands:")
    for u, d in rows:
        if d:
            print(f"  {u.ljust(width)}  - {d}")
        else:
            print(f"  {u}")
    # Ensure help/quit always present & aligned
    extras = [("help", "this help"), ("quit", "exit")]
    for u, d in extras:
        print(f"  {u.ljust(width)}  - {d}")

def loop(ctx: Ctx):
    print(f"Impersonating: {ctx.user_email}")
    print("Type 'help' for commands. (Tip: run 'ls' to list the current folder)\n")

    # history
    if readline:
        safe_user = re.sub(r'[^A-Za-z0-9_.@-]', '_', ctx.user_email)
        histfile = os.path.expanduser(f"~/.gC_history_{safe_user}")
        readline.set_history_length(50)
        try:
            readline.read_history_file(histfile)
        except FileNotFoundError:
            pass
        atexit.register(lambda: readline.write_history_file(histfile))

    while True:
        try:
            line = input(f"[{ctx.breadcrumb[-1]} - {ctx.user_email}]$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if not line:
            continue
        parts = line.split()
        cmd, args = parts[0], parts[1:]
        if cmd in ("quit","exit"):
            return
        if cmd == "help":
            show_help()
            continue
        h = REGISTRY.get(cmd)
        if not h:
            print("Unknown command. Type 'help'."); continue
        try:
            h["fn"](ctx, args)
        except Exception as e:
            print(f"[!] {e}")
