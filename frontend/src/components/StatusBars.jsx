import { STATUSES } from "../utils";

export default function StatusBars({ summary }) {
  const by = (summary && summary.by_status) || {};
  const max = Math.max(1, ...STATUSES.map((s) => by[s] || 0));
  return (
    <section className="panel" aria-labelledby="status-title">
      <h2 id="status-title">Records by status</h2>
      {STATUSES.map((s) => {
        const n = by[s] || 0;
        return (
          <div className="bar-row" key={s}>
            <span>{s}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(n / max) * 100}%` }} />
            </div>
            <span className="bar-count">{n}</span>
          </div>
        );
      })}
    </section>
  );
}