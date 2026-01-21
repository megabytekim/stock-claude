"""Tests for data_fetcher module."""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


class TestGetOhlcv:
    """Tests for get_ohlcv function."""

    def test_returns_dataframe(self, sample_ticker_kr):
        """get_ohlcv should return a DataFrame."""
        from utils.data_fetcher import get_ohlcv

        with patch('utils.data_fetcher.stock.get_market_ohlcv_by_date') as mock:
            mock.return_value = pd.DataFrame({
                '시가': [50000], '고가': [51000], '저가': [49000],
                '종가': [50500], '거래량': [1000000]
            })
            result = get_ohlcv(sample_ticker_kr, days=5)

        assert isinstance(result, pd.DataFrame)

    def test_returns_none_on_empty_dataframe(self, sample_ticker_kr):
        """get_ohlcv should return None when DataFrame is empty."""
        from utils.data_fetcher import get_ohlcv

        with patch('utils.data_fetcher.stock.get_market_ohlcv_by_date') as mock:
            mock.return_value = pd.DataFrame()
            result = get_ohlcv(sample_ticker_kr, days=5)

        assert result is None

    def test_returns_none_on_error(self, sample_ticker_kr):
        """get_ohlcv should return None on error."""
        from utils.data_fetcher import get_ohlcv

        with patch('utils.data_fetcher.stock.get_market_ohlcv_by_date') as mock:
            mock.side_effect = Exception("Network error")
            result = get_ohlcv(sample_ticker_kr, days=5)

        assert result is None

    def test_respects_days_parameter(self, sample_ticker_kr):
        """get_ohlcv should return at most 'days' rows."""
        from utils.data_fetcher import get_ohlcv

        with patch('utils.data_fetcher.stock.get_market_ohlcv_by_date') as mock:
            # Return more rows than requested
            mock.return_value = pd.DataFrame({
                '시가': [50000 + i for i in range(100)],
                '고가': [51000 + i for i in range(100)],
                '저가': [49000 + i for i in range(100)],
                '종가': [50500 + i for i in range(100)],
                '거래량': [1000000 + i for i in range(100)],
            })
            result = get_ohlcv(sample_ticker_kr, days=30)

        assert len(result) == 30


class TestGetTickerName:
    """Tests for get_ticker_name function."""

    def test_returns_string(self, sample_ticker_kr):
        """get_ticker_name should return company name as string."""
        from utils.data_fetcher import get_ticker_name

        with patch('utils.data_fetcher.stock.get_market_ticker_name') as mock:
            mock.return_value = "삼성전자"
            result = get_ticker_name(sample_ticker_kr)

        assert isinstance(result, str)
        assert result == "삼성전자"

    def test_returns_none_on_empty(self, sample_ticker_kr):
        """get_ticker_name should return None when name is empty."""
        from utils.data_fetcher import get_ticker_name

        with patch('utils.data_fetcher.stock.get_market_ticker_name') as mock:
            mock.return_value = ""
            result = get_ticker_name(sample_ticker_kr)

        assert result is None

    def test_returns_none_on_error(self, sample_ticker_kr):
        """get_ticker_name should return None on error."""
        from utils.data_fetcher import get_ticker_name

        with patch('utils.data_fetcher.stock.get_market_ticker_name') as mock:
            mock.side_effect = Exception("Not found")
            result = get_ticker_name(sample_ticker_kr)

        assert result is None


class TestGetFundamental:
    """Tests for get_fundamental function."""

    def test_returns_dict_with_metrics(self, sample_ticker_kr):
        """get_fundamental should return dict with PER, PBR, etc."""
        from utils.data_fetcher import get_fundamental

        with patch('utils.data_fetcher.stock.get_market_fundamental') as mock:
            mock.return_value = pd.DataFrame({
                'BPS': [50000],
                'PER': [25.5],
                'PBR': [1.12],
                'EPS': [2000],
                'DIV': [2.1],
                'DPS': [1000],
            })
            result = get_fundamental(sample_ticker_kr)

        assert isinstance(result, dict)
        assert 'PER' in result
        assert 'PBR' in result
        assert 'BPS' in result
        assert 'EPS' in result
        assert 'DIV' in result
        assert 'DPS' in result

    def test_returns_none_on_error(self, sample_ticker_kr):
        """get_fundamental should return None when all sources fail."""
        from utils.data_fetcher import get_fundamental

        with patch('utils.data_fetcher.stock.get_market_fundamental') as mock_pykrx:
            mock_pykrx.side_effect = Exception("pykrx error")
            # Patch the web_scraper module import to fail
            with patch.dict('sys.modules', {'utils.web_scraper': None}):
                result = get_fundamental(sample_ticker_kr)

        assert result is None

    def test_returns_none_on_empty_dataframe(self, sample_ticker_kr):
        """get_fundamental should try fallback when pykrx returns empty."""
        from utils.data_fetcher import get_fundamental

        with patch('utils.data_fetcher.stock.get_market_fundamental') as mock_pykrx:
            mock_pykrx.return_value = pd.DataFrame()
            # Patch the web_scraper module import to fail
            with patch.dict('sys.modules', {'utils.web_scraper': None}):
                result = get_fundamental(sample_ticker_kr)

        assert result is None


class TestGetTickerList:
    """Tests for get_ticker_list function."""

    def test_returns_list(self):
        """get_ticker_list should return list of tickers."""
        from utils.data_fetcher import get_ticker_list

        with patch('utils.data_fetcher.stock.get_market_ticker_list') as mock:
            mock.return_value = ['005930', '000660', '035420']
            result = get_ticker_list()

        assert isinstance(result, list)
        assert len(result) == 3
        assert '005930' in result

    def test_returns_none_on_all_failures(self):
        """get_ticker_list should return None when all sources fail."""
        from utils.data_fetcher import get_ticker_list

        with patch('utils.data_fetcher.stock.get_market_ticker_list') as mock_pykrx:
            mock_pykrx.side_effect = Exception("pykrx error")
            # Mock the web_scraper import to fail
            with patch.dict('sys.modules', {'utils.web_scraper': None}):
                result = get_ticker_list()

        assert result is None


class TestGetMarketCap:
    """Tests for get_market_cap function."""

    def test_returns_dict_with_market_cap(self, sample_ticker_kr):
        """get_market_cap should return dict with market cap info."""
        from utils.data_fetcher import get_market_cap

        with patch('utils.data_fetcher.stock.get_market_cap') as mock:
            mock.return_value = pd.DataFrame({
                '시가총액': [300000000000000],
                '거래량': [10000000],
                '거래대금': [500000000000],
                '상장주식수': [5969782550],
            })
            result = get_market_cap(sample_ticker_kr)

        assert isinstance(result, dict)
        assert '시가총액' in result
        assert '거래량' in result

    def test_returns_none_on_error(self, sample_ticker_kr):
        """get_market_cap should return None when all sources fail."""
        from utils.data_fetcher import get_market_cap

        with patch('utils.data_fetcher.stock.get_market_cap') as mock_pykrx:
            mock_pykrx.side_effect = Exception("pykrx error")
            with patch.dict('sys.modules', {'utils.web_scraper': None}):
                result = get_market_cap(sample_ticker_kr)

        assert result is None
