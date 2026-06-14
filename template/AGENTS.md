# Agent Rules for This LLM Wiki

This repository is an **LLM Wiki**. Read these rules before making changes.

## The LLM Wiki Concept

An LLM Wiki separates **captured source material** from **compiled knowledge**.

- Raw sources preserve original context.
- Wiki notes turn useful claims into short, linked, reusable knowledge.
- The most useful workflow is to **search the compiled Wiki first**, and open Raw sources only when more evidence or detail is needed.

Source material is compiled into a number of Wiki notes, for example:

- one or more **topic** notes (`Wiki/Topics/`)
- one or more **concept** notes (`Wiki/Concepts/`)
- one or more **entity** notes (`Wiki/Entities/`)

**Log** notes (`Wiki/Logs/`) record meaningful changes to the Wiki and are normally created by deterministic tooling.

Every compiled Wiki note must link back to its Raw source(s) in `Raw/Sources/`. Do not rely on generated text alone — keep the transformation visible: a small Raw source should become focused Wiki notes.

## Hard Rules

1. **Treat `Raw/Sources/` as source material, not as compiled notes.** Never edit a Raw source to make it read like a finished Wiki note.
2. **Write reusable knowledge only under `Wiki/`.** Topics, concepts, and entities live here.
3. **Keep every compiled note linked to one or more Raw Sources.** Populate the `sources` list and keep `source_count` equal to its length.
4. **Search `Wiki/catalog.jsonl` before opening broad Raw context.** Use the query skill / `search-catalog` first. Only open Raw sources when the compiled note is insufficient or the user asks for source-level verification.
5. **Run `build`, `lint`, and source checks before commits** (see the Maintenance Gate below).
6. **Do not invent citations or create unsupported claims.** If a claim is not backed by a Raw source, do not assert it.

## Layout

| Path | Purpose |
|------|---------|
| `Raw/Sources/` | Original source notes (Markdown). Evidence. |
| `Raw/Files/` | Binary / large source files (git-ignored). |
| `Wiki/Topics/` | Broad topic notes. |
| `Wiki/Concepts/` | Focused concept notes. |
| `Wiki/Entities/` | People, orgs, things. |
| `Wiki/Logs/` | Change log notes. |
| `Wiki/catalog.jsonl` | Machine-readable catalog of compiled notes. |
| `Wiki/index.md` | Human index of the Wiki. |
| `Schema/` | Schema, conventions, lint rules, source manifest. |
| `_templates/` | Note templates. |
| `.agents/skills/` | Agent skills. |
| `scripts/` | Deterministic tooling. |

## Allowed Compiled Note Tags

Each compiled Wiki note uses exactly one of: `topic`, `concept`, `entity`, `log`.

## Maintenance Gate

Before every meaningful commit:

```bash
python3 scripts/wiki_tool.py doctor
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-lint
python3 scripts/audit_public.py
```

After ingesting sources, also run:

```bash
python3 scripts/wiki_tool.py source-scan --update --accept-covered
python3 scripts/wiki_tool.py source-lint
```

## Ingest Workflow

1. Put cleaned Markdown in `Raw/Sources/`.
2. Run `search-catalog` for likely related topics.
3. Open only the most relevant compiled Wiki notes.
4. Create or update focused notes in `Wiki/`.
5. Add Raw source links to `sources` and keep `source_count` accurate.
6. Run the build + lint + source-scan + source-lint commands above.
7. Add a log entry if the ingest meaningfully changed the Wiki.

See `Schema/` for frontmatter schema, naming conventions, the lint checklist, the command reference, and `Schema/workflow-examples.md` for worked examples.
