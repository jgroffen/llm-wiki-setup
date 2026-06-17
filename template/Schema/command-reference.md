# Command Reference

All tooling is in `scripts/` and uses only the Python standard library. Run from the repo root.

## `wiki_tool.py`

| Command | Mutates? | Description |
|---------|----------|-------------|
| `doctor` | no | Health check: folders, Python version, catalog, manifest, note counts. |
| `build` | yes | Generate `Wiki/catalog.jsonl`, `Wiki/index.md`, and per-folder `index.md` files. |
| `lint` | no | Validate compiled Wiki note frontmatter, tags, sources, and `source_count`. |
| `source-scan` | no | List Raw sources and their coverage state. |
| `source-scan --update` | yes | Write `Schema/source-manifest.jsonl` from sources + computed coverage. |
| `source-scan --update --accept-covered` | yes | Update manifest, accepting current coverage state. |
| `source-lint` | no | Validate source frontmatter and coverage; fail if processed-but-uncovered. |
| `source-delta` | no | Show Raw sources not represented in the manifest (and stale manifest rows). |
| `source-coverage` | no | Show which Raw sources are covered by compiled Wiki notes. |
| `search-catalog --query "text"` | no | Search compiled notes through the catalog. |
| `log --title "t" --details "d"` | yes | Add a log note under `Wiki/Logs/`. |
| `plugins` | no | List installed plugins and the note types they add. |

### Examples

```bash
python3 scripts/wiki_tool.py doctor
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-scan
python3 scripts/wiki_tool.py source-scan --update --accept-covered
python3 scripts/wiki_tool.py source-lint
python3 scripts/wiki_tool.py source-delta
python3 scripts/wiki_tool.py source-coverage
python3 scripts/wiki_tool.py search-catalog --query "navigation"
python3 scripts/wiki_tool.py log --title "Ingest X" --details "Added concept notes from x.md"
python3 scripts/wiki_tool.py plugins
```

Plugins extend the allowed note types via `Schema/plugins/*.json`; see
`Schema/plugin-schema.md`.

## `audit_public.py`

```bash
python3 scripts/audit_public.py
```

Fails on obvious secrets, private keys, machine-local absolute paths, and committed plugin/cache/workspace state.

## Git Hooks

```bash
bash scripts/install_hooks.sh
```

Points `core.hooksPath` at `.githooks/`. The `pre-commit` hook runs `build`, `lint`, `source-lint`, and `audit_public.py`.

## Maintenance Gate

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
