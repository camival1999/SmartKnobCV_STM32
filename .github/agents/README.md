# Custom Agents

<!-- Owner: SmartKnobCV_STM32 | Version: 5.0 | Last updated: 2026-02-28 -->

Registry of AI agents available for specialized tasks in this repository.

## Agent Architecture

The main agent invokes these subagents for specialized work:

| Role | Agent | Purpose |
|------|-------|---------|
| **Planner** | `planner.agent.md` | Analyzes requests, gathers context |
| **Worker** | `worker.agent.md` | Executes implementation tasks |
| **Validator** | `qa-validator.agent.md` | Verifies work answers the request |
| **Scribe** | `scribe.agent.md` | Maintains documentation, tracks progress |
| **Generic** | `generic-subagent.agent.md` | Catch-all for misc tasks |

## Workflow

```
User -> Main Agent -> [Planner -> Worker -> Validator] -> Scribe -> Main Agent -> User
              ↑                                                          |
              +------------------- (loop if needed) ---------------------+
```

## Subagent Constraints

All subagents follow these rules:

1. **NEVER call `ask_user`** — only the main agent interfaces with the user
2. **NEVER spawn subagents** — only the main agent can invoke runSubagent
3. **Maximum 250 lines output** — use temp files for overflow
4. **End with "Returning to main agent."**

## Related

- [Agent Patterns](../processes/agent-patterns.md)
- [Core Agent Rules](../copilot-instructions.md)
