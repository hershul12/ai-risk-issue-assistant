export const ROLES = ["Project Manager", "Risk Owner", "Programme Lead"];
export const CATEGORIES = [
  "Schedule", "Budget", "Scope", "Resource",
  "Technical", "Vendor", "Compliance", "Security",
];
export const STATUSES = ["Open", "In Progress", "Pending Review", "Closed"];

export const EMPTY_FILTERS = {
  search: "",
  status: "",
  priority: "",
  category: "",
  owner: "",
  overdueOnly: false,
  cell: null,
};

export const ROLE_NOTES = {
  "Project Manager":
    "You can create and edit records and change any status.",
  "Risk Owner":
    "You can edit records and move them to In Progress or Pending Review.",
  "Programme Lead":
    "You can review records, then approve and close them or send them back.",
};

export function priorityFor(score) {
  if (score >= 20) return "Critical";
  if (score >= 13) return "High";
  if (score >= 6) return "Medium";
  return "Low";
}

export const canCreate = (role) => role === "Project Manager";

export const canEdit = (role, item) =>
  (role === "Project Manager" || role === "Risk Owner") &&
  item.status !== "Closed";

export const canReview = (role, item) =>
  (role === "Programme Lead" || role === "Project Manager") &&
  item.status === "Pending Review";

export const allowedStatuses = (role) =>
  role === "Risk Owner" ? ["In Progress", "Pending Review"] : STATUSES;

export const statusClass = (s) =>
  "status-" + s.toLowerCase().replace(/\s+/g, "-");

export function sortItems(list) {
  return [...list].sort(
    (a, b) => b.score - a.score || a.due_date.localeCompare(b.due_date)
  );
}

export function formatDate(iso) {
  if (!iso) return "";
  return new Date(iso + "T00:00:00").toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatDateTime(iso) {
  if (!iso) return "";
  const hasZone = /[zZ]$|[+-]\d\d:\d\d$/.test(iso);
  return new Date(hasZone ? iso : iso + "Z").toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function applyFilters(items, f) {
  const q = f.search.trim().toLowerCase();
  return items.filter((it) => {
    if (q && !`${it.title} ${it.description} ${it.owner}`.toLowerCase().includes(q))
      return false;
    if (f.status === "active") {
      if (it.status === "Closed") return false;
    } else if (f.status && it.status !== f.status) return false;
    if (f.priority === "high+") {
      if (it.priority !== "High" && it.priority !== "Critical") return false;
    } else if (f.priority && it.priority !== f.priority) return false;
    if (f.category && it.category !== f.category) return false;
    if (f.owner && it.owner !== f.owner) return false;
    if (f.overdueOnly && !it.overdue) return false;
    if (f.cell) {
      if (it.status === "Closed") return false;
      if (it.probability !== f.cell.p || it.impact !== f.cell.i) return false;
    }
    return true;
  });
}