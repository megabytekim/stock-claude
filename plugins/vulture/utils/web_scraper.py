"""웹 스크래핑 유틸리티

네이버 금융 등에서 데이터를 추출하는 함수들
Playwright 결과를 후처리하거나 requests로 직접 스크래핑
"""
import re
from typing import Optional
import requests
from bs4 import BeautifulSoup


def get_naver_stock_info(ticker: str) -> Optional[dict]:
    """
    네이버 금융에서 종목 정보 스크래핑

    Args:
        ticker: 종목코드 (예: "048910")

    Returns:
        {
            "name": "대원미디어",
            "price": 7490,
            "change": -310,
            "change_pct": -3.97,
            "volume": 63512,
            "prev_close": 7800,
            "open": 7790,
            "high": 7850,
            "low": 7490,
            "market_cap": 89014,  # 억 단위 정수 (8조 9,014억 = 89014)
            "per": 12.5,
            "pbr": 1.04,
            "foreign_ratio": 3.24
        }
        or None (실패 시)
    """
    try:
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        result = {}

        # 종목명
        wrap_company = soup.select_one("div.wrap_company h2 a")
        if wrap_company:
            result["name"] = wrap_company.text.strip()

        # 현재가
        no_today = soup.select_one("p.no_today span.blind")
        if no_today:
            result["price"] = _parse_number(no_today.text)

        # 전일대비
        no_exday = soup.select("p.no_exday span.blind")
        if len(no_exday) >= 2:
            change = _parse_number(no_exday[0].text)
            change_pct = _parse_float(no_exday[1].text.replace("%", ""))

            # 상승/하락 판단
            ico = soup.select_one("p.no_exday em")
            if ico and "down" in str(ico.get("class", [])):
                change = -change
                change_pct = -change_pct

            result["change"] = change
            result["change_pct"] = change_pct

        # 시세 테이블 (전일, 시가, 고가, 저가, 거래량)
        table = soup.select_one("table.no_info")
        if table:
            rows = table.select("tr")
            for row in rows:
                tds = row.select("td")
                for td in tds:
                    text = td.text.strip()
                    blind = td.select_one("span.blind")
                    if blind:
                        value = _parse_number(blind.text)
                        if "전일" in text:
                            result["prev_close"] = value
                        elif "시가" in text:
                            result["open"] = value
                        elif "고가" in text:
                            result["high"] = value
                        elif "저가" in text:
                            result["low"] = value
                        elif "거래량" in text:
                            result["volume"] = value

        # 투자정보 (시가총액, PER, PBR, 외국인비율)
        aside = soup.select_one("div.aside_invest_info")
        if aside:
            items = aside.select("tr")
            for item in items:
                th = item.select_one("th")
                td = item.select_one("td")
                if th and td:
                    label = th.text.strip()
                    value_elem = td.select_one("em") or td
                    value_text = value_elem.text.strip()

                    if label == "시가총액":  # 정확 매칭 (시가총액순위와 구분)
                        result["market_cap"] = _parse_market_cap(value_text)
                    elif "PER" in label:
                        result["per"] = _parse_float(value_text)
                    elif "PBR" in label:
                        result["pbr"] = _parse_float(value_text)
                    elif "외국인" in label:
                        result["foreign_ratio"] = _parse_float(value_text.replace("%", ""))

        return result if result else None

    except Exception:
        return None


def get_naver_stock_news(ticker: str, limit: int = 5) -> Optional[list]:
    """
    네이버 금융에서 종목 뉴스 스크래핑

    Args:
        ticker: 종목코드
        limit: 최대 뉴스 개수

    Returns:
        [
            {"title": "...", "date": "01/08", "url": "..."},
            ...
        ]
        or None (실패 시)
    """
    try:
        url = f"https://finance.naver.com/item/news.naver?code={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        news_list = []
        items = soup.select("table.type5 tr")

        for item in items[:limit * 2]:  # 헤더 등 건너뛰기 위해 여유있게
            title_elem = item.select_one("td.title a")
            date_elem = item.select_one("td.date")

            if title_elem and date_elem:
                news_list.append({
                    "title": title_elem.text.strip(),
                    "date": date_elem.text.strip(),
                    "url": "https://finance.naver.com" + title_elem.get("href", "")
                })

                if len(news_list) >= limit:
                    break

        return news_list if news_list else None

    except Exception:
        return None


def get_naver_discussion(ticker: str, limit: int = 10) -> Optional[list]:
    """
    네이버 금융 종목토론방 스크래핑

    Args:
        ticker: 종목코드
        limit: 최대 게시글 개수

    Returns:
        [
            {"title": "...", "date": "01/08 10:21", "url": "..."},
            ...
        ]
        or None (실패 시)
    """
    try:
        url = f"https://finance.naver.com/item/board.naver?code={ticker}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        posts = []
        items = soup.select("table.type2 tr")

        for item in items:
            title_elem = item.select_one("td.title a")
            date_elem = item.select_one("td span.tah")

            if title_elem:
                date_text = date_elem.text.strip() if date_elem else ""
                posts.append({
                    "title": title_elem.text.strip(),
                    "date": date_text,
                    "url": "https://finance.naver.com" + title_elem.get("href", "")
                })

                if len(posts) >= limit:
                    break

        return posts if posts else None

    except Exception:
        return None


def clean_playwright_result(text: str) -> str:
    """
    Playwright 결과물 후처리 (크기 축소)

    Args:
        text: Playwright snapshot 텍스트

    Returns:
        정제된 텍스트 (크기 약 70-80% 감소)
    """
    # 1. [ref=eXXX] 제거
    text = re.sub(r'\[ref=e\d+\]', '', text)

    # 2. [cursor=pointer] 제거
    text = re.sub(r'\[cursor=\w+\]', '', text)

    # 3. 빈 괄호 정리
    text = re.sub(r'\[\s*\]', '', text)

    # 4. 연속 공백 정리
    text = re.sub(r'  +', ' ', text)

    # 5. 빈 줄 정리
    text = re.sub(r'\n\s*\n', '\n', text)

    return text.strip()


def _parse_number(text: str) -> int:
    """텍스트에서 숫자 추출 (콤마 제거)"""
    try:
        clean = re.sub(r'[^\d\-]', '', text)
        return int(clean) if clean else 0
    except:
        return 0


def _parse_float(text: str) -> float:
    """텍스트에서 실수 추출"""
    try:
        clean = re.sub(r'[^\d\.\-]', '', text)
        return float(clean) if clean else 0.0
    except:
        return 0.0


def get_naver_stock_list(market: str = "KOSPI") -> Optional[list]:
    """
    네이버 금융에서 종목 리스트 조회

    Args:
        market: "KOSPI" 또는 "KOSDAQ"

    Returns:
        [{"code": "005930", "name": "삼성전자"}, ...] or None
    """
    market_code = "0" if market == "KOSPI" else "1"
    url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={market_code}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        all_stocks = []
        for page in range(1, 50):  # 최대 50페이지
            resp = requests.get(f"{url}&page={page}", headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select("table.type_2 tr")
            page_stocks = []

            for row in rows:
                link = row.select_one("a.tltle")
                if link:
                    href = link.get("href", "")
                    code = href.split("code=")[-1] if "code=" in href else ""
                    if code and len(code) == 6:
                        page_stocks.append({"code": code, "name": link.get_text(strip=True)})

            if not page_stocks:
                break
            all_stocks.extend(page_stocks)

        return all_stocks if all_stocks else None
    except Exception:
        return None


def _parse_market_cap(text: str) -> int:
    """
    시가총액 텍스트를 억 단위 숫자로 변환

    Args:
        text: "8조 9,014억", "883조\n8,019", "500억" 등의 형식

    Returns:
        억 단위 정수 (예: 89014, 8838019, 500)
    """
    if not text:
        return 0

    try:
        # 공백, 줄바꿈, 탭 정리
        clean = re.sub(r'[\s]+', ' ', text).strip()

        if '조' in clean:
            # "8조 9,014" 또는 "883조 8,019" 형식 처리
            # 조 앞의 숫자와 조 뒤의 숫자를 추출
            jo_match = re.search(r'(\d+)\s*조', clean)
            eok_match = re.search(r'조\s*([\d,]+)', clean)

            jo = int(jo_match.group(1)) if jo_match else 0
            eok = 0
            if eok_match:
                eok_str = eok_match.group(1).replace(',', '')
                eok = int(eok_str) if eok_str else 0

            return jo * 10000 + eok  # 억 단위로 변환
        elif '억' in clean:
            # "9,014억" 형식 처리
            eok_match = re.search(r'([\d,]+)\s*억', clean)
            if eok_match:
                return int(eok_match.group(1).replace(',', ''))
            return 0
        else:
            # 숫자만 있는 경우
            digits = re.sub(r'[^\d]', '', clean)
            return int(digits) if digits else 0
    except (ValueError, IndexError):
        return 0
