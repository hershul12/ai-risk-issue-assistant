const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function formatError(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    return data.detail
      .map((e) => `${(e.loc || []).slice(1).join(" ")}: ${e.msg}`)
      .join("; ");
  }
  return `The request failed (status ${status}).`;
}

async function request(path, { method = "GET", role, body } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (role) headers["X-Role"] = role;

  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error(
      `Cannot reach the server at ${BASE}. Check that the backend is running.`
    );
  }

  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) throw new Error(formatError(data, res.status));
  return data;
}

export const api = {
  listItems: () => request("/items"),
  summary: () => request("/dashboard/summary"),
  audit: (id) => request(`/items/${id}/audit`),
  createItem: (role, body) => request("/items", { method: "POST", role, body }),
  updateItem: (role, id, body) =>
    request(`/items/${id}`, { method: "PUT", role, body }),
  changeStatus: (role, id, body) =>
    request(`/items/${id}/status`, { method: "PATCH", role, body }),
  suggest: (body) => request("/suggest", { method: "POST", body }),
    extract: (text) => request("/extract", { method: "POST", body: { text } }),
};