import { useState } from "react";
import { abortJob } from "../api";

export default function AbortButton({ jobId, onAborted }) {
  const [aborting, setAborting] = useState(false);

  const handleAbort = async () => {
    if (!jobId || aborting) return;
    setAborting(true);
    try {
      await abortJob(jobId);
      onAborted?.();
    } catch (e) {
      console.error("Abort failed:", e);
    }
  };

  return (
    <button
      onClick={handleAbort}
      disabled={aborting}
      style={{
        padding: "8px 20px",
        background: aborting ? "#374151" : "#dc2626",
        color: "white",
        border: "none",
        borderRadius: 6,
        cursor: aborting ? "default" : "pointer",
        fontFamily: "monospace",
        fontSize: 13,
        fontWeight: "bold",
        letterSpacing: 0.5,
      }}
    >
      {aborting ? "⏳ Aborting..." : "⬛ Abort Execution"}
    </button>
  );
}
