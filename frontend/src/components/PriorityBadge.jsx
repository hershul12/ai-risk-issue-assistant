export default function PriorityBadge({ priority, score }) {
  return (
    <span className={`badge badge-${priority.toLowerCase()}`}>
      {priority}
      {score !== undefined && <span className="badge-score">{score}</span>}
    </span>
  );
}