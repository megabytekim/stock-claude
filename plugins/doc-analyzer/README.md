# Doc Analyzer

Industry document analyzer for Korean stock discovery.

## Overview

Processes large industry trend PDFs (analyst reports, conference materials) to:
1. Extract key insights and trends
2. Discover related Korean stocks via LLM inference
3. Generate brief profiles for each stock using vulture sub-agents

## Usage

```bash
/doc-analyze /path/to/report.pdf
```

## Architecture

```
/doc-analyze report.pdf
    |
    +-> pdf_processor.py (chunk large PDFs)
    |
    +-> Main context reads chunks
    |   - Summarizes trends
    |   - Discovers related Korean stocks
    |   - Saves queue to file (prevents forgetting)
    |
    +-> For each stock (via stock-profiler agent):
        +-> vulture:financial-intelligence
        +-> vulture:market-intelligence
        +-> Generate brief profile with relevance
    |
    +-> Final output:
        reports/{doc-name}/
        ├── summary.md        # Document analysis + stock index
        └── stocks/
            ├── {company}_{ticker}.md
            └── ...
```

## Dependencies

- Python 3.8+
- pdfplumber (`pip install pdfplumber`)

## Temp Files

Chunks and queue stored in `/tmp/doc-analyzer/{doc-name}/`
