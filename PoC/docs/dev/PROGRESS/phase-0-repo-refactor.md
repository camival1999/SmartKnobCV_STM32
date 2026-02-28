# Phase 0: Repository Refactor — Complete ✓

**Started:** 2026-02-28
**Completed:** 2026-02-28

## Objective

Separate learning material from PoC code. Separate firmware from Windows driver/software. Establish a clean project structure for ongoing development.

## Sub-Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create `PoC/` + `FOC_Learnings/` folder structure | ✓ Done | Two top-level folders as planned |
| 2 | Move firmware to `PoC/firmware/` | ✓ Done | `main.cpp` + `platformio.ini` |
| 3 | Move Python tools to `PoC/software/smartknob/` | ✓ Done | Package structure with `__init__.py` files |
| 4 | Move learning path to `FOC_Learnings/` | ✓ Done | Includes learning path doc + `.bak` iterations |
| 5 | Create Python package structure | ✓ Done | `smartknob/`, `integrations/`, `gui/`, `config/` |
| 6 | Verify firmware build from new location | ✓ Done | 17.4% Flash, 2.5% RAM, 6.70s |
| 7 | Update README files | ✓ Done | Root, PoC, FOC_Learnings READMEs |
| 8 | Create initial docs | ✓ Done | ARCHITECTURE.md, serial-protocol.md, ROADMAP.md |
| 9 | Verify GUI loads from new location | ✓ Done | Imports updated and verified |
| 10 | Clean up old files from root | ✓ Done | Removed original files after moves |

## Decisions

- **Two top-level folders**: `PoC/` for active development, `FOC_Learnings/` for archived learning material
- **Python package structure**: `smartknob` package with `integrations/` subpackage for individual Windows API wrappers
- **Config files**: `presets.json` and `contexts.json` placed in `PoC/software/config/`
- **Docs location**: Technical docs at `PoC/docs/`, development tracking at `PoC/docs/dev/`

## Issues Encountered

- **PlatformIO CLI not on PATH**: Used full path `$env:USERPROFILE\.platformio\penv\Scripts\pio.exe`
- **Missing Python dependencies**: Installed `pyserial`, `wmi` into workspace `.venv`
- **BUG-001 discovered**: Windows Link options not showing in GUI after refactor (logged in KNOWN-ISSUES.md)
- **BUG-002 discovered**: VS Code Run button not using `.venv` (logged in KNOWN-ISSUES.md)

## Build Verification

```
Firmware: SUCCESS (17.4% Flash, 2.5% RAM, 6.70s)
GUI:     SUCCESS (importlib load verified)
```
