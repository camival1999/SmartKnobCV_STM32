# Agent Patterns Reference

> **Owner:** SmartKnobCV_STM32 | **Version:** 5.0 | **Last updated:** 2026-02-28

> **Tier 3 On-Demand Reference:** This document contains advanced agent workflow patterns. It is loaded on-demand when agents need guidance on lifecycle management, escalation patterns, or debugging workflows.
>
> - **Tier 1 (Core Rules):** `.github/copilot-instructions.md`
> - **Tier 2 (Auto-Scoped):** `.github/instructions/*.instructions.md`
> - **Tier 3 (On-Demand):** This file, project READMEs

---

## Work Cycle / Lifecycle Framework

The main agent should conceptually follow this lifecycle when processing user requests:

```
+-------------------------------------------------------------------------+
|                                                                         |
|   ASSESS  ->  PLAN  ->  BUILD  ->  VALIDATE  ->  DELIVER               |
|     |          |                      ^                                 |
|     |          |                      |                                 |
|     |          +----------------------+                                 |
|     |               (loop as needed)                                    |
|     |                                                                   |
|     +-----> (simple requests: handle inline)                            |
|                                                                         |
+-------------------------------------------------------------------------+
```

| Phase | Role | Description |
|-------|------|-------------|
| **Assess** | Main Agent | Evaluate request, decide: inline vs delegate to subagent. |
| **Plan** | Planner | Analyze request, gather context, recommend Worker. |
| **Build** | Worker | Concrete implementation work (code, docs, analysis). |
| **Validate** | Validator | Check if work answers original request. Identify gaps. |
| **Deliver** | Main Agent | Present results to user. Call `ask_user`. |

**Usage notes:**
- Simple requests: main agent handles inline
- Complex requests may require multiple Build->Validate loops
- Main agent should always confirm compliance with repository conventions before delivering

---

## Escalation Loop

```
User Request -> Main Agent -> [Planner -> Worker -> Validator -> approval]
                    ^                                       |
                    +---------- reinvoke if rework <--------+
                                                            v
                                                 Main Agent -> ask_user -> Done
```

**Decision Points:**
- Simple query → main agent handles inline
- Complex task → main agent invokes subagents: `[Planner, Worker, ...]`
- Unclear → main agent calls `ask_user` for clarification

---

## Git History for Context (Optional)

For complex tasks involving legacy code, debugging, or refactoring, consider browsing recent git commits to understand context. **Delegate this to a subagent** to avoid filling the main agent's context window:

```bash
git log --oneline -20                    # Recent commit overview
git log --oneline -- <file>              # History of specific file
git show <commit>                        # Details of specific change
git blame <file>                         # Line-by-line attribution
git log --all --oneline -- <deleted>     # Find when file was deleted
```

**Use git history when:**
- Cleaning up legacy code (understand why files exist)
- Debugging unexpected behavior (find when it was introduced)
- Refactoring (find related files that changed together)
- Understanding design decisions beyond what docs capture

**Not needed for:**
- Simple new implementations with clear intent
- Tasks where documentation is sufficient
- Quick file edits with obvious purpose

---

## Subagent Output Guidelines

Subagent responses fill the main agent's context window. Verbose output wastes tokens and degrades performance.

### Output Length Limits

| Task Complexity | Max Output |
|-----------------|-----------|
| **All tasks** | **250 lines** |

### Overflow Handling

If output exceeds 250 lines:
1. Create temp file at `.copilot-tracking/temp/<task-id>.md`
2. Return filepath to main agent: `TEMP_FILE: .copilot-tracking/temp/<task-id>.md`
3. Main agent will read the file and delete it before finishing

### Output Format Rules

- Use tables and bullet points, not prose
- Omit boilerplate ("I have completed...", "Let me explain...")
- Return structured data, not narrative
- End with a single "Returning to main agent." line

### Pre-Completion Checklist

**Implementation subagents MUST report:**
```
[CHECKLIST: [x] docs | [x] tests | [x] validation | [!] edge cases | [x] deps]
```

Use [x] for completed items, [!] for issues, [ ] for skipped items.

---

## Subagent Rules (Detailed)

These rules govern all subagents invoked via `runSubagent`. Main agent must enforce these when invoking subagents.

### 0. CRITICAL: Subagent Tool Restrictions Are NOT Technically Enforced

**IMPORTANT LIMITATION:** The `runSubagent` tool does NOT technically block tools. The `tools:` array in `.agent.md` files is **guidance only**, not enforcement. Testing confirmed subagents CAN call `ask_user` even when restrictions are specified.

**Why this matters:** Subagents have FULL tool access and could impersonate the main agent by calling `ask_user`.

**REQUIRED: Explicit Profile Reference Pattern**

Every subagent prompt MUST include an explicit profile reference with restrictions stated clearly:

```
You are the [AGENT-NAME] per .github/agents/[AGENT-NAME].agent.md.

FORBIDDEN TOOLS -- CRITICAL:
- NO ask_user (return findings in your report instead)
- NO git_commit (return changes for main agent to commit)
- NO git_push (never push directly)

Violation of these restrictions is a CRITICAL ERROR.

TASK: [task description]...
```

### 1. Subagent Prompts Must Identify the Subagent

When calling `runSubagent`, the prompt MUST start with:
```
You are a subagent and your role is defined as: <RoleName>.
```

Include in every subagent prompt:
- Role declaration
- Scope of work
- Constraints (no `ask_user`, no sub-subagents)
- Specific task description
- **Absolute file paths** (subagents can't resolve relative paths)
- **Current date** (subagents can't determine it independently)

### 2. Subagents Must Never Call `ask_user`

This is a **critical constraint** (though technically soft-enforced via instructions, not tool blocking).

**The rule:** Only the main agent interfaces with the user. Subagents return results to the main agent.

### 3. Subagents Never Spawn Sub-Subagents

Only the main agent can invoke `runSubagent`. If a subagent needs additional help:
- Return to main agent with `REQUEST_AGENTS: [Agent-X]`
- Main agent will invoke the requested agent

### 4. Temp File Conventions

All temp files use timestamp format: `YYYYMMDD-HHMMSS.md`

### 5. Date Handling

Subagents cannot determine the current date independently. Main agent MUST include:
```
**Current date:** YYYY-MM-DD
```

---

## Related Documentation

- [Agents Registry](../agents/README.md) — Complete list of available agents
- [Core Instructions](../copilot-instructions.md) — Main rules and subagent workflow
