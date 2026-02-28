---
description: 'Documentation and content creation standards for markdown files'
applyTo: '**/*.md'
lastUpdated: 2026-02-28
---
<!-- Owner: SmartKnobCV_STM32 | Last updated: 2026-02-28 -->
# Markdown Documentation Standards

Standards for all markdown documentation in this repository.

## Document Types

| Type | Location | Purpose |
|------|----------|---------|
| **README.md** | Root, subfolders | Quick reference, architecture overview |
| **Technical Docs** | `PoC/docs/` | Architecture, protocol spec |
| **Dev Tracking** | `PoC/docs/dev/` | Roadmap, changelog, issues, progress |
| **Learning Docs** | `FOC_Learnings/` | Learning path, exercises |

---

## README.md Conventions

### Required Section Order

1. **Overview** — One-paragraph description, key features
2. **Quick Start** — Minimal steps to run/build
3. **Architecture** — Package structure, data flow diagram
4. **Key Files** — Table of important files with descriptions
5. **License** — License reference

### README Constraints

- **Keep under 1000 lines** — Link to `PoC/docs/` for details
- **Use tables for file lists** — Not prose paragraphs
- **One H1 only** — The document title
- **Relative links** — Use `./docs/` not absolute paths

### Good vs Bad Examples

[X] **Bad: Verbose prose for file list**
```markdown
The package contains several important files. The main.cpp file is the 
firmware entry point that handles motor control. The windows_link.py file 
manages Windows integrations...
```

[x] **Good: Table format**
```markdown
| File | Purpose |
|------|---------|
| `main.cpp` | Firmware entry point, motor control + haptic modes |
| `windows_link.py` | Windows integration orchestrator |
```

---

## General Markdown Style

### Headings

- **H1 (`#`)**: Document title only, one per file
- **H2 (`##`)**: Major sections
- **H3 (`###`)**: Subsections
- **Avoid H4+**: Restructure content if needed

### Code Blocks

Always specify language for syntax highlighting:

~~~markdown
```cpp
// C++ firmware code
motor.loopFOC();
```
~~~

~~~markdown
```python
# Python driver code
driver.connect("COM3")
```
~~~

### Links

- **Internal files**: `[Config](PoC/firmware/src/config.h)`
- **Relative paths**: `./PoC/docs/ARCHITECTURE.md`
- **Section anchors**: `[Testing](#testing)`

### Tables Over Lists

Use tables when data has multiple attributes.

---

## Changelog Format

Use semantic versioning with date:

```markdown
## [v0.0.2] - 2026-02-28

### Added
- Repository refactor separating PoC from learning material

### Fixed
- Fixed import paths after restructuring
```

---

## Validation Checklist

Before committing markdown changes:

- [ ] No broken internal links
- [ ] Code blocks have language specifiers
- [ ] Tables are properly formatted
- [ ] README under 1000 lines
- [ ] Changelog updated if structure changed
