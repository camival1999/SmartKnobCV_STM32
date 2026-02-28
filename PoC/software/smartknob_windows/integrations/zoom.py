"""
zoom_control.py

Controls Windows screen zoom using the Magnification API for smooth fullscreen zoom.

The Magnification API (Magnification.dll) provides smooth zoom from 1.0x to 8.0x.
"""

import ctypes
from ctypes import wintypes


# Load User32 for cursor position and screen dimensions
user32 = ctypes.WinDLL("user32", use_last_error=True)

# Screen dimension constants for GetSystemMetrics
SM_CXSCREEN = 0  # Primary screen width
SM_CYSCREEN = 1  # Primary screen height

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

def _get_cursor_pos():
    """Get the current mouse cursor position."""
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def _get_screen_size():
    """Get the primary screen dimensions."""
    width = user32.GetSystemMetrics(SM_CXSCREEN)
    height = user32.GetSystemMetrics(SM_CYSCREEN)
    return width, height


# Load the Magnification DLL
try:
    magnification = ctypes.WinDLL("Magnification.dll")
    _API_AVAILABLE = True
except OSError:
    magnification = None
    _API_AVAILABLE = False


# Constants
MIN_ZOOM = 1.0   # 100% - normal view
MAX_ZOOM = 8.0   # 800% - maximum zoom


def _init_api():
    """Initialize Magnification API function signatures."""
    if not _API_AVAILABLE:
        return False
    
    # BOOL MagInitialize(void)
    magnification.MagInitialize.restype = wintypes.BOOL
    magnification.MagInitialize.argtypes = []
    
    # BOOL MagUninitialize(void)
    magnification.MagUninitialize.restype = wintypes.BOOL
    magnification.MagUninitialize.argtypes = []
    
    # BOOL MagSetFullscreenTransform(float magnificationFactor, int xOffset, int yOffset)
    magnification.MagSetFullscreenTransform.restype = wintypes.BOOL
    magnification.MagSetFullscreenTransform.argtypes = [
        ctypes.c_float,  # magnification factor
        ctypes.c_int,    # x offset (center point)
        ctypes.c_int,    # y offset (center point)
    ]
    
    # BOOL MagGetFullscreenTransform(float* pMagnificationFactor, int* pxOffset, int* pyOffset)
    magnification.MagGetFullscreenTransform.restype = wintypes.BOOL
    magnification.MagGetFullscreenTransform.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
    ]
    
    return True


class ZoomController:
    """
    Controls Windows screen magnification with smooth zoom.
    
    Uses the Magnification API for fullscreen zoom.
    Zoom range: 1.0 (100%) to 8.0 (800%)
    """
    
    def __init__(self):
        """Initialize the zoom controller."""
        self._initialized = False
        self._current_zoom = 1.0
        self.available = _API_AVAILABLE
        
        if _API_AVAILABLE:
            _init_api()
    
    def initialize(self) -> bool:
        """
        Initialize the Magnification API.
        
        Must be called before using zoom functions.
        
        Returns:
            bool: True if successful
        """
        if not self.available:
            return False
        
        if self._initialized:
            return True
        
        result = magnification.MagInitialize()
        self._initialized = bool(result)
        
        if self._initialized:
            # Read current zoom level
            self._current_zoom = self._read_zoom()
        
        return self._initialized
    
    def uninitialize(self) -> bool:
        """
        Clean up the Magnification API.
        
        Resets zoom to 100% before uninitializing.
        
        Returns:
            bool: True if successful
        """
        if not self._initialized:
            return True
        
        # Reset zoom to 1.0 (normal) using direct API call to avoid recursion
        magnification.MagSetFullscreenTransform(
            ctypes.c_float(1.0),
            ctypes.c_int(0),
            ctypes.c_int(0)
        )
        self._current_zoom = 1.0
        
        result = magnification.MagUninitialize()
        self._initialized = False
        return bool(result)
    
    def _read_zoom(self) -> float:
        """Read current zoom level from the API."""
        if not self._initialized:
            return 1.0
        
        factor = ctypes.c_float()
        x = ctypes.c_int()
        y = ctypes.c_int()
        
        result = magnification.MagGetFullscreenTransform(
            ctypes.byref(factor),
            ctypes.byref(x),
            ctypes.byref(y)
        )
        
        if result:
            return factor.value
        return self._current_zoom
    
    def get_zoom(self) -> float:
        """
        Get current zoom level.
        
        Returns:
            float: Zoom factor (1.0 = 100%, 2.0 = 200%, etc.)
        """
        if self._initialized:
            self._current_zoom = self._read_zoom()
        return self._current_zoom
    
    def get_zoom_percent(self) -> int:
        """
        Get current zoom as percentage.
        
        Returns:
            int: Zoom percentage (100 = normal, 200 = 2x, etc.)
        """
        return int(round(self.get_zoom() * 100))
    
    def set_zoom(self, factor: float, follow_cursor: bool = True) -> bool:
        """
        Set the screen zoom level (smooth).
        
        Can set any value between 1.0 and 8.0 for smooth zoom.
        Automatically initializes the API if needed.
        
        Args:
            factor: Zoom factor (1.0 = 100%, 2.0 = 200%, etc.)
                    Clamped to MIN_ZOOM (1.0) and MAX_ZOOM (8.0)
            follow_cursor: If True, zoom centers on current mouse position
        
        Returns:
            bool: True if successful
        """
        # Clamp to valid range
        factor = max(MIN_ZOOM, min(MAX_ZOOM, factor))
        
        # If returning to 100%, uninitialize (closes magnifier cleanly)
        if factor <= MIN_ZOOM:
            if self._initialized:
                self._current_zoom = 1.0
                return self.uninitialize()
            return True
        
        # Auto-initialize if needed
        if not self._initialized:
            if not self.initialize():
                return False
        
        # Calculate offset to center zoom on cursor position
        # The API offset is the top-left of the visible magnified area
        # To center on cursor: offset = cursor - (screen_size / 2 / factor)
        if follow_cursor:
            cursor_x, cursor_y = _get_cursor_pos()
            screen_w, screen_h = _get_screen_size()
            
            # Calculate offset to place cursor at center of view
            offset_x = int(cursor_x - (screen_w / 2.0 / factor))
            offset_y = int(cursor_y - (screen_h / 2.0 / factor))
        else:
            offset_x, offset_y = 0, 0
        
        result = magnification.MagSetFullscreenTransform(
            ctypes.c_float(factor),
            ctypes.c_int(offset_x),
            ctypes.c_int(offset_y)
        )
        
        if result:
            self._current_zoom = factor
            return True
        return False
    
    def set_zoom_percent(self, percent: int) -> bool:
        """
        Set zoom as percentage.
        
        Args:
            percent: Zoom percentage (100 = normal, 200 = 2x)
        
        Returns:
            bool: True if successful
        """
        return self.set_zoom(percent / 100.0)
    
    def zoom_in(self, amount: float = 0.1) -> float:
        """
        Increase zoom by amount.
        
        Args:
            amount: Zoom factor increase (default 0.1 = 10%)
        
        Returns:
            float: New zoom level
        """
        new_zoom = min(MAX_ZOOM, self._current_zoom + amount)
        self.set_zoom(new_zoom)
        return self._current_zoom
    
    def zoom_out(self, amount: float = 0.1) -> float:
        """
        Decrease zoom by amount (clamped at 100%).
        
        Args:
            amount: Zoom factor decrease (default 0.1 = 10%)
        
        Returns:
            float: New zoom level
        """
        new_zoom = max(MIN_ZOOM, self._current_zoom - amount)
        self.set_zoom(new_zoom)
        return self._current_zoom
    
    def reset(self) -> bool:
        """
        Reset zoom to 100% and close magnifier.
        
        Returns:
            bool: True if successful
        """
        self._current_zoom = 1.0
        if self._initialized:
            return self.uninitialize()
        return True
    
    def __del__(self):
        """Clean up on destruction."""
        if self._initialized:
            try:
                self.uninitialize()
            except Exception:
                pass


# Quick test
if __name__ == "__main__":
    import time
    
    print("Smooth Zoom Control Test")
    print(f"API available: {_API_AVAILABLE}")
    print()
    
    if not _API_AVAILABLE:
        print("ERROR: Magnification.dll not available")
        exit(1)
    
    zc = ZoomController()
    
    print("Initializing Magnification API...")
    if not zc.initialize():
        print("ERROR: Failed to initialize Magnification API")
        exit(1)
    
    print(f"Current zoom: {zc.get_zoom_percent()}%")
    print()
    
    # Test smooth zoom
    print("Testing smooth zoom in (10 steps)...")
    for i in range(10):
        zc.set_zoom(1.0 + i * 0.1)
        print(f"  Zoom: {zc.get_zoom_percent()}%")
        time.sleep(0.1)
    
    print()
    print("Holding at 200% for 2 seconds...")
    time.sleep(2)
    
    print()
    print("Smooth zoom out...")
    for i in range(10, 0, -1):
        zc.set_zoom(1.0 + (i-1) * 0.1)
        print(f"  Zoom: {zc.get_zoom_percent()}%")
        time.sleep(0.1)
    
    print()
    print("Cleaning up...")
    zc.uninitialize()
    print("Test complete!")
