# Known Issues

## Active Issues

*No active issues.*

---

## Resolved Issues

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
