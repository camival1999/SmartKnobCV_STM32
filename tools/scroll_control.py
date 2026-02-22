"""
scroll_control.py

Scrolls mouse wheel via simulated input events with Windows API (ctypes).

Cross-platform fallback available via subprocess/clip (not implemented here).
"""

import ctypes
from ctypes import wintypes


# Windows constants for SendInput
INPUT_MOUSE = 0
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x01000  # Horizontal scroll (if needed in future)
WHEEL_DELTA = 120  # Standard scroll increment


class MOUSEINPUT(ctypes.Structure):
    """Structure for mouse input events."""
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    """Structure for SendInput."""
    _fields_ = [
        ("type", wintypes.DWORD),
        ("mi", MOUSEINPUT),
    ]


def scroll(delta: int) -> None:
    """
    Send a mouse wheel scroll event.
    
    Args:
        delta: Scroll amount. Positive = scroll up, negative = scroll down.
               Standard unit is 120 (WHEEL_DELTA) per notch.
    
    Example:
        scroll(120)   # Scroll up one notch
        scroll(-120)  # Scroll down one notch
        scroll(360)   # Scroll up three notches
    """
    if delta == 0:
        return
    
    # Build mouse input structure
    extra = ctypes.pointer(ctypes.c_ulong(0))
    mi = MOUSEINPUT(0, 0, delta, MOUSEEVENTF_WHEEL, 0, extra)
    inp = INPUT(INPUT_MOUSE, mi)
    
    # Send the input
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def scroll_ticks(ticks: int) -> None:
    """
    Scroll by a number of standard ticks (notches).
    
    Args:
        ticks: Number of scroll ticks. Positive = up, negative = down.
    
    Example:
        scroll_ticks(1)   # Scroll up one tick
        scroll_ticks(-3)  # Scroll down three ticks
    """
    scroll(ticks * WHEEL_DELTA)


def scroll_smooth(delta: int) -> None:
    """
    Send high-resolution (smooth) scroll event.
    
    Unlike scroll_ticks(), this sends raw delta units allowing sub-line
    precision. Apps that support smooth scrolling (browsers, modern Win apps)
    will scroll smoothly. Legacy apps accumulate until reaching 120 (WHEEL_DELTA).
    
    For smooth scrolling, call frequently with small values (e.g., 10-30).
    
    Args:
        delta: Raw scroll units. Positive = up, negative = down.
               120 = 1 traditional line. Use smaller values for smooth scroll.
    
    Example:
        scroll_smooth(30)   # 1/4 of a line (smooth)
        scroll_smooth(-15)  # 1/8 of a line down (very smooth)
    """
    scroll(delta)


# Quick test
if __name__ == "__main__":
    import time
    
    print("Scroll control test")
    print(f"WHEEL_DELTA = {WHEEL_DELTA} (standard line scroll)")
    print()
    
    # Test traditional scrolling
    print("[Traditional] Will scroll down 3 ticks in 2 seconds...")
    time.sleep(2)
    
    for i in range(3):
        scroll_ticks(-1)
        print(f"  Tick {i + 1}: -120 units")
        time.sleep(0.15)
    
    print()
    print("[Smooth] Will scroll up smoothly in 1 second...")
    time.sleep(1)
    
    # Smooth scroll: 12 small increments = same as 3 ticks but smoother
    for i in range(12):
        scroll_smooth(30)  # 30 * 12 = 360 = 3 ticks worth
        print(f"  Smooth {i + 1}: +30 units")
        time.sleep(0.05)
    
    print()
    print("Test complete. Smooth scrolling should feel more fluid!")
