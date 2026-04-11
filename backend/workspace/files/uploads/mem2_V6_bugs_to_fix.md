# mem2 V6 Bugs To Fix

## Status

`V6/mem2` has most of the V4 and V5 backend in place and includes the V6 file/context endpoints, but it should not be treated as fully complete against the root mem2 SOP yet.

## Issues

### 1. Block path traversal on file upload

Severity: High

Problem:
- `V6/mem2/backend/main.py` writes uploaded files using `file.filename` directly
- `POST /files/upload` builds the destination with `os.path.join(FILES_UPLOAD_DIR, file.filename)` and does not normalize or validate the final path
- A crafted filename can escape `workspace/files/uploads`

Why this matters:
- The V6 SOP requires secure file access
- The current implementation protects delete/read paths more than upload, which leaves the new file manager incomplete
- This is the most important backend security gap in the V6 work

What to do:
- Sanitize upload filenames before writing
- Resolve the absolute destination path and verify it stays inside `workspace/files/uploads`
- Reject invalid filenames with a proper error response instead of writing the file

Relevant file:
- `V6/mem2/backend/main.py`

### 2. Return real HTTP error statuses for file deletion failures

Severity: Medium

Problem:
- `DELETE /files/{filename}` returns plain JSON dicts for missing files and denied access
- In FastAPI, that means the handler can still respond with HTTP 200 unless an exception/response status is set
- The SOP explicitly expects missing/denied cases to behave like 404 or 403, not success

Why this matters:
- The V6 test cases specifically call out path traversal being blocked with `403` or `404`
- A 200 response on invalid deletion attempts breaks the contract and weakens the security story
- Downstream frontend behavior may incorrectly interpret failed deletes as successful

What to do:
- Raise `HTTPException(status_code=404, ...)` for missing uploads
- Raise `HTTPException(status_code=403, ...)` for denied paths
- Re-run the V6 delete and traversal test cases after the change

Relevant file:
- `V6/mem2/backend/main.py`

### 3. Align `GET /context` with the SOP response contract

Severity: Medium

Problem:
- The root SOP defines `/context` as a simple folder-to-filenames tree
- `V6/mem2/backend/main.py` currently returns per-file metadata objects with `name`, `size`, and `modified_at`
- That is richer data, but it is not the documented contract

Why this matters:
- mem1 and future consumers should be able to trust the root SOP response shape
- Silent contract drift can break clients built to the documented format
- “More data” is not automatically compliant when the API schema changes

What to do:
- Either change `/context` back to the SOP shape
- Or update the SSoT/SOP if the richer metadata response is an intentional contract change
- Keep the implementation and documentation in sync

Relevant files:
- `V6/mem2/backend/main.py`
- `mem2_backend_SOP_v4_onwards.md`

### 4. Add the missing V6 handoff artifact

Severity: Medium

Problem:
- The SOP requires `docs/handoffs/v6/mem2_handoff.md`
- `V6/mem2/docs/handoffs/` is currently missing
- That means the implementation does not have the required delivery evidence

Why this matters:
- mem2 owns the backend handoff trail, not just the code
- The handoff is part of release readiness and integration trust for mem1 and mem3
- Missing artifacts make sign-off incomplete even if most endpoints exist

What to do:
- Create `V6/mem2/docs/handoffs/v6/mem2_handoff.md`
- Include the full V6 endpoint list, workspace directory structure, security measures, known limitations, and future work as the SOP requires
- Make sure the handoff matches the actual implementation state

Relevant path:
- `V6/mem2/docs/handoffs/`

### 5. Remove “preview” language or finish the V6 contract cleanly

Severity: Low

Problem:
- `V6/mem2/backend/main.py` labels the V6 areas as `V6 Preview: File Management` and `V6 Preview: Context browsing`
- The repo structure suggests this is the actual V6 deliverable, not a preview branch
- The current naming makes the implementation sound provisional

Why this matters:
- Release code and release handoffs should present a consistent level of completion
- Calling core V6 features a preview increases ambiguity about whether the SOP is fully met

What to do:
- Remove the preview wording if this is intended as the final V6 backend
- Or explicitly document remaining gaps if the preview wording is intentional

Relevant file:
- `V6/mem2/backend/main.py`

## Recommended follow-up checks

- Run the V4, V5, and V6 backend validation flow against a live server
- Verify `POST /files/upload` rejects traversal-style filenames
- Verify `DELETE /files/{filename}` returns 404/403 instead of HTTP 200 on failure cases
- Confirm `/context` matches the documented contract expected by mem1
- Add the missing V6 handoff before marking mem2 complete

## Sign-off Recommendation

Do not mark `V6/mem2` fully complete until:
- upload path traversal is blocked
- delete failures return proper HTTP status codes
- the `/context` response contract is aligned with the SOP
- the required V6 handoff file is added
- the implementation is presented as final only if the actual V6 contract is complete
