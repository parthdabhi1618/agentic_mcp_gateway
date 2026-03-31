export default function StepViewer({ steps, logs }) {
  if (!steps || steps.length === 0) return null;

  return (
    <div style={{ marginBottom: 32 }}>
      <h2 style={{ fontSize: 20, marginBottom: 16, color: "var(--primary)" }}>Execution Trace</h2>
      {steps.map((step, i) => {
        const log = logs?.[i];
        const status = log?.status;
        const failed = status === "failed";

        return (
          <div
            key={i}
            className="animate-reveal"
            style={{
              background: failed ? "var(--error-container)" : "var(--surface-container-low)",
              borderRadius: 12,
              padding: 20,
              marginBottom: 16,
              boxShadow: failed ? "0 4px 20px rgba(159, 5, 25, 0.4)" : "0 4px 20px rgba(0,0,0,0.4)",
              animationDelay: `${i * 0.15}s`,
              transition: "transform 0.2s ease, background 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "scale(1.02)";
              if (!failed) e.currentTarget.style.background = "var(--surface-container-high)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "scale(1)";
              if (!failed) e.currentTarget.style.background = "var(--surface-container-low)";
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 12,
              }}
            >
              <strong
                style={{
                  display: "block",
                  fontSize: 18,
                  fontFamily: "var(--font-display)",
                  marginBottom: 12,
                  color: failed ? "var(--on-error-container)" : "var(--on-surface)",
                }}
              >
                Step {i + 1}:{" "}
                <span style={{ textTransform: "uppercase", color: failed ? "var(--on-error-container)" : "var(--primary)" }}>
                  {step.tool}
                </span>
              </strong>
              {status && (
                <span
                  style={{
                    padding: "4px 12px",
                    borderRadius: 9999,
                    fontSize: 12,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    background:
                      status === "success" ? "var(--tertiary-container)" : "var(--on-error-container)",
                    color:
                      status === "success" ? "var(--on-tertiary-container)" : "var(--on-error)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {status}
                </span>
              )}
            </div>

            <pre
              style={{
                marginTop: 8,
                fontSize: 14,
                background: "var(--surface-container-lowest)",
                padding: "16px",
                borderRadius: 8,
                overflowX: "auto",
                color: "var(--secondary)",
                fontFamily: "monospace",
                boxShadow: "0 0 8px rgba(110, 155, 255, 0.1)",
              }}
            >
              {JSON.stringify(step.args, null, 2)}
            </pre>

            {log && (
              <div
                style={{
                  marginTop: 12,
                  fontSize: 13,
                  fontFamily: "monospace",
                  color: failed ? "var(--on-error-container)" : "var(--outline-variant)",
                }}
              >
                {log.step}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
