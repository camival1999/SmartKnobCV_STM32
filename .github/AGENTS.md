# AI Agent Instructions

<!-- Owner: SmartKnobCV_STM32 | Version: 5.0 | Last updated: 2026-02-28 -->

This repository uses a **3-rule agent architecture** for AI-assisted development.

## Tiered Instruction System

| Tier | Location | Description |
|------|----------|-------------|
| **Tier 1** | [copilot-instructions.md](copilot-instructions.md) | Always-on core agent rules |
| **Tier 2** | [instructions/](instructions/) | Auto-scoped tool/language instructions |
| **Tier 3** | [processes/](processes/), [agents/](agents/), `PoC/docs/` | On-demand deep context |

## Tier 1: Core Rules (Always-On)

**Primary instruction file:** [copilot-instructions.md](copilot-instructions.md)

## Tier 2: Auto-Scoped Instructions

**Language-specific instructions** (auto-applied by path):

- [instructions/markdown.instructions.md](instructions/markdown.instructions.md) — All `.md` files
- [instructions/cpp.instructions.md](instructions/cpp.instructions.md) — All `.cpp` and `.h` files
- [instructions/python.instructions.md](instructions/python.instructions.md) — All `.py` files

## Tier 3: On-Demand Reference

- [processes/standard-repo-structure.md](processes/standard-repo-structure.md) — Repository folder structure
- [processes/agent-patterns.md](processes/agent-patterns.md) — Lifecycle, escalation patterns
- [agents/README.md](agents/README.md) — Available agent profiles
- [PoC/docs/ARCHITECTURE.md](../PoC/docs/ARCHITECTURE.md) — System architecture
- [PoC/docs/serial-protocol.md](../PoC/docs/serial-protocol.md) — Serial protocol specification

## Quick Rules

1. **Main agent** must call `ask_user` at the end of every response
2. **Main agent** invokes Scribe after significant events
3. **Main agent** delegates complex work to subagents with 3-element header
4. **Subagents** never call `ask_user` — return results to main agent only
5. **Documentation-first**: Read README files before making changes
6. **Git operations** require explicit user approval

For complete rules, see [copilot-instructions.md](copilot-instructions.md).
