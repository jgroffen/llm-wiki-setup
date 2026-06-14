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
2. Copy `llm-wiki-setup.md` from this project to the root of the new Vault.:
   
   ```
   cp -r /path/to/llm-wiki-setup/llm-wiki-setup.md /path/to/new/vault/
   ```

3. From the root of your new Vault, start your local AI client tool and give it
   the following prompt:
   
   ```
   Use @llm-wiki-setup.md to build the core LLM Wiki in this folder. Follow the setup order exactly, commit after each major step if git is available, run the maintenance checks, and stop once `Step 06: Final Acceptance Criteria` described in @llm-wiki-setup.md passes.
   ```

# Usage Notes

Use this prompt after the core system exists:

```
Read AGENTS.md and inspect the current LLM Wiki. Search the catalog before opening Raw sources. Compile any unprocessed Raw sources into concise Wiki notes, keep every claim linked to sources, rebuild indexes, run lint/source checks, and summarize what changed.
```

# Thankyou

This process is heavily based on the work of `wanderloots`: https://github.com/wanderloots-tutorials/vibe-coding/blob/main/wanderloots-llm-wiki-core-setup-v1.0.0.md
