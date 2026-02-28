"""
SmartKnob — Cross-platform serial driver for the SmartKnob haptic controller.

Provides:
- SmartKnobDriver: Thread-safe serial communication with the STM32 firmware
- HapticMode: Enum of available haptic modes
- print_help(): Quick protocol reference

For Windows integrations (volume, brightness, scroll, zoom), see smartknob_windows.
"""

__version__ = "0.0.3"

from smartknob.driver import SmartKnobDriver
from smartknob.protocol import HapticMode, print_help

__all__ = ["SmartKnobDriver", "HapticMode", "print_help"]
