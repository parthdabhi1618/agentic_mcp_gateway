import { useState } from "react";

export default function PromptBox({ onSubmit, loading }) {
  const [text, setText] = useState("");

  return (
    <div style={{ marginBottom: 20 }}>
      <textarea
        rows={3}
        placeholder="Describe a workflow... e.g. Create a GitHub branch fix/auth, notify #dev on Slack, and open a Linear issue"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter" && e.metaKey && text.trim()) onSubmit(text.trim()); }}
        style={{
          width: "100%",
          fontSize: 14,
          padding: "14px 16px",
          boxSizing: "border-box",
          background: "#1e293b",
          border: "1px solid #334155",
          borderRadius: 8,
          color: "#f1f5f9",
          fontFamily: "monospace",
          resize: "vertical",
          outline: "none",
        }}
      />
      <button
        onClick={() => { if (text.trim()) onSubmit(text.trim()); }}
        disabled={loading || !text.trim()}
        style={{
          marginTop: 8,
          padding: "10px 28px",
          fontSize: 14,
          background: loading ? "#1e3a5f" : "#0ea5e9",
          color: "white",
          border: "none",
          borderRadius: 6,
          cursor: loading ? "default" : "pointer",
          fontFamily: "monospace",
          fontWeight: "bold",
        }}
      >
        {loading ? "⟳ Running..." : "▶ Run Workflow"}
      </button>
    </div>
  );
}
