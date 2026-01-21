"""기술지표 함수

순수 함수로 구현된 기술지표 계산 유틸리티
입력: pandas Series
출력: pandas Series 또는 tuple
"""
from typing import Tuple

import pandas as pd
import numpy as np


def sma(close: pd.Series, period: int) -> pd.Series:
    """
    단순이동평균 (Simple Moving Average)

    Args:
        close: 종가 Series
        period: 이동평균 기간

    Returns:
        SMA Series

    Formula:
        SMA = sum(close[n-period:n]) / period
    """
    return close.rolling(window=period).mean()


def ema(close: pd.Series, period: int) -> pd.Series:
    """
    지수이동평균 (Exponential Moving Average)

    Args:
        close: 종가 Series
        period: 이동평균 기간

    Returns:
        EMA Series

    Formula:
        EMA = close * k + EMA_prev * (1-k)
        k = 2 / (period + 1)
    """
    return close.ewm(span=period, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    RSI (Relative Strength Index)

    Args:
        close: 종가 Series
        period: RSI 기간 (기본 14)

    Returns:
        RSI Series (0-100)

    해석:
        > 70: 과매수 (매도 고려)
        < 30: 과매도 (매수 고려)
        50 기준 상승/하락 추세 판단
    """
    delta = close.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    # Wilder's Smoothing (α = 1/period)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))

    return rsi_values


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD (Moving Average Convergence Divergence)

    Args:
        close: 종가 Series
        fast: 단기 EMA 기간 (기본 12)
        slow: 장기 EMA 기간 (기본 26)
        signal: 시그널 EMA 기간 (기본 9)

    Returns:
        (macd_line, signal_line, histogram)

    해석:
        macd > signal (골든크로스): 매수 신호
        macd < signal (데드크로스): 매도 신호
        histogram 방향: 모멘텀 강도
    """
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)

    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def bollinger(
    close: pd.Series,
    period: int = 20,
    std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    볼린저 밴드

    Args:
        close: 종가 Series
        period: SMA 기간 (기본 20)
        std: 표준편차 배수 (기본 2.0)

    Returns:
        (upper, middle, lower)

    해석:
        가격 > upper: 과매수, 하락 가능
        가격 < lower: 과매도, 반등 가능
        밴드 수축: 변동성 감소, 돌파 임박
        밴드 확장: 변동성 증가
    """
    middle = sma(close, period)
    std_dev = close.rolling(window=period).std()

    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    return upper, middle, lower


def stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    스토캐스틱 오실레이터

    Args:
        high: 고가 Series
        low: 저가 Series
        close: 종가 Series
        k_period: %K 기간 (기본 14)
        d_period: %D 기간 (기본 3)

    Returns:
        (%K, %D)

    해석:
        > 80: 과매수
        < 20: 과매도
        %K > %D 상향돌파: 매수
        %K < %D 하향돌파: 매도
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()

    return k, d


def support_resistance(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    lookback: int = 20
) -> dict:
    """
    지지/저항선 (피봇 포인트 기반)

    Args:
        high: 고가 Series
        low: 저가 Series
        close: 종가 Series
        lookback: 계산 기간 (기본 20)

    Returns:
        {
            "pivot": float,  # 피봇 포인트
            "r1": float,     # 저항선 1
            "r2": float,     # 저항선 2
            "s1": float,     # 지지선 1
            "s2": float      # 지지선 2
        }

    Formula:
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
    """
    # lookback 기간의 최근 데이터 사용
    h = high.iloc[-lookback:].max()
    l = low.iloc[-lookback:].min()
    c = close.iloc[-1]

    pivot = (h + l + c) / 3
    r1 = 2 * pivot - l
    r2 = pivot + (h - l)
    s1 = 2 * pivot - h
    s2 = pivot - (h - l)

    return {
        "pivot": float(pivot),
        "r1": float(r1),
        "r2": float(r2),
        "s1": float(s1),
        "s2": float(s2),
    }
