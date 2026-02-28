"""SmartKnob serial driver — thread-safe, GUI-independent.

Provides SmartKnobDriver: the single interface between Python code and
the SmartKnob STM32 firmware over a serial port.

Usage:
    from smartknob.driver import SmartKnobDriver

    knob = SmartKnobDriver()
    knob.on_position = lambda angle_deg: print(f"Angle: {angle_deg}°")
    knob.connect("COM3")
    knob.set_mode(HapticMode.HAPTIC)
    knob.set_detent_count(24)
    knob.disconnect()
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

import serial
import serial.tools.list_ports

from smartknob.protocol import (
    BAUD_RATE,
    CMD_BOUNDED,
    CMD_COUPLING,
    CMD_DAMPING,
    CMD_DETENT_COUNT,
    CMD_DETENT_STRENGTH,
    CMD_FRICTION,
    CMD_HAPTIC,
    CMD_INERTIA,
    CMD_INERTIA_VAL,
    CMD_LOWER_BOUND,
    CMD_MOTOR_PID_D,
    CMD_MOTOR_PID_I,
    CMD_MOTOR_PID_P,
    CMD_MOTOR_VEL_LIMIT,
    CMD_QUERY_POS,
    CMD_QUERY_STATE,
    CMD_SEEK,
    CMD_SPRING,
    CMD_SPRING_CENTER,
    CMD_SPRING_DAMPING,
    CMD_SPRING_STIFFNESS,
    CMD_UPPER_BOUND,
    CMD_WALL_STRENGTH,
    RESP_ACK,
    RESP_POSITION,
    RESP_SEEK_DONE,
    SERIAL_TIMEOUT,
    HapticMode,
    print_help,
)

logger = logging.getLogger(__name__)

# Type aliases for callback signatures
PositionCallback = Callable[[float], None]
"""Called with angle_deg (float) on every position update from the firmware."""

AckCallback = Callable[[str], None]
"""Called with ack_text (str) — the part after 'A:' — on every acknowledgment."""

SeekDoneCallback = Callable[[], None]
"""Called (no args) when the firmware reports A:SEEK_DONE."""

RawLineCallback = Callable[[str], None]
"""Called with the full line (str) for any unrecognised serial data."""


class SmartKnobDriver:
    """Thread-safe serial driver for the SmartKnob STM32 firmware.

    All public methods are safe to call from any thread (GUI main thread,
    background workers, etc.).  The reader loop runs in its own daemon
    thread and dispatches callbacks on that thread — if your callback
    touches GUI widgets, schedule it onto the GUI event loop yourself
    (e.g. ``root.after(0, callback)`` for Tkinter).

    Attributes:
        on_position:  Callback fired on every ``P<angle>`` line.
        on_ack:       Callback fired on every ``A:<text>`` line.
        on_seek_done: Callback fired when ``A:SEEK_DONE`` is received.
        on_raw:       Callback fired for lines that don't match P or A:.
    """

    # ------------------------------------------------------------------ #
    #  Construction
    # ------------------------------------------------------------------ #

    def __init__(self) -> None:
        self._serial: Optional[serial.Serial] = None
        self._lock: threading.Lock = threading.Lock()
        self._running: bool = False
        self._reader_thread: Optional[threading.Thread] = None

        # Public callbacks — assign your handlers before calling connect()
        self.on_position: Optional[PositionCallback] = None
        self.on_ack: Optional[AckCallback] = None
        self.on_seek_done: Optional[SeekDoneCallback] = None
        self.on_raw: Optional[RawLineCallback] = None

        # Last known position (thread-safe via _lock)
        self._current_angle: float = 0.0

    # ------------------------------------------------------------------ #
    #  Connection management
    # ------------------------------------------------------------------ #

    @staticmethod
    def list_ports() -> list[str]:
        """Return a list of available serial port names (e.g. ``['COM3', 'COM5']``)."""
        return [p.device for p in serial.tools.list_ports.comports()]

    @property
    def is_connected(self) -> bool:
        """True when the serial port is open and the reader thread is alive."""
        with self._lock:
            return (
                self._serial is not None
                and self._serial.is_open
                and self._running
            )

    @property
    def current_angle(self) -> float:
        """Last received angle in degrees (thread-safe read)."""
        with self._lock:
            return self._current_angle

    def connect(self, port: str) -> None:
        """Open *port* at 115 200 baud and start the reader thread.

        Args:
            port: Serial port name, e.g. ``"COM3"`` or ``"/dev/ttyACM0"``.

        Raises:
            serial.SerialException: If the port cannot be opened.
            RuntimeError: If already connected.
        """
        if self.is_connected:
            raise RuntimeError(f"Already connected — disconnect first")

        ser = serial.Serial(port, BAUD_RATE, timeout=SERIAL_TIMEOUT)

        with self._lock:
            self._serial = ser
            self._running = True

        self._reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True, name="smartknob-reader"
        )
        self._reader_thread.start()
        logger.info("Connected to %s", port)

    def disconnect(self) -> None:
        """Stop the reader thread and close the serial port."""
        with self._lock:
            self._running = False

        # Wait for reader to finish (short timeout to avoid deadlock)
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1.0)

        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.close()
            self._serial = None
            self._reader_thread = None

        logger.info("Disconnected")

    # ------------------------------------------------------------------ #
    #  Mode switching
    # ------------------------------------------------------------------ #

    def set_mode(self, mode: HapticMode) -> None:
        """Switch the firmware to *mode*.

        Args:
            mode: One of ``HapticMode.HAPTIC``, ``.INERTIA``,
                  ``.SPRING``, or ``.BOUNDED``.
        """
        self._send(mode.value)

    # ------------------------------------------------------------------ #
    #  Haptic parameters (affect HAPTIC and BOUNDED modes)
    # ------------------------------------------------------------------ #

    def set_detent_count(self, count: int) -> None:
        """Set number of detents per 360° rotation.

        Args:
            count: Detent count, 2–360. Firmware acks ``A:S<count>``.
        """
        self._send(f"{CMD_DETENT_COUNT}{count}")

    def set_detent_strength(self, volts: float) -> None:
        """Set detent snap strength.

        Args:
            volts: Voltage applied at detent center, typically 0.5–6.0 V.
        """
        self._send(f"{CMD_DETENT_STRENGTH}{volts:.2f}")

    # ------------------------------------------------------------------ #
    #  Inertia parameters
    # ------------------------------------------------------------------ #

    def set_inertia(self, virtual_mass: float) -> None:
        """Set the virtual flywheel mass (higher = heavier feel).

        Args:
            virtual_mass: Dimensionless mass, typically 1–20.
        """
        self._send(f"{CMD_INERTIA_VAL}{virtual_mass:.2f}")

    def set_damping(self, drag_coefficient: float) -> None:
        """Set drag / viscous damping (higher = more resistance when spinning).

        Args:
            drag_coefficient: Dimensionless, typically 0–5.
        """
        self._send(f"{CMD_DAMPING}{drag_coefficient:.2f}")

    def set_friction(self, static_friction: float) -> None:
        """Set static friction (minimum force to start spinning).

        Args:
            static_friction: Dimensionless, typically 0–1.
        """
        self._send(f"{CMD_FRICTION}{static_friction:.2f}")

    def set_coupling(self, spring_constant: float) -> None:
        """Set coupling spring between motor shaft and virtual flywheel.

        Args:
            spring_constant: Higher = stiffer link, typically 10–100.
        """
        self._send(f"{CMD_COUPLING}{spring_constant:.2f}")

    # ------------------------------------------------------------------ #
    #  Spring parameters
    # ------------------------------------------------------------------ #

    def set_spring_stiffness(self, volts_per_radian: float) -> None:
        """Set spring constant (how hard the knob snaps back to center).

        Args:
            volts_per_radian: Spring constant in V/rad, typically 0.5–30.
        """
        self._send(f"{CMD_SPRING_STIFFNESS}{volts_per_radian:.2f}")

    def set_spring_center(self, angle_deg: Optional[float] = None) -> None:
        """Set the spring's center position.

        Args:
            angle_deg: Center angle in degrees, or ``None`` to use the
                       current motor position.
        """
        if angle_deg is None:
            self._send(CMD_SPRING_CENTER)
        else:
            self._send(f"{CMD_SPRING_CENTER}{angle_deg:.1f}")

    def set_spring_damping(self, damping: float) -> None:
        """Set velocity damping for spring mode (prevents oscillation).

        Args:
            damping: Dimensionless coefficient, typically 0–2.
        """
        self._send(f"{CMD_SPRING_DAMPING}{damping:.2f}")

    # ------------------------------------------------------------------ #
    #  Bounded parameters
    # ------------------------------------------------------------------ #

    def set_lower_bound(self, angle_deg: float) -> None:
        """Set lower wall position for bounded mode.

        Args:
            angle_deg: Wall angle in degrees (e.g. -60).
        """
        self._send(f"{CMD_LOWER_BOUND}{angle_deg:.1f}")

    def set_upper_bound(self, angle_deg: float) -> None:
        """Set upper wall position for bounded mode.

        Args:
            angle_deg: Wall angle in degrees (e.g. 60).
        """
        self._send(f"{CMD_UPPER_BOUND}{angle_deg:.1f}")

    def set_wall_strength(self, volts_per_radian: float) -> None:
        """Set wall spring constant (how hard the walls push back).

        Args:
            volts_per_radian: Wall stiffness in V/rad, typically 1–30.
        """
        self._send(f"{CMD_WALL_STRENGTH}{volts_per_radian:.2f}")

    # ------------------------------------------------------------------ #
    #  Position commands
    # ------------------------------------------------------------------ #

    def query_position(self) -> None:
        """Request a single position report (response arrives via ``on_position``)."""
        self._send(CMD_QUERY_POS)

    def query_state(self) -> None:
        """Request a full state dump (response arrives via ``on_raw``)."""
        self._send(CMD_QUERY_STATE)

    def seek(self, angle_deg: float) -> None:
        """Command the motor to seek to *angle_deg* degrees.

        The firmware will acknowledge with ``A:Z<angle>`` immediately,
        then fire ``A:SEEK_DONE`` (and ``on_seek_done``) when settled.

        Args:
            angle_deg: Target position in degrees.
        """
        self._send(f"{CMD_SEEK}{angle_deg:.1f}")

    def seek_zero(self) -> None:
        """Shortcut: seek to 0° (sends ``Z0``)."""
        self._send(f"{CMD_SEEK}0")

    # ------------------------------------------------------------------ #
    #  Motor PID configuration
    # ------------------------------------------------------------------ #

    def set_pid_p(self, proportional_gain: float) -> None:
        """Set position PID proportional gain.

        Args:
            proportional_gain: P-term, typically 0–100 (default 50).
        """
        self._send(f"{CMD_MOTOR_PID_P}{proportional_gain:.2f}")

    def set_pid_i(self, integral_gain: float) -> None:
        """Set position PID integral gain.

        Args:
            integral_gain: I-term, typically 0–5 (default 0).
        """
        self._send(f"{CMD_MOTOR_PID_I}{integral_gain:.2f}")

    def set_pid_d(self, derivative_gain: float) -> None:
        """Set position PID derivative gain.

        Args:
            derivative_gain: D-term, typically 0–5 (default 0.3).
        """
        self._send(f"{CMD_MOTOR_PID_D}{derivative_gain:.2f}")

    def set_velocity_limit(self, radians_per_second: float) -> None:
        """Set maximum motor velocity during seeks.

        Args:
            radians_per_second: Velocity cap in rad/s, typically 0–100
                                (default 40).
        """
        self._send(f"{CMD_MOTOR_VEL_LIMIT}{radians_per_second:.2f}")

    # ------------------------------------------------------------------ #
    #  Convenience
    # ------------------------------------------------------------------ #

    @staticmethod
    def print_help() -> None:
        """Print protocol reference to stdout.  Delegates to ``protocol.print_help()``."""
        print_help()

    def send_raw(self, command: str) -> None:
        """Send an arbitrary ASCII command string (for advanced / debug use).

        A newline is appended automatically. The command is logged at
        DEBUG level.

        Args:
            command: Raw command text, e.g. ``"Q"`` or ``"Z45.0"``.
        """
        self._send(command)

    # ------------------------------------------------------------------ #
    #  Internal: send / receive
    # ------------------------------------------------------------------ #

    def _send(self, cmd: str) -> None:
        """Write *cmd* + newline to the serial port (thread-safe)."""
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.write(f"{cmd}\n".encode())
                logger.debug("TX: %s", cmd)

    def _reader_loop(self) -> None:
        """Background thread: continuously read lines and dispatch callbacks."""
        while True:
            with self._lock:
                if not self._running:
                    break
                ser = self._serial

            if ser is None:
                break

            try:
                if ser.in_waiting:
                    raw = ser.readline()
                    if raw:
                        line = raw.decode(errors="replace").strip()
                        if line:
                            self._process_line(line)
            except serial.SerialException as exc:
                logger.error("Serial read error: %s", exc)
                break
            except Exception as exc:  # noqa: BLE001
                logger.warning("Reader exception: %s", exc)

            time.sleep(0.01)

        logger.debug("Reader loop exited")

    def _process_line(self, line: str) -> None:
        """Parse a single firmware response line and fire the matching callback."""
        if line.startswith(RESP_POSITION) and len(line) > 1 and (line[1].isdigit() or line[1] == '-'):
            # Position update: P<angle_deg> (e.g., P60.12, P-30.5)
            try:
                angle = float(line[len(RESP_POSITION):])
                with self._lock:
                    self._current_angle = angle
                if self.on_position:
                    self.on_position(angle)
            except ValueError:
                logger.warning("Bad position line: %s", line)

        elif line == RESP_SEEK_DONE:
            # Seek completed — fire specific callback
            if self.on_seek_done:
                self.on_seek_done()
            if self.on_ack:
                self.on_ack("SEEK_DONE")

        elif line.startswith(RESP_ACK):
            # General acknowledgment: A:<text>
            ack_text = line[len(RESP_ACK):]
            if self.on_ack:
                self.on_ack(ack_text)

        else:
            # Unrecognised — forward to raw callback
            if self.on_raw:
                self.on_raw(line)
