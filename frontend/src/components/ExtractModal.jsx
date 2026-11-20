import { useEffect, useState } from "react";
import { api } from "../api";

export default function ExtractModal({ state, onChange, onUse, onClose }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { text, items, used } = state;

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function extract() {
    setBusy(true);
    setError("");
    try {
      const res = await api.extract(text);
      const found = res.items || [];
      onChange({ text, items: found, used: [] });
      if (found.length === 0) setError("No risks or issues were found in this text.");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const tooShort = text.trim().length < 20;

  return (
    <div
      className="modal-layer"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="extract-title">
        <div className="modal-head">
          <h2 id="extract-title">Import from text</h2>
          <button type="button" className="btn btn-ghost btn-small" onClick={onClose}>Close</button>
        </div>

        <div className="field">
          <label htmlFor="x-text">Paste an email or meeting notes</label>
          <textarea
            id="x-text"
            style={{ minHeight: 160 }}
            value={text}
            onChange={(e) => onChange({ text: e.target.value, items: [], used: [] })}
            placeholder="For example: Minutes of the steering meeting..."
          />
          <div className="block-actions">
            <button type="button" className="btn btn-small" disabled={busy || tooShort} onClick={extract}>
              {busy ? "Finding risks..." : "Find risks with AI"}
            </button>
            {tooShort && <span className="hint">Paste at least a few sentences.</span>}
          </div>
        </div>

        {error && <div className="problems" role="alert" style={{ marginTop: 14 }}>{error}</div>}

        {items.length > 0 && (
          <div className="suggestion" style={{ marginTop: 16 }} aria-live="polite">
            <p className="suggestion-title">
              AI found {items.length} possible {items.length === 1 ? "record" : "records"}. Review each one before you create it.
            </p>
            {items.map((it, i) => (
              <div key={i}>
                <p className="label">
                  {it.item_type} · {it.category}: {it.title}
                </p>
                <p>{it.description}</p>
                {it.suggested_mitigation && (
                  <p className="hint">Suggested mitigation: {it.suggested_mitigation}</p>
                )}
                <div className="block-actions">
                  {used.includes(i) ? (
                    <span className="hint">Record created</span>
                  ) : (
                    <button type="button" className="btn btn-ghost btn-small" onClick={() => onUse(it, i)}>
                      Review and create
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}