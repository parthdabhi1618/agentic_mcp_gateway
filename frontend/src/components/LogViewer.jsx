export default function LogViewer({ logs }) {
  if (!logs || logs.length === 0) return null;

  return (
    <div style={{
      background: "var(--surface-container)",
      padding: 24,
      borderRadius: 16,
      boxShadow: "0 8px 32px rgba(0,0,0,0.4)"
    }}>
      <h2 style={{ fontSize: 20, marginBottom: 16, color: "var(--primary)" }}>System Logs</h2>
      {logs.map((log, i) => {
        const isSuccess = log.status === "success";
        return (
          <div key={i} style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "12px 16px",
            marginBottom: 8,
            borderRadius: 8,
            background: isSuccess ? "var(--tertiary-container)" : "var(--error-container)",
            color: isSuccess ? "var(--on-tertiary-container)" : "var(--on-error-container)",
            fontFamily: "var(--font-body)"
          }}>
            <span style={{ fontFamily: "monospace", fontSize: 14 }}>{log.step}</span>
            <span style={{
              fontWeight: "bold",
              fontSize: 12,
              letterSpacing: "0.05em",
              padding: "4px 12px",
              borderRadius: 9999,
              background: "rgba(0,0,0,0.1)",
              textTransform: "uppercase"
            }}>
              {log.status}
            </span>
          </div>
        );
      })}
    </div>
  );
}
