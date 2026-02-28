# Changelog

All notable changes to the SmartKnob PoC project.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [Semantic Versioning](https://semver.org/).

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
