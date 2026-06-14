#!/usr/bin/env python3
"""Public-safety audit for the LLM Wiki.

Fails (exit 1) on obvious secrets, private keys, machine-local absolute paths,
and committed plugin/cache state. Standard library only. Non-mutating.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

# Directories / paths we never want committed.
FORBIDDEN_PATHS = [
    ".obsidian/plugins",
    ".obsidian/cache",
    ".obsidian/logs",
]
FORBIDDEN_NAME_RE = re.compile(r"workspace.*\.json$")

# File extensions to scan for secret-like content.
TEXT_EXTS = {".md", ".py", ".sh", ".json", ".jsonl", ".txt", ".yml", ".yaml", ".cfg", ".ini", ".toml"}

# Skip scanning these (binary / vendor / vcs).
SKIP_DIRS = {".git", "Raw/Files", ".obsidian"}

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"), "private key block"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key id"),
    (re.compile(r"\bASIA[0-9A-Z]{16}\b"), "AWS temporary key id"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "API secret token (sk-...)"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "GitHub personal access token"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*\S+"), "AWS secret access key"),
    (re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{6,}['\"]"), "hardcoded credential"),
]

# Machine-local absolute paths (allow them only inside fenced/example contexts is
# too lenient; we flag real home paths but ignore generic placeholders).
LOCAL_PATH_RE = re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/")
# Allow obvious placeholders.
PLACEHOLDER_RE = re.compile(r"/(?:home|Users)/(?:USER|username|user|youruser|me|example)/")

# This audit script itself contains the patterns above; skip self.
SELF = Path(__file__).resolve()


def in_skip_dir(rel_posix):
    for d in SKIP_DIRS:
        if rel_posix == d or rel_posix.startswith(d + "/"):
            return True
    return False


def scan():
    problems = []

    for fp in FORBIDDEN_PATHS:
        p = ROOT / fp
        # Only a problem if tracked content exists (we ignore via .gitignore,
        # but flag if present and not ignored).
        if p.exists() and any(p.rglob("*")):
            # Check git is ignoring it; if .gitignore covers it, that's fine.
            problems.append(f"{fp}/ contains files (should be git-ignored, not committed)")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.resolve().relative_to(ROOT).as_posix()
        if in_skip_dir(rel):
            continue
        if FORBIDDEN_NAME_RE.search(path.name) and rel.startswith(".obsidian"):
            problems.append(f"{rel}: obsidian workspace file should not be committed")
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        if path.resolve() == SELF:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for pat, label in SECRET_PATTERNS:
                if pat.search(line):
                    problems.append(f"{rel}:{line_no}: possible {label}")
            for m in LOCAL_PATH_RE.finditer(line):
                snippet = line[max(0, m.start() - 0): m.end() + 8]
                if PLACEHOLDER_RE.search(line):
                    continue
                problems.append(f"{rel}:{line_no}: machine-local path '{m.group(0)}...'")
    return problems


def main():
    problems = scan()
    # De-duplicate while preserving order.
    seen = set()
    unique = []
    for p in problems:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    if unique:
        for p in unique:
            print(f"{RED}AUDIT{RESET}: {p}")
        print(f"{RED}audit_public: {len(unique)} issue(s){RESET}")
        return 1
    print(f"{GREEN}audit_public: ok{RESET} — no secrets, local paths, or cache state found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
