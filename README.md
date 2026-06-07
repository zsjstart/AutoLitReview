# LLM Papers Collector & Processor

Research idea → OpenAlex search → LLM analysis → Automatically grouped Excel report

This tool automates literature discovery and organization for a research topic. Given a research idea, it:

1. Generates literature-search concepts using an LLM
2. Searches OpenAlex for relevant papers
3. Extracts paper summaries and target objects
4. Filters out off-topic papers
5. Discovers thematic categories automatically
6. Produces a structured Excel report

---

## Features

- Multi-concept literature search
- OpenAlex integration
- DOI-based deduplication
- Automatic abstract reconstruction
- LLM-powered paper summarization
- LLM-powered relevance filtering
- Automatic taxonomy discovery
- Excel export with categorized papers
- Supports local and cloud-hosted LLMs

---

## Installation

```bash
pip install openai requests openpyxl
```

## Environment

```bash
export OPENALEX_API_KEY=YOUR_KEY
```

## Quick Start

```bash
python llm_papers_collector_and_processor.py \
    "LLM-powered phishing attacks"
```

## Workflow

```text
Research Idea
      │
      ▼
Concept Extraction
      │
      ▼
OpenAlex Search
      │
      ▼
Paper Collection & Deduplication
      │
      ▼
Phase 1: Local Analysis
(summary + target object)
      │
      ▼
Relevance Filtering
      │
      ▼
Phase 2: Global Analysis
(category discovery + assignment)
      │
      ▼
Excel Report
```

## Output

### Papers Sheet

- Title
- Year
- Summary
- Target Object
- Category
- Venue
- Venue Quality
- Source

### Categories Sheet

- Category Name
- Description

## Supported Providers

- vLLM (GPT-OSS)
- OpenAI
- Gemini
- Claude
