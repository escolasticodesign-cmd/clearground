"""
Stage 3 — Event clustering
Group articles covering the same real-world event using TF-IDF + cosine similarity.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import uuid

SIMILARITY_THRESHOLD = 0.35  # tune: lower = more aggressive grouping


def cluster_articles(articles: list) -> dict:
    """
    Group articles into event clusters.
    Returns: { cluster_id: [Article, ...] }
    """
    if not articles:
        return {}

    # Use title + first 300 chars of snippet for clustering signal
    texts = [f"{a.title} {a.snippet[:300]}" for a in articles]
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        max_features=5000,
        min_df=1,
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    sim_matrix = cosine_similarity(tfidf_matrix)

    # Union-find to group articles above threshold
    parent = list(range(len(articles)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            if sim_matrix[i, j] >= SIMILARITY_THRESHOLD:
                union(i, j)

    # Group by root
    groups = defaultdict(list)
    for i, article in enumerate(articles):
        root = find(i)
        groups[root].append(article)

    # Assign stable cluster IDs and update articles
    clusters = {}
    for root, group in groups.items():
        cluster_id = str(uuid.uuid4())[:8]
        for a in group:
            a.cluster_id = cluster_id
        clusters[cluster_id] = sorted(group, key=lambda x: x.published)

    print(f"{len(articles)} articles → {len(clusters)} clusters")
    return clusters
