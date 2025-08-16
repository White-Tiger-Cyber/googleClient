import os, re, hashlib
import fnmatch

def sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip()

def parse_selection(sel: str, max_index: int):
    indices = set()
    parts = re.split(r'[,\s]+', sel.strip())
    for p in parts:
        if not p: continue
        if '-' in p:
            a, b = p.split('-', 1)
            if not a.isdigit() or not b.isdigit():
                raise ValueError(f"Bad range '{p}'")
            start, end = int(a), int(b)
            if start < 1 or end < 1 or start > max_index or end > max_index or start > end:
                raise ValueError(f"Out-of-range '{p}' (1..{max_index})")
            for i in range(start-1, end):
                indices.add(i)
        else:
            if not p.isdigit():
                raise ValueError(f"Bad index '{p}'")
            n = int(p)
            if n < 1 or n > max_index:
                raise ValueError(f"Out-of-range '{n}' (1..{max_index})")
            indices.add(n-1)
    return sorted(indices)

def select_by_glob(pattern: str, items):
    pat = pattern.lower()
    idxs = []
    for i, it in enumerate(items):
        name = it.get("name","")
        if fnmatch.fnmatch(name.lower(), pat):
            idxs.append(i)
    return idxs

def normalize_compact_flags(args, int_flags=("-L",), assign_flags=("--into",)):
    """
    Expand compact flags so '-L1' -> ['-L','1'] and '--into=/x' -> ['--into','/x'].
    - int_flags: short flags that take an integer immediately after them (e.g., -L)
    - assign_flags: long flags that may be passed as --flag=value
    """
    out = []
    for a in args:
        # Handle short int flags like -L1
        matched = False
        for f in int_flags:
            if a.startswith(f) and a != f:
                tail = a[len(f):]
                if tail.isdigit():
                    out.extend([f, tail])
                    matched = True
                    break
        if matched:
            continue

        # Handle --flag=value
        matched = False
        for f in assign_flags:
            prefix = f + "="
            if a.startswith(prefix):
                out.extend([f, a[len(prefix):]])
                matched = True
                break
        if matched:
            continue

        out.append(a)
    return out
