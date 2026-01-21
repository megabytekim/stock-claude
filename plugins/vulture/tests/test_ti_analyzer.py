"""Tests for ti_analyzer module - Technical Intelligence integration."""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from io import StringIO
import sys


class TestGetRsiSignal:
    """Tests for RSI signal interpretation."""

    def test_overbought_signal(self):
        """RSI > 70 should return overbought signal (과매수)."""
        from utils.ti_analyzer import get_rsi_signal

        result = get_rsi_signal(75.0)

        assert result == "과매수"

    def test_overbought_boundary(self):
        """RSI exactly 70.1 should return overbought signal."""
        from utils.ti_analyzer import get_rsi_signal

        result = get_rsi_signal(70.1)

        assert result == "과매수"

    def test_oversold_signal(self):
        """RSI < 30 should return oversold signal (과매도)."""
        from utils.ti_analyzer import get_rsi_signal

        result = get_rsi_signal(25.0)

        assert result == "과매도"

    def test_oversold_boundary(self):
        """RSI exactly 29.9 should return oversold signal."""
        from utils.ti_analyzer import get_rsi_signal

        result = get_rsi_signal(29.9)

        assert result == "과매도"

    def test_neutral_signal_middle(self):
        """RSI in 30-70 range should return neutral signal (중립)."""
        from utils.ti_analyzer import get_rsi_signal

        result = get_rsi_signal(50.0)

        assert result == "중립"

    def test_neutral_at_lower_boundary(self):
        """RSI exactly 30 should return neutral signal."""
        from utils.ti_analyzer import get_rsi_signal

        result = get_rsi_signal(30.0)

        assert result == "중립"

    def test_neutral_at_upper_boundary(self):
        """RSI exactly 70 should return neutral signal."""
        from utils.ti_analyzer import get_rsi_signal

        result = get_rsi_signal(70.0)

        assert result == "중립"

    def test_extreme_overbought(self):
        """RSI at extreme high (95) should return overbought."""
        from utils.ti_analyzer import get_rsi_signal

        result = get_rsi_signal(95.0)

        assert result == "과매수"

    def test_extreme_oversold(self):
        """RSI at extreme low (5) should return oversold."""
        from utils.ti_analyzer import get_rsi_signal

        result = get_rsi_signal(5.0)

        assert result == "과매도"


class TestGetMaAlignment:
    """Tests for moving average alignment detection."""

    def test_bullish_alignment(self):
        """current > MA5 > MA20 > MA60 should be bullish (완전 정배열)."""
        from utils.ti_analyzer import get_ma_alignment

        result = get_ma_alignment(current=56000, ma5=55000, ma20=52000, ma60=50000)

        assert result == "완전 정배열"

    def test_bearish_alignment(self):
        """current < MA5 < MA20 < MA60 should be bearish (완전 역배열)."""
        from utils.ti_analyzer import get_ma_alignment

        result = get_ma_alignment(current=48000, ma5=49000, ma20=51000, ma60=53000)

        assert result == "완전 역배열"

    def test_mixed_alignment_current_below_ma5(self):
        """Mixed condition should return 혼조."""
        from utils.ti_analyzer import get_ma_alignment

        # current < ma5 but ma5 > ma20 > ma60
        result = get_ma_alignment(current=54000, ma5=55000, ma20=52000, ma60=50000)

        assert result == "혼조"

    def test_mixed_alignment_ma20_above_ma5(self):
        """MA20 > MA5 should return 혼조."""
        from utils.ti_analyzer import get_ma_alignment

        result = get_ma_alignment(current=56000, ma5=51000, ma20=53000, ma60=50000)

        assert result == "혼조"

    def test_mixed_alignment_ma60_above_ma20(self):
        """MA60 > MA20 should return 혼조."""
        from utils.ti_analyzer import get_ma_alignment

        result = get_ma_alignment(current=56000, ma5=55000, ma20=50000, ma60=52000)

        assert result == "혼조"

    def test_equal_values_not_bullish(self):
        """Equal values should not satisfy strict inequality for bullish."""
        from utils.ti_analyzer import get_ma_alignment

        result = get_ma_alignment(current=50000, ma5=50000, ma20=50000, ma60=50000)

        assert result == "혼조"


class TestGetTiFullAnalysis:
    """Tests for get_ti_full_analysis integration function."""

    def test_returns_dict(self, sample_ticker_kr, sample_ohlcv_df):
        """Should return a comprehensive analysis dict."""
        from utils.ti_analyzer import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = {
                'name': '삼성전자',
                'price': 55000,
                'change': 500,
                'change_pct': 0.92,
                'market_cap': '328조'
            }
            mock_name.return_value = '삼성전자'

            result = get_ti_full_analysis(sample_ticker_kr)

        assert isinstance(result, dict)

    def test_contains_meta_section(self, sample_ticker_kr, sample_ohlcv_df):
        """Result should contain meta section with ticker and timestamp."""
        from utils.ti_analyzer import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = {'name': '삼성전자', 'price': 55000}
            mock_name.return_value = '삼성전자'

            result = get_ti_full_analysis(sample_ticker_kr)

        assert 'meta' in result
        assert result['meta']['ticker'] == sample_ticker_kr
        assert result['meta']['name'] == '삼성전자'
        assert 'timestamp' in result['meta']

    def test_contains_required_sections(self, sample_ticker_kr, sample_ohlcv_df):
        """Result should contain all required sections."""
        from utils.ti_analyzer import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = {'name': '삼성전자', 'price': 55000}
            mock_name.return_value = '삼성전자'

            result = get_ti_full_analysis(sample_ticker_kr)

        required_keys = ['meta', 'price_info', 'week52', 'indicators', 'support_resistance', 'signals']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    def test_price_info_populated_from_naver(self, sample_ticker_kr, sample_ohlcv_df):
        """price_info should be populated from Naver data."""
        from utils.ti_analyzer import get_ti_full_analysis

        naver_data = {
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

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = naver_data
            mock_name.return_value = '삼성전자'

            result = get_ti_full_analysis(sample_ticker_kr)

        assert result['price_info'] is not None
        assert result['price_info']['price'] == 55000
        assert result['price_info']['market_cap'] == '328조'

    def test_handles_naver_failure(self, sample_ticker_kr, sample_ohlcv_df):
        """Should handle Naver data fetch failure gracefully."""
        from utils.ti_analyzer import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = None  # Naver fetch failed
            mock_name.return_value = '삼성전자'

            result = get_ti_full_analysis(sample_ticker_kr)

        assert isinstance(result, dict)
        assert result['price_info'] is None

    def test_handles_ohlcv_failure(self, sample_ticker_kr):
        """Should handle OHLCV data fetch failure gracefully."""
        from utils.ti_analyzer import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = None  # OHLCV fetch failed
            mock_naver.return_value = {'name': '삼성전자', 'price': 55000}
            mock_name.return_value = '삼성전자'

            result = get_ti_full_analysis(sample_ticker_kr)

        assert isinstance(result, dict)
        assert result['indicators'] is None
        assert result['signals'] is None

    def test_indicators_contain_rsi(self, sample_ticker_kr, sample_ohlcv_df):
        """Indicators should contain RSI data."""
        from utils.ti_analyzer import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = {'name': '삼성전자', 'price': 55000}
            mock_name.return_value = '삼성전자'

            result = get_ti_full_analysis(sample_ticker_kr)

        assert result['indicators'] is not None
        assert 'rsi' in result['indicators']
        assert 'value' in result['indicators']['rsi']
        assert 'signal' in result['indicators']['rsi']

    def test_indicators_contain_macd(self, sample_ticker_kr, sample_ohlcv_df):
        """Indicators should contain MACD data."""
        from utils.ti_analyzer import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = {'name': '삼성전자', 'price': 55000}
            mock_name.return_value = '삼성전자'

            result = get_ti_full_analysis(sample_ticker_kr)

        assert 'macd' in result['indicators']
        assert 'trend' in result['indicators']['macd']

    def test_signals_populated(self, sample_ticker_kr, sample_ohlcv_df):
        """Signals section should contain aggregated signals."""
        from utils.ti_analyzer import get_ti_full_analysis

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = {'name': '삼성전자', 'price': 55000}
            mock_name.return_value = '삼성전자'

            result = get_ti_full_analysis(sample_ticker_kr)

        assert result['signals'] is not None
        assert 'rsi_signal' in result['signals']
        assert 'macd_signal' in result['signals']
        assert 'stochastic_signal' in result['signals']
        assert 'ma_alignment' in result['signals']


class TestPrintTiReport:
    """Tests for print_ti_report function."""

    def test_runs_without_error(self, sample_ticker_kr, sample_ohlcv_df):
        """print_ti_report should run without raising exceptions."""
        from utils.ti_analyzer import print_ti_report

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = {
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
            mock_name.return_value = '삼성전자'

            # Should not raise any exception
            print_ti_report(sample_ticker_kr)

    def test_outputs_report_sections(self, sample_ticker_kr, sample_ohlcv_df, capsys):
        """print_ti_report should output expected sections."""
        from utils.ti_analyzer import print_ti_report

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = sample_ohlcv_df
            mock_naver.return_value = {
                'name': '삼성전자',
                'price': 55000,
                'change': 500,
                'change_pct': 0.92,
                'market_cap': '328조'
            }
            mock_name.return_value = '삼성전자'

            print_ti_report(sample_ticker_kr)

        captured = capsys.readouterr()
        assert 'TI Report' in captured.out
        assert '삼성전자' in captured.out

    def test_handles_missing_data_gracefully(self, sample_ticker_kr, capsys):
        """print_ti_report should handle missing data without crashing."""
        from utils.ti_analyzer import print_ti_report

        with patch('utils.ti_analyzer.get_ohlcv') as mock_ohlcv, \
             patch('utils.ti_analyzer.get_naver_stock_info') as mock_naver, \
             patch('utils.ti_analyzer.get_ticker_name') as mock_name:
            mock_ohlcv.return_value = None
            mock_naver.return_value = None
            mock_name.return_value = None

            # Should not raise any exception even with missing data
            print_ti_report(sample_ticker_kr)

        captured = capsys.readouterr()
        assert 'TI Report' in captured.out
        assert '조회 실패' in captured.out
