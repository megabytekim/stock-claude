"""pykrx 래퍼 함수

다른 에이전트가 사용할 데이터 조회 인프라 함수
실패 시 None 반환
"""
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from pykrx import stock


def get_ohlcv(
    ticker: str,
    days: int = 60,
    end_date: Optional[str] = None,
    frequency: str = "d",
    adjusted: bool = True
) -> Optional[pd.DataFrame]:
    """
    OHLCV 데이터 조회

    Args:
        ticker: 종목코드 (예: "005930")
        days: 조회 일수 (기본 60)
        end_date: 종료일 YYYYMMDD (기본 오늘)
        frequency: "d"(일), "m"(월), "y"(연)
        adjusted: True=수정주가, False=원주가

    Returns:
        DataFrame or None (실패 시)

    Columns:
        시가, 고가, 저가, 종가, 거래량, 거래대금, 등락률
    """
    try:
        if end_date is None:
            end_dt = datetime.now()
        else:
            end_dt = datetime.strptime(end_date, "%Y%m%d")

        start_dt = end_dt - timedelta(days=days * 2)  # 영업일 고려하여 여유있게
        start = start_dt.strftime("%Y%m%d")
        end = end_dt.strftime("%Y%m%d")

        df = stock.get_market_ohlcv_by_date(start, end, ticker)

        if df.empty:
            return None

        # days 개수만큼 자르기
        return df.tail(days)

    except Exception:
        return None


def get_ticker_name(ticker: str) -> Optional[str]:
    """
    종목명 조회

    Args:
        ticker: 종목코드 (예: "005930")

    Returns:
        종목명 or None (실패 시)

    Example:
        >>> get_ticker_name("005930")
        "삼성전자"
    """
    try:
        name = stock.get_market_ticker_name(ticker)
        if not name:
            return None
        return name
    except Exception:
        return None


def get_ticker_list(
    date: Optional[str] = None,
    market: str = "KOSPI"
) -> Optional[list]:
    """
    전체 종목 리스트 조회 (pykrx 우선, 실패 시 Naver fallback)

    Args:
        date: 조회일 YYYYMMDD (기본 오늘)
        market: "KOSPI", "KOSDAQ", "KONEX", "ALL"

    Returns:
        ['005930', '000660', ...] or None (실패 시)
    """
    # 1차: pykrx
    try:
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        tickers = stock.get_market_ticker_list(date, market=market)
        if tickers:
            return list(tickers)
    except Exception:
        pass

    # 2차: Naver fallback
    try:
        from utils.web_scraper import get_naver_stock_list
        stocks = get_naver_stock_list(market)
        if stocks:
            return [s["code"] for s in stocks]
    except Exception:
        pass
    return None


def get_fundamental(
    ticker: str,
    date: Optional[str] = None
) -> Optional[dict]:
    """
    펀더멘털 지표 조회 (pykrx 우선, 실패 시 네이버 금융 fallback)

    Args:
        ticker: 종목코드
        date: 조회일 YYYYMMDD (기본 오늘)

    Returns:
        {
            "BPS": int,      # 주당순자산
            "PER": float,    # 주가수익비율
            "PBR": float,    # 주가순자산비율
            "EPS": int,      # 주당순이익
            "DIV": float,    # 배당수익률 (%)
            "DPS": int       # 주당배당금
        }
        or None (실패 시)
    """
    # 1차 시도: pykrx
    try:
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        df = stock.get_market_fundamental(date, date, ticker)

        if not df.empty:
            row = df.iloc[-1]
            return {
                "BPS": int(row["BPS"]),
                "PER": float(row["PER"]),
                "PBR": float(row["PBR"]),
                "EPS": int(row["EPS"]),
                "DIV": float(row["DIV"]),
                "DPS": int(row["DPS"]),
            }
    except Exception:
        pass

    # 2차 시도: 네이버 금융 fallback
    try:
        from utils.web_scraper import get_naver_stock_info
        info = get_naver_stock_info(ticker)
        if info and (info.get("per") is not None or info.get("pbr") is not None):
            return {
                "BPS": 0,  # 네이버에서 제공 안 함
                "PER": float(info.get("per", 0) or 0),
                "PBR": float(info.get("pbr", 0) or 0),
                "EPS": 0,  # 네이버에서 제공 안 함
                "DIV": 0.0,  # 네이버에서 제공 안 함
                "DPS": 0,  # 네이버에서 제공 안 함
            }
    except Exception:
        pass

    return None


def get_market_cap(
    ticker: str,
    date: Optional[str] = None
) -> Optional[dict]:
    """
    시가총액 정보 조회 (pykrx 우선, 실패 시 Naver fallback)

    Args:
        ticker: 종목코드
        date: 조회일 YYYYMMDD (기본 오늘)

    Returns:
        {
            "시가총액": int,
            "거래량": int,
            "거래대금": int or None,
            "상장주식수": int or None,
            "외국인보유주식수": int or None
        }
        or None (실패 시)
    """
    # 1차: pykrx
    try:
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        df = stock.get_market_cap(date, date, ticker)

        if not df.empty:
            row = df.iloc[-1]
            return {
                "시가총액": int(row["시가총액"]),
                "거래량": int(row["거래량"]),
                "거래대금": int(row["거래대금"]),
                "상장주식수": int(row["상장주식수"]),
                "외국인보유주식수": int(row.get("외국인보유주식수", 0)),
            }
    except Exception:
        pass

    # 2차: Naver fallback
    try:
        from utils.web_scraper import get_naver_stock_info
        info = get_naver_stock_info(ticker)
        if info and info.get("market_cap"):
            return {
                "시가총액": int(info["market_cap"]) * 100000000,  # 억→원
                "거래량": int(info.get("volume", 0) or 0),
                "거래대금": None,  # Naver 미제공
                "상장주식수": None,  # Naver 미제공
                "외국인보유주식수": None,  # Naver 미제공
            }
    except Exception:
        pass

    return None


