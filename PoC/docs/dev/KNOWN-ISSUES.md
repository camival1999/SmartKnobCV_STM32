# Known Issues

## Active Issues

*No active issues.*

---

## Resolved Issues

### BUG-004: "Bad position line" Warnings on Startup

| Field | Value |
|-------|-------|
| **Severity** | Low (cosmetic) |
| **Found** | 2026-02-28 |
| **Resolved** | 2026-02-28 |
| **Phase** | 1B |
| **Component** | `smartknob/driver.py` |

**Description:** On connect, the terminal shows `Bad position line: Position: 60.12 deg` and `Bad position line: Pos PID: P=50.00 I=0.00 D=0.30`. Functionality is unaffected.

**Root Cause:** The driver's position parser matched any line starting with `P` (the position report prefix). Firmware info messages like `Position: ...` and `Pos PID: ...` also start with `P`, so the parser tried to parse them as position floats, failed, and logged warnings.

**Fix:** Added stricter match in `_process_line()` — now checks that the character after `P` is a digit or minus sign before treating the line as a position report. Human-readable info lines are silently skipped.

---

### BUG-003: PlatformIO VS Code Extension Can't Detect Nucleo Environment

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Found** | 2026-02-28 |
| **Resolved** | 2026-02-28 |
| **Phase** | N/A (Build Tooling) |
| **Component** | `platformio.ini` |

**Description:** PlatformIO VS Code extension doesn't detect the `nucleo_l452re` environment in a multi-root workspace. The extension instead picks up the ESP32 project (`SmartKnobCV_ESP32/platformio.ini`) because that file is at a workspace folder root.

**Root Cause:** PlatformIO VS Code extension only scans workspace folder roots for `platformio.ini`. When the file was nested at `SmartKnobCV_STM32/PoC/firmware/platformio.ini`, the extension couldn't find it.

**Fix:** Moved `platformio.ini` to the repository root (`SmartKnobCV_STM32/platformio.ini`) and added a `[platformio]` section with `src_dir`, `lib_dir`, `include_dir`, and `test_dir` pointing to `PoC/firmware/` subdirectories. Deleted old `PoC/firmware/platformio.ini`. Build verified: Flash 17.5% / RAM 2.5% unchanged. Updated GETTING-STARTED.md Section 4 to document the `platformio.ini` location requirement.

---

### BUG-002: VS Code Run Button Not Using .venv

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Found** | 2026-02-28 |
| **Resolved** | 2026-02-28 |
| **Phase** | N/A (Environment) |
| **Component** | VS Code configuration |

**Description:** Pressing the "Run Python File" button in VS Code uses the system Python interpreter instead of the workspace `.venv`.

**Root Cause:** No `.vscode/settings.json` existed to configure `python.defaultInterpreterPath`.

**Fix:** Created `.vscode/settings.json` pointing to `.venv/Scripts/python.exe`. Users can also manually select the interpreter via `Ctrl+Shift+P` → "Python: Select Interpreter".

---

### BUG-001: Windows Link Options Not Showing After Refactor

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Found** | 2026-02-28 |
| **Resolved** | 2026-02-28 |
| **Phase** | Phase 0 (Repo Refactor) |
| **Component** | `PoC/software/gui/app.py` |

**Description:** After the Phase 0 repo refactor, the Windows Link integration options were not visible in the GUI. The GUI loaded without errors but the Windows Link frame was missing entirely.

**Root Cause:** The `smartknob` package was not installed in the venv. The `from smartknob.windows_link import WindowsLink` import failed silently, setting `WINDOWS_LINK_AVAILABLE = False` and skipping the entire UI section.

**Fix:** Installed `smartknob` as an editable package (`pip install -e PoC/software/`). This registers the package in the venv so Python can find it regardless of working directory. Documented in [GETTING-STARTED.md](../guides/GETTING-STARTED.md).
