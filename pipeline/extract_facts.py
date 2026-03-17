"""
Stage 4 — Fact extraction
Send article cluster to Claude, extract confirmed facts with attribution.
"""

import anthropic
import json

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

FACT_EXTRACTION_PROMPT = """You are a fact extraction system for Clearground News.

Your job: read multiple news articles about the same event and extract ONLY confirmed factual claims.

Rules:
- Facts only. No opinion, analysis, framing, or speculation.
- Every fact must cite which source confirmed it.
- If sources conflict on a fact, flag it as CONFLICTED with both versions.
- If something is not yet known, list it explicitly under unknowns.
- Numbers are sacred — include every specific quantifiable fact with its exact value.

Return ONLY valid JSON in this exact format:
{
  "confirmed_facts": [
    {
      "fact": "string — the factual claim in plain language",
      "source": "string — publication or official body name",
      "confidence": "high|medium|low",
      "timestamp": "string or null — when this fact was confirmed"
    }
  ],
  "conflicted_facts": [
    {
      "topic": "string",
      "versions": [{"claim": "...", "source": "..."}, ...]
    }
  ],
  "unknowns": ["string — things not yet confirmed"],
  "confidence_score": 1
}"""


def extract_facts_for_cluster(cluster_articles: list) -> dict:
    """Run Claude fact extraction on a cluster of articles."""
    articles_text = "\n\n---\n\n".join(
        f"SOURCE: {a.source}\nTITLE: {a.title}\n\n{a.full_text[:3000]}"
        for a in cluster_articles
    )
    user_message = f"Extract facts from these {len(cluster_articles)} articles about the same event:\n\n{articles_text}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=FACT_EXTRACTION_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    try:
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}\nRaw: {raw[:200]}")
        return {"confirmed_facts": [], "unknowns": [], "confidence_score": 1}
