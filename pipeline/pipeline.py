"""
Clearground — Full pipeline orchestrator
Run all 6 stages and output stories.json for the frontend.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python pipeline.py
"""

from newsapi_ingest import ingest_all
from fetch_fulltext import fetch_all_fulltext
from cluster import cluster_articles
from extract_facts import extract_facts_for_cluster
from title_engine import generate_title
from spin_detect import detect_spin_for_cluster
import json


def run_pipeline() -> list:
    """Full Clearground pipeline. Returns list of story records."""

    # Stage 1: Ingest
    print("[1/6] Ingesting articles...")
    articles = ingest_all()
    print(f"  → {len(articles)} articles ingested")

    # Stage 2: Full-text fetch
    print("[2/6] Fetching full text...")
    articles = fetch_all_fulltext(articles)

    # Stage 3: Cluster by event
    print("[3/6] Clustering by event...")
    clusters = cluster_articles(articles)

    stories = []
    for cluster_id, cluster_articles_list in clusters.items():
        # Skip solo articles with only a snippet (not enough signal)
        if len(cluster_articles_list) == 1 and not cluster_articles_list[0].full_text:
            continue

        print(f"[4/6] Extracting facts: cluster {cluster_id} ({len(cluster_articles_list)} articles)")
        facts_data = extract_facts_for_cluster(cluster_articles_list)

        print(f"[5/6] Generating title: cluster {cluster_id}")
        title_data = generate_title(facts_data)

        print(f"[6/6] Detecting spin: cluster {cluster_id}")
        spin_flags = detect_spin_for_cluster(
            cluster_articles_list,
            facts_data.get("confirmed_facts", [])
        )

        # Assemble the Clearground story record
        story = {
            "cluster_id": cluster_id,
            "title": title_data.get("title"),
            "formula_breakdown": title_data.get("formula_breakdown"),
            "confidence_score": facts_data.get("confidence_score", 1),
            "confirmed_facts": facts_data.get("confirmed_facts", []),
            "conflicted_facts": facts_data.get("conflicted_facts", []),
            "unknowns": facts_data.get("unknowns", []),
            "spin_flags": spin_flags,
            "source_articles": [a.url for a in cluster_articles_list],
            "last_updated": max(a.published for a in cluster_articles_list).isoformat(),
        }
        stories.append(story)

    # Save for the frontend
    with open("stories.json", "w") as f:
        json.dump(stories, f, indent=2)
    print(f"\nDone. {len(stories)} stories written to stories.json")
    return stories


if __name__ == "__main__":
    run_pipeline()
