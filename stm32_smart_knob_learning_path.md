# STM32 Smart Knob — Learning Path

> **Stack:** Nucleo-64 L452RE · PlatformIO (Arduino framework / STM32Duino) · SimpleFOC · MT6701 encoder · SimpleFOC Shield  
> **Motor:** Mitoot 2804 100KV gimbal BLDC  
> **Goal:** Progress from zero STM32 experience to advanced developer by building a fully functional haptic smart knob with USB HID computer interface.  
> **Background assumption:** Mechatronics engineering background — fundamentals of microcontrollers, control systems, and signal processing are assumed. Focus is on STM32-specific knowledge and the FOC/haptic application layer.

---

## Key Hardware Notes (read before starting)

- **PlatformIO board ID:** `nucleo_l452re` | Framework: `arduino` (STM32Duino core) | MCU: `stm32l452ret6` @ 80 MHz
- **USB:** The STM32L452RE has a built-in USB 2.0 full-speed peripheral — no external crystal required. This enables USB HID natively.
- **SimpleFOC + Nucleo PWM quirk:** On Nucleo-64 boards, pins 11 and 6 **cannot both** generate PWM simultaneously. When using the SimpleFOC Shield with a Nucleo, **avoid pin 11 — use pin 13 instead** for PWM phase C.
- **Logic levels:** The L452RE is 3.3V logic. Verify that all peripherals and shield interfaces are compatible or correctly configured for 3.3V.
- **I2C pull-ups:** STM32 Nucleo boards commonly have issues with I2C sensors without external pull-ups. The SimpleFOC Shield has solder-pad-selectable pull-ups (4.7 kΩ) — enable these for the MT6701.
- **HAL strategy:** Use HAL through Phases 1–3. Drop into registers only when performance or debugging demands it from Phase 4 onwards.

### Motor — Mitoot 2804 100KV

| Parameter | Value |
|-----------|-------|
| Configuration | 12N14P → **7 pole pairs** |
| Phase resistance | 11.2 Ω |
| Test voltage / max voltage | 11.1V (3S) / 14.8V (4S) |
| Max current | 5A |
| Max speed | 2180 RPM |
| Stator | Ø28mm × 4mm |
| Weight | 41.5g |

> ⚠️ Note: specs are from the Aliexpress seller — treat as a starting reference and verify against measurements during M9 (motor parameter identification). The 11.2Ω phase resistance is notably high for a BLDC — this makes the motor forgiving to drive but reduces efficiency at higher currents. The 7 pole pair count should be physically verified by counting rotor magnets before first closed-loop run.

### SimpleFOC Shield v3.2

- Gate driver upgraded from L6234 to **DRV8313** — better overcurrent protection, fault and reset pins now exposed on headers. Consider wiring the fault pin to the Nucleo for software-readable fault detection (useful from M4 onwards).
- Current sensing via **ACS712** Hall-effect sensors (±5A range — matches motor max current spec). ACS712 sensitivity is 185mV/A at rated supply voltage.
- ⚠️ **Verify current sensing supply voltage configuration before using current control mode.** The ACS712 is rated for a specific supply voltage and its output scaling depends on it — incorrect supply voltage will give wrong current readings. Check the board configuration against the v3.2 schematic before relying on current feedback in M8.

---

## Glossary of Key Terms and Abbreviations

| Term | Full name / meaning |
|------|-------------------|
| FOC | Field-Oriented Control — transforms 3-phase motor control into 2-axis d/q frame, enabling independent control of flux and torque |
| d/q frame | Direct/Quadrature rotating reference frame — a coordinate system locked to the rotor's magnetic field. d-axis is aligned with rotor flux; q-axis is 90° ahead and is the torque-producing axis |
| SPMSM | Surface Permanent Magnet Synchronous Motor — rotor magnets mounted on the surface; low saliency (Ld ≈ Lq) |
| IPMSM | Interior Permanent Magnet Synchronous Motor — rotor magnets embedded inside the rotor; high saliency (Ld ≠ Lq), better for HFI sensorless |
| BLDC | Brushless DC Motor — often used interchangeably with PMSM in the context of FOC-controlled motors |
| Rs | Stator phase resistance (Ω) |
| Ld | d-axis inductance (H) |
| Lq | q-axis inductance (H) |
| L | Phase inductance (H) — used when Ld ≈ Lq (SPMSM case) |
| Ke | Back-EMF constant — referred to **electrical** speed: Ke = λm (numerically identical). Referred to **mechanical** speed: Ke_m = p·λm. Convention varies between tools — always check which speed reference is used |
| λm | Permanent magnet flux linkage (Wb) — the fundamental physical quantity. Appears directly in d/q voltage equations. Numerically equal to Ke when referred to electrical speed |
| KV | Motor velocity constant (RPM/V) — relates to flux linkage by: KV = 60/(2π·p·λm) |
| id | d-axis current (A) — controls flux; set to 0 for maximum efficiency in SPMSM |
| iq | q-axis current (A) — controls torque; Te ∝ iq |
| Te | Electromagnetic torque (N·m) |
| TL | Load torque (N·m) |
| J | Moment of inertia of rotor + load (kg·m²) |
| B | Viscous friction coefficient (N·m·s/rad) |
| p | Number of pole pairs |
| ωe | Electrical angular velocity (rad/s) = p × ωm |
| ωm | Mechanical angular velocity (rad/s) |
| α | Angular acceleration (rad/s²) |
| IMC | Internal Model Control — controller design method that inverts the plant model and uses a single tuning parameter τ (desired closed-loop time constant) to analytically derive all controller gains |
| τ | In IMC context: desired closed-loop time constant (s). Smaller τ = faster response = more aggressive |
| PI / PID | Proportional-Integral / Proportional-Integral-Derivative controller |
| SMO | Sliding Mode Observer — a nonlinear state observer used for sensorless back-EMF estimation |
| MRAS | Model Reference Adaptive System — sensorless estimation technique using a reference model and adaptive mechanism |
| EKF | Extended Kalman Filter — optimal state estimator for nonlinear systems |
| HFI | High Frequency Injection — sensorless technique that exploits d/q inductance asymmetry (saliency) for zero-speed position estimation |
| SOGI | Second-Order Generalised Integrator — used in flux observers to avoid DC bias in integration |
| PLL | Phase-Locked Loop — used in sensorless FOC to extract rotor angle and speed from estimated back-EMF vector |
| ARR | Auto-Reload Register — STM32 timer register that sets the PWM period |
| HAL | Hardware Abstraction Layer — ST's middleware API for peripheral configuration |
| LL | Low Layer — ST's thin register-wrapper API, one level above bare metal |
| DMA | Direct Memory Access — peripheral that transfers data without CPU involvement |
| SWD | Serial Wire Debug — 2-pin debug interface used to flash and debug STM32 |
| HID | Human Interface Device — USB device class for keyboards, mice, game controllers, etc. |
| ACS712 | Hall-effect based inline current sensor IC used on SimpleFOC Shield v3.x |
| DRV8313 | Texas Instruments 3-phase gate driver IC used on SimpleFOC Shield v3.x |

---

## Resource Library

A curated reference library organised by topic. Pick from these as needed — they are not sequential reading but a collection to dip into at the relevant phase.

---

### 🔧 STM32 & PlatformIO

| Resource | Type | Notes |
|----------|------|-------|
| [STM32L452RE Reference Manual (RM0394)](https://www.st.com/resource/en/reference_manual/rm0394-stm32l41xxx42xxx43xxx44xxx45xxx46xxx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf) | Official docs | The ground truth for timers, I2C, USB, DMA, ADC on your specific MCU. Dense but authoritative — use it to look up specific registers when needed |
| [STM32L452RE Datasheet](https://www.st.com/resource/en/datasheet/stm32l452re.pdf) | Official docs | Pin alternate function table lives here — essential for M2 |
| [STM32Duino GitHub & Wiki](https://github.com/stm32duino/Arduino_Core_STM32) | Documentation | The Arduino core you're actually running. Wiki covers HardwareTimer API, USB, and known board quirks |
| [PlatformIO STM32 Platform Docs](https://docs.platformio.org/en/latest/platforms/ststm32.html) | Official docs | PlatformIO-specific config for STM32 — build flags, framework options, debug setup |
| [STM32CubeMX](https://www.st.com/en/development-tools/stm32cubemx.html) | Tool | Use as visual reference only (not for code generation). Indispensable for pin conflict resolution and clock tree visualisation |
| *Mastering STM32* — Carmine Noviello | Book | The most comprehensive English-language STM32 book. Covers HAL, timers, I2C, USB, DMA in depth. Freely available as a PDF from the author's site |
| [STMicroelectronics YouTube channel](https://www.youtube.com/@STMicroelectronics) | Video | Official tutorials on STM32 peripherals, CubeMX, and motor control from ST engineers |

---

### ⚡ SimpleFOC

| Resource | Type | Notes |
|----------|------|-------|
| [SimpleFOC Documentation](https://docs.simplefoc.com) | Official docs | Primary reference for the library — sensor integration, driver config, control modes, current sensing |
| [SimpleFOC Community Forum](https://community.simplefoc.com) | Community | Active forum with 1500+ members. Excellent for Nucleo-specific issues and shield wiring questions |
| [SimpleFOC GitHub](https://github.com/simplefoc/Arduino-FOC) | Source code | Worth reading the source for understanding what the library actually does under the hood — especially `BLDCMotor.cpp` |
| [SimpleFOC Discord](https://discord.gg/simplefoc) | Community | Faster responses than the forum for quick questions |
| [MT6701 + SimpleFOC community thread](https://community.simplefoc.com/t/mt6701-magnetic-position-encoder-support/2618) | Forum thread | Specifically documents MT6701 I2C support — directly relevant to M6 |

---

### 🎛️ FOC Theory & BLDC Motor Control

| Resource | Type | Notes |
|----------|------|-------|
| *Permanent Magnet Synchronous and Brushless DC Motor Drives* — R. Krishnan | Textbook | The most complete academic reference on PMSM/BLDC drives. Covers d/q modelling, FOC, current control, parameter identification, and sensorless control rigorously. Directly relevant to Phases 3–7 |
| *Electric Motor Drives: Modeling, Analysis, and Control* — R. Krishnan | Textbook | Broader drives textbook, good for grounding the control theory in M8/M9 |
| [Texas Instruments — "Field Oriented Control of 3-Phase AC-Motors" (Literature No. BPRA073)](https://www.ti.com/lit/an/bpra073/bpra073.pdf) | Application note | Clear, practical derivation of the Clarke and Park transforms and the full FOC algorithm. Free and well-written |
| [Microchip — "AN1078: Sensorless Field Oriented Control of a PMSM"](https://www.microchip.com/en-us/application-notes/an1078) | Application note | Concise sensorless FOC overview — covers SMO and startup strategy, relevant to Phase 7 |
| [ST Motor Control — X-CUBE-MCSDK](https://www.st.com/en/embedded-software/x-cube-mcsdk.html) | ST software | ST's own motor control SDK. Use as a reference implementation for FOC algorithms and SMO observer — source is readable. Not used directly in this project |
| [George Gillard — "An Introduction to Brushless DC Motor Control"](https://www.georgegillard.com/resources/documents) | Tutorial paper | Accessible introduction to FOC, Clarke/Park transforms, and PWM generation for BLDC motors. Good bridge between theory and implementation |

---

### 🎯 Reference Projects

| Resource | Type | Notes |
|----------|------|-------|
| [scottbez1/smartknob](https://github.com/scottbez1/smartknob) | GitHub project | The original open-source haptic smart knob. ESP32-based with a different hardware stack, but the haptic effect design, torque law implementations, and architectural decisions are directly relevant to Phases 4–5. Read the firmware, not just the README |
| [VESC Project](https://vesc-project.com) | Open source tool | The most mature open-source FOC motor controller. Excellent reference for motor parameter identification (M9) and sensorless algorithms (Phase 7). The VESC firmware source is readable C |
| [ODrive Robotics](https://odriverobotics.com) | Open source tool | Another high-quality open-source FOC controller with good documentation on motor commissioning and calibration procedures |

---

### 🖥️ USB HID

| Resource | Type | Notes |
|----------|------|-------|
| [USB HID Specification (usb.org)](https://www.usb.org/hid) | Official spec | The authoritative reference for report descriptors, usage pages, and HID protocol. Dense — use it as a lookup reference, not sequential reading |
| [USB HID Descriptor Tool](https://www.usb.org/document-library/hid-descriptor-tool) | Tool | Essential for validating your report descriptor before flashing — catches syntax errors that would silently prevent enumeration |
| [Frank Zhao — USB HID Report Descriptor Tutorial](https://eleccelerator.com/tutorial-about-usb-hid-report-descriptors/) | Tutorial | The best practical introduction to writing HID report descriptors. Clear examples and annotated walkthroughs |
| [hidapi](https://github.com/libusb/hidapi) | Library | Cross-platform C library for HID communication. The Python `hid` package wraps this — reading the C docs gives you the full picture |
| [Python `hid` package](https://pypi.org/project/hid/) | Library | Python bindings for hidapi used in M14 host application |

---

### 📡 Sensorless FOC (Phase 7)

| Resource | Type | Notes |
|----------|------|-------|
| [Morimoto et al. — "Sensorless Control Strategy for Salient-Pole PMSM Based on Extended EMF in Rotating Reference Frame"](https://ieeexplore.ieee.org/document/912918) | Academic paper | Foundational paper on back-EMF based sensorless FOC — referenced in most subsequent implementations |
| [Boldea & Nasar — "Electric Machine Dynamics"](https://www.routledge.com/Electric-Machine-Dynamics/Boldea-Nasar/p/book/9780023113109) | Textbook | Theoretical foundation for flux observer design and state estimation in electric machines |
| [ST Application Note AN5397 — "Current Sensing in Motion Control Applications"](https://www.st.com/resource/en/application_note/an5397-current-sensing-in-motion-control-applications-stmicroelectronics.pdf) | Application note | Practical guide to current sensing circuits and ADC configuration — relevant to M8 current sensing and Phase 7 observer inputs |
| [VESC Firmware Source — Observer implementation](https://github.com/vedderb/bldc) | Source code | Read `mcpwm_foc.c` — contains a real, production-quality SMO and flux observer implementation to compare against your own |

---

### 🌐 Communities

| Resource | Notes |
|----------|-------|
| [SimpleFOC Community](https://community.simplefoc.com) | Best forum for Phases 2–5 questions |
| [SimpleFOC Discord](https://discord.gg/simplefoc) | Real-time help, active |
| [r/embedded](https://reddit.com/r/embedded) | General embedded systems discussion — good for STM32 and architecture questions |
| [r/robotics](https://reddit.com/r/robotics) | Broader context for motor control and haptics projects |
| [EEVblog Forum](https://www.eevblog.com/forum/) | Strong community for electronics debugging, measurement, and hardware questions |
| [ST Community Forum](https://community.st.com) | Official ST support forum — useful for L452RE-specific peripheral bugs and errata |

---

> **Objective:** Get comfortable with the PlatformIO + STM32Duino environment and understand how STM32 peripherals differ from Arduino/ESP32, particularly timers and PWM.

---

### 📝 Phase 1 Notes

#### Framework choice: Arduino vs HAL vs bare metal

On STM32, PlatformIO supports multiple frameworks targeting the same hardware — analogous to Arduino vs ESP-IDF on ESP32:

| Framework | Entry point | Abstraction level | SimpleFOC compatible |
|-----------|-------------|-------------------|----------------------|
| **Arduino (STM32Duino)** | `setup()` / `loop()` | High — wraps HAL in familiar Arduino API | ✅ Yes — required |
| **STM32 HAL** | `main.c` | Medium — ST's own peripheral abstraction | ❌ No |
| **STM32 LL (Low Layer)** | `main.c` | Low — thin register wrappers | ❌ No |
| **Bare metal / CMSIS** | `main.c` | None — direct register access | ❌ No |

**For this project:** Use the Arduino framework throughout Phases 1–5. SimpleFOC is written against it and the productivity gain is real. From Phase 6–7 onwards (performance audit, sensorless observers) dropping to HAL or LL becomes natural since you'll no longer be tied to SimpleFOC and will be writing low-level code anyway. The same logic applies as moving from Arduino to ESP-IDF — it's not that Arduino is wrong, it's that at some point the abstraction stops serving you.

#### STM32CubeMX — use as a visual reference, not a code generator

CubeMX generates HAL initialisation code designed for STM32CubeIDE projects. This output does **not** integrate cleanly into a PlatformIO + Arduino framework project — mixing the two creates build system conflicts and is not recommended.

However, CubeMX is an excellent **interactive reference tool**:
- Its **pin conflict resolver** visually shows which peripherals can be assigned to which pins and flags conflicts immediately
- Its **clock tree configurator** lets you verify your timer input clock frequency before calculating prescalers
- Its **register preview** shows what a given configuration actually writes to hardware — useful for cross-referencing with the reference manual

**Recommended workflow:** Open CubeMX, load the STM32L452RE, configure peripherals visually to understand pin assignments and clock relationships — then implement the same configuration in PlatformIO using the STM32Duino `HardwareTimer` API. Use CubeMX as an interactive datasheet, not a code source.

---

### Milestone 1 — First working PlatformIO project on the L452RE

Get the toolchain fully set up: PlatformIO extension in VSCode, correct `platformio.ini` for the L452RE, LED blink, and `Serial` output over USB. Understand the project structure, how ST-Link flashing works, and how to use the PlatformIO debugger (not just serial printing).

**Checklist:**
- [ ] Install VSCode + PlatformIO extension
- [ ] Create new PlatformIO project: board `nucleo_l452re`, framework `arduino`
- [ ] Understand `platformio.ini` — board, framework, upload protocol, monitor speed
- [ ] Verify ST-Link is recognised by PlatformIO (no driver issues on your OS)
- [ ] Build and flash the default blink example — onboard LED (PB13 on L452RE) blinks
- [ ] Get `Serial.begin()` + `Serial.println()` working over USB UART (ST-Link virtual COM port)
- [ ] Open PlatformIO serial monitor and confirm output
- [ ] Set a breakpoint in the debugger and confirm it halts — verify the debug probe works, not just flashing
- [ ] Understand the difference between `upload_protocol = stlink` (flash) and the debug session
- [ ] Identify where compiled output lives (`.pio/build/`) and understand the memory map output (flash used, RAM used)

---

### Milestone 2 — GPIO and the STM32 timer/PWM system

Understand the STM32 timer architecture: prescalers, ARR, timer channels, and the difference between general-purpose and advanced timers. Manually configure PWM output using the STM32Duino `HardwareTimer` API. Understand center-aligned PWM mode (critical for FOC). Know how to determine which pins support PWM and which timer they belong to on the L452RE. Use CubeMX as a visual reference for pin/timer assignments — do not use its generated code.

**Checklist:**
- [ ] Open the L452RE in CubeMX — assign TIM1 and TIM2 visually, observe pin options and conflicts (no code generation)
- [ ] Read the L452RE datasheet alternate function table — understand how pins map to timer channels (AF1–AF14)
- [ ] Identify which pins support PWM and which specific timer/channel each belongs to
- [ ] Configure a PWM output manually using `HardwareTimer` (STM32Duino API) — not `analogWrite()`
- [ ] Set PWM frequency explicitly (target: 20–25 kHz, above audible range — relevant for FOC)
- [ ] Set and vary duty cycle in code, verify with oscilloscope or logic analyser
- [ ] Configure center-aligned (up-down) PWM mode — understand why FOC uses this instead of edge-aligned
- [ ] Configure complementary PWM output with dead-time insertion on an advanced timer (TIM1 or TIM8) — this is what the gate driver needs
- [ ] Confirm that pin 11 and pin 13 cannot share a timer simultaneously — document the conflict for M4
- [ ] Read an external PWM signal using input capture mode on a timer channel
- [ ] Calculate PWM frequency manually from system clock (80 MHz), prescaler, and ARR — verify the result matches what you see on the scope

---

### Milestone 3 — I2C communication

Scan the I2C bus, read and write registers from a peripheral. Understand clock speed configuration, pull-up requirements on STM32, and how to navigate a datasheet register map. This milestone directly prepares for MT6701 integration in M6.

**Checklist:**
- [ ] Identify I2C peripheral instances on the L452RE (I2C1, I2C2, I2C3) and their default pin mappings — use CubeMX to visualise
- [ ] Understand pull-up requirements — STM32 I2C is open-drain; external pull-ups required (do not rely on weak internal pull-ups for real use)
- [ ] Write an I2C bus scanner — iterate all 128 addresses and report which respond
- [ ] Connect any I2C peripheral you have available and confirm it appears at the correct address
- [ ] Read a multi-byte register using `Wire.beginTransmission()` / `Wire.requestFrom()`
- [ ] Write to a register and confirm the effect
- [ ] Test at both 100 kHz (standard) and 400 kHz (fast mode) — confirm reliable communication at 400 kHz (MT6701 supports this)
- [ ] Understand and handle `Wire` return codes — detect missing pull-ups, wrong address, clock stretching timeout
- [ ] Confirm I2C works on the pins exposed by the SimpleFOC Shield headers, or plan wire routing if they conflict

---

## Phase 2 — SimpleFOC Open-Loop (No Encoder)

> **Objective:** Validate the full hardware stack — Nucleo, SimpleFOC Shield, and motor — before adding sensor complexity.

---

### Milestone 4 — SimpleFOC Shield wiring and library initialisation

Wire the SimpleFOC Shield to the Nucleo respecting the Nucleo-specific PWM pin constraints (use pin 13, not 11). Install SimpleFOC via PlatformIO library manager. Configure `BLDCDriver3PWM` with correct pin assignments for the L452RE. Confirm the library initialises without errors and the motor does not produce fault conditions or angry noises at rest.

**Checklist:**
- [ ] Install SimpleFOC via PlatformIO library manager — add `simple-foc` to `lib_deps` in `platformio.ini`
- [ ] Stack the SimpleFOC Shield onto the Nucleo-64 — verify mechanical fit and that all headers seat correctly
- [ ] Confirm power supply: the shield accepts 12–24V on its power input; the Nucleo is powered separately via USB. Do **not** power the motor from the Nucleo 5V rail
- [ ] Identify the three PWM phase pins used by the shield on the Nucleo headers — use the shield schematic to find the Arduino pin numbers it expects
- [ ] Cross-reference those Arduino pin numbers against the L452RE pin map — confirm no timer conflicts (recall: pin 11 conflict from M2)
- [ ] Remap phase C from pin 11 to pin 13 in code using `BLDCDriver3PWM driver(6, 5, 13)` or equivalent valid assignment
- [ ] Identify and configure the enable pin if your shield version has one
- [ ] Configure logic level: set the SimpleFOC driver voltage limit to match 3.3V ADC range for current sensing
- [ ] Write minimal initialisation sketch: construct `BLDCDriver3PWM`, call `driver.init()`, check return value
- [ ] Confirm no fault condition on the shield's fault/enable pin at rest (probe with multimeter or logic analyser)
- [ ] Confirm motor phases are not getting warm at rest with driver initialised — rules out shoot-through from a misconfigured dead-time

---

### Milestone 5 — Open-loop velocity spin

Run the Mitoot 2804 in open-loop velocity mode. Tune the voltage limit to a safe value for this low-resistance gimbal motor. Experiment with different velocity targets and observe the relationship between voltage limit, target velocity, smoothness, and motor heating. Validate the full hardware chain is functional before adding the encoder.

**Checklist:**
- [ ] Construct a `BLDCMotor` object with the correct pole pair count for the 2804 — the 2804 100KV is typically **7 pole pairs** (14 poles); verify against motor spec or count magnets physically
- [ ] Set a conservative voltage limit before first spin — start at **2–3V** for a gimbal motor; these have very low phase resistance and will draw large currents at higher voltages
- [ ] Call `motor.initFOC()` in open-loop mode (no sensor argument) and confirm no hang or fault
- [ ] Command a low target velocity (e.g. 2–5 rad/s) and confirm the motor rotates smoothly
- [ ] Verify rotation direction — note it and understand how to reverse it (swap any two phase wires, or negate velocity target)
- [ ] Gradually increase voltage limit while monitoring motor temperature by touch — establish a safe operating envelope for bench testing
- [ ] Vary velocity target across the range — observe where open-loop becomes rough or loses synchronisation (this is the fundamental limit of open-loop FOC)
- [ ] Confirm the motor stops cleanly when velocity target is set to zero — no coasting, no oscillation
- [ ] Monitor supply current during spin with a multimeter in series — sanity check against expected values
- [ ] Note any audible noise at different PWM/velocity combinations — this informs PWM frequency tuning later

---

## Phase 3 — Closed-Loop with MT6701

> **Objective:** Add position feedback, complete the FOC loop, and tune the system to the point where haptic effects are feasible.

---

### 📝 Phase 3 Notes

#### BLDC motor model in the d/q reference frame

Field-Oriented Control works by transforming the three-phase motor currents into a two-axis rotating reference frame (the **d/q frame**) that is locked to the rotor's magnetic field. In this frame, a BLDC motor behaves like two independent first-order electrical systems, plus a mechanical equation:

**Electrical model:**
```
Vd = Rs·id + Ld·(did/dt) - ωe·Lq·iq        [d-axis voltage equation]
Vq = Rs·iq + Lq·(diq/dt) + ωe·Ld·id + ωe·λm  [q-axis voltage equation]
```

**Mechanical model:**
```
Te = (3/2)·p·λm·iq          [electromagnetic torque, Nm]
Te - TL = J·(dω/dt) + B·ω   [Newton's second law for rotation]
```

**Symbol reference:**

| Symbol | Name | Units |
|--------|------|-------|
| Rs | Stator phase resistance | Ω |
| Ld | d-axis inductance | H |
| Lq | q-axis inductance | H |
| ωe | Electrical angular velocity (= p·ωm) | rad/s |
| λm | Permanent magnet flux linkage | Wb |
| Ke | Back-EMF constant | V·s/rad |
| id | d-axis current | A |
| iq | q-axis current (torque-producing) | A |
| Vd, Vq | d/q axis voltages | V |
| Te | Electromagnetic torque | N·m |
| TL | Load torque | N·m |
| J | Rotor + load moment of inertia | kg·m² |
| B | Viscous friction coefficient | N·m·s/rad |
| p | Pole pairs | — |
| α | Angular acceleration | rad/s² |
| τ | Desired closed-loop time constant (IMC) | s |

**For your SPMSM (surface-mount motor):** Ld ≈ Lq = L, which simplifies the electrical equations and means the cross-coupling terms (ωe·Lq·iq and ωe·Ld·id) are equal and can be decoupled with a simple feedforward term in the current controller.

**Key insight — why iq controls torque:** In the d/q frame, `id` controls flux (set to 0 for maximum efficiency in an SPMSM), and `iq` is directly proportional to torque via Te = (3/2)·p·λm·iq. This is why torque control in FOC reduces to controlling a single DC current — iq — rather than three sinusoidal phase currents.

#### IMC-based current controller tuning

**IMC** (Internal Model Control) is a controller design method that inverts the plant model and sets a single tuning parameter — the desired closed-loop bandwidth time constant τ — from which all controller gains are derived analytically. For the d/q current loops (which look like first-order RL systems):

```
Plant transfer function (d or q axis, ignoring cross-coupling):
  G(s) = 1 / (Rs + L·s)     →    pole at s = -Rs/L

IMC-derived PI gains:
  Kp = L / τ
  Ki = Rs / τ

Where τ is your target closed-loop time constant.
Smaller τ = faster response = more aggressive = more noise-sensitive.
A good starting point: τ = L/Rs (matches the plant's natural time constant) → Kp = 1, Ki = Rs²/L
```

This means once you have Rs and L from M9, you can compute current loop gains directly — no manual tuning. The velocity and position loops on top are then tuned empirically (or via a second model-based step using J and B).

---

### Milestone 6 — MT6701 position reading over I2C

Wire the MT6701 to the Nucleo's I2C bus and read raw 14-bit angle values. Verify consistency and handle the zero-crossing. Zero position is not set on the encoder — this will be managed in software. The goal is a clean, reliable angle data stream before the motor is involved.

**Checklist:**
- [ ] Wire MT6701 to the Nucleo I2C pins — confirm SDA, SCL, VDD (3.3V), GND, and enable the SimpleFOC Shield's I2C pull-up pads
- [ ] Confirm MT6701 I2C address (0x06 default) appears on the bus scanner written in M3
- [ ] Read the raw 14-bit angle register (registers 0x03 and 0x04) and reconstruct the full angle value from the two bytes
- [ ] Verify the reading changes continuously and smoothly as the shaft is rotated by hand — no jumps other than the 0→16383→0 zero-crossing
- [ ] Implement zero-crossing handling: detect the wraparound and produce a continuous accumulating angle (multi-turn counter) rather than a sawtooth — this is essential for haptic effects later
- [ ] Implement real-time serial plotting of the angle — verify linearity across a full rotation
- [ ] Verify read rate at 400kHz I2C — confirm consistent reads with no I2C errors at speed
- [ ] Note the I2C read latency (can measure with a scope or GPIO toggle + logic analyser) — establishes baseline sensor update rate for later FOC loop timing analysis
- [ ] Document that I2C at 400kHz is sufficient for this application; note Phase 6 as the point to consider switching to SPI/SSI if higher sensor bandwidth is ever needed

---

### Milestone 7 — SimpleFOC closed-loop velocity and angle modes

Integrate the MT6701 as a SimpleFOC sensor, run the FOC alignment routine, and achieve stable closed-loop velocity then angle control. Motor must be properly mounted on its base for this milestone.

**Checklist:**
- [ ] Instantiate the MT6701 as a `MagneticSensorI2C` SimpleFOC sensor object with correct I2C address and resolution (14-bit)
- [ ] Call `sensor.init()` and verify angle reads through SimpleFOC's sensor interface match your raw reads from M6
- [ ] Link the sensor to the motor object with `motor.linkSensor(&sensor)`
- [ ] Run `motor.initFOC()` — the alignment sequence will briefly energise the motor and rotate the shaft to find the electrical angle offset. Verify the sequence completes without fault
- [ ] Understand what alignment is doing: applying a known voltage vector to lock the rotor to a known electrical angle, then rotating it to establish sensor direction (CW vs CCW) and polarity relative to the motor's winding sequence
- [ ] Verify `motor.sensor_direction` and `motor.zero_electric_angle` are set correctly after alignment — print them over serial and save them to avoid re-running alignment each power cycle later
- [ ] Switch to `TORQUE` / voltage mode and command a small constant torque — verify smooth rotation
- [ ] Switch to closed-loop velocity mode (`VELOCITY`) — command a low target velocity and confirm stable tracking
- [ ] Verify velocity control stability: the motor should maintain a commanded velocity under gentle manual load without oscillating
- [ ] Switch to closed-loop angle mode (`ANGLE`) — command a target angle and verify the motor holds it with stiffness against manual disturbance
- [ ] Test angle mode step response: command a step change in angle and observe overshoot, rise time, and settling — this is the pre-tuning baseline for M8

---

### Milestone 8 — FOC tuning

Tune the current, velocity, and angle controllers using a model-based approach for the inner current loop (IMC) and structured empirical tuning for the outer loops. Requires accurate Rs and L from M9 — this milestone should be revisited and finalised after M9, even if initial empirical tuning is done first.

> **Note on sequencing:** You may do an initial empirical pass on M8 to get the system running stably, then complete M9 (parameter identification), then return to M8 to apply IMC-derived gains and compare results. This iterative approach is valid and instructive.

**Checklist:**

*Current loop (inner loop):*
- [ ] Verify current sensing is working correctly — confirm ACS712 supply voltage configuration per hardware notes before proceeding
- [ ] Enable current sensing in SimpleFOC with `LowsideCurrentSense` or `InlineCurrentSense` as appropriate for the shield v3.2
- [ ] Read and plot phase currents over serial while the motor is held at standstill with a small commanded torque — verify the readings are plausible (expect low current at small torque commands given 11.2Ω resistance)
- [ ] Once Rs and L are available from M9: compute IMC-based current PI gains using `Kp = L/τ` and `Ki = Rs/τ` with an initial τ = L/Rs
- [ ] Apply computed gains, run step torque commands, and verify current tracks the commanded iq reference without oscillation
- [ ] Tighten τ (reduce it) incrementally to increase bandwidth — stop when current response becomes noisy or oscillatory

*Velocity loop (middle loop):*
- [ ] Start with conservative P gain only (I = 0, D = 0) — increase P until the motor holds velocity under load without oscillating
- [ ] Add I gain gradually to eliminate steady-state velocity error under constant load
- [ ] Characterise velocity loop bandwidth — how fast can it track a sinusoidal velocity reference before amplitude drops or phase lag becomes significant
- [ ] Note that velocity loop bandwidth must be well below current loop bandwidth (typically 5–10× separation)

*Angle loop (outer loop):*
- [ ] Tune angle P gain — this is the dominant knob for position stiffness. Higher P = stiffer hold = more haptic feel, but too high causes oscillation
- [ ] Add D gain to damp overshoot on step position commands
- [ ] Test disturbance rejection: push the shaft and observe how quickly and cleanly it returns to target
- [ ] Characterise the stiffness at the shaft: estimate the effective spring constant (N·m/rad) at your chosen P gain — this will inform haptic effect design in Phase 4
- [ ] Document final gain set and the reasoning behind each value — this record is the foundation for haptic parameter design

---

### Milestone 9 — Motor self-commissioning and parameter identification

Implement a standstill parameter identification routine to experimentally extract the motor's electrical and mechanical parameters. Understand the BLDC plant model these parameters describe and use the results to derive model-based current controller gains. This is the same fundamental procedure used by VESC, ST Motor Profiler, ODrive, and Moteus in their automatic motor detection routines.

**Background — why this matters:**
Accurate Rs and L allow current controller gains to be computed analytically via IMC rather than tuned by feel. Accurate Ke/λm defines the torque-per-amp relationship essential for calibrated haptic force output. Accurate J enables model-based velocity loop tuning and is a prerequisite for the sensorless observer design in Phase 7.

**Checklist:**

*Phase resistance (Rs) — DC injection, pure standstill:*
- [ ] Apply a known DC voltage across two motor phases (third floating) using the driver — start very low (0.5V given 11.2Ω expected)
- [ ] Measure the steady-state current drawn using the ACS712 sensors
- [ ] Calculate Rs = V / I. For a wye-connected motor this measures 2×Rs (two phases in series) — divide by 2
- [ ] Repeat at 3–5 different voltage levels and average — confirms linearity and reduces noise error
- [ ] Compare against datasheet value (11.2Ω) — a ±20% agreement is reasonable; larger deviation suggests a measurement issue
- [ ] Apply a correction for winding temperature if the motor has been running — Rs is temperature-dependent (~0.4%/°C for copper)

*Phase inductance (L) — AC injection, pure standstill:*
- [ ] Apply a small AC voltage signal (sine wave) at a known frequency (typically 1–5 kHz) across two phases using the PWM driver
- [ ] Measure the resulting current amplitude and phase shift using the ACS712
- [ ] Calculate impedance: Z = V_amplitude / I_amplitude
- [ ] Extract inductance: L = √(Z² - Rs²) / (2π·f) — this is the total series inductance; divide by 2 for single-phase L
- [ ] Repeat at 2–3 frequencies to check for frequency dependence (iron losses cause apparent L to drop at higher frequencies)
- [ ] For SPMSM: Ld ≈ Lq — a single measurement is sufficient. Note the value for potential HFI use in Phase 7
- [ ] Verify the result is physically plausible — gimbal motors typically have L in the range of 0.1–5 mH

*Back-EMF constant and flux linkage (Ke, λm) — automated via steady-state voltage equations:*
- [ ] Understand the relationship between λm and Ke before starting: λm (Wb) is the fundamental physical quantity describing rotor flux linkage. Ke is derived from it — referred to electrical speed, Ke = λm numerically; referred to mechanical speed, Ke_m = p·λm. The document uses λm as the primary quantity throughout. KV (from the spec sheet) provides a sanity check: `KV = 60 / (2π · p · λm)` — expect ~100 RPM/V
- [ ] The extraction method exploits the steady-state q-axis voltage equation. Under free spin with no load (TL ≈ 0), id = 0, and iq ≈ 0, the equation simplifies to: `Vq ≈ ωe · λm`. Since you command Vq and measure ωe from the encoder, λm = Vq / ωe — entirely computable in firmware, no oscilloscope needed
- [ ] Implement the automated extraction: spin the motor at a stable open-loop velocity (from M5), sample Vq (the commanded q-axis voltage) and ωe (from MT6701, converted to electrical speed by multiplying ωm by p) over several hundred milliseconds and average to reduce noise
- [ ] Calculate `λm = mean(Vq) / mean(ωe)` — average over multiple samples to reduce noise
- [ ] Repeat at 2–3 different spin speeds and verify λm is consistent across them — it should be speed-independent if the measurement is clean
- [ ] Cross-check against KV rating: compute `KV_estimated = 60 / (2π · p · λm)` and compare to the 100 RPM/V spec — expect reasonable agreement within ~15%
- [ ] Store λm — this value feeds directly into the torque equation `Te = (3/2)·p·λm·iq` and is a required input for the Phase 7 sensorless observers

*Rotor + load inertia (J) — speed ramp test:*
- [ ] Apply a known constant torque command Te = (3/2)·p·λm·iq using closed-loop current control (requires M7 and M9 Ke first)
- [ ] Measure the resulting angular acceleration α from the MT6701 position data (differentiate velocity numerically)
- [ ] Calculate: J = (Te - B·ω) / α ≈ Te / α at low speeds where friction term B·ω is small
- [ ] Repeat at several torque levels and average — J should be constant, B can be extracted from the speed-dependent residual
- [ ] Note: J includes both rotor inertia and any attached load (knob, indicator disc) — measure with the final mechanical assembly in place for the most accurate haptic model

*Model synthesis and IMC gain derivation:*
- [ ] Assemble the full motor parameter set: {Rs, L, Ke, λm, J, B, p}
- [ ] Write the d/q voltage equations with your measured values and verify the model predicts steady-state behaviour (e.g. predicted vs measured current at a given voltage and speed)
- [ ] Compute IMC current controller gains: `Kp = L/τ`, `Ki = Rs/τ` — try τ = L/Rs as a starting point
- [ ] Apply gains in SimpleFOC current controller and compare step response against empirical tuning from M8
- [ ] Derive velocity loop bandwidth estimate from J and current loop bandwidth — use this to set an informed starting point for velocity PI gains
- [ ] Document the complete parameter set and derived gains in a motor characterisation record — these values carry forward into Phase 7 observer design

---

## Phase 4 — Haptic Engine

> **Objective:** Build the core haptic capability of the smart knob — the system that makes it feel like something.

---

### 📝 Phase 4 Notes

#### Haptic effects as torque commands

Every haptic effect in this project is fundamentally a function that takes the current shaft state (position θ, velocity ω) and outputs a torque command Te. The FOC current loop then executes that torque as an iq setpoint. This is the conceptual model for all effects:

```
haptic_effect(θ, ω) → Te → iq = Te / ((3/2)·p·λm)
```

The three primitive effect types and their torque laws:

```
Detent (spring-to-nearest-notch):
  Te = -Kd · sin((θ - θ_nearest) · n)    where n = detents per revolution, Kd = detent strength

Endstop (one-sided spring):
  Te = -Ke · (θ - θ_limit)   if θ > θ_limit (or < θ_min)
  Te = 0                      otherwise

Friction (velocity damping):
  Te = -Kf · ω
```

More complex effects are compositions or extensions of these primitives. The quality of haptic feel is determined by: (1) torque calculation correctness, (2) FOC loop rate and latency, and (3) how well the current loop executes the commanded torque — which is why M8/M9 are prerequisites.

#### Software architecture for haptics

A clean haptic engine separates three concerns:

- **Effect definition** — a function (or object) that computes Te from {θ, ω, effect parameters}
- **Effect execution** — the FOC loop calling the active effect at high rate and passing the result to the motor
- **Effect management** — switching between effects, storing parameter sets, responding to user input

Keeping these three layers separate from the start makes M11 and M12 significantly easier to build on top of M10.

---

### Milestone 10 — First haptic effects

Implement the three fundamental haptic primitives — detents, endstops, and friction — as torque commands in the SimpleFOC torque control loop. Get each feeling physically convincing as a standalone mode before combining or extending them.

**Checklist:**

*Setup — torque control mode:*
- [ ] Switch SimpleFOC to `TORQUE` control mode with current sensing enabled — this is the direct path from effect → iq → motor
- [ ] Verify that commanding iq = 0 results in the motor spinning freely with minimal resistance — confirms the control path is clean before adding effects
- [ ] Implement the main haptic loop: read θ and ω from the MT6701, compute Te from the active effect, convert to iq and pass to SimpleFOC — confirm the loop runs at a stable, known rate
- [ ] Measure and log the actual haptic loop execution rate — this is a critical number for effect feel. Target ≥1 kHz for responsive haptics

*Detent effect:*
- [ ] Implement the sinusoidal detent torque law: `Te = -Kd · sin((θ mod (2π/n)) · n)` where n is number of detents per revolution
- [ ] Start with n = 12 (30° spacing) and a conservative Kd — increase Kd until detents are clearly felt, back off before oscillation appears
- [ ] Verify the motor snaps cleanly to each detent position when released from between two detents
- [ ] Test at different n values (4, 8, 12, 24, 48) — feel how detent spacing affects the character of the effect
- [ ] Identify the maximum Kd before the control loop becomes unstable at each n — this defines your usable haptic force envelope
- [ ] Note that very fine detents (high n) require a higher FOC loop rate to feel clean — document any degradation observed

*Endstop effect:*
- [ ] Implement one-sided spring torque: `Te = -Ke · max(0, θ - θ_max)` for upper limit, mirrored for lower
- [ ] Set soft limits (θ_min, θ_max) and verify the motor pushes back when the shaft is rotated past them
- [ ] Tune Ke for a natural-feeling wall — too soft feels vague, too hard causes current saturation and harsh bouncing
- [ ] Combine endstops with detents: detents within a bounded range with hard walls at each end
- [ ] Implement a non-linear endstop (stiffness increases with penetration depth) — more natural feel than a pure spring

*Friction / damping effect:*
- [ ] Implement velocity-proportional damping: `Te = -Kf · ω`
- [ ] Tune Kf for a smooth, viscous feel — the shaft should feel like it's moving through a fluid
- [ ] Combine friction with detents — friction makes detents feel more deliberate, prevents rattling through them at high speed
- [ ] Implement a dead-band around ω = 0 to avoid noise-driven micro-oscillation at standstill
- [ ] Experiment with nonlinear friction (Kf increases with |ω|) to simulate magnetic braking feel

---

### Milestone 11 — Haptic playground

Build a runtime-configurable haptic system where effects and their parameters can be changed over serial without reflashing. Expand the effect library. The goal is a personal sandbox for feel exploration and parameter intuition.

**Checklist:**

*Runtime configuration interface:*
- [ ] Design a simple serial command protocol — e.g. `MODE 1`, `SET Kd 0.8`, `SET n 12`, `GET params` — parsed in the main loop
- [ ] Implement a parameter struct per effect type that can be updated live from serial commands
- [ ] Verify that parameter changes take effect immediately on the next haptic loop iteration — no reflash needed
- [ ] Add a `PRINT` command that dumps the current effect type and all active parameters — useful for recording good configurations
- [ ] Add bounds checking on all incoming parameters — prevent commands that would saturate current or destabilise the loop

*Extended effect library:*
- [ ] **Inertia simulation:** augment the mechanical equation with a virtual inertia term `Te = -J_virtual · α` — makes the knob feel heavier or lighter than it physically is
- [ ] **Magnetic snap with overshoot:** detent with a deliberate underdamped response — the knob overshoots the target detent slightly before settling, mimicking a physical ratchet snap
- [ ] **Ratchet / one-directional detent:** detents resist motion in one direction but release freely in the other — implemented by making Kd asymmetric depending on the sign of ω relative to the direction of displacement
- [ ] **Variable resistance profile:** Kf varies as a function of position — e.g. high friction near centre, low friction at extremes, for a context-dependent feel
- [ ] **Progressive detents:** detent strength Kd varies with position — creates a sense of moving through regions of different texture
- [ ] **Combined modes:** implement at least two composite effects (e.g. detents + friction + endstops as a single configurable mode)

*Feel calibration and documentation:*
- [ ] For each effect, document the parameter range that feels good on your specific motor/assembly — this is your personal haptic parameter library
- [ ] Note which effects are most sensitive to FOC loop rate — identify any effects that feel noticeably worse at lower update rates
- [ ] Identify any effects that expose tuning limitations from M8 (e.g. oscillation at high Kd that better current loop gains might resolve) — flag for revisiting after M9

---

### Milestone 12 — State machine and profile persistence

Implement a proper application state machine and haptic profile management system. The knob should behave like a finished device — switching modes, remembering state, and responding to physical inputs cleanly.

**Checklist:**

*Physical input:*
- [ ] Wire a button to a Nucleo GPIO pin — implement debouncing in software (either time-based or state-machine-based, not just `delay()`)
- [ ] Detect short press, long press, and double press as distinct events — these become the mode navigation gestures
- [ ] Assign gesture → action mapping: e.g. short press = next mode, long press = reset position to zero, double press = toggle parameter lock

*State machine:*
- [ ] Define a set of named haptic modes (e.g. `FREE_SPIN`, `DETENT_12`, `DETENT_48`, `BOUNDED_DIAL`, `INERTIA_WHEEL`) — at least 4–5 distinct feels
- [ ] Implement a state machine with states corresponding to haptic modes plus transition states (e.g. `TRANSITIONING` during a mode switch)
- [ ] On mode transition: ramp Te smoothly to zero before switching effect, then ramp back up — prevents torque step that would feel like a jolt
- [ ] Add a visual or audio indicator of current mode if hardware allows (e.g. LED pattern, or a brief haptic pulse pattern as mode confirmation)

*Profile persistence:*
- [ ] Store the active mode index and any user-modified parameters to STM32 flash using EEPROM emulation. **Background:** The STM32L452RE has no dedicated EEPROM — only flash, where program code lives. Flash can only be erased in entire 2KB pages and has a ~10,000 erase cycle lifetime, making naive read/write impractical for frequent configuration saves. ST's EEPROM emulation scheme (exposed as `EEPROM.h` in STM32Duino) solves this by appending new values with a tag into a reserved flash page rather than erasing on every write — the page is only erased when full, spreading wear across many writes. From your code's perspective it behaves like Arduino EEPROM: `EEPROM.put(address, value)` and `EEPROM.get(address, value)`
- [ ] On power-up: read stored profile and restore last active mode and parameters — the knob should wake up in the same state it was left in
- [ ] Implement a factory reset (e.g. hold button at power-up) that clears stored profile and returns to defaults
- [ ] Verify that flash write cycles are not triggered excessively — only write on deliberate parameter change, not continuously
- [ ] *(Optional)* Explore an external SPI SD card module as an alternative or supplementary storage medium — useful for logging haptic sessions, storing large numbers of effect profiles, or exporting parameter data for analysis. SPI on the L452RE is straightforward via the Arduino `SD.h` library; the main considerations are SPI pin assignment (check for conflicts with other peripherals) and the FAT filesystem overhead. This also serves as a practical SPI communication exercise complementing the I2C work from M3

*Code architecture review:*
- [ ] Ensure the haptic effect logic, state machine, serial interface, and sensor reading are cleanly separated into distinct modules or files
- [ ] Verify the haptic loop rate has not degraded from M10 — adding state machine and serial parsing overhead should not affect the core torque update rate
- [ ] The system at this point should be demonstrable to someone unfamiliar with the project — hand them the knob and they should immediately understand that it feels like something intentional

---

## Phase 5 — Computer Interface & Polish

> **Objective:** Make the smart knob interface with a computer over USB HID with full bidirectional communication — the knob sends position and input events to the host, the host sends haptic profile configurations back to the knob.

---

### 📝 Phase 5 Notes

#### USB HID fundamentals

USB HID (Human Interface Device) is a USB device class that allows a device to exchange structured data packets with a host without requiring a custom driver — the OS handles enumeration natively. Communication is built around **reports**, which are fixed-format byte arrays described by a **report descriptor** written in a compact binary language that the OS parses at enumeration time.

There are two report directions:
- **IN reports** (device → host): the knob sends position, velocity, button state, active mode
- **OUT reports** (host → device): the host sends haptic profile index and parameters

Key HID concepts relevant to this milestone:

| Concept | Meaning |
|---------|---------|
| Report descriptor | Binary descriptor that defines the structure and meaning of every byte in every report. Written once, parsed by the OS at enumeration |
| Report ID | One-byte prefix that identifies which report format is being sent — allows multiple report types on the same endpoint |
| Polling rate | How often the host requests an IN report. Default 10ms (100Hz); can request 1ms (1kHz) in the descriptor. Directly affects input latency |
| Endpoint | A unidirectional data pipe. HID uses interrupt endpoints — guaranteed maximum latency, not guaranteed bandwidth |
| Usage page / Usage | HID's semantic labelling system. Custom vendor-defined usages (Usage Page 0xFF00) are the correct approach for application-specific data |

#### Report design for the smart knob

A practical bidirectional report structure for this project:

```
IN report (knob → host), sent every poll interval:
  Byte 0:   Report ID (0x01)
  Bytes 1-4: Shaft angle (int32, in encoder counts or millidegrees)
  Bytes 5-8: Shaft velocity (int32, in milli-rad/s)
  Byte 9:   Button state bitmask (bit 0 = press, bit 1 = long press, etc.)
  Byte 10:  Active mode index
  Byte 11:  Status flags (e.g. bit 0 = FOC healthy, bit 1 = current limit active)

OUT report (host → knob), sent on configuration change:
  Byte 0:   Report ID (0x02)
  Byte 1:   Target mode index
  Bytes 2-5: Parameter 1 (float32, e.g. Kd — detent strength)
  Bytes 6-9: Parameter 2 (float32, e.g. n — detent count)
  Bytes 10-13: Parameter 3 (float32, e.g. Kf — friction)
  Bytes 14-17: Parameter 4 (float32, e.g. endstop position)
  Byte 18:  Flags (e.g. bit 0 = persist to flash)
```

This is a starting point — adjust field widths and parameter count as your effect library grows. Keeping reports under 64 bytes avoids needing to split across multiple transfers.

#### Host-side architecture

The host GUI application has three responsibilities:
- **Listening:** continuously read IN reports and update the UI with current knob state
- **Context detection:** determine which application has focus and select the appropriate haptic profile
- **Commanding:** send OUT reports when the profile changes or the user adjusts parameters manually

Python is the practical choice for the host side: `hid` (hidapi bindings) for USB communication, and `tkinter`, `PyQt6`, or `Dear PyGui` for the GUI layer.

---

### Milestone 13 — USB HID device

Implement the smart knob as a custom USB HID device with bidirectional report communication. The OS should enumerate the device without any custom driver. IN reports deliver knob state to the host; OUT reports deliver haptic configuration to the knob.

**Checklist:**

*USB configuration on the L452RE:*
- [ ] Enable USB in `platformio.ini` — add `build_flags = -DUSBCON -DUSBD_USE_HID_COMPOSITE` or the appropriate STM32Duino USB HID flag for the L452RE
- [ ] Verify the USB pins (PA11 = D-, PA12 = D+) are not conflicting with any other peripheral assignments from earlier milestones
- [ ] Confirm the device enumerates when plugged in — OS should recognise a new HID device. Check Device Manager (Windows) or `lsusb` / `hidapi-hidtest` (Linux/macOS)
- [ ] Set meaningful USB descriptor strings: manufacturer name, product name, serial number — these appear in the OS device list and in the host application

*Report descriptor:*
- [ ] Write the HID report descriptor defining both the IN report (ID 0x01) and OUT report (ID 0x02) using vendor-defined usage page (0xFF00)
- [ ] Validate the descriptor using the [USB HID Descriptor Tool](https://www.usb.org/document-library/hid-descriptor-tool) before flashing — a malformed descriptor will prevent enumeration with no useful error message
- [ ] Request a 1ms polling interval in the descriptor (bInterval = 1) — this gives 1kHz maximum IN report rate, reducing input latency
- [ ] Verify the total report size (excluding Report ID byte) stays under 64 bytes for both IN and OUT reports

*IN reports (knob → host):*
- [ ] Implement the IN report struct in firmware — pack angle, velocity, button state, active mode, and status flags into the defined byte layout
- [ ] Send IN reports from the main loop or a timer interrupt at the poll rate — verify on the host that reports arrive at the expected rate
- [ ] Confirm angle and velocity values are correctly scaled and signed — test by rotating the shaft and watching values change on the host
- [ ] Verify button events are captured correctly and appear in the report bitmask

*OUT reports (host → device):*
- [ ] Implement the OUT report receive handler in firmware — STM32Duino HID libraries typically provide a callback for received OUT reports
- [ ] Parse the incoming byte array into the target mode index and parameter fields
- [ ] Apply the received mode and parameters to the haptic engine immediately — verify the knob changes behaviour within one poll cycle of receiving the command
- [ ] Implement the persist flag: if bit 0 of the flags byte is set, write the new profile to flash (EEPROM emulation from M12)
- [ ] Add basic validation of received parameters — reject out-of-range values and send a status flag back in the next IN report

---

### Milestone 14 — Host-side GUI and dynamic reconfiguration

Build a host-side GUI application in Python that reads the knob's IN reports, displays live state, detects the active application context, and sends appropriate haptic profiles via OUT reports. This is the "smart" in smart knob.

**Checklist:**

*USB communication layer:*
- [ ] Install `hid` (hidapi Python bindings) — `pip install hid`
- [ ] Write a minimal script that enumerates HID devices and finds the smart knob by vendor ID / product ID — verify it connects and reads raw bytes
- [ ] Parse incoming IN report bytes into named fields (angle, velocity, button state, mode, flags) — verify values match what the knob is doing physically
- [ ] Write a function that constructs and sends an OUT report given a mode index and parameter dict — verify the knob responds correctly
- [ ] Implement a background thread for continuous IN report reading — the GUI must not block on USB reads

*GUI application:*
- [ ] Choose a GUI framework — `PyQt6` is recommended for a polished result; `Dear PyGui` for faster iteration; `tkinter` if minimal dependencies are the priority
- [ ] Build the main window layout: live knob position visualisation (circular dial or angle readout), current mode display, active parameter readout, connection status indicator
- [ ] Add a mode selector (dropdown or button row) that sends the corresponding OUT report when changed
- [ ] Add parameter sliders for the key effect parameters (Kd, n, Kf, endstop position) — sliders send OUT reports in real time as they are dragged, giving live haptic feel adjustment from the host
- [ ] Display the IN report status flags — FOC health, current limit indicator — so faults are visible on the host

*Application context detection:*
- [ ] Implement active window detection using `pywin32` (Windows), `AppKit` (macOS), or `xdotool` / `wnck` (Linux) — poll the foreground application name every 200–500ms
- [ ] Define a profile mapping: a dict or config file that maps application names to haptic mode index and parameter sets. Example: `{"Spotify": (DETENT_12, {...}), "Chrome": (FREE_SPIN, {...}), "Figma": (BOUNDED_DIAL, {...})}`
- [ ] When the foreground application changes and a mapping exists: automatically send the corresponding OUT report — knob reconfigures without user interaction
- [ ] When no mapping exists for the active application: either hold the last profile or fall back to a configurable default mode
- [ ] Display the currently detected application and active profile mapping in the GUI — makes the automatic switching visible and debuggable

*Profile management:*
- [ ] Save the profile mapping to a local JSON or TOML config file — persists across host application restarts
- [ ] Add a GUI panel to create, edit, and delete profile mappings — user can teach the application which haptic mode to use for each program
- [ ] Add an "add current app" button that reads the current foreground application name and creates a new mapping for it with the currently active parameters — lowest-friction way to build up the mapping library
- [ ] Implement import/export of the full profile config as a JSON file — allows sharing configurations

---

## Phase 6 — Advanced STM32 & Productisation

> **Objective:** Resolve real performance constraints encountered during the project and optionally produce a standalone hardware design.

### Milestone 15 — Performance and architecture audit
By this phase, real STM32 bottlenecks will have surfaced. Address them: move time-critical code into interrupts or DMA transfers, audit the clock tree for optimal PWM frequency and FOC loop rate, reduce HAL overhead causing timing jitter in haptic response. This is where register-level knowledge becomes motivated by real problems rather than abstract learning.

### Milestone 16 — Custom PCB (optional)
Design a minimal custom board integrating the STM32L452 (or similar), gate driver, and MT6701 into a single smart knob unit. This forces engagement with STM32 bootstrapping: boot pin configuration, oscillator selection (HSI vs crystal), SWD debug header, decoupling strategy, and USB routing. Natural conclusion of the hardware journey.

---

## Phase 7 — Sensorless FOC (Advanced Learning Branch)

> **Objective:** Understand and implement sensorless FOC with particular focus on the zero-speed and low-speed problem, which is the genuinely hard part. This phase is a deliberate departure from the SimpleFOC library — you will be writing observers and state estimators yourself, or integrating lower-level STM32 motor control middleware (e.g. ST's MCSDK / X-CUBE-MCSDK).
>
> **Why pursue sensorless if encoders are better for this project?** In mass-market applications (appliances, compressors, EV auxiliary motors, cooling fans) sensorless is the dominant approach — it eliminates encoder cost, cabling, connectors, and a mechanical failure point. At high speeds it can also outperform low-resolution encoders on velocity estimation smoothness. However, for any application requiring holding torque at standstill, precise low-speed control, or absolute positioning — robotics joints, CNC axes, haptic devices — encoders win unambiguously. Sensorless gives you an *estimate* with potential drift; an encoder gives you ground truth. The smart knob uses an encoder because haptic effects operate exactly at the worst-case operating point for sensorless (zero/low speed, standstill torque). Phase 7 is pursued as a learning branch relevant to a large segment of industrial motor drives, with the option to revisit on a more salient (IPM) motor later.
>
> **Critical motor context:** The Mitoot 2804 is a **surface-mount PMSM (SPMSM)** with low magnetic saliency. This has direct consequences for which techniques are available to you:
> - **Back-EMF / SMO methods** — work well at medium-high speed, fail at zero/low speed because back-EMF amplitude is proportional to speed and vanishes at standstill.
> - **High Frequency Injection (HFI)** — relies on inductance asymmetry between d and q axes (saliency). On an SPMSM this asymmetry is minimal, making HFI unreliable or unusable without careful motor characterisation. Works well on IPM (interior magnet) motors.
> - **I/F open-loop startup + observer transition** — the standard practical approach: start the motor open-loop in current-controlled mode (known assumed angle) until sufficient back-EMF is available, then transition to a closed-loop observer. The transition region is the engineering challenge.
>
> This means achieving truly sensorless torque control at zero speed on this specific motor is a research-grade problem. The realistic and valuable goal is understanding the full landscape, implementing the mid-to-high speed region well, and understanding the fundamental limits that require either a sensor or a more salient motor to overcome.

### Milestone 17 — Sensorless FOC theory and the speed-range problem
Understand the full taxonomy of sensorless methods: back-EMF estimation, Sliding Mode Observers (SMO), Model Reference Adaptive Systems (MRAS), Extended Kalman Filters (EKF), flux observers, and HFI. Understand clearly why each method has a valid operating speed range and why zero speed is the universal hard boundary for back-EMF methods. Map each technique to the SPMSM vs IPMSM distinction. Outcome: a clear mental model of the solution space before writing any code.

### Milestone 18 — I/F open-loop startup strategy
Implement a controlled open-loop startup sequence: inject a known current vector at an assumed rotor angle, ramp speed while monitoring current response, detect the minimum speed at which back-EMF is estimable. This is the necessary foundation for any back-EMF sensorless scheme on this motor and teaches current-controlled FOC (id/iq control) directly on the STM32 without SimpleFOC abstraction.

### Milestone 19 — Back-EMF Sliding Mode Observer (SMO)
Implement a basic SMO to estimate back-EMF from measured phase currents and commanded voltages. Extract rotor position and speed via a Phase-Locked Loop (PLL) on the estimated back-EMF vector. Characterise the minimum reliable operating speed. Understand the SMO's chattering problem and a standard mitigation (sigmoid or saturation function replacing the discontinuous sign function).

### Milestone 20 — Seamless startup-to-observer transition
Implement the transition from I/F open-loop startup into closed-loop SMO operation. This is the core engineering challenge of the phase: the transition must be smooth (no torque step, no current spike, no stall). Tune the crossover speed and implement a blending or bumpless transfer strategy. A clean transition on a real motor is a meaningful achievement.

### Milestone 21 — Flux observer and comparison
Implement a second observer architecture — a voltage-model flux observer (e.g. SOGI-based) — and compare its behaviour against the SMO in terms of low-speed performance, noise sensitivity, and parameter sensitivity. Understand the DC bias problem inherent in pure integrator-based flux observers and how second-order generalised integrators (SOGI) address it. This milestone builds estimation theory intuition through direct comparison.

### Milestone 22 — HFI exploration on the 2804 (experimental)
Attempt pulsating d-axis high-frequency voltage injection on the 2804 and measure the resulting current response. Characterise the actual d/q inductance asymmetry experimentally (it may be small but nonzero). Determine empirically whether the saliency is sufficient for reliable position estimation at standstill. This milestone is intentionally open-ended — a negative result (HFI is not viable on this motor) is as valuable a learning outcome as a positive one, and directly motivates the use of a more salient motor for future work.

---

## Progress Tracker

| Phase | Milestone | Status |
|-------|-----------|--------|
| 1 | M1 — PlatformIO first project | ⬜ |
| 1 | M2 — GPIO & timer/PWM | ⬜ |
| 1 | M3 — I2C communication | ⬜ |
| 2 | M4 — Shield wiring & SimpleFOC init | ⬜ |
| 2 | M5 — Open-loop velocity spin | ⬜ |
| 3 | M6 — MT6701 position reading | ⬜ |
| 3 | M7 — Closed-loop velocity & angle | ⬜ |
| 3 | M8 — FOC tuning | ⬜ |
| 3 | M9 — Motor self-commissioning & parameter ID | ⬜ |
| 4 | M10 — First haptic effects | ⬜ |
| 4 | M11 — Haptic playground | ⬜ |
| 4 | M12 — State machine & persistence | ⬜ |
| 5 | M13 — USB HID device | ⬜ |
| 5 | M14 — Host-side protocol | ⬜ |
| 6 | M15 — Performance audit | ⬜ |
| 6 | M16 — Custom PCB (optional) | ⬜ |
| 7 | M17 — Sensorless theory & speed-range taxonomy | ⬜ |
| 7 | M18 — I/F open-loop startup | ⬜ |
| 7 | M19 — Back-EMF Sliding Mode Observer (SMO) | ⬜ |
| 7 | M20 — Startup-to-observer transition | ⬜ |
| 7 | M21 — Flux observer & comparison | ⬜ |
| 7 | M22 — HFI exploration on 2804 (experimental) | ⬜ |

---

## Document Status

- [x] Phase/milestone overview — *complete*
- [x] Per-milestone checklists — *complete for Phases 1–5; intentionally omitted for Phases 6–7*
- [ ] Per-milestone how-to / resources — *to be added*
