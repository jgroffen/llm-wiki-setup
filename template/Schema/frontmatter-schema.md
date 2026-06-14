# Frontmatter Schema

This file defines the required and optional frontmatter for notes in the LLM Wiki.

## Raw Source Notes (`Raw/Sources/`)

```yaml
---
Title: ""              # required, non-empty
Author: ""             # optional
Reference: ""          # required: URL or citation to the original
ContentType:
  - "markdown"         # list of content types
Created: YYYY-MM-DD     # required, ISO date
Processed: false        # required boolean; true once compiled into Wiki notes
tags:
  - "source"           # required; must include "source"
---
```

Notes:
- `Processed: true` asserts that the source has been compiled into one or more Wiki notes. `source-lint` fails if a processed source has no Wiki coverage.

## Compiled Wiki Notes (`Wiki/Topics|Concepts|Entities|Logs/`)

```yaml
---
tags:
  - "concept"          # required; exactly one of: topic, concept, entity, log
topics: []             # list of topic slugs/links this note belongs to
status: seed           # seed | draft | stable
created: YYYY-MM-DD     # required, ISO date
updated: YYYY-MM-DD     # required, ISO date
sources: []            # list of paths under Raw/Sources/ this note is built from
source_count: 0        # required; must equal len(sources)
aliases: []            # optional alternate titles
---
```

Notes:
- `tags` must contain **exactly one** allowed tag value: `topic`, `concept`, `entity`, or `log`.
- `source_count` must equal the number of entries in `sources`.
- Each entry in `sources` should be a path to an existing file under `Raw/Sources/` (a bare filename like `example.md` is also accepted and resolved against `Raw/Sources/`).
- `log` notes are exempt from requiring a source link, since they record Wiki changes rather than compile sources.

See `naming-conventions.md` for filenames and `lint-checklist.md` for the validation gate.
