"""SmartKnob serial protocol constants.

Mirrors the firmware's serial command interface defined in comms.h/cpp.
All commands are ASCII text, newline-terminated, at 115200 baud.

Usage:
    from smartknob.protocol import HapticMode, CMD_SEEK, RESP_POSITION
    from smartknob.protocol import print_help
"""

from enum import Enum

# ======================== Serial Configuration ========================
BAUD_RATE: int = 115200
"""Serial baud rate. Must match firmware (Serial.begin in setup())."""

SERIAL_TIMEOUT: float = 0.1
"""Serial read timeout in seconds. Used by serial.Serial(timeout=...)."""

# ======================== Haptic Modes ========================


class HapticMode(str, Enum):
    """Available haptic feedback modes.

    Each mode produces a different torque feel on the knob:
        HAPTIC  — Virtual sine-based detents (infinite rotation)
        INERTIA — Simulated rotational mass with coupling spring
        SPRING  — Hooke's law centered return with damping
        BOUNDED — Detents distributed within walled range
    """

    HAPTIC = "H"
    INERTIA = "I"
    SPRING = "C"
    BOUNDED = "O"


# ======================== Commands (PC → STM32) ========================

# Mode switching
CMD_HAPTIC: str = "H"
"""Switch to haptic detent mode. Ack: A:H"""

CMD_INERTIA: str = "I"
"""Switch to inertia flywheel mode. Ack: A:I"""

CMD_SPRING: str = "C"
"""Switch to spring centered mode. Ack: A:C"""

CMD_BOUNDED: str = "O"
"""Switch to bounded detent+wall mode. Ack: A:O"""

# Haptic parameters (affect HAPTIC and BOUNDED modes)
CMD_DETENT_COUNT: str = "S"
"""S<2-360> — Number of detents per 360°. Ack: A:S<count>"""

CMD_DETENT_STRENGTH: str = "D"
"""D<volts> — Detent snap strength in volts. Ack: A:D<strength>"""

# Inertia parameters
CMD_INERTIA_VAL: str = "J"
"""J<float> — Virtual mass (higher = heavier flywheel). Ack: A:J<value>"""

CMD_DAMPING: str = "B"
"""B<float> — Drag coefficient (higher = more resistance). Ack: A:B<value>"""

CMD_FRICTION: str = "F"
"""F<float> — Static friction (minimum force to spin). Ack: A:F<value>"""

CMD_COUPLING: str = "K"
"""K<float> — Coupling spring between motor and virtual flywheel. Ack: A:K<value>"""

# Spring parameters
CMD_SPRING_STIFFNESS: str = "W"
"""W<V/rad> — Spring constant. Higher = stiffer snap-back. Ack: A:W<value>"""

CMD_SPRING_CENTER: str = "E"
"""E<deg> — Set spring center angle. Empty = use current position. Ack: A:E<angle>"""

CMD_SPRING_DAMPING: str = "G"
"""G<float> — Velocity damping to prevent oscillation. Ack: A:G<value>"""

# Bounded parameters
CMD_LOWER_BOUND: str = "L"
"""L<deg> — Lower wall position in degrees. Ack: A:L<angle>"""

CMD_UPPER_BOUND: str = "U"
"""U<deg> — Upper wall position in degrees. Ack: A:U<angle>"""

CMD_WALL_STRENGTH: str = "A"
"""A<V/rad> — Wall spring constant. Higher = harder walls. Ack: A:A<value>"""

# Position commands
CMD_QUERY_POS: str = "P"
"""Query current angle. Response: P<angle_deg>"""

CMD_QUERY_STATE: str = "Q"
"""Query full device state. Response: multi-line state dump"""

CMD_SEEK: str = "Z"
"""Z<deg> — Seek to angle in degrees. Ack: A:Z<angle>, then A:SEEK_DONE on completion"""

# Motor configuration
CMD_MOTOR: str = "M"
"""M<sub><val> — Motor config subcommands (PP/PI/PD/VL)"""

CMD_MOTOR_PID_P: str = "MPP"
"""MPP<float> — Position PID proportional gain. Ack: A:MPP<value>"""

CMD_MOTOR_PID_I: str = "MPI"
"""MPI<float> — Position PID integral gain. Ack: A:MPI<value>"""

CMD_MOTOR_PID_D: str = "MPD"
"""MPD<float> — Position PID derivative gain. Ack: A:MPD<value>"""

CMD_MOTOR_VEL_LIMIT: str = "MVL"
"""MVL<float> — Maximum velocity in rad/s during seeks. Ack: A:MVL<value>"""

# ======================== Responses (STM32 → PC) ========================

RESP_POSITION: str = "P"
"""P<angle_deg> — Position update in degrees (float, 2 decimal places)"""

RESP_ACK: str = "A:"
"""A:<command> — Command acknowledged. The text after A: identifies the command."""

RESP_SEEK_DONE: str = "A:SEEK_DONE"
"""Position seek completed. Motor has settled at target and returned to previous mode."""

# ======================== Mode Parameters Reference ========================

MODE_PARAMETERS: dict[str, list[str]] = {
    "HAPTIC": [
        "detent_count (S<2-360>) — detents per 360°",
        "detent_strength (D<volts>) — snap voltage",
    ],
    "INERTIA": [
        "virtual_inertia (J<float>) — mass feel",
        "damping (B<float>) — drag coefficient",
        "friction (F<float>) — static friction",
        "coupling (K<float>) — spring stiffness to motor",
    ],
    "SPRING": [
        "spring_stiffness (W<V/rad>) — spring constant",
        "spring_center (E<deg> or E) — center position",
        "spring_damping (G<float>) — velocity damping",
    ],
    "BOUNDED": [
        "detent_count (S<2-360>) — detents within bounds",
        "detent_strength (D<volts>) — snap voltage",
        "lower_bound (L<deg>) — lower wall angle",
        "upper_bound (U<deg>) — upper wall angle",
        "wall_strength (A<V/rad>) — wall spring constant",
    ],
}
"""Maps each mode to its adjustable parameters with command syntax."""


def print_help() -> None:
    """Print a human-readable summary of all commands, modes, and parameters.

    Call from Python REPL or scripts for quick reference:
        >>> from smartknob.protocol import print_help
        >>> print_help()
    """
    print("=== SmartKnob Serial Protocol ===")
    print(f"    Baud: {BAUD_RATE} | Format: ASCII | Terminator: \\n")
    print()

    print("Modes:")
    for mode in HapticMode:
        print(f"  {mode.value} — {mode.name}")
    print()

    print("Mode Parameters:")
    for mode_name, params in MODE_PARAMETERS.items():
        print(f"  {mode_name}:")
        for p in params:
            print(f"    {p}")
    print()

    print("Position Commands:")
    print(f"  {CMD_QUERY_POS}        — Query current angle (response: P<deg>)")
    print(f"  {CMD_QUERY_STATE}        — Query full device state (multi-line)")
    print(f"  {CMD_SEEK}<deg>   — Seek to angle (ack: A:Z, then A:SEEK_DONE)")
    print()

    print("Motor Config:")
    print(f"  {CMD_MOTOR_PID_P}<val> — Position P gain")
    print(f"  {CMD_MOTOR_PID_I}<val> — Position I gain")
    print(f"  {CMD_MOTOR_PID_D}<val> — Position D gain")
    print(f"  {CMD_MOTOR_VEL_LIMIT}<val> — Velocity limit (rad/s)")
    print()

    print("Responses (STM32 → PC):")
    print(f"  P<angle>     — Position update (degrees, 2 dp)")
    print(f"  A:<command>  — Command acknowledged")
    print(f"  A:SEEK_DONE  — Seek completed, returned to previous mode")
