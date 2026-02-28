# Roadmap

## Phase 0: Repository Refactor — **Complete** ✓

Separate learning material from PoC code. Separate firmware from Windows driver/software.

| Task | Status |
|------|--------|
| Create `PoC/` + `FOC_Learnings/` folder structure | ✓ Done |
| Move firmware to `PoC/firmware/` | ✓ Done |
| Move Python tools to `PoC/software/smartknob/` | ✓ Done |
| Move learning path to `FOC_Learnings/` | ✓ Done |
| Create Python package structure | ✓ Done |
| Verify firmware build from new location | ✓ Done |
| Update README files | ✓ Done |
| Create initial docs (Architecture, Protocol, Roadmap) | ✓ Done |
| Verify GUI loads from new location | ✓ Done |
| Clean up old files from root | ✓ Done |

## Phase 1: Firmware Modularization + Driver API

Split `main.cpp` into modules. Extract serial communication from GUI into reusable `SmartKnobDriver`.

| Task | Status |
|------|--------|
| Split `main.cpp` into `config.h`, `haptics.h/cpp`, `comms.h/cpp`, `button.h/cpp` | Not started |
| Verify firmware builds and all 4 modes work | Not started |
| Create `SmartKnobDriver` class (serial connect, thread-safe send/receive, callbacks) | Not started |
| Create `protocol.py` (command constants, ACK parsing) | Not started |
| Refactor GUI to use `SmartKnobDriver` | Not started |
| Create `driver-api.md` | Not started |

## Phase 2: Context-Aware Switching + Button Shortcuts

Auto-detect active Windows app and switch knob function. Add double/long press button shortcuts.

| Task | Status |
|------|--------|
| `ActiveWindowDetector` (Win32 foreground window monitoring) | Not started |
| `ContextRouter` (load `contexts.json`, map apps → presets) | Not started |
| Firmware: double-press and long-press detection | Not started |
| Firmware: button event serial messages (`BTN:SHORT/DOUBLE/LONG`) | Not started |
| Driver: button event callbacks | Not started |
| Quick-volume shortcut (double-press toggles volume) | Not started |
| GUI: show current context and active mapping | Not started |

## Phase 3: Haptic Preset System

Define presets in JSON. Apply instantly on context switch with minimal latency.

| Task | Status |
|------|--------|
| `presets.py` — load and validate `presets.json` | Not started |
| `SmartKnobDriver.apply_preset()` | Not started |
| Firmware: `PRESET:` batch command (single-message mode switch) | Not started |
| GUI: preset selector dropdown | Not started |
| Custom presets documentation (`presets.md`) | Not started |

## Phase 4+: Future Expansion

| Feature | Description | Priority |
|---------|-------------|----------|
| Media playback | Play/pause, next/prev track | Medium |
| System tray mode | Background service, minimize to tray | Medium |
| Alt-Tab selector | Bounded detents mapped to open windows | Medium |
| Presentation control | Next/prev slide for PowerPoint | Low |
| USB HID upgrade | Replace serial with native USB HID | Low |
| Overlay notification | Small popup on context switch | Low |
