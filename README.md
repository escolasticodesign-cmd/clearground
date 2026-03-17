# Clearground News

> *Facts, staged — no spin*

A news aggregator that treats every story as a living factual record. Every title is AI-generated from verified facts — never sourced from outlet headlines which carry framing, bias, or incomplete information.

## Project structure

```
/
├── index.html          # Homepage — story feed with expandable timelines
├── pipeline.html       # Pipeline reference with code documentation
├── title-engine.html   # Live AI title generator (requires Anthropic API key)
├── vercel.json         # Vercel routing config
└── pipeline/
    ├── README.md
    ├── requirements.txt
    ├── newsapi_ingest.py   # Stage 1: RSS + API ingest
    ├── fetch_fulltext.py   # Stage 2: Full-text fetch
    ├── cluster.py          # Stage 3: Event clustering
    ├── extract_facts.py    # Stage 4: AI fact extraction
    ├── title_engine.py     # Stage 5: AI title generation
    ├── spin_detect.py      # Stage 6: Spin detection
    └── pipeline.py         # Orchestrator
```

## Deploy to Vercel

1. Push this repo to GitHub
2. Import the repo in [vercel.com](https://vercel.com)
3. Deploy — no build step needed (static HTML)

## Live title engine

Open `title-engine.html` (or `/title-engine` on Vercel), enter your Anthropic API key, paste headlines from different outlets, and get a Clearground title + spin analysis in real time.

Your API key is stored only in session memory and sent directly to `api.anthropic.com`.

## Design system

| Token | Value |
|-------|-------|
| Primary teal | `#1D9E75` |
| Warning amber | `#EF9F27` |
| Headline font | DM Serif Display |
| Body font | DM Sans |

## Status

Current build is a **static prototype** with hardcoded story data. The Python pipeline in `/pipeline` is the planned backend.

**Built:** Story feed UI, staged timeline, spin flag components, confidence pip system, title formula visualizer, live AI title engine, full pipeline code reference.

**Next:** Live data pipeline, story detail page, mobile layout, source credibility scoring.

---

*Version 1.0 — March 2026*
