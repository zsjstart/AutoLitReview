# AutoLitReview

**Turn a research idea into a structured literature review using OpenAlex and LLMs.**

AutoLitReview is an AI-powered literature discovery pipeline that automatically searches, filters, analyzes, and organizes academic papers from a simple research idea description.

Instead of manually crafting search queries, screening dozens of papers, and organizing findings into spreadsheets, AutoLitReview uses large language models to automate much of the workflow.

The result is a categorized Excel report containing relevant papers, summaries, extracted target objects, venue information, and research categories.

This tool analyzes OpenAlex abstracts instead of full paper texts. Because abstracts are typically only a few hundred tokens long — versus several thousand for a full paper — the approach substantially reduces token consumption and inference costs. In addition, papers are analyzed in small batches, which reduces the number of API calls and keeps each response within the model's output limit.

---

## Features

- 🔍 Generate literature-search concepts from a research idea
- 📚 Search OpenAlex across multiple concepts
- 🧹 Deduplicate papers automatically
- 🤖 Extract paper summaries using LLMs
- 🎯 Identify the target object of each paper
- 🚦 Filter out irrelevant search results
- 📂 Automatically categorize papers into research themes
- 📊 Export results to a structured Excel workbook
- 🔌 Support local and cloud-hosted LLMs

---

## Workflow

```text
Research Idea
(typically a short research problem statement)
      │
      ▼
Concept Generation
(generate literature-search concepts)
      │
      ▼
OpenAlex Retrieval
(retrieve candidate papers)
      │
      ▼
Deduplication
(remove duplicate papers)
      │
      ▼
Paper Analysis
(summary + target object extraction)
      │
      ▼
Relevance Filtering
(remove unrelated papers)
      │
      ▼
Theme Categorization
(generate research themes and assign papers)
      │
      ▼
Excel Report
(papers, summaries, categories, and sources)
```
---

## Installation

### 1. Install Dependencies

```bash
pip install openai requests openpyxl
```

### 2. Configure OpenAlex

```bash
export OPENALEX_API_KEY=YOUR_KEY
```

OpenAlex API keys are free and available from:

https://openalex.org/settings/api

---

## Supported LLM Backends

| Backend | Example Model |
|----------|--------------|
| Local LLM | GPT-OSS-120B |
| OpenAI API | GPT-4o |
| Google Gemini API | Gemini Flash |
| Anthropic API | Claude Sonnet |

The project uses OpenAI-compatible APIs, making it easy to connect local or hosted models.

---

## Quick Start

### Local GPT-OSS via vLLM

```bash
python AutoLitReview.py \
    "LLM-powered phishing attacks" \
    --provider vllm
```

### Example: Cybersecurity Literature Search

```bash
python AutoLitReview.py \
    "Automated OSINT-based profiling for targeted phishing" \
    --domain cybersecurity \
    --concepts 4 \
    --per-concept 10 \
    --year-from 2024 \
    --provider vllm
```

### Providing Your Own Search Concepts

By default, AutoLitReview generates literature-search concepts from your
research idea automatically. If you'd rather supply your own, use the
`--manual-concepts` flag:

```bash
python AutoLitReview.py "Automated OSINT-based profiling for targeted phishing" \
    --manual-concepts "footprinting" "OSINT" "attack surface discovery" "spear phishing"
```


---

## Example Output

```text
Concepts:
['LLM phishing',
 'Automated OSINT',
 'Profile inference',
 'Targeted social engineering']

Collected 39 unique papers

Phase 1 (per-paper analysis) done

Relevance gate:
10 papers kept as on-topic

Phase 2 (grouping) done
4 categories discovered

Done -> papers_grouped.xlsx
```

---

## Output Structure

### Papers Sheet

| Column | Description |
|----------|-------------|
| Title | Paper title |
| Year | Publication year |
| Summary | One-sentence summary |
| Target Object | What the method acts upon |
| Category | Automatically assigned category |
| Venue | Publication venue |
| Venue Quality | Core / DOAJ / Other |
| Source | DOI or source URL |


## Command Line Options

| Argument | Description |
|-----------|-------------|
| `--concepts` | Number of concepts to generate |
| `--per-concept` | Papers retrieved per concept |
| `--year-from` | Earliest publication year |
| `--year-to` | Latest publication year |
| `--domain` | Restrict search to an OpenAlex field |
| `--core-only` | Keep only papers from core venues |
| `--provider` | LLM backend (`vllm`, `openai`, `gemini`, `claude`) |
| `--model` | Override default model |
| `--manual-concepts` | Use custom search concepts |
| `--out` | Output Excel filename |

---

## Supported Domains

```text
cybersecurity
computer science
engineering
materials science
mathematics
physics
biology
chemistry
medicine
psychology
social sciences
economics
neuroscience
environmental science
```

---

## Why AutoLitReview?

Traditional literature reviews require:

- Designing search queries
- Running multiple database searches
- Screening papers manually
- Extracting key information
- Grouping papers into themes

AutoLitReview automates much of this process, allowing researchers to move from a research idea to an organized literature overview in minutes.

---

## Typical Use Cases

- Literature reviews
- Survey paper preparation
- PhD topic exploration
- Research trend discovery
- Rapid state-of-the-art analysis

---

## Limitations

- Results depend on the coverage, metadata quality, and search relevance of OpenAlex.
- LLM quality affects concept generation, paper summarization, relevance filtering, and thematic categorization.
- Commercial LLM APIs may incur token costs, but appropriately configuring `--concepts` and `--per-concept` can help control token usage and reduce expenses.
  
---

## Citation

If you use AutoLitReview in academic work, please cite:

- OpenAlex
- The LLM provider used for analysis
- This repository

---

## License

MIT License
