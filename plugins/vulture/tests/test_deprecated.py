"""Tests for deprecated module stubs."""
import pytest


def test_get_investor_trading_returns_none():
    """Deprecated function should return None."""
    from utils.deprecated import get_investor_trading
    result = get_investor_trading("005930")
    assert result is None


def test_get_short_selling_returns_none():
    """Deprecated function should return None."""
    from utils.deprecated import get_short_selling
    result = get_short_selling("005930")
    assert result is None
