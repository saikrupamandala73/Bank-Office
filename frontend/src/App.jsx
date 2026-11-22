import { useState, useEffect, useCallback } from "react";
import {
  getDashboard,
  getInvoices,
  getBills,
  createInvoice,
  createBill,
  updateInvoice,
  updateBill,
  resetDemo,
  getSettings,
  updateSettings,
  getFxRates,
} from "./api.js";
import { formatMoney } from "./currency.js";

const EMPTY_INVOICE_FORM = { client_name: "", amount: "", due_date: "", currency: "" };
const EMPTY_BILL_FORM = { title: "", amount: "", due_date: "", currency: "" };

function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyKey, setBusyKey] = useState(null);
  const [settings, setSettings] = useState(null);
  const [fx, setFx] = useState(null);

  const [invoiceForm, setInvoiceForm] = useState(EMPTY_INVOICE_FORM);
  const [invoiceFormError, setInvoiceFormError] = useState("");
  const [invoiceSubmitting, setInvoiceSubmitting] = useState(false);

  const [billForm, setBillForm] = useState(EMPTY_BILL_FORM);
  const [billFormError, setBillFormError] = useState("");
  const [billSubmitting, setBillSubmitting] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      const [d, i, b, s, f] = await Promise.all([
        getDashboard().catch(() => null),
        getInvoices(),
        getBills(),
        getSettings(),
        getFxRates().catch(() => null),
      ]);
      setDashboard(d);
      setInvoices(i);
      setBills(b);
      setSettings(s);
      setFx(f);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Runs a change, then reloads everything. Tracks the in-flight key for disabling buttons.
  const runAction = async (key, fn) => {
    setBusyKey(key);
    setError("");
    try {
      await fn();
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyKey(null);
    }
  };

  const handleCurrencyChange = (e) =>
    runAction("settings", () => updateSettings(e.target.value));

  const handleInvoiceSubmit = async (e) => {
    e.preventDefault();
    setInvoiceFormError("");
    setInvoiceSubmitting(true);
    try {
      await createInvoice({
        client_name: invoiceForm.client_name,
        amount: Number(invoiceForm.amount),
        due_date: invoiceForm.due_date,
        currency: invoiceForm.currency || formCurrency,
      });
      setInvoiceForm(EMPTY_INVOICE_FORM);
      await load();
    } catch (err) {
      setInvoiceFormError(err.message);
    } finally {
      setInvoiceSubmitting(false);
    }
  };

  const handleBillSubmit = async (e) => {
    e.preventDefault();
    setBillFormError("");
    setBillSubmitting(true);
    try {
      await createBill({
        title: billForm.title,
        amount: Number(billForm.amount),
        due_date: billForm.due_date,
        currency: billForm.currency || formCurrency,
      });
      setBillForm(EMPTY_BILL_FORM);
      await load();
    } catch (err) {
      setBillFormError(err.message);
    } finally {
      setBillSubmitting(false);
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="app">
        <p className="status-message">Loading dashboard…</p>
      </div>
    );
  }

  const upcoming = Number(dashboard?.upcoming_bills) || 0;
  const overdue = Number(dashboard?.overdue_bills) || 0;
  const net = Number(dashboard?.net_outlook) || 0;
  const actions = dashboard?.actions || [];
  const displayCode = settings?.display_currency || dashboard?.display_currency || "USD";
  const formCurrency = settings?.display_currency || displayCode;
  const supportedCurrencies = settings?.supported_currencies || [];

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Bank Office</h1>
          <p className="subtitle">What money arrives, what bills are due, and what to do today</p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={() => runAction("reset", resetDemo)}
          disabled={busyKey !== null}
        >
          Reset demo data
        </button>
      </header>

      <section className="card settings-card">
        <h2>Settings</h2>
        <label>
          Display currency{" "}
          <select
            value={settings?.display_currency || ""}
            disabled={busyKey !== null || !settings}
            onChange={handleCurrencyChange}
          >
            {supportedCurrencies.map((c) => (
              <option key={c.code} value={c.code}>
                {`${c.code} – ${c.name} (${c.symbol})`}
              </option>
            ))}
          </select>
        </label>
        {displayCode === "USD" ? (
          <p className="muted">Base currency: US Dollar</p>
        ) : fx?.rates?.[displayCode] != null ? (
          <p className="muted">
            1 USD = {Number(fx.rates[displayCode]).toFixed(4)} {displayCode}
          </p>
        ) : null}
        {fx && (
          <p className="muted">
            Last updated: {fx.last_updated ? new Date(fx.last_updated).toLocaleString() : "unknown"}
          </p>
        )}
        {fx?.stale && <p className="warning">Showing last saved rates; live update failed.</p>}
        {!fx && (
          <p className="warning">
            Exchange rates could not be loaded, so totals are not converted. Each invoice and bill keeps its original amount.
          </p>
        )}
      </section>

      {error && <div className="error-banner">{error}</div>}

      <section className="snapshot-grid">
        <div className="card">
          <p className="card-label">Expected inflows</p>
          <p className="card-value">
            {dashboard ? formatMoney(dashboard.expected_inflows, displayCode) : "—"}
          </p>
        </div>
        <div className="card">
          <p className="card-label">Upcoming &amp; overdue bills</p>
          <p className="card-value">
            {dashboard ? formatMoney(upcoming + overdue, displayCode) : "—"}
          </p>
          <p className="card-sub">
            Overdue: {dashboard ? formatMoney(overdue, displayCode) : "—"}
          </p>
        </div>
        <div className="card">
          <p className="card-label">Projected net outlook</p>
          <p className={`card-value ${dashboard && net < 0 ? "negative" : ""}`}>
            {dashboard ? formatMoney(net, displayCode) : "—"}
          </p>
        </div>
      </section>

      {!loading && !dashboard && (
        <p className="warning">
          Totals in the selected currency are unavailable because exchange rates could not be loaded.
        </p>
      )}

      {dashboard && displayCode !== "USD" && (
        <p className="muted">
          Converted at rates updated{" "}
          {dashboard?.fx_last_updated
            ? new Date(dashboard.fx_last_updated).toLocaleString()
            : "unknown"}
        </p>
      )}

      <section className="card">
        <h2>Today's priority actions</h2>
        {!dashboard ? (
          <p className="muted">Today's actions are unavailable until exchange rates load.</p>
        ) : actions.length === 0 ? (
          <p className="empty-text">Nothing here yet</p>
        ) : (
          <ul className="action-list">
            {actions.map((action, index) => {
              const key = `action-${index}`;
              const isInvoiceAction =
                action.ref_type === "invoice" &&
                (action.kind === "follow_up" || action.kind === "collect");
              const isBillAction = action.ref_type === "bill";
              return (
                <li key={key} className="action-item">
                  <div className="action-text">
                    <span className="priority-label">{action.priority}</span>
                    <span>{action.message}</span>
                  </div>
                  {isInvoiceAction && (
                    <button
                      className="btn btn-primary btn-small"
                      disabled={busyKey !== null}
                      onClick={() =>
                        runAction(key, () => updateInvoice(action.ref_id, { status: "paid" }))
                      }
                    >
                      Mark invoice paid
                    </button>
                  )}
                  {isBillAction && (
                    <button
                      className="btn btn-primary btn-small"
                      disabled={busyKey !== null}
                      onClick={() =>
                        runAction(key, () => updateBill(action.ref_id, { status: "paid" }))
                      }
                    >
                      Mark bill paid
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="panels">
        <div className="card">
          <h2>Money arriving (invoices)</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Client</th>
                  <th>Amount</th>
                  <th>Due</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {invoices.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="empty-text">Nothing here yet</td>
                  </tr>
                ) : (
                  invoices.map((inv) => (
                    <tr key={inv.id}>
                      <td>{inv.client_name}</td>
                      <td>
                        {inv.amount_display != null
                          ? formatMoney(inv.amount_display, displayCode)
                          : formatMoney(inv.amount, inv.currency)}
                        {inv.amount_display != null && inv.currency !== displayCode && (
                          <div className="muted">
                            {`Original: ${formatMoney(inv.amount, inv.currency)}`}
                          </div>
                        )}
                      </td>
                      <td>{inv.due_date}</td>
                      <td>
                        <StatusBadge status={inv.status} />
                      </td>
                      <td className="right">
                        {inv.status !== "paid" && (
                          <button
                            className="btn btn-primary btn-small"
                            disabled={busyKey !== null}
                            onClick={() =>
                              runAction(`inv-${inv.id}`, () =>
                                updateInvoice(inv.id, { status: "paid" })
                              )
                            }
                          >
                            Mark paid
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <form className="entry-form" onSubmit={handleInvoiceSubmit}>
            <input
              type="text"
              placeholder="Client name"
              required
              value={invoiceForm.client_name}
              onChange={(e) => setInvoiceForm({ ...invoiceForm, client_name: e.target.value })}
            />
            <input
              type="number"
              placeholder="Amount"
              min="0.01"
              step="0.01"
              required
              value={invoiceForm.amount}
              onChange={(e) => setInvoiceForm({ ...invoiceForm, amount: e.target.value })}
            />
            <select
              value={invoiceForm.currency || formCurrency}
              onChange={(e) => setInvoiceForm({ ...invoiceForm, currency: e.target.value })}
            >
              {supportedCurrencies.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code}
                </option>
              ))}
            </select>
            <input
              type="date"
              required
              value={invoiceForm.due_date}
              onChange={(e) => setInvoiceForm({ ...invoiceForm, due_date: e.target.value })}
            />
            <button className="btn btn-primary" type="submit" disabled={invoiceSubmitting}>
              Add invoice
            </button>
            {invoiceFormError && <p className="form-error">{invoiceFormError}</p>}
          </form>
        </div>

        <div className="card">
          <h2>Bills coming (payables)</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Vendor/Title</th>
                  <th>Amount</th>
                  <th>Due</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {bills.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="empty-text">Nothing here yet</td>
                  </tr>
                ) : (
                  bills.map((bill) => (
                    <tr key={bill.id}>
                      <td>{bill.title}</td>
                      <td>
                        {bill.amount_display != null
                          ? formatMoney(bill.amount_display, displayCode)
                          : formatMoney(bill.amount, bill.currency)}
                        {bill.amount_display != null && bill.currency !== displayCode && (
                          <div className="muted">
                            {`Original: ${formatMoney(bill.amount, bill.currency)}`}
                          </div>
                        )}
                      </td>
                      <td>{bill.due_date}</td>
                      <td>
                        <StatusBadge status={bill.status} />
                      </td>
                      <td className="right">
                        {bill.status !== "paid" && (
                          <button
                            className="btn btn-primary btn-small"
                            disabled={busyKey !== null}
                            onClick={() =>
                              runAction(`bill-${bill.id}`, () =>
                                updateBill(bill.id, { status: "paid" })
                              )
                            }
                          >
                            Mark paid
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <form className="entry-form" onSubmit={handleBillSubmit}>
            <input
              type="text"
              placeholder="Title"
              required
              value={billForm.title}
              onChange={(e) => setBillForm({ ...billForm, title: e.target.value })}
            />
            <input
              type="number"
              placeholder="Amount"
              min="0.01"
              step="0.01"
              required
              value={billForm.amount}
              onChange={(e) => setBillForm({ ...billForm, amount: e.target.value })}
            />
            <select
              value={billForm.currency || formCurrency}
              onChange={(e) => setBillForm({ ...billForm, currency: e.target.value })}
            >
              {supportedCurrencies.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code}
                </option>
              ))}
            </select>
            <input
              type="date"
              required
              value={billForm.due_date}
              onChange={(e) => setBillForm({ ...billForm, due_date: e.target.value })}
            />
            <button className="btn btn-primary" type="submit" disabled={billSubmitting}>
              Add bill
            </button>
            {billFormError && <p className="form-error">{billFormError}</p>}
          </form>
        </div>
      </section>
    </div>
  );
}
