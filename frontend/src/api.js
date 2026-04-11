const BASE = "http://localhost:8000";

export async function runWorkflow(prompt) {
  const res = await fetch(`${BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error("Server error: " + res.status);
  return res.json();
}

export async function executeJob(steps) {
  const res = await fetch(`${BASE}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ steps, execution_mode: "run_now" }),
  });
  if (!res.ok) throw new Error("Execute failed: " + res.status);
  return res.json();
}

export function openJobStream(jobId, onEvent, onDone, onError) {
  const es = new EventSource(`${BASE}/job/${jobId}/stream`);
  es.onmessage = (e) => {
    try {
      const event = JSON.parse(e.data);
      if (event.keepalive) return;
      onEvent(event);
      if (["success", "failed", "aborted"].includes(event.status) && event.step_id === "__final__") {
        es.close();
        onDone();
      }
    } catch (parseErr) {
      console.warn("SSE parse error:", parseErr);
    }
  };
  es.onerror = (err) => {
    es.close();
    onError(err);
  };
  return es;
}

export async function abortJob(jobId) {
  const res = await fetch(`${BASE}/job/${jobId}/abort`, { method: "POST" });
  return res.json();
}

export async function getPermissions() {
  const res = await fetch(`${BASE}/permissions`);
  return res.json();
}

export async function setPermission(tool, action, allowed, scope = "always") {
  const res = await fetch(`${BASE}/permissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, action, allowed, scope }),
  });
  return res.json();
}

export async function createPlan(prompt, contextRefs = [], toolScope = []) {
  const res = await fetch(`${BASE}/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, context_refs: contextRefs, tool_scope: toolScope }),
  });
  if (!res.ok) throw new Error("Plan failed: " + res.status);
  return res.json();
}

export async function executeFromPlan(planId, steps) {
  const res = await fetch(`${BASE}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan_id: planId, steps, execution_mode: "run_now" }),
  });
  if (!res.ok) throw new Error("Execute failed: " + res.status);
  return res.json();
}

export async function getKeyStatus() {
  const res = await fetch(`${BASE}/keys/status`);
  return res.json();
}

export async function connectKey(tool, key) {
  const res = await fetch(`${BASE}/keys/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, key }),
  });
  return res.json();
}

export async function schedulePlan(planId, steps, scheduleConfig) {
  const res = await fetch(`${BASE}/schedule`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan_id: planId, steps, schedule: scheduleConfig }),
  });
  if (!res.ok) throw new Error("Schedule failed: " + res.status);
  return res.json();
}

export async function getFiles() {
  const res = await fetch(`${BASE}/files`);
  return res.json();
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  
  const res = await fetch(`${BASE}/files/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Upload failed: " + res.statusText);
  return res.json();
}

export async function deleteFile(filename) {
  const res = await fetch(`${BASE}/files/${filename}`, {
    method: "DELETE"
  });
  if (!res.ok) throw new Error("Delete failed: " + res.statusText);
  return res.json();
}

export async function getContextTree() {
  const res = await fetch(`${BASE}/context`);
  return res.json();
}
