---
description: 'C++ and PlatformIO development standards for STM32 firmware'
applyTo: '**/*.cpp,**/*.h,**/*.ino'
lastUpdated: 2026-02-28
---
<!-- Owner: SmartKnobCV_STM32 | Last updated: 2026-02-28 -->
# C++ / PlatformIO / SimpleFOC Standards

Standards for all C++ firmware code in this repository.

---

## Build System

| Tool | Version | Notes |
|------|---------|-------|
| **PlatformIO** | Latest | Build via `pio run`, upload via `pio run -t upload` |
| **Framework** | Arduino (STM32Duino) | `framework = arduino` in `platformio.ini` |
| **Board** | `nucleo_l452re` | STM32L452RET6, 80 MHz Cortex-M4 |

### Build Commands

```bash
cd PoC/firmware
pio run                   # Build
pio run -t upload         # Flash
pio device monitor        # Serial monitor (115200 baud)
```

### Build Flags

- `-Wl,-u,_printf_float` — Required for float printing over serial
- `lib_archive = false` — Required for SimpleFOC to link properly

---

## Library Conventions

| Library | Version | Purpose |
|---------|---------|---------|
| **SimpleFOC** | v2.4.0 | FOC motor control |
| **SimpleFOCDrivers** | v1.0.9 | MT6701 SSI encoder driver |

### SimpleFOC Patterns

```cpp
// Motor initialization — always in this order
motor.linkSensor(&sensor);
motor.linkDriver(&driver);
motor.init();
motor.initFOC();
```

- Use `motor.loopFOC()` in every loop iteration
- Use `motor.move(target_torque)` for torque control mode
- Use `motor.controller = MotionControlType::torque` for haptic feedback

---

## Pin Definitions

- Define all pin assignments in header files (e.g., `config.h`)
- Use descriptive `#define` names: `PIN_MOTOR_PWM_A`, `PIN_ENCODER_CS`
- Group by peripheral: motor pins, encoder pins, button pins

```cpp
// Good
#define PIN_MOTOR_PWM_A PB10
#define PIN_MOTOR_PWM_B PC7
#define PIN_MOTOR_PWM_C PB4
#define PIN_MOTOR_ENABLE PA9

// Bad
#define A PB10
#define B PC7
```

---

## Serial Protocol

- Baud rate: **115200**
- Line terminator: `\n`
- Character encoding: ASCII text
- All commands are single-character + optional arguments
- Position reports: `POS:angle_deg\n` format

See `PoC/docs/serial-protocol.md` for full protocol specification.

---

## Code Style

### Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `camelCase` | `computeHapticTorque()` |
| Variables | `camelCase` | `detentCount` |
| Constants | `UPPER_SNAKE` | `MAX_VOLTAGE` |
| Pin defines | `PIN_UPPER_SNAKE` | `PIN_MOTOR_ENABLE` |
| Classes | `PascalCase` | `HapticEngine` |

### Structure

- Keep `setup()` and `loop()` minimal — delegate to functions
- Group related functionality into separate `.h/.cpp` files
- Use `static` for file-local variables and functions
- Prefer `const` over `#define` for typed constants

### Comments

```cpp
// Single-line comments for brief explanations

/**
 * @brief Computes haptic detent torque based on angular position
 * @param angle Current motor angle in radians
 * @param detentCount Number of detent positions per revolution
 * @param detentStrength Peak torque at detent (Nm)
 * @return Torque value to apply
 */
float computeHapticTorque(float angle, int detentCount, float detentStrength);
```

---

## Hardware Safety

- **Never exceed voltage limits**: `motor.voltage_limit` must be set before `initFOC()`
- **Always set current limits** when using current sense
- **Test with low voltage first** (0.5V) before increasing
- **Emergency stop**: Set `motor.disable()` on error conditions

---

## Debugging

- Use `Serial.print()` / `Serial.println()` for debug output
- Use `_LSTR()` macro for SimpleFOC string literals
- Monitor with `pio device monitor` at 115200 baud
- Use SimpleFOC Commander for interactive parameter tuning

---

## File Organization (Target — Phase 1)

```
PoC/firmware/src/
├── main.cpp          # Setup/loop, top-level orchestration
├── config.h          # Pin definitions, constants, defaults
├── haptics.h/cpp     # Haptic mode computation functions
├── comms.h/cpp       # Serial protocol, Commander handlers
└── button.h/cpp      # Button input, press detection
```
