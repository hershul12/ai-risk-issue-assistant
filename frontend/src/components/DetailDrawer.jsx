import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import PriorityBadge from "./PriorityBadge";
import {
  allowedStatuses, canEdit, canReview, formatDate, formatDateTime, statusClass,
} from "../utils";

const ACTION_LABELS = {
  created: "Created",
  updated: "Updated",
  status_change: "Status changed",
};

export default function DetailDrawer({ item, role, onClose, onChanged, onError }) {
  const closeRef = useRef(null);
  const [audit, setAudit] = useState([]);
  const [mitigation, setMitigation] = useState(item.mitigation || "");
  const [status, setStatus] = useState(() => allowedStatuses(role, item.status)[0] || "");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  // Reset the form when the record or role changes (adjusting state during render
  // instead of in an effect avoids an extra render pass).
  const resetKey = `${item.id}|${item.updated_at}|${item.status}|${item.mitigation}|${role}`;
  const [prevResetKey, setPrevResetKey] = useState(resetKey);
  if (prevResetKey !== resetKey) {
    setPrevResetKey(resetKey);
    setMitigation(item.mitigation || "");
    setNote("");
    setStatus(allowedStatuses(role, item.status)[0] || "");
  }

  const showReview = canReview(role, item);
  const statusOptions = allowedStatuses(role, item.status);
  const showStatus =
    !showReview &&
    statusOptions.length > 0 &&
    !(role === "Risk Owner" && item.status === "Closed");

  useEffect(() => {
    closeRef.current?.focus();
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;
    api
      .audit(item.id)
      .then((rows) => {
        if (!cancelled) setAudit(rows);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [item.id, item.updated_at]);

  async function run(action, message) {
    setBusy(true);
    try {
      const updated = await action();
      onChanged(updated, message);
    } catch (e) {
      onError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const saveMitigation = () =>
    run(() => api.updateItem(role, item.id, { mitigation }), "Mitigation saved");

  const saveStatus = () =>
    run(
      () => api.changeStatus(role, item.id, { status, note: note.trim() }),
      `Status changed to ${status}`
    );

  function decide(newStatus) {
    if (newStatus === "In Progress" && !note.trim()) {
      onError("Add a review note before sending the record back.");
      return;
    }
    run(
      () => api.changeStatus(role, item.id, { status: newStatus, note: note.trim() }),
      newStatus === "Closed" ? "Record approved and closed" : "Record sent back to In Progress"
    );
  }

  return (
    <>
      <div className="backdrop" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
        <header className="drawer-head">
          <div>
            <div className="drawer-tags">
              <PriorityBadge priority={item.priority} score={item.score} />
              <span className={`status ${statusClass(item.status)}`}>{item.status}</span>
              {item.overdue && <span className="overdue-tag">Overdue</span>}
            </div>
            <h2 id="drawer-title">{item.title}</h2>
          </div>
          <button ref={closeRef} type="button" className="btn btn-ghost btn-small" onClick={onClose}>
            Close
          </button>
        </header>

        <div className="drawer-body">
          <p>{item.description}</p>

          <dl className="facts">
            <div><dt>Type</dt><dd>{item.item_type}</dd></div>
            <div><dt>Category</dt><dd>{item.category}</dd></div>
            <div><dt>Probability</dt><dd>{item.probability} of 5</dd></div>
            <div><dt>Impact</dt><dd>{item.impact} of 5</dd></div>
            <div><dt>Owner</dt><dd>{item.owner}</dd></div>
            <div><dt>Due date</dt><dd>{formatDate(item.due_date)}</dd></div>
          </dl>

          <section>
            <h3>Mitigation</h3>
            {canEdit(role, item) ? (
              <>
                <textarea
                  value={mitigation}
                  onChange={(e) => setMitigation(e.target.value)}
                  aria-label="Mitigation"
                />
                <div className="block-actions">
                  <button
                    type="button"
                    className="btn btn-small"
                    disabled={busy || mitigation === (item.mitigation || "")}
                    onClick={saveMitigation}
                  >
                    Save mitigation
                  </button>
                </div>
              </>
            ) : (
              <p className="notes">{item.mitigation || "No mitigation recorded yet."}</p>
            )}
          </section>

          {item.review_notes && (
            <section>
              <h3>Review notes</h3>
              <p className="notes">{item.review_notes}</p>
            </section>
          )}

          {showReview && (
            <section className="review-box">
              <h3>Review decision</h3>
              <p className="muted">
                This record is waiting for review. Approve it to close it, or send it back with a note.
              </p>
              <div className="field" style={{ marginTop: 10 }}>
                <label htmlFor="review-note">Review note</label>
                <textarea id="review-note" value={note} onChange={(e) => setNote(e.target.value)} />
              </div>
              <div className="block-actions">
                <button type="button" className="btn" disabled={busy} onClick={() => decide("Closed")}>
                  Approve and close
                </button>
                <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => decide("In Progress")}>
                  Send back
                </button>
              </div>
            </section>
          )}

          {showStatus && (
            <section>
              <h3>Change status</h3>
              <div className="field">
                <label htmlFor="new-status">New status</label>
                <select id="new-status" value={status} onChange={(e) => setStatus(e.target.value)}>
                  {statusOptions.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div className="field" style={{ marginTop: 10 }}>
                <label htmlFor="status-note">Note (optional)</label>
                <textarea id="status-note" value={note} onChange={(e) => setNote(e.target.value)} />
              </div>
              <div className="block-actions">
                <button type="button" className="btn btn-small" disabled={busy || !status} onClick={saveStatus}>
                  Update status
                </button>
              </div>
            </section>
          )}

          <section>
            <h3>History</h3>
            <ul className="trail">
              {audit.map((a, idx) => (
                <li key={idx}>
                  <strong>{ACTION_LABELS[a.action] || a.action}</strong> by {a.changed_by}
                  <div className="trail-meta">{formatDateTime(a.timestamp)}</div>
                  {a.details && <div>{a.details}</div>}
                </li>
              ))}
            </ul>
          </section>
        </div>
      </aside>
    </>
  );
}