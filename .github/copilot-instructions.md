# AI Agent Instructions for SmartKnobCV_STM32

> **Owner:** Camilo | **Version:** 5.0 | **Last updated:** 2026-02-28

---

## [!] CRITICAL RULES

### Rule 1: Main Agent Behavior

**First action:** Look up the current date.

**During discussion:** When the task requires multiple steps or non-trivial changes, present a detailed plan using `plan_review` or #planReview and wait for approval before executing. If the plan is rejected, incorporate the comments provided by the user and submit an updated plan with `plan_review` or #planReview.

**When the user request instructions:** If asked for a step-by-step guide or walkthrough, present it using `walkthrough_review` or #walkthroughReview.

**Last action:** Call `ask_user` or #askUser at the end of every response. No exceptions.

- `ask_user` is MANDATORY — even for errors, clarifications, or partial work
- Provide your `agentName`: `"Main Orchestrator"` for the main agent
- Never end with "let me know if you need help" — always use the tool

### Rule 2: Subagent Delegation

When invoking `runSubagent`, the prompt MUST start with this 3-element header:

```
You are a SUBAGENT. You must NOT call ask_user. Return your results directly to the main agent.

Current date: YYYY-MM-DD

Your role is [AgentName]. Follow the instructions in `.github/agents/[agent-name].agent.md`.
```

| Element | Purpose |
|---------|---------|
| Declaration | Establishes identity and restrictions |
| Date | Subagents cannot determine current date independently |
| Profile reference | Points to detailed role instructions |

### Rule 3: Subagents Never Call ask_user

Subagents return results to the main agent. Only the main agent interfaces with the user.

If a subagent needs clarification, it returns `REQUEST_CLARIFICATION: <question>` in its output.

---

## Scribe Integration

The **Scribe** agent maintains all documentation in `PoC/docs/dev/`. Invoke Scribe after significant events.

### Invoke Scribe After:

| Event | What to Log |
|-------|-------------|
| **Phase progress** | Update PROGRESS/, CHANGELOG, ROADMAP |
| **Bug discovered** | Add to KNOWN-ISSUES.md |
| **Bug fixed** | Move to resolved, add to CHANGELOG |
| **New file/folder created** | Update parent README |
| **Architecture changed** | Update ARCHITECTURE.md |
| **Phase completed** | Update ROADMAP, CHANGELOG, mark PROGRESS complete |

### Scribe Invocation

```
You are a SUBAGENT. You must NOT call ask_user. Return your results directly to the main agent.

Current date: YYYY-MM-DD

Your role is Scribe. Follow the instructions in `.github/agents/scribe.agent.md`.

## Event: [event_type]

| Field | Value |
|-------|-------|
| Event Type | [phase_progress / bug_found / bug_fixed / etc.] |
| Date | YYYY-MM-DD |
| Summary | [Brief description] |
| Details | [Files changed, decisions made] |
```

> **Reference:** [agents/scribe.agent.md](agents/scribe.agent.md)

---

## Instruction Tiering

| Tier | Location | Loading |
|------|----------|---------|
| **Tier 1** | `.github/copilot-instructions.md` | Always-on |
| **Tier 2** | `.github/instructions/*.instructions.md` | Auto-scoped by file path |
| **Tier 3** | `PoC/docs/`, `.github/processes/` | On-demand |

### Instruction Precedence

1. **Component-specific** (e.g., `cpp.instructions.md`) — highest priority
2. **Language-specific** (e.g., `python.instructions.md`)
3. **Global** (this file) — lowest priority

---

## Documentation Navigation

| Looking for... | Read this file |
|----------------|----------------|
| System architecture | [PoC/docs/ARCHITECTURE.md](../PoC/docs/ARCHITECTURE.md) |
| Serial protocol | [PoC/docs/serial-protocol.md](../PoC/docs/serial-protocol.md) |
| Development roadmap | [PoC/docs/dev/ROADMAP.md](../PoC/docs/dev/ROADMAP.md) |
| Progress tracking | [PoC/docs/dev/PROGRESS/](../PoC/docs/dev/PROGRESS/) |
| Known issues | [PoC/docs/dev/KNOWN-ISSUES.md](../PoC/docs/dev/KNOWN-ISSUES.md) |
| Changelog | [PoC/docs/dev/CHANGELOG.md](../PoC/docs/dev/CHANGELOG.md) |
| Agent patterns | [processes/agent-patterns.md](processes/agent-patterns.md) |
| Repo structure | [processes/standard-repo-structure.md](processes/standard-repo-structure.md) |
| Available agents | [agents/README.md](agents/README.md) |

---

## Instruction Routing

| Context | Auto-Loaded | Read If Needed |
|---------|-------------|----------------|
| Any `.cpp` or `.h` file | `cpp.instructions.md` | `PoC/docs/serial-protocol.md` |
| Any `.py` file | `python.instructions.md` | `PoC/software/smartknob/__init__.py` |
| Any `.md` file | `markdown.instructions.md` | — |
| `PoC/firmware/` | `cpp.instructions.md` | `PoC/firmware/platformio.ini` |
| `PoC/software/` | `python.instructions.md` | `PoC/software/pyproject.toml` |
| `PoC/docs/` | `markdown.instructions.md` | — |

---

## Repository Architecture

| Folder | Purpose | Status |
|--------|---------|--------|
| `.github/` | AI agents, instructions, processes | Active |
| `PoC/` | Proof of Concept — active development | Active |
| `PoC/firmware/` | PlatformIO STM32 firmware (C++) | Active |
| `PoC/software/smartknob/` | Cross-platform driver package (pyserial only) | Active |
| `PoC/software/smartknob_windows/` | Windows app: GUI, integrations, context | Active |
| `PoC/docs/` | Architecture, protocol spec, dev tracking | Active |
| `FOC_Learnings/` | Learning path, firmware iterations | Archive |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **MCU** | STM32L452RET6 (Nucleo L452RE) — 80 MHz Cortex-M4 |
| **Motor Control** | SimpleFOC v2.4.0 (FOC torque control) |
| **Encoder** | MT6701 14-bit magnetic encoder (SSI over SPI) |
| **Motor Driver** | SimpleFOCShield V3.2 (DRV8313 + ACS712) |
| **Motor** | Mitoot 2804 100KV gimbal BLDC (7 pole pairs) |
| **Build System** | PlatformIO (Arduino framework, STM32Duino) |
| **Serial** | 115200 baud, ASCII text protocol |
| **Python** | pyserial, pycaw, comtypes, wmi, tkinter |
| **GUI** | Tkinter (PoC/software/smartknob_windows/gui/app.py) |

---

## Code Conventions

### C++/Firmware

- Use PlatformIO for builds (`pio run`)
- Pin definitions in header files
- `camelCase` for functions and variables, `UPPER_SNAKE` for constants
- Serial debug at 115200 baud
- SimpleFOC torque control mode for haptic feedback
- See `cpp.instructions.md` for full conventions

### Python/Software

- `smartknob` package structure with `__init__.py` files
- Integration controllers: `XxxController` class pattern
- `snake_case` for functions/variables, `PascalCase` for classes
- Type hints for public API methods
- See `python.instructions.md` for full conventions

---

## Agent Architecture (Summary)

```
User -> Main Agent -> [Planner -> Worker -> Validator] -> Scribe -> Main Agent -> User
              ↑                                                          |
              +------------------- (loop if needed) ---------------------+
```

| Role | Agent | Purpose |
|------|-------|---------|
| **Main Agent** | (this file) | User interface, subagent orchestration |
| **Planner** | `planner.agent.md` | Context gathering, routing |
| **Worker** | `worker.agent.md` | Implementation |
| **Validator** | `qa-validator.agent.md` | Verification |
| **Scribe** | `scribe.agent.md` | Documentation, progress tracking |
| **Generic** | `generic-subagent.agent.md` | Catch-all for misc tasks |

> **Deep context:** See [agents/README.md](agents/README.md) for full agent list.

---

## Main Agent Identity Marker

**If you can read this section, you are the main agent.** Subagents do not receive this file.

### Available Agents

| Agent | File | Use For |
|-------|------|---------|
| `planner` | `planner.agent.md` | Context gathering, routing |
| `worker` | `worker.agent.md` | Implementation |
| `validator` | `qa-validator.agent.md` | Verification |
| `scribe` | `scribe.agent.md` | Documentation, progress tracking |
| `generic-subagent` | `generic-subagent.agent.md` | General tasks |

### Tool Restrictions Note

**IMPORTANT:** Tool restrictions in `.agent.md` frontmatter are NOT technically enforced. Subagents have FULL tool access. Restrictions work only through explicit instructions in the prompt header.

---

## Safety Boundaries

| Operation | Rule |
|-----------|------|
| **Git operations** | Only with explicit user approval |
| **File deletion** | Flag as high-risk, require confirmation |
| **Instruction file edits** | `.github/` files require explicit permission |
| **Temp file cleanup** | Delete `.copilot-tracking/temp/` before finishing |

---

## CRITICAL: No Auto-Commit

**NEVER automatically make a git commit.** Always ask the user first:

1. Complete your work (code, docs, etc.)
2. Call `ask_user` to ask: "Ready to commit? I can commit with message 'X' or provide the message for you to commit manually."
3. Only commit if user explicitly approves

---

## Code Quality Triggers

| Trigger | Action |
|---------|--------|
| Creating a function | Add input validation |
| Creating a class | Add docstrings |
| Adding a file | Update parent README **immediately** |
| Deleting a file | Remove from README, check references |
| Changing serial protocol | Update `PoC/docs/serial-protocol.md` |
| Changing firmware behavior | Update `PoC/docs/ARCHITECTURE.md` |

---

## Date Handling

- Use `YYYY-MM-DD` format
- Get current date from conversation context
- Include `Current date: YYYY-MM-DD` in all subagent prompts
- Never invent dates — use `[DATE]` placeholder if uncertain

---

## When in Doubt

1. Read documentation first
2. Preserve existing patterns
3. Update documentation after changes
4. Test after changes (firmware: `pio run`, Python: import test)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| **5.0** | 2026-02-28 | Initial Tribunal adoption v5.0 — adapted agents, instructions, processes, Scribe tracking to this project|
