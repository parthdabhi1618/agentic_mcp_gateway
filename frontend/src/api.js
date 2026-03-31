export async function runWorkflow(prompt) {
  const res = await fetch("http://localhost:8000/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error("Server error: " + res.status);
  return res.json();
}
