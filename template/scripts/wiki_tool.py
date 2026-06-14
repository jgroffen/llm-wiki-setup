#!/usr/bin/env python3
"""Deterministic tooling for the LLM Wiki.

Standard library only. Provides health checks, catalog/index builds, linting,
and source-manifest reconciliation.

Commands:
  doctor                         Non-mutating health check.
  build                          Generate catalog.jsonl, index.md, per-folder indexes.
  lint                           Validate compiled Wiki note frontmatter.
  source-scan [--update]         List Raw sources; optionally write the manifest.
  source-scan --update --accept-covered
                                 Update manifest, accepting current coverage state.
  source-lint                    Validate source frontmatter and coverage.
  source-delta                   Raw sources not represented in the manifest.
  source-coverage                Which Raw sources are covered by compiled notes.
  search-catalog --query "text"  Search compiled notes via the catalog.
  log --title "t" --details "d"  Add a log note under Wiki/Logs/.
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCES_DIR = ROOT / "Raw" / "Sources"
WIKI_DIR = ROOT / "Wiki"
WIKI_SUBDIRS = {
    "topic": WIKI_DIR / "Topics",
    "concept": WIKI_DIR / "Concepts",
    "entity": WIKI_DIR / "Entities",
    "log": WIKI_DIR / "Logs",
}
CATALOG = WIKI_DIR / "catalog.jsonl"
WIKI_INDEX = WIKI_DIR / "index.md"
MANIFEST = ROOT / "Schema" / "source-manifest.jsonl"

ALLOWED_TAGS = ("topic", "concept", "entity", "log")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


# --------------------------------------------------------------------------- #
# Minimal frontmatter parser (a small, predictable YAML subset)
# --------------------------------------------------------------------------- #
def _coerce(scalar):
    s = scalar.strip()
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1]
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("", "null", "~"):
        return ""
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def _split_inline_list(s):
    inner = s.strip()[1:-1].strip()
    if not inner:
        return []
    return [_coerce(part) for part in inner.split(",")]


def parse_frontmatter(text):
    """Return (frontmatter_dict, body_str). Empty dict if no frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    fm_lines = lines[1:end]
    body = "\n".join(lines[end + 1 :])

    data = {}
    i = 0
    while i < len(fm_lines):
        raw = fm_lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", raw)
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2).strip()
        if rest == "" :
            # Possible block list on following indented "- " lines.
            items = []
            j = i + 1
            while j < len(fm_lines) and re.match(r"^\s+-\s*", fm_lines[j]):
                item = re.sub(r"^\s+-\s*", "", fm_lines[j])
                items.append(_coerce(item))
                j += 1
            if j > i + 1:
                data[key] = items
                i = j
                continue
            data[key] = ""
            i += 1
        elif rest.startswith("[") and rest.endswith("]"):
            data[key] = _split_inline_list(rest)
            i += 1
        else:
            data[key] = _coerce(rest)
            i += 1
    return data, body


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def today():
    return datetime.date.today().isoformat()


def read(path):
    return path.read_text(encoding="utf-8")


def as_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [v for v in value if v != ""]
    return [value]


def rel(path):
    return path.resolve().relative_to(ROOT).as_posix()


def is_index(path):
    return path.name.lower() == "index.md"


def iter_wiki_notes():
    """Yield (path, frontmatter, body) for compiled Wiki notes."""
    for sub in WIKI_SUBDIRS.values():
        if not sub.exists():
            continue
        for p in sorted(sub.glob("*.md")):
            if is_index(p):
                continue
            fm, body = parse_frontmatter(read(p))
            yield p, fm, body


def iter_sources():
    """Yield (path, frontmatter, body) for Raw sources."""
    if not SOURCES_DIR.exists():
        return
    for p in sorted(SOURCES_DIR.glob("*.md")):
        if is_index(p):
            continue
        fm, body = parse_frontmatter(read(p))
        yield p, fm, body


def note_tag(fm):
    tags = as_list(fm.get("tags"))
    allowed = [t for t in tags if t in ALLOWED_TAGS]
    return allowed[0] if len(allowed) == 1 else None


def note_title(path, fm, body):
    for line in body.splitlines():
        m = re.match(r"^#\s+(.*)$", line.strip())
        if m:
            return m.group(1).strip()
    aliases = as_list(fm.get("aliases"))
    if aliases:
        return str(aliases[0])
    return path.stem.replace("-", " ").title()


def normalize_source(entry):
    """Normalize a sources entry to 'Raw/Sources/<name>' posix form."""
    s = str(entry).strip().strip("\"'")
    name = Path(s).name
    return (SOURCES_DIR / name).resolve().relative_to(ROOT).as_posix()


def coverage_map():
    """Map normalized Raw/Sources path -> list of Wiki note paths covering it."""
    cover = {}
    for p, fm, body in iter_wiki_notes():
        for entry in as_list(fm.get("sources")):
            key = normalize_source(entry)
            cover.setdefault(key, []).append(rel(p))
    return cover


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_doctor(args):
    problems = []
    info = []

    if sys.version_info < (3, 8):
        problems.append(f"Python {sys.version.split()[0]} < 3.8")
    else:
        info.append(f"Python {sys.version.split()[0]}")

    required_dirs = [
        SOURCES_DIR,
        ROOT / "Raw" / "Files",
        WIKI_SUBDIRS["topic"],
        WIKI_SUBDIRS["concept"],
        WIKI_SUBDIRS["entity"],
        WIKI_SUBDIRS["log"],
        ROOT / "Schema",
        ROOT / "_templates",
        ROOT / ".agents" / "skills",
        ROOT / "scripts",
    ]
    for d in required_dirs:
        if not d.is_dir():
            problems.append(f"missing folder: {rel(d) if d.exists() else d.relative_to(ROOT)}")

    notes = list(iter_wiki_notes())
    sources = list(iter_sources())
    info.append(f"compiled Wiki notes: {len(notes)}")
    info.append(f"Raw sources: {len(sources)}")

    if CATALOG.exists():
        info.append(f"catalog: {CATALOG.name} ({sum(1 for _ in CATALOG.open())} entries)")
    else:
        info.append("catalog: not built yet (run `build`)")

    if MANIFEST.exists():
        info.append(f"source manifest: {MANIFEST.name} ({sum(1 for _ in MANIFEST.open())} entries)")
    else:
        info.append("source manifest: not built yet (run `source-scan --update`)")

    for line in info:
        print(f"  {line}")
    if problems:
        for p in problems:
            print(f"{RED}DOCTOR FAIL{RESET}: {p}")
        return 1
    print(f"{GREEN}doctor: ok{RESET}")
    return 0


def cmd_build(args):
    entries = []
    for p, fm, body in iter_wiki_notes():
        tag = note_tag(fm)
        entries.append(
            {
                "path": rel(p),
                "title": note_title(p, fm, body),
                "tag": tag or "",
                "topics": as_list(fm.get("topics")),
                "sources": [normalize_source(s) for s in as_list(fm.get("sources"))],
                "updated": str(fm.get("updated", "")),
            }
        )

    entries.sort(key=lambda e: e["path"])
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    with CATALOG.open("w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n")

    # Per-folder index files.
    for tag, sub in WIKI_SUBDIRS.items():
        sub.mkdir(parents=True, exist_ok=True)
        folder_entries = [e for e in entries if Path(e["path"]).parent == Path(rel(sub))]
        lines = [f"# {sub.name} Index", "", f"_Generated by `wiki_tool.py build`. {len(folder_entries)} note(s)._", ""]
        if folder_entries:
            for e in folder_entries:
                name = Path(e["path"]).stem
                lines.append(f"- [[{name}]] — {e['title']}")
        else:
            lines.append("_No notes yet._")
        lines.append("")
        (sub / "index.md").write_text("\n".join(lines), encoding="utf-8")

    # Top-level Wiki index.
    lines = [
        "# Wiki Index",
        "",
        f"_Generated by `wiki_tool.py build` on {today()}. {len(entries)} compiled note(s)._",
        "",
        "Search the catalog before opening broad Raw context:",
        "",
        "```bash",
        'python3 scripts/wiki_tool.py search-catalog --query "your topic"',
        "```",
        "",
    ]
    for tag, sub in WIKI_SUBDIRS.items():
        folder_entries = [e for e in entries if Path(e["path"]).parent == Path(rel(sub))]
        lines.append(f"## {sub.name} ({len(folder_entries)})")
        lines.append("")
        if folder_entries:
            for e in folder_entries:
                name = Path(e["path"]).stem
                lines.append(f"- [[{name}]] — {e['title']}")
        else:
            lines.append("_No notes yet._")
        lines.append("")
    WIKI_INDEX.write_text("\n".join(lines), encoding="utf-8")

    print(f"{GREEN}build: ok{RESET} — {len(entries)} note(s) -> {rel(CATALOG)}, indexes written")
    return 0


def cmd_lint(args):
    errors = []
    count = 0
    for p, fm, body in iter_wiki_notes():
        count += 1
        loc = rel(p)
        if not fm:
            errors.append(f"{loc}: missing frontmatter")
            continue

        tags = as_list(fm.get("tags"))
        allowed = [t for t in tags if t in ALLOWED_TAGS]
        if len(allowed) != 1:
            errors.append(
                f"{loc}: tags must contain exactly one of {ALLOWED_TAGS}, found {tags!r}"
            )
        tag = allowed[0] if len(allowed) == 1 else None

        for key in ("created", "updated"):
            val = str(fm.get(key, ""))
            if not DATE_RE.match(val):
                errors.append(f"{loc}: {key} must be YYYY-MM-DD, found {val!r}")

        sources = as_list(fm.get("sources"))
        if "source_count" not in fm:
            errors.append(f"{loc}: missing source_count")
        else:
            try:
                sc = int(fm.get("source_count"))
            except (TypeError, ValueError):
                sc = None
                errors.append(f"{loc}: source_count is not an integer ({fm.get('source_count')!r})")
            if sc is not None and sc != len(sources):
                errors.append(
                    f"{loc}: source_count {sc} != number of sources {len(sources)}"
                )

        for entry in sources:
            target = ROOT / normalize_source(entry)
            if not target.exists():
                errors.append(f"{loc}: source not found: {entry}")

        if tag != "log" and not sources:
            errors.append(f"{loc}: non-log note must link at least one source")

    if errors:
        for e in errors:
            print(f"{RED}LINT{RESET}: {e}")
        print(f"{RED}lint: {len(errors)} problem(s) across {count} note(s){RESET}")
        return 1
    print(f"{GREEN}lint: ok{RESET} — {count} note(s) valid")
    return 0


def _build_manifest_records():
    cover = coverage_map()
    records = []
    for p, fm, body in iter_sources():
        key = rel(p)
        processed = bool(fm.get("Processed", False)) if isinstance(fm.get("Processed"), bool) else str(fm.get("Processed", "")).lower() == "true"
        records.append(
            {
                "path": key,
                "title": str(fm.get("Title", "")) or note_title(p, fm, body),
                "processed": processed,
                "covered_by": sorted(cover.get(key, [])),
                "updated": today(),
            }
        )
    records.sort(key=lambda r: r["path"])
    return records


def cmd_source_scan(args):
    records = _build_manifest_records()
    if args.update:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        with MANIFEST.open("w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        note = " (accepting current coverage)" if args.accept_covered else ""
        print(f"{GREEN}source-scan: updated{RESET}{note} — {len(records)} source(s) -> {rel(MANIFEST)}")
    else:
        if not records:
            print("No Raw sources found.")
        for r in records:
            mark = "covered" if r["covered_by"] else ("processed!uncovered" if r["processed"] else "uncovered")
            print(f"  {r['path']} [{mark}] -> {', '.join(r['covered_by']) or '-'}")
        print(f"{len(records)} source(s). Use --update to write {rel(MANIFEST)}.")
    return 0


def _load_manifest():
    if not MANIFEST.exists():
        return None
    out = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def cmd_source_lint(args):
    errors = []
    cover = coverage_map()
    count = 0
    for p, fm, body in iter_sources():
        count += 1
        loc = rel(p)
        for key in ("Title", "Reference", "Created", "Processed", "tags"):
            if key not in fm:
                errors.append(f"{loc}: missing required field '{key}'")
        if not str(fm.get("Title", "")).strip():
            errors.append(f"{loc}: Title must be non-empty")
        if "source" not in as_list(fm.get("tags")):
            errors.append(f"{loc}: tags must include 'source'")
        created = str(fm.get("Created", ""))
        if created and not DATE_RE.match(created):
            errors.append(f"{loc}: Created must be YYYY-MM-DD, found {created!r}")
        processed = str(fm.get("Processed", "")).lower() == "true" or fm.get("Processed") is True
        if processed and not cover.get(loc):
            errors.append(f"{loc}: marked Processed but no compiled Wiki note covers it")

    # Manifest consistency (if present).
    manifest = _load_manifest()
    if manifest is not None:
        on_disk = {rel(p) for p, _, _ in iter_sources()}
        in_manifest = {r["path"] for r in manifest}
        for missing in sorted(on_disk - in_manifest):
            errors.append(f"manifest: source not recorded: {missing} (run source-scan --update)")
        for stale in sorted(in_manifest - on_disk):
            errors.append(f"manifest: records a source that no longer exists: {stale}")

    if errors:
        for e in errors:
            print(f"{RED}SOURCE-LINT{RESET}: {e}")
        print(f"{RED}source-lint: {len(errors)} problem(s) across {count} source(s){RESET}")
        return 1
    print(f"{GREEN}source-lint: ok{RESET} — {count} source(s) valid")
    return 0


def cmd_source_delta(args):
    on_disk = {rel(p): (fm, body) for p, fm, body in iter_sources()}
    manifest = _load_manifest()
    in_manifest = {r["path"] for r in manifest} if manifest else set()
    new = sorted(set(on_disk) - in_manifest)
    removed = sorted(in_manifest - set(on_disk))
    if not new and not removed:
        print(f"{GREEN}source-delta: manifest in sync{RESET} ({len(on_disk)} source(s))")
        return 0
    for n in new:
        print(f"{YELLOW}NEW{RESET}    {n} (not in manifest)")
    for r in removed:
        print(f"{YELLOW}REMOVED{RESET} {r} (in manifest, not on disk)")
    print(f"{len(new)} new, {len(removed)} removed. Run `source-scan --update`.")
    return 0


def cmd_source_coverage(args):
    cover = coverage_map()
    sources = list(iter_sources())
    if not sources:
        print("No Raw sources found.")
        return 0
    covered = 0
    for p, fm, body in sources:
        loc = rel(p)
        by = cover.get(loc, [])
        if by:
            covered += 1
            print(f"{GREEN}COVERED{RESET}   {loc} <- {', '.join(by)}")
        else:
            print(f"{YELLOW}UNCOVERED{RESET} {loc}")
    print(f"{covered}/{len(sources)} source(s) covered by compiled notes.")
    return 0


def cmd_search_catalog(args):
    if not CATALOG.exists():
        print(f"{RED}catalog not found{RESET}: run `build` first.")
        return 1
    q = args.query.lower()
    hits = []
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        haystack = " ".join(
            [
                obj.get("title", ""),
                obj.get("tag", ""),
                obj.get("path", ""),
                " ".join(obj.get("topics", [])),
            ]
        ).lower()
        if q in haystack:
            hits.append(obj)
    if not hits:
        print(f"No matches for {args.query!r}.")
        return 0
    for obj in hits:
        print(f"  [{obj.get('tag','')}] {obj.get('title','')} — {obj.get('path','')}")
        if obj.get("topics"):
            print(f"      topics: {', '.join(obj['topics'])}")
    print(f"{len(hits)} match(es) for {args.query!r}.")
    return 0


def cmd_log(args):
    logs_dir = WIKI_SUBDIRS["log"]
    logs_dir.mkdir(parents=True, exist_ok=True)
    date = today()
    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-") or "entry"
    base = f"{date}-{slug}"
    path = logs_dir / f"{base}.md"
    n = 2
    while path.exists():
        path = logs_dir / f"{base}-{n}.md"
        n += 1

    content = (
        "---\n"
        "tags:\n"
        '  - "log"\n'
        "topics: []\n"
        "status: stable\n"
        f"created: {date}\n"
        f"updated: {date}\n"
        "sources: []\n"
        "source_count: 0\n"
        "aliases: []\n"
        "---\n\n"
        f"# {date} — {args.title}\n\n"
        "## Details\n\n"
        f"{args.details}\n"
    )
    path.write_text(content, encoding="utf-8")
    print(f"{GREEN}log: written{RESET} -> {rel(path)}")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(description="LLM Wiki deterministic tooling.")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Non-mutating health check.")
    sub.add_parser("build", help="Generate catalog and indexes.")
    sub.add_parser("lint", help="Validate compiled Wiki notes.")

    sp = sub.add_parser("source-scan", help="List Raw sources / update manifest.")
    sp.add_argument("--update", action="store_true", help="Write Schema/source-manifest.jsonl.")
    sp.add_argument("--accept-covered", action="store_true", help="Accept current coverage state.")

    sub.add_parser("source-lint", help="Validate source frontmatter and coverage.")
    sub.add_parser("source-delta", help="Raw sources not represented in the manifest.")
    sub.add_parser("source-coverage", help="Which Raw sources are covered.")

    sc = sub.add_parser("search-catalog", help="Search compiled notes via catalog.")
    sc.add_argument("--query", required=True, help="Search text.")

    lg = sub.add_parser("log", help="Add a log note.")
    lg.add_argument("--title", required=True)
    lg.add_argument("--details", required=True)

    return p


DISPATCH = {
    "doctor": cmd_doctor,
    "build": cmd_build,
    "lint": cmd_lint,
    "source-scan": cmd_source_scan,
    "source-lint": cmd_source_lint,
    "source-delta": cmd_source_delta,
    "source-coverage": cmd_source_coverage,
    "search-catalog": cmd_search_catalog,
    "log": cmd_log,
}


def main(argv=None):
    args = build_parser().parse_args(argv)
    return DISPATCH[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
