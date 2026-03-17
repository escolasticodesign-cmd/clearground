"""
Stage 5 — Title engine
Generate a Clearground title from confirmed facts using the 5-rule formula.
"""

import anthropic
import json

client = anthropic.Anthropic()

TITLE_SYSTEM_PROMPT = """You are the Clearground title engine.

Your job: generate a factual headline from confirmed facts using the Clearground formula.

Formula: [Who/Where] + [neutral past-tense verb] + [specific number] + [status/signal]

5 rules:
1. Numbers over adjectives: "5,100 acres" not "devastating fire"
2. Actions not narratives: "Fed held rate" not "Fed refuses to cut"
3. Unknown = stated: "cause under investigation" is a valid title element
4. Highest-confidence fact leads: anchor on the most verified specific fact
5. Implications go in the body, not the title

Return ONLY valid JSON:
{
  "title": "the generated title string",
  "formula_breakdown": {
    "who_where": "...",
    "action": "...",
    "number": "...",
    "status": "..."
  },
  "confidence_used": "which confirmed fact anchors the title"
}"""


def generate_title(facts_data: dict) -> dict:
    """Generate a Clearground title from extracted facts."""
    facts_summary = json.dumps({
        "confirmed_facts": facts_data.get("confirmed_facts", []),
        "unknowns": facts_data.get("unknowns", []),
    }, indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=TITLE_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Generate a Clearground title from these facts:\n\n{facts_summary}"
        }],
    )
    try:
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)
    except Exception:
        return {"title": "Title generation failed", "formula_breakdown": {}}
