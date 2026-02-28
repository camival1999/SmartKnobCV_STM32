# Tier 2 Instruction Files

<!-- Owner: SmartKnobCV_STM32 | Last updated: 2026-02-28 -->

Auto-scoped instruction files that are loaded based on file path patterns.

## How Tier 2 Works

VS Code Copilot automatically loads these instructions when working with matching files. Each file uses `applyTo:` frontmatter to specify glob patterns.

## Available Instructions

| File | Scope | Description |
|------|-------|-------------|
| `markdown.instructions.md` | `**/*.md` | Markdown documentation standards |
| `cpp.instructions.md` | `**/*.cpp,**/*.h,**/*.ino` | C++/PlatformIO/SimpleFOC conventions |
| `python.instructions.md` | `**/*.py` | Python package and integration conventions |

## Related

- [AGENTS.md](../AGENTS.md) — Tier system overview
- [copilot-instructions.md](../copilot-instructions.md) — Tier 1 core rules
