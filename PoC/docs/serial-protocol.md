# Serial Protocol Specification

Communication between the STM32 firmware and Windows software over UART at **115200 baud**, newline-terminated (`\n`).

## Message Format

All messages are ASCII text terminated by `\n`. No binary framing.

| Direction | Format | Example |
|-----------|--------|---------|
| PC → STM32 | `<command>[value]\n` | `S36\n`, `H\n`, `Z45.0\n` |
| STM32 → PC (ACK) | `A:<command>[value]\n` | `A:S36\n`, `A:H\n` |
| STM32 → PC (position) | `P<angle_deg>\n` | `P45.20\n` |
| STM32 → PC (info) | Free-form text | `Mode: HAPTIC \| Detents: 36\n` |

## Commands (PC → STM32)

### Mode Selection

| Command | Description | Response |
|---------|-------------|----------|
| `H` | Switch to Haptic (detent) mode | `A:H` |
| `I` | Switch to Inertia (flywheel) mode | `A:I` |
| `C` | Switch to Spring (centered) mode | `A:C` |
| `O` | Switch to Bounded (detents + walls) mode | `A:O` |

### Haptic Parameters

| Command | Description | Range | Response |
|---------|-------------|-------|----------|
| `S<n>` | Set detent count per revolution | 2–360 | `A:S<n>` |
| `D<v>` | Set detent strength (volts) | 0.5–6.0 | `A:D<v>` |

### Inertia Parameters

| Command | Description | Response |
|---------|-------------|----------|
| `J<v>` | Set virtual inertia (mass) | `A:J<v>` |
| `B<v>` | Set damping coefficient | `A:B<v>` |
| `F<v>` | Set Coulomb friction | `A:F<v>` |
| `K<v>` | Set coupling stiffness | `A:K<v>` |

### Spring Parameters

| Command | Description | Response |
|---------|-------------|----------|
| `W<v>` | Set spring stiffness (V/rad) | `A:W<v>` |
| `G<v>` | Set spring damping | `A:G<v>` |
| `E` | Set spring center to current position | `A:E<angle>` |
| `E<deg>` | Set spring center to specified angle | `A:E<angle>` |

### Bounded Parameters

| Command | Description | Response |
|---------|-------------|----------|
| `L<deg>` | Set lower bound (degrees) | `A:L<deg>` |
| `U<deg>` | Set upper bound (degrees) | `A:U<deg>` |
| `A<v>` | Set wall strength (V/rad) | `A:A<v>` |
| `S<n>` | Set detent count per revolution | 2–360 | `A:S<n>` |
| `D<v>` | Set detent strength (volts) | 0.5–6.0 | `A:D<v>` |

### Position Control

| Command | Description | Response |
|---------|-------------|----------|
| `P` | Query current position | `P<angle>` |
| `Q` | Query full state (mode, all params) | Multi-line state dump |
| `Z<deg>` | Seek to angle (degrees) | `A:Z<deg>`, then `A:SEEK_DONE` |

### Motor Configuration

| Command | Description | Response |
|---------|-------------|----------|
| `MPP<v>` | Set position PID P gain | `A:MPP<v>` |
| `MPI<v>` | Set position PID I gain | `A:MPI<v>` |
| `MPD<v>` | Set position PID D gain | `A:MPD<v>` |
| `MVL<v>` | Set velocity limit (rad/s) | `A:MVL<v>` |
| `M` | Query current PID values | `PP=<v> PI=<v> PD=<v> VL=<v>` |

## Events (STM32 → PC)

### Position Updates

Format: `P<angle_degrees>`

- Sent when angle changes by ≥0.5° AND ≥20ms since last report (haptic/spring/bounded modes)
- Sent when angle changes by ≥0.5° AND ≥10ms since last report (inertia mode — faster updates)
- Angle is in degrees with 2 decimal places

### Seek Completion

When a `Z<deg>` seek command completes:
1. Motor holds at target for 200ms settle time
2. Sends `A:SEEK_DONE`
3. Returns to previous haptic mode automatically

### Future: Button Events (Phase 2)

| Event | Format | Trigger |
|-------|--------|---------|
| Short press | `BTN:SHORT` | Quick press (<400ms) |
| Double press | `BTN:DOUBLE` | Two presses within 400ms |
| Long press | `BTN:LONG` | Hold for 1+ second |

## Timing

| Parameter | Value | Notes |
|-----------|-------|-------|
| Baud rate | 115200 | 8N1 |
| FOC loop rate | >1 kHz | `motor.loopFOC()` — must not be slowed by serial |
| Position report interval | 10–20 ms | Mode-dependent |
| Position report threshold | 0.5° | Minimum change to trigger report |
| Seek settle time | 200 ms | Hold at target before declaring done |
| Seek timeout | 10,000 ms | Abort and return to previous mode |
| Button debounce | 200 ms | Minimum time between button events |
