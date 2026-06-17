# Plugin Schema

The LLM Wiki ships four core note types — `topic`, `concept`, `entity`, `log`. **Plugins**
extend the wiki with additional note types (and the folders that hold them) without editing
`scripts/wiki_tool.py`. `build`, `lint`, and `doctor` discover plugins automatically.

## How a plugin registers

A plugin drops one JSON manifest into `Schema/plugins/<name>.json`. On every run,
`wiki_tool.py` reads all manifests in that folder and merges their note types with the core
set.

```json
{
  "name": "mtg-wiki",
  "version": "0.1.0",
  "note_types": [
    {"tag": "card",     "folder": "Wiki/Cards",     "requires_source": true},
    {"tag": "set",      "folder": "Wiki/Sets",      "requires_source": true},
    {"tag": "mechanic", "folder": "Wiki/Mechanics", "requires_source": false}
  ],
  "source_subdirs": ["Raw/Sources/cards", "Raw/Sources/sets"]
}
```

## Fields

| Field | Required | Meaning |
|-------|----------|---------|
| `name` | yes | Plugin name (defaults to the manifest filename). |
| `version` | no | Plugin version string, for display. |
| `note_types` | yes | List of note types this plugin adds. |
| `note_types[].tag` | yes | The single allowed tag for the note type. Must not collide with a core tag or another plugin's tag. |
| `note_types[].folder` | yes | Vault-relative folder holding these notes, e.g. `Wiki/Cards`. Must be unique across all note types. |
| `note_types[].requires_source` | no (default `true`) | Whether `lint` requires the note to link ≥1 Raw source. Set `false` for derived/cross-cutting notes (like the core `log` type). |
| `source_subdirs` | no | Raw source subfolders the plugin uses, e.g. `Raw/Sources/cards`. Informational/for scaffolding — `iter_sources` already recurses all of `Raw/Sources/`. |

## Rules and behavior

- **Tags and folders must be unique.** A plugin that re-declares a core tag (`topic`,
  `concept`, `entity`, `log`) or collides with another plugin's tag/folder is rejected, and
  `build`/`lint`/`doctor` fail with a clear `PLUGIN:` error until fixed.
- A note type's `tag` participates in the same lint rules as core notes: each compiled note
  carries exactly one allowed tag, has valid `created`/`updated` dates, and keeps
  `source_count == len(sources)`. The only per-type difference is `requires_source`.
- Raw sources may live in subfolders (e.g. `Raw/Sources/cards/black-lotus.md`); the `sources`
  frontmatter list should reference them by path.
- Inspect what's installed with `python3 scripts/wiki_tool.py plugins`. That command also
  doubles as the **capability probe**: a plugin installer can run it to confirm the core is
  plugin-aware before installing.

## Removing a plugin

Delete its manifest from `Schema/plugins/` (and, if desired, its folders/notes). The core
note types always remain.
