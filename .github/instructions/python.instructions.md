---
description: 'Python development standards for the SmartKnob software package'
applyTo: '**/*.py'
lastUpdated: 2026-02-28
---
<!-- Owner: SmartKnobCV_STM32 | Last updated: 2026-02-28 -->
# Python Standards — SmartKnob Software

Standards for all Python code in the `PoC/software/` package.

---

## Package Structure

```
PoC/software/
├── pyproject.toml                  # Package metadata + dependencies
├── requirements.txt                # Pip-compatible dependency list
├── gui/
│   └── app.py                      # Tkinter GUI application
├── smartknob/
│   ├── __init__.py                 # Package init (version, exports)
│   ├── windows_link.py             # Windows integration orchestrator
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── volume.py               # Volume control (pycaw)
│   │   ├── brightness.py           # Brightness control (WMI)
│   │   ├── scroll.py               # Scroll emulation (ctypes)
│   │   └── zoom.py                 # Magnification API (ctypes)
│   └── context/
│       └── __init__.py             # Context-aware switching (Phase 2)
├── config/
│   ├── presets.json                # Haptic preset definitions
│   └── contexts.json               # App-to-preset mappings
└── tests/                          # Test suite (future)
```

---

## Import Conventions

### Package imports (preferred)

```python
from smartknob.windows_link import WindowsLink
from smartknob.integrations.volume import VolumeController
from smartknob.integrations.brightness import BrightnessController
```

### Running the GUI

The GUI must be run from the `PoC/software/` directory so the `smartknob` package is importable:

```bash
cd PoC/software
python gui/app.py
```

Or with the package installed in dev mode: `pip install -e .`

---

## Integration Module Pattern

Each Windows integration follows this pattern:

```python
class XxxController:
    """Controls [system function] via [Windows API]."""
    
    def __init__(self):
        """Initialize the controller. May raise on unsupported systems."""
        pass
    
    def get_value(self) -> float:
        """Get current value (0.0 - 1.0 normalized)."""
        pass
    
    def set_value(self, value: float) -> None:
        """Set value (0.0 - 1.0 normalized)."""
        pass
```

- Normalize all values to 0.0–1.0 range
- Handle `ImportError` gracefully for platform-specific dependencies
- Include `try/except` around initialization for unsupported hardware

---

## Dependencies

| Package | Purpose | Platform |
|---------|---------|----------|
| `pyserial` | Serial communication with STM32 | All |
| `pycaw` | Windows audio volume control | Windows only |
| `comtypes` | COM interface support (pycaw dep) | Windows only |
| `wmi` | WMI brightness control | Windows only |

### Virtual Environment

Use the workspace `.venv` at the repo root:

```bash
# Activate
.venv\Scripts\Activate.ps1   # PowerShell
source .venv/bin/activate     # bash

# Install deps
pip install -r PoC/software/requirements.txt
```

---

## Code Style

### Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Functions/methods | `snake_case` | `get_volume()` |
| Variables | `snake_case` | `current_angle` |
| Constants | `UPPER_SNAKE` | `BOUND_MIN_DEG` |
| Classes | `PascalCase` | `VolumeController` |
| Private methods | `_leading_underscore` | `_parse_response()` |

### Type Hints

Use type hints for public API methods:

```python
def process_position(self, angle_degrees: float) -> None:
    """Process a position update from the knob."""
    pass
```

### Docstrings

Use triple-quote docstrings for all public classes and methods:

```python
def link_volume(self) -> bool:
    """Link knob rotation to system volume control.
    
    Returns:
        True if volume control was successfully initialized.
    """
```

---

## Serial Communication

- Baud rate: 115200
- Encoding: ASCII (`str.encode('ascii')`)
- Line terminator: `\n`
- Thread-safe reads: use a dedicated reader thread
- Timeout: 1 second for serial reads

---

## Error Handling

- Wrap serial operations in `try/except SerialException`
- Log errors to console, don't silently swallow
- Use `WINDOWS_LINK_AVAILABLE` flag pattern for optional features:

```python
try:
    from smartknob.windows_link import WindowsLink
    WINDOWS_LINK_AVAILABLE = True
except ImportError:
    WINDOWS_LINK_AVAILABLE = False
```

---

## GUI (Tkinter) Conventions

- Use `ttk` widgets over plain `tk` where available
- Group related controls into `LabelFrame` widgets
- Use `grid` layout manager (not `pack` or `place`)
- Thread serial reads — never block the main thread
- Use `root.after()` for periodic UI updates, not `time.sleep()`
