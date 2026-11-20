import PriorityBadge from "./PriorityBadge";
import { formatDate, statusClass } from "../utils";

export default function RegisterTable({ items, selectedId, onOpen, onReset }) {
  if (items.length === 0) {
    return (
      <div className="table-wrap">
        <div className="empty">
          <h3>No records match these filters</h3>
          <p>Clear a filter or choose another cell in the risk matrix.</p>
          <button type="button" className="btn btn-ghost" onClick={onReset}>
            Clear filters
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">Priority</th>
            <th scope="col">Record</th>
            <th scope="col">Type</th>
            <th scope="col">Owner</th>
            <th scope="col">Due</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr
              key={it.id}
              className={`row p-${it.priority.toLowerCase()}${selectedId === it.id ? " is-active" : ""}`}
              onClick={() => onOpen(it.id)}
            >
              <td><PriorityBadge priority={it.priority} score={it.score} /></td>
              <td>
                <button type="button" className="row-title">{it.title}</button>
                <div className="row-sub">{it.category}</div>
              </td>
              <td>{it.item_type}</td>
              <td>{it.owner}</td>
              <td>
                {formatDate(it.due_date)}
                {it.overdue && <div className="overdue-tag">Overdue</div>}
              </td>
              <td><span className={`status ${statusClass(it.status)}`}>{it.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}