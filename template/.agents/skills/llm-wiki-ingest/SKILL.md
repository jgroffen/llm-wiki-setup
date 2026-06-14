---
name: llm-wiki-ingest
description: Compile a new or updated Raw source under Raw/Sources/ into focused, linked Wiki notes. Use when the user adds source material to the LLM Wiki and wants it turned into reusable knowledge.
---

# LLM Wiki: Ingest

Turn a Raw source into concise, reusable Wiki notes while keeping every claim traceable.

## When to use

- The user dropped a cleaned Markdown source into `Raw/Sources/`.
- The user asks to "ingest", "compile", "process", or "add" source material to the Wiki.

## Steps

1. **Confirm the source exists** under `Raw/Sources/` with valid frontmatter (use the `_templates/source-note.md` shape: `Title`, `Reference`, `Created`, `Processed`, `tags: [source]`).
2. **Search first — do not bulk-read Raw.** Find related compiled notes:
   ```bash
   python3 scripts/wiki_tool.py search-catalog --query "key terms from the source"
   ```
3. **Open only the most relevant** existing Wiki notes returned above.
4. **Create or update focused notes** under `Wiki/Topics|Concepts|Entities/` from the matching template:
   - one subject per note, kebab-case filename, exactly one allowed tag (`topic`/`concept`/`entity`).
   - add the source path to `sources` and set `source_count` to its length.
   - link related notes with `[[wikilinks]]`.
   - **Never invent citations.** Only assert claims the source supports.
5. **Mark the source processed**: set `Processed: true` once it is covered by at least one note.
6. **Build, lint, reconcile**:
   ```bash
   python3 scripts/wiki_tool.py build
   python3 scripts/wiki_tool.py lint
   python3 scripts/wiki_tool.py source-scan --update --accept-covered
   python3 scripts/wiki_tool.py source-lint
   ```
7. **Log the change** if it was meaningful:
   ```bash
   python3 scripts/wiki_tool.py log --title "Ingest <source>" --details "<what changed>"
   ```

## Done when

`lint` and `source-lint` pass, the new notes appear in `Wiki/catalog.jsonl`, and the source shows as covered in `source-coverage`.
