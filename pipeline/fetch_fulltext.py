"""
Stage 2 — Full-text fetch
Retrieve full article body text from URLs collected in Stage 1.
"""

import concurrent.futures
import time
from newspaper import Article as NewspaperArticle
from newsapi_ingest import Article

# Sources that give full body via API — skip fetching for these
FULL_TEXT_SOURCES = {"theguardian.com", "federalreserve.gov", "whitehouse.gov"}
PAYWALL_DOMAINS = {"nytimes.com", "wsj.com", "ft.com", "bloomberg.com"}


def is_paywalled(url: str) -> bool:
    return any(d in url for d in PAYWALL_DOMAINS)


def fetch_article_text(article: Article) -> Article:
    """Fetch full text for a single article. Returns article with .full_text set."""
    if is_paywalled(article.url):
        article.full_text = article.snippet  # use snippet only for paywalled
        return article
    try:
        np_article = NewspaperArticle(article.url)
        np_article.download()
        np_article.parse()
        text = np_article.text.strip()
        # Must be substantial — reject stubs and error pages
        article.full_text = text if len(text) > 200 else article.snippet
    except Exception as e:
        print(f"Fetch failed for {article.url}: {e}")
        article.full_text = article.snippet
    time.sleep(0.5)  # be a respectful crawler
    return article


def fetch_all_fulltext(articles: list, max_workers: int = 8) -> list:
    """Fetch full text for all articles in parallel."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(fetch_article_text, articles))
    enriched = sum(1 for a in results if len(a.full_text) > len(a.snippet))
    print(f"{enriched}/{len(results)} articles enriched with full text")
    return results
