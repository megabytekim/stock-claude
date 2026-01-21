"""
Deprecated functions - stub implementations for backwards compatibility.

These functions no longer work due to KRX (Korea Exchange) access policy changes
as of 2025-12-27. KRX now requires login for data access.

Related issues:
- https://github.com/sharebook-kr/pykrx/issues/244
- https://github.com/sharebook-kr/pykrx/issues/247
"""
from typing import Optional, Any


def get_investor_trading(ticker: str, *args: Any, **kwargs: Any) -> Optional[dict]:
    """
    DEPRECATED: 투자자별 매매동향 데이터 - KRX 로그인 필수화로 사용 불가.

    대안: KRX Data Marketplace 유료 API 또는 증권사 API 사용

    Args:
        ticker: 종목코드

    Returns:
        None (always)
    """
    return None


def get_short_selling(ticker: str, *args: Any, **kwargs: Any) -> Optional[dict]:
    """
    DEPRECATED: 공매도 현황 데이터 - KRX 로그인 필수화로 사용 불가.

    대안: KRX Data Marketplace 유료 API 또는 증권사 API 사용

    Args:
        ticker: 종목코드

    Returns:
        None (always)
    """
    return None
