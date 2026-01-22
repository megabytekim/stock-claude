---
name: vulture-analyze
description: Comprehensive stock analysis with parallel MI/SI/TI/FI worker execution. Main context orchestrates directly.
arguments:
  - name: ticker
    description: Stock symbol to analyze (e.g., NVDA, 005930, Samsung)
    required: true
  - name: depth
    description: Analysis depth (quick/standard/deep)
    required: false
    default: deep
---

# Vulture Analysis Command

This command performs comprehensive stock analysis by **orchestrating MI/SI/TI/FI workers directly from main context**.

## Reference File (Golden Sample)

> **TODO**: Golden sample 파일은 아직 없습니다. 추후 추가 예정.
>
> Golden sample이 추가되면 `references:` frontmatter에 경로를 넣고,
> 아래 기준으로 리포트 포맷을 참조하세요:
> - 목차 구성 및 순서
> - 테이블 포맷 및 컬럼 구성
> - 섹션별 내용 깊이와 톤
> - Cross-Check Matrix 형식
> - Executive Summary 스타일

## Architecture

```
/vulture-analyze (Main Context - Orchestrator)
    |
    +-> STEP 0: Date verification (WebSearch)
    |
    +-> Parallel Task dispatch:
    |   +-> Task(MI): 정성적 정보 (뉴스, 기업개요, 산업동향) - 숫자 없음!
    |   +-> Task(SI): Sentiment analysis
    |   +-> Task(TI): 숫자 데이터 + 기술지표 (가격, 시총, PER, RSI 등)
    |   +-> Task(FI): 재무제표 (매출, 영업이익, 자산/부채, 성장률)
    |
    +-> STEP 1: Integrate results + Strategic analysis
    +-> STEP 2: Generate report
    +-> STEP 3: Save to watchlist/stocks/{종목명}_{종목코드}.md
```

## Worker Role Division

| Worker | 수집 대상 | 수집 금지 |
|--------|----------|----------|
| **MI** | 뉴스, 기업개요, 산업동향, 경쟁사, 애널리스트 코멘트(정성적) | 가격, 시총, PER, 거래량, 재무제표 등 모든 숫자 |
| **SI** | 센티먼트 점수, 포럼 의견, 이상징후 | - |
| **TI** | 가격, 시총, PER/PBR, 52주고저, RSI, MACD, 볼린저 등 | 재무제표 (FI 담당) |
| **FI** | 매출액, 영업이익, 순이익, 자산/부채, 성장률, PEG | 가격, 기술지표 |

**역할 분리 이유**:
- **TI**: 실시간 가격/기술지표 (pykrx/Naver Finance)
- **FI**: 재무제표 (FnGuide requests -> yfinance fallback)

## Critical Rules

### Data Accuracy Protocol (MANDATORY)

1. **STEP 0 - Date First**: Always verify current date before any data collection
   - Do NOT include explicit year numbers in date search queries (e.g., "2025", "2026")
   - Use: `"what is today's date"` or `"current date"` (without year)
   - Reason: Hardcoded years become outdated and cause incorrect searches
2. **Source Attribution**: ALL data must include source + timestamp
3. **No Speculation**: Never guess prices or make up numbers
4. **Cross-Validation**: Verify data across multiple sources when possible

### Storage Rule (Important)

**Always PREPEND (새 분석을 앞에 추가), never overwrite.**

주식 데이터는 시간에 따라 변합니다. 각 분석은 타임스탬프와 함께 **파일 상단에** 추가됩니다:

```markdown
## Analysis: 2025-01-12 14:30 KST  <- 최신 (새로 추가됨)

[New analysis content]

---

## Analysis: 2025-01-11 09:15 KST  <- 이전 (기존 내용)

[Previous analysis content]
```

이렇게 하면 파일을 열었을 때 최신 분석이 바로 보이고, 과거 분석도 보존됩니다.

---

## Output Path (IMPORTANT)

```python
# Analysis results are saved to watchlist directory at repository root
OUTPUT_DIR = "watchlist/stocks"

# File naming: {종목명}_{종목코드}.md (단일 파일, 폴더 없음)

# Examples:
# Korean: f"{OUTPUT_DIR}/삼성전자_005930.md"
# US: f"{OUTPUT_DIR}/NVIDIA_NVDA.md"
```

---

## Execution Flow

### Phase 1: Setup & Date Verification

```python
# 1. Verify current date (CRITICAL)
# IMPORTANT: Do NOT include year numbers in date search queries!
# Bad:  "today's date 2025" (year may be outdated)
# Good: "what is today's date" or "current date"
WebSearch("what is today's date")

# 2. Determine market type and get company name
market = "KRX" if ticker.isdigit() else "US"
# Company name is retrieved from MI worker or yfinance

# 3. Create/check output directory
OUTPUT_DIR = "watchlist/stocks"
work_dir = f"{OUTPUT_DIR}/{ticker}/"
output_file = f"{work_dir}/analysis.md"
```

### Phase 2: Parallel Worker Dispatch

**Main context dispatches MI + SI + TI + FI in parallel (single message, multiple Task calls)**

```python
# Dispatch all workers in ONE message (parallel execution)

# MI Worker - 정성적 정보만! (숫자 데이터 수집 금지)
Task(
    subagent_type="vulture:market-intelligence",
    prompt=f"""
    Collect QUALITATIVE information for {ticker}:

    DO NOT COLLECT: 가격, 시총, PER, 거래량 등 숫자 데이터 (TI 담당)

    COLLECT:
    1. 최신 뉴스 (5~10개, 날짜/출처 필수, 숫자 제외한 전략적 의미)
    2. 기업 개요 (사업 내용, 주요 제품/서비스)
    3. 경쟁사 정보 (주요 경쟁사, 시장 포지션)
    4. 산업 동향 (섹터 전망, 성장 드라이버)
    5. 전략적 이벤트 (M&A, 신제품, 규제 변화)
    6. 애널리스트 의견 (Buy/Hold/Sell, 정성적 코멘트만)
    7. 리스크 요인 (기업 특화 리스크)

    Return structured qualitative data with ALL sources cited.
    """,
    description=f"MI: {ticker} qualitative info"
)

# SI Worker
Task(
    subagent_type="vulture:sentiment-intelligence",
    prompt=f"""
    Collect sentiment for {ticker}:

    Korean stocks:
    - Naver Stock Forum (종토방)
    - Community reactions

    US stocks:
    - Reddit (WSB, r/stocks)
    - StockTwits bullish/bearish ratio

    Output:
    1. Sentiment score (-2 to +2)
    2. Bullish/Bearish percentage
    3. Key opinions summary
    4. Anomaly check (pump-and-dump, manipulation)
    """,
    description=f"SI: {ticker} sentiment"
)

# TI Worker - 숫자 데이터 + 기술지표 (항상 실행)
Task(
    subagent_type="vulture:technical-intelligence",
    prompt=f"""
    Collect ALL NUMERICAL data and technical indicators for {ticker}:

    ## 1. 숫자 데이터 (MI에서 위임)
    - 현재가, 전일대비, 시가/고가/저가
    - 시가총액 (Naver Finance)
    - 52주 고저 (pykrx 정확 계산)
    - 거래량
    - PER, PBR, 외국인비율 (Naver Finance)

    ## 2. 기술지표
    - RSI(14), MACD, 볼린저밴드
    - 스토캐스틱, 이동평균 (MA5/20/60)
    - 지지/저항선

    ## 3. 종합 판단
    - 매수/중립/매도 신호
    - 신호 근거

    Use Bash + Python with utils functions (get_naver_stock_info, get_ohlcv, rsi, macd, etc.)
    Do NOT use WebSearch for price data.
    """,
    description=f"TI: {ticker} numerical + technicals"
)

# FI Worker - 재무제표 (항상 실행)
Task(
    subagent_type="vulture:financial-intelligence",
    prompt=f"""
    Collect financial statement data for {ticker}:

    ## 데이터 수집 우선순위 (CRITICAL)
    1. FnGuide (utils.get_financial_data) - 1순위
    2. yfinance MCP - 2순위 (US stocks only)
    3. 모두 실패 시 FAIL 명시적 보고
    Playwright 사용 금지 - requests만 사용

    ## 수집 대상
    - 매출액, 영업이익, 순이익 (3년 추이)
    - 자산총계, 부채총계, 자본총계
    - 매출 성장률, 영업이익 성장률 (YoY)
    - PEG (TI의 PER 사용)

    ## 출력 규칙
    - 모든 숫자에 출처 명시 필수
    - 단위: 억원
    - 기준 시점 명시

    Use Bash + Python with utils functions first.
    If utils fails, use yfinance MCP (US stocks only).
    Playwright 사용 금지.
    """,
    description=f"FI: {ticker} financials"
)
```

### Phase 3: Strategic Analysis (Main Context)

After workers complete, main context performs strategic analysis using sector knowledge:

```python
# Integrate MI + SI + TI + FI results
# Apply sector knowledge (see below)
# Generate investment thesis
# Formulate entry/exit strategy
```

### Phase 4: Report Generation & Save (PREPEND 방식 - Context 효율화)

```python
OUTPUT_DIR = "watchlist/stocks"
file_name = f"{company_name}_{ticker}.md"  # 예: 삼성전자_005930.md, NVIDIA_NVDA.md
output_file = f"{OUTPUT_DIR}/{file_name}"

# STEP 1: 디렉토리 확인
mkdir -p {OUTPUT_DIR}

# STEP 2: 새 분석을 임시 파일에 저장 (Write 도구 사용)
# 병렬 실행 시 충돌 방지를 위해 ticker별 고유 파일명 사용
temp_file = f"/tmp/vulture_{ticker}.md"
new_analysis = f"""
# {company_name} ({ticker}) 분석

## Analysis: {current_datetime}

{report_content}

---
"""
Write(temp_file, new_analysis)

# STEP 3: Bash로 PREPEND (기존 파일을 컨텍스트에 로드하지 않음)
# 기존 파일이 없으면 새 분석만 저장, 있으면 prepend
Bash(f"""
if [ -f "{output_file}" ]; then
    cat {temp_file} {output_file} > /tmp/vulture_merged_{ticker}.md
    mv /tmp/vulture_merged_{ticker}.md {output_file}
else
    mv {temp_file} {output_file}
fi
""")

# 결과 예시:
# watchlist/stocks/삼성전자_005930.md
# watchlist/stocks/NVIDIA_NVDA.md
```

**PREPEND 규칙:**
- Bash로 prepend하여 기존 내용을 컨텍스트에 로드하지 않음
- 최신 분석이 항상 파일 상단에 위치
- 기존 분석 내용 절대 삭제 금지

---

## Sector Knowledge Base (Inline)

### Technology

```yaml
Semiconductor:
  Memory: DRAM, NAND, HBM (SK Hynix, Samsung, Micron)
  Non-Memory: AP, Foundry (TSMC, Samsung Foundry)
  Equipment: ASML, Lam Research, Applied Materials
  Key Metrics: ASP trends, bit growth, capex cycle

Software:
  SaaS: ARR, NRR, CAC/LTV
  AI/ML: GPU demand, inference costs
  Cloud: AWS/Azure/GCP market share
```

### Healthcare

```yaml
Pharma:
  Pipeline: Phase 1/2/3 success rates
  Patent cliff: Generic competition timing
  Key Metrics: R&D/Revenue ratio, approval timeline

Biotech:
  Gene therapy: Delivery mechanisms
  Cell therapy: CAR-T, CRISPR
  Key Metrics: Cash runway, clinical milestones
```

### Energy

```yaml
Traditional: Oil price correlation, refining margins
Renewable: Solar/Wind capacity factors, PPA prices
Battery: Cathode/Anode materials, cell-to-pack efficiency
EV: Attach rate, charging infrastructure
```

### Consumer

```yaml
Staples: Pricing power, input costs
Discretionary: Consumer confidence correlation
Luxury: China exposure, brand equity
```

---

## Moat Analysis Framework

Apply these checks during strategic analysis:

```markdown
- Network Effects - Does value increase with more users?
- Switching Costs - How painful to switch to competitor?
- Cost Advantages - Scale economies, proprietary tech?
- Intangible Assets - Brand, patents, licenses?
- Efficient Scale - Natural monopoly characteristics?
```

---

## Valuation Framework

```python
valuation_approach = {
    "growth_stocks": ["PEG", "PSR", "Revenue Growth", "Rule of 40"],
    "value_stocks": ["PER", "PBR", "EV/EBITDA", "FCF Yield"],
    "quality_stocks": ["ROE", "ROIC", "Gross Margin stability"],
    "dividend_stocks": ["Dividend Yield", "Payout Ratio", "DPS Growth"]
}
```

---

## Analysis Depth Options

| Depth | MI Scope | SI Scope | TI Scope | FI Scope |
|-------|----------|----------|----------|----------|
| `quick` | Price + 2 news | Skip | Skip | Skip |
| `standard` | Full data | Forum scan | Basic | Basic (매출/영업이익) |
| `deep` | + Competitor comparison | + Deep sentiment | Full technicals | Full (3년 추이, PEG) |

---

## Output Template

```markdown
# {Company} ({ticker}) Analysis

**Date**: {YYYY-MM-DD HH:MM TZ}
**Depth**: {depth}
**Market**: {KRX/US}

---

## 1. 숫자 데이터 (TI)

### 가격 정보
| 항목 | 값 | 출처 |
|------|-----|------|
| 현재가 | XXX,XXX원 | Naver Finance |
| 전일대비 | +X.X% | |
| 시가총액 | X.XX조원 | Naver Finance |
| 52주 최고 | XXX,XXX원 | pykrx |
| 52주 최저 | XX,XXX원 | pykrx |

### 밸류에이션
| 지표 | 값 | 출처 |
|------|-----|------|
| PER | XX.Xx | Naver Finance |
| PBR | X.XXx | Naver Finance |

---

## 2. 재무제표 (FI)

### 연간 재무 추이 (단위: 억원)
| 연도 | 매출액 | 영업이익 | 순이익 | 출처 |
|------|--------|----------|--------|------|
| 2022 | X,XXX | X,XXX | X,XXX | FnGuide |
| 2023 | X,XXX | X,XXX | X,XXX | FnGuide |
| 2024 | X,XXX | X,XXX | X,XXX | FnGuide |

### 성장률 분석
| 지표 | 값 | 판단 |
|------|-----|------|
| 매출 성장률 (YoY) | +XX.X% | 우수/보통/부진 |
| 영업이익 성장률 (YoY) | +XX.X% | 우수/보통/부진 |

### 재무 안정성
| 항목 | 값 | 출처 |
|------|-----|------|
| 자산총계 | X,XXX억원 | FnGuide |
| 부채총계 | X,XXX억원 | FnGuide |
| 자본총계 | X,XXX억원 | FnGuide |
| 부채비율 | XX.X% | 계산 |

### 밸류에이션 (TI 연계)
| 지표 | 값 | 해석 |
|------|-----|------|
| PER | XX.X | TI 제공 |
| PEG | X.XX | 저평가/적정/고평가 |

---

## 3. 정성적 정보 (MI)

### 최신 뉴스
1. [{title}]({url}) - {source}, {date}
   - 전략적 의미: ...
2. ...

### 기업 개요
- 사업 내용: ...
- 주요 제품: ...

### 산업 동향
- 섹터 전망: ...
- 경쟁 구도: ...

### 애널리스트 의견
- Buy/Hold/Sell 분포 (정성적)
- 주요 코멘트: ...

---

## 4. 센티먼트 (SI)

### Score Summary
| Platform | Score | Interpretation |
|----------|-------|----------------|
| Forum/Reddit | +X.X | Bullish/Bearish |

### Key Opinions
**Bullish**:
- ...

**Bearish**:
- ...

### Anomaly Check
- Pump-and-dump: {status}
- Manipulation signals: {status}

---

## 5. 기술적 분석 (TI)

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI (14) | XX | Overbought/Oversold/Neutral |
| MACD | X.XX | Golden/Dead Cross |
| Bollinger | {position} | |

Support: XXX,XXX원 / Resistance: XXX,XXX원

---

## 6. 전략적 분석

### Sector Position
{MI 기반 산업 분석}

### Moat Assessment
- Network Effects: {Yes/No/Partial}
- Switching Costs: {High/Medium/Low}
- ...

### Investment Thesis
- **Bull Case**: ...
- **Bear Case**: ...
- **Base Case**: ...

---

## 7. 투자 전략

### Entry Points
| Level | Price | Allocation |
|-------|-------|------------|
| 1st | XXX,XXX원 | 30% |
| 2nd | XXX,XXX원 | 40% |
| 3rd | XXX,XXX원 | 30% |

### Targets & Stop Loss
- Target 1: XXX,XXX원 (+XX%)
- Target 2: XXX,XXX원 (+XX%)
- Stop Loss: XXX,XXX원 (-X%)

---

## 8. 리스크

1. **{Risk 1}**: {description}
2. **{Risk 2}**: {description}
3. **Sentiment Risk**: {SI-based risk}

---

## 9. 결론

**Rating**: {Buy/Hold/Sell}
**Confidence**: {High/Medium/Low}

### Cross-Check
- TI 기술적 신호: {Buy/Neutral/Sell}
- FI 재무 상태: {성장/안정/주의}
- SI 개인 센티먼트: {Bullish/Neutral/Bearish}
- MI 애널리스트 의견: {Buy/Neutral/Sell}
- 괴리: {Yes/No} - {interpretation}

### Monitoring Points
- [ ] {Point 1}
- [ ] {Point 2}

---
*이 분석은 투자 참고 자료이며, 투자 권유가 아닙니다.*
*Tags: #analysis #{sector} #{ticker}*
```

---

## Execution

When this command is invoked:

1. **Main context** verifies date and basic info (including company name)
2. **Main context** dispatches MI + SI + TI + FI workers in parallel
3. **Main context** waits for results and integrates
4. **Main context** applies sector knowledge for strategic analysis
5. **Main context** generates report and **PREPENDS** to `watchlist/stocks/{종목명}_{종목코드}.md`

```
Analyzing: {{ticker}}
Depth: {{depth}}

Starting parallel worker dispatch...
```
