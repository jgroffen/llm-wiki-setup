---
name: llm-wiki-maintain
description: Run the full LLM Wiki maintenance gate (doctor, build, lint, source-lint, audit) before committing, and reconcile the source manifest. Use before any meaningful commit to the Wiki.
---

# LLM Wiki: Maintain

Keep the Wiki healthy and safe to commit.

## When to use

- Before any meaningful commit to the vault.
- Periodically, to confirm catalog, indexes, and manifest are in sync.

## Maintenance gate

```bash
python3 scripts/wiki_tool.py doctor
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-lint
python3 scripts/audit_public.py
```

All five must pass before committing.

## After ingesting sources

```bash
python3 scripts/wiki_tool.py source-scan --update --accept-covered
python3 scripts/wiki_tool.py source-lint
```

## Useful diagnostics

- `python3 scripts/wiki_tool.py source-delta` — Raw sources not yet in the manifest.
- `python3 scripts/wiki_tool.py source-coverage` — which sources compiled notes cover.
- `python3 scripts/wiki_tool.py doctor` — folders, Python, catalog, manifest, counts.

## Git hooks

Install the pre-commit gate once per clone:

```bash
bash scripts/install_hooks.sh
```

It runs `build`, `lint`, `source-lint`, and `audit_public.py` automatically on commit.

## Guardrails

- Never commit if `audit_public.py` fails (secrets, machine-local paths, cache/plugin state).
- Commit regenerated `Wiki/catalog.jsonl`, `Wiki/index.md`, and per-folder `index.md` files together with the notes that changed.
