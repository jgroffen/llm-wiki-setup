# LLM Wiki

This vault is an **LLM Wiki**: a knowledge system designed to be read and maintained by AI agents as well as humans.

## How It Works

An LLM Wiki separates *captured source material* from *compiled knowledge*:

- **`Raw/Sources/`** — original source notes. Cleaned Markdown goes here. Treat this as evidence, not as finished notes.
- **`Raw/Files/`** — binary or large source files (ignored by git by default).
- **`Wiki/`** — concise, reusable, interlinked knowledge notes compiled from Raw sources.
  - `Wiki/Topics/`, `Wiki/Concepts/`, `Wiki/Entities/`, `Wiki/Logs/`
- **`Schema/`** — frontmatter schema, naming conventions, lint rules, the source manifest, and the command reference.
- **`_templates/`** — note templates for sources and compiled notes.
- **`.agents/skills/`** — agent skills for ingest, query, lint, and maintenance.
- **`scripts/`** — deterministic tooling (`wiki_tool.py`, hooks, audit).

## Core Workflow

1. Put cleaned source Markdown in `Raw/Sources/`.
2. Compile useful claims into short, linked notes under `Wiki/`.
3. Keep every Wiki note linked back to its Raw source(s).
4. Build the catalog and indexes, then run health checks.

## For Agents

**Search `Wiki/catalog.jsonl` (or `Wiki/index.md`) before opening broad Raw context.** See `AGENTS.md` for the full rules.

Run the maintenance gate before meaningful commits:

```bash
python3 scripts/wiki_tool.py doctor
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-lint
python3 scripts/audit_public.py
```
