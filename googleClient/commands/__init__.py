# googleClient/commands/__init__.py
REGISTRY = {}

def command(name, helpline):
    def deco(fn):
        REGISTRY[name] = {"fn": fn, "help": helpline}
        return fn
    return deco

# --- auto-import all command modules so decorators run ---
import pkgutil, importlib

for _finder, _name, _ispkg in pkgutil.iter_modules(__path__):
    # ignore private modules like __pycache__ or _something.py
    if not _name.startswith("_"):
        importlib.import_module(f"{__name__}.{_name}")
# --------------------------------------------------------
