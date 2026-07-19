#!/usr/bin/env python3
"""Shared note-authoring utilities for LLM Wiki plugin tools.

This module ships with the core wiki template (scripts/wiki_notes.py) so plugin tool scripts
(e.g. quiz_tool.py, mtg_tool.py) can import it as a sibling instead of each carrying their own
copy of these helpers:

    from wiki_notes import slug, emit_frontmatter, write_note, run_gate, ...

It provides slug/date helpers, the YAML-subset frontmatter emitter that matches wiki_tool.py,
frontmatter/section readers, surgical in-place frontmatter + managed-block editors, and a
`run_gate()` that shells the core maintenance checks. `ROOT` resolves to the vault root because
this file lives in <vault>/scripts/.
"""

import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI_TOOL = ROOT / "scripts" / "wiki_tool.py"


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def today():
    return datetime.date.today().isoformat()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def slug(name):
    """Kebab-case slug. Collapses `//` (e.g. double-faced card names) before other runs."""
    s = str(name).replace("//", "-")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "untitled"


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def _norm(text):
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


# --------------------------------------------------------------------------- #
# Frontmatter emission (matches wiki_tool.py's YAML subset)
# --------------------------------------------------------------------------- #
# Characters that, as the FIRST char of a plain YAML scalar, change its meaning.
_YAML_INDICATOR_START = set("!&*?|>%@`\"'#,[]{}:- ")


def _scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return '""'
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    needs_quote = (
        s == ""
        or s != s.strip()
        or s[0] in _YAML_INDICATOR_START
        or re.search(r'[:#\[\]{}"\',]', s)
    )
    if needs_quote:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def emit_frontmatter(data):
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                lines.extend(f"  - {_scalar(v)}" for v in value)
        else:
            lines.append(f"{key}: {_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def existing_created(path):
    """Preserve an existing note's `created`/`Created` date so re-runs are idempotent."""
    path = Path(path)
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^[Cc]reated:\s*(.+)$", line.strip())
        if m:
            return m.group(1).strip().strip("\"'")
    return None


def write_note(path, frontmatter, body):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(emit_frontmatter(frontmatter) + "\n\n" + body.rstrip() + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Frontmatter / body reading + surgical in-place updates
# --------------------------------------------------------------------------- #
def read_frontmatter(path):
    """Parse the top-level scalar frontmatter fields (list items are skipped)."""
    fm = {}
    path = Path(path)
    if not path.exists():
        return fm
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return fm
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m:
            val = m.group(2).strip()
            if val:
                val = val.strip("\"'")
            fm[m.group(1)] = val
    return fm


def read_title(path):
    path = Path(path)
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def read_section(path, header):
    """Return the text under a `## <header>` heading, up to the next `## ` or end."""
    path = Path(path)
    if not path.exists():
        return ""
    out, capture = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            capture = line[3:].strip().lower() == header.lower()
            continue
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def set_frontmatter_fields(text, updates):
    """Update (or insert) top-level scalar frontmatter fields, leaving the rest intact."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return text
    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if close is None:
        return text
    present = {}
    for i in range(1, close):
        m = re.match(r"^([A-Za-z0-9_]+):", lines[i])
        if m:
            present[m.group(1)] = i
    inserts = []
    for key, value in updates.items():
        newline = f"{key}: {_scalar(value)}"
        if key in present:
            lines[present[key]] = newline
        else:
            inserts.append(newline)
    if inserts:
        lines[close:close] = inserts
    return "\n".join(lines)


def replace_block(text, start, end, inner):
    """Replace the managed region between markers (inclusive) with `inner`, preserving prose."""
    block = start + "\n" + inner + "\n" + end if inner else start + "\n" + end
    pattern = re.escape(start) + r".*?" + re.escape(end)
    if re.search(pattern, text, re.S):
        return re.sub(pattern, lambda _m: block, text, count=1, flags=re.S)
    return text.rstrip() + "\n\n" + block + "\n"


def update_managed(path, start, end, entries, fm_updates):
    """Rewrite a note's managed list + selected frontmatter fields in place."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    text = replace_block(text, start, end, "\n".join(entries))
    text = set_frontmatter_fields(text, {**fm_updates, "updated": today()})
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def extract_managed_block(text, start, end):
    """Inner text between two markers (exclusive), or None if the markers aren't present."""
    m = re.search(re.escape(start) + r"\n?(.*?)\n?" + re.escape(end), text or "", re.S)
    return m.group(1) if m else None


# --------------------------------------------------------------------------- #
# Maintenance gate (shells the core wiki_tool.py checks)
# --------------------------------------------------------------------------- #
DEFAULT_GATE = [["build"], ["lint"], ["source-scan", "--update", "--accept-covered"], ["source-lint"]]


def run_gate(steps=None):
    """Run the core maintenance gate so a plugin command leaves the vault green.

    `source-scan --update` re-syncs the source manifest (harmless for source-exempt plugins) so
    pre-existing drift doesn't surface as a plugin-command failure.
    """
    steps = steps or DEFAULT_GATE
    for i, step in enumerate(steps, 1):
        print(f"  gate [{i}/{len(steps)}]: {' '.join(step)}", file=sys.stderr)
        proc = subprocess.run([sys.executable, str(WIKI_TOOL)] + step)
        if proc.returncode != 0:
            print(f"\ngate failed at: wiki_tool.py {' '.join(step)}", file=sys.stderr)
            return proc.returncode
    return 0
