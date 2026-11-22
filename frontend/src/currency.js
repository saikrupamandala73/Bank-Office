export const CURRENCY_SYMBOLS = { INR: "₹", USD: "$", EUR: "€", GBP: "£", AED: "د.إ", JPY: "¥" };
export const CURRENCY_DECIMALS = { INR: 2, USD: 2, EUR: 2, GBP: 2, AED: 2, JPY: 0 };
export function formatMoney(value, code) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  const c = code || "USD";
  const n = Number(value);
  const d = CURRENCY_DECIMALS[c] ?? 2;
  const symbol = CURRENCY_SYMBOLS[c] ?? `${c} `;
  const body = new Intl.NumberFormat("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }).format(Math.abs(n));
  const sign = n < 0 ? "-" : "";
  const space = c === "AED" ? " " : "";
  return `${sign}${symbol}${space}${body}`;
}
