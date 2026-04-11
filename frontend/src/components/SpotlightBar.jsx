import { useState, useEffect, useRef } from "react";
import { getContextTree } from "../api";

export default function SpotlightBar({ onSubmit, visible, onClose }) {
  const [text, setText] = useState("");
  const [contextTree, setContextTree] = useState(null);
  const [showContext, setShowContext] = useState(false);
  const [attachedRefs, setAttachedRefs] = useState([]);
  const inputRef = useRef(null);

  useEffect(() => {
    if (visible) {
      setText("");
      setAttachedRefs([]);
      setShowContext(false);
      setTimeout(() => inputRef.current?.focus(), 50);
      // Fetch context tree when spotlight opens
      getContextTree()
        .then((data) => setContextTree(data.tree || {}))
        .catch(() => setContextTree(null));
    }
  }, [visible]);

  const handleAttach = (folder, file) => {
    const ref = `@${folder}/${file}`;
    if (!attachedRefs.includes(ref)) {
      setAttachedRefs((p) => [...p, ref]);
    }
    setShowContext(false);
    inputRef.current?.focus();
  };

  const handleRemoveRef = (ref) => {
    setAttachedRefs((p) => p.filter((r) => r !== ref));
  };

  const handleSubmit = () => {
    if (!text.trim()) return;
    // Extract @context refs from text as well
    const textRefs = (text.match(/@[\w/._-]+/g) || []);
    const allRefs = [...new Set([...attachedRefs, ...textRefs])];
    onSubmit(text.trim(), allRefs);
    onClose();
  };

  if (!visible) return null;

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, zIndex: 2000,
        background: "rgba(0,0,0,0.7)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        paddingTop: "15vh",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 640,
          background: "rgba(30,41,59,0.95)",
          border: "1px solid rgba(100,116,139,0.4)",
          borderRadius: 16,
          boxShadow: "0 32px 80px rgba(0,0,0,0.8)",
          overflow: "hidden",
        }}
      >
        {/* Input row */}
        <div style={{ display: "flex", alignItems: "center", padding: "16px 20px", gap: 12 }}>
          <span style={{ fontSize: 20 }}>⚡</span>
          <input
            ref={inputRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && text.trim()) handleSubmit();
              if (e.key === "Escape") onClose();
            }}
            placeholder='Run a workflow... or type @context/github_context to attach context'
            style={{
              flex: 1,
              background: "none",
              border: "none",
              outline: "none",
              color: "#f1f5f9",
              fontFamily: "monospace",
              fontSize: 16,
            }}
          />
          <button
            onClick={() => setShowContext(!showContext)}
            style={{
              background: showContext ? "#0ea5e9" : "rgba(14,165,233,0.15)",
              border: "1px solid rgba(14,165,233,0.4)",
              borderRadius: 6,
              color: "#7dd3fc",
              padding: "4px 10px",
              cursor: "pointer",
              fontFamily: "monospace",
              fontSize: 11,
            }}
          >
            @ Context
          </button>
        </div>

        {/* Attached context refs */}
        {attachedRefs.length > 0 && (
          <div style={{ padding: "0 20px 10px", display: "flex", flexWrap: "wrap", gap: 6 }}>
            {attachedRefs.map((ref) => (
              <span key={ref} style={{
                background: "#0f172a", border: "1px solid #334155", borderRadius: 4,
                padding: "2px 8px", fontSize: 11, fontFamily: "monospace", color: "#7dd3fc",
                display: "flex", alignItems: "center", gap: 4,
              }}>
                {ref}
                <span
                  onClick={() => handleRemoveRef(ref)}
                  style={{ cursor: "pointer", color: "#ef4444", fontSize: 13 }}
                >
                  ×
                </span>
              </span>
            ))}
          </div>
        )}

        {/* Context tree browser */}
        {showContext && contextTree && (
          <div style={{
            borderTop: "1px solid #1e293b", padding: "12px 20px",
            maxHeight: 200, overflowY: "auto",
          }}>
            <div style={{ color: "#94a3b8", fontFamily: "monospace", fontSize: 11, marginBottom: 8 }}>
              Available Context — click to attach
            </div>
            {Object.entries(contextTree).map(([folder, files]) => (
              <div key={folder} style={{ marginBottom: 8 }}>
                <div style={{ color: "#64748b", fontFamily: "monospace", fontSize: 11, marginBottom: 4 }}>
                  📂 {folder}/
                </div>
                {(Array.isArray(files) ? files : []).map((file) => (
                  <button
                    key={file}
                    onClick={() => handleAttach(folder, file)}
                    style={{
                      display: "block", background: "none", border: "none",
                      color: "#7dd3fc", fontFamily: "monospace", fontSize: 12,
                      cursor: "pointer", padding: "2px 0 2px 16px", textAlign: "left",
                    }}
                  >
                    📄 {file}
                  </button>
                ))}
              </div>
            ))}
            {Object.keys(contextTree).length === 0 && (
              <div style={{ color: "#475569", fontFamily: "monospace", fontSize: 11 }}>
                No context files found.
              </div>
            )}
          </div>
        )}

        {/* Footer hints */}
        <div style={{
          borderTop: "1px solid #1e293b",
          padding: "8px 20px",
          color: "#475569",
          fontSize: 11,
          fontFamily: "monospace",
          display: "flex",
          gap: 24,
        }}>
          <span>↵ Run</span>
          <span>@ Browse Context</span>
          <span>Esc  Dismiss</span>
        </div>
      </div>
    </div>
  );
}
