# Naming Conventions

## Files

- Use lowercase `kebab-case` for note filenames: `photosynthesis-overview.md`, `ada-lovelace.md`.
- One subject per note. Prefer specific over broad.
- Filenames should be stable; prefer adding `aliases` in frontmatter over renaming.

## Folders

- `Raw/Sources/` — raw source notes (kebab-case).
- `Raw/Files/` — binary/large originals (git-ignored).
- `Wiki/Topics/` — broad topic notes.
- `Wiki/Concepts/` — focused concept notes.
- `Wiki/Entities/` — people, organizations, products, places, things.
- `Wiki/Logs/` — change log notes, normally tool-generated (e.g. `2026-06-14-some-change.md`).

## Note Types and Tags

| Folder | tag value |
|--------|-----------|
| `Wiki/Topics/` | `topic` |
| `Wiki/Concepts/` | `concept` |
| `Wiki/Entities/` | `entity` |
| `Wiki/Logs/` | `log` |

Each compiled note carries exactly one of these tag values.

## Links

- Link between Wiki notes with Obsidian wikilinks: `[[note-name]]`.
- Link a compiled note to its sources via the `sources` frontmatter list (paths under `Raw/Sources/`), not only inline.

## Titles

- The note `Title:` / `# Heading` should be human-readable Title Case.
- Logs use a date-prefixed slug: `YYYY-MM-DD-short-description`.
