import { useState, useEffect } from "react";
import { runWorkflow } from "./api";
import PromptBox from "./components/PromptBox";
import StepViewer from "./components/StepViewer";
import LogViewer from "./components/LogViewer";
import HistorySidebar from "./components/HistorySidebar";
import ProgressBar from "./components/ProgressBar";
import "./App.css";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastPrompt, setLastPrompt] = useState("");
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const saved = localStorage.getItem("agentic_history");
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse history", e);
      }
    }
  }, []);

  const handleRestore = (run) => {
    setLastPrompt(run.prompt);
    setResult({ steps: run.steps, logs: run.logs });
    setError(null);
  };

  const handleRun = async (prompt) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setLastPrompt(prompt);
    try {
      const data = await runWorkflow(prompt);
      
      // Fallback safely if steps/logs are completely missing
      const safeData = {
        steps: data?.steps || [],
        logs: data?.logs || []
      };
      
      setResult(safeData);

      // Save to history
      const newRun = {
        prompt,
        steps: safeData.steps,
        logs: safeData.logs,
        timestamp: Date.now()
      };
      
      setHistory(prev => {
        const next = [newRun, ...prev].slice(0, 10);
        localStorage.setItem("agentic_history", JSON.stringify(next));
        return next;
      });

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyJson = () => {
    if (result) {
      navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    }
  };

  return (
    <div className="app-layout">
      <main className="main-content">
        <header style={{ marginBottom: 48 }}>
          <h1 style={{ 
            fontSize: 48, 
            fontWeight: 700, 
            letterSpacing: "-1px",
            color: "var(--on-surface)",
            textShadow: "0 0 20px rgba(129, 236, 255, 0.3)"
          }}>
            Agentic MCP<span style={{ color: "var(--primary)" }}>.</span>
          </h1>
          <p style={{ color: "var(--outline-variant)", fontSize: 18 }}>The Sentinel Interface</p>
        </header>

        <PromptBox onSubmit={handleRun} loading={loading} />
        <ProgressBar loading={loading} />
        
        {error && (
          <div style={{ 
            color: "var(--on-error-container)", 
            padding: 16, 
            background: "var(--error-container)", 
            borderRadius: 8,
            marginBottom: 32,
            fontWeight: 500
          }}>
            ALERT: {error}
          </div>
        )}

        {result && (
          <div
            className="glass-panel"
            style={{
              padding: 16,
              borderRadius: 10,
              marginBottom: 20,
              fontStyle: "italic",
            }}
          >
            Prompt: "{lastPrompt}"
          </div>
        )}

        {result && <StepViewer steps={result.steps} logs={result.logs} />}
        {result && <LogViewer logs={result.logs} />}
        
        {result && (
          <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
            <button
              onClick={() => setResult(null)}
              style={{
                padding: "10px 20px",
                borderRadius: 8,
                background: "transparent",
                border: "1px solid rgba(68, 72, 85, 0.5)",
                color: "var(--on-surface)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'var(--surface-container-high)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
              }}
            >
              Clear & Run Again
            </button>
            <button
              onClick={handleCopyJson}
              style={{
                padding: "10px 20px",
                borderRadius: 8,
                background: "linear-gradient(90deg, var(--primary), var(--primary-dim))",
                color: "var(--on-primary-fixed)",
                fontWeight: 600
              }}
            >
              Copy JSON
            </button>
          </div>
        )}
      </main>

      <aside className="sidebar-content">
        <HistorySidebar history={history} onRestore={handleRestore} />
      </aside>
    </div>
  );
}
