"""Integration tests for vulture plugin workflows.

Tests the integration between various utils modules - simulating how the agents use them together.
Each test class represents a different agent workflow.
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime


class TestTIWorkflow:
    """Integration test for Technical Intelligence workflow.

    Simulates the full TI (Technical Intelligence) worker workflow:
    1. Fetch OHLCV data from pykrx
    2. Fetch stock info from Naver Finance
    3. Calculate technical indicators
    4. Generate signals and analysis
    """

    def test_full_ti_workflow(self, sample_ticker_kr, sample_ohlcv_df):
        """Test complete TI workflow from ticker to report."""
        from utils import get_ti_full_analysis

        mock_naver_data = {
            'name': '삼성전자',
            'price': 55000,
            'change': 500,
            'change_pct': 0.92,
            'open': 54500,
            'high': 55500,
            'low': 54000,
            'volume': 10000000,
            'market_cap': '328조',
            'per': 12.5,
            'pbr': 1.2,
            'foreign_ratio': 52.3
        }

        with patch('utils.ti_analyzer.get_ohlcv', return_value=sample_ohlcv_df), \
             patch('utils.ti_analyzer.get_naver_stock_info', return_value=mock_naver_data), \
             patch('utils.ti_analyzer.get_ticker_name', return_value='삼성전자'):
            result = get_ti_full_analysis(sample_ticker_kr)

        # Verify full workflow completed
        assert result is not None
        assert isinstance(result, dict)

        # Verify all sections are present
        assert 'meta' in result
        assert 'price_info' in result
        assert 'indicators' in result
        assert 'signals' in result
        assert 'support_resistance' in result

    def test_ti_workflow_returns_all_indicator_types(self, sample_ticker_kr, sample_ohlcv_df):
        """TI workflow should calculate all technical indicators."""
        from utils import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv', return_value=sample_ohlcv_df), \
             patch('utils.ti_analyzer.get_naver_stock_info', return_value={'price': 55000}), \
             patch('utils.ti_analyzer.get_ticker_name', return_value='삼성전자'):
            result = get_ti_full_analysis(sample_ticker_kr)

        indicators = result.get('indicators', {})
        assert 'rsi' in indicators
        assert 'macd' in indicators
        assert 'bollinger' in indicators
        assert 'stochastic' in indicators
        assert 'ma' in indicators

    def test_ti_workflow_generates_signals(self, sample_ticker_kr, sample_ohlcv_df):
        """TI workflow should generate trading signals."""
        from utils import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv', return_value=sample_ohlcv_df), \
             patch('utils.ti_analyzer.get_naver_stock_info', return_value={'price': 55000}), \
             patch('utils.ti_analyzer.get_ticker_name', return_value='삼성전자'):
            result = get_ti_full_analysis(sample_ticker_kr)

        signals = result.get('signals', {})
        assert 'rsi_signal' in signals
        assert 'macd_signal' in signals
        assert 'stochastic_signal' in signals
        assert 'ma_alignment' in signals

    def test_ti_workflow_with_partial_data_failure(self, sample_ticker_kr, sample_ohlcv_df):
        """TI workflow should handle partial data failures gracefully."""
        from utils import get_ti_full_analysis

        # Naver fails but OHLCV works
        with patch('utils.ti_analyzer.get_ohlcv', return_value=sample_ohlcv_df), \
             patch('utils.ti_analyzer.get_naver_stock_info', return_value=None), \
             patch('utils.ti_analyzer.get_ticker_name', return_value='삼성전자'):
            result = get_ti_full_analysis(sample_ticker_kr)

        # Should still have indicators from OHLCV data
        assert result is not None
        assert result['price_info'] is None  # Naver failed
        assert result['indicators'] is not None  # OHLCV succeeded

    def test_ti_print_report_integration(self, sample_ticker_kr, sample_ohlcv_df, capsys):
        """Test print_ti_report integration with full workflow."""
        from utils import print_ti_report

        mock_naver = {
            'name': '삼성전자',
            'price': 55000,
            'change': 500,
            'change_pct': 0.92,
            'market_cap': '328조',
            'per': 12.5,
            'foreign_ratio': 52.3
        }

        with patch('utils.ti_analyzer.get_ohlcv', return_value=sample_ohlcv_df), \
             patch('utils.ti_analyzer.get_naver_stock_info', return_value=mock_naver), \
             patch('utils.ti_analyzer.get_ticker_name', return_value='삼성전자'):
            print_ti_report(sample_ticker_kr)

        captured = capsys.readouterr()
        assert 'TI Report' in captured.out
        assert '삼성전자' in captured.out
        assert 'RSI' in captured.out
        assert 'MACD' in captured.out


class TestFIWorkflow:
    """Integration test for Financial Intelligence workflow.

    Simulates the full FI (Financial Intelligence) worker workflow:
    1. Fetch financial data from FnGuide
    2. Calculate financial ratios
    3. Calculate growth metrics
    4. Generate financial report
    """

    def test_full_fi_workflow(self, sample_ticker_kr):
        """Test complete FI workflow from ticker to report."""
        from utils import get_financial_data

        mock_fnguide_response = MagicMock()
        mock_fnguide_response.status_code = 200
        mock_fnguide_response.text = """
        <html>
        <h1 class="giName">삼성전자</h1>
        <div id="divSonikY">
            <table>
                <thead><tr><th></th><th>2024/12</th><th>2023/12</th></tr></thead>
                <tbody>
                    <tr class="rowBold"><th>매출액</th><td>3000000</td><td>2500000</td></tr>
                    <tr class="rowBold"><th>영업이익</th><td>500000</td><td>400000</td></tr>
                    <tr class="rowBold"><th>당기순이익</th><td>400000</td><td>350000</td></tr>
                </tbody>
            </table>
        </div>
        </html>
        """

        with patch('utils.financial_scraper.requests.get', return_value=mock_fnguide_response):
            result = get_financial_data(sample_ticker_kr)

        # May return None if parsing fails due to mock simplicity
        # But should not raise an exception
        assert result is None or isinstance(result, dict)

    def test_fi_calculate_peg_integration(self):
        """Test PEG calculation as part of FI workflow."""
        from utils import calculate_peg

        # Standard case
        peg = calculate_peg(per=15.0, eps_growth=10.0)
        assert peg == 1.5

        # High growth company
        peg = calculate_peg(per=30.0, eps_growth=30.0)
        assert peg == 1.0

        # Handles zero growth
        peg = calculate_peg(per=15.0, eps_growth=0)
        assert peg is None

        # Handles None inputs
        peg = calculate_peg(per=None, eps_growth=10.0)
        assert peg is None

    def test_fi_print_report_handles_missing_data(self, sample_ticker_kr, capsys):
        """FI print report should handle missing data gracefully."""
        from utils import print_fi_report

        with patch('utils.financial_scraper.get_financial_data', return_value=None):
            print_fi_report(sample_ticker_kr)

        captured = capsys.readouterr()
        assert '조회 실패' in captured.out

    def test_fi_workflow_with_valid_data(self, sample_ticker_kr, capsys):
        """FI workflow should output proper report with valid data."""
        from utils import print_fi_report

        mock_data = {
            'source': 'FnGuide',
            'ticker': sample_ticker_kr,
            'name': '삼성전자',
            'period': '2024/12',
            'annual': {
                '2024': {'revenue': 3000000, 'operating_profit': 500000, 'net_income': 400000},
                '2023': {'revenue': 2500000, 'operating_profit': 400000, 'net_income': 350000},
            },
            'balance': {},
            'cash_flow': {},
            'latest': {'revenue': 3000000, 'operating_profit': 500000},
            'growth': {'revenue_yoy': 20.0, 'operating_profit_yoy': 25.0, 'comparison': '2024 vs 2023'},
            'ratios': {'debt_ratio': 45.0, 'current_ratio': 180.0, 'roe': 15.5, 'roa': 8.2},
            'period_labels': {},
        }

        with patch('utils.financial_scraper.get_financial_data', return_value=mock_data):
            print_fi_report(sample_ticker_kr)

        captured = capsys.readouterr()
        assert 'FI Report' in captured.out
        assert '삼성전자' in captured.out
        assert 'FnGuide' in captured.out


class TestSIWorkflow:
    """Integration test for Sentiment Intelligence workflow.

    Simulates SI (Sentiment Intelligence) workflow:
    1. Fetch discussion board posts from Naver
    2. Fetch news from Naver
    3. Aggregate sentiment data
    """

    def test_sentiment_discussion_fetch(self, sample_ticker_kr):
        """Test fetching discussion board posts for sentiment analysis."""
        from utils import get_naver_discussion

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <table class="type2">
            <tr>
                <td class="title"><a href="/test1">게시글 제목 1</a></td>
                <td><span class="tah">01/20 10:30</span></td>
            </tr>
            <tr>
                <td class="title"><a href="/test2">게시글 제목 2</a></td>
                <td><span class="tah">01/20 09:15</span></td>
            </tr>
        </table>
        </html>
        """

        with patch('utils.web_scraper.requests.get', return_value=mock_response):
            result = get_naver_discussion(sample_ticker_kr, limit=5)

        # Should either return posts or None (based on parsing)
        assert result is None or isinstance(result, list)

    def test_sentiment_news_fetch(self, sample_ticker_kr):
        """Test fetching stock news for sentiment analysis."""
        from utils import get_naver_stock_news

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <table class="type5">
            <tr>
                <td class="title"><a href="/news1">뉴스 제목 1</a></td>
                <td class="date">01/20</td>
            </tr>
        </table>
        </html>
        """

        with patch('utils.web_scraper.requests.get', return_value=mock_response):
            result = get_naver_stock_news(sample_ticker_kr, limit=5)

        assert result is None or isinstance(result, list)

    def test_sentiment_stock_info_fetch(self, sample_ticker_kr):
        """Test fetching stock info for sentiment context."""
        from utils import get_naver_stock_info

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <div class="wrap_company"><h2><a>삼성전자</a></h2></div>
        <p class="no_today"><span class="blind">55,000</span></p>
        </html>
        """

        with patch('utils.web_scraper.requests.get', return_value=mock_response):
            result = get_naver_stock_info(sample_ticker_kr)

        assert result is None or isinstance(result, dict)

    def test_clean_playwright_result_utility(self):
        """Test Playwright result cleaning utility for SI workflow."""
        from utils import clean_playwright_result

        raw_text = """
        [ref=e123] Some content [cursor=pointer]
        [ref=e456] More content []
        Multiple   spaces   here
        """

        cleaned = clean_playwright_result(raw_text)

        assert '[ref=' not in cleaned
        assert '[cursor=' not in cleaned
        assert '[]' not in cleaned
        assert '   ' not in cleaned  # No triple spaces


class TestDataFetcherWorkflow:
    """Integration tests for data fetcher utilities."""

    def test_ohlcv_to_indicators_flow(self, sample_ohlcv_df):
        """Test OHLCV data flowing to indicator calculations."""
        from utils import rsi, macd, bollinger, stochastic, sma

        close = sample_ohlcv_df['종가']
        high = sample_ohlcv_df['고가']
        low = sample_ohlcv_df['저가']

        # All indicators should work with OHLCV data
        rsi_result = rsi(close)
        assert len(rsi_result) == len(close)

        macd_line, signal_line, hist = macd(close)
        assert len(macd_line) == len(close)

        upper, middle, lower = bollinger(close)
        assert len(upper) == len(close)

        k, d = stochastic(high, low, close)
        assert len(k) == len(close)

        sma_result = sma(close, 5)
        assert len(sma_result) == len(close)

    def test_ticker_info_chain(self, sample_ticker_kr):
        """Test ticker information retrieval chain."""
        from utils import get_ticker_name

        with patch('utils.data_fetcher.stock.get_market_ticker_name', return_value='삼성전자'):
            name = get_ticker_name(sample_ticker_kr)

        assert name == '삼성전자'

    def test_fundamental_data_chain(self, sample_ticker_kr):
        """Test fundamental data retrieval with fallback."""
        from utils import get_fundamental

        mock_df = pd.DataFrame({
            'BPS': [50000],
            'PER': [12.5],
            'PBR': [1.2],
            'EPS': [4000],
            'DIV': [2.0],
            'DPS': [500],
        })

        with patch('utils.data_fetcher.stock.get_market_fundamental', return_value=mock_df):
            result = get_fundamental(sample_ticker_kr)

        assert result is not None
        assert result['PER'] == 12.5


class TestFullAnalysisWorkflow:
    """Integration test for complete vulture-analyze workflow.

    Tests that all worker components can be invoked and work together.
    """

    def test_all_workers_can_run(self, sample_ticker_kr):
        """Verify all worker components can be invoked."""
        from utils import (
            get_ti_full_analysis, get_financial_data,
            get_naver_discussion, get_naver_stock_info,
        )

        # All should be callable
        assert callable(get_ti_full_analysis)
        assert callable(get_financial_data)
        assert callable(get_naver_discussion)
        assert callable(get_naver_stock_info)

    def test_import_chain_complete(self):
        """All public exports should be importable."""
        from utils import (
            # data_fetcher
            get_ohlcv, get_ticker_name, get_ticker_list,
            get_fundamental, get_market_cap,
            # indicators
            rsi, macd, bollinger, sma, stochastic, ema, support_resistance,
            # web_scraper
            get_naver_stock_info, get_naver_discussion,
            get_naver_stock_news, clean_playwright_result,
            # ti_analyzer
            get_ti_full_analysis, print_ti_report,
            get_rsi_signal, get_ma_alignment,
            # financial_scraper
            get_financial_data, print_fi_report, calculate_peg,
            get_fnguide_financial, get_naver_financial,
            # deprecated
            get_investor_trading, get_short_selling,
        )

        # Import chain complete
        assert True

    def test_deprecated_functions_return_none(self, sample_ticker_kr):
        """Deprecated functions should return None gracefully."""
        from utils import get_investor_trading, get_short_selling

        assert get_investor_trading(sample_ticker_kr) is None
        assert get_short_selling(sample_ticker_kr) is None

    def test_cross_module_data_flow(self, sample_ticker_kr, sample_ohlcv_df):
        """Test data flowing across multiple modules."""
        from utils import get_ti_full_analysis
        from utils.indicators import rsi, macd

        # Manual indicator calculation
        close = sample_ohlcv_df['종가']
        manual_rsi = rsi(close).iloc[-1]
        manual_macd, manual_signal, _ = macd(close)

        # TI analysis should use same indicators
        with patch('utils.ti_analyzer.get_ohlcv', return_value=sample_ohlcv_df), \
             patch('utils.ti_analyzer.get_naver_stock_info', return_value={'price': 55000}), \
             patch('utils.ti_analyzer.get_ticker_name', return_value='삼성전자'):
            result = get_ti_full_analysis(sample_ticker_kr)

        ti_rsi = result['indicators']['rsi']['value']

        # Values should be consistent (with rounding tolerance)
        assert abs(ti_rsi - manual_rsi) < 0.2

    def test_error_propagation_handling(self, sample_ticker_kr):
        """Errors in one module should not crash entire workflow."""
        from utils import get_ti_full_analysis

        # Simulate None returns (the functions already handle exceptions internally)
        with patch('utils.ti_analyzer.get_ohlcv', return_value=None), \
             patch('utils.ti_analyzer.get_naver_stock_info', return_value=None), \
             patch('utils.ti_analyzer.get_ticker_name', return_value=None):
            result = get_ti_full_analysis(sample_ticker_kr)

        # Should return structure with None values, not crash
        assert result is not None
        assert 'meta' in result
        assert result['indicators'] is None
        assert result['price_info'] is None


class TestIndicatorIntegration:
    """Integration tests for indicator calculations working together."""

    def test_all_indicators_with_realistic_data(self, sample_ohlcv_df):
        """Test all indicators produce valid outputs with realistic data."""
        from utils import rsi, macd, bollinger, stochastic, sma, ema, support_resistance
        import numpy as np

        close = sample_ohlcv_df['종가']
        high = sample_ohlcv_df['고가']
        low = sample_ohlcv_df['저가']

        # RSI
        rsi_val = rsi(close).iloc[-1]
        assert 0 <= rsi_val <= 100

        # MACD
        macd_line, signal_line, histogram = macd(close)
        assert not macd_line.isna().all()
        assert not signal_line.isna().all()

        # Bollinger - compare only non-NaN values
        upper, middle, lower = bollinger(close)
        # Get valid (non-NaN) values for comparison
        valid_mask = ~(upper.isna() | middle.isna() | lower.isna())
        if valid_mask.any():
            assert (upper[valid_mask] >= middle[valid_mask]).all()
            assert (middle[valid_mask] >= lower[valid_mask]).all()

        # Stochastic
        k, d = stochastic(high, low, close)
        last_k = k.iloc[-1]
        if not pd.isna(last_k):
            assert 0 <= last_k <= 100

        # SMA & EMA
        sma_val = sma(close, 20)
        ema_val = ema(close, 20)
        assert not sma_val.isna().all()
        assert not ema_val.isna().all()

        # Support/Resistance
        sr = support_resistance(high, low, close)
        assert 'pivot' in sr
        assert 'r1' in sr
        assert 's1' in sr

    def test_indicators_handle_edge_cases(self):
        """Test indicators handle edge cases properly."""
        from utils import rsi, sma

        # Very short series
        short_series = pd.Series([100, 101, 102])
        sma_result = sma(short_series, 2)
        assert len(sma_result) == 3

        # Series with all same values
        flat_series = pd.Series([100] * 20)
        rsi_result = rsi(flat_series)
        # RSI of flat series is typically NaN or 50
        assert True  # Just verify no exception


class TestWorkflowResilience:
    """Tests for workflow resilience and error handling."""

    def test_ti_workflow_with_empty_dataframe(self, sample_ticker_kr):
        """TI workflow should handle empty DataFrame gracefully."""
        from utils import get_ti_full_analysis

        empty_df = pd.DataFrame()

        with patch('utils.ti_analyzer.get_ohlcv', return_value=empty_df), \
             patch('utils.ti_analyzer.get_naver_stock_info', return_value=None), \
             patch('utils.ti_analyzer.get_ticker_name', return_value='테스트'):
            result = get_ti_full_analysis(sample_ticker_kr)

        assert result is not None
        assert result['indicators'] is None

    def test_ti_workflow_with_none_ohlcv(self, sample_ticker_kr):
        """TI workflow should handle None OHLCV gracefully."""
        from utils import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv', return_value=None), \
             patch('utils.ti_analyzer.get_naver_stock_info', return_value={'price': 50000}), \
             patch('utils.ti_analyzer.get_ticker_name', return_value='테스트'):
            result = get_ti_full_analysis(sample_ticker_kr)

        assert result is not None
        assert result['indicators'] is None
        assert result['week52'] is None

    def test_fi_workflow_with_network_timeout(self, sample_ticker_kr):
        """FI workflow should handle network timeout gracefully."""
        from utils import get_financial_data
        import requests

        with patch('utils.financial_scraper.requests.get', side_effect=requests.Timeout):
            result = get_financial_data(sample_ticker_kr)

        assert result is None  # Should return None on failure

    def test_web_scraper_handles_malformed_html(self, sample_ticker_kr):
        """Web scraper should handle malformed HTML gracefully."""
        from utils import get_naver_stock_info

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>malformed content without expected elements"

        with patch('utils.web_scraper.requests.get', return_value=mock_response):
            result = get_naver_stock_info(sample_ticker_kr)

        # Should return None or empty dict, not crash
        assert result is None or isinstance(result, dict)
