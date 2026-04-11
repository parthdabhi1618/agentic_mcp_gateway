import { useState, useEffect } from "react";
import { getKeyStatus, connectKey } from "../api";

const ALL_TOOLS = ["github", "slack", "jira", "sheets", "linear", "notion", "discord"];

export default function SettingsDrawer({ open, onClose }) {
  const [statuses, setStatuses] = useState({});
  const [inputs, setInputs] = useState({});
  const [connecting, setConnecting] = useState({});
  const [feedback, setFeedback] = useState({});

  useEffect(() => {
    if (open) {
      getKeyStatus().then(setStatuses).catch(console.error);
    }
  }, [open]);

  const handleConnect = async (tool) => {
    const key = inputs[tool];
    if (!key) return;
    setConnecting((p) => ({ ...p, [tool]: true }));
    try {
      const result = await connectKey(tool, key);
      setStatuses((p) => ({ ...p, [tool]: result.status === "connected" ? "connected" : "failed" }));
      setFeedback((p) => ({ ...p, [tool]: result.status === "connected" ? "✓ Connected" : "✗ Failed — check key" }));
    } catch {
      setFeedback((p) => ({ ...p, [tool]: "✗ Error" }));
    } finally {
      setConnecting((p) => ({ ...p, [tool]: false }));
    }
  };

  if (!open) return null;

  return (
    <div style={{
      position: "fixed", top: 0, right: 0, height: "100vh", width: 360,
      background: "#1e293b", borderLeft: "1px solid #334155",
      zIndex: 3000, padding: 24, overflowY: "auto",
      boxShadow: "-8px 0 32px rgba(0,0,0,0.5)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
        <h2 style={{ color: "#f1f5f9", fontFamily: "monospace", fontSize: 15, margin: 0 }}>
          ⚙ Tool Connections
        </h2>
        <button
          onClick={onClose}
          style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: 18 }}
        >
          ✕
        </button>
      </div>

      {ALL_TOOLS.map((tool) => {
        const status = statuses[tool];
        const isConnected = status === "connected";
        return (
          <div key={tool} style={{
            border: "1px solid #334155",
            borderRadius: 8,
            padding: "14px 16px",
            marginBottom: 12,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <span style={{ color: "#f1f5f9", fontFamily: "monospace", textTransform: "uppercase", fontSize: 12 }}>
                {tool}
              </span>
              <span style={{
                padding: "2px 10px",
                borderRadius: 20,
                fontSize: 11,
                fontFamily: "monospace",
                background: isConnected ? "#14532d" : "#1f2937",
                color: isConnected ? "#4ade80" : "#6b7280",
              }}>
                {isConnected ? "● connected" : "○ not connected"}
              </span>
            </div>
            <input
              type="password"
              placeholder={`${tool.toUpperCase()}_TOKEN or API key`}
              value={inputs[tool] || ""}
              onChange={(e) => setInputs((p) => ({ ...p, [tool]: e.target.value }))}
              style={{
                width: "100%",
                boxSizing: "border-box",
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 4,
                padding: "6px 10px",
                color: "#f1f5f9",
                fontFamily: "monospace",
                fontSize: 12,
                outline: "none",
                marginBottom: 8,
              }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <button
                onClick={() => handleConnect(tool)}
                disabled={connecting[tool] || !inputs[tool]}
                style={{
                  padding: "5px 16px",
                  background: connecting[tool] ? "#1e3a5f" : "#0ea5e9",
                  color: "white",
                  border: "none",
                  borderRadius: 4,
                  cursor: connecting[tool] || !inputs[tool] ? "default" : "pointer",
                  fontFamily: "monospace",
                  fontSize: 12,
                }}
              >
                {connecting[tool] ? "Testing..." : "Connect →"}
              </button>
              {feedback[tool] && (
                <span style={{
                  fontSize: 11,
                  fontFamily: "monospace",
                  color: feedback[tool].startsWith("✓") ? "#4ade80" : "#ef4444",
                }}>
                  {feedback[tool]}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
