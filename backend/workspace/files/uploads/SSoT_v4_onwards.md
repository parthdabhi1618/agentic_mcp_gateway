# Agentic MCP Gateway — Single Source of Truth (SSoT)
## V4 and Beyond (Post-V3 Execution Plan)

> Date locked: April 10, 2026 (Day 1, ~11 PM)
> Team: mem1 (Frontend), mem2 (Backend), mem3 (AI/Integration + Gluer)
> This file is the final authority for V4+ work. If anything conflicts, this file wins.

---

## 1. Project State and Goal

### Current confirmed state
- V3 is complete and is the base branch for all V4+ work.
- Existing system has `/run`, planner (Ollama/Mistral), executor, and 4 tools (GitHub, Slack, Jira, Sheets).
- V3 codebase structure assumed:
```
agentic-mcp-gateway/
├── backend/
│   ├── main.py           (FastAPI app, single /run endpoint)
│   ├── planner.py        (Ollama LLM → list[dict] plan)
│   ├── executor.py       (execute_steps, TOOL_MAP)
│   ├── models.py         (Pydantic models)
│   ├── tools/
│   │   ├── github_tool.py
│   │   ├── slack_tool.py
│   │   ├── jira_tool.py
│   │   └── sheets_tool.py
│   ├── prompt_template.txt
│   ├── .env.example
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx
        ├── api.js
        └── components/
            ├── PromptBox.jsx
            ├── StepViewer.jsx
            └── LogViewer.jsx
```

### Final product direction
Build a **Web-based Agentic OS** where users:
- Prompt the agent in natural language via a Spotlight command bar
- Preview and interactively edit execution plans before running
- Control permissions per tool/action with inline governance UI
- Run and abort jobs in real time via SSE event streams
- Add manual context (`@context`) into planning
- Manage files (Finder-like) and Vault context folders
- Schedule recurring or one-time tasks using a cron-based scheduler

---

## 2. Team Roles (Frozen)

| Member | Role | Owns |
|---|---|---|
| mem1 | Frontend | OS UI shell, Spotlight bar, Plan Preview cards (editable), Execution Timeline, Permission modals, File manager, Settings drawer, Scheduler UI |
| mem2 | Backend | API contracts, 7-tool runtime with uniform contracts, permission middleware, job system, SSE streaming, abort, API key vault, file endpoints, context endpoints, scheduler daemon |
| mem3 | AI + Integration Lead | Planner prompt schemas for all 7 tools, context injection, manual @context RAG, output context logging, E2E validation scripts, demo scripting, version sign-off |

---

## 3. Global Build Rules

1. No one changes API request/response shapes without updating this SSoT and informing all members.
2. Each version ends ONLY after all three handoff files are committed to `docs/handoffs/vX/`.
3. All runtime errors MUST be represented as structured responses/events, not crashes.
4. `.env` is never committed. `.env.example` MUST be updated whenever new variables are introduced.
5. Every version has a demo flow and a validation checklist — mem3 runs it to sign off.
6. Any blocked dependency > 20 minutes must be escalated to mem3.
7. Tool functions MUST return `{ "success": bool, "data": {}, "error": null }` — no raw exceptions.

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
│   │   │   ├── mem1_handoff.md
│   │   │   ├── mem2_handoff.md
│   │   │   └── mem3_handoff.md
│   │   └── v6/
│   │       ├── mem1_handoff.md
│   │       ├── mem2_handoff.md
│   │       └── mem3_handoff.md
│   └── contracts/
│       ├── api_contract_v4_plus.md
│       └── sse_event_schema.json
├── backend/
│   ├── main.py
│   ├── planner.py
│   ├── executor.py
│   ├── permissions.py         ← V4 new
│   ├── jobs.py                ← V4 new (job registry + SSE)
│   ├── vault.py               ← V5 new (encrypted key store)
│   ├── scheduler.py           ← V5 new (APScheduler integration)
│   ├── models.py
│   ├── tools/
│   │   ├── github_tool.py     (expanded)
│   │   ├── slack_tool.py      (expanded)
│   │   ├── jira_tool.py       (expanded)
│   │   ├── sheets_tool.py     (expanded)
│   │   ├── linear_tool.py     ← V4 new
│   │   ├── notion_tool.py     ← V4 new
│   │   └── discord_tool.py    ← V4 new
│   └── workspace/             ← V6 new
│       ├── context/
│       │   ├── github_context/
│       │   ├── slack_context/
│       │   ├── session_context/
│       │   └── task_context/
│       └── files/
│           ├── uploads/
│           └── generated/
└── frontend/
    └── src/
        ├── App.jsx
        ├── api.js
        └── components/
            ├── PromptBox.jsx         (V4+ has @context tags)
            ├── PlanPreview.jsx       ← V5 new
            ├── ExecutionTimeline.jsx ← V4 new (SSE consumer)
            ├── PermissionModal.jsx   ← V4 new
            ├── AbortButton.jsx       ← V4 new
            ├── SpotlightBar.jsx      ← V6 new (CMD+K)
            ├── FileManager.jsx       ← V6 new
            ├── Scheduler.jsx         ← V5 new
            └── SettingsDrawer.jsx    ← V5 new (API keys + permissions matrix)
```

Every version submission MUST include `docs/handoffs/vX/memY_handoff.md`.

---

## 5. Full API Contract (V4+)

### 5.1 `POST /plan` (V5+)
Request:
```json
{ "prompt": "string", "context_refs": ["optional/path/or/context-id"], "tool_scope": ["github", "slack"] }
```
Response:
```json
{
  "plan_id": "uuid-string",
  "steps": [
    {
      "step_id": "uuid-string",
      "tool": "github",
      "action": "create_branch",
      "args": { "name": "fix/login", "from_branch": "main" },
      "requires_permission": true
    }
  ],
  "validation": { "valid": true, "issues": [] }
}
```

### 5.2 `POST /execute` (V4 starts as direct execute, V5 takes plan_id)
Request:
```json
{ "plan_id": "uuid-string", "steps": [{ "step_id": "string", "tool": "string", "action": "string", "args": {} }], "execution_mode": "run_now" }
```
Response:
```json
{ "job_id": "uuid-string", "status": "accepted" }
```

### 5.3 `GET /job/{job_id}/stream` (SSE)
Each event is a `data:` line with JSON:
```json
{
  "job_id": "string",
  "step_id": "string",
  "tool": "string",
  "action": "string",
  "status": "pending | running | success | failed | permission_denied | aborted",
  "result": {},
  "error": null,
  "timestamp": "ISO-8601"
}
```

### 5.4 `POST /job/{job_id}/abort`
Response: `{ "job_id": "string", "status": "aborting" }`

### 5.5 `GET /permissions` and `POST /permissions`
GET response:
```json
{ "github": { "create_branch": true, "delete_branch": false }, "slack": { "send_message": true } }
```
POST request:
```json
{ "tool": "github", "action": "delete_branch", "allowed": true, "scope": "always | once" }
```

### 5.6 `POST /keys/connect` (V5+)
Request: `{ "tool": "github", "key": "ghp_xxxxxx" }`
Response: `{ "tool": "github", "status": "connected | failed", "message": "string" }`

### 5.7 `GET /keys/status` (V5+)
Response: `{ "github": "connected", "slack": "disconnected", "notion": "not_configured" }`

### 5.8 `GET /files`, `POST /files/upload`, `DELETE /files/{filename}` (V6+)
GET response: `{ "files": [{ "name": "string", "size": int, "uploaded_at": "ISO-8601", "type": "upload|generated" }] }`
POST: multipart/form-data with `file` field.

### 5.9 `GET /context` (V6+)
Response: `{ "tree": { "github_context": ["repos.json", "open_prs.json"], "session_context": ["2026-04-10.json"] } }`

### 5.10 `POST /schedule` (V5+)
Request: `{ "plan_id": "string", "steps": [...], "schedule": { "type": "once|recurring", "run_at": "ISO-8601", "cron": "0 9 * * MON" } }`
Response: `{ "schedule_id": "string", "status": "scheduled" }`

---

## 6. Tool Action Coverage (V4 Mandatory — All 7 Tools)

```
GitHub:        create_branch, delete_branch, list_branches, create_issue, close_issue,
               comment_on_issue, create_pr, merge_pr, list_prs, get_repo_info,
               push_file, list_commits

Slack:         send_message, create_channel, list_channels, get_messages, add_reaction,
               pin_message, invite_user

Jira:          create_issue, update_issue, close_issue, add_comment, transition_status,
               search_issues, assign_issue

Google Sheets: append_row, read_range, update_cell, clear_sheet, create_sheet, list_sheets

Linear:        create_issue, update_issue, list_issues, assign_issue, set_priority,
               move_to_cycle

Notion:        create_page, update_page, append_block, query_database, create_database_entry

Discord:       send_message, create_channel, list_channels, add_role, kick_member
```

Uniform tool return contract:
```python
{ "success": True, "data": {}, "error": None }
# On failure:
{ "success": False, "data": {}, "error": "Human-readable error string" }
```
No tool function may raise an exception. All errors go into the `error` field.

---

## 7. Version Plan and Deadlines

### V4 — Tool Expansion + Permissions + Job/SSE System
The backend engine. After V4: mem1 can consume live streaming steps.

### V5 — Plan/Execute Split + Editable Plan Preview + Vault + Scheduler
The OS logic layer. After V5: user can preview, edit, and confirm plans. Keys are vaulted.

### V6 — Agentic OS UI + File Manager + Context Vault + @context Injection
The full shell. After V6: the product looks and feels like an OS. Demo-ready.

---

## 8. Version Exit Criteria (Must Pass Before Handoff)

For every version `vX`:
1. Backend endpoints compile and respond with documented shapes.
2. Frontend flow for that version is user-testable end-to-end.
3. Planner validates to schema and never returns invalid step objects.
4. `docs/handoffs/vX/mem1_handoff.md` exists and is complete.
5. `docs/handoffs/vX/mem2_handoff.md` exists and is complete.
6. `docs/handoffs/vX/mem3_handoff.md` exists and is signed off.
7. mem3's E2E validation script passes all assertions.

No version is "done" without all 7 criteria.

---

## 9. Handoff File Template (Required Format)

Each handoff file must include EXACTLY these sections:

```md
# Version vX — memY Handoff

## Summary
One paragraph describing what was built and why it matters for the next version.

## Files Created / Updated
- `path/to/file.py` — what changed and why
- `path/to/component.jsx` — what changed and why

## API / Schema Changes
List any endpoints added, removed, or modified with before/after shapes.

## Local Test Evidence
Paste actual terminal output or describe the exact test run with result.

## Known Risks / Blockers
What could break when another member consumes this output.

## Required Next Action
- **Owner: mem1** — [specific action]
- **Owner: mem2** — [specific action]
- **Owner: mem3** — [specific action]
```

---

## 10. Cross-Member Dependency Order (Per Version)

```
V4:
  1. mem3 publishes updated prompt_template.txt (7-tool schema)
  2. mem2 implements 7 tools + permissions + job/SSE system
  3. mem1 connects to SSE stream, builds timeline + permission modal
  4. mem3 runs integration validation, issues V4 handoff sign-off

V5:
  1. mem2 splits /plan from /execute, adds vault + scheduler endpoints
  2. mem3 wires context_refs into planner, tests plan output quality
  3. mem1 builds editable Plan Preview cards consuming GET /plan
  4. mem3 runs E2E test (edit a plan field → execute → SSE stream → correct result)

V6:
  1. mem2 delivers /files + /context endpoints + workspace folder structure
  2. mem3 implements @context injection into planner prompt
  3. mem1 builds Spotlight, File Manager, Settings drawer, Scheduler UI
  4. mem3 runs final demo rehearsal script, issues V6 sign-off
```

---

## 11. V4+ Non-Negotiables

- No destructive action (delete_branch, merge_pr, kick_member) runs without permission check.
- No execution without the job system in V4+. Direct sync `/run` is deprecated after V3.
- No hidden failures — every tool error must emit a structured SSE event.
- Context injection is strictly manual — user must use `@` mentions. No auto-injection.
- No plaintext key exposure in any frontend response.
- The abort flag must be checked between every single step — not just at the start.

---

Last updated: April 10, 2026 (~11 PM Day 1)
Owner: mem3
Locked: Yes — changes require all-member agreement
