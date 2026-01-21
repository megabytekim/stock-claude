"""TI (Technical Intelligence) 통합 분석 함수

TI 워커 에이전트가 사용하는 통합 분석 함수
숫자 데이터 + 52주 고저 + 기술지표 + 신호 판단을 한 번에 처리
"""
from datetime import datetime
from typing import Optional

from utils.data_fetcher import get_ohlcv, get_ticker_name
from utils.indicators import sma, ema, rsi, macd, bollinger, stochastic, support_resistance
from utils.web_scraper import get_naver_stock_info


def get_rsi_signal(rsi_value: float) -> str:
    """RSI 값으로 신호 판단

    Args:
        rsi_value: RSI 값 (0-100)

    Returns:
        "과매수" | "과매도" | "중립"
    """
    if rsi_value > 70:
        return "과매수"
    elif rsi_value < 30:
        return "과매도"
    else:
        return "중립"


def get_ma_alignment(current: float, ma5: float, ma20: float, ma60: float) -> str:
    """이동평균 배열 판단

    Args:
        current: 현재가
        ma5: 5일 이동평균
        ma20: 20일 이동평균
        ma60: 60일 이동평균

    Returns:
        "완전 정배열" | "완전 역배열" | "혼조"
    """
    if current > ma5 > ma20 > ma60:
        return "완전 정배열"
    elif current < ma5 < ma20 < ma60:
        return "완전 역배열"
    else:
        return "혼조"


def get_ti_full_analysis(ticker: str) -> dict:
    """TI 워커를 위한 통합 분석 함수

    숫자 데이터, 52주 고저, 기술지표, 신호 판단을 모두 수행

    Args:
        ticker: 종목코드 (예: "005930")

    Returns:
        {
            "meta": {"ticker", "name", "timestamp"},
            "price_info": {...} or None,
            "week52": {...} or None,
            "indicators": {...} or None,
            "support_resistance": {...} or None,
            "signals": {...} or None
        }
    """
    result = {
        "meta": {
            "ticker": ticker,
            "name": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "price_info": None,
        "week52": None,
        "indicators": None,
        "support_resistance": None,
        "signals": None,
    }

    # 1. 종목명 조회
    name = get_ticker_name(ticker)
    result["meta"]["name"] = name

    # 2. 숫자 데이터 (Naver Finance)
    naver_info = get_naver_stock_info(ticker)
    if naver_info:
        result["price_info"] = {
            "name": naver_info.get("name"),
            "price": naver_info.get("price"),
            "change": naver_info.get("change"),
            "change_pct": naver_info.get("change_pct"),
            "open": naver_info.get("open"),
            "high": naver_info.get("high"),
            "low": naver_info.get("low"),
            "volume": naver_info.get("volume"),
            "market_cap": naver_info.get("market_cap"),
            "per": naver_info.get("per"),
            "pbr": naver_info.get("pbr"),
            "foreign_ratio": naver_info.get("foreign_ratio"),
        }

    # 3. 52주 고저 (pykrx)
    df_year = get_ohlcv(ticker, days=252)
    if df_year is not None and not df_year.empty:
        high_52w = df_year['고가'].max()
        low_52w = df_year['저가'].min()
        high_date = df_year['고가'].idxmax()
        low_date = df_year['저가'].idxmin()

        # 현재가 위치 계산
        current_price = naver_info.get("price") if naver_info else None
        position_pct = None
        if current_price and high_52w > low_52w:
            position_pct = (current_price - low_52w) / (high_52w - low_52w) * 100

        result["week52"] = {
            "high": int(high_52w),
            "high_date": str(high_date),
            "low": int(low_52w),
            "low_date": str(low_date),
            "position_pct": round(position_pct, 1) if position_pct else None,
        }

    # 4. 기술지표 (pykrx 60일 데이터)
    df = get_ohlcv(ticker, days=60)
    if df is not None and not df.empty:
        close = df['종가']
        high = df['고가']
        low = df['저가']

        # RSI
        rsi_val = rsi(close).iloc[-1]
        rsi_signal_str = get_rsi_signal(rsi_val)

        # MACD
        macd_line, signal_line, hist = macd(close)
        macd_signal_str = "상승" if macd_line.iloc[-1] > signal_line.iloc[-1] else "하락"

        # 볼린저 밴드
        upper, middle, lower = bollinger(close)
        current = close.iloc[-1]
        bb_position = (current - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1]) * 100

        # 스토캐스틱
        k, d = stochastic(high, low, close)
        stoch_signal = "과매수" if k.iloc[-1] > 80 else ("과매도" if k.iloc[-1] < 20 else "중립")

        # 이동평균
        ma5_val = sma(close, 5).iloc[-1]
        ma20_val = sma(close, 20).iloc[-1]
        ma60_val = sma(close, 60).iloc[-1] if len(close) >= 60 else None

        # 배열 판단
        ma_alignment_str = None
        if ma60_val:
            ma_alignment_str = get_ma_alignment(current, ma5_val, ma20_val, ma60_val)

        result["indicators"] = {
            "rsi": {
                "value": round(rsi_val, 1),
                "signal": rsi_signal_str,
            },
            "macd": {
                "macd": round(macd_line.iloc[-1], 2),
                "signal": round(signal_line.iloc[-1], 2),
                "histogram": round(hist.iloc[-1], 2),
                "trend": macd_signal_str,
            },
            "bollinger": {
                "upper": round(upper.iloc[-1], 0),
                "middle": round(middle.iloc[-1], 0),
                "lower": round(lower.iloc[-1], 0),
                "position_pct": round(bb_position, 1),
            },
            "stochastic": {
                "k": round(k.iloc[-1], 1),
                "d": round(d.iloc[-1], 1),
                "signal": stoch_signal,
            },
            "ma": {
                "ma5": round(ma5_val, 0),
                "ma20": round(ma20_val, 0),
                "ma60": round(ma60_val, 0) if ma60_val else None,
                "alignment": ma_alignment_str,
            },
        }

        # 지지/저항선
        sr = support_resistance(high, low, close)
        result["support_resistance"] = {
            "pivot": round(sr["pivot"], 0),
            "r1": round(sr["r1"], 0),
            "r2": round(sr["r2"], 0),
            "s1": round(sr["s1"], 0),
            "s2": round(sr["s2"], 0),
        }

        # 종합 신호
        result["signals"] = {
            "rsi_signal": rsi_signal_str,
            "macd_signal": macd_signal_str,
            "stochastic_signal": stoch_signal,
            "ma_alignment": ma_alignment_str,
        }

    return result


def print_ti_report(ticker: str) -> None:
    """TI 리포트 출력 (TI 에이전트 호출용)

    Args:
        ticker: 종목코드
    """
    data = get_ti_full_analysis(ticker)

    print("=" * 50)
    print(f"TI Report: {data['meta']['name']} ({data['meta']['ticker']})")
    print(f"수집 시각: {data['meta']['timestamp']}")
    print("=" * 50)

    # 1. 숫자 데이터
    price = data.get("price_info")
    if price:
        print("\n[1. 숫자 데이터 (Naver Finance)]")
        print(f"종목명: {price.get('name')}")
        if price.get('price'):
            print(f"현재가: {price.get('price'):,}원")
        if price.get('change') is not None:
            print(f"전일대비: {price.get('change'):+,}원 ({price.get('change_pct'):+.2f}%)")
        if price.get('open'):
            print(f"시가/고가/저가: {price.get('open'):,} / {price.get('high'):,} / {price.get('low'):,}")
        if price.get('volume'):
            print(f"거래량: {price.get('volume'):,}주")
        if price.get('market_cap'):
            print(f"시가총액: {price.get('market_cap')}")
        if price.get('per'):
            print(f"PER: {price.get('per')}")
        if price.get('pbr'):
            print(f"PBR: {price.get('pbr')}")
        if price.get('foreign_ratio'):
            print(f"외국인비율: {price.get('foreign_ratio')}%")
    else:
        print("\n[1. 숫자 데이터] 조회 실패")

    # 2. 52주 고저
    w52 = data.get("week52")
    if w52:
        print("\n[2. 52주 고저 (pykrx)]")
        print(f"52주 최고: {w52.get('high'):,}원 ({w52.get('high_date')})")
        print(f"52주 최저: {w52.get('low'):,}원 ({w52.get('low_date')})")
        if w52.get('position_pct') is not None:
            print(f"52주 레인지 위치: {w52.get('position_pct')}%")
    else:
        print("\n[2. 52주 고저] 조회 실패")

    # 3. 기술지표
    ind = data.get("indicators")
    if ind:
        print("\n[3. 기술지표]")
        rsi_data = ind.get("rsi", {})
        print(f"RSI(14): {rsi_data.get('value')} ({rsi_data.get('signal')})")

        macd_data = ind.get("macd", {})
        print(f"MACD: {macd_data.get('macd')} / Signal: {macd_data.get('signal')} ({macd_data.get('trend')})")

        bb = ind.get("bollinger", {})
        print(f"볼린저: {bb.get('lower'):,.0f} ~ {bb.get('upper'):,.0f} (위치: {bb.get('position_pct')}%)")

        stoch = ind.get("stochastic", {})
        print(f"스토캐스틱: %K={stoch.get('k')}, %D={stoch.get('d')} ({stoch.get('signal')})")

        ma = ind.get("ma", {})
        ma_str = f"MA5={ma.get('ma5'):,.0f} / MA20={ma.get('ma20'):,.0f}"
        if ma.get('ma60'):
            ma_str += f" / MA60={ma.get('ma60'):,.0f}"
        print(f"이동평균: {ma_str}")
        if ma.get('alignment'):
            print(f"배열: {ma.get('alignment')}")
    else:
        print("\n[3. 기술지표] 조회 실패")

    # 4. 지지/저항선
    sr = data.get("support_resistance")
    if sr:
        print("\n[4. 지지/저항선]")
        print(f"저항선: R1={sr.get('r1'):,.0f}원, R2={sr.get('r2'):,.0f}원")
        print(f"지지선: S1={sr.get('s1'):,.0f}원, S2={sr.get('s2'):,.0f}원")

    print("\n" + "=" * 50)
    print("TI 데이터 수집 완료")
    print("=" * 50)


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "005930"
    print_ti_report(ticker)
