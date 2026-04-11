import { useState, useEffect, useRef } from "react";
import { getFiles, uploadFile, deleteFile } from "../api";

const TYPE_ICONS = { upload: "📁", generated: "🤖" };

export default function FileManager({ visible, onClose }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const fileInputRef = useRef(null);

  const refresh = () => {
    setLoading(true);
    getFiles().then((d) => setFiles(d.files || [])).finally(() => setLoading(false));
  };

  useEffect(() => { if (visible) refresh(); }, [visible]);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    await uploadFile(file);
    refresh();
  };

  const handleDelete = async (name) => {
    setDeleting(name);
    await deleteFile(name);
    setDeleting(null);
    refresh();
  };

  if (!visible) return null;

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 1500,
      background: "rgba(0,0,0,0.6)",
      backdropFilter: "blur(6px)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}>
      <div style={{
        width: 680,
        maxHeight: "75vh",
        background: "#1e293b",
        border: "1px solid #334155",
        borderRadius: 16,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        boxShadow: "0 24px 64px rgba(0,0,0,0.7)",
      }}>
        <div style={{
          padding: "16px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #334155",
          background: "#0f172a",
        }}>
          <h2 style={{ color: "#f1f5f9", fontFamily: "monospace", fontSize: 14, margin: 0 }}>
            📁 File Manager
          </h2>
          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={() => fileInputRef.current?.click()}
              style={{ padding: "6px 16px", background: "#0ea5e9", color: "white",
                       border: "none", borderRadius: 6, cursor: "pointer", fontFamily: "monospace", fontSize: 12 }}
            >
              + Upload
            </button>
            <input ref={fileInputRef} type="file" style={{ display: "none" }} onChange={handleUpload} />
            <button onClick={onClose}
              style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: 18 }}>
              ✕
            </button>
          </div>
        </div>

        <div style={{ overflowY: "auto", padding: 16, flex: 1 }}>
          {loading && <p style={{ color: "#475569", fontFamily: "monospace", textAlign: "center" }}>Loading...</p>}
          {!loading && files.length === 0 && (
            <p style={{ color: "#475569", fontFamily: "monospace", textAlign: "center", marginTop: 40 }}>
              No files yet. Upload one to get started.
            </p>
          )}
          {files.map((file) => (
            <div key={file.name} style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "10px 14px",
              marginBottom: 8,
              background: "#0f172a",
              borderRadius: 8,
              border: "1px solid #1e293b",
            }}>
              <div>
                <span style={{ marginRight: 8 }}>{TYPE_ICONS[file.type] || "📄"}</span>
                <span style={{ color: "#f1f5f9", fontFamily: "monospace", fontSize: 13 }}>{file.name}</span>
                <span style={{ color: "#475569", fontFamily: "monospace", fontSize: 11, marginLeft: 12 }}>
                  {(file.size / 1024).toFixed(1)} KB · {file.type}
                </span>
              </div>
              <button
                onClick={() => handleDelete(file.name)}
                disabled={deleting === file.name}
                style={{ background: "none", border: "none", color: "#ef4444",
                         cursor: "pointer", fontFamily: "monospace", fontSize: 12 }}
              >
                {deleting === file.name ? "..." : "Delete"}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
