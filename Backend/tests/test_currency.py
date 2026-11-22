import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.fx import format_money


def test_format_money_usd():
    assert format_money(1234.5, "USD") == "$1,234.50"


def test_format_money_inr():
    assert format_money(1234.5, "INR") == "₹1,234.50"


def test_format_money_eur():
    assert format_money(1234.5, "EUR") == "€1,234.50"


def test_format_money_gbp():
    assert format_money(1234.5, "GBP") == "£1,234.50"


def test_format_money_aed():
    assert format_money(1234.5, "AED") == "د.إ 1,234.50"


def test_format_money_jpy():
    assert format_money(1234.5, "JPY") == "¥1,234"
