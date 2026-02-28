# Getting Started

Step-by-step guide to clone, set up, and run the SmartKnob PoC on your machine.

For full system architecture and hardware details, see [ARCHITECTURE.md](../ARCHITECTURE.md) and the [PoC README](../../README.md).

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10+ | Driver, integrations, GUI |
| **PlatformIO** | Latest (CLI or VS Code extension) | Firmware build & flash |
| **VS Code** | Latest + Python extension | Recommended IDE |
| **Git** | Any | Clone the repo |
| **Windows 10/11** | Required | Windows API integrations (volume, brightness, etc.) |

Hardware: STM32 Nucleo L452RE + SimpleFOCShield V3.2 + MT6701 encoder + Mitoot 2804 motor. See [ARCHITECTURE.md](../ARCHITECTURE.md) for wiring and component details.

---

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/SmartKnobCV_STM32.git
cd SmartKnobCV_STM32
```

---

## 2. Python Environment Setup

### Create a Virtual Environment

```bash
python -m venv .venv
```

### Activate the Virtual Environment

```powershell
# PowerShell
.venv\Scripts\Activate.ps1

# CMD
.venv\Scripts\activate.bat
```

You should see `(.venv)` in your terminal prompt.

### Install Dependencies

```bash
python -m pip install -r PoC/software/requirements.txt
```

### Install SmartKnob Package (Editable Mode)

```bash
python -m pip install -e PoC/software/
```

This registers the `smartknob` package in your venv so Python can find it from anywhere. The `-e` flag means **editable** — it creates a link to your live source files, so any code changes take effect immediately without reinstalling.

### Verify Installation

```bash
python -c "from smartknob.windows_link import WindowsLink; print('OK')"
```

---

## 3. VS Code Configuration

### Select the Python Interpreter

VS Code needs to know which Python interpreter to use. The repo includes a `.vscode/settings.json` that points to the local `.venv`, but you may need to select it manually the first time:

1. Press `Ctrl+Shift+P` to open the Command Palette
2. Type **"Python: Select Interpreter"** and press Enter
3. Choose the interpreter inside `.venv/`:
   ```
   .venv\Scripts\python.exe
   ```
4. VS Code will now use this interpreter for:
   - The "Run Python File" button (play button in the top-right)
   - Integrated terminal
   - IntelliSense and linting

> **Tip:** If the `.venv` doesn't appear in the list, click "Enter interpreter path..." and browse to `.venv\Scripts\python.exe`.

---

## 4. Build & Flash Firmware

### Using PlatformIO CLI

```bash
cd PoC/firmware
pio run              # Build
pio run -t upload    # Flash to Nucleo board
pio device monitor   # Open serial monitor (115200 baud)
```

### Using VS Code PlatformIO Extension

1. Open the `PoC/firmware/` folder in VS Code (or the project root — PlatformIO auto-detects)
2. Click the PlatformIO icon in the sidebar
3. Use **Build** (checkmark), **Upload** (arrow), or **Monitor** (plug icon)

> **Note:** If `pio` is not on your PATH, use the full path:
> `$env:USERPROFILE\.platformio\penv\Scripts\pio.exe`

---

## 5. Run the GUI

With the venv activated and the STM32 connected via USB:

```bash
python PoC/software/gui/app.py
```

1. Select the COM port from the dropdown and click **Connect**
2. Choose a haptic mode (Haptic, Inertia, Spring, Bounded)
3. Use the **Windows Link** section to bind knob rotation to a system function (volume, brightness, scroll, zoom)

---

## Understanding Python Packages

The `smartknob` source code lives in `PoC/software/smartknob/`. Here's how the Python package system works:

### What is `__init__.py`?

Every folder that contains an `__init__.py` file is treated as a **Python package**. Without this file, Python sees the folder as just a regular directory and won't allow imports from it.

```
smartknob/                  ← package (has __init__.py)
├── __init__.py             ← marks as package + contains version
├── windows_link.py         ← module: smartknob.windows_link
└── integrations/           ← sub-package (also has __init__.py)
    ├── __init__.py         ← marks as sub-package
    ├── volume.py           ← module: smartknob.integrations.volume
    └── brightness.py       ← module: smartknob.integrations.brightness
```

### Why `pip install -e`?

Even with `__init__.py` files, Python needs to know **where** the `smartknob/` folder is. `pip install -e` ("editable install") registers the package location in your venv. This means:

- `from smartknob.windows_link import WindowsLink` works from **any directory**
- You edit source files and changes take effect **immediately** (no re-install)
- The `pyproject.toml` file defines the package metadata (name, version, dependencies)

### `pyproject.toml` vs `requirements.txt`

| File | Purpose |
|------|---------|
| `requirements.txt` | Quick dependency install for users (`pip install -r`) |
| `pyproject.toml` | Full package definition — name, version, dependencies, build config. Used by `pip install -e` |

Both list the same dependencies. `pyproject.toml` is the modern Python standard; `requirements.txt` is a convenience shortcut.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'smartknob'"

The package isn't installed in your venv. Run:

```bash
python -m pip install -e PoC/software/
```

### "ModuleNotFoundError: No module named 'serial'"

Dependencies not installed. Run:

```bash
python -m pip install -r PoC/software/requirements.txt
```

### COM Port Not Found

- Ensure the Nucleo board is connected via USB
- Check Device Manager for the COM port number
- Try a different USB cable (some are charge-only)

### VS Code "Run" Button Uses Wrong Python

See [Section 3: VS Code Configuration](#3-vs-code-configuration) to select the correct interpreter.

### PlatformIO "pio" Command Not Found

PlatformIO may not be on your PATH. Use the full path:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run
```

Or install the PlatformIO VS Code extension, which handles paths automatically.

### `pip` Shows "Fatal error in launcher"

If the `.venv` was moved or the folder was renamed, pip's launcher can break. Use `python -m pip` instead:

```bash
python -m pip install -r PoC/software/requirements.txt
```
