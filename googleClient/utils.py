import os, re, hashlib

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

import fnmatch
def select_by_glob(pattern: str, items):
    pat = pattern.lower()
    idxs = []
    for i, it in enumerate(items):
        name = it.get("name","")
        if fnmatch.fnmatch(name.lower(), pat):
            idxs.append(i)
    return idxs
