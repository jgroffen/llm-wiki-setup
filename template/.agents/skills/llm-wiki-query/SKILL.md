---
name: llm-wiki-query
description: Answer a question from the LLM Wiki by searching the compiled catalog first and only opening Raw sources when needed. Use when the user asks a knowledge question that the Wiki may already cover.
---

# LLM Wiki: Query

Answer from compiled knowledge first; reach for Raw sources only when necessary.

## When to use

- The user asks a factual or conceptual question the Wiki might cover.
- You need to ground an answer in this vault's recorded knowledge.

## Steps

1. **Start with the index** for orientation: `Wiki/index.md`.
2. **Search the catalog** — this is the primary entry point, before opening broad Raw context:
   ```bash
   python3 scripts/wiki_tool.py search-catalog --query "user's topic"
   ```
3. **Open the most relevant compiled notes** from the results (`Wiki/Topics|Concepts|Entities/`).
4. **Open Raw sources only when** the compiled note is insufficient, contradictory, or the user explicitly wants source-level verification. Follow each note's `sources` frontmatter to the file under `Raw/Sources/`.
5. **Cite** both the compiled note and the Raw source when the answer depends on source material.

## Guardrails

- Do not assert claims that no compiled note or source supports.
- Prefer the compiled note's wording; it is the reusable, distilled knowledge.
- If nothing matches, say so and offer to ingest a source rather than inventing an answer.
