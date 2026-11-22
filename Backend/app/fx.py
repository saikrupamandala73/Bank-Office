import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FxRate, Setting

logger = logging.getLogger(__name__)

CURRENCIES = {
    "INR": {"name": "Indian Rupee", "symbol": "₹", "decimals": 2},
    "USD": {"name": "US Dollar", "symbol": "$", "decimals": 2},
    "EUR": {"name": "Euro", "symbol": "€", "decimals": 2},
    "GBP": {"name": "British Pound", "symbol": "£", "decimals": 2},
    "AED": {"name": "UAE Dirham", "symbol": "د.إ", "decimals": 2},
    "JPY": {"name": "Japanese Yen", "symbol": "¥", "decimals": 0},
}
SUPPORTED_CODES = list(CURRENCIES.keys())

RATES_URL = "https://open.er-api.com/v6/latest/USD"
CACHE_MAX_AGE = timedelta(hours=12)
DISPLAY_CURRENCY_KEY = "display_currency"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def fetch_remote_rates():
    """Return (rates, source_updated_at) for SUPPORTED_CODES from the remote API."""
    try:
        with urllib.request.urlopen(RATES_URL, timeout=10) as response:
            body = response.read()
        data = json.loads(body)
        if data.get("result") != "success":
            raise RuntimeError("exchange-rate API returned no success result")
        remote = data["rates"]
        rates = {}
        for code in SUPPORTED_CODES:
            if code == "USD":
                rates[code] = 1.0
            else:
                rates[code] = float(remote[code])
        source_updated_at = datetime.fromtimestamp(
            data["time_last_update_unix"], tz=timezone.utc
        ).replace(tzinfo=None)
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError):
            logger.error(
                "FX provider returned HTTP %s %s for %s",
                exc.code,
                exc.reason,
                RATES_URL,
            )
        logger.exception("FX rate fetch failed: %s: %s", type(exc).__name__, exc)
        raise RuntimeError(f"failed to fetch exchange rates: {exc}") from exc
    return rates, source_updated_at


def get_rates(db: Session) -> dict:
    """Return cached rates when fresh; otherwise refresh them, falling back to stale cache."""
    now = _utcnow()
    cached = db.scalars(select(FxRate)).all()
    cached_codes = {row.code for row in cached}

    if cached and set(SUPPORTED_CODES).issubset(cached_codes):
        fetched_at = min(row.fetched_at for row in cached)
        if fetched_at >= now - CACHE_MAX_AGE:
            return {
                "rates": {row.code: row.rate_per_usd for row in cached},
                "source_updated_at": cached[0].source_updated_at,
                "fetched_at": fetched_at,
                "stale": False,
            }

    try:
        rates, source_updated_at = fetch_remote_rates()
    except RuntimeError:
        if cached and set(SUPPORTED_CODES).issubset(cached_codes):
            return {
                "rates": {row.code: row.rate_per_usd for row in cached},
                "source_updated_at": cached[0].source_updated_at,
                "fetched_at": min(row.fetched_at for row in cached),
                "stale": True,
            }
        raise HTTPException(
            status_code=503,
            detail="Exchange rates unavailable; try again later",
        )

    db.execute(FxRate.__table__.delete())
    for code in SUPPORTED_CODES:
        db.add(
            FxRate(
                code=code,
                rate_per_usd=rates[code],
                source_updated_at=source_updated_at,
                fetched_at=now,
            )
        )
    db.commit()

    return {
        "rates": dict(rates),
        "source_updated_at": source_updated_at,
        "fetched_at": now,
        "stale": False,
    }


def convert(amount: float, from_code: str, to_code: str, rates: dict) -> float:
    if from_code == to_code:
        return amount
    return amount / rates[from_code] * rates[to_code]


def format_money(amount: float, code: str) -> str:
    info = CURRENCIES[code]
    decimals = info["decimals"]
    prefix = info["symbol"] + (" " if code == "AED" else "")
    return prefix + f"{amount:,.{decimals}f}"


def get_display_currency(db: Session) -> str:
    setting = db.get(Setting, DISPLAY_CURRENCY_KEY)
    if setting is None or setting.value not in CURRENCIES:
        return "USD"
    return setting.value


def set_display_currency(db: Session, code: str) -> None:
    setting = db.get(Setting, DISPLAY_CURRENCY_KEY)
    if setting is None:
        db.add(Setting(key=DISPLAY_CURRENCY_KEY, value=code))
    else:
        setting.value = code
    db.commit()
