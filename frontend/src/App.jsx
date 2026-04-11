import { useState, useEffect, useRef } from "react";
import { createPlan, executeFromPlan, openJobStream, setPermission, schedulePlan, getContextTree } from "./api";
import SpotlightBar from "./components/SpotlightBar";
import PlanPreview from "./components/PlanPreview";
import ExecutionTimeline from "./components/ExecutionTimeline";
import AbortButton from "./components/AbortButton";
import SettingsDrawer from "./components/SettingsDrawer";
import FileManager from "./components/FileManager";

const FLOW = { IDLE: "idle", PLANNING: "planning", PREVIEW: "preview", EXECUTING: "executing", DONE: "done", SCHEDULED: "scheduled" };

export default function App() {
  const [flow, setFlow] = useState(FLOW.IDLE);
  const [plan, setPlan] = useState(null);
  const [events, setEvents] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [error, setError] = useState(null);
  const [spotlightOpen, setSpotlightOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [fileManagerOpen, setFileManagerOpen] = useState(false);
  const esRef = useRef(null);

  // Global CMD+K spotlight shortcut
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSpotlightOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const handlePromptSubmit = async (prompt, contextRefs = []) => {
    setFlow(FLOW.PLANNING);
    setError(null);
    setEvents([]);
    try {
      const result = await createPlan(prompt, contextRefs);
      setPlan(result);
      setFlow(FLOW.PREVIEW);
    } catch (e) {
      setError(e.message);
      setFlow(FLOW.IDLE);
    }
  };

  const handleConfirmPlan = async (planId, steps) => {
    setFlow(FLOW.EXECUTING);
    try {
      const { job_id } = await executeFromPlan(planId, steps);
      setJobId(job_id);
      esRef.current = openJobStream(
        job_id,
        (ev) => setEvents((p) => [...p, ev]),
        () => setFlow(FLOW.DONE),
        () => { setFlow(FLOW.DONE); setError("Stream disconnected"); }
      );
    } catch (e) {
      setError(e.message);
      setFlow(FLOW.PREVIEW);
    }
  };

  const handleSchedulePlan = async (planId, steps, scheduleConfig) => {
    try {
      await schedulePlan(planId, steps, scheduleConfig);
      setFlow(FLOW.SCHEDULED);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleReset = () => {
    setPlan(null);
    setFlow(FLOW.IDLE);
    setEvents([]);
    setError(null);
    setJobId(null);
  };

  return (
    <div style={{
      display: "flex",
      minHeight: "100vh",
      background: "#0a0f1e",
      fontFamily: "'Inter', 'Segoe UI', sans-serif",
      color: "#e2e8f0",
    }}>
      {/* Sidebar */}
      <div style={{
        width: 200,
        background: "rgba(15,23,42,0.9)",
        borderRight: "1px solid #1e293b",
        padding: "24px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}>
        <div style={{ fontFamily: "monospace", color: "#94a3b8", fontSize: 10,
                      letterSpacing: 2, marginBottom: 16, paddingLeft: 12 }}>
          AGENTIC OS
        </div>
        {[
          { label: "⚡ Run", action: () => setSpotlightOpen(true) },
          { label: "📁 Files", action: () => setFileManagerOpen(true) },
          { label: "⚙ Settings", action: () => setSettingsOpen(true) },
        ].map(({ label, action }) => (
          <button
            key={label}
            onClick={action}
            style={{
              background: "none",
              border: "none",
              color: "#94a3b8",
              textAlign: "left",
              padding: "9px 12px",
              borderRadius: 6,
              cursor: "pointer",
              fontFamily: "monospace",
              fontSize: 13,
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => e.target.style.background = "#1e293b"}
            onMouseLeave={(e) => e.target.style.background = "none"}
          >
            {label}
          </button>
        ))}
        <div style={{ marginTop: "auto", padding: "8px 12px", color: "#334155",
                      fontFamily: "monospace", fontSize: 10 }}>
          ⌘K to open Spotlight
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, padding: "40px 48px", overflowY: "auto", maxWidth: 860 }}>
        {flow === FLOW.IDLE && (
          <div style={{ textAlign: "center", paddingTop: "15vh" }}>
            <h1 style={{ fontSize: 28, fontFamily: "monospace", color: "#f1f5f9",
                         marginBottom: 8, letterSpacing: -1 }}>
              ⚡ Agentic OS
            </h1>
            <p style={{ color: "#475569", fontSize: 14, fontFamily: "monospace", marginBottom: 40 }}>
              Your AI-powered automation shell
            </p>
            <button
              onClick={() => setSpotlightOpen(true)}
              style={{
                padding: "14px 36px",
                background: "rgba(14,165,233,0.15)",
                border: "1px solid rgba(14,165,233,0.4)",
                borderRadius: 12,
                color: "#7dd3fc",
                fontFamily: "monospace",
                fontSize: 14,
                cursor: "pointer",
                letterSpacing: 0.5,
              }}
            >
              Press ⌘K or click to run a workflow
            </button>
          </div>
        )}
        {flow === FLOW.PLANNING && (
          <p style={{ color: "#94a3b8", fontFamily: "monospace", paddingTop: 40 }}>
            ⟳ Generating plan...
          </p>
        )}
        {flow === FLOW.PREVIEW && plan && (
          <PlanPreview
            planId={plan.plan_id}
            steps={plan.steps}
            onConfirm={handleConfirmPlan}
            onReplan={handleReset}
            onSchedule={handleSchedulePlan}
          />
        )}
        {flow === FLOW.EXECUTING && (
          <div style={{ marginBottom: 16 }}>
            <AbortButton jobId={jobId} onAborted={() => setFlow(FLOW.DONE)} />
          </div>
        )}
        {(flow === FLOW.EXECUTING || flow === FLOW.DONE) && (
          <ExecutionTimeline
            events={events}
            onGrantPermission={(t, a, s) => setPermission(t, a, s !== "deny", s)}
          />
        )}
        {flow === FLOW.SCHEDULED && (
          <div style={{
            marginTop: 40, padding: "20px 24px", background: "#0a1f0f",
            border: "1px solid #22c55e", borderRadius: 8, textAlign: "center",
          }}>
            <div style={{ color: "#22c55e", fontFamily: "monospace", fontSize: 16, marginBottom: 8 }}>
              ✓ Plan Scheduled Successfully
            </div>
            <p style={{ color: "#475569", fontFamily: "monospace", fontSize: 12 }}>
              Your workflow has been queued. It will execute at the scheduled time.
            </p>
            <button
              onClick={handleReset}
              style={{
                marginTop: 16, padding: "10px 24px", background: "#1e293b",
                border: "1px solid #334155", borderRadius: 8, color: "#94a3b8",
                cursor: "pointer", fontFamily: "monospace", fontSize: 13,
              }}
            >
              ↩ Back to Home
            </button>
          </div>
        )}
        {flow === FLOW.DONE && (
          <button
            onClick={handleReset}
            style={{
              marginTop: 24,
              padding: "10px 24px",
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#94a3b8",
              cursor: "pointer",
              fontFamily: "monospace",
              fontSize: 13,
            }}
          >
            ↩ Back to Home
          </button>
        )}
        {error && (
          <div style={{ marginTop: 16, padding: "12px 16px", background: "#1f0a0a",
                        border: "1px solid #ef4444", borderRadius: 6, color: "#ef4444",
                        fontFamily: "monospace", fontSize: 13 }}>
            ⚠ {error}
          </div>
        )}
      </div>

      {/* Overlays */}
      <SpotlightBar
        visible={spotlightOpen}
        onClose={() => setSpotlightOpen(false)}
        onSubmit={handlePromptSubmit}
      />
      <FileManager visible={fileManagerOpen} onClose={() => setFileManagerOpen(false)} />
      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
