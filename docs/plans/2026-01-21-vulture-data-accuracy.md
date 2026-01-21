# Vulture Data Accuracy Improvements

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix PER parsing bug in TI worker and add FnGuide FinanceRatio page for ROE/ROA in FI worker

**Architecture:**
- Task 3: TI의 web_scraper.py에서 PER 파싱 시 "동일업종 PER"이 아닌 실제 종목 PER을 수집하도록 수정
- Task 4: FI의 financial_scraper.py에 FnGuide 재무비율 페이지(SVD_FinanceRatio.asp) 파싱 추가, ROE/ROA 직접 수집 (계산은 fallback)

**Tech Stack:** Python, requests, BeautifulSoup, pytest

---

## Task 1: PER 파싱 버그 분석 및 테스트 작성

**Files:**
- Modify: `plugins/vulture/tests/test_web_scraper.py`
- Reference: `plugins/vulture/tests/fixtures/naver_stock_page.html`

**Step 1: 현재 fixture 확인 및 문제점 분석**

네이버 금융 시세 페이지 HTML 구조:
```html
<!-- 실제 종목 PER (이것을 파싱해야 함) -->
<tr>
  <td>PER</td>
  <td>31.04</td>  <!-- 삼성전자 PER -->
</tr>

<!-- 동일업종 PER (현재 잘못 파싱되고 있음) -->
<tr>
  <th>동일업종 PER</th>
  <td>21.33배</td>
</tr>
```

**Step 2: 실패하는 테스트 작성**

`plugins/vulture/tests/test_web_scraper.py`의 `TestGetNaverStockInfo` 클래스에 추가:

```python
@patch("utils.web_scraper.requests.get")
def test_parses_stock_per_not_industry_per(self, mock_get):
    """종목 PER 파싱 (동일업종 PER 아님)"""
    mock_response = Mock()
    mock_response.text = load_fixture("naver_sise_page.html")
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_naver_stock_info("005930")

    # 삼성전자 실제 PER은 31.04, 동일업종 PER은 21.33
    # 동일업종 PER이 아닌 실제 종목 PER을 파싱해야 함
    assert result["per"] == 31.04
    assert result["per"] != 21.33  # 동일업종 PER이면 안 됨
```

**Step 3: 테스트용 fixture 생성**

Create: `plugins/vulture/tests/fixtures/naver_sise_page.html`

네이버 금융 시세 페이지(sise.naver) HTML 구조를 반영한 fixture:

```html
<!DOCTYPE html>
<html>
<head><title>삼성전자 시세</title></head>
<body>
<div class="wrap_company"><h2><a>삼성전자</a></h2></div>
<table class="no_info">
  <tr>
    <td><span class="blind">55,100</span>전일</td>
    <td><span class="blind">56,000</span>시가</td>
  </tr>
  <tr>
    <td><span class="blind">56,500</span>고가</td>
    <td><span class="blind">54,900</span>저가</td>
  </tr>
  <tr>
    <td><span class="blind">15,234,567</span>거래량</td>
  </tr>
</table>
<p class="no_today"><span class="blind">55,500</span></p>
<p class="no_exday"><span class="blind">400</span><span class="blind">0.73%</span></p>
<div class="aside_invest_info">
  <table>
    <tr><th>시가총액</th><td><em>328조 4,300</em></td></tr>
    <tr><th>시가총액순위</th><td><em>1위</em></td></tr>
    <tr>
      <th>PER</th>
      <td><em>31.04</em>배</td>
    </tr>
    <tr>
      <th>동일업종 PER</th>
      <td><em>21.33</em>배</td>
    </tr>
    <tr>
      <th>PBR</th>
      <td><em>1.12</em>배</td>
    </tr>
    <tr><th>외국인</th><td><em>52.34%</em></td></tr>
  </table>
</div>
</body>
</html>
```

**Step 4: 테스트 실행 (실패 확인)**

Run: `cd plugins/vulture && python -m pytest tests/test_web_scraper.py::TestGetNaverStockInfo::test_parses_stock_per_not_industry_per -v`

Expected: FAIL (현재 코드는 동일업종 PER을 파싱할 가능성)

---

## Task 2: PER 파싱 로직 수정

**Files:**
- Modify: `plugins/vulture/utils/web_scraper.py:98-116`

**Step 1: get_naver_stock_info 함수의 PER 파싱 로직 수정**

현재 코드 (문제):
```python
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

            if label == "시가총액":
                result["market_cap"] = _parse_market_cap(value_text)
            elif "PER" in label:  # 문제: "동일업종 PER"도 매칭됨
                result["per"] = _parse_float(value_text)
```

수정된 코드:
```python
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

            if label == "시가총액":
                result["market_cap"] = _parse_market_cap(value_text)
            elif label == "PER":  # 정확 매칭 (동일업종 PER 제외)
                result["per"] = _parse_float(value_text)
            elif label == "PBR":  # 정확 매칭
                result["pbr"] = _parse_float(value_text)
            elif "외국인" in label:
                result["foreign_ratio"] = _parse_float(value_text.replace("%", ""))
```

**Step 2: 테스트 실행 (성공 확인)**

Run: `cd plugins/vulture && python -m pytest tests/test_web_scraper.py::TestGetNaverStockInfo -v`

Expected: PASS

**Step 3: 기존 테스트 모두 통과 확인**

Run: `cd plugins/vulture && python -m pytest tests/test_web_scraper.py -v`

Expected: All PASS

**Step 4: Commit**

```bash
git add plugins/vulture/utils/web_scraper.py plugins/vulture/tests/test_web_scraper.py plugins/vulture/tests/fixtures/naver_sise_page.html
git commit -m "fix: PER 파싱 시 동일업종 PER 대신 실제 종목 PER 수집"
```

---

## Task 3: FnGuide 재무비율 페이지 파싱 함수 테스트 작성

**Files:**
- Modify: `plugins/vulture/tests/test_financial_scraper.py`
- Create: `plugins/vulture/tests/fixtures/fnguide_ratio_page.html`

**Step 1: FnGuide 재무비율 페이지 구조 분석**

URL: `https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?pGB=1&gicode=A005930`

주요 데이터:
- PER: 29.34 (또는 31.04)
- PBR: 2.51
- ROE: 9.0%
- ROA: 7.1%

**Step 2: fixture 생성**

Create: `plugins/vulture/tests/fixtures/fnguide_ratio_page.html`

```html
<!DOCTYPE html>
<html>
<head><title>삼성전자 재무비율</title></head>
<body>
<h1 class="giName">삼성전자</h1>
<!-- 수익성 지표 테이블 -->
<div id="divProfitRatio">
  <table>
    <thead>
      <tr><th>IFRS연결</th><th>2022/12</th><th>2023/12</th><th>2024/12</th></tr>
    </thead>
    <tbody>
      <tr><th>ROE</th><td>16.22</td><td>3.84</td><td>9.01</td></tr>
      <tr><th>ROA</th><td>12.86</td><td>2.98</td><td>7.12</td></tr>
      <tr><th>영업이익률</th><td>14.35</td><td>2.53</td><td>10.87</td></tr>
    </tbody>
  </table>
</div>
<!-- 밸류에이션 지표 -->
<div id="divValueRatio">
  <table>
    <thead>
      <tr><th>IFRS연결</th><th>2022/12</th><th>2023/12</th><th>2024/12</th></tr>
    </thead>
    <tbody>
      <tr><th>PER</th><td>9.57</td><td>34.12</td><td>29.34</td></tr>
      <tr><th>PBR</th><td>1.52</td><td>1.31</td><td>2.51</td></tr>
    </tbody>
  </table>
</div>
</body>
</html>
```

**Step 3: 실패하는 테스트 작성**

`plugins/vulture/tests/test_financial_scraper.py`에 추가:

```python
class TestGetFnguideRatios:
    """get_fnguide_ratios 함수 테스트 (재무비율 페이지)"""

    @patch('utils.financial_scraper.requests.get')
    def test_returns_dict_on_success(self, mock_get, sample_ticker_kr):
        """성공 시 dict 반환"""
        mock_response = Mock()
        mock_response.text = load_fixture("fnguide_ratio_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_fnguide_ratios(sample_ticker_kr)

        assert isinstance(result, dict)

    @patch('utils.financial_scraper.requests.get')
    def test_has_roe_and_roa(self, mock_get, sample_ticker_kr):
        """ROE, ROA 값 존재 확인"""
        mock_response = Mock()
        mock_response.text = load_fixture("fnguide_ratio_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_fnguide_ratios(sample_ticker_kr)

        assert result is not None
        assert 'roe' in result
        assert 'roa' in result
        # 2024년 기준 ROE=9.01, ROA=7.12
        assert result['roe'] == 9.01
        assert result['roa'] == 7.12

    @patch('utils.financial_scraper.requests.get')
    def test_has_per_and_pbr(self, mock_get, sample_ticker_kr):
        """PER, PBR 값 존재 확인"""
        mock_response = Mock()
        mock_response.text = load_fixture("fnguide_ratio_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_fnguide_ratios(sample_ticker_kr)

        assert result is not None
        assert 'per' in result
        assert 'pbr' in result

    @patch('utils.financial_scraper.requests.get')
    def test_returns_none_on_network_error(self, mock_get, sample_ticker_kr):
        """네트워크 에러 시 None 반환"""
        mock_get.side_effect = Exception("Network error")

        result = get_fnguide_ratios(sample_ticker_kr, retry=0)

        assert result is None

    @patch('utils.financial_scraper.requests.get')
    def test_uses_correct_url(self, mock_get, sample_ticker_kr):
        """올바른 URL 사용 확인"""
        mock_response = Mock()
        mock_response.text = load_fixture("fnguide_ratio_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        get_fnguide_ratios("048910")

        call_args = mock_get.call_args
        assert "SVD_FinanceRatio.asp" in call_args[0][0]
        assert "A048910" in call_args[0][0]
```

**Step 4: import 추가 (테스트 파일)**

`test_financial_scraper.py` 상단에 import 추가:
```python
from utils.financial_scraper import (
    # ... 기존 imports ...
    get_fnguide_ratios,  # 추가
)
```

**Step 5: 테스트 실행 (실패 확인)**

Run: `cd plugins/vulture && python -m pytest tests/test_financial_scraper.py::TestGetFnguideRatios -v`

Expected: FAIL (get_fnguide_ratios 함수가 아직 없음)

---

## Task 4: FnGuide 재무비율 파싱 함수 구현

**Files:**
- Modify: `plugins/vulture/utils/financial_scraper.py`

**Step 1: 상수 추가**

`plugins/vulture/utils/financial_scraper.py` 상단에 추가:

```python
FNGUIDE_RATIO_URL = "https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp"

# 재무비율 테이블 ID
FNGUIDE_RATIO_TABLE_IDS = {
    "divProfitRatio": "profitability",   # 수익성 지표 (ROE, ROA)
    "divValueRatio": "valuation",        # 밸류에이션 (PER, PBR)
}

# 재무비율 메트릭 매핑
PROFITABILITY_METRICS = {
    "ROE": "roe",
    "ROA": "roa",
    "영업이익률": "operating_margin",
    "EBITDA마진율": "ebitda_margin",
}

VALUATION_METRICS = {
    "PER": "per",
    "PBR": "pbr",
    "PSR": "psr",
    "EV/EBITDA": "ev_ebitda",
}
```

**Step 2: get_fnguide_ratios 함수 구현**

```python
def get_fnguide_ratios(ticker: str, retry: int = 1) -> Optional[dict]:
    """FnGuide 재무비율 페이지에서 ROE, ROA, PER, PBR 스크래핑

    Args:
        ticker: 종목코드 (예: "005930")
        retry: 실패 시 재시도 횟수

    Returns:
        {
            "source": "FnGuide FinanceRatio",
            "ticker": "005930",
            "period": "2024/12",
            "roe": 9.01,
            "roa": 7.12,
            "per": 29.34,
            "pbr": 2.51,
            "operating_margin": 10.87,
            "annual": {
                "2024": {"roe": 9.01, "roa": 7.12, "per": 29.34, "pbr": 2.51},
                "2023": {"roe": 3.84, "roa": 2.98, ...},
                ...
            }
        }
        or None (실패 시)
    """
    url = f"{FNGUIDE_RATIO_URL}?pGB=1&gicode=A{ticker}"

    for attempt in range(retry + 1):
        try:
            response = requests.get(url, headers=FNGUIDE_HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            result = {
                "source": "FnGuide FinanceRatio",
                "ticker": ticker,
                "period": None,
                "annual": {},
            }

            # 수익성 지표 파싱 (ROE, ROA)
            profit_data = _parse_fnguide_ratio_table(soup, "divProfitRatio", PROFITABILITY_METRICS)
            if profit_data:
                result["annual"].update({k: {**result["annual"].get(k, {}), **v} for k, v in profit_data.items()})

            # 밸류에이션 지표 파싱 (PER, PBR)
            value_data = _parse_fnguide_ratio_table(soup, "divValueRatio", VALUATION_METRICS)
            if value_data:
                result["annual"].update({k: {**result["annual"].get(k, {}), **v} for k, v in value_data.items()})

            if not result["annual"]:
                raise ValueError("Failed to parse ratio data")

            # 최신 연도 데이터 추출
            years = sorted(result["annual"].keys(), reverse=True)
            if years:
                latest_year = years[0]
                result["period"] = f"{latest_year}/12"
                latest = result["annual"][latest_year]
                result["roe"] = latest.get("roe")
                result["roa"] = latest.get("roa")
                result["per"] = latest.get("per")
                result["pbr"] = latest.get("pbr")
                result["operating_margin"] = latest.get("operating_margin")

            return result

        except Exception as e:
            if attempt < retry:
                time.sleep(1)
                continue
            return None

    return None


def _parse_fnguide_ratio_table(soup: BeautifulSoup, div_id: str, metrics: dict) -> Optional[dict]:
    """FnGuide 재무비율 테이블 파싱

    Args:
        soup: BeautifulSoup 객체
        div_id: 테이블 div ID (예: "divProfitRatio")
        metrics: 한글→영문 메트릭 매핑

    Returns:
        {
            "2024": {"roe": 9.01, "roa": 7.12},
            "2023": {"roe": 3.84, "roa": 2.98},
            ...
        }
    """
    div_elem = soup.find("div", id=div_id)
    if not div_elem:
        return None

    table = div_elem.find("table")
    if not table:
        return None

    # 헤더에서 기간 추출
    headers = []
    thead = table.find("thead")
    if thead:
        for th in thead.find_all("th"):
            text = th.text.strip()
            if text:
                headers.append(text)

    if len(headers) < 2:
        return None

    # 기간 컬럼 추출 (YYYY/MM 형식 → YYYY 키)
    periods = []
    for h in headers[1:]:
        match = re.match(r"(\d{4})/(\d{2})", h)
        if match:
            periods.append(match.group(1))
        else:
            periods.append(None)

    # 데이터 행 파싱
    result = {p: {} for p in periods if p}
    tbody = table.find("tbody")
    if not tbody:
        return None

    for tr in tbody.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        # 행 이름 (첫 번째 셀)
        row_name = cells[0].text.strip()
        eng_key = metrics.get(row_name)
        if not eng_key:
            continue

        # 값 추출
        for i, cell in enumerate(cells[1:]):
            if i >= len(periods) or not periods[i]:
                continue
            value = _parse_fnguide_number(cell.text.strip())
            if value is not None:
                result[periods[i]][eng_key] = value

    return {k: v for k, v in result.items() if v} or None
```

**Step 3: 테스트 실행 (성공 확인)**

Run: `cd plugins/vulture && python -m pytest tests/test_financial_scraper.py::TestGetFnguideRatios -v`

Expected: PASS

**Step 4: Commit**

```bash
git add plugins/vulture/utils/financial_scraper.py plugins/vulture/tests/test_financial_scraper.py plugins/vulture/tests/fixtures/fnguide_ratio_page.html
git commit -m "feat: FnGuide 재무비율 페이지에서 ROE/ROA 수집 기능 추가"
```

---

## Task 5: _calculate_ratios 함수 수정 (FnGuide 우선, 계산 fallback)

**Files:**
- Modify: `plugins/vulture/utils/financial_scraper.py`
- Modify: `plugins/vulture/tests/test_financial_scraper.py`

**Step 1: 테스트 작성 - ROE/ROA FnGuide 우선 수집**

```python
class TestCalculateRatiosWithFnguide:
    """_calculate_ratios 함수 테스트 (FnGuide 우선)"""

    def test_uses_fnguide_roe_when_available(self):
        """FnGuide ROE가 있으면 계산하지 않고 그대로 사용"""
        income_data = {'2024': {'net_income': 10}}
        balance_data = {'2024': {'total_equity': 100}}
        fnguide_ratios = {'roe': 9.01, 'roa': 7.12}

        result = _calculate_ratios(income_data, balance_data, fnguide_ratios)

        # 계산값(10.0)이 아닌 FnGuide 값(9.01) 사용
        assert result['roe'] == 9.01
        assert result['roa'] == 7.12

    def test_calculates_roe_when_fnguide_unavailable(self):
        """FnGuide 없으면 직접 계산"""
        income_data = {'2024': {'net_income': 10}}
        balance_data = {'2024': {'total_equity': 100}}
        fnguide_ratios = None

        result = _calculate_ratios(income_data, balance_data, fnguide_ratios)

        # 직접 계산: 10/100 * 100 = 10.0
        assert result['roe'] == 10.0

    def test_calculates_roe_when_fnguide_roe_is_none(self):
        """FnGuide ROE가 None이면 직접 계산"""
        income_data = {'2024': {'net_income': 10}}
        balance_data = {'2024': {'total_equity': 100}}
        fnguide_ratios = {'roe': None, 'roa': None}

        result = _calculate_ratios(income_data, balance_data, fnguide_ratios)

        assert result['roe'] == 10.0
```

**Step 2: 테스트 실행 (실패 확인)**

Run: `cd plugins/vulture && python -m pytest tests/test_financial_scraper.py::TestCalculateRatiosWithFnguide -v`

Expected: FAIL (현재 _calculate_ratios는 fnguide_ratios 파라미터 없음)

**Step 3: _calculate_ratios 함수 수정**

기존:
```python
def _calculate_ratios(income_data: Optional[dict], balance_data: Optional[dict]) -> dict:
```

수정:
```python
def _calculate_ratios(
    income_data: Optional[dict],
    balance_data: Optional[dict],
    fnguide_ratios: Optional[dict] = None
) -> dict:
    """재무비율 계산 (FnGuide 우선, 계산 fallback)

    Args:
        income_data: 손익계산서 데이터
        balance_data: 재무상태표 데이터
        fnguide_ratios: FnGuide 재무비율 페이지 데이터 (우선 사용)

    Returns:
        {
            "debt_ratio": float,
            "current_ratio": float,
            "roe": float,
            "roa": float,
            "roe_source": "FnGuide" | "calculated",
            "roa_source": "FnGuide" | "calculated"
        }
    """
    ratios = {
        "debt_ratio": None,
        "current_ratio": None,
        "roe": None,
        "roa": None,
        "roe_source": None,
        "roa_source": None,
    }

    # 1순위: FnGuide 재무비율 페이지에서 ROE/ROA 가져오기
    if fnguide_ratios:
        if fnguide_ratios.get("roe") is not None:
            ratios["roe"] = fnguide_ratios["roe"]
            ratios["roe_source"] = "FnGuide"
        if fnguide_ratios.get("roa") is not None:
            ratios["roa"] = fnguide_ratios["roa"]
            ratios["roa_source"] = "FnGuide"

    if not balance_data:
        return ratios

    latest_year = max(balance_data.keys())
    balance = balance_data[latest_year]

    # 부채비율, 유동비율 계산 (항상 계산)
    tl = balance.get("total_liabilities")
    te = balance.get("total_equity")
    if tl and te and te != 0:
        ratios["debt_ratio"] = round(tl / te * 100, 2)

    ca = balance.get("current_assets")
    cl = balance.get("current_liabilities")
    if ca and cl and cl != 0:
        ratios["current_ratio"] = round(ca / cl * 100, 2)

    # 2순위: FnGuide 없으면 직접 계산 (fallback)
    if ratios["roe"] is None and income_data and latest_year in income_data:
        ni = income_data[latest_year].get("net_income")
        if ni is not None and te and te != 0:
            ratios["roe"] = round(ni / te * 100, 2)
            ratios["roe_source"] = "calculated"

    if ratios["roa"] is None and income_data and latest_year in income_data:
        ni = income_data[latest_year].get("net_income")
        ta = balance.get("total_assets")
        if ni is not None and ta and ta != 0:
            ratios["roa"] = round(ni / ta * 100, 2)
            ratios["roa_source"] = "calculated"

    return ratios
```

**Step 4: get_fnguide_financial 함수에서 재무비율 페이지 호출 추가**

`get_fnguide_financial` 함수 수정:

```python
def get_fnguide_financial(ticker: str, retry: int = 2) -> Optional[dict]:
    # ... 기존 코드 ...

    # 재무비율 페이지에서 ROE/ROA 가져오기 (1순위)
    fnguide_ratios = get_fnguide_ratios(ticker, retry=1)

    # ... 손익, 재무상태표 파싱 ...

    # 재무비율 계산 (FnGuide 우선)
    ratios = _calculate_ratios(income_annual, balance_annual, fnguide_ratios)

    return {
        # ... 기존 필드들 ...
        "ratios": ratios,
        "fnguide_ratios": fnguide_ratios,  # 원본 데이터 보존
    }
```

**Step 5: 테스트 실행**

Run: `cd plugins/vulture && python -m pytest tests/test_financial_scraper.py -v`

Expected: All PASS

**Step 6: Commit**

```bash
git add plugins/vulture/utils/financial_scraper.py plugins/vulture/tests/test_financial_scraper.py
git commit -m "feat: ROE/ROA 수집 시 FnGuide 재무비율 페이지 우선, 계산은 fallback으로"
```

---

## Task 6: 통합 테스트 및 실제 데이터 검증

**Files:**
- Reference: `plugins/vulture/tests/test_integration.py`

**Step 1: 실제 네트워크 호출로 검증 (수동)**

```bash
cd plugins/vulture && python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from utils.web_scraper import get_naver_stock_info
from utils.financial_scraper import get_fnguide_ratios, get_financial_data

# TI: Naver Finance PER 확인
print("=== TI: Naver Finance ===")
naver = get_naver_stock_info("005930")
if naver:
    print(f"삼성전자 PER: {naver.get('per')}")
    print(f"삼성전자 PBR: {naver.get('pbr')}")
else:
    print("Naver Finance 조회 실패")

# FI: FnGuide 재무비율 확인
print("\n=== FI: FnGuide 재무비율 ===")
ratios = get_fnguide_ratios("005930")
if ratios:
    print(f"ROE: {ratios.get('roe')}%")
    print(f"ROA: {ratios.get('roa')}%")
    print(f"PER: {ratios.get('per')}")
    print(f"PBR: {ratios.get('pbr')}")
else:
    print("FnGuide 재무비율 조회 실패")

# FI: 통합 재무제표
print("\n=== FI: 통합 재무제표 ===")
financial = get_financial_data("005930")
if financial:
    ratios = financial.get("ratios", {})
    print(f"ROE: {ratios.get('roe')}% (source: {ratios.get('roe_source')})")
    print(f"ROA: {ratios.get('roa')}% (source: {ratios.get('roa_source')})")
else:
    print("재무제표 조회 실패")
EOF
```

**Step 2: 예상 출력 확인**

Expected:
```
=== TI: Naver Finance ===
삼성전자 PER: 31.04  (동일업종 PER 21.33이 아님)
삼성전자 PBR: ...

=== FI: FnGuide 재무비율 ===
ROE: 9.01%  (또는 유사한 값)
ROA: 7.12%  (또는 유사한 값)

=== FI: 통합 재무제표 ===
ROE: 9.01% (source: FnGuide)  (calculated가 아님)
ROA: 7.12% (source: FnGuide)
```

**Step 3: 전체 테스트 실행**

Run: `cd plugins/vulture && python -m pytest tests/ -v --tb=short`

Expected: All PASS

**Step 4: Final Commit**

```bash
git add -A
git commit -m "test: 통합 테스트 및 실제 데이터 검증 완료"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | PER 파싱 버그 테스트 작성 | test_web_scraper.py, fixture |
| 2 | PER 파싱 로직 수정 (정확 매칭) | web_scraper.py |
| 3 | FnGuide 재무비율 파싱 테스트 | test_financial_scraper.py, fixture |
| 4 | get_fnguide_ratios 함수 구현 | financial_scraper.py |
| 5 | _calculate_ratios FnGuide 우선 | financial_scraper.py |
| 6 | 통합 테스트 및 검증 | 수동 테스트 |

---

## Key Changes

### PER 수집 (TI)
- Before: `elif "PER" in label:` (동일업종 PER도 매칭)
- After: `elif label == "PER":` (정확 매칭)

### ROE/ROA 수집 (FI)
- Before: 직접 계산만 (`net_income / total_equity`)
- After:
  1. FnGuide SVD_FinanceRatio.asp 페이지에서 직접 수집 (1순위)
  2. 실패 시 직접 계산 (2순위, fallback)
  3. `roe_source`, `roa_source` 필드로 출처 명시
