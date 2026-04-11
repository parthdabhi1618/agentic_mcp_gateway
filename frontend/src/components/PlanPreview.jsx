import { useState } from "react";

const TOOL_ICONS = {
  github: "🐙", slack: "💬", jira: "🔵", sheets: "📊",
  linear: "⚡", notion: "📄", discord: "🎮"
};

const TOOL_COLORS = {
  github: "#6e40c9", slack: "#4a154b", jira: "#0052cc",
  sheets: "#0f9d58", linear: "#5e6ad2", notion: "#374151", discord: "#5865f2"
};

function EditableArg({ label, value, onChange }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
      <span style={{ color: "#64748b", fontFamily: "monospace", fontSize: 11, minWidth: 80 }}>
        {label}
      </span>
      <input
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        style={{
          flex: 1,
          background: "#0f172a",
          border: "1px solid #334155",
          borderRadius: 4,
          padding: "4px 10px",
          color: "#f1f5f9",
          fontFamily: "monospace",
          fontSize: 12,
          outline: "none",
        }}
      />
    </div>
  );
}

export default function PlanPreview({ planId, steps, onConfirm, onReplan, onSchedule }) {
  const [localSteps, setLocalSteps] = useState(
    (steps || []).map((s) => ({ ...s, args: { ...(s.args || {}) } }))
  );
  const [isScheduling, setIsScheduling] = useState(false);
  const [scheduleType, setScheduleType] = useState("once");
  const [scheduleValue, setScheduleValue] = useState("");
  const [scheduleFeedback, setScheduleFeedback] = useState(null);

  const updateArg = (stepIdx, key, value) => {
    setLocalSteps((prev) => {
      const updated = [...prev];
      updated[stepIdx] = {
        ...updated[stepIdx],
        args: { ...updated[stepIdx].args, [key]: value }
      };
      return updated;
    });
  };

  const handleScheduleSubmit = () => {
    if (!scheduleValue.trim()) return;
    const config = scheduleType === "once"
      ? { type: "once", run_at: scheduleValue }
      : { type: "recurring", cron: scheduleValue };
    if (onSchedule) {
      onSchedule(planId, localSteps, config);
      setScheduleFeedback("✓ Schedule submitted");
      setTimeout(() => setScheduleFeedback(null), 3000);
    }
  };

  return (
    <div style={{ marginTop: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ color: "#e2e8f0", fontSize: 16, fontFamily: "monospace",
                     textTransform: "uppercase", letterSpacing: 1, margin: 0 }}>
          🗺 Plan Preview — {localSteps.length} step{localSteps.length !== 1 ? "s" : ""}
        </h2>
        <span style={{ color: "#475569", fontSize: 11, fontFamily: "monospace" }}>
          Edit fields below before confirming
        </span>
      </div>

      {localSteps.map((step, i) => {
        const toolColor = TOOL_COLORS[step.tool] || "#555";
        const icon = TOOL_ICONS[step.tool] || "🔧";
        return (
          <div
            key={step.step_id || i}
            style={{
              border: `1px solid ${toolColor}40`,
              borderLeft: `4px solid ${toolColor}`,
              borderRadius: 8,
              padding: "16px 20px",
              marginBottom: 10,
              background: "#1e293b",
              animation: `fadeSlideIn 0.3s ease ${i * 0.07}s both`,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
              <span style={{ fontSize: 18 }}>{icon}</span>
              <span style={{ color: "#f1f5f9", fontFamily: "monospace", fontWeight: 700 }}>
                Step {i + 1}
              </span>
              <span style={{
                background: toolColor,
                color: "white",
                padding: "2px 10px",
                borderRadius: 4,
                fontSize: 11,
                fontFamily: "monospace",
                textTransform: "uppercase",
              }}>
                {step.tool}
              </span>
              <span style={{ color: "#94a3b8", fontFamily: "monospace", fontSize: 13 }}>
                {step.action}
              </span>
              {step.requires_permission && (
                <span style={{ color: "#f59e0b", fontSize: 11, fontFamily: "monospace" }}>
                  ⚠ requires permission
                </span>
              )}
            </div>

            {step.args && Object.entries(step.args).map(([key, val]) => (
              <EditableArg
                key={key}
                label={key}
                value={val}
                onChange={(newVal) => updateArg(i, key, newVal)}
              />
            ))}
          </div>
        );
      })}

      <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
        <button
          onClick={() => onConfirm(planId, localSteps)}
          style={{
            padding: "11px 32px",
            background: "#22c55e",
            color: "#0f172a",
            border: "none",
            borderRadius: 6,
            fontFamily: "monospace",
            fontWeight: 700,
            fontSize: 14,
            cursor: "pointer",
          }}
        >
          ✓ Confirm & Run Plan
        </button>
        <button
          onClick={() => setIsScheduling(!isScheduling)}
          style={{
            padding: "11px 24px",
            background: "transparent",
            color: "#0ea5e9",
            border: "1px solid #0ea5e9",
            borderRadius: 6,
            fontFamily: "monospace",
            fontSize: 14,
            cursor: "pointer",
          }}
        >
          ⏱ Schedule...
        </button>
        <button
          onClick={onReplan}
          style={{
            padding: "11px 24px",
            background: "transparent",
            color: "#94a3b8",
            border: "1px solid #334155",
            borderRadius: 6,
            fontFamily: "monospace",
            fontSize: 14,
            cursor: "pointer",
          }}
        >
          ↩ Re-plan
        </button>
      </div>

      {isScheduling && (
        <div style={{
          marginTop: 16, padding: 16, background: "#0f172a",
          border: "1px solid #334155", borderRadius: 8,
        }}>
          <div style={{ color: "#94a3b8", fontFamily: "monospace", fontSize: 12, marginBottom: 10 }}>
            Configure Schedule
          </div>
          <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
            <select
              value={scheduleType}
              onChange={(e) => { setScheduleType(e.target.value); setScheduleValue(""); }}
              style={{
                background: "#1e293b", border: "1px solid #334155", borderRadius: 4,
                padding: "8px 12px", color: "#f1f5f9", fontFamily: "monospace", fontSize: 13, outline: "none",
              }}
            >
              <option value="once">Once</option>
              <option value="recurring">Recurring</option>
            </select>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <input
              autoFocus
              type={scheduleType === "once" ? "datetime-local" : "text"}
              value={scheduleValue}
              onChange={(e) => setScheduleValue(e.target.value)}
              placeholder={scheduleType === "once" ? "" : "0 9 * * *"}
              style={{
                flex: 1, background: "#1e293b", border: "1px solid #334155", borderRadius: 4,
                padding: "8px 12px", color: "#f1f5f9", fontFamily: "monospace", fontSize: 13, outline: "none",
              }}
            />
            <button
              onClick={handleScheduleSubmit}
              disabled={!scheduleValue.trim()}
              style={{
                padding: "8px 20px",
                background: scheduleValue.trim() ? "#0ea5e9" : "#334155",
                color: "white", border: "none", borderRadius: 6,
                fontFamily: "monospace", fontWeight: 700, fontSize: 13,
                cursor: scheduleValue.trim() ? "pointer" : "default",
              }}
            >
              Confirm Schedule
            </button>
          </div>
          {scheduleFeedback && (
            <div style={{ marginTop: 8, color: "#4ade80", fontFamily: "monospace", fontSize: 11 }}>
              {scheduleFeedback}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
