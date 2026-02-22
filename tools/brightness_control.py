"""
Windows Brightness Control Module

Uses WMI to interface with display brightness.
Works on most laptops with integrated displays.
Requires: pip install wmi

Note: This typically only works on laptops/tablets with built-in displays.
External monitors usually don't support software brightness control.
"""

import wmi


class BrightnessController:
    """Controls Windows display brightness via WMI."""
    
    def __init__(self):
        """Initialize connection to WMI brightness interface."""
        self._wmi = wmi.WMI(namespace='wmi')
        self._methods = None
        self._available = False
        
        # Check if brightness control is available
        try:
            methods = self._wmi.WmiMonitorBrightnessMethods()
            if methods:
                self._methods = methods[0]
                self._available = True
        except Exception:
            self._available = False
    
    @property
    def available(self) -> bool:
        """Check if brightness control is available on this system."""
        return self._available
    
    def get_brightness(self) -> int:
        """
        Get current display brightness.
        
        Returns:
            int: Brightness level 0-100, or -1 if not available
        """
        if not self._available:
            return -1
        
        try:
            brightness = self._wmi.WmiMonitorBrightness()[0]
            return brightness.CurrentBrightness
        except Exception:
            return -1
    
    def set_brightness(self, level: int) -> bool:
        """
        Set display brightness.
        
        Args:
            level: Brightness level 0-100
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._available:
            return False
        
        try:
            level = max(0, min(100, level))
            self._methods.WmiSetBrightness(level, 0)
            return True
        except Exception:
            return False
    
    def get_brightness_float(self) -> float:
        """
        Get current brightness as float 0.0-1.0.
        
        Returns:
            float: Brightness 0.0-1.0, or -1.0 if not available
        """
        b = self.get_brightness()
        return b / 100.0 if b >= 0 else -1.0
    
    def set_brightness_float(self, level: float) -> bool:
        """
        Set brightness from float 0.0-1.0.
        
        Args:
            level: Brightness 0.0-1.0
        
        Returns:
            bool: True if successful
        """
        return self.set_brightness(int(round(level * 100)))


# Quick test when run directly
if __name__ == "__main__":
    bc = BrightnessController()
    if bc.available:
        print(f"Brightness control available")
        print(f"Current brightness: {bc.get_brightness()}%")
    else:
        print("Brightness control not available on this system")
        print("(This typically only works on laptops with built-in displays)")
