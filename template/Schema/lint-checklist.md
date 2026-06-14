# Lint Checklist

This is the deterministic gate enforced by `scripts/wiki_tool.py`. Run `lint` and `source-lint` before committing.

## Compiled Wiki Notes (`wiki_tool.py lint`)

- [ ] Frontmatter is present and parses as YAML-like key/value blocks.
- [ ] `tags` contains **exactly one** allowed value: `topic`, `concept`, `entity`, or `log`.
- [ ] `created` and `updated` are present and ISO `YYYY-MM-DD` dates.
- [ ] `source_count` is present and **equals** the number of entries in `sources`.
- [ ] Every entry in `sources` resolves to an existing file under `Raw/Sources/`.
- [ ] Non-`log` notes have at least one source.

## Raw Source Notes (`wiki_tool.py source-lint`)

- [ ] Frontmatter includes `Title`, `Reference`, `Created`, `Processed`, and `tags`.
- [ ] `Title` is non-empty.
- [ ] `tags` includes `source`.
- [ ] If `Processed: true`, at least one compiled Wiki note lists the source in its `sources` (coverage).
- [ ] The source manifest (`Schema/source-manifest.jsonl`) is consistent with the sources on disk (`source-delta` is empty after `source-scan --update`).

## Build Artifacts (`wiki_tool.py build`)

- [ ] `Wiki/catalog.jsonl` regenerated and committed.
- [ ] `Wiki/index.md` and per-folder index files regenerated and committed.

## Public Safety (`audit_public.py`)

- [ ] No obvious secrets, private keys, machine-local absolute paths, or plugin/cache state.
