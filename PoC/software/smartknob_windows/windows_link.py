"""
Windows Link Module

Manages the connection between SmartKnob motor position and Windows system functions.
"""

import time
from smartknob_windows.integrations.volume import VolumeController
from smartknob_windows.integrations.brightness import BrightnessController
from smartknob_windows.integrations.scroll import scroll_smooth, WHEEL_DELTA
from smartknob_windows.integrations.zoom import ZoomController, MIN_ZOOM, MAX_ZOOM


class WindowsLink:
    """
    Links motor position to Windows functions.
    
    Supports:
    - System Volume: Maps bounded mode (-60° to +60°) to volume (0-100%)
    - Display Brightness: Maps bounded mode (-60° to +60°) to brightness (0-100%)
    - Mouse Scroll: Maps inertia mode rotation to smooth scroll (infinite rotation)
    - Screen Zoom: Maps spring mode displacement to zoom rate (100-800%)
    """
    
    # Angle bounds for bounded mode (must match firmware defaults)
    BOUND_MIN_DEG = -60.0
    BOUND_MAX_DEG = 60.0
    ANGLE_RANGE = BOUND_MAX_DEG - BOUND_MIN_DEG  # 120°
    
    # Smooth scroll: degrees per WHEEL_DELTA (120 units = 1 line)
    # Lower value = more sensitive. 6° means 60 lines per revolution (360/6)
    SCROLL_DEGREES_PER_LINE = 6.0  # ~60 lines per revolution
    # Convert to units per degree for smooth scrolling
    SCROLL_UNITS_PER_DEGREE = WHEEL_DELTA / SCROLL_DEGREES_PER_LINE  # 20 units/deg
    
    # Zoom: displacement-to-rate mapping (Spring mode)
    # Smooth zoom using Magnification API
    ZOOM_DEAD_ZONE = 5.0  # Degrees - no zoom change within this range
    ZOOM_MAX_DISPLACEMENT = 45.0  # Full deflection = fastest zoom
    ZOOM_MAX_RATE = 0.05  # Zoom factor change per update at max displacement
    
    def __init__(self):
        """Initialize with no active link."""
        self.active_function = None  # "volume", "brightness", "scroll", "zoom", or None
        self._volume_ctrl = None
        self._brightness_ctrl = None
        self._zoom_ctrl = None
        
        # Scroll tracking state
        self._last_angle = None
        self._scroll_accumulator = 0.0
        self._last_time = None
        
        # Zoom tracking state
        self._current_zoom = 1.0  # Track as factor (1.0 = 100%)
        self._current_zoom = 100  # Track as percentage
        self._last_zoom_time = 0.0  # For rate limiting
    
    def _ensure_volume_controller(self) -> VolumeController:
        """Lazy initialization of volume controller."""
        if self._volume_ctrl is None:
            self._volume_ctrl = VolumeController()
        return self._volume_ctrl
    
    def _ensure_brightness_controller(self) -> BrightnessController:
        """Lazy initialization of brightness controller."""
        if self._brightness_ctrl is None:
            self._brightness_ctrl = BrightnessController()
        return self._brightness_ctrl
    
    def _ensure_zoom_controller(self) -> ZoomController:
        """Lazy initialization of zoom controller."""
        if self._zoom_ctrl is None:
            self._zoom_ctrl = ZoomController()
        return self._zoom_ctrl
    
    def is_brightness_available(self) -> bool:
        """Check if brightness control is available on this system."""
        bc = self._ensure_brightness_controller()
        return bc.available
    
    def is_zoom_available(self) -> bool:
        """Check if zoom control is available on this system."""
        zc = self._ensure_zoom_controller()
        return zc.available
    
    @property
    def is_linked(self) -> bool:
        """Check if any Windows function is currently linked."""
        return self.active_function is not None
    
    def link_volume(self) -> float:
        """
        Link to Windows system volume.
        
        Returns:
            float: Target angle (degrees) matching current volume.
                   Motor should seek to this position before entering bounded mode.
        """
        vc = self._ensure_volume_controller()
        volume = vc.get_volume()  # 0.0 to 1.0
        
        # Calculate angle that represents current volume
        angle = self.BOUND_MIN_DEG + (volume * self.ANGLE_RANGE)
        
        self.active_function = "volume"
        return angle
    
    def link_brightness(self) -> float:
        """
        Link to Windows display brightness.
        
        Returns:
            float: Target angle (degrees) matching current brightness.
                   Motor should seek to this position before entering bounded mode.
        
        Raises:
            RuntimeError: If brightness control is not available
        """
        bc = self._ensure_brightness_controller()
        if not bc.available:
            raise RuntimeError("Brightness control not available on this system")
        
        brightness = bc.get_brightness_float()  # 0.0 to 1.0
        
        # Calculate angle that represents current brightness
        angle = self.BOUND_MIN_DEG + (brightness * self.ANGLE_RANGE)
        
        self.active_function = "brightness"
        return angle
    
    def link_scroll(self, sensitivity: float = None) -> None:
        """
        Link to mouse scroll wheel (smooth scrolling mode).
        
        Uses Inertia mode - maps rotation delta directly to scroll events.
        Sends high-resolution scroll units for smooth continuous scrolling.
        
        Args:
            sensitivity: Degrees per line (default: 6.0 = 60 lines/rev).
                         Lower = more sensitive.
        """
        if sensitivity is not None:
            self.SCROLL_DEGREES_PER_LINE = sensitivity
            self.SCROLL_UNITS_PER_DEGREE = WHEEL_DELTA / sensitivity
        
        # Reset scroll tracking state
        self._last_angle = None
        self._scroll_accumulator = 0.0
        self._last_time = time.time()
        
        self.active_function = "scroll"
    
    def link_zoom(self) -> None:
        """
        Link to screen zoom (Fullscreen Magnifier).
        
        Uses Spring mode - displacement from center controls zoom rate:
        - Center (0°): Hold current zoom
        - CW rotation: Zoom in (rate proportional to displacement)
        - CCW rotation: Zoom out (stops at 100%)
        
        Smooth zoom using the Magnification API.
        """
        zc = self._ensure_zoom_controller()
        if not zc.available:
            raise RuntimeError("Zoom control not available on this system")
        
        # Initialize the Magnification API
        if not zc.initialize():
            raise RuntimeError("Failed to initialize Magnification API")
        
        # Get current zoom level (as factor 1.0-8.0)
        self._current_zoom = zc.get_zoom()
        
        self.active_function = "zoom"
    
    def unlink(self) -> None:
        """Disconnect from Windows function and clean up."""
        # Reset zoom to 100% and close magnifier if zoom was active
        if self.active_function == "zoom" and self._zoom_ctrl is not None:
            self._zoom_ctrl.reset()  # Resets to 100% and uninitializes
        
        self.active_function = None
        self._last_angle = None
        self._scroll_accumulator = 0.0
    
    def get_current_volume_percent(self) -> int:
        """
        Get current Windows volume as percentage.
        
        Returns:
            int: Volume 0-100, or -1 if not available
        """
        try:
            vc = self._ensure_volume_controller()
            return vc.get_volume_percent()
        except Exception:
            return -1
    
    def get_current_brightness_percent(self) -> int:
        """
        Get current display brightness as percentage.
        
        Returns:
            int: Brightness 0-100, or -1 if not available
        """
        try:
            bc = self._ensure_brightness_controller()
            return bc.get_brightness()
        except Exception:
            return -1
    
    def get_current_zoom_percent(self) -> int:
        """
        Get current screen zoom as percentage.
        
        Returns:
            int: Zoom percent (100 = normal, 200 = 2x), or -1 if not available
        """
        try:
            zc = self._ensure_zoom_controller()
            return zc.get_zoom_percent()
        except Exception:
            return -1
    
    def reset_zoom(self) -> bool:
        """
        Reset screen zoom to 100%.
        
        Returns:
            bool: True if successful
        """
        try:
            zc = self._ensure_zoom_controller()
            return zc.reset()
        except Exception:
            return False
    
    def process_position(self, angle_deg: float) -> dict | None:
        """
        Process a motor position update.
        
        If linked to a Windows function, updates that function based on angle.
        
        Args:
            angle_deg: Current motor position in degrees
        
        Returns:
            dict with function-specific info, or None if not linked.
            For volume: {"function": "volume", "percent": int}
            For brightness: {"function": "brightness", "percent": int}
            For scroll: {"function": "scroll", "units": int, "direction": str}
            For zoom: {"function": "zoom", "percent": int, "action": str}
        """
        if self.active_function == "volume":
            return self._process_volume(angle_deg)
        elif self.active_function == "brightness":
            return self._process_brightness(angle_deg)
        elif self.active_function == "scroll":
            return self._process_scroll(angle_deg)
        elif self.active_function == "zoom":
            return self._process_zoom(angle_deg)
        return None
    
    def _process_volume(self, angle_deg: float) -> dict:
        """
        Convert angle to volume and set Windows volume.
        
        Args:
            angle_deg: Motor position in degrees
        
        Returns:
            dict: {"function": "volume", "percent": int}
        """
        # Clamp angle to bounds
        angle = max(self.BOUND_MIN_DEG, min(self.BOUND_MAX_DEG, angle_deg))
        
        # Convert angle to volume (0.0 to 1.0)
        volume = (angle - self.BOUND_MIN_DEG) / self.ANGLE_RANGE
        
        # Set Windows volume
        vc = self._ensure_volume_controller()
        vc.set_volume(volume)
        
        return {
            "function": "volume",
            "percent": int(round(volume * 100))
        }
    
    def _process_brightness(self, angle_deg: float) -> dict:
        """
        Convert angle to brightness and set display brightness.
        
        Args:
            angle_deg: Motor position in degrees
        
        Returns:
            dict: {"function": "brightness", "percent": int}
        """
        # Clamp angle to bounds
        angle = max(self.BOUND_MIN_DEG, min(self.BOUND_MAX_DEG, angle_deg))
        
        # Convert angle to brightness (0.0 to 1.0)
        brightness = (angle - self.BOUND_MIN_DEG) / self.ANGLE_RANGE
        
        # Set display brightness
        bc = self._ensure_brightness_controller()
        bc.set_brightness_float(brightness)
        
        return {
            "function": "brightness",
            "percent": int(round(brightness * 100))
        }
    
    def _process_scroll(self, angle_deg: float) -> dict:
        """
        Convert rotation delta to smooth scroll events.
        
        Sends high-resolution scroll units directly proportional to rotation.
        This provides smooth, continuous scrolling in supporting applications.
        
        Args:
            angle_deg: Current motor position in degrees
        
        Returns:
            dict: {"function": "scroll", "units": int, "direction": str}
        """
        # Initialize on first call
        if self._last_angle is None:
            self._last_angle = angle_deg
            return {"function": "scroll", "units": 0, "direction": "none"}
        
        # Calculate delta (supports infinite rotation)
        delta = angle_deg - self._last_angle
        self._last_angle = angle_deg
        
        # Skip tiny movements
        if abs(delta) < 0.1:
            return {"function": "scroll", "units": 0, "direction": "none"}
        
        # Convert degrees to scroll units (smooth, fractional accumulation)
        self._scroll_accumulator += delta * self.SCROLL_UNITS_PER_DEGREE
        
        # Get integer units to send (keep remainder for smooth accumulation)
        units = int(self._scroll_accumulator)
        
        if units != 0:
            # Fire smooth scroll event
            scroll_smooth(units)
            
            # Remove sent units from accumulator (keep fraction)
            self._scroll_accumulator -= units
        
        return {
            "function": "scroll",
            "units": units,
            "direction": "up" if units > 0 else ("down" if units < 0 else "none")
        }
    
    def _process_zoom(self, angle_deg: float) -> dict:
        """
        Convert spring displacement to smooth zoom rate.
        
        Displacement from center controls zoom rate:
        - Center (within dead zone): Hold current zoom
        - CW (positive): Zoom in, rate proportional to displacement
        - CCW (negative): Zoom out, rate proportional to displacement
        
        Args:
            angle_deg: Current motor position in degrees (0 = spring center)
        
        Returns:
            dict: {"function": "zoom", "percent": int, "action": str}
        """
        # Apply dead zone at center
        if abs(angle_deg) < self.ZOOM_DEAD_ZONE:
            return {
                "function": "zoom",
                "percent": int(round(self._current_zoom * 100)),
                "action": "hold"
            }
        
        # Calculate displacement beyond dead zone
        if angle_deg > 0:
            displacement = angle_deg - self.ZOOM_DEAD_ZONE
        else:
            displacement = angle_deg + self.ZOOM_DEAD_ZONE
        
        # Normalize displacement to [-1, 1] range
        normalized = displacement / (self.ZOOM_MAX_DISPLACEMENT - self.ZOOM_DEAD_ZONE)
        normalized = max(-1.0, min(1.0, normalized))
        
        # Calculate zoom rate (factor change per update)
        rate = normalized * self.ZOOM_MAX_RATE
        
        # Apply smooth zoom change
        new_zoom = self._current_zoom + rate
        
        # Clamp: can't go below 100%, max at 800%
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))
        
        # Only update if changed significantly
        if abs(new_zoom - self._current_zoom) > 0.001:
            zc = self._ensure_zoom_controller()
            zc.set_zoom(new_zoom)
            self._current_zoom = new_zoom
        
        # Determine action string
        if rate > 0.001:
            action = "zoom_in"
        elif rate < -0.001:
            action = "zoom_out"
        else:
            action = "hold"
        
        return {
            "function": "zoom",
            "percent": int(round(self._current_zoom * 100)),
            "action": action
        }
    
    def update_bounds(self, lower_deg: float, upper_deg: float) -> None:
        """
        Update angle bounds to match motor configuration.
        
        Call this if user changes bounded mode limits in the GUI.
        
        Args:
            lower_deg: Lower bound in degrees
            upper_deg: Upper bound in degrees
        """
        self.BOUND_MIN_DEG = lower_deg
        self.BOUND_MAX_DEG = upper_deg
        self.ANGLE_RANGE = upper_deg - lower_deg


# Quick test when run directly
if __name__ == "__main__":
    link = WindowsLink()
    print(f"Is linked: {link.is_linked}")
    
    # Test volume
    angle = link.link_volume()
    print(f"\nLinked to volume. Seek to: {angle:.1f}°")
    print(f"Current volume: {link.get_current_volume_percent()}%")
    
    result = link.process_position(0.0)
    print(f"Position 0° → {result}")
    
    link.unlink()
    
    # Test brightness
    print(f"\nBrightness available: {link.is_brightness_available()}")
    if link.is_brightness_available():
        angle = link.link_brightness()
        print(f"Linked to brightness. Seek to: {angle:.1f}°")
        print(f"Current brightness: {link.get_current_brightness_percent()}%")
        
        result = link.process_position(0.0)
        print(f"Position 0° → {result}")
        
        link.unlink()
    
    # Test scroll (smooth mode)
    print(f"\nTesting smooth scroll link...")
    link.link_scroll()
    print(f"Linked to smooth scroll: {link.SCROLL_DEGREES_PER_LINE}°/line ({link.SCROLL_UNITS_PER_DEGREE:.1f} units/°)")
    
    # Simulate rotation
    result = link.process_position(0.0)
    print(f"Position 0° → {result}")
    
    result = link.process_position(3.0)  # +3° = ~60 units (half a line)
    print(f"Position 3° → {result}")
    
    result = link.process_position(9.0)  # +6° more = ~120 units (1 full line)
    print(f"Position 9° → {result}")
    
    link.unlink()
    
    # Test zoom
    print(f"\nZoom available: {link.is_zoom_available()}")
    if link.is_zoom_available():
        print("Testing zoom link (Spring mode)...")
        link.link_zoom()
        print(f"Linked to zoom. Current: {link.get_current_zoom_percent()}%")
        
        # Simulate spring position updates
        print("  Center (0°) - should hold:")
        result = link.process_position(0.0)
        print(f"    → {result}")
        
        print("  CW +20° - should zoom in:")
        for _ in range(5):
            result = link.process_position(20.0)
        print(f"    → {result}")
        
        print("  Back to center - should hold:")
        result = link.process_position(0.0)
        print(f"    → {result}")
        
        print("  CCW -20° - should zoom out:")
        for _ in range(5):
            result = link.process_position(-20.0)
        print(f"    → {result}")
        
        print("  Resetting zoom to 100%...")
        link.reset_zoom()
        print(f"  Current zoom: {link.get_current_zoom_percent()}%")
        
        link.unlink()
    
    print(f"\nUnlinked. Is linked: {link.is_linked}")
