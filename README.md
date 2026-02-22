# SmartKnob STM32 — Haptic BLDC Controller for Windows

[![Platform](https://img.shields.io/badge/platform-STM32_Nucleo_L452RE-blue.svg)]()
[![SimpleFOC](https://img.shields.io/badge/library-SimpleFOC_v2.4.0-brightgreen.svg)]()
[![FOC](https://img.shields.io/badge/motor_control-FOC-orange.svg)]()
[![Windows](https://img.shields.io/badge/integration-Windows-0078D6.svg)]()
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()

A haptic knob controller using an **STM32 Nucleo L452RE**, **MT6701 magnetic encoder**, **SimpleFOCShield V3.2**, and the **SimpleFOC library** for BLDC motor FOC control. Features **four switchable haptic modes**: detented wheel, inertial flywheel, spring-centered, and bounded rotation with hard stops.

This project is a **proof of concept** for a smart knob that can dynamically adjust its haptic behavior and interact with PC applications. Current Windows integration includes **volume control**, **smooth scrolling**, **screen brightness**, and experimental **screen zoom**. The goal is to evolve this into more complex contextual controls.

> **Project Evolution:** This started as a learning platform for SimpleFOC on STM32 and advanced haptic feedback techniques (explaining the detailed hardware documentation). It has since evolved into a dual-purpose project: (1) a **PC control proof-of-concept** using open-source libraries to prototype commercial applications, and (2) a **learning resource** for the STM32 platform, FOC, control theory, and haptic feedback.

> **Why SSI instead of I2C?** The MT6701's I2C address is `0x06`, which falls in the I2C reserved address range (0x00–0x07). While ESP32/Arduino tolerate this, STM32 I2C peripherals strictly enforce the spec and refuse to communicate. SSI over hardware SPI is the reliable alternative, and ideally the use of a proper SPI peripheral would be recommended

### Acknowledgments

This project was inspired by [**Scott Bezek's SmartKnob**](https://github.com/scottbez1/smartknob) — an incredible open-source haptic input knob that sparked my interest in FOC motor control and haptic feedback. While this is not a fork (different MCU, different goals), Scott's work was the catalyst that got me into this field. Check out his project if you haven't already!

---

## Table of Contents

1. [Hardware Overview](#hardware-overview)
2. [Wiring Reference](#wiring-reference)
3. [PlatformIO Configuration](#platformio-configuration)
4. [SimpleFOC Haptics Implementation](#simplefoc-haptics-implementation)
   - [SimpleFOC Setup](#simplefoc-setup)
   - [Haptic Modes](#haptic-modes)
   - [Commander Interface](#commander-interface-serial-tuning)
   - [User Button (Mode Cycling)](#user-button-mode-cycling)
   - [SimpleFOC Core Concepts](#simplefoc-core-concepts)
   - [Motion Control Modes](#motion-control-modes)
   - [Monitoring & Debugging](#monitoring--debugging)
   - [Complete Source Code](#complete-source-code)
5. [PC Control Software (Windows)](#pc-control-software-windows)
6. [Troubleshooting & Gotchas](#troubleshooting--gotchas)
7. [Lessons Learned](#lessons-learned)
8. [Resources](#resources)

---

## Hardware Overview

| Component         | Detail                                                                                               |
| ----------------- | ---------------------------------------------------------------------------------------------------- |
| **MCU**           | STM32L452RET6 (Nucleo L452RE) — 80 MHz Cortex-M4, 160 KB RAM, 512 KB Flash                           |
| **Encoder**       | MT6701 magnetic encoder, 14-bit resolution (0.022° per count)                                        |
| **Interface**     | SSI over SPI1 @ 1 MHz, **SPI_MODE1**                                                                 |
| **Motor Driver**  | SimpleFOCShield V3.2 (3-PWM, ACS712 inline current sense)                                            |
| **Motor**         | BLDC with 7 pole pairs (14 magnets)                                                                  |
| **Current Sense** | ACS712-05B inline current sensors (185 mV/A) — NOT shunt resistors                                   |
| **Libraries**     | [SimpleFOC v2.4.0](https://github.com/simplefoc/Arduino-FOC) + [SimpleFOCDrivers v1.0.9](https://github.com/simplefoc/Arduino-FOC-drivers) |
| **Framework**     | Arduino (via PlatformIO + `ststm32` platform)                                                        |

---

## Wiring Reference

### MT6701 Encoder (SSI over SPI)

| Nucleo Pin | MT6701 Pin    | Function         | Notes                                                                |
| ---------- | ------------- | ---------------- | -------------------------------------------------------------------- |
| **PA5**    | Pin 2 (CLK)   | SPI1_SCK         | Also `LED_BUILTIN` — onboard LED is unavailable while SPI1 is in use |
| **PA6**    | Pin 3 (DO/Z)  | SPI1_MISO        | Data from sensor                                                     |
| **PB6**    | Pin 1 (CSN/A) | GPIO chip-select | Active LOW; directly driven by `MagneticSensorMT6701SSI` class       |
| PA7        | —             | SPI1_MOSI        | Leave unconnected (SSI is read-only, no MOSI needed)                 |

### SPI Configuration — Critical Details

| Parameter   | Value                       | Reason                                                                                               |
| ----------- | --------------------------- | ---------------------------------------------------------------------------------------------------- |
| Clock speed | 1 MHz                       | Conservative; MT6701 supports up to ~25 MHz                                                          |
| SPI Mode    | **MODE 1** (CPOL=0, CPHA=1) | CLK idles LOW; sensor shifts data on rising edge, master samples on falling edge (per MT6701 datasheet Figure 24) |
| Bit order   | MSB first                   | D13 (MSB of angle) is transmitted first                                                              |
| Frame size  | 24 bits (3 bytes)           | 14-bit angle + 4-bit magnetic field status + 6-bit CRC                                               |

> **Why SPI_MODE1 specifically?** This was discovered through exhaustive testing of all 4 SPI modes:
>
> - **MODE 0** (CPOL=0, CPHA=0): CLK idle matches, but the first rising edge both shifts AND samples — the MSB is lost. Angle reads only 180°–360°.
> - **MODE 1** (CPOL=0, CPHA=1): **Correct.** CLK idle LOW matches the sensor's idle state. First rising edge shifts data out, first falling edge samples it — no false edge, no lost bit. Full 0°–360° range.
> - **MODE 2** (CPOL=1, CPHA=0): CLK idles HIGH — creates a false falling edge on CS assertion. MSB is lost.
> - **MODE 3** (CPOL=1, CPHA=1): CLK idles HIGH — same false-edge problem.
>
> **Symptom of wrong mode:** Angle only reads 180°–360° (the lost MSB becomes a stuck `1`, halving the apparent range).

### BLDC Motor Driver (SimpleFOCShield V3.2 on Nucleo L452RE)

| Nucleo Pin | Arduino Pin | Shield Jumper           | Function    | Timer           |
| ---------- | ----------- | ----------------------- | ----------- | --------------- |
| **PB10**   | D6          | PWM_A = D6 (default)    | Phase A PWM | TIM2_CH3        |
| **PC7**    | D9          | PWM_B = **D9** (moved!) | Phase B PWM | TIM3_CH2        |
| **PB4**    | D5          | PWM_C = D5 (default)    | Phase C PWM | TIM3_CH1        |
| **PA9**    | D8          | EN = D8 (default)       | Enable      | GPIO (no timer) |

> **CRITICAL — PWM Timer Synchronization:** The SimpleFOCShield's default pin mapping (D6, D10, D5) assigns each PWM phase to a different timer. On Arduino/ESP32 this is fine, but **STM32 requires synchronized PWM timers** for proper FOC. With 3 separate timers, the phases cannot be synchronized, causing motor control issues. You **must** move the **PWM_B solder jumper from D10 to D9** (PC7). This puts phases B and C on TIM3, and phase A on TIM2 — only 2 timers total, which SimpleFOC can synchronize. This is the **only** jumper change needed; PWM_A=D6, PWM_C=D5, and EN=D8 stay at their default positions. (Note: D10 also conflicts with PB6 used by the sensor CS, but the timer issue is the primary reason for this change.)

> **Timer Grouping:** SimpleFOC works best when all PWM pins share as few timers as possible (synchronized PWM). This pin mapping uses only **TIM2 + TIM3** (2 timers total, score: 2). Verify during boot with `SimpleFOCDebug::enable(&Serial)` — the debug output will show which timer each pin is assigned to.

### Inline Current Sense (ACS712-05B)

| Nucleo Pin | Arduino Pin | Function              | Notes                |
| ---------- | ----------- | --------------------- | -------------------- |
| **PA0**    | A0          | Phase A current sense | ACS712 analog output |
| **PA4**    | A2          | Phase B current sense | ACS712 analog output |

> **ACS712 vs. Shunt Resistors:** SimpleFOCShield V3.2 uses **ACS712-05B** Hall-effect inline current sensor ICs (the small 8-pin SOIC chips on the board labeled "ACS712"). These are NOT shunt resistors — they use the `InlineCurrentSense` class (not `LowsideCurrentSense`), with the **mV/A** sensitivity value (185 mV/A for the -05B variant) as the first constructor argument.

---

## PlatformIO Configuration

```ini
[env:nucleo_l452re]
platform = ststm32
board = nucleo_l452re
framework = arduino
monitor_speed = 115200
build_flags = -Wl,-u,_printf_float
lib_deps = 
	askuric/Simple FOC@^2.4.0
	https://github.com/simplefoc/Arduino-FOC-drivers.git
lib_archive = false
```

| Setting                                                | Purpose                                          | Why It Matters                                                                                       |
| ------------------------------------------------------ | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| `build_flags = -Wl,-u,_printf_float`                   | Enable float support in `printf`/`Serial.printf` | STM32 newlib-nano strips float formatting by default. Without this flag, any `printf("%f", ...)` prints blank or corrupts the output buffer with garbage characters. |
| `askuric/Simple FOC@^2.4.0`                            | Install SimpleFOC from PlatformIO registry       | Standard PlatformIO dependency                                                                       |
| `https://github.com/simplefoc/Arduino-FOC-drivers.git` | Install SimpleFOCDrivers from GitHub             | **Must use full GitHub URL** — the PlatformIO registry name doesn't match what PlatformIO expects. Using a short name like `simplefoc/SimpleFOCDrivers` will fail to resolve. |
| `lib_archive = false`                                  | Disable library archiving                        | Required for SimpleFOC to compile correctly on some STM32 targets. Without it, linker errors may occur. |

> **File Extension:** SimpleFOC is a C++ library. Your main source file **must** be `main.cpp`, not `main.c`. If PlatformIO creates `main.c` by default, rename it or the build will fail with missing symbol errors.

---

## SimpleFOC Haptics Implementation

This section covers the complete SimpleFOC implementation for haptic feedback, including hardware setup, haptic modes, control interface, and debugging.

### SimpleFOC Setup

#### Sensor — MagneticSensorMT6701SSI

The **SimpleFOCDrivers** library provides a native `MagneticSensorMT6701SSI` class that handles all SSI protocol details (SPI mode, frame parsing, CRC). No manual SPI code or `GenericSensor` callbacks needed:

```cpp
#include <SimpleFOC.h>
#include "SimpleFOCDrivers.h"
#include "encoders/MT6701/MagneticSensorMT6701SSI.h"

MagneticSensorMT6701SSI sensor(PB6);  // CS pin only — uses default SPI1

void setup() {
  sensor.init();           // Initializes SPI and CS pin
  motor.linkSensor(&sensor);
}
```

The class internally configures SPI_MODE1, 1 MHz clock, MSB-first, and handles the 24-bit frame parsing (14-bit angle extraction).

### Standalone Sensor Testing (No Motor)

```cpp
void setup() {
  Serial.begin(115200);
  sensor.init();
}

void loop() {
  sensor.update();  // Must be called frequently!
  Serial.print(sensor.getAngle());       // cumulative angle (rad)
  Serial.print("\t");
  Serial.println(sensor.getVelocity());  // angular velocity (rad/s)
}
```

---

#### Motor & Driver Setup

```cpp
BLDCMotor motor = BLDCMotor(7);                          // 7 pole pairs
BLDCDriver3PWM driver = BLDCDriver3PWM(PB10, PC7, PB4, PA9);  // D6/D9/D5/D8

void setup() {
  sensor.init();
  motor.linkSensor(&sensor);

  driver.voltage_power_supply = 12;  // Match your PSU
  driver.init();
  motor.linkDriver(&driver);

  motor.controller = MotionControlType::torque;  // Voltage-based torque
  motor.voltage_limit = 8;           // Max voltage to motor (V)
  motor.voltage_sensor_align = 5;    // Alignment voltage (see current sense section)
  motor.velocity_limit = 20;         // rad/s safety limit

  motor.init();
  motor.initFOC();  // Aligns sensor — motor will jerk briefly
}
```

> **`pole_pairs`** — the number of magnetic pole *pairs*, not total poles. A motor with 14 magnets on the rotor has 7 pole pairs. Count the magnets and divide by 2.

> **Voltage Torque Mode & Current:** In voltage torque mode, SimpleFOC applies a voltage and the resulting current is governed purely by **Ohm's law** ($I = V / R_{phase}$). There is no active current measurement or limiting. The maximum current you see (~600 mA at 8V, for example) is determined by your motor's phase resistance, not a software limit. For true current limiting, switch to `dc_current` torque mode with the current sense feedback loop.

---

#### Inline Current Sense (ACS712)

```cpp
InlineCurrentSense current_sense = InlineCurrentSense(185.0f, PA0, PA4);

void setup() {
  // After driver.init(), before motor.init():
  current_sense.linkDriver(&driver);
  current_sense.init();
  motor.linkCurrentSense(&current_sense);
}
```

### Constructor Explained

`InlineCurrentSense(185.0f, PA0, PA4)` — the first argument is the **mV/A sensitivity** of the ACS712-05B (185 mV/A). This is the `InlineCurrentSense` overload for mV/A sensors, NOT the shunt-resistor overload (which takes resistance in Ohms).

Only two phase current pins are provided (A and B). SimpleFOC calculates the third phase current using Kirchhoff's current law ($I_A + I_B + I_C = 0$).

### Sensor Alignment Voltage

```cpp
motor.voltage_sensor_align = 5;  // Volts — default is ~1V
```

> **Why 5V?** During `initFOC()`, SimpleFOC applies a small voltage to each phase and measures the current response to determine sensor-to-motor alignment. The **ACS712 has lower sensitivity** than low-side shunt resistors, so the default ~1V alignment voltage produces current too small for the ACS712 to resolve reliably. This causes the error `CS: Err too low current, curr: 0.00`. Setting `voltage_sensor_align = 5` ensures enough current flows to exceed the ACS712's noise floor.

---

### Haptic Modes

The firmware implements **four switchable haptic feedback modes**, selectable via serial command (`H`/`I`/`W`/`C`) or cycling with the blue user button (PC13).

| Mode        | Command | Description                            |
| ----------- | ------- | -------------------------------------- |
| **Haptic**  | `H`     | Virtual detents, infinite rotation     |
| **Inertia** | `I`     | Virtual flywheel with momentum         |
| **Bounded** | `W`     | Detents with hard wall stops at ±60°   |
| **Spring**  | `C`     | Centered spring (snaps back to center) |

### Mode 1: Haptic Wheel (Detented)

Creates virtual detent positions using a **sine-based potential energy field**:

```
torque = -strength × sin(N × angle)
```

where $N = 360° / spacing$ is the number of detents per revolution.

The sine function creates periodic energy wells — the shaft naturally falls into the nearest detent. Between detents, the restoring torque increases sinusoidally, creating a satisfying "click" feel.

**Tunable Parameters:**

| Parameter       | Commander | Default | Effect                                                                    |
| --------------- | --------- | ------- | ------------------------------------------------------------------------- |
| Detent spacing  | `S<val>`  | 10°     | Degrees between clicks (e.g., `S30` for 12 positions/rev)                 |
| Detent strength | `D<val>`  | 2.0 V   | Snap force — higher = harder to push past (e.g., `D4` for strong detents) |

### Mode 2: Inertial Wheel (Flywheel)

Simulates a **heavy flywheel** attached to the knob via a virtual spring. Uses a **position-based spring-mass-damper** model — no velocity derivatives, no noise amplification, stable at any inertia value.

#### Physics Model

```
┌─────────┐    spring (K)    ┌───────────────┐
│  Real    │ ←─────────────→ │   Virtual     │
│  Shaft   │   pos_error     │   Flywheel    │
│ (sensor) │                 │ (simulated)   │
└─────────┘                  └───────────────┘
```

The virtual flywheel has position (`virt_pos`) and velocity (`virt_vel`). A spring of stiffness $K$ connects it to the real shaft:

$a_{virtual} = \frac{K \times (shaft_{pos} - virt_{pos}) - B \times virt_{vel}}{J}$

$torque_{motor} = -K \times (shaft_{pos} - virt_{pos})$

When you push the knob, the spring compresses (position error grows), which:

1. **Accelerates the virtual flywheel** — it starts spinning
2. **Resists your push** via the motor — you feel the inertia

When you let go, the flywheel's momentum pulls the shaft along through the spring, creating a coasting/spinning effect.

**Tunable Parameters:**

| Parameter              | Commander | Default | Effect                                                             |
| ---------------------- | --------- | ------- | ------------------------------------------------------------------ |
| Virtual inertia (J)    | `J<val>`  | 5.0     | Mass of flywheel (kg·m²) — higher = heavier, slower to accelerate  |
| Damping (B)            | `B<val>`  | 1.0     | Viscous drag (N·m·s) — 0 = coasts forever, higher = stops sooner   |
| Coulomb friction       | `F<val>`  | 0.2     | Constant deceleration (rad/s²) — simulates bearing friction        |
| Coupling stiffness (K) | `K<val>`  | 40.0    | Spring stiffness (V/rad) — higher = more direct/rigid connection   |
| Velocity LPF Tf        | `L<val>`  | 0.03    | Low-pass filter time constant for `motor.shaft_velocity` (seconds) |

#### Why Position-Based (Not Velocity Derivative)?

Earlier approaches tried to simulate inertia by opposing *acceleration* (computing the derivative of velocity). These all failed:

1. **Raw `sensor.getVelocity()`** bypasses SimpleFOC's internal velocity low-pass filter → extreme noise → high-pitched motor whine
2. **Using `motor.shaft_velocity`** (filtered) helped, but differentiating even a filtered velocity still amplifies noise
3. **Heavy LPF** to suppress the noise adds so much lag that the feedback loop becomes unstable at high inertia values → oscillation and vibration

The **spring-mass-damper** approach avoids ALL derivatives of sensor data. It only uses the shaft **position** (which is clean and direct from the 14-bit encoder). The virtual flywheel is integrated forward in time (integration smooths, differentiation amplifies noise), making it inherently stable at any inertia value.

> **Note:** The spring-mass approach is a workaround, not the ideal solution. The goal is to eventually implement direct flywheel simulation without the coupling spring, once a clean acceleration signal can be derived. For now, this method provides stable and satisfying inertial feedback.

### Mode 3: Spring Mode (Centered)

A simple torsional spring that always pulls the knob back to center (0°). Useful for rate-based controls like zoom, where displacement from center determines the rate of change.

$torque = -K_{spring} \times angle - B_{spring} \times velocity$

**Parameters (in firmware):**

| Parameter          | Default    | Description                             |
| ------------------ | ---------- | --------------------------------------- |
| `spring_center`    | 0.0 rad    | Center position                         |
| `spring_stiffness` | 10.0 V/rad | Spring constant                         |
| `spring_damping`   | 0.1        | Velocity damping (prevents oscillation) |

### Mode 4: Bounded Mode (Detents with Walls)

Combines haptic detents with **hard wall stops** at configurable angle limits. Ideal for bounded controls like volume (0-100%).

When the shaft reaches the boundary:

1. A strong spring force pushes it back
2. Damping prevents overshooting
3. The last stable detent is just before the wall, providing satisfying end-stop feedback

**Implementation detail:** The wall is placed slightly beyond the last detent position (e.g., wall at ±62° with stable detent at ±60°). The spring force targets a position *before* the wall to ensure strong restitution. This creates a "hit wall → slide back into detent" feel.

$torque_{wall} = -K_{wall} \times (angle - wall_{target}) - B_{wall} \times velocity$

**Parameters:**

| Parameter                                      | Commander      | Default    | Description                   |
| ---------------------------------------------- | -------------- | ---------- | ----------------------------- |
| Angle limits                                   | `N<min>,<max>` | ±60°       | Boundary positions            |
| Wall strength                                  | —              | 20.0 V/rad | Spring constant at walls      |
| Wall damping                                   | —              | 2.0        | Prevents oscillation at walls |
| (Also uses detent parameters from Haptic mode) |                |            |                               |

---

### Commander Interface (Serial Tuning)

All parameters are tunable at runtime via the serial Commander interface at 115200 baud:

### Custom Haptic Commands

| Command        | Description                              | Example             |
| -------------- | ---------------------------------------- | ------------------- |
| `H`            | Switch to Haptic Wheel mode              | `H`                 |
| `I`            | Switch to Inertial Wheel mode            | `I`                 |
| `W`            | Switch to Bounded mode (walls)           | `W`                 |
| `C`            | Switch to Spring mode (centered)         | `C`                 |
| `S<val>`       | Set detent count (2-360 detents per rev) | `S36` → 10° spacing |
| `D<val>`       | Set detent strength (volts)              | `D3`                |
| `B<val>`       | Set inertia damping                      | `B0.5`              |
| `F<val>`       | Set inertia friction                     | `F0.15`             |
| `J<val>`       | Set virtual inertia (heaviness)          | `J10`               |
| `K<val>`       | Set coupling stiffness                   | `K20`               |
| `L<val>`       | Set velocity LPF Tf (seconds)            | `L0.05`             |
| `N<min>,<max>` | Set angle limits (bounded mode)          | `N-60,60`           |
| `X`            | Stop motor (zero torque)                 | `X`                 |
| `Y`            | Start motor (resume haptics)             | `Y`                 |
| `Z<angle>`     | Seek to position (degrees)               | `Z45`               |
| `R`            | Reset position to 0°                     | `R`                 |
| `P`            | Query current position                   | `P` → `P45.2`       |
| `Q`            | Query full state (mode + params)         | `Q`                 |

### Built-in SimpleFOC Motor Commands (via `M`)

| Command               | Description                            |
| --------------------- | -------------------------------------- |
| `M`                   | Show motor status                      |
| `ME1` / `ME0`         | Enable / disable motor                 |
| `MC0` / `MC1` / `MC2` | Set mode: torque / velocity / angle    |
| `M<val>`              | Set target (units depend on mode)      |
| `MVP<val>`            | Set velocity PID P gain                |
| `MVI<val>`            | Set velocity PID I gain                |
| `MVD<val>`            | Set velocity PID D gain                |
| `MLU<val>`            | Set voltage limit                      |
| `MS<val>`             | Set monitor downsample (e.g., `MS100`) |
| `MD<val>`             | Set monitor decimals                   |
| `?`                   | List all registered commands           |

> **Tip:** Set Serial Monitor to **Newline** line ending and **115200** baud.

---

### User Button (Mode Cycling)

The Nucleo L452RE's **blue user button** (PC13, active LOW, external pull-up on board) cycles through all four haptic modes:

```cpp
#define USER_BTN PC13
// Press cycles: Haptic → Inertia → Bounded → Spring → Haptic...
```

- Press: cycles to next mode (200 ms debounce)
- When switching to Inertia mode, the virtual flywheel initializes at the current shaft position with zero velocity
- `pinMode(USER_BTN, INPUT)` — no `INPUT_PULLUP` needed, the Nucleo board has an external pull-up resistor on PC13

---

### SimpleFOC Core Concepts

### Library Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Sensor     │     │   Driver     │     │ Current Sense│
│  (position)  │     │   (PWM)      │     │  (optional)  │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────┬───────────┘────────────────────┘
                │
         ┌──────▼───────┐
         │  BLDCMotor   │
         │  (FOC loop)  │
         └──────┬───────┘
                │
         ┌──────▼───────┐
         │   Motion     │
         │  Controller  │
         └──────────────┘
```

### Initialization Order (Must Follow Exactly)

```
1. sensor.init()                    → Initialize sensor hardware (SPI)
2. motor.linkSensor(&sensor)        → Connect sensor to motor
3. driver.init()                    → Initialize PWM timers
4. motor.linkDriver(&driver)        → Connect driver to motor
5. current_sense.linkDriver(&driver)→ Link current sense to driver
6. current_sense.init()             → Initialize ADC for current sense
7. motor.linkCurrentSense(&cs)      → Connect current sense to motor
8. motor.init()                     → Initialize motor parameters
9. motor.initFOC()                  → Align sensor & calibrate (motor moves!)
```

### Real-Time Loop

```cpp
void loop() {
  motor.loopFOC();     // Inner FOC loop — must run at >1 kHz
  motor.move(voltage); // Outer control — sets voltage (in torque mode)
  motor.monitor();     // Optional: serial monitoring
  command.run();       // Process serial commands
}
```

---

### Motion Control Modes

| Mode                   | Enum                                   | Target Unit | Use Case                                |
| ---------------------- | -------------------------------------- | ----------- | --------------------------------------- |
| **Torque (voltage)**   | `MotionControlType::torque`            | Volts       | Direct force — used for haptic feedback |
| **Velocity**           | `MotionControlType::velocity`          | rad/s       | Speed regulation                        |
| **Angle**              | `MotionControlType::angle`             | rad         | Position hold (cascade PID)             |
| **Velocity open-loop** | `MotionControlType::velocity_openloop` | rad/s       | Testing without sensor                  |
| **Angle open-loop**    | `MotionControlType::angle_openloop`    | rad         | Testing without sensor                  |

This project uses **voltage torque mode** — the motor applies a voltage proportional to the computed haptic torque. No PID loop for the haptic modes; PID parameters are only relevant if switching to velocity or angle control via Commander.

---

### Monitoring & Debugging

### Debug Output

Enable **before** any `init()` call to see timer assignments, PWM config, sensor alignment results, and errors:

```cpp
SimpleFOCDebug::enable(&Serial);
```

### Real-Time Monitoring

```cpp
motor.useMonitoring(Serial);
motor.monitor_downsample = 0;  // Disabled by default (0 = no output)
```

Enable at runtime via Commander: `MD100` (set 100 decimal resolution), then `MS1` (print every loop). Use the Arduino Serial Plotter for live graphs.

> **Performance Warning:** Excessive serial output in the loop slows `loopFOC()` below the >1 kHz threshold. Keep `monitor_downsample` high (e.g., 100+) or disabled (0) during normal haptic operation.

---

### Complete Source Code

See [src/main.cpp](src/main.cpp) for the full annotated source. Backup files in `src/`:

- `main_FullControl.bak` — SimpleFOC full control example with Commander
- `main_AngleControl.bak` — Angle position control example
- `main_firstSSIWorking.bak` — First working SSI sensor readout (milestone)

---

## PC Control Software (Windows)

A Python GUI application in `tools/` connects the SmartKnob to Windows system functions.

### Quick Start

```bash
cd tools
pip install -r requirements.txt
python smartknob_simple.py
```

### Windows Integration Features

| Function              | Haptic Mode | Description                                                |
| --------------------- | ----------- | ---------------------------------------------------------- |
| **Volume Control**    | Bounded     | Knob position (±60°) maps directly to volume (0-100%)      |
| **Screen Brightness** | Bounded     | Knob position maps to display brightness                   |
| **Smooth Scroll**     | Inertia     | Rotation simulates smooth mouse wheel scrolling            |
| **Screen Zoom**       | Spring      | Displacement from center controls zoom rate (experimental) |

### Implementation Notes

- **Volume & Brightness**: Straightforward bounded-to-percentage mapping. Implemented in one iteration with no issues.
- **Smooth Scroll**: Uses smooth scrolling (not notched line-by-line) for a fluid experience in documents and code editors. Avoids sudden jumps regardless of rotation speed.
- **Zoom**: Experimental feature using the Windows Magnification API. Works but is somewhat finnicky; not a priority for further development.

### File Structure

| File                    | Purpose                                   |
| ----------------------- | ----------------------------------------- |
| `smartknob_simple.py`   | Main GUI application                      |
| `windows_link.py`       | Links motor position to Windows functions |
| `volume_control.py`     | Windows Core Audio API wrapper (pycaw)    |
| `brightness_control.py` | Display brightness via WMI                |
| `scroll_control.py`     | Mouse wheel simulation (smooth scrolling) |
| `zoom_control.py`       | Screen magnification API                  |
| `requirements.txt`      | Python dependencies                       |

### Dependencies

```
pyserial      # Serial communication
pycaw         # Windows audio control
comtypes      # Required by pycaw
wmi           # Brightness control
```

---

## Troubleshooting & Gotchas

| Symptom                                    | Cause                                                                | Fix                                                                                                  |
| ------------------------------------------ | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Angle only reads 180°–360°**             | Wrong SPI mode — MSB (D13) is lost and read as `1`                   | Must use **SPI_MODE1** (CPOL=0, CPHA=1). MODE 0/2/3 all lose the MSB.                                |
| **`printf` prints blank instead of float** | STM32 newlib-nano strips float from printf/sprintf                   | Add `-Wl,-u,_printf_float` to `build_flags` in platformio.ini                                        |
| **Garbage characters on Serial**           | Printf failure from missing float support corrupts the output buffer | Same fix as above                                                                                    |
| **`CS: Err too low current, curr: 0.00`**  | ACS712 alignment current too low to detect                           | Set `motor.voltage_sensor_align = 5;` (default ~1V is too weak for ACS712)                           |
| **SimpleFOCDrivers library not found**     | PlatformIO registry name mismatch                                    | Use full GitHub URL: `https://github.com/simplefoc/Arduino-FOC-drivers.git`                          |
| **Linker errors / undefined references**   | Source file is `.c` instead of `.cpp`                                | Rename `main.c` → `main.cpp` (SimpleFOC is C++)                                                      |
| **D10 conflict / SPI stops working**       | Shield PWM_B default D10 = PB6 = sensor CS                           | Move PWM_B solder jumper from D10 to D9                                                              |
| **PWM timer error (>2 timers)**            | PWM pins spread across too many timers                               | Use D6/D9/D5 mapping (TIM2+TIM3 only)                                                                |
| **Motor vibrates but doesn't spin**        | Wrong pole pair count, PID gains too high, or sensor wrong direction | Verify `pole_pairs`; reduce PID gains; try `motor.sensor_direction = Direction::CCW;`                |
| **`initFOC()` fails / no alignment**       | Voltage too low, loose wiring, or wrong pole pairs                   | Check connections, increase `motor.voltage_limit`, verify motor wires                                |
| **Sensor reads 0x0000 or 0x3FFF**          | MT6701 not configured for SSI output                                 | Program MT6701 output mode to SSI via the MT6701 configuration tool (ESP32/Arduino) first            |
| **Inertia mode vibrates/whines**           | Using velocity derivatives for inertia (noise amplification)         | Use the position-based spring-mass-damper approach (see [Haptic Modes](#haptic-modes))               |
| **`loopFOC()` running slow (<1 kHz)**      | Too much Serial output in the loop                                   | Set `motor.monitor_downsample = 0` or a high value (100+)                                            |
| **Current limited to ~600 mA**             | Not a bug — voltage torque mode: $I = V / R_{phase}$                 | This is Ohm's law, not a software limit. For higher current, increase voltage_limit or use `dc_current` torque mode. |

---

## Lessons Learned

A collection of non-obvious gotchas discovered during development:

### 1. MT6701 I2C Address (0x06) Doesn't Work on STM32

The address falls in the I2C reserved range. ESP32/Arduino's Wire library is lenient and communicates anyway; STM32's HAL I2C driver rejects it. Use SSI (over SPI) instead.

### 2. SPI Mode Must Be MODE 1 — Not MODE 0

Most SPI sensor examples use MODE 0. The MT6701 SSI interface specifically requires **MODE 1** (CPOL=0, CPHA=1). Using any other mode loses the MSB, and the symptom (180°–360° only range) is subtle enough to look like a wiring issue rather than a timing issue.

### 3. Printf Float Requires a Linker Flag on STM32

The STM32 Arduino core uses newlib-nano, which strips float support from `printf`/`sprintf` to save flash. The fix (`-Wl,-u,_printf_float`) must go in `build_flags`, not in code. This also affects `Serial.printf()` and `sprintf()`.

### 4. SimpleFOCDrivers Must Be Installed from GitHub

The PlatformIO library registry naming doesn't match what the build system expects. Using a short name fails silently or with confusing errors. Always use the full GitHub URL in `lib_deps`.

### 5. SimpleFOCShield D10 = PB6 on Nucleo L452RE

The Arduino pin mapping on the Nucleo L452RE maps D10 to PB6. If you use PB6 for anything else (like the sensor CS), the shield's default PWM_B (D10) will conflict. One solder jumper change (D10→D9) fixes it.

### 6. ACS712 Needs Higher Alignment Voltage

The default `voltage_sensor_align` (~1V) doesn't generate enough current to register on the ACS712 (which has 185 mV/A sensitivity, output centered at Vcc/2). Setting it to 5V ensures reliable alignment. The error message `CS: Err too low current` means exactly what it says.

### 7. Velocity Derivatives Don't Work for Inertia Simulation

Differentiating angular velocity to get acceleration amplifies sensor noise catastrophically. Even with heavy low-pass filtering, the lag introduced makes the system oscillate at high virtual inertia values. The position-based spring-mass-damper approach works because it only uses **position** (clean) and **integration** (smoothing), never differentiation (noise-amplifying).

### 8. `sensor.getVelocity()` Bypasses SimpleFOC's Internal LPF

If you call `sensor.getVelocity()` directly, you get the raw (unfiltered) velocity. For filtered velocity, use `motor.shaft_velocity`, which has been through `motor.LPF_velocity.Tf`. This matters for any code that uses velocity outside of SimpleFOC's built-in control loops.

### 9. Voltage Torque Mode Current is Ohm's Law

In voltage torque mode, SimpleFOC doesn't measure or regulate current — it just applies a PWM duty cycle. The resulting current is $I = V / R_{phase}$. If you want true current control, switch to `dc_current` or `foc_current` torque mode with current sense feedback.

### 10. `lib_archive = false` Is Required

On some STM32 targets, SimpleFOC fails to link if `lib_archive` is not set to `false` in platformio.ini. This is a PlatformIO build system quirk with how SimpleFOC's weak symbols and platform-specific code is structured.

### 11. Use `motor.shaft_angle`, Not `sensor.getAngle()`

When implementing haptic modes, always use `motor.shaft_angle` for position calculations, not `sensor.getAngle()` directly. The sensor value can have opposite sign or different zero reference than what SimpleFOC's internal control loop uses. This mismatch causes confusing issues where haptics feel "inverted" or "fighting" depending on rotation direction.

### 12. Bounded Mode: Place Walls Beyond Last Detent

For satisfying bounded-mode feedback, place the hard wall slightly *after* the last desired stable position. For example, with a ±60° range:

- Set the wall collision point at ±62°
- Keep the last stable detent at ±60°
- Have the wall spring force target ±50° (not the wall itself)

This creates a "hit wall → slide back into detent" feel. The strong spring force targeting a point well before the wall, combined with damping, ensures the knob quickly settles into the last valid detent without bouncing or overshooting.

### 13. Smooth Scrolling vs. Notched Scrolling

For mouse wheel simulation, use smooth scrolling (fractional scroll units) rather than notched line-by-line scrolling. Smooth scrolling provides fluid document/code navigation that scales naturally with rotation speed, avoiding the jerky feel of discrete scroll steps.

---

## Resources

- **SimpleFOC Documentation:** [docs.simplefoc.com](https://docs.simplefoc.com/)
- **SimpleFOC Getting Started:** [docs.simplefoc.com/example_from_scratch](https://docs.simplefoc.com/example_from_scratch)
- **SimpleFOCDrivers (MT6701 support):** [github.com/simplefoc/Arduino-FOC-drivers](https://github.com/simplefoc/Arduino-FOC-drivers)
- **SimpleFOCStudio (GUI tuner):** [docs.simplefoc.com/studio](https://docs.simplefoc.com/studio)
- **Commander Interface:** [docs.simplefoc.com/commander_interface](https://docs.simplefoc.com/commander_interface)
- **Motion Control Modes:** [docs.simplefoc.com/motion_control](https://docs.simplefoc.com/motion_control)
- **Community Forum:** [community.simplefoc.com](https://community.simplefoc.com/)
- **MT6701 Datasheet:** Search for "MT6701 MagnTek datasheet"
- **GitHub (SimpleFOC):** [github.com/simplefoc/Arduino-FOC](https://github.com/simplefoc/Arduino-FOC)

---

## License

This project is proprietary software. **All rights reserved.**

- You may view this code for personal, educational reference
- Commercial use, modification, and redistribution are **prohibited** without written permission
- See [LICENSE](LICENSE) for full terms

*Copyright (c) 2025 Camilo Valencia*