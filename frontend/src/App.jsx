import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import {
  EMPTY_FILTERS, ROLES, ROLE_NOTES, applyFilters, canCreate, sortItems,
} from "./utils";
import SummaryStrip from "./components/SummaryStrip";
import RiskMatrix from "./components/RiskMatrix";
import StatusBars from "./components/StatusBars";
import Filters from "./components/Filters";
import RegisterTable from "./components/RegisterTable";
import DetailDrawer from "./components/DetailDrawer";
import NewRecordModal from "./components/NewRecordModal";

export default function App() {
  const [role, setRole] = useState("Project Manager");
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [selectedId, setSelectedId] = useState(null);
  const [showNew, setShowNew] = useState(false);
  const [toast, setToast] = useState(null);

  const notify = useCallback(
    (message, kind = "ok") => setToast({ message, kind, id: Date.now() }),
    []
  );

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const [list, sum] = await Promise.all([api.listItems(), api.summary()]);
      setItems(list);
      setSummary(sum);
    } catch (e) {
      setLoadError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!toast) return undefined;
    const t = setTimeout(() => setToast(null), 4500);
    return () => clearTimeout(t);
  }, [toast]);

  const refreshSummary = useCallback(() => {
    api.summary().then(setSummary).catch(() => {});
  }, []);

  const handleUpdated = useCallback(
    (updated, message) => {
      setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
      refreshSummary();
      notify(message);
    },
    [refreshSummary, notify]
  );

  const handleCreated = useCallback(
    (created) => {
      setItems((prev) => sortItems([created, ...prev]));
      refreshSummary();
      setShowNew(false);
      notify("Record created");
    },
    [refreshSummary, notify]
  );

  const closeDrawer = useCallback(() => setSelectedId(null), []);
  const closeModal = useCallback(() => setShowNew(false), []);

  function handlePick(kind) {
    const next = { ...EMPTY_FILTERS };
    if (kind === "open") next.status = "active";
    if (kind === "overdue") next.overdueOnly = true;
    if (kind === "high") {
      next.priority = "high+";
      next.status = "active";
    }
    if (kind === "review") next.status = "Pending Review";
    setFilters(next);
  }

  const owners = useMemo(
    () => [...new Set(items.map((i) => i.owner))].sort(),
    [items]
  );
  const visible = useMemo(() => applyFilters(items, filters), [items, filters]);
  const selected = items.find((i) => i.id === selectedId) || null;

  return (
    <>
      <a className="skip-link" href="#register">Skip to the register</a>

      <header className="topbar">
        <div className="topbar-inner">
          <div>
            <h1 className="brand">RiskPilot</h1>
            <p className="brand-sub">Risk and issue register for financial services programmes</p>
          </div>
          <div className="topbar-actions">
            <div className="field">
              <label htmlFor="role">Viewing as</label>
              <select id="role" value={role} onChange={(e) => setRole(e.target.value)}>
                {ROLES.map((r) => <option key={r}>{r}</option>)}
              </select>
            </div>
            <button
              type="button"
              className="btn"
              disabled={!canCreate(role)}
              title={canCreate(role) ? "" : "Only a Project Manager can create records"}
              onClick={() => setShowNew(true)}
            >
              New record
            </button>
          </div>
        </div>
      </header>

      <main className="shell">
        <p className="role-note">{ROLE_NOTES[role]}</p>

        {loadError ? (
          <div className="panel state" role="alert">
            <h2>The register could not be loaded</h2>
            <p className="muted">{loadError}</p>
            <button type="button" className="btn" onClick={load}>Try again</button>
          </div>
        ) : loading ? (
          <div className="panel state"><p className="muted">Loading the register...</p></div>
        ) : (
          <>
            <SummaryStrip summary={summary} onPick={handlePick} />
            <div className="layout">
              <section className="main-col" id="register" aria-labelledby="register-title">
                <h2 id="register-title">Risk and issue register</h2>
                <Filters
                  filters={filters}
                  onChange={setFilters}
                  owners={owners}
                  shown={visible.length}
                  total={items.length}
                />
                <RegisterTable
                  items={visible}
                  selectedId={selectedId}
                  onOpen={setSelectedId}
                  onReset={() => setFilters(EMPTY_FILTERS)}
                />
              </section>
              <div className="side-col">
                <RiskMatrix
                  items={items}
                  selected={filters.cell}
                  onSelect={(cell) => setFilters({ ...filters, cell })}
                />
                <StatusBars summary={summary} />
              </div>
            </div>
          </>
        )}
      </main>

      {selected && (
        <DetailDrawer
          item={selected}
          role={role}
          onClose={closeDrawer}
          onChanged={handleUpdated}
          onError={(m) => notify(m, "error")}
        />
      )}
      {showNew && (
        <NewRecordModal role={role} onClose={closeModal} onCreated={handleCreated} />
      )}
      {toast && (
        <div key={toast.id} className={`toast toast-${toast.kind}`} role={toast.kind === "error" ? "alert" : "status"}>
          {toast.message}
        </div>
      )}
    </>
  );
}