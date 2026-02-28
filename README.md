# SmartKnob STM32

[![Platform](https://img.shields.io/badge/platform-STM32_Nucleo_L452RE-blue.svg)]()
[![SimpleFOC](https://img.shields.io/badge/library-SimpleFOC_v2.4.0-brightgreen.svg)]()
[![FOC](https://img.shields.io/badge/motor_control-FOC-orange.svg)]()
[![Windows](https://img.shields.io/badge/integration-Windows-0078D6.svg)]()
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()

A dual-purpose project for haptic BLDC motor control on STM32: a working **Proof of Concept** for a context-aware haptic input knob that controls Windows applications, and a **learning archive** documenting the journey from zero to FOC motor control.

## Project Structure

### [PoC/](PoC/) — Proof of Concept

The main deliverable. A complete haptic knob system that:

- Provides **4 haptic feedback modes** — detent clicks, free-spinning inertia, spring centering, and bounded range with end-stop walls
- **Controls Windows applications** — volume, screen brightness, scroll, and zoom — all driven by physical knob rotation
- Communicates over **serial protocol** between STM32 firmware and a Python GUI/driver on Windows
- Is evolving toward **context-aware auto-switching** — automatically change knob behavior based on the active Windows application (e.g., Spotify → volume, Chrome → scroll, Photoshop → zoom)

| Subfolder | What's inside |
|-----------|---------------|
| [PoC/firmware/](PoC/firmware/) | PlatformIO C++ project — modular STM32 firmware (config, haptics, comms, button) with FOC motor control |
| [PoC/software/smartknob/](PoC/software/smartknob/) | Cross-platform Python driver — `SmartKnobDriver` class, protocol constants, callbacks (pyserial only) |
| [PoC/software/smartknob_windows/](PoC/software/smartknob_windows/) | Windows app — Tkinter GUI, system integrations (volume, brightness, scroll, zoom), preset/context config |
| [PoC/docs/](PoC/docs/) | Architecture diagram, serial protocol specification, driver API reference, and dev tracking |

### [FOC_Learnings/](FOC_Learnings/) — Learning Archive

A structured record of learning STM32, SimpleFOC, and Field-Oriented Control from scratch:

- **Learning path document** — step-by-step curriculum covering motor theory, encoder integration, PID tuning, and haptic feedback design
- **Firmware iterations** — 4 milestone snapshots (`.bak` files) from the development journey, each representing a key breakthrough (first SSI reading, angle control, full haptic control)

This folder is read-only reference material — all active development happens in `PoC/`.

## Hardware

| Component | Detail |
|-----------|--------|
| **MCU** | STM32L452RET6 (Nucleo L452RE) — 80 MHz Cortex-M4 |
| **Encoder** | MT6701 magnetic encoder, 14-bit resolution (SSI over SPI) |
| **Motor Driver** | SimpleFOCShield V3.2 (DRV8313 + ACS712 current sense) |
| **Motor** | Mitoot 2804 100KV gimbal BLDC (7 pole pairs) |

## Quick Start

### Firmware
```bash
pio run              # Build (run from repo root — platformio.ini is here)
pio run -t upload    # Flash to Nucleo
pio device monitor   # Serial monitor (115200 baud)
```

### Windows Software
```bash
pip install -e "PoC/software/[windows]"    # Install both packages (editable)
python -m smartknob_windows.gui.app        # Launch GUI
```

Connect to the STM32 via the GUI's serial port dropdown, select a haptic mode, and start turning the knob. Use the "Windows Link" section to map knob rotation to system controls.

## Current Status

**Phases 0 and 1** are complete. The codebase has been reorganized into `PoC/` + `FOC_Learnings/`, firmware split into 5 modular C++ files, and a reusable `SmartKnobDriver` API extracted into its own cross-platform package. Next up is **Phase 2: Context-Aware Switching** — auto-detecting the active Windows application to switch knob behavior automatically.

See [PoC/docs/dev/ROADMAP.md](PoC/docs/dev/ROADMAP.md) for the full development roadmap.

## Acknowledgments

Inspired by [**Scott Bezek's SmartKnob**](https://github.com/scottbez1/smartknob) — an incredible open-source haptic input knob that sparked my interest in FOC motor control and haptic feedback. While this is not a fork (different MCU, different goals), Scott's work was the catalyst. Check out his project!

## License

This project is proprietary software. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Camilo Valencia. All rights reserved.
