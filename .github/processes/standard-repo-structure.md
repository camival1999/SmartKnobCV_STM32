# SmartKnobCV_STM32 Repository Structure

> **Owner:** SmartKnobCV_STM32 | **Version:** 1.0 | **Last updated:** 2026-02-28

---

## Structure

```
SmartKnobCV_STM32/
├── README.md                           # Project overview, quick start
├── LICENSE                             # Proprietary license
├── .gitignore                          # Build/IDE/venv ignores
│
├── .github/                            # AI & GitHub configuration
│   ├── copilot-instructions.md         # Tier 1: Core agent rules
│   ├── AGENTS.md                       # Tier overview
│   ├── agents/                         # Subagent profiles
│   ├── instructions/                   # Tier 2: Auto-scoped by file type
│   ├── processes/                      # Tier 3: On-demand workflows
│   └── prompts/                        # Reusable prompt templates
│
├── PoC/                                # Proof of Concept (active development)
│   ├── firmware/                       # PlatformIO STM32 project
│   │   ├── platformio.ini
│   │   └── src/main.cpp
│   ├── software/                       # Python package + GUI
│   │   ├── pyproject.toml
│   │   ├── requirements.txt
│   │   ├── gui/app.py
│   │   ├── smartknob/                  # Python package
│   │   │   ├── windows_link.py
│   │   │   ├── integrations/           # Volume, brightness, scroll, zoom
│   │   │   └── context/               # Context-aware switching (Phase 2)
│   │   └── config/                     # Presets and context mappings
│   └── docs/                           # PoC documentation
│       ├── README.md                   # Docs index
│       ├── ARCHITECTURE.md             # System architecture
│       ├── serial-protocol.md          # Serial protocol specification
│       └── dev/                        # Development tracking (Scribe-maintained)
│           ├── ROADMAP.md
│           ├── CHANGELOG.md
│           ├── KNOWN-ISSUES.md
│           └── PROGRESS/               # Per-phase progress tracking
│
├── FOC_Learnings/                      # Learning archive (read-only reference)
│   ├── README.md
│   ├── stm32_smart_knob_learning_path.md
│   └── firmware_iterations/            # Development milestone snapshots
│
└── .venv/                              # Python virtual environment (gitignored)
```

---

## Folder Purposes

### `PoC/` — Proof of Concept

Active development. Contains the complete haptic knob system:

| Subfolder | Purpose |
|-----------|---------|
| `firmware/` | PlatformIO C++ project for STM32 |
| `software/` | Python package with driver, integrations, and GUI |
| `docs/` | Technical docs (architecture, protocol) + Scribe-tracked dev files |

### `FOC_Learnings/` — Learning Archive

Read-only reference material documenting the journey from zero to FOC motor control. Not actively modified.

### `.github/` — AI Configuration

CopilotTribunal agent framework adapted for this project.

---

## Related

- [Agent Patterns](agent-patterns.md)
- [Core Agent Rules](../copilot-instructions.md)
