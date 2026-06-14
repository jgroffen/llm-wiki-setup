# Workflow Examples

Worked examples of the core LLM Wiki workflows.

## Example 1: Ingesting a New Source

You have a cleaned article about how bees navigate.

1. Save it as a Raw source:

   `Raw/Sources/bee-navigation.md`

   ```yaml
   ---
   Title: "How Bees Navigate"
   Author: "Jane Doe"
   Reference: "https://example.org/bee-navigation"
   ContentType:
     - "markdown"
   Created: 2026-06-14
   Processed: false
   tags:
     - "source"
   ---
   ```

2. Search the catalog for related notes before writing:

   ```bash
   python3 scripts/wiki_tool.py search-catalog --query "navigation"
   ```

3. Compile focused Wiki notes, e.g.:
   - `Wiki/Concepts/sun-compass-orientation.md` (tag `concept`)
   - `Wiki/Entities/honey-bee.md` (tag `entity`)

   Each lists the source and keeps the count accurate:

   ```yaml
   ---
   tags:
     - "concept"
   topics:
     - "animal-navigation"
   status: draft
   created: 2026-06-14
   updated: 2026-06-14
   sources:
     - "Raw/Sources/bee-navigation.md"
   source_count: 1
   aliases: []
   ---
   ```

4. Mark the source processed (`Processed: true`) once it is covered.

5. Build, lint, and reconcile the manifest:

   ```bash
   python3 scripts/wiki_tool.py build
   python3 scripts/wiki_tool.py lint
   python3 scripts/wiki_tool.py source-scan --update --accept-covered
   python3 scripts/wiki_tool.py source-lint
   ```

6. Record the change:

   ```bash
   python3 scripts/wiki_tool.py log --title "Ingest bee navigation" \
     --details "Added sun-compass-orientation and honey-bee from bee-navigation.md"
   ```

## Example 2: Answering a Question

1. Start with `Wiki/index.md`.
2. Search the catalog:

   ```bash
   python3 scripts/wiki_tool.py search-catalog --query "sun compass"
   ```

3. Open the most relevant compiled note(s).
4. Open the Raw source only if the compiled note is insufficient, or the user wants source-level verification.
5. Cite both the compiled note and the Raw source when the answer depends on source material.

## Example 3: Maintenance Before a Commit

```bash
python3 scripts/wiki_tool.py doctor
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-lint
python3 scripts/audit_public.py
```

If all pass, commit.
