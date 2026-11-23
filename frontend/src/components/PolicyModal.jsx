import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { canCreate, formatDateTime } from "../utils";

export default function PolicyModal({ role, onClose, onNotify }) {
  const fileRef = useRef(null);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const canManage = canCreate(role);

  const load = useCallback(async () => {
    try {
      setDocs(await api.listPolicies());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function upload(e) {
    const file = e.target.files[0];
    e.target.value = "";
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const res = await api.uploadPolicy(role, file);
      onNotify(`Policy uploaded: ${res.pages} pages, ${res.passages} passages`);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function remove(doc) {
    if (!window.confirm(`Delete the policy "${doc.name}"?`)) return;
    setBusy(true);
    setError("");
    try {
      await api.deletePolicy(role, doc.id);
      onNotify("Policy deleted");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="modal-layer"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="policy-title">
        <div className="modal-head">
          <h2 id="policy-title">Bank policies</h2>
          <button type="button" className="btn btn-ghost btn-small" onClick={onClose}>Close</button>
        </div>

        <p className="muted">
          Upload the bank's policy documents as PDF. When someone uses Draft with AI, the most
          relevant policy passages are given to the AI, and its mitigation must follow them.
        </p>

        {canManage ? (
          <div className="block-actions" style={{ marginTop: 14 }}>
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf,.pdf"
              style={{ display: "none" }}
              onChange={upload}
            />
            <button
              type="button"
              className="btn btn-small"
              disabled={busy}
              onClick={() => fileRef.current?.click()}
            >
              {busy ? "Working..." : "Upload PDF"}
            </button>
            <span className="hint">PDF with text, up to 10 MB. Scanned images are not supported.</span>
          </div>
        ) : (
          <p className="hint" style={{ marginTop: 14 }}>Only a Project Manager can upload or delete policies.</p>
        )}

        {error && <div className="problems" role="alert" style={{ marginTop: 14 }}>{error}</div>}

        <div style={{ marginTop: 16 }}>
          {loading ? (
            <p className="muted">Loading policies...</p>
          ) : docs.length === 0 ? (
            <p className="muted">No policies uploaded yet.</p>
          ) : (
            <ul className="trail">
              {docs.map((d) => (
                <li key={d.id}>
                  <strong>{d.name}</strong>
                  <div className="trail-meta">
                    {d.pages} pages, {d.passages} passages. Uploaded by {d.uploaded_by},{" "}
                    {formatDateTime(d.uploaded_at)}
                  </div>
                  {canManage && (
                    <div className="block-actions">
                      <button
                        type="button"
                        className="btn btn-ghost btn-small"
                        disabled={busy}
                        onClick={() => remove(d)}
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}