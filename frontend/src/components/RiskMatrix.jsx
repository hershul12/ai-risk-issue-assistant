import { priorityFor } from "../utils";

const ROWS = [5, 4, 3, 2, 1];
const COLS = [1, 2, 3, 4, 5];

export default function RiskMatrix({ items, selected, onSelect }) {
  const counts = {};
  items.forEach((it) => {
    if (it.status === "Closed") return;
    const key = `${it.probability}-${it.impact}`;
    counts[key] = (counts[key] || 0) + 1;
  });

  return (
    <section className="panel" aria-labelledby="matrix-title">
      <h2 id="matrix-title">Risk matrix</h2>
      <p className="muted">
        Open records by probability and impact. Select a cell to filter the register.
      </p>
      <div className="matrix">
        <div className="matrix-ylabel">Probability</div>
        <div className="matrix-rows">
          {ROWS.map((p) => (
            <span key={p}>{p}</span>
          ))}
        </div>
        <div className="matrix-grid">
          {ROWS.map((p) =>
            COLS.map((i) => {
              const n = counts[`${p}-${i}`] || 0;
              const band = priorityFor(p * i).toLowerCase();
              const isSelected = !!selected && selected.p === p && selected.i === i;
              return (
                <button
                  key={`${p}-${i}`}
                  type="button"
                  className={`cell cell-${band}${isSelected ? " is-selected" : ""}`}
                  aria-pressed={isSelected}
                  aria-label={`Probability ${p}, impact ${i}, ${n} open records`}
                  onClick={() => onSelect(isSelected ? null : { p, i })}
                >
                  {n > 0 ? n : ""}
                </button>
              );
            })
          )}
        </div>
        <div className="matrix-cols">
          {COLS.map((i) => (
            <span key={i}>{i}</span>
          ))}
        </div>
        <div className="matrix-xlabel">Impact</div>
      </div>
      <div className="legend">
        <span className="badge badge-low">Low 1-5</span>
        <span className="badge badge-medium">Medium 6-12</span>
        <span className="badge badge-high">High 13-19</span>
        <span className="badge badge-critical">Critical 20-25</span>
      </div>
    </section>
  );
}