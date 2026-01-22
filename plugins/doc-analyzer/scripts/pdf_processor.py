#!/usr/bin/env python3
"""
PDF Processor for Doc Analyzer Plugin

Processes PDF documents with hybrid chunking strategy:
1. Try section-based chunking (using TOC/headers)
2. Fall back to fixed-size chunking if structure unclear

Usage:
    python pdf_processor.py --input report.pdf --output /tmp/doc-analyzer/report/

Dependencies:
    pip install pdfplumber
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)


def get_file_info(pdf_path: str) -> dict:
    """Get basic file information."""
    path = Path(pdf_path)
    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    return {
        "file_name": path.name,
        "file_path": str(path.absolute()),
        "size_bytes": size_bytes,
        "size_mb": round(size_mb, 2),
        "doc_name": path.stem
    }


def extract_toc(pdf) -> list:
    """
    Try to extract table of contents from PDF.
    Returns list of {title, page} dicts.
    """
    toc = []

    # Method 1: Check PDF outline/bookmarks
    try:
        if hasattr(pdf, 'metadata') and pdf.metadata:
            # Some PDFs have outline in metadata
            pass
    except:
        pass

    # Method 2: Look for TOC-like patterns in first few pages
    toc_patterns = [
        r'^(목차|contents|table of contents)$',
        r'^\d+\.\s+.+\s+\d+$',  # "1. Introduction 5"
        r'^[IVX]+\.\s+.+\s+\d+$',  # "I. Overview 3"
    ]

    for i, page in enumerate(pdf.pages[:5]):  # Check first 5 pages
        text = page.extract_text() or ""
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            # Look for section headers with page numbers
            match = re.match(r'^(\d+\.?\s+.+?)\s+\.{2,}\s*(\d+)$', line)
            if match:
                toc.append({
                    "title": match.group(1).strip(),
                    "page": int(match.group(2))
                })

    return toc


def detect_section_headers(text: str) -> list:
    """
    Detect section headers in text.
    Returns list of {title, position} dicts.
    """
    headers = []
    lines = text.split('\n')

    patterns = [
        # Korean section patterns
        r'^(제?\s*\d+[장절]\.?\s*.+)$',
        r'^(\d+\.\s+[가-힣].+)$',
        # English section patterns
        r'^(\d+\.\s+[A-Z][A-Za-z\s]+)$',
        r'^(Chapter\s+\d+[:\s].+)$',
        r'^(Section\s+\d+[:\s].+)$',
        # Roman numerals
        r'^([IVX]+\.\s+.+)$',
    ]

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        for pattern in patterns:
            if re.match(pattern, line):
                headers.append({
                    "title": line,
                    "line_number": i
                })
                break

    return headers


def chunk_by_sections(pdf, toc: list, output_dir: str) -> list:
    """
    Chunk PDF by sections based on TOC.
    Returns list of chunk metadata.
    """
    chunks = []
    chunk_dir = os.path.join(output_dir, "chunks")
    os.makedirs(chunk_dir, exist_ok=True)

    if not toc:
        return []

    # Add end marker
    toc_with_end = toc + [{"title": "END", "page": len(pdf.pages) + 1}]

    for i in range(len(toc)):
        start_page = toc_with_end[i]["page"] - 1  # 0-indexed
        end_page = toc_with_end[i + 1]["page"] - 1

        # Clamp to valid range
        start_page = max(0, min(start_page, len(pdf.pages) - 1))
        end_page = max(start_page + 1, min(end_page, len(pdf.pages)))

        # Extract text from section pages
        section_text = ""
        for page_num in range(start_page, end_page):
            if page_num < len(pdf.pages):
                page_text = pdf.pages[page_num].extract_text() or ""
                section_text += f"\n--- Page {page_num + 1} ---\n{page_text}"

        if section_text.strip():
            chunk_file = os.path.join(chunk_dir, f"chunk_{i+1:03d}.txt")
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(f"# Section: {toc[i]['title']}\n\n{section_text}")

            chunks.append({
                "chunk_id": i + 1,
                "file": chunk_file,
                "section_title": toc[i]["title"],
                "start_page": start_page + 1,
                "end_page": end_page,
                "char_count": len(section_text)
            })

    return chunks


def chunk_by_pages(pdf, chunk_size: int, output_dir: str) -> list:
    """
    Chunk PDF by fixed number of pages.
    Returns list of chunk metadata.
    """
    chunks = []
    chunk_dir = os.path.join(output_dir, "chunks")
    os.makedirs(chunk_dir, exist_ok=True)

    total_pages = len(pdf.pages)
    chunk_num = 0

    for start_page in range(0, total_pages, chunk_size):
        chunk_num += 1
        end_page = min(start_page + chunk_size, total_pages)

        # Extract text from chunk pages
        chunk_text = ""
        for page_num in range(start_page, end_page):
            page_text = pdf.pages[page_num].extract_text() or ""
            chunk_text += f"\n--- Page {page_num + 1} ---\n{page_text}"

        if chunk_text.strip():
            chunk_file = os.path.join(chunk_dir, f"chunk_{chunk_num:03d}.txt")
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk_text)

            chunks.append({
                "chunk_id": chunk_num,
                "file": chunk_file,
                "section_title": f"Pages {start_page + 1}-{end_page}",
                "start_page": start_page + 1,
                "end_page": end_page,
                "char_count": len(chunk_text)
            })

    return chunks


def process_pdf(input_path: str, output_dir: str, chunk_size: int = 10) -> dict:
    """
    Main PDF processing function.
    Uses hybrid chunking: section-based if TOC available, else fixed-size.
    """
    # Get file info
    file_info = get_file_info(input_path)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Open PDF
    with pdfplumber.open(input_path) as pdf:
        total_pages = len(pdf.pages)

        # Try to extract TOC
        toc = extract_toc(pdf)

        # Decide chunking strategy
        if toc and len(toc) >= 3:
            # Use section-based chunking
            chunking_method = "section"
            chunks = chunk_by_sections(pdf, toc, output_dir)
        else:
            # Fall back to fixed-size chunking
            chunking_method = "fixed"
            toc = []
            chunks = chunk_by_pages(pdf, chunk_size, output_dir)

    # Build metadata
    metadata = {
        "doc_name": file_info["doc_name"],
        "file_name": file_info["file_name"],
        "file_path": file_info["file_path"],
        "size_mb": file_info["size_mb"],
        "total_pages": total_pages,
        "chunking_method": chunking_method,
        "chunk_size": chunk_size if chunking_method == "fixed" else None,
        "chunk_count": len(chunks),
        "toc": toc,
        "chunks": chunks
    }

    # Save metadata
    metadata_file = os.path.join(output_dir, "metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # Initialize queue file
    queue = {
        "doc_name": file_info["doc_name"],
        "discovered": [],
        "completed": [],
        "current": None
    }
    queue_file = os.path.join(output_dir, "queue.json")
    with open(queue_file, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

    return metadata


def main():
    parser = argparse.ArgumentParser(
        description="Process PDF for Doc Analyzer plugin"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input PDF file path"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output directory for chunks and metadata"
    )
    parser.add_argument(
        "--chunk-size", "-c",
        type=int,
        default=10,
        help="Pages per chunk for fixed-size chunking (default: 10)"
    )

    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    if not args.input.lower().endswith('.pdf'):
        print(f"ERROR: Input file must be a PDF: {args.input}")
        sys.exit(1)

    # Process PDF
    print(f"Processing: {args.input}")
    metadata = process_pdf(args.input, args.output, args.chunk_size)

    # Print summary
    print(f"\nProcessing complete!")
    print(f"  Document: {metadata['doc_name']}")
    print(f"  Pages: {metadata['total_pages']}")
    print(f"  Size: {metadata['size_mb']} MB")
    print(f"  Chunking: {metadata['chunking_method']}")
    print(f"  Chunks: {metadata['chunk_count']}")
    print(f"  Output: {args.output}")

    if metadata['toc']:
        print(f"\nTable of Contents detected:")
        for item in metadata['toc'][:5]:
            print(f"  - {item['title']} (p.{item['page']})")
        if len(metadata['toc']) > 5:
            print(f"  ... and {len(metadata['toc']) - 5} more sections")


if __name__ == "__main__":
    main()
