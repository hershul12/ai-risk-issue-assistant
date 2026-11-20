import { useEffect, useState } from "react";
import { api } from "../api";
import PriorityBadge from "./PriorityBadge";
import { CATEGORIES, priorityFor } from "../utils";

const PROBABILITY = ["Very unlikely", "Unlikely", "Possible", "Likely", "Almost certain"];
const IMPACT = ["Minor", "Limited", "Moderate", "Major", "Severe"];

function inDays(n) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  const p = (x) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function validate(f) {
  const problems = [];
  if (f.title.trim().length < 3) problems.push("Enter a title of at least 3 characters.");
  if (f.description.trim().length < 5) problems.push("Enter a description of at least 5 characters.");
  if (!f.owner.trim()) problems.push("Enter the owner's name.");
  if (!f.due_date) problems.push("Choose a due date.");
  return problems;
}

export default function NewRecordModal({ role, initial, onClose, onCreated }) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    item_type: "Risk",
    category: "Schedule",
    probability: 3,
    impact: 3,
    owner: "",
    due_date: inDays(14),
    mitigation: "",
    ...initial,
  });
  const [problems, setProblems] = useState([]);
  const [busy, setBusy] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [suggestion, setSuggestion] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [draftError, setDraftError] = useState("");

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const score = Number(form.probability) * Number(form.impact);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function draft() {
    setDrafting(true);
    setSuggestion(null);
    setDraftError("");
    try {
      const res = await api.suggest({
        title: form.title,
        description: form.description,
        category: form.category,
      });
      const r = res.result || {};
      setSimilar(res.similar || []);
      if (!r.standardised_description && !r.suggested_mitigation) {
        setDraftError("The AI reply could not be read. Try drafting again.");
      } else {
        setSuggestion(r);
      }
    } catch (e) {
      setDraftError(e.message);
    } finally {
      setDrafting(false);
    }
  }

  const actions = suggestion && Array.isArray(suggestion.follow_up_actions)
    ? suggestion.follow_up_actions.map((a) => (typeof a === "string" ? a : Object.values(a).join(" ")))
    : [];

  function useMitigation() {
    let text = suggestion.suggested_mitigation || "";
    if (actions.length) text += `\n\nFollow-up actions:\n${actions.map((a) => `- ${a}`).join("\n")}`;
    set("mitigation", text.trim());
  }

  async function submit(e) {
    e.preventDefault();
    const found = validate(form);
    if (found.length) {
      setProblems(found);
      return;
    }
    setProblems([]);
    setBusy(true);
    try {
      const created = await api.createItem(role, {
        title: form.title.trim(),
        description: form.description.trim(),
        item_type: form.item_type,
        category: form.category,
        probability: Number(form.probability),
        impact: Number(form.impact),
        owner: form.owner.trim(),
        due_date: form.due_date,
        mitigation: form.mitigation.trim(),
      });
      onCreated(created);
    } catch (err) {
      setProblems([err.message]);
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
      <form className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" onSubmit={submit} noValidate>
        <div className="modal-head">
          <h2 id="modal-title">New record</h2>
          <button type="button" className="btn btn-ghost btn-small" onClick={onClose}>Cancel</button>
        </div>

        <div className="form-grid">
          <div className="field span-2">
            <label htmlFor="n-title">Title</label>
            <input id="n-title" value={form.title} onChange={(e) => set("title", e.target.value)} />
          </div>

          <div className="field span-2">
            <label htmlFor="n-desc">Description</label>
            <textarea id="n-desc" value={form.description} onChange={(e) => set("description", e.target.value)} />
            <div className="block-actions">
              <button
                type="button"
                className="btn btn-ghost btn-small"
                disabled={drafting || form.description.trim().length < 5}
                onClick={draft}
              >
                {drafting ? "Drafting..." : "Draft with AI"}
              </button>
              {form.description.trim().length < 5 && (
                <span className="hint">Write a short description first.</span>
              )}
            </div>
          </div>

          {draftError && <div className="problems span-2" role="alert">{draftError}</div>}

          {suggestion && (
            <div className="suggestion span-2" aria-live="polite">
              <p className="suggestion-title">AI suggestion. Review before you use it.</p>
              {suggestion.standardised_description && (
                <div>
                  <p className="label">Clearer description</p>
                  <p>{suggestion.standardised_description}</p>
                  <div className="block-actions">
                    <button type="button" className="btn btn-ghost btn-small"
                      onClick={() => set("description", suggestion.standardised_description)}>
                      Use this description
                    </button>
                  </div>
                </div>
              )}
              {CATEGORIES.includes(suggestion.suggested_category) && (
                <div>
                  <p className="label">Suggested category: {suggestion.suggested_category}</p>
                  <div className="block-actions">
                    <button type="button" className="btn btn-ghost btn-small"
                      onClick={() => set("category", suggestion.suggested_category)}>
                      Use this category
                    </button>
                  </div>
                </div>
              )}
              {similar.length > 0 && (
                <div>
                  <p className="label">Similar past risks used as context</p>
                  <ul>{similar.map((c) => <li key={c.id}>{c.description}</li>)}</ul>
                </div>
              )}
              {suggestion.suggested_mitigation && (
                <div>
                  <p className="label">Mitigation and follow-up actions</p>
                  <p>{suggestion.suggested_mitigation}</p>
                  {actions.length > 0 && (
                    <ul>{actions.map((a, i) => <li key={i}>{a}</li>)}</ul>
                  )}
                  <div className="block-actions">
                    <button type="button" className="btn btn-ghost btn-small" onClick={useMitigation}>
                      Use mitigation and actions
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="field">
            <label htmlFor="n-type">Type</label>
            <select id="n-type" value={form.item_type} onChange={(e) => set("item_type", e.target.value)}>
              <option>Risk</option>
              <option>Issue</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="n-cat">Category</label>
            <select id="n-cat" value={form.category} onChange={(e) => set("category", e.target.value)}>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="n-prob">Probability</label>
            <select id="n-prob" value={form.probability} onChange={(e) => set("probability", e.target.value)}>
              {PROBABILITY.map((t, i) => <option key={t} value={i + 1}>{i + 1} - {t}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="n-impact">Impact</label>
            <select id="n-impact" value={form.impact} onChange={(e) => set("impact", e.target.value)}>
              {IMPACT.map((t, i) => <option key={t} value={i + 1}>{i + 1} - {t}</option>)}
            </select>
          </div>
          <div className="span-2 score-line">
            <span className="label">Score</span>
            <PriorityBadge priority={priorityFor(score)} score={score} />
            <span className="hint">Calculated as probability x impact.</span>
          </div>
          <div className="field">
            <label htmlFor="n-owner">Owner</label>
            <input id="n-owner" value={form.owner} onChange={(e) => set("owner", e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="n-due">Due date</label>
            <input id="n-due" type="date" value={form.due_date} onChange={(e) => set("due_date", e.target.value)} />
          </div>
          <div className="field span-2">
            <label htmlFor="n-mit">Mitigation (optional)</label>
            <textarea id="n-mit" value={form.mitigation} onChange={(e) => set("mitigation", e.target.value)} />
          </div>
        </div>

        {problems.length > 0 && (
          <div className="problems" role="alert" style={{ marginTop: 14 }}>
            <ul>{problems.map((p, i) => <li key={i}>{p}</li>)}</ul>
          </div>
        )}

        <div className="modal-foot">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn" disabled={busy}>
            {busy ? "Saving..." : "Create record"}
          </button>
        </div>
      </form>
    </div>
  );
}