import { useEffect, useRef } from "react";

const STATUS_COLORS = {
  pending:           { bg: "#1a1a2e", border: "#444",    badge: "#888",    label: "PENDING" },
  running:           { bg: "#0f2027", border: "#0ea5e9", badge: "#0ea5e9", label: "RUNNING" },
  success:           { bg: "#0a1f0f", border: "#22c55e", badge: "#22c55e", label: "SUCCESS" },
  failed:            { bg: "#1f0a0a", border: "#ef4444", badge: "#ef4444", label: "FAILED" },
  permission_denied: { bg: "#1f1a00", border: "#f59e0b", badge: "#f59e0b", label: "PERMISSION DENIED" },
  aborted:           { bg: "#1a1a1a", border: "#6b7280", badge: "#6b7280", label: "ABORTED" },
};

const TOOL_COLORS = {
  github:  "#6e40c9",
  slack:   "#4a154b",
  jira:    "#0052cc",
  sheets:  "#0f9d58",
  linear:  "#5e6ad2",
  notion:  "#000000",
  discord: "#5865f2",
};

export default function ExecutionTimeline({ events, onGrantPermission }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  if (!events || events.length === 0) return null;

  return (
    <div style={{ marginTop: 24 }}>
      <h2 style={{ color: "#e2e8f0", fontSize: 16, marginBottom: 16, letterSpacing: 1,
                   textTransform: "uppercase", fontFamily: "monospace" }}>
        ⚡ Execution Timeline
      </h2>
      {events.map((event, i) => {
        const colors = STATUS_COLORS[event.status] || STATUS_COLORS.pending;
        const toolColor = TOOL_COLORS[event.tool] || "#555";
        const isPermDenied = event.status === "permission_denied";

        return (
          <div
            key={event.step_id || i}
            style={{
              border: `1px solid ${colors.border}`,
              borderLeft: `4px solid ${toolColor}`,
              borderRadius: 8,
              padding: "14px 18px",
              marginBottom: 10,
              background: colors.bg,
              animation: "fadeSlideIn 0.3s ease forwards",
              opacity: 0,
              animationDelay: `${i * 0.05}s`,
              animationFillMode: "forwards",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <span style={{
                  background: toolColor,
                  color: "white",
                  padding: "2px 10px",
                  borderRadius: 4,
                  fontSize: 11,
                  fontFamily: "monospace",
                  marginRight: 10,
                  textTransform: "uppercase",
                }}>
                  {event.tool}
                </span>
                <span style={{ color: "#94a3b8", fontFamily: "monospace", fontSize: 13 }}>
                  {event.action}
                </span>
              </div>
              <span style={{
                background: colors.badge,
                color: "#0f172a",
                fontWeight: "bold",
                fontSize: 11,
                padding: "2px 10px",
                borderRadius: 20,
                fontFamily: "monospace",
              }}>
                {colors.label}
              </span>
            </div>

            {event.result && typeof event.result === "object" && Object.keys(event.result).length > 0 && (
              <pre style={{
                marginTop: 10,
                fontSize: 11,
                color: "#64748b",
                background: "rgba(0,0,0,0.3)",
                padding: "8px 12px",
                borderRadius: 4,
                overflow: "auto",
                maxHeight: 120,
              }}>
                {JSON.stringify(event.result, null, 2)}
              </pre>
            )}

            {event.error && (
              <div style={{ marginTop: 8, color: "#ef4444", fontSize: 12, fontFamily: "monospace" }}>
                ↳ {event.error}
              </div>
            )}

            {isPermDenied && onGrantPermission && (
              <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
                <span style={{ color: "#f59e0b", fontSize: 12, fontFamily: "monospace" }}>
                  Agent wants to run: {event.tool}.{event.action}
                </span>
                <button
                  onClick={() => onGrantPermission(event.tool, event.action, "once")}
                  style={{
                    padding: "4px 12px", fontSize: 12, background: "#f59e0b",
                    color: "#0f172a", border: "none", borderRadius: 4, cursor: "pointer",
                    fontFamily: "monospace",
                  }}
                >
                  Allow Once
                </button>
                <button
                  onClick={() => onGrantPermission(event.tool, event.action, "always")}
                  style={{
                    padding: "4px 12px", fontSize: 12, background: "#22c55e",
                    color: "#0f172a", border: "none", borderRadius: 4, cursor: "pointer",
                    fontFamily: "monospace",
                  }}
                >
                  Always Allow
                </button>
                <button
                  onClick={() => onGrantPermission(event.tool, event.action, "deny")}
                  style={{
                    padding: "4px 12px", fontSize: 12, background: "#ef4444",
                    color: "white", border: "none", borderRadius: 4, cursor: "pointer",
                    fontFamily: "monospace",
                  }}
                >
                  Never
                </button>
              </div>
            )}
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
