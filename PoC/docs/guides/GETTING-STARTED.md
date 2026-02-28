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

This registers both `smartknob` (driver) and `smartknob_windows` (application) packages in your venv so Python can find them from anywhere. The `-e` flag means **editable** — it creates a link to your live source files, so any code changes take effect immediately without reinstalling.

### Verify Installation

```bash
python -c "from smartknob import SmartKnobDriver; print('Driver OK')"
python -c "from smartknob_windows.windows_link import WindowsLink; print('Windows App OK')"
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

### Project Layout

The `platformio.ini` lives at the **repo root** (not inside `PoC/firmware/`). This is required for the PlatformIO VS Code extension to detect the project in multi-root workspaces. The ini uses `[platformio]` directory settings to point to the actual source code:

```ini
[platformio]
src_dir = PoC/firmware/src      # C++ source files
lib_dir = PoC/firmware/lib      # Additional libraries
include_dir = PoC/firmware/include
test_dir = PoC/firmware/test
```

### Using PlatformIO CLI

```bash
# From the repo root (where platformio.ini lives)
pio run              # Build
pio run -t upload    # Flash to Nucleo board
pio device monitor   # Open serial monitor (115200 baud)
```

### Using VS Code PlatformIO Extension

1. Open the SmartKnobCV_STM32 folder in VS Code
2. The PlatformIO extension auto-detects `platformio.ini` at root → shows `nucleo_l452re` in the status bar
3. Click the PlatformIO icon in the sidebar
4. Use **Build** (checkmark), **Upload** (arrow), or **Monitor** (plug icon)

> **Note:** If `pio` is not on your PATH, use the full path:
> `$env:USERPROFILE\.platformio\penv\Scripts\pio.exe`

> **Multi-Root Workspace Tip:** PlatformIO only scans workspace folder roots for `platformio.ini`. If you add SmartKnobCV_STM32 as a workspace folder, the extension will detect the environment automatically. It won't find `platformio.ini` if it's nested in subdirectories.

---

## 5. Run the GUI

With the venv activated and the STM32 connected via USB:

```bash
python PoC/software/smartknob_windows/gui/app.py
```

1. Select the COM port from the dropdown and click **Connect**
2. Choose a haptic mode (Haptic, Inertia, Spring, Bounded)
3. Use the **Windows Link** section to bind knob rotation to a system function (volume, brightness, scroll, zoom)

---

## Understanding Python Packages

The Python code is split into two packages in `PoC/software/`:

| Package | Purpose | Dependencies |
|---------|---------|-------------|
| `smartknob/` | Reusable driver — works on any OS | `pyserial` only |
| `smartknob_windows/` | Windows app (GUI, integrations) | `pycaw`, `comtypes`, `wmi` |

### What is `__init__.py`?

Every folder that contains an `__init__.py` file is treated as a **Python package**. Without this file, Python sees the folder as just a regular directory and won't allow imports from it.

```
smartknob/                  ← cross-platform driver package
├── __init__.py             ← re-exports SmartKnobDriver, HapticMode
├── driver.py               ← SmartKnobDriver class
└── protocol.py             ← constants, enums, print_help()

smartknob_windows/          ← Windows-specific application
├── __init__.py
├── windows_link.py         ← motor ↔ Windows function binding
├── gui/
│   └── app.py              ← Tkinter GUI
├── integrations/           ← volume, brightness, scroll, zoom
├── config/                 ← presets.json, contexts.json
└── context/                ← active window detection
```

### Why `pip install -e`?

Even with `__init__.py` files, Python needs to know **where** the packages are. `pip install -e` ("editable install") registers their locations in your venv. This means:

- `from smartknob import SmartKnobDriver` works from **any directory**
- `from smartknob_windows.windows_link import WindowsLink` also works everywhere
- You edit source files and changes take effect **immediately** (no re-install)
- The `pyproject.toml` file defines the package metadata (name, version, dependencies)

### `pyproject.toml` vs `requirements.txt`

| File | Purpose |
|------|---------|
| `requirements.txt` | Quick dependency install for users (`pip install -r`) |
| `pyproject.toml` | Full package definition — name, version, dependencies, build config. Used by `pip install -e` |

Both list the same dependencies. `pyproject.toml` is the modern Python standard; `requirements.txt` is a convenience shortcut.

---

## Understanding C++ Firmware Structure

The firmware in `PoC/firmware/src/` is split into modules. This section explains the C++ patterns used and why.

### How `.h` and `.cpp` Work Together

Think of it like a restaurant:

- **`.h` (header file)** = the **menu**. It lists what's available — function names, types, constants — so other files know what they can use.
- **`.cpp` (source file)** = the **kitchen**. It has the actual code that does the work.

When file A wants to call a function from file B, it `#include`s B's header. The header promises "this function exists," and the linker connects the dots at build time.

```
config.h      → Pin definitions, mode enum, extern declarations
haptics.h     → computeHapticTorque(), computeInertiaTorque(), etc.
haptics.cpp   → Actual torque math implementation
comms.h       → doHaptic(), doInertia(), reportPosition(), etc.
comms.cpp     → Serial command handler implementations
button.h      → ButtonState struct, initButton(), checkButtonPress()
button.cpp    → Debounce logic, mode cycling
main.cpp      → Hardware objects, setup(), loop() — ties everything together
```

### The `extern` Keyword

`extern` says: "this variable exists, but it's defined somewhere else."

```cpp
// config.h — DECLARES the variable (menu says it exists)
extern BLDCMotor motor;
extern int detent_count;

// main.cpp — DEFINES the variable (kitchen has the actual thing)
BLDCMotor motor = BLDCMotor(7);
int detent_count = 36;
```

Without `extern`, each `.cpp` file that includes the header would create its **own copy** of the variable, causing linker errors ("multiple definition of...").

### The Build Process: Compile → Link

PlatformIO builds firmware in two steps:

1. **Compile**: Each `.cpp` file is compiled independently into an `.o` (object) file. Headers are copy-pasted in via `#include`. At this stage, the compiler trusts `extern` declarations — it doesn't check if the variable actually exists yet.

2. **Link**: All `.o` files are combined into one binary. The linker resolves all the `extern` promises — if `haptics.cpp` references `motor`, the linker finds it in `main.o`. If anything is missing, you get a "undefined reference" error.

```
config.h  ──┐
haptics.cpp ─┤──> haptics.o ──┐
comms.cpp ───┤──> comms.o   ──┤──> firmware.elf (final binary)
button.cpp ──┤──> button.o  ──┤
main.cpp ────┘──> main.o    ──┘
```

### Include Guards

Every header file has include guards to prevent being included twice:

```cpp
#ifndef CONFIG_H
#define CONFIG_H
// ... contents ...
#endif // CONFIG_H
```

Without this, if both `haptics.cpp` and `comms.cpp` include `config.h`, and `comms.cpp` also includes `haptics.h` (which also includes `config.h`), you'd get "redefinition" errors.

### Multi-Button Pattern: Struct-Based Design

Instead of separate variables per button, we use a `ButtonState` struct:

```cpp
struct ButtonState {
  uint8_t       pin;          // GPIO pin
  bool          lastState;    // Previous reading
  unsigned long lastPressMs;  // Last accepted press timestamp
};
```

Adding a second button is then trivial — no new global variables, no code duplication:

```cpp
ButtonState userBtn;   // Already exists (PC13)
ButtonState btn2;      // New button — just add one line

initButton(userBtn, USER_BTN);
initButton(btn2, PB5);         // Initialize with any GPIO

if (checkButtonPress(btn2)) {
  // Handle second button action
}
```

### Why Globals Instead of Classes (For Now)

The current firmware uses **global variables with `extern`** rather than wrapping everything in C++ classes. This is intentional for the PoC stage:

| Approach | Pros | Cons |
|----------|------|------|
| **Globals + extern** | Simple, easy to debug via Serial, matches SimpleFOC examples | Harder to scale, no encapsulation |
| **Classes** | Clean API, encapsulation, reusable | More boilerplate, harder to follow for embedded beginners |

As the project grows past PoC, key modules (like `HapticEngine`, `SerialProtocol`) may be promoted to classes. The current module split makes that transition easy — each `.h/.cpp` pair maps naturally to a class.

### Framework Swappability

The firmware currently uses **Arduino framework via STM32Duino** (configured in `platformio.ini`). This provides familiar functions like `digitalWrite()`, `Serial.println()`, `millis()`.

If performance demands it later, the framework could be swapped to **STM32 HAL** (Hardware Abstraction Layer) — the manufacturer's low-level API. The modular structure means only the hardware-touching code in `config.h` and `main.cpp` would need changes; the haptic math in `haptics.cpp` is framework-agnostic.

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
