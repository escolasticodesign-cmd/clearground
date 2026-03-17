"""
Stage 6 — Spin detection
Compare outlet headlines against confirmed facts and classify spin.
"""

import anthropic
import json

client = anthropic.Anthropic()

SPIN_SYSTEM_PROMPT = """You are the Clearground spin detection system.

Your job: compare an outlet's headline against confirmed facts and classify spin.

Spin classifications:
- Loaded: language chosen to provoke emotional response (e.g. "raging inferno", "refuses to cut")
- Framing: neutral facts wrapped in narrative (e.g. "under pressure", "bowing to demands")
- Vague: headline withholds specific facts that were available at time of publication
- OK: headline is broadly factual and specific, no spin detected

Return ONLY valid JSON:
{
  "classification": "Loaded|Framing|Vague|OK",
  "spin_present": true|false,
  "description": "one sentence explaining what the spin is (or 'No spin detected')",
  "specific_language": "the exact phrase in the headline that carries the spin, or null"
}"""


def detect_spin(outlet_headline: str, outlet_name: str, confirmed_facts: list) -> dict:
    """Classify spin in a single outlet headline vs the confirmed facts."""
    facts_text = "\n".join(f"- {f['fact']} (source: {f['source']})" for f in confirmed_facts)
    user_msg = f"""Outlet: {outlet_name}
Headline: "{outlet_headline}"

Confirmed facts about this event:
{facts_text}

Classify the spin in this headline."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SPIN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    try:
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(raw)
        result["outlet"] = outlet_name
        result["original_headline"] = outlet_headline
        return result
    except Exception:
        return {"classification": "OK", "spin_present": False, "description": "Parse error"}


def detect_spin_for_cluster(cluster_articles: list, confirmed_facts: list) -> list:
    """Run spin detection on all article headlines in a cluster."""
    results = []
    for article in cluster_articles:
        result = detect_spin(article.title, article.source, confirmed_facts)
        if result["spin_present"]:
            results.append(result)
    return results
