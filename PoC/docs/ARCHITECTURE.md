# Architecture

## Overview

The SmartKnob PoC is a two-part system: **firmware** running on an STM32 Nucleo board that provides haptic motor control, and **software** running on a Windows PC that connects motor position to system functions.

```
┌─────────────────────┐     Serial (115200)     ┌─────────────────────────────┐
│   STM32 Firmware     │ ←────────────────────→ │       Windows Software       │
│                      │                         │                              │
│  ┌────────────────┐  │    Commands (PC→STM32)  │  ┌──────────────────────┐    │
│  │   SimpleFOC    │  │    Position (STM32→PC)  │  │   SmartKnobDriver    │    │
│  │   FOC Loop     │  │                         │  │   (serial comms)     │    │
│  └───────┬────────┘  │                         │  └──────────┬───────────┘    │
│          │           │                         │             │                │
│  ┌───────▼────────┐  │                         │  ┌──────────▼───────────┐    │
│  │  Haptic Modes  │  │                         │  │   WindowsLink        │    │
│  │  - Detent      │  │                         │  │   (integration       │    │
│  │  - Inertia     │  │                         │  │    orchestrator)     │    │
│  │  - Spring      │  │                         │  └──────────┬───────────┘    │
│  │  - Bounded     │  │                         │             │                │
│  └───────┬────────┘  │                         │  ┌──────────▼───────────┐    │
│          │           │                         │  │   Integrations       │    │
│  ┌───────▼────────┐  │                         │  │   - Volume           │    │
│  │    Comms       │  │                         │  │   - Brightness       │    │
│  │  (Commander    │  │                         │  │   - Scroll           │    │
│  │   + Protocol)  │  │                         │  │   - Zoom             │    │
│  └────────────────┘  │                         │  └──────────────────────┘    │
│                      │                         │                              │
│  ┌────────────────┐  │                         │  ┌──────────────────────┐    │
│  │  Button Input  │  │                         │  │   GUI (Tkinter)      │    │
│  └────────────────┘  │                         │  └──────────────────────┘    │
└──────────────────────┘                         └──────────────────────────────┘
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

| Component | Location | Responsibility |
|-----------|----------|----------------|
| SimpleFOC | firmware | FOC loop, PWM generation, sensor reading |
| Haptic Modes | firmware | Torque computation for each mode |
| Comms | firmware | Serial protocol, command parsing, position reporting |
| Button | firmware | Debounce, mode cycling, future: double/long press |
| SmartKnobDriver | software/smartknob | Serial connection, thread-safe send/receive, callbacks |
| WindowsLink | software/smartknob | Maps position to Windows functions, manages integrations |
| Integrations | software/smartknob/integrations | Individual Windows API wrappers |
| Context | software/smartknob/context | Active window detection, preset routing |
| GUI | software/gui | User interface for manual control and monitoring |

## Hardware

| Component | Model | Interface |
|-----------|-------|-----------|
| MCU | STM32L452RET6 (Nucleo L452RE) | — |
| Encoder | MT6701 14-bit magnetic | SSI over SPI1 @ 1 MHz |
| Motor Driver | SimpleFOCShield V3.2 (DRV8313) | 3x PWM (TIM2+TIM3) |
| Motor | Mitoot 2804 100KV (7 pole pairs) | 3-phase BLDC |
| Current Sense | ACS712-05B (185 mV/A) | Analog (PA0, PA4) |
| User Button | Nucleo onboard (PC13) | GPIO, active LOW |
