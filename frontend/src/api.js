export const API_BASE = "http://localhost:8000";

async function request(path, options = {}) {
  const init = { method: options.method || "GET", headers: {} };
  if (options.body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }

  const res = await fetch(API_BASE + path, init);

  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`.trim();
    try {
      const data = await res.json();
      if (data && data.detail) {
        message = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // response body was not JSON; keep the status-based message
    }
    throw new Error(message);
  }

  if (res.status === 204) {
    return null;
  }
  return res.json();
}

export function getDashboard() {
  return request("/dashboard/today");
}

export function getInvoices() {
  return request("/invoices");
}

export function getBills() {
  return request("/bills");
}

export function createInvoice(data) {
  return request("/invoices", { method: "POST", body: data });
}

export function createBill(data) {
  return request("/bills", { method: "POST", body: data });
}

export function updateInvoice(id, patch) {
  return request(`/invoices/${id}`, { method: "PATCH", body: patch });
}

export function updateBill(id, patch) {
  return request(`/bills/${id}`, { method: "PATCH", body: patch });
}

export function resetDemo() {
  return request("/demo/reset", { method: "POST" });
}

export function getSettings() {
  return request("/settings");
}

export function updateSettings(display_currency) {
  return request("/settings", { method: "PATCH", body: { display_currency } });
}

export function getFxRates() {
  return request("/fx/rates");
}
