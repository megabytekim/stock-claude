# Vulture - 한국주식시장 종합 분석

대화형 AI 기반 투자 분석 시스템

## 소개

Vulture는 한국주식시장을 위한 종합 분석 시스템입니다. 사용자와의 자연스러운 대화를 통해 실시간으로 시장을 분석하고, 맞춤형 투자 전략을 제시합니다.

## 데이터 정확성 보장

주식 정보는 실시간성이 생명입니다. 모든 에이전트는 다음 순서를 따릅니다:

### STEP 0: 오늘 날짜 확인 (최우선)
- WebFetch 또는 WebSearch로 현재 날짜 먼저 확인
- 모든 검색어에 연도와 날짜 명시

### 데이터 수집 우선순위

**한국 주식:**
1. Playwright - FnGuide (재무제표, PER/PBR)
2. WebSearch (뉴스, 날짜 필수 포함)
3. Naver Finance (실시간 가격, 공시)

**미국 주식:**
1. yfinance MCP (최우선 - 가장 정확)
2. WebFetch - Yahoo Finance (MCP 없을 시)
3. WebSearch (뉴스, 날짜 필수 포함)
4. Playwright (차트/시각 확인)

### 절대 금지
- 날짜 확인 없이 분석 시작
- "today", "latest" 같은 모호한 검색어
- 추측/기억/오래된 데이터 사용
- 출처와 날짜 없는 데이터 제공

## 시작하기

```bash
/vulture-analyze 삼성전자
/vulture-analyze NVDA
```

## 에이전트 구성

| 에이전트 | 역할 |
|---------|------|
| Market Intelligence | 시장 정보 수집, 뉴스, 기업 개요 |
| Sentiment Intelligence | 커뮤니티 센티먼트 분석 |
| Technical Intelligence | 기술적 지표, 가격, 밸류에이션 |
| Financial Intelligence | 재무제표 분석 |

## 주요 기능

### 1. 즉문즉답 시장 분석
- 시장 분위기 파악
- 주목할 종목 선별
- 미국 시장 영향 분석

### 2. 심층 종목 분석
- 재무제표 분석
- 경쟁사 대비 분석
- 적정 주가 산출

### 3. 리스크 진단
- 포트폴리오 진단
- 헤징 방법 추천
- 손절 타이밍 조언

## 알려진 이슈

### pykrx KRX 데이터 접근 불가 (2025-12-27~)

KRX가 로그인 필수 정책으로 변경되어 일부 함수가 제한됩니다.

**작동하는 함수:**
- get_market_ohlcv_by_date() - Naver 소스
- get_market_ticker_name() - Naver 소스
- get_market_ticker_list() - Naver fallback
- get_market_fundamental() - Naver fallback
- get_market_cap() - Naver fallback

**대안 없는 데이터:**
- 투자자별 매매동향 (기관/외국인/개인)
- 공매도 현황

## 면책조항

투자 권유가 아닙니다. 모든 투자 결정은 본인 책임입니다.
