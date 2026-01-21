"""Shared test fixtures for vulture plugin tests."""
import pytest
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def sample_ticker_kr():
    """Korean stock ticker for testing."""
    return "005930"  # Samsung Electronics


@pytest.fixture
def sample_ticker_us():
    """US stock ticker for testing."""
    return "AAPL"


@pytest.fixture
def sample_ohlcv_df():
    """Sample OHLCV DataFrame for testing."""
    dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
    return pd.DataFrame({
        '시가': [50000 + i * 100 for i in range(60)],
        '고가': [50500 + i * 100 for i in range(60)],
        '저가': [49500 + i * 100 for i in range(60)],
        '종가': [50200 + i * 100 for i in range(60)],
        '거래량': [1000000 + i * 10000 for i in range(60)],
    }, index=dates)


@pytest.fixture
def mock_naver_response():
    """Mock Naver Finance HTML response."""
    return '''
    <table class="type2">
        <tr><td>현재가</td><td>55,000</td></tr>
        <tr><td>전일대비</td><td>+500</td></tr>
        <tr><td>시가총액</td><td>328조 4,300억</td></tr>
    </table>
    '''
