# Clearground — Data Pipeline

Python pipeline scripts for the Clearground News backend. These scripts implement the 6-stage data pipeline documented in `pipeline.html`.

## Stages

| # | Script | What it does |
|---|--------|-------------|
| 1 | `newsapi_ingest.py` | Pull headlines from RSS feeds and NewsData.io |
| 2 | `fetch_fulltext.py` | Retrieve full article body text |
| 3 | `cluster.py` | Group articles by real-world event (TF-IDF) |
| 4 | `extract_facts.py` | AI fact extraction via Claude API |
| 5 | `title_engine.py` | AI title generation via Claude API |
| 6 | `spin_detect.py` | AI spin classification per outlet |
| — | `pipeline.py` | Orchestrator — runs all 6 stages |

## Setup

```bash
pip install requests feedparser python-dateutil newspaper3k lxml[html_clean] scikit-learn numpy anthropic
```

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
python pipeline.py
```

Output: `stories.json` — array of story records ready for the frontend.

## Story record format

```json
{
  "cluster_id": "abc12345",
  "title": "Federal Reserve held federal funds rate at 4.25–4.50% for third consecutive meeting",
  "formula_breakdown": {
    "who_where": "Federal Reserve",
    "action": "held rate",
    "number": "4.25–4.50%",
    "status": "3rd consecutive hold"
  },
  "confidence_score": 4,
  "confirmed_facts": [...],
  "conflicted_facts": [...],
  "unknowns": [...],
  "spin_flags": [...],
  "source_articles": [...],
  "last_updated": "2026-03-17T11:45:00+00:00"
}
```
