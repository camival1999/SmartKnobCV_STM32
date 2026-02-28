"""
Windows Volume Control Module

Uses pycaw to interface with Windows Core Audio API.
Requires: pip install pycaw comtypes
"""

from pycaw.pycaw import AudioUtilities


class VolumeController:
    """Controls Windows system volume via Core Audio API."""
    
    def __init__(self):
        """Initialize connection to default audio endpoint."""
        devices = AudioUtilities.GetSpeakers()
        self._volume = devices.EndpointVolume
    
    def get_volume(self) -> float:
        """
        Get current master volume level.
        
        Returns:
            float: Volume level from 0.0 (silent) to 1.0 (max)
        """
        return self._volume.GetMasterVolumeLevelScalar()
    
    def set_volume(self, level: float) -> None:
        """
        Set master volume level.
        
        Args:
            level: Volume level from 0.0 (silent) to 1.0 (max).
                   Values outside range are clamped.
        """
        level = max(0.0, min(1.0, level))
        self._volume.SetMasterVolumeLevelScalar(level, None)
    
    def get_volume_percent(self) -> int:
        """
        Get current volume as integer percentage.
        
        Returns:
            int: Volume percentage 0-100
        """
        return int(round(self.get_volume() * 100))
    
    def set_volume_percent(self, percent: int) -> None:
        """
        Set volume from integer percentage.
        
        Args:
            percent: Volume percentage 0-100
        """
        self.set_volume(percent / 100.0)
    
    def get_mute(self) -> bool:
        """
        Check if audio is muted.
        
        Returns:
            bool: True if muted, False otherwise
        """
        return bool(self._volume.GetMute())
    
    def set_mute(self, mute: bool) -> None:
        """
        Set mute state.
        
        Args:
            mute: True to mute, False to unmute
        """
        self._volume.SetMute(int(mute), None)
    
    def toggle_mute(self) -> bool:
        """
        Toggle mute state.
        
        Returns:
            bool: New mute state after toggle
        """
        new_state = not self.get_mute()
        self.set_mute(new_state)
        return new_state


# Quick test when run directly
if __name__ == "__main__":
    vc = VolumeController()
    print(f"Current volume: {vc.get_volume_percent()}%")
    print(f"Muted: {vc.get_mute()}")
