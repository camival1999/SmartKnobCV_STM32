# SmartKnob Driver API

> **Created:** 2026-02-28 | **Phase:** 1B

## Overview

`SmartKnobDriver` is the single Python interface to the SmartKnob STM32 firmware. It owns the serial connection, runs a background reader thread, and dispatches events via callbacks. The GUI (or any other consumer) never touches `serial` directly.

```
┌──────────┐    callbacks     ┌─────────────────┐    serial    ┌──────────┐
│  GUI /   │ ◄──────────────  │ SmartKnobDriver │ ◄──────────► │  STM32   │
│  Script  │  ──────────────► │  (thread-safe)  │              │ Firmware │
└──────────┘    method calls  └─────────────────┘              └──────────┘
```

## Quick Start

```python
from smartknob import SmartKnobDriver, HapticMode

knob = SmartKnobDriver()
knob.on_position = lambda angle: print(f"{angle:.1f}°")
knob.connect("COM3")

knob.set_mode(HapticMode.HAPTIC)
knob.set_detent_count(24)
knob.seek(90.0)

knob.disconnect()
```

## Module Structure

| Package | File | Purpose |
|---------|------|---------|
| `smartknob` | `protocol.py` | Constants, enums, `print_help()` — no I/O |
| `smartknob` | `driver.py` | `SmartKnobDriver` class — serial I/O + threading |
| `smartknob` | `__init__.py` | Convenience re-exports |
| `smartknob_windows` | `gui/app.py` | Tkinter GUI — uses driver, zero serial code |
| `smartknob_windows` | `windows_link.py` | Motor ↔ Windows function binding |
| `smartknob_windows` | `integrations/` | Volume, brightness, scroll, zoom controllers |
| `smartknob_windows` | `config/` | Presets and context mappings |
| `smartknob_windows` | `context/` | Active window detection |

> `smartknob` is cross-platform (only depends on `pyserial`).
> `smartknob_windows` is Windows-specific (`pycaw`, `comtypes`, `wmi`).

## Connection

```python
# List available ports
ports = SmartKnobDriver.list_ports()  # → ["COM3", "COM5"]

# Connect
knob = SmartKnobDriver()
knob.connect("COM3")       # Opens at 115200 baud
print(knob.is_connected)   # True
print(knob.current_angle)  # Last known angle (float)

# Disconnect
knob.disconnect()
```

## Callbacks

All callbacks fire on the reader thread. If updating GUI widgets, schedule onto the GUI event loop:

```python
# Tkinter example
knob.on_position = lambda angle: root.after(0, update_label, angle)

# PyQt6 example (future)
knob.on_position = lambda angle: QMetaObject.invokeMethod(...)
```

| Callback | Signature | When |
|----------|-----------|------|
| `on_position` | `(angle_deg: float) -> None` | Every `P<angle>` line |
| `on_ack` | `(ack_text: str) -> None` | Every `A:<text>` line |
| `on_seek_done` | `() -> None` | `A:SEEK_DONE` received |
| `on_raw` | `(line: str) -> None` | Unrecognised lines |

## Mode Switching

```python
from smartknob.protocol import HapticMode

knob.set_mode(HapticMode.HAPTIC)   # Sine-based detents
knob.set_mode(HapticMode.INERTIA)  # Virtual flywheel
knob.set_mode(HapticMode.SPRING)   # Centered return
knob.set_mode(HapticMode.BOUNDED)  # Detents within walls
```

## Parameter Methods

### Haptic (affects HAPTIC + BOUNDED)

| Method | Args | Description |
|--------|------|-------------|
| `set_detent_count(count)` | `int` 2–360 | Detents per 360° |
| `set_detent_strength(volts)` | `float` 0.5–6.0 | Snap voltage |

### Inertia

| Method | Args | Description |
|--------|------|-------------|
| `set_inertia(virtual_mass)` | `float` 1–20 | Flywheel mass |
| `set_damping(drag_coefficient)` | `float` 0–5 | Drag |
| `set_friction(static_friction)` | `float` 0–1 | Min force to spin |
| `set_coupling(spring_constant)` | `float` 10–100 | Motor–flywheel link |

### Spring

| Method | Args | Description |
|--------|------|-------------|
| `set_spring_stiffness(volts_per_radian)` | `float` 0.5–30 | Spring constant |
| `set_spring_center(angle_deg)` | `float` or `None` | Center position (None = current) |
| `set_spring_damping(damping)` | `float` 0–2 | Velocity damping |

### Bounded

| Method | Args | Description |
|--------|------|-------------|
| `set_lower_bound(angle_deg)` | `float` | Lower wall (degrees) |
| `set_upper_bound(angle_deg)` | `float` | Upper wall (degrees) |
| `set_wall_strength(volts_per_radian)` | `float` 1–30 | Wall stiffness |

### Position

| Method | Args | Description |
|--------|------|-------------|
| `query_position()` | — | Request angle (fires `on_position`) |
| `query_state()` | — | Request state dump (fires `on_raw`) |
| `seek(angle_deg)` | `float` | Seek to angle |
| `seek_zero()` | — | Seek to 0° |

### Motor PID

| Method | Args | Description |
|--------|------|-------------|
| `set_pid_p(proportional_gain)` | `float` 0–100 | P-term (default 50) |
| `set_pid_i(integral_gain)` | `float` 0–5 | I-term (default 0) |
| `set_pid_d(derivative_gain)` | `float` 0–5 | D-term (default 0.3) |
| `set_velocity_limit(radians_per_second)` | `float` 0–100 | Velocity cap (default 40) |

## Thread Safety

- All public methods acquire an internal `threading.Lock` before touching the serial port
- The reader thread runs as a daemon — it dies when the main process exits
- `current_angle` property is thread-safe (lock-protected read)
- Callbacks fire on the reader thread — schedule GUI updates accordingly

## Protocol Reference

Call `print_help()` for a quick reference of all commands:

```python
from smartknob.protocol import print_help
print_help()
```

## PyQt6 Migration Path

The driver is GUI-framework-agnostic. To migrate from Tkinter to PyQt6:

| Layer | Change needed |
|-------|---------------|
| `protocol.py` | None |
| `driver.py` | None |
| `windows_link.py` | None |
| `integrations/` | None |
| `gui/app.py` | Rewrite widgets only — all `driver.*` calls stay identical |
