# mem1 V4 Issues To Fix

This document captures the remaining issues found while evaluating `V4/mem1` against `mem1_frontend_SOP_v4_onwards.md` for V4 specifically.

## Overall Assessment

`V4/mem1` appears largely aligned with the V4 SOP's implementation steps for:
- `api.js`
- `ExecutionTimeline.jsx`
- `AbortButton.jsx`
- `App.jsx`
- dark-themed `PromptBox.jsx`
- required V4 handoff file

The biggest remaining gaps are not the core SSE UI itself, but correctness of the V4 completion claim, reproducibility of the documented test evidence, and a few behavioral mismatches against the V4 success criteria.

## 1. The handoff overstates the `/run` replacement

The handoff says the monolithic `/run` result display was "replaced" by the V4 flow, but the current implementation still depends on `/run` to generate `steps` before calling `/execute`.

- Handoff claim:
  - `V4/mem1/docs/handoffs/v4/mem1_handoff.md:4`
  - `V4/mem1/docs/handoffs/v4/mem1_handoff.md:10`
- Actual implementation:
  - `V4/mem1/frontend/src/App.jsx:15`
  - `V4/mem1/frontend/src/App.jsx:24`
  - `V4/mem1/frontend/src/api.js:5`

Why this matters:
- The V4 SOP's sample implementation does still use `/run`, so the code is not wrong relative to the SOP.
- But the handoff wording is stronger than what was actually delivered, which can mislead mem2 or mem3 during sign-off.

Recommended fix:
- Either soften the handoff language to say V4 uses `/run` for planning and `/execute` plus SSE for execution, or remove the `/run` dependency if the team wants the handoff claim to be literally true.

## 2. Local test evidence in the handoff is not reproducible in this workspace

The handoff says `npm run build` succeeded, but the current workspace does not reproduce that result.

Observed evidence:
- `npm run build` fails because the Vite shim is not executable:
  - `V4/mem1/frontend/node_modules/.bin/vite`
- Direct Vite invocation also fails due to missing native `rolldown` bindings for the current environment.
- A `dist/` directory does exist, but that is not proof that the current workspace can still build successfully.

Relevant files:
- `V4/mem1/docs/handoffs/v4/mem1_handoff.md:39`
- `V4/mem1/frontend/dist/index.html`

Why this matters:
- The V4 handoff is supposed to provide trustworthy local validation evidence.
- Right now, someone consuming the handoff cannot rerun the stated build successfully from the checked-in workspace state.

Recommended fix:
- Reinstall frontend dependencies cleanly and rerun the documented checks.
- Update the handoff with actual reproducible command output from the current environment.

## 3. Abort UX does not fully meet the stated V4 success criterion

The V4 SOP says the aborted state should be shown cleanly with a "Stopped after step X of Y" style effect. The current frontend only appends a synthetic `system.abort` event locally when the abort button is pressed.

Relevant code:
- `V4/mem1/frontend/src/App.jsx:52`
- `V4/mem1/frontend/src/App.jsx:55`

Why this matters:
- The current UI does show that something was aborted, which is good.
- But it does not calculate or present progress context such as how many steps completed, which the V4 success criteria explicitly call out.
- It also closes the SSE stream immediately on local abort, so any richer backend-emitted aborted state may never be displayed.

Recommended fix:
- Keep listening long enough to render the backend's final abort event, or compute and display a clearer summary such as "Stopped after N completed steps".

## 4. Permission grant flow is fragile and depends entirely on backend auto-retry

The inline permission UI exists and matches the V4 SOP at surface level, but after clicking `Allow Once` or `Always Allow`, the frontend only posts the permission update and leaves re-execution entirely implicit.

Relevant code:
- `V4/mem1/frontend/src/components/ExecutionTimeline.jsx:110`
- `V4/mem1/frontend/src/App.jsx:45`
- `V4/mem1/frontend/src/App.jsx:48`
- `V4/mem1/docs/handoffs/v4/mem1_handoff.md:48`

Why this matters:
- The V4 test case expects the denied step to retry and eventually show success.
- That may happen if mem2 built backend auto-retry behavior exactly as assumed.
- But the frontend has no explicit confirmation, no pending state for the grant action, and no fallback if the step does not resume.

Recommended fix:
- Add explicit UI handling after a permission grant, such as a temporary "permission updated, waiting for retry" state, or coordinate with mem2 and document the exact retry contract more clearly in the handoff.

## 5. The handoff test evidence is weaker than the V4 success criteria require

The handoff lists `npm install`, `npm run build`, `npm run dev`, and a browser screenshot, but it does not provide concrete evidence for the V4 behaviors the SOP actually cares about:

- SSE events arriving in order
- abort mid-execution behavior
- permission denied then grant
- failed-step error rendering
- graceful disconnect behavior

Relevant source:
- `mem1_frontend_SOP_v4_onwards.md:509`
- `mem1_frontend_SOP_v4_onwards.md:542`
- `V4/mem1/docs/handoffs/v4/mem1_handoff.md:39`

Why this matters:
- The frontend may still be fine.
- But the current handoff does not prove the V4 flow was actually exercised against the key behavioral scenarios defined by the SOP.

Recommended fix:
- Expand the handoff's `Local Test Evidence` section with specific V4 scenario runs, especially SSE progression, abort behavior, permission grant behavior, and stream disconnect handling.

## Bottom Line

`V4/mem1` is close and the core V4 UI work is present. The remaining work is mainly:
- making the handoff accurate
- making the test evidence trustworthy
- tightening abort and permission-grant behavior so it better matches the V4 success criteria
