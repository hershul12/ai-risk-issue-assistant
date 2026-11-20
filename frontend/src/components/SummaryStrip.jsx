export default function SummaryStrip({ summary, onPick }) {
  const s = summary || {};
  const review = s.by_status ? s.by_status["Pending Review"] || 0 : null;
  const items = [
    { key: "open", label: "Open records", value: s.open },
    { key: "overdue", label: "Overdue", value: s.overdue, alert: s.overdue > 0 },
    { key: "high", label: "High or critical", value: s.high_priority },
    { key: "review", label: "Awaiting review", value: review },
  ];
  return (
    <div className="strip" role="group" aria-label="Register summary">
      {items.map((it) => (
        <button
          key={it.key}
          type="button"
          className={`strip-item${it.alert ? " is-alert" : ""}`}
          onClick={() => onPick(it.key)}
        >
          <span className="strip-value">{it.value ?? "-"}</span>
          <span className="strip-label">{it.label}</span>
        </button>
      ))}
    </div>
  );
}