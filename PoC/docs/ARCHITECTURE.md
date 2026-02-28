# Architecture

## Overview

The SmartKnob PoC is a two-part system: **firmware** running on an STM32 Nucleo board that provides haptic motor control, and **software** running on a Windows PC that connects motor position to system functions.

```
┌───────────────────────┐    Serial (115200)    ┌─────────────────────────────────────┐
│   STM32 Firmware      │ ←──────────────────→ │            PC Software               │
│   (PoC/firmware/)     │                       │                                      │
│                       │  Commands (PC→STM32)  │  ┌────────────────────────────────┐  │
│  ┌─────────────────┐  │  Position (STM32→PC)  │  │  smartknob (cross-platform)    │  │
│  │  SimpleFOC      │  │                       │  │  ┌──────────────────────────┐  │  │
│  │  FOC Loop       │  │                       │  │  │  SmartKnobDriver         │  │  │
│  └────────┬────────┘  │                       │  │  │  (thread-safe serial,    │  │  │
│           │           │                       │  │  │   callbacks, protocol)   │  │  │
│  ┌────────▼────────┐  │                       │  │  └──────────────────────────┘  │  │
│  │  Haptic Modes   │  │                       │  │  protocol.py  driver.py        │  │
│  │  (haptics.cpp)  │  │                       │  └────────────────┬───────────────┘  │
│  │  - Detent       │  │                       │                   │                  │
│  │  - Inertia      │  │                       │  ┌────────────────▼───────────────┐  │
│  │  - Spring       │  │                       │  │  smartknob_windows (Win only)  │  │
│  │  - Bounded      │  │                       │  │  ┌──────────────────────────┐  │  │
│  └────────┬────────┘  │                       │  │  │  WindowsLink             │  │  │
│           │           │                       │  │  │  (integration            │  │  │
│  ┌────────▼────────┐  │                       │  │  │   orchestrator)          │  │  │
│  │  Comms          │  │                       │  │  └──────────┬───────────────┘  │  │
│  │  (comms.cpp)    │  │                       │  │             │                  │  │
│  │  Commander      │  │                       │  │  ┌──────────▼───────────────┐  │  │
│  │  + Protocol     │  │                       │  │  │  Integrations            │  │  │
│  └─────────────────┘  │                       │  │  │  - Volume  - Brightness  │  │  │
│                       │                       │  │  │  - Scroll  - Zoom        │  │  │
│  ┌─────────────────┐  │                       │  │  └──────────────────────────┘  │  │
│  │  Button Input   │  │                       │  │                                │  │
│  │  (button.cpp)   │  │                       │  │  ┌──────────────────────────┐  │  │
│  └─────────────────┘  │                       │  │  │  GUI (Tkinter)           │  │  │
│                       │                       │  │  └──────────────────────────┘  │  │
│  ┌─────────────────┐  │                       │  │                                │  │
│  │  Config         │  │                       │  │  config/ context/              │  │
│  │  (config.h/cpp) │  │                       │  └────────────────────────────────┘  │
│  └─────────────────┘  │                       │                                      │
└───────────────────────┘                       └──────────────────────────────────────┘
```

## Data Flow

### Position Reporting (STM32 → PC)

1. `motor.loopFOC()` updates `motor.shaft_angle` at >1 kHz
2. `reportPosition()` checks thresholds (0.5° change, 20ms interval)
3. Sends `P<angle_degrees>` over serial
4. `SmartKnobDriver` receives and fires position callbacks
5. `WindowsLink.process_position()` maps angle to system function (e.g., volume)
6. Integration module calls Windows API

### Command Flow (PC → STM32)

1. GUI / driver sends command string (e.g., `S36`, `H`, `Z45.0`)
2. STM32 Commander dispatches to handler function
3. Handler updates parameters / mode
4. Handler sends acknowledgment: `A:<command>` (e.g., `A:S36`)

## Component Responsibilities

### Firmware (`PoC/firmware/src/`)

| Module | File(s) | Responsibility |
|--------|---------|----------------|
| Config | `config.h`, `config.cpp` | Pin definitions, hardware constants, `HapticMode` enum, runtime parameter defaults |
| SimpleFOC | via library | FOC loop, PWM generation, sensor reading |
| Haptic Modes | `haptics.h`, `haptics.cpp` | 4 torque computation functions (haptic, inertia, spring, bounded) with inertia state |
| Comms | `comms.h`, `comms.cpp` | 19 serial command handlers, position reporting, Commander setup, startup banner |
| Button | `button.h`, `button.cpp` | `ButtonState` struct, debounced input, mode cycling |
| Main | `main.cpp` | ~115 lines — hardware object definitions, `setup()`, `loop()` glue |

> **Build config:** `platformio.ini` lives at the **repo root** with `[platformio]` section path overrides pointing to `PoC/firmware/` subdirectories. Run `pio run` from the repo root.

### Software (`PoC/software/`)

Two Python packages installed via `pip install -e PoC/software/`:

| Package | Location | Platform | Responsibility |
|---------|----------|----------|----------------|
| `smartknob` | `software/smartknob/` | Cross-platform (pyserial only) | Reusable driver library |
| `smartknob_windows` | `software/smartknob_windows/` | Windows only | GUI + Windows integrations |

| Component | Package / Location | Responsibility |
|-----------|-------------------|----------------|
| SmartKnobDriver | `smartknob/driver.py` | Thread-safe serial connection, callbacks, 20+ parameter methods |
| Protocol | `smartknob/protocol.py` | `HapticMode` enum, command/response constants, `MODE_PARAMETERS` dict |
| WindowsLink | `smartknob_windows/windows_link.py` | Maps knob position to Windows functions, manages integrations |
| Integrations | `smartknob_windows/integrations/` | Individual Windows API wrappers (volume, brightness, scroll, zoom) |
| Context | `smartknob_windows/context/` | Active window detection, preset routing (Phase 2) |
| GUI | `smartknob_windows/gui/app.py` | Tkinter UI for manual control, monitoring, and Windows Link |

## Hardware

| Component | Model | Interface |
|-----------|-------|-----------|
| MCU | STM32L452RET6 (Nucleo L452RE) | — |
| Encoder | MT6701 14-bit magnetic | SSI over SPI1 @ 1 MHz |
| Motor Driver | SimpleFOCShield V3.2 (DRV8313) | 3x PWM (TIM2+TIM3) |
| Motor | Mitoot 2804 100KV (7 pole pairs) | 3-phase BLDC |
| Current Sense | ACS712-05B (185 mV/A) | Analog (PA0, PA4) |
| User Button | Nucleo onboard (PC13) | GPIO, active LOW |
