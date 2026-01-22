---
name: doc-analyze
description: Analyze industry trend PDFs to discover and profile related Korean stocks
arguments:
  - name: file_path
    description: Path to PDF file (analyst report, conference material)
    required: true
---

# Doc Analyze Command

Processes industry trend documents (PDF) to discover related Korean stocks and generate brief profiles.

## Architecture

```
/doc-analyze <file_path>
    |
    +-> STEP 0: Validate file exists, get metadata
    |
    +-> STEP 1: Process PDF (chunking if large)
    |   +-> Bash: python ${CLAUDE_PLUGIN_ROOT}/scripts/pdf_processor.py <file_path>
    |   +-> Output: chunks in /tmp/doc-analyzer/{doc-name}/
    |
    +-> STEP 2: Analyze chunks, discover stocks
    |   +-> Read each chunk sequentially
    |   +-> Summarize key trends and insights
    |   +-> LLM inference: "What Korean stocks relate to these trends?"
    |   +-> Save discovered stocks to queue.json
    |
    +-> STEP 3: Profile each stock (via stock-profiler agent)
    |   +-> Read queue.json for pending stocks
    |   +-> For each stock:
    |       +-> Task(doc-analyzer:stock-profiler)
    |       +-> Update queue.json (mark completed)
    |
    +-> STEP 4: Generate final report
        +-> reports/{doc-name}/summary.md
        +-> reports/{doc-name}/stocks/{company}_{ticker}.md
```

## Execution Flow

### STEP 0: Validate and Setup

```python
# 1. Check file exists
file_path = "{{file_path}}"
Bash(f"ls -lh {file_path}")  # Verify exists, check size

# 2. Extract doc name from filename
doc_name = file_path.split("/")[-1].replace(".pdf", "")

# 3. Create temp directory
TEMP_DIR = f"/tmp/doc-analyzer/{doc_name}"
Bash(f"mkdir -p {TEMP_DIR}/chunks")

# 4. Create output directory
OUTPUT_DIR = f"reports/{doc_name}"
Bash(f"mkdir -p {OUTPUT_DIR}/stocks")
```

### STEP 1: Process PDF

```python
# Run PDF processor script
Bash(f"""
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pdf_processor.py \\
    --input "{file_path}" \\
    --output "{TEMP_DIR}" \\
    --chunk-size 10
""")

# Script outputs:
# - {TEMP_DIR}/chunks/chunk_001.txt, chunk_002.txt, ...
# - {TEMP_DIR}/metadata.json (page_count, chunk_count, toc)
```

### STEP 2: Analyze Chunks and Discover Stocks

```python
# 1. Read metadata
Read(f"{TEMP_DIR}/metadata.json")

# 2. Process each chunk
for chunk_file in sorted(glob(f"{TEMP_DIR}/chunks/*.txt")):
    content = Read(chunk_file)

    # Summarize chunk content
    # Identify key trends, technologies, market drivers

# 3. After all chunks processed, infer related stocks
# Ask: "Based on these industry trends, which Korean stocks would benefit?"
# Consider:
#   - Direct beneficiaries (companies in the sector)
#   - Supply chain (suppliers, customers)
#   - Indirect beneficiaries (infrastructure, services)

# 4. Categorize stocks by theme (based on document trends)
# Group stocks by their primary relevance theme:
#   - Use short, descriptive theme names (e.g., "AI_Semiconductor", "Energy", "Biotech")
#   - Use underscores instead of spaces for folder compatibility
#   - Each stock should have exactly one theme assignment

# 5. Save discovered stocks to queue WITH theme
queue = {
    "doc_name": doc_name,
    "trends": ["Trend 1", "Trend 2", ...],  # Key trends from document
    "discovered": [
        {"name": "SK하이닉스", "ticker": "000660", "relevance": "HBM AI 반도체", "theme": "AI_Semiconductor"},
        {"name": "한화솔루션", "ticker": "009830", "relevance": "태양광, 배터리", "theme": "Energy"},
        ...
    ],
    "completed": [],
    "current": null
}
Write(f"{TEMP_DIR}/queue.json", json.dumps(queue))
```

### STEP 3: Profile Each Stock (Parallel Batch Processing)

**CRITICAL: Process in parallel batches, then verify outputs to update queue.**

```python
BATCH_SIZE = 3  # Limit concurrent agents to avoid resource exhaustion

# 1. Read current queue
queue = json.loads(Read(f"{TEMP_DIR}/queue.json"))

# 2. Filter pending stocks (not yet completed)
pending = [s for s in queue["discovered"] if s["name"] not in queue["completed"]]

# 3. Process in batches
for i in range(0, len(pending), BATCH_SIZE):
    batch = pending[i:i+BATCH_SIZE]

    # Update queue: mark batch as in_progress
    queue["current"] = [s["name"] for s in batch]
    Write(f"{TEMP_DIR}/queue.json", json.dumps(queue))

    # 4. Launch ALL agents in this batch IN PARALLEL (single message, multiple Task calls)
    # IMPORTANT: Make all Task() calls in ONE response to run them in parallel
    for stock_info in batch:
        Task(
            subagent_type="doc-analyzer:stock-profiler",
            prompt=f"""
            Generate brief profile for: {stock_info["name"]}

            Context from document:
            - Document: {doc_name}
            - Key trends: [summarized trends from STEP 2]
            - Relevance: {stock_info["relevance"]}
            - Theme: {stock_info["theme"]}

            Output directory: {OUTPUT_DIR}/stocks/
            Theme folder: {stock_info["theme"]}

            IMPORTANT: Create theme folder if it doesn't exist, then save profile there.
            File naming: {stock_info["name"]}_{stock_info["ticker"]}.md
            """,
            description=f"Profile: {stock_info['name']}"
        )

    # 5. AFTER batch completes, verify which profiles were created
    # Check file existence to confirm success (more reliable than Task status)
    for stock_info in batch:
        expected_file = f"{OUTPUT_DIR}/stocks/{stock_info['theme']}/{stock_info['name']}_{stock_info['ticker']}.md"
        if Glob(expected_file):  # File exists
            queue["completed"].append(stock_info["name"])

    # 6. Update queue after batch
    queue["current"] = null
    Write(f"{TEMP_DIR}/queue.json", json.dumps(queue))

    # Log progress
    print(f"Batch {i//BATCH_SIZE + 1} complete: {len(queue['completed'])}/{len(queue['discovered'])} stocks profiled")
```

**Resume capability**: Re-running the command will skip already-completed stocks (checked via queue.json).

### STEP 4: Generate Final Report

```python
# 1. Create summary report
summary = f"""
# {doc_name} 분석 리포트

**분석일**: {current_date}
**원본 문서**: {file_path}

---

## 문서 요약

[Document summary from STEP 2]

## 핵심 트렌드

1. [Trend 1]
2. [Trend 2]
3. [Trend 3]

---

## 관련 종목 ({len(discovered)} 종목)

### AI_Semiconductor
| 종목명 | 티커 | 관련성 | 프로필 |
|--------|------|--------|--------|
| SK하이닉스 | 000660 | HBM AI 반도체 | [링크](stocks/AI_Semiconductor/SK하이닉스_000660.md) |
| 삼성전자 | 005930 | AI 반도체, HBM | [링크](stocks/AI_Semiconductor/삼성전자_005930.md) |

### Energy
| 종목명 | 티커 | 관련성 | 프로필 |
|--------|------|--------|--------|
| 한화솔루션 | 009830 | 태양광, 배터리 | [링크](stocks/Energy/한화솔루션_009830.md) |

... (group stocks by theme)

---

## 투자 아이디어

[Investment ideas based on document trends + stock analysis]

---

*이 분석은 투자 참고 자료이며, 투자 권유가 아닙니다.*
"""

Write(f"{OUTPUT_DIR}/summary.md", summary)
```

## Stock Discovery Guidelines

When inferring related Korean stocks, consider:

### Direct Exposure
- Companies directly mentioned in the document
- Korean competitors of mentioned global companies
- Korean market leaders in the discussed sector

### Supply Chain
- Upstream: Raw material suppliers, component makers
- Downstream: Customers, distributors, integrators

### Indirect Beneficiaries
- Infrastructure providers (data centers, logistics)
- Service companies (consulting, maintenance)
- Enablers (equipment, tools, software)

### Risk Exposure
- Companies that may be negatively impacted
- Note these separately with "Risk" tag

## Output Format

### Stock Profile (Brief)

Each stock profile in `reports/{doc-name}/stocks/` should contain:

```markdown
# {회사명} ({티커})

**문서 관련성**: [1-2 sentences on why this stock relates to the document]

## 기업 개요
[Brief company description from MI]

## 핵심 재무 (FI)
| 항목 | 값 | 출처 |
|------|-----|------|
| 시가총액 | X.X조원 | |
| 매출액 (최근) | X,XXX억원 | FnGuide |
| 영업이익 | X,XXX억원 | FnGuide |
| 매출성장률 (YoY) | +XX% | |

## 최근 동향 (MI)
- [Recent news 1]
- [Recent news 2]

## 투자 포인트
- **Bull**: [Why this stock benefits from the trend]
- **Bear**: [Risks or concerns]

---
*Source: {doc_name}*
```

## Error Handling

1. **PDF processing fails**: Report error, suggest alternative format
2. **No stocks discovered**: Report "no direct Korean stock exposure found"
3. **Stock profiler fails**: Log to queue.json, continue with next stock
4. **Resume capability**: Re-run command to continue from queue.json

## Execution

When this command is invoked:

1. Validate PDF file exists and is readable
2. Run PDF processor script for chunking
3. Analyze chunks sequentially, build trend summary
4. Discover related Korean stocks via LLM inference
5. Profile each stock using stock-profiler agent
6. Generate final summary report with stock index

```
Analyzing: {{file_path}}
Starting document analysis workflow...
```
