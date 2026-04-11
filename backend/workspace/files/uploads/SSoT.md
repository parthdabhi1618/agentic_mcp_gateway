# Agentic MCP Gateway — Single Source of Truth (SSoT)
## V4 and Beyond (Post-V3 Execution Plan)

> Date locked: April 10, 2026 (Day 1)
> Team: mem1 (Frontend), mem2 (Backend), mem3 (AI/Integration + Gluer)
> This file is the final authority for V4+ work. If anything conflicts, this file wins.

---

## 1. Project State and Goal

### Current confirmed state
- V3 is complete and is the base branch for all V4+ work.
- Existing system has `/run`, planner, executor, and 4 tools (GitHub, Slack, Jira, Sheets).

### Final product direction
Build an **Agentic OS-style web platform** where users:
- Prompt the agent in natural language
- Preview and edit execution plans before running
- Control permissions per tool/action
- Run and abort jobs in real time
- Add manual context (`@...`) into planning
- Manage files/context vaults
- Schedule recurring or one-time tasks

---

## 2. Team Roles (Frozen)

| Member | Role | Owns |
|---|---|---|
| mem1 | Frontend | UX, plan preview UI, execution timeline, settings panels, file/context views |
| mem2 | Backend | API contracts, tool runtime, permission middleware, job system, storage interfaces |
| mem3 | AI + Integration Lead | Planner quality, prompt schemas, context injection, validation, E2E glue and release checks |

---

## 3. Global Build Rules

1. No one changes API request/response shapes without updating this SSoT and informing all members.
2. Each version ends only after all three handoff files are committed.
3. All runtime errors must be represented as structured responses/events, not crashes.
4. `.env` is never committed; `.env.example` must be updated whenever new variables are introduced.
5. Every version has a demo flow and validation checklist.
6. Any blocked dependency >20 minutes must be escalated to mem3.

---

## 4. Canonical Folder Additions for V4+

```
agentic-mcp-gateway/
├── docs/
│   ├── handoffs/
│   │   ├── v4/
│   │   │   ├── mem1_handoff.md
│   │   │   ├── mem2_handoff.md
│   │   │   └── mem3_handoff.md
│   │   ├── v5/
│   │   ├── v6/
│   │   ├── v7/
│   │   ├── v8/
│   │   ├── v9/
│   │   ├── v10/
│   │   ├── v11/
│   │   └── v12/
│   ├── contracts/
│   │   ├── api_contract_v4_plus.md
│   │   ├── planner_output_schema.json
│   │   └── sse_event_schema.json
│   └── decisions/
│       └── adr_v4_plus.md
├── backend/
├── frontend/
└── README.md
```

Every version submission must include the corresponding `docs/handoffs/vX/memY_handoff.md` file.

---

## 5. API Contract (V4+)

### 5.1 `POST /plan`
Request:
```json
{ "prompt": "string", "context_refs": ["optional/path/or/context-id"], "tool_scope": ["github", "slack"] }
```
Response:
```json
{
  "plan_id": "string",
  "steps": [{ "step_id": "string", "tool": "string", "args": {}, "requires_permission": true }],
  "validation": { "valid": true, "issues": [] }
}
```

### 5.2 `POST /execute`
Request:
```json
{ "plan_id": "string", "steps": [{ "step_id": "string", "tool": "string", "args": {} }], "execution_mode": "run_now" }
```
Response:
```json
{ "job_id": "string", "status": "accepted" }
```

### 5.3 `GET /job/{job_id}/stream` (SSE)
Event payload:
```json
{
  "job_id": "string",
  "step_id": "string",
  "tool": "string",
  "action": "string",
  "status": "pending|running|success|failed|permission_denied|aborted",
  "result": {},
  "error": null,
  "timestamp": "ISO-8601"
}
```

### 5.4 `POST /job/{job_id}/abort`
Response:
```json
{ "job_id": "string", "status": "aborting" }
```

### 5.5 `GET /permissions` and `POST /permissions`
- Persistent map by `tool -> action -> allowed`.
- Supports one-time runtime grant event (`allow_once`) from execution UI.

---

## 6. Tool Action Coverage (V4 Mandatory)

- GitHub: `create_branch`, `delete_branch`, `list_branches`, `create_issue`, `close_issue`, `comment_on_issue`, `create_pr`, `merge_pr`, `list_prs`, `get_repo_info`, `push_file`, `list_commits`
- Slack: `send_message`, `create_channel`, `list_channels`, `get_messages`, `add_reaction`, `pin_message`, `invite_user`
- Jira: `create_issue`, `update_issue`, `close_issue`, `add_comment`, `transition_status`, `search_issues`, `assign_issue`
- Google Sheets: `append_row`, `read_range`, `update_cell`, `clear_sheet`, `create_sheet`, `list_sheets`
- Linear: `create_issue`, `update_issue`, `list_issues`, `assign_issue`, `set_priority`, `move_to_cycle`
- Notion: `create_page`, `update_page`, `append_block`, `query_database`, `create_database_entry`
- Discord: `send_message`, `create_channel`, `list_channels`, `add_role`, `kick_member`

Tool function return contract (uniform):
```json
{ "success": true, "data": {}, "error": null }
```

---

## 7. Version Plan and Deadlines

### Day 1 — Friday, April 10, 2026
- V4: Tool Expansion + uniform result contracts
- V5: Permissions and governance middleware
- V6: `/plan` and `/execute` split + editable plan flow
- V7: Job system + SSE + abort
- V8: Frontend overhaul integration pass

### Day 2 — Saturday, April 11, 2026
- V9: API key vault + connection onboarding + tool health panel
- V10: Context system + manual `@context` attachment + secure local context storage
- V11: File manager + upload + operations + context folder browser

### Day 3 — Sunday, April 12, 2026 (until 11:00 AM)
- V12: Scheduler (run later/recurring) + final demo hardening + release candidate

---

## 8. Version Exit Criteria (Must Pass)

For every version `vX`:
1. Backend endpoints compile and respond with documented shapes.
2. Frontend flow for that version is user-testable end-to-end.
3. Planner validates to schema and never returns invalid step objects.
4. `docs/handoffs/vX/mem1_handoff.md` exists.
5. `docs/handoffs/vX/mem2_handoff.md` exists.
6. `docs/handoffs/vX/mem3_handoff.md` exists.

---

## 9. Handoff File Template (Required)

Each handoff file must include exactly these sections:

```md
# Version vX — memY Handoff
## Summary
## Files Created/Updated
## API/Schema Changes
## Local Test Evidence
## Known Risks/Blockers
## Required Next Action (Owner: mem1|mem2|mem3)
```

---

## 10. Cross-Member Dependency Order

1. mem3 publishes planner/tool schema constraints first.
2. mem2 implements/updates backend contracts and event streams.
3. mem1 consumes stable contracts and finalizes UX.
4. mem3 runs integration validation and signs off.

No version is “done” without step 4.

---

## 11. V4+ Non-Negotiables

- No destructive action runs without permission checks.
- No execution without a plan preview step in UI.
- No hidden failures; every failure must emit a visible log/event.
- No context injection unless user explicitly attaches context (manual `@` model).
- No plaintext token exposure in frontend responses.

---

Last updated: April 10, 2026 (Day 1 planning lock)
Owner: mem3
