# Vulture Plugin Migration Design

## 개요

`stock-analyzer-advanced` 플러그인을 `stock-claude` 레포지토리의 `vulture` 플러그인으로 마이그레이션

## 디렉토리 구조

```
stock-claude/
├── .claude/
│   └── settings.json
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   └── vulture/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── README.md
│       ├── commands/
│       │   └── vulture-analyze.md
│       ├── agents/
│       │   ├── financial-intelligence.md
│       │   ├── market-intelligence.md
│       │   ├── sentiment-intelligence.md
│       │   └── technical-intelligence.md
│       └── utils/
│           ├── __init__.py
│           ├── data_fetcher.py
│           ├── financial_scraper.py
│           ├── indicators.py
│           ├── ti_analyzer.py
│           ├── web_scraper.py
│           └── requirements.txt
├── watchlist/
│   ├── stocks/
│   │   └── .gitkeep
│   └── daily_summaries/
│       └── .gitkeep
├── README.md
└── CLAUDE.md
```

## 설정 파일

### Root README.md

```markdown
# stock-claude

US/Korea 주식 분석 플러그인 모음

## 플러그인

- `vulture` - 종합 주식 분석
```

### Root CLAUDE.md

```markdown
# 개발 규칙

- 이모지 사용 금지
- 분석 결과 등 출력 콘텐츠는 한국어로 작성
- 커밋 메시지에 Claude 서명 포함하지 않음
```

### Root .claude/settings.json

```json
{}
```

### Root .claude-plugin/marketplace.json

```json
{
  "name": "stock-claude",
  "version": "1.0.0",
  "description": "US/Korea 주식 시장 분석 플러그인 모음",
  "author": {
    "name": "Michael"
  },
  "keywords": ["stock", "korea", "kospi", "kosdaq", "us", "finance"],
  "license": "MIT",
  "plugins": [
    "plugins/vulture"
  ]
}
```

### Plugin plugin.json

```json
{
  "name": "vulture",
  "version": "1.0.0",
  "description": "한국주식시장 종합 분석 - 시장, 센티먼트, 기술적, 재무 분석 에이전트 병렬 실행",
  "author": {
    "name": "Michael"
  },
  "keywords": ["stock", "korea", "analysis", "kospi", "kosdaq"],
  "license": "MIT"
}
```

## 마이그레이션 상세

### Command

| 소스 | 타겟 | 변경사항 |
|------|------|----------|
| `stock-analyze.md` | `vulture-analyze.md` | name 변경, ml-analyst 참조 제거, 경로 업데이트 |
| `stock-git-add-push.md` | (제외) | 마이그레이션하지 않음 |

### Agents

| 소스 | 타겟 | 변경사항 |
|------|------|----------|
| `financial-intelligence.md` | `financial-intelligence.md` | 그대로 복사 |
| `market-intelligence.md` | `market-intelligence.md` | 그대로 복사 |
| `sentiment-intelligence.md` | `sentiment-intelligence.md` | 그대로 복사 |
| `technical-intelligence.md` | `technical-intelligence.md` | 그대로 복사 |
| `financial-ml-analyst.md` | (제외) | 마이그레이션하지 않음 |

### Utils

**포함:**
- `__init__.py`
- `data_fetcher.py`
- `financial_scraper.py`
- `indicators.py`
- `ti_analyzer.py`
- `web_scraper.py`
- `requirements.txt`

**제외:**
- `deprecated.py`
- `test_utils.py`
- `test_ti_analyzer.py`
- `plan.md`
- `PRD.md`

### Watchlist

- 빈 디렉토리 구조만 생성
- 기존 분석 결과는 복사하지 않음
- `.gitkeep` 파일로 디렉토리 유지

## 소스 경로

- 템플릿: `/Users/michael/Desktop/git_repo/data-business-aie-claude-plugin`
- 소스 플러그인: `/Users/michael/Desktop/git_repo/public_agents/plugins/stock-analyzer-advanced`
- 타겟: `/Users/michael/Desktop/git_repo/stock-claude`
