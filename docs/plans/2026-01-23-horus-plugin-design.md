# Horus Plugin Design

> 호루스 - upvote 종목 심층분석 및 모니터링 시스템

## 변경 이력
- 2026-01-23: 초안 작성

---

## 1. 개요

### 목적
vulture 1차 분석 후 등급 분류된 종목 중 **upvote** 등급에 대해:
- 심층 분석 (재무, 증권사 보고서, 경영진 평가)
- 최신 정보 추적 (DART 공시, 텔레그램)

### 전체 흐름
```
[vulture-analyze]
      ↓
watchlist/stocks/삼성전자_005930.md  (버퍼)
      ↓
[수동 mv로 분류]
      ↓
classified/
├── upvote/삼성전자_005930/        <- 호루스 대상
│   ├── vulture_summary.md         <- mv한 원본
│   ├── horus_deep.md              <- 심층분석 (rewrite)
│   ├── horus_refresh.md           <- 최신정보 (prepend)
│   └── horus_refresh_index.json   <- 중복방지
├── neutral/                        <- 대기
└── graveyard/                      <- 끝
```

---

## 2. 등급 분류 체계

| 등급 | 설명 | 호루스 대상 |
|------|------|------------|
| **upvote** | 관심 종목, 추가 분석 가치 있음 | O |
| **neutral** | 지켜보는 중, 아직 확신 없음 | X |
| **graveyard** | 탈락, 관심 종료 | X |

### 분류 방법
- 수동 파일 이동 (`mv`)
- watchlist/stocks/ → classified/{등급}/

---

## 3. 아키텍처

### Agents (각각 단일 책임)
```
horus/agents/
├── fnguide-analyzer.md      <- 1. FnGuide 심층 재무
├── report-analyzer.md       <- 2. 증권사 보고서 + 경영진 평가
├── catalyst-tracker.md      <- 3. DART 촉매 추적
└── telegram-scanner.md      <- 4. 텔레그램 최신정보
```

### Commands (에이전트 조합)
```
horus/commands/
├── horus-deep.md            <- 1 + 2 병렬 호출
├── horus-refresh.md         <- 3 + 4 병렬 호출
└── horus-full.md            <- deep → refresh 순차
```

| 커맨드 | 실행 에이전트 | 용도 |
|--------|--------------|------|
| `/horus-deep {종목}` | fnguide + report | 심층 펀더멘털 분석 |
| `/horus-refresh {종목}` | catalyst + telegram | 최신 정보 업데이트 |
| `/horus-full {종목}` | deep → refresh | 전체 분석 |

---

## 4. 에이전트 상세

### 4.1 fnguide-analyzer (심층 재무)

**데이터 소스**: FnGuide (Playwright)

**수집 방식**:
- Playwright로 FnGuide 접속
- JS 동적 로딩 완료 대기
- 전체 데이터 파싱

**수집 항목**:
- 손익계산서 (연간 + 분기)
- 재무상태표 (자산/부채/자본)
- 현금흐름표
- 주요 비율 (ROE, ROA, 부채비율 등)
- 피어 비교 (동종업계)

---

### 4.2 report-analyzer (증권사 보고서 + 경영진 평가)

**데이터 소스**: 네이버 증권 리서치 탭

**수집 방식**:
- 네이버 증권 리서치 PDF 스크래핑
- PDF 다운로드 → chunking → 분석

**분석 항목**:
- 증권사 투자의견/목표가 요약
- 산업 전망 추출
- **경영진 평가 (버핏 스타일)**:
  - 자본 배분 능력: ROE 추이, 자사주 매입, 배당 정책, M&A 이력
  - 오너십: 경영진 지분율, 스톡옵션 vs 자기 돈 매수
  - 솔직함: IR 자료에서 실패/리스크 언급 여부, 가이던스 정확도

---

### 4.3 catalyst-tracker (DART 촉매)

**데이터 소스**: DART OpenAPI 또는 스크래핑

**수집 항목**:
- 주요 공시 (실적발표, 유상증자, 자사주, M&A 등)
- 대주주 지분 변동
- 임원 변경
- 이벤트 캘린더 (실적발표일, 주총, IR 일정)

---

### 4.4 telegram-scanner (텔레그램 최신정보)

**데이터 소스**: 텔레그램 MCP (기존 구현 활용)

**수집 대상**:
- 종목 관련 공개 채널 메시지
- 루머/뉴스 요약

**구체적 채널/설정**: 추후 결정

---

## 5. Output 명세

### 5.1 horus_deep.md
- **생성 주체**: /horus-deep
- **저장 방식**: Rewrite (요청 시 덮어쓰기)
- **내용**: 심층 재무 + 증권사 보고서 + 경영진 평가

### 5.2 horus_refresh.md
- **생성 주체**: /horus-refresh
- **저장 방식**: Prepend (최신이 위로)
- **내용**: 촉매 공시 + 텔레그램 최신정보
- **타임스탬프**: 각 refresh 마다 날짜/시간 포함

### 5.3 horus_refresh_index.json
- **목적**: 중복 방지
- **구조**:
```json
{
  "dart": ["공시ID1", "공시ID2", ...],
  "telegram": ["msg_id_1", "msg_id_2", ...],
  "last_refresh": "2026-01-23T14:30:00"
}
```
- **동작**: refresh 시 index 체크 → 새 항목만 추가

---

## 6. 폴더 구조 예시

```
classified/
└── upvote/
    └── 삼성전자_005930/
        ├── vulture_summary.md           <- 1차 분석 (vulture)
        ├── horus_deep.md                <- 심층분석
        ├── horus_refresh.md             <- 최신정보 (누적)
        └── horus_refresh_index.json     <- 중복방지 인덱스
```

---

## 7. 향후 확장 (미정)

- [ ] 정기 자동 실행 (upvote 폴더 daily refresh)
- [ ] 중요 촉매 감지 시 알림 (텔레그램 봇)
- [ ] neutral → upvote 자동 승격 조건

---

## 8. 구현 우선순위

1. **fnguide-analyzer** - 핵심 재무 데이터
2. **catalyst-tracker** - DART 공시
3. **report-analyzer** - 증권사 보고서 + 경영진
4. **telegram-scanner** - 텔레그램 연동

커맨드는 에이전트 완성 후 조합.

---

*이 문서는 구현 진행에 따라 업데이트됩니다.*
