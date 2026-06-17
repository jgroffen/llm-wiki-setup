# LLM Wiki Core Setup Guide For Agents

## Mission

Build a clean LLM Wiki in Obsidian.

The finished core system should let the user put source notes in `Raw/Sources/`. The agent or LLM connection can then:

1. Compile those sources into concise, reusable notes in `Wiki/`.
2. Keep claims traceable from Wiki notes back to Raw sources.
3. Build indexes and a machine-readable catalog.
4. Run deterministic health checks before committing changes.
5. Ask future agents to query the compiled Wiki before reading broad Raw context.

## What This File Can Rebuild

This file is sufficient for a capable AI coding agent to build a functional core LLM Wiki from an empty folder, including:
- Raw source layer
- compiled Wiki layer
- Schema/rules layer
- note templates
- core agent skills
- deterministic `wiki_tool.py`
- source manifest
- catalog and indexes
- lint and audit gates

## Before Editing

Inspect the target folder first.

If it is not a git repo, initialize git:

```bash
git init
```

Do not assume any other git configuration such as `git config user.email` is to be performed.

If it is already an Obsidian vault, preserve existing `.obsidian/` basics and ignore plugin state, caches, workspace churn, private files, and binary source files by default.

Ensure a safe `.gitignore` exists that ignores:

```gitignore
.DS_Store
.obsidian/workspace*.json
.obsidian/plugins/
.obsidian/cache/
.obsidian/logs/
Raw/Files/*
!Raw/Files/.gitkeep
Drafts/
```

## Core Build Order

Follow this order. Do not skip ahead.
### Step 00: Empty Vault

Create or preserve:

- `.gitignore`
- `Welcome.md`

Update `Welcome.md` to identify the Wiki as an LLM Wiki with usage information.

Once Step 00 is complete, commit with the following commit message:

```text
llmwiki-00-empty-vault
```

### Step 01: Core Structure

Create or preserve these folders:

```text
Raw/Sources/
Raw/Files/
Wiki/Topics/
Wiki/Concepts/
Wiki/Entities/
Wiki/Logs/
Schema/
Schema/plugins/
_templates/
.agents/skills/
scripts/
```

Add `.gitkeep` files only where needed to preserve empty folders (including
`Schema/plugins/`, which holds plugin manifests and is normally empty at first).

Once Step 01 is complete, commit with the following commit message:

```text
llmwiki-01-core-structure
```

### Step 02: Schema And Agent Rules

Review and if required create or update:
- `AGENTS.md`
- `CLAUDE.md`
- `Schema/frontmatter-schema.md`
- `Schema/workflow-examples.md`
- `Schema/lint-checklist.md`
- `Schema/naming-conventions.md`
- `Schema/plugin-schema.md`

`AGENTS.md` must tell agents:
- The LLM Wiki concept. A summary is provided in the `LLM Wiki Concept Summary` sub-section that follows this section.
- Treat `Raw/Sources/` as source material, not as compiled notes.
- Write reusable knowledge only under `Wiki/`.
- Keep every compiled note linked to one or more Raw Sources.
- Search `Wiki/catalog.jsonl` before opening broad Raw context.
- Run `build`, `lint`, and source checks before commits.
- Do not invent citations or create unsupported claims.

`CLAUDE.md` should include only the following content:

```
# Claude Code Instructions

@AGENTS.md
```

Once Step 02 is complete, commit with the following commit message:

```text
llmwiki-02-schema-and-agent-rules
```

#### LLM Wiki Concept Summary

An LLM Wiki separates captured source material from compiled knowledge notes. Raw sources preserve original context, while Wiki notes turn useful claims into short, linked, reusable knowledge. The most useful workflow is to search the compiled Wiki first, then open Raw sources only when more evidence or detail is needed.

Source material is compiled into a number of Wiki notes, for example:

- one or more topic notes
- one or more concept notes
- one or more entity notes

Log notes record meaningful changes to the wiki, and may be created by the user with deterministic tooling.

Every compiled Wiki note must link back to the Raw source in `Sources`.

Do not rely on generated text alone. Keep the transformation visible: a small Raw source should become focused Wiki notes.

### Step 03: Templates

Review and if required create or update:

- `_templates/source-note.md`
- `_templates/concept-note.md`
- `_templates/topic-note.md`
- `_templates/entity-note.md`
- `_templates/log-note.md`

Source notes should include:

```yaml
---
Title: ""
Author: ""
Reference: ""
ContentType:
  - "markdown"
Created: YYYY-MM-DD
Processed: false
tags:
  - "source"
---
```

Compiled Wiki notes should include:

```yaml
---
tags:
  - "concept"
topics: []
status: seed
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
source_count: 0
aliases: []
---
```

Allowed compiled note tags:

- `topic`
- `concept`
- `entity`
- `log`

Once Step 03 is complete, commit with the following commit message:

```text
llmwiki-03-templates
```

### Step 04: Deterministic Tooling

Review and if required create or update `scripts/wiki_tool.py`.

Ensure `scripts/wiki_tool.py` uses only the Python standard library and is consistent with the following required commands:

- `doctor`: non-mutating health check for folders, Python version, catalog, source manifest, and basic note counts.
- `build`: generate `Wiki/catalog.jsonl`, `Wiki/index.md`, and per-folder index files.
- `lint`: validate compiled Wiki note frontmatter, allowed tags, source links, and `source_count`.
- `source-scan`: list Raw sources and optionally update `Schema/source-manifest.jsonl`.
- `source-scan --update --accept-covered`: update the source manifest after Wiki notes cover Raw sources.
- `source-lint`: validate source frontmatter and source coverage state.
- `source-delta`: show Raw sources not represented in the manifest.
- `source-coverage`: show which Raw sources are covered by compiled Wiki notes.
- `search-catalog --query "text"`: search compiled Wiki notes through the catalog.
- `log --title "title" --details "details"`: add a log record to `Wiki/Logs/`.
- `plugins`: list installed plugins and the note types they add (and serve as a
  capability probe for plugin-aware cores).

The core note types are `topic`, `concept`, `entity`, and `log`, but `wiki_tool.py` must
derive its allowed tags and folders from a registry that merges these with any plugin
manifests found in `Schema/plugins/*.json` — so plugins can add note types (e.g. an
`mtg-wiki` plugin adding `card`/`set`) without editing the tool. Each plugin note type
declares `tag`, `folder`, and `requires_source`; tag/folder collisions must fail the gates.
`iter_sources` must recurse `Raw/Sources/` so plugin sources may live in subfolders. Document
the manifest contract in `Schema/plugin-schema.md`.

Alse ensure the following exist and are consistent with `scripts/wiki_tool.py`:

- `scripts/install_hooks.sh`
- `.githooks/pre-commit`
- `scripts/audit_public.py`
- `Schema/command-reference.md`

The pre-commit hook may run:

```bash
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-lint
```

`audit_public.py` should fail on obvious secrets, machine-local paths, private keys, and plugin/cache state.

Minimum catalog contract:

`Wiki/catalog.jsonl` should contain one JSON object per compiled Wiki note. Each object should include:

```json
{"path":"Wiki/Concepts/example.md","title":"Example","tag":"concept","topics":[],"sources":[],"updated":"YYYY-MM-DD"}
```

Minimum source manifest contract:

`Schema/source-manifest.jsonl` should contain one JSON object per Raw source. Each object should include:

```json
{"path":"Raw/Sources/example.md","title":"Example","processed":true,"covered_by":["Wiki/Concepts/example.md"],"updated":"YYYY-MM-DD"}
```

Minimum lint behavior:

- compiled Wiki notes must use one allowed tag: `topic`, `concept`, `entity`, or `log`
- compiled Wiki notes must keep `source_count` equal to the number of `sources`
- compiled Wiki note source links should point to existing files under `Raw/Sources/`
- Raw source notes should include `Title`, `Reference`, `Created`, `Processed`, and `tags`
- `source-lint` should fail if a source is marked processed but has no Wiki coverage

Once Step 04 is complete, commit with the following commit message:

```text
llmwiki-04-tooling
```

### Step 05: Agent Skills

Review and if required create or update:
- `.agents/skills/llm-wiki-ingest/SKILL.md`
- `.agents/skills/llm-wiki-query/SKILL.md`
- `.agents/skills/llm-wiki-lint/SKILL.md`
- `.agents/skills/llm-wiki-maintain/SKILL.md`

Ensure each llm-wiki `SKILL.md` file includes a valid frontmatter section that describes the skill, for example:

```
---
name: my-custom-skill
description: A clear description of what this skill does so the agent knows when to invoke it.
---
```

Once Step 05 is complete, commit with the following commit message:

```text
llmwiki-05-agent-skills
```

At this point the user has a working core LLM Wiki.

## Step 06: Final Acceptance Criteria

The core build is complete only when all of these are true:

- `AGENTS.md` exists and describes Raw/Wiki/Schema rules
- `_templates/` contains source, concept, topic, entity, and log templates
- `.agents/skills/` contains ingest, query, lint, and maintain skills
- `scripts/wiki_tool.py` supports every command listed in Step 04
- `scripts/audit_public.py` exists and passes
- `Wiki/catalog.jsonl` exists and includes the compiled Wiki notes
- `Schema/source-manifest.jsonl` exists and covers processed Raw sources
- `Wiki/index.md` and per-folder indexes exist
- the maintenance gate passes

If any additional work is performed during evaluation of final acceptance criteria, perofrm a commit with the following commit message:

```text
llmwiki-06-final
```

## Ingest Workflow For Future Sources

When the user adds a new source:

1. Put cleaned Markdown in `Raw/Sources/`.
2. Run `search-catalog` for likely related topics.
3. Open only the most relevant compiled Wiki notes.
4. Create or update focused notes in `Wiki/`.
5. Add Raw source links to `sources`.
6. Keep `source_count` accurate.
7. Run:

```bash
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-scan --update --accept-covered
python3 scripts/wiki_tool.py source-lint
```

8. Add a log entry if the ingest meaningfully changed the Wiki.

## Query Workflow

When answering a question from the Wiki:

1. Start with `Wiki/index.md`.
2. Search the catalog:

```bash
python3 scripts/wiki_tool.py search-catalog --query "user topic"
```

3. Open the most relevant Wiki notes.
4. Open Raw sources only when the compiled note is insufficient or the user asks for source-level verification.
5. Cite the compiled note and Raw source when the answer depends on source material.

## Maintenance Gate

Before every meaningful commit, run:

```bash
python3 scripts/wiki_tool.py doctor
python3 scripts/wiki_tool.py build
python3 scripts/wiki_tool.py lint
python3 scripts/wiki_tool.py source-lint
python3 scripts/audit_public.py
```

After source ingestion, also run:

```bash
python3 scripts/wiki_tool.py source-scan --update --accept-covered
python3 scripts/wiki_tool.py source-lint
```
