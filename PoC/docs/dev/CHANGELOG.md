# Changelog

All notable changes to the SmartKnob PoC project.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [Semantic Versioning](https://semver.org/).

---

## [v0.0.3] — 2026-02-28

### Phase 1A: Firmware Modularization

Split monolithic 586-line `main.cpp` into 4 focused modules with clean separation of concerns.

### Phase 1B: Python Driver API

Extracted reusable `SmartKnobDriver` from GUI's raw serial code. Created protocol constants module, thread-safe driver class with callbacks, and refactored GUI to use the driver API.

### Phase 1B Refinements: Package Restructure & Convergence Refactor

Restructured `PoC/software/` into two packages: `smartknob/` (cross-platform driver, pyserial only) and `smartknob_windows/` (Windows app: GUI, integrations, windows_link, config, context). Replaced `_wait_for_convergence()` polling in Lens Zoom link with event-driven `on_seek_done` callback (~30 lines of polling code removed). Added `*.egg-info/` to `.gitignore`.

### Documentation Revision

Corrected and updated project documentation to reflect Phase 1 structural changes.

#### Changed

- `PoC/docs/guides/driver-api.md` — fixed hallucinated date (2025-06-24 → 2026-02-28)
- `PoC/docs/ARCHITECTURE.md` — updated ASCII diagram for two-package split (`smartknob` + `smartknob_windows`), added firmware module table, added `platformio.ini` repo-root note
- `README.md` — updated software descriptions for two-package structure, revised Quick Start commands (repo-root `pio run` + editable install), current status → Phase 2 next
- `PoC/README.md` — rewrote PC Control Software section for `smartknob` + `smartknob_windows` packages, added `platformio.ini` repo-root note
- `PoC/docs/README.md` — added `driver-api.md` to Guides listing

#### Added (cross-repo)

- Added `## MANDATORY: Date Verification` section to all 23 agent files across 4 repositories (CopilotTribunal: 6, JARVIS: 6, USD: 6, SmartKnobCV_STM32: 5) — prevents date hallucination in AI-generated documentation

### Added

- `PoC/software/smartknob_windows/__init__.py` — Windows app package init
- `PoC/software/smartknob_windows/gui/__init__.py` — GUI subpackage init
- `PoC/firmware/src/config.h` — pin definitions, mode enum, extern declarations for all hardware objects and parameters
- `PoC/firmware/src/haptics.h/cpp` — 4 torque computation functions (haptic, inertia, spring, bounded) with inertia state management
- `PoC/firmware/src/comms.h/cpp` — 19 serial command handlers, position reporting, Commander setup, startup banner
- `PoC/firmware/src/button.h/cpp` — `ButtonState` struct for multi-button support, debounced detection, mode cycling
- `PoC/firmware/src/main_monolithic.bak` — backup of original monolithic main.cpp
- "Understanding C++ Firmware Structure" section in `GETTING-STARTED.md` — 7 subsections covering header/source files, extern keyword, compile-link process, include guards, multi-button struct pattern, globals vs classes tradeoffs, framework swappability
- `PoC/software/smartknob/protocol.py` — protocol constants, `HapticMode` enum, `MODE_PARAMETERS` dict, `print_help()` function
- `PoC/software/smartknob/driver.py` — `SmartKnobDriver` class with thread-safe serial communication, position/mode callbacks, 20+ parameter methods
- `PoC/docs/guides/driver-api.md` — Driver API documentation with quick start, callback usage, and migration guide

### Changed

- `PoC/firmware/src/main.cpp` — refactored from 586 lines to ~155 lines (hardware object definitions, parameter definitions, `setup()`, `loop()` only)
- `PoC/software/gui/app.py` → `PoC/software/smartknob_windows/gui/app.py` — moved to Windows app package; replaced `_wait_for_convergence()` polling with `on_seek_done` callback; removed `time` import
- `PoC/software/smartknob/windows_link.py` → `PoC/software/smartknob_windows/windows_link.py` — moved to Windows app package; updated imports to `smartknob_windows.integrations`
- `PoC/software/smartknob/integrations/` → `PoC/software/smartknob_windows/integrations/` — moved to Windows app package
- `PoC/software/config/` → `PoC/software/smartknob_windows/config/` — moved to Windows app package
- `PoC/software/smartknob/context/` → `PoC/software/smartknob_windows/context/` — moved to Windows app package
- `PoC/software/pyproject.toml` — split dependencies (core: pyserial; windows extras: pycaw, comtypes, wmi); find both packages
- `PoC/software/smartknob/__init__.py` — updated docstring (cross-platform driver only)
- `.github/copilot-instructions.md` — updated repo architecture table for new package structure
- `PoC/docs/guides/driver-api.md` — updated module structure table
- `PoC/docs/guides/GETTING-STARTED.md` — updated package docs, GUI path, verify commands
- `.gitignore` — added `*.egg-info/`

### Fixed

- **BUG-003:** PlatformIO VS Code extension couldn't detect `nucleo_l452re` environment — `platformio.ini` was nested in `PoC/firmware/` instead of repo root. Moved to `SmartKnobCV_STM32/platformio.ini` with path overrides pointing to `PoC/firmware/` subdirectories. Updated GETTING-STARTED.md Section 4.
- **BUG-004:** "Bad position line" warnings on startup — driver position parser (`_process_line()`) matched any line starting with `P`, including firmware info messages like `Position: 60.12 deg`. Added stricter check (digit/minus after `P`) so only actual position reports are parsed.

### Verified

- Firmware builds: 17.5% Flash, 2.5% RAM (unchanged from monolithic)
- Zero compiler warnings
- All Python imports verified
- GUI syntax verified

---

## [v0.0.2] — 2026-02-28

### Phase 0: Repository Refactor

Complete restructuring from flat layout to organized PoC + FOC_Learnings structure.

### Added

- `PoC/firmware/` — firmware isolated with its own `platformio.ini`
- `PoC/software/smartknob/` — Python package with `__init__.py` files
- `PoC/software/smartknob/integrations/` — volume, brightness, scroll, zoom modules
- `PoC/software/config/` — `presets.json` (6 presets) and `contexts.json` (app mappings)
- `PoC/software/gui/app.py` — GUI with updated imports
- `PoC/docs/ARCHITECTURE.md` — system architecture documentation
- `PoC/docs/serial-protocol.md` — serial command protocol specification
- `PoC/docs/ROADMAP.md` — 4-phase development roadmap
- `FOC_Learnings/` — learning path document and firmware iteration backups
- Root `README.md` — expanded project gateway with hardware table and license section

### Changed

- Moved `src/main.cpp` → `PoC/firmware/src/main.cpp`
- Moved `platformio.ini` → `PoC/firmware/platformio.ini`
- Moved `tools/smartknob_simple.py` → `PoC/software/gui/app.py`
- Moved `tools/windows_link.py` → `PoC/software/smartknob/windows_link.py`
- Moved `tools/*_control.py` → `PoC/software/smartknob/integrations/`
- Moved `.bak` files → `FOC_Learnings/firmware_iterations/`
- Moved `stm32_smart_knob_learning_path.md` → `FOC_Learnings/`
- Updated all Python imports to use `smartknob` package paths

### Verified

- Firmware builds: 17.4% Flash, 2.5% RAM, 6.70s build time
- GUI loads successfully with updated imports

### Fixed

- **BUG-001:** Windows Link options not showing after refactor — `smartknob` package was not installed in venv. Fixed with `pip install -e PoC/software/`
- **BUG-002:** VS Code Run button using system Python instead of `.venv` — added `.vscode/settings.json` with `python.defaultInterpreterPath`

### Documentation

- Added `PoC/docs/guides/GETTING-STARTED.md` — developer setup guide with Python package concepts, venv setup, VS Code configuration, and troubleshooting
- Added `.github/` — CopilotTribunal agent framework (agents, instructions, processes)
- Added `PoC/docs/dev/` — development tracking (CHANGELOG, KNOWN-ISSUES, ROADMAP, PROGRESS/)

---

## [v0.0.1] — 2026-02-28

### Pre-Prototype Working Demo

First functional demo with all core features working end-to-end.

### Added

- 4 haptic modes: Haptic (detent), Inertia (flywheel), Spring (centered), Bounded (walls)
- Serial protocol: position reporting, mode switching, parameter tuning
- Windows integrations: volume, brightness, scroll, zoom control
- Tkinter GUI for manual control and monitoring
- Button cycling between haptic modes
- Learning path documentation

---

## [v0.0.0] — 2026-02-22

### Initial Release

Project repository created with initial firmware and tools.

### Added

- STM32 firmware with SimpleFOC motor control
- MT6701 SSI encoder integration
- Basic serial command interface
- Python control scripts
