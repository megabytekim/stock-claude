"""Tests for indicators module - technical analysis functions."""
import pytest
import pandas as pd
import numpy as np


class TestSMA:
    """Tests for SMA (Simple Moving Average) calculation."""

    def test_sma_returns_series(self, sample_ohlcv_df):
        """SMA should return a pandas Series."""
        from utils.indicators import sma

        result = sma(sample_ohlcv_df['종가'], period=20)

        assert isinstance(result, pd.Series)

    def test_sma_length_matches_input(self, sample_ohlcv_df):
        """SMA output length should match input length."""
        from utils.indicators import sma

        result = sma(sample_ohlcv_df['종가'], period=20)

        assert len(result) == len(sample_ohlcv_df)

    def test_sma_first_values_are_nan(self, sample_ohlcv_df):
        """First (period-1) values should be NaN due to rolling window."""
        from utils.indicators import sma

        period = 20
        result = sma(sample_ohlcv_df['종가'], period=period)

        # First (period-1) values should be NaN
        assert result.iloc[:period-1].isna().all()
        # Value at index (period-1) should be valid
        assert not pd.isna(result.iloc[period-1])

    def test_sma_calculation_correct(self):
        """SMA should calculate correctly for known values."""
        from utils.indicators import sma

        # Simple test case: [1, 2, 3, 4, 5] with period=3
        close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = sma(close, period=3)

        # Expected: NaN, NaN, 2.0, 3.0, 4.0
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert result.iloc[2] == pytest.approx(2.0)
        assert result.iloc[3] == pytest.approx(3.0)
        assert result.iloc[4] == pytest.approx(4.0)


class TestEMA:
    """Tests for EMA (Exponential Moving Average) calculation."""

    def test_ema_returns_series(self, sample_ohlcv_df):
        """EMA should return a pandas Series."""
        from utils.indicators import ema

        result = ema(sample_ohlcv_df['종가'], period=20)

        assert isinstance(result, pd.Series)

    def test_ema_length_matches_input(self, sample_ohlcv_df):
        """EMA output length should match input length."""
        from utils.indicators import ema

        result = ema(sample_ohlcv_df['종가'], period=20)

        assert len(result) == len(sample_ohlcv_df)

    def test_ema_no_nan_values(self, sample_ohlcv_df):
        """EMA should not have NaN values (adjust=False starts from first value)."""
        from utils.indicators import ema

        result = ema(sample_ohlcv_df['종가'], period=20)

        assert not result.isna().any()

    def test_ema_first_value_equals_input(self, sample_ohlcv_df):
        """First EMA value should equal first input value (adjust=False)."""
        from utils.indicators import ema

        result = ema(sample_ohlcv_df['종가'], period=20)

        assert result.iloc[0] == sample_ohlcv_df['종가'].iloc[0]


class TestRSI:
    """Tests for RSI (Relative Strength Index) calculation."""

    def test_rsi_returns_series(self, sample_ohlcv_df):
        """RSI should return a pandas Series."""
        from utils.indicators import rsi

        result = rsi(sample_ohlcv_df['종가'], period=14)

        assert isinstance(result, pd.Series)

    def test_rsi_values_in_range(self, sample_ohlcv_df):
        """RSI values should be between 0 and 100."""
        from utils.indicators import rsi

        result = rsi(sample_ohlcv_df['종가'], period=14)
        valid_values = result.dropna()

        assert (valid_values >= 0).all()
        assert (valid_values <= 100).all()

    def test_rsi_length_matches_input(self, sample_ohlcv_df):
        """RSI output length should match input length."""
        from utils.indicators import rsi

        result = rsi(sample_ohlcv_df['종가'], period=14)

        assert len(result) == len(sample_ohlcv_df)

    def test_rsi_default_period(self, sample_ohlcv_df):
        """RSI should use default period of 14."""
        from utils.indicators import rsi

        result_default = rsi(sample_ohlcv_df['종가'])
        result_explicit = rsi(sample_ohlcv_df['종가'], period=14)

        pd.testing.assert_series_equal(result_default, result_explicit)

    def test_rsi_uptrend_high_value(self):
        """RSI should be high (>50) for consistent uptrend."""
        from utils.indicators import rsi

        # Create consistent uptrend data
        close = pd.Series([100 + i * 10 for i in range(30)])
        result = rsi(close, period=14)

        # After warmup, RSI should be high for uptrend
        assert result.iloc[-1] > 50

    def test_rsi_downtrend_low_value(self):
        """RSI should be low (<50) for consistent downtrend."""
        from utils.indicators import rsi

        # Create consistent downtrend data
        close = pd.Series([300 - i * 10 for i in range(30)])
        result = rsi(close, period=14)

        # After warmup, RSI should be low for downtrend
        assert result.iloc[-1] < 50


class TestMACD:
    """Tests for MACD (Moving Average Convergence Divergence) calculation."""

    def test_macd_returns_tuple_of_three(self, sample_ohlcv_df):
        """MACD should return a tuple of 3 Series."""
        from utils.indicators import macd

        result = macd(sample_ohlcv_df['종가'])

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_macd_all_elements_are_series(self, sample_ohlcv_df):
        """All MACD return elements should be pandas Series."""
        from utils.indicators import macd

        macd_line, signal_line, histogram = macd(sample_ohlcv_df['종가'])

        assert isinstance(macd_line, pd.Series)
        assert isinstance(signal_line, pd.Series)
        assert isinstance(histogram, pd.Series)

    def test_macd_lengths_match_input(self, sample_ohlcv_df):
        """All MACD output lengths should match input length."""
        from utils.indicators import macd

        macd_line, signal_line, histogram = macd(sample_ohlcv_df['종가'])

        assert len(macd_line) == len(sample_ohlcv_df)
        assert len(signal_line) == len(sample_ohlcv_df)
        assert len(histogram) == len(sample_ohlcv_df)

    def test_macd_histogram_is_difference(self, sample_ohlcv_df):
        """Histogram should equal MACD line minus Signal line."""
        from utils.indicators import macd

        macd_line, signal_line, histogram = macd(sample_ohlcv_df['종가'])

        expected_histogram = macd_line - signal_line
        pd.testing.assert_series_equal(histogram, expected_histogram)

    def test_macd_default_parameters(self, sample_ohlcv_df):
        """MACD should use default parameters (12, 26, 9)."""
        from utils.indicators import macd

        result_default = macd(sample_ohlcv_df['종가'])
        result_explicit = macd(sample_ohlcv_df['종가'], fast=12, slow=26, signal=9)

        pd.testing.assert_series_equal(result_default[0], result_explicit[0])
        pd.testing.assert_series_equal(result_default[1], result_explicit[1])
        pd.testing.assert_series_equal(result_default[2], result_explicit[2])


class TestBollinger:
    """Tests for Bollinger Bands calculation."""

    def test_bollinger_returns_tuple_of_three(self, sample_ohlcv_df):
        """Bollinger should return a tuple of 3 Series."""
        from utils.indicators import bollinger

        result = bollinger(sample_ohlcv_df['종가'])

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_bollinger_all_elements_are_series(self, sample_ohlcv_df):
        """All Bollinger return elements should be pandas Series."""
        from utils.indicators import bollinger

        upper, middle, lower = bollinger(sample_ohlcv_df['종가'])

        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)

    def test_bollinger_band_order(self, sample_ohlcv_df):
        """Upper band should be > middle > lower band."""
        from utils.indicators import bollinger

        upper, middle, lower = bollinger(sample_ohlcv_df['종가'])

        # Check only non-NaN values
        valid_idx = upper.notna() & middle.notna() & lower.notna()

        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_bollinger_middle_is_sma(self, sample_ohlcv_df):
        """Middle band should equal SMA of the same period."""
        from utils.indicators import bollinger, sma

        upper, middle, lower = bollinger(sample_ohlcv_df['종가'], period=20)
        expected_sma = sma(sample_ohlcv_df['종가'], period=20)

        pd.testing.assert_series_equal(middle, expected_sma)

    def test_bollinger_lengths_match_input(self, sample_ohlcv_df):
        """All Bollinger output lengths should match input length."""
        from utils.indicators import bollinger

        upper, middle, lower = bollinger(sample_ohlcv_df['종가'])

        assert len(upper) == len(sample_ohlcv_df)
        assert len(middle) == len(sample_ohlcv_df)
        assert len(lower) == len(sample_ohlcv_df)

    def test_bollinger_default_parameters(self, sample_ohlcv_df):
        """Bollinger should use default parameters (period=20, std=2.0)."""
        from utils.indicators import bollinger

        result_default = bollinger(sample_ohlcv_df['종가'])
        result_explicit = bollinger(sample_ohlcv_df['종가'], period=20, std=2.0)

        pd.testing.assert_series_equal(result_default[0], result_explicit[0])
        pd.testing.assert_series_equal(result_default[1], result_explicit[1])
        pd.testing.assert_series_equal(result_default[2], result_explicit[2])


class TestStochastic:
    """Tests for Stochastic Oscillator calculation."""

    def test_stochastic_returns_tuple_of_two(self, sample_ohlcv_df):
        """Stochastic should return a tuple of 2 Series (%K, %D)."""
        from utils.indicators import stochastic

        result = stochastic(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_stochastic_all_elements_are_series(self, sample_ohlcv_df):
        """Both Stochastic return elements should be pandas Series."""
        from utils.indicators import stochastic

        k, d = stochastic(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )

        assert isinstance(k, pd.Series)
        assert isinstance(d, pd.Series)

    def test_stochastic_values_in_range(self, sample_ohlcv_df):
        """Stochastic %K and %D values should be between 0 and 100."""
        from utils.indicators import stochastic

        k, d = stochastic(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )

        valid_k = k.dropna()
        valid_d = d.dropna()

        assert (valid_k >= 0).all()
        assert (valid_k <= 100).all()
        assert (valid_d >= 0).all()
        assert (valid_d <= 100).all()

    def test_stochastic_lengths_match_input(self, sample_ohlcv_df):
        """Stochastic output lengths should match input length."""
        from utils.indicators import stochastic

        k, d = stochastic(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )

        assert len(k) == len(sample_ohlcv_df)
        assert len(d) == len(sample_ohlcv_df)

    def test_stochastic_default_parameters(self, sample_ohlcv_df):
        """Stochastic should use default parameters (k_period=14, d_period=3)."""
        from utils.indicators import stochastic

        result_default = stochastic(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )
        result_explicit = stochastic(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가'],
            k_period=14,
            d_period=3
        )

        pd.testing.assert_series_equal(result_default[0], result_explicit[0])
        pd.testing.assert_series_equal(result_default[1], result_explicit[1])

    def test_stochastic_d_is_smoothed_k(self, sample_ohlcv_df):
        """Stochastic %D should be a moving average of %K."""
        from utils.indicators import stochastic

        k, d = stochastic(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가'],
            k_period=14,
            d_period=3
        )

        # %D should be rolling mean of %K with d_period window
        expected_d = k.rolling(window=3).mean()
        pd.testing.assert_series_equal(d, expected_d)


class TestSupportResistance:
    """Tests for Support/Resistance (Pivot Point) calculation."""

    def test_support_resistance_returns_dict(self, sample_ohlcv_df):
        """Support/Resistance should return a dictionary."""
        from utils.indicators import support_resistance

        result = support_resistance(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )

        assert isinstance(result, dict)

    def test_support_resistance_has_required_keys(self, sample_ohlcv_df):
        """Support/Resistance should have all required keys."""
        from utils.indicators import support_resistance

        result = support_resistance(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )

        required_keys = ['pivot', 'r1', 'r2', 's1', 's2']
        for key in required_keys:
            assert key in result

    def test_support_resistance_values_are_floats(self, sample_ohlcv_df):
        """Support/Resistance values should be floats."""
        from utils.indicators import support_resistance

        result = support_resistance(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )

        for key, value in result.items():
            assert isinstance(value, float)

    def test_support_resistance_level_order(self, sample_ohlcv_df):
        """Resistance levels should be > pivot > support levels."""
        from utils.indicators import support_resistance

        result = support_resistance(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )

        # R2 > R1 > pivot > S1 > S2
        assert result['r2'] > result['r1']
        assert result['r1'] > result['pivot']
        assert result['pivot'] > result['s1']
        assert result['s1'] > result['s2']

    def test_support_resistance_default_lookback(self, sample_ohlcv_df):
        """Support/Resistance should use default lookback of 20."""
        from utils.indicators import support_resistance

        result_default = support_resistance(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가']
        )
        result_explicit = support_resistance(
            sample_ohlcv_df['고가'],
            sample_ohlcv_df['저가'],
            sample_ohlcv_df['종가'],
            lookback=20
        )

        assert result_default == result_explicit
