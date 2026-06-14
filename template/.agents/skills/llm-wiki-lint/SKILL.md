---
name: llm-wiki-lint
description: Validate LLM Wiki note and source frontmatter and fix lint failures. Use when build/lint/source-lint report problems or before committing Wiki changes.
---

# LLM Wiki: Lint

Validate the Wiki and fix any structural problems the tooling reports.

## When to use

- `lint` or `source-lint` reports errors.
- Before committing changes to compiled notes or sources.

## Steps

1. **Run the validators**:
   ```bash
   python3 scripts/wiki_tool.py build
   python3 scripts/wiki_tool.py lint
   python3 scripts/wiki_tool.py source-lint
   ```
2. **Fix compiled-note (`lint`) failures**:
   - `tags` must contain exactly one of `topic`, `concept`, `entity`, `log`.
   - `created` and `updated` must be `YYYY-MM-DD`.
   - `source_count` must equal the number of entries in `sources`.
   - every `sources` entry must resolve to an existing file under `Raw/Sources/`.
   - non-`log` notes must link at least one source.
3. **Fix source (`source-lint`) failures**:
   - sources need `Title` (non-empty), `Reference`, `Created`, `Processed`, and `tags` including `source`.
   - a source marked `Processed: true` must be covered by at least one compiled note — either compile it or set `Processed: false`.
   - if the manifest is out of sync, run `python3 scripts/wiki_tool.py source-scan --update --accept-covered`.
4. **Re-run** until both pass clean.

## Reference

See `Schema/lint-checklist.md` and `Schema/frontmatter-schema.md` for the full rules.
