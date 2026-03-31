import { useState } from "react";

export default function PromptBox({ onSubmit, loading }) {
  const [text, setText] = useState("");

  const handleClick = () => {
    if (text.trim()) onSubmit(text.trim());
  };

  return (
    <div style={{ marginBottom: 32 }}>
      <textarea
        rows={4}
        style={{
          width: "100%",
          fontSize: 16,
          padding: 16,
          boxSizing: "border-box",
          background: "var(--surface-container-lowest)",
          color: "var(--on-surface)",
          border: "none",
          borderRadius: 8,
          outline: "none",
          resize: "vertical",
          boxShadow: "inset 0 2px 10px rgba(0,0,0,0.5)",
          fontFamily: "var(--font-body)"
        }}
        placeholder="Describe a workflow... e.g. Create a GitHub branch and notify Slack"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 16 }}>
        <button
          onClick={handleClick}
          disabled={loading}
          style={{
            padding: "12px 28px",
            fontSize: 16,
            fontWeight: 600,
            background: "linear-gradient(135deg, var(--primary), var(--primary-dim))",
            color: "var(--on-primary)",
            borderRadius: 8,
            boxShadow: "0 4px 14px rgba(129, 236, 255, 0.4)",
          }}
        >
          {loading ? "Running..." : "Run Workflow"}
        </button>
      </div>
    </div>
  );
}
