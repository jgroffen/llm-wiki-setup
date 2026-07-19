This repo contains instructions for setting up an LLM Wiki using Obsidian.

# One-Time Setup

1. Install Obsidian:
	- https://obsidian.md/download
2. Install Obsidian WebClipper add-on to your browser
	- https://addons.mozilla.org/en-US/firefox/addon/web-clipper-obsidian/
3. Ensure the command line interface in Obsidian General settings under the
   Advanced section is enabled.
4. Install obsidian skills into your AI client tool (see the next section).
   See https://github.com/kepano/obsidian-skills for details.

## AI Client Setup - Claude

```
# You can install the skills globally for all projects to access:
git clone https://github.com/kepano/obsidian-skills.git ~/.claude/skills/obsidian-skills

# ... or install per project:
git clone https://github.com/kepano/obsidian-skills.git .claude

```

## AI Client Setup - Codex

```
# You can install the skills globally for all projects to access:
git clone https://github.com/kepano/obsidian-skills.git ~/.agents/skills/obsidian-skills
rm -r ~/.agents/skills/obsidian-skills/.claude-plugin/

# ... or install per project:
git clone https://github.com/kepano/obsidian-skills.git .codex
rm -r .codex/.claude-plugin/
```

## AI Client Setup - OpenCode

```
# install obsidian skills for OpenCode
git clone https://github.com/kepano/obsidian-skills.git ~/.opencode/skills/obsidian-skills
```

# Setup Notes

1. In Obsidian, create a new Vault
   1. A new folder with the name of your vault will be created under the
      folder you select.
2. Copy `llm-wiki-setup.md` and the templated llm-wiki files from this project
   to the root of the new Vault.:
   
   ```bash
   NEW_WIKI_PATH=/path/to/new/vault/
   cp llm-wiki-setup.md $NEW_WIKI_PATH
   cp -r template/. $NEW_WIKI_PATH
   ```

3. From the root of your new Vault, start your local AI client tool. If you
   haven't yet, ensure your local tool has access to the obsidian skills
   (usually with a `/skills` command), then give it the following prompt:
   
   ```
   Use @llm-wiki-setup.md to build the core LLM Wiki in this folder. Follow the setup order exactly, commit after each major step if git is available, run the maintenance checks, and stop once `Step 06: Final Acceptance Criteria` described in @llm-wiki-setup.md passes.
   ```

4. Install Plugins - an LLM-Wiki supports a plugin concept which adds
   content-specific context to the wiki. Plugins reuse shared code the core ships
   (`scripts/wiki_plugin.py`, `scripts/wiki_notes.py`), so **make sure the vault's core is
   up to date first** (re-copy `template/.` — step 2 — if you set the vault up before those
   modules existed). Then clone the plugin repos and install them into your repo:

   ```bash
   # clone the plugin repos
   cd ~/sandbox/
   git clone git@github.com:jgroffen/mtg-wiki.git
   git clone git@github.com:jgroffen/llm-quiz.git

   # install into your llm-wiki repo
   ~/sandbox/mtg-wiki/install.py .
   ~/sandbox/llm-quiz/install.py .
   ```

   If a plugin's installer says the core is too old (no `scripts/wiki_plugin.py`), re-run the
   `cp -r template/. $NEW_WIKI_PATH` from step 2 to refresh the core, then re-install.

# Usage Notes

Use this prompt after the core system exists:

```
Read AGENTS.md and inspect the current LLM Wiki. Search the catalog before opening Raw sources. Compile any unprocessed Raw sources into concise Wiki notes, keep every claim linked to sources, rebuild indexes, run lint/source checks, and summarize what changed.
```

## Plugin examples

The examples below assume you installed the plugins (step 4 above) and are run from the vault
root. Each plugin also bundles skills you can drive in natural language (e.g. "populate the
Bloomburrow set", "make a quiz about Bloomburrow", "add trivia to the quiz"); the commands are
the deterministic equivalents.

### Populate a set with `mtg-wiki`

Pull a Magic set's cards from Scryfall into `card`/`set`/`mechanic` notes (or use the
**mtg-wiki-populate** skill):

```bash
python3 scripts/mtg_tool.py populate-set --code blb --limit 15   # a slice, to try it out
python3 scripts/mtg_tool.py populate-set --code blb              # the whole set
```

### Create a quiz with `llm-quiz`

Create a quiz and its ordered categories, then add questions grounded in the wiki's notes (or
use the **llm-quiz-author** / **llm-quiz-questions** skills):

```bash
python3 scripts/quiz_tool.py new-quiz --title "Bloomburrow Basics" \
    --topic "the Bloomburrow set" --scope "BLB cards, mechanics & set facts" \
    --category "Mechanics" --category "Cards" --category "Lore"

python3 scripts/quiz_tool.py add-question --quiz bloomburrow-basics --category "Mechanics" \
    --difficulty 2 --format multiple-choice \
    --question "What does Offspring do? A) ... B) ... C) ... D) ..." \
    --answer "B) Pay an extra cost to also make a 1/1 token copy." --based-on offspring
```

### Add trivia to a quiz with `llm-quiz`

Attach wiki-grounded trivia to a share of a quiz's questions (or use the **llm-quiz-trivia**
skill). `--quiz` is optional — omit it and the tool auto-selects the only quiz or prompts you:

The easiest way is to just ask, letting the **llm-quiz-trivia** skill drive it:

```
Add trivia to about 30% of the questions in the Bloomburrow Basics quiz. Ground every fact in the wiki's content notes (not the quiz's own questions), spread it across the difficulty range, and skip anything the wiki doesn't have good material for.
```

Or run the commands directly. `--quiz` is optional — omit it and the tool auto-selects the only
quiz or prompts you:

```bash
python3 scripts/quiz_tool.py trivia-plan --percent 30          # per-category quotas + coverage

python3 scripts/quiz_tool.py add-trivia --question bloomburrow-basics-2-mechanics-11-... \
    --trivia "Offspring debuted in Bloomburrow across many creature rarities." \
    --based-on offspring
```

### Tailoring the prompt templates

Installing a plugin drops reusable prompt templates into the vault's `_prompts/` — e.g. llm-quiz
adds `quiz-structure.md`, `question-generation.md`, `trivia-generation.md`, and `take-quiz.md`;
mtg-wiki adds `mtg-set-quiz.md`. The plugin **skills load these prompts** — preferring the
vault's `_prompts/<name>.md` and falling back to a default bundled with the skill — so **editing
a prompt is how you tailor that skill's behavior** to your vault's content domain (the topics it
asks about, what counts as good trivia, how it runs a quiz, etc.).

You don't have to wire anything up: the skills pick up your edits automatically. On re-install,
a plugin content-hashes each prompt against a per-vault receipt: an **untouched prompt is
auto-updated** so bundled improvements reach you, while a prompt you've **customized is
preserved** — the installer asks keep/update/diff in a terminal, or notes an update is available
when run non-interactively (`--update-prompts` / `--keep-prompts` override). So your tailoring is
safe, but stock prompts won't silently go stale.

# Thankyou

This process is heavily based on the work of `wanderloots`: https://github.com/wanderloots-tutorials/vibe-coding/blob/main/wanderloots-llm-wiki-core-setup-v1.0.0.md
