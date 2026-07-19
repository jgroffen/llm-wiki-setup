#!/usr/bin/env python3
"""Shared install/lifecycle base class for LLM Wiki plugins.

This module ships with the core wiki template (scripts/wiki_plugin.py). A plugin's install.py
imports it from the target vault and subclasses `PluginInstaller`, declaring only what's
specific to the plugin (name, folders, payload files, AGENTS snippet, post-install message).
The base provides the common lifecycle every plugin shares:

  * verify the target is a plugin-aware LLM Wiki,
  * copy the code payload (manifest, schema, tool script, templates),
  * sync `_prompts/` templates against a per-vault receipt — auto-updating untouched (stock)
    prompts while preserving tailored ones (asking keep/update/diff in a terminal, else
    notifying),
  * create folders, append the AGENTS section once, and run the post-install gate.

Subclasses override the hook attributes/methods; `run()` orchestrates the rest.
"""

import difflib
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


class PluginInstaller:
    # --- Hooks a subclass MUST set -------------------------------------------
    name = "?"                 # plugin name, also the receipt filename stem
    manifest_name = "?.json"   # Schema/plugins/<manifest_name> written by copy_payload
    agents_marker = ""         # unique heading that marks this plugin's AGENTS section
    agents_snippet = None      # Path to the AGENTS-*.md snippet appended to the vault AGENTS.md
    new_dirs = []              # vault-relative folders to create (with .gitkeep when empty)

    def __init__(self, repo, payload):
        self.repo = Path(repo)
        self.payload = Path(payload)

    # --- Hooks a subclass overrides ------------------------------------------
    def payload_copies(self, vault):
        """Return [(src, dst)] of code-payload files to copy into the vault. Override."""
        raise NotImplementedError

    def post_install_message(self, updating):
        """Return the closing message printed after a successful install/update. Override."""
        return ""

    # --- Shared lifecycle ----------------------------------------------------
    def plugin_version(self):
        try:
            return json.loads((self.payload / "manifest.json").read_text(encoding="utf-8")).get("version", "?")
        except (OSError, ValueError):
            return "?"

    def verify_llm_wiki(self, vault):
        wiki_tool = vault / "scripts" / "wiki_tool.py"
        needed = [wiki_tool, vault / "Wiki", vault / "Raw" / "Sources", vault / "Schema"]
        missing = [p for p in needed if not p.exists()]
        if missing:
            die(f"{vault} is not an LLM Wiki (missing "
                f"{', '.join(str(m.relative_to(vault)) for m in missing)}). "
                "Run llm-wiki-setup on this folder first.")
        probe = subprocess.run([sys.executable, str(wiki_tool), "plugins"],
                               capture_output=True, text=True)
        if probe.returncode != 0:
            die("this LLM Wiki core does not support plugins. Update it from llm-wiki-setup "
                "(the core needs the `plugins` command and a plugin-aware wiki_tool.py).")

    def copy_payload(self, vault):
        for src, dst in self.payload_copies(vault):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"  installed {dst.relative_to(vault)}")

    # --- Prompt sync (per-vault receipt) -------------------------------------
    @staticmethod
    def sha256_file(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def receipt_path(self, vault):
        return vault / "Schema" / "plugins" / f"{self.name}.prompts.json"

    def read_receipt(self, vault):
        path = self.receipt_path(vault)
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("prompts", {})
        except (OSError, ValueError):
            return {}

    def write_receipt(self, vault, prompts):
        path = self.receipt_path(vault)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(
            {"plugin": self.name, "version": self.plugin_version(), "prompts": prompts},
            indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def classify_prompt(dst_exists, vault_hash, shipped_hash, receipt_hash):
        """Decide what to do with one prompt. Pure — no I/O.

        Returns: install | up_to_date | update_stock | update_available | customized.
        """
        if not dst_exists:
            return "install"
        if vault_hash == shipped_hash:
            return "up_to_date"
        if receipt_hash is not None and vault_hash == receipt_hash:
            return "update_stock"       # untouched since install, but bundled moved on
        if shipped_hash != receipt_hash:
            return "update_available"   # tailored (or no receipt) AND a newer bundle exists
        return "customized"             # tailored, bundled unchanged since install

    @staticmethod
    def _prompt_resolve(name, dst, src):
        """Interactively resolve a tailored prompt with an available update. True = update."""
        while True:
            ans = input(f"  '_prompts/{name}' is customized; a newer bundled version exists. "
                        "[k]eep / [u]pdate / [d]iff? ").strip().lower()
            if ans in ("", "k", "keep"):
                return False
            if ans in ("u", "update"):
                return True
            if ans in ("d", "diff"):
                diff = difflib.unified_diff(
                    dst.read_text(encoding="utf-8").splitlines(),
                    src.read_text(encoding="utf-8").splitlines(),
                    fromfile=f"{name} (your copy)", tofile=f"{name} (bundled)", lineterm="")
                print("\n".join(diff) or "  (no textual difference)")

    def sync_prompts(self, vault, interactive, force_update, keep):
        src_dir = self.payload / "_prompts"
        if not src_dir.is_dir():
            return
        receipt = self.read_receipt(vault)
        counts = {"installed": 0, "updated": 0, "current": 0, "preserved": 0}
        pending = []

        for src in sorted(src_dir.glob("*.md")):
            name = src.name
            dst = vault / "_prompts" / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shipped_hash = self.sha256_file(src)
            receipt_hash = receipt.get(name, {}).get("hash")
            vault_hash = self.sha256_file(dst) if dst.exists() else None
            action = self.classify_prompt(dst.exists(), vault_hash, shipped_hash, receipt_hash)

            def install(tag):
                shutil.copyfile(src, dst)
                receipt[name] = {"hash": shipped_hash, "version": self.plugin_version()}
                print(f"  {tag} _prompts/{name}")

            if action == "install":
                install("installed"); counts["installed"] += 1
            elif action == "up_to_date":
                receipt[name] = {"hash": shipped_hash, "version": self.plugin_version()}
                counts["current"] += 1
            elif action == "update_stock":
                install("updated (stock)"); counts["updated"] += 1
            elif action == "customized":
                print(f"  preserved _prompts/{name} (customized)"); counts["preserved"] += 1
            else:  # update_available
                if force_update:
                    install("updated (--update-prompts)"); counts["updated"] += 1
                elif keep:
                    print(f"  preserved _prompts/{name} (customized; update available)")
                    counts["preserved"] += 1; pending.append(name)
                elif interactive and self._prompt_resolve(name, dst, src):
                    install("updated"); counts["updated"] += 1
                elif interactive:
                    print(f"  preserved _prompts/{name} (kept your version)")
                    counts["preserved"] += 1
                else:
                    print(f"  preserved _prompts/{name} (customized; update available)")
                    counts["preserved"] += 1; pending.append(name)

        self.write_receipt(vault, receipt)
        print(f"  prompts: {counts['installed']} installed, {counts['updated']} updated, "
              f"{counts['current']} up to date, {counts['preserved']} preserved")
        if pending:
            print(f"  note: {len(pending)} tailored prompt(s) have a newer bundled version "
                  f"({', '.join(pending)}). Re-run in a terminal to review (keep/update/diff), "
                  "or pass --update-prompts to overwrite.")

    def make_dirs(self, vault):
        for d in self.new_dirs:
            path = vault / d
            path.mkdir(parents=True, exist_ok=True)
            if not any(path.iterdir()):
                (path / ".gitkeep").touch()

    def update_agents(self, vault):
        agents = vault / "AGENTS.md"
        snippet = Path(self.agents_snippet).read_text(encoding="utf-8").strip()
        if agents.exists():
            text = agents.read_text(encoding="utf-8")
            if self.agents_marker in text:
                print(f"  AGENTS.md already documents the {self.name} plugin (skipped)")
                return
            agents.write_text(text.rstrip() + "\n\n" + snippet + "\n", encoding="utf-8")
        else:
            agents.write_text(snippet + "\n", encoding="utf-8")
        print("  updated AGENTS.md")

    def run_gate(self, vault):
        wiki_tool = vault / "scripts" / "wiki_tool.py"
        for step in (["plugins"], ["doctor"], ["build"]):
            proc = subprocess.run([sys.executable, str(wiki_tool)] + step)
            if proc.returncode != 0:
                die(f"post-install check failed: wiki_tool.py {' '.join(step)}")

    def run(self, vault, update_prompts=False, keep_prompts=False):
        vault = Path(vault).resolve()
        if not vault.is_dir():
            die(f"{vault} is not a directory")
        updating = (vault / "Schema" / "plugins" / self.manifest_name).exists()
        verb = "Updating" if updating else "Installing"
        prep = "in" if updating else "into"
        print(f"{verb} {self.name} plugin {prep} {vault}")
        self.verify_llm_wiki(vault)
        self.copy_payload(vault)
        self.sync_prompts(vault, interactive=sys.stdin.isatty(),
                          force_update=update_prompts, keep=keep_prompts)
        self.make_dirs(vault)
        self.update_agents(vault)
        self.run_gate(vault)
        msg = self.post_install_message(updating)
        if msg:
            print("\n" + msg)
        return 0
