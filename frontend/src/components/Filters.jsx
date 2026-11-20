import { CATEGORIES, EMPTY_FILTERS, STATUSES } from "../utils";

export default function Filters({ filters, onChange, owners, shown, total }) {
  const set = (key, value) => onChange({ ...filters, [key]: value });
  const active =
    JSON.stringify(filters) !== JSON.stringify(EMPTY_FILTERS);

  return (
    <section className="panel" aria-label="Filters">
      <div className="filters">
        <div className="field">
          <label htmlFor="f-search">Search</label>
          <input
            id="f-search"
            type="search"
            placeholder="Title, description or owner"
            value={filters.search}
            onChange={(e) => set("search", e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="f-status">Status</label>
          <select id="f-status" value={filters.status} onChange={(e) => set("status", e.target.value)}>
            <option value="">All statuses</option>
            <option value="active">Not closed</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="f-priority">Priority</label>
          <select id="f-priority" value={filters.priority} onChange={(e) => set("priority", e.target.value)}>
            <option value="">All priorities</option>
            <option value="high+">High and critical</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="f-category">Category</label>
          <select id="f-category" value={filters.category} onChange={(e) => set("category", e.target.value)}>
            <option value="">All categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="f-owner">Owner</label>
          <select id="f-owner" value={filters.owner} onChange={(e) => set("owner", e.target.value)}>
            <option value="">All owners</option>
            {owners.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="filters-foot">
        <label className="check">
          <input
            type="checkbox"
            checked={filters.overdueOnly}
            onChange={(e) => set("overdueOnly", e.target.checked)}
          />
          Overdue only
        </label>
        {filters.cell && (
          <span className="badge badge-low">
            Matrix cell: probability {filters.cell.p}, impact {filters.cell.i}
          </span>
        )}
        <span className="muted">
          Showing {shown} of {total} records
        </span>
        {active && (
          <button type="button" className="btn btn-ghost btn-small" onClick={() => onChange(EMPTY_FILTERS)}>
            Clear filters
          </button>
        )}
      </div>
    </section>
  );
}