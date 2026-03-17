"""
Stage 1 — News ingest
Pull headlines and metadata from RSS feeds and NewsAPI.org.

SETUP:
  Replace NEWSAPI_KEY below with your key from https://newsapi.org
  Free tier: 100 requests/day, top headlines + search
"""

import requests
import feedparser
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List

# ─────────────────────────────────────────────
# YOUR NEWSAPI.ORG KEY — paste it here
# Get one free at https://newsapi.org/register
# ─────────────────────────────────────────────
NEWSAPI_KEY = "YOUR_NEWSAPI_KEY_HERE"
NEWSAPI_TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
NEWSAPI_EVERYTHING_URL    = "https://newsapi.org/v2/everything"

# Free RSS feeds — no auth required (fallback / supplement)
FREE_RSS_FEEDS = [
    "https://feeds.ap.org/rss/apf-topnews",            # AP (wire service, high quality)
    "https://feeds.reuters.com/reuters/topNews",        # Reuters
    "https://www.theguardian.com/world/rss",
    "https://rss.politico.com/politics-news.xml",
    "https://feeds.npr.org/1001/rss.xml",
    "https://www.federalreserve.gov/feeds/press_all.xml",  # Primary: Fed
    "https://www.whitehouse.gov/feed/",                    # Primary: White House
    "https://www.congress.gov/rss/most-recent-bills.xml",  # Primary: Congress
]


@dataclass
class Article:
    title: str
    url: str
    source: str
    published: datetime
    snippet: str
    full_text: str = ""       # filled in Stage 2
    cluster_id: str = ""      # assigned in Stage 3


def ingest_rss(feed_url: str) -> List[Article]:
    """Parse an RSS feed and return Article objects."""
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:20]:  # cap per feed
        published = datetime.now(timezone.utc)
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        articles.append(Article(
            title=entry.get('title', '').strip(),
            url=entry.get('link', ''),
            source=feed.feed.get('title', feed_url),
            published=published,
            snippet=entry.get('summary', '')[:500],
        ))
    return articles


def ingest_newsapi_top(country: str = "us", category: str = "") -> List[Article]:
    """
    Pull top headlines from NewsAPI.org.
    Free tier: US only, 100 req/day.
    category options: business, entertainment, general, health, science, sports, technology
    """
    if NEWSAPI_KEY == "YOUR_NEWSAPI_KEY_HERE":
        print("⚠  NEWSAPI_KEY not set — skipping NewsAPI.org. Add your key to newsapi_ingest.py")
        return []
    params = {
        "apiKey": NEWSAPI_KEY,
        "country": country,
        "pageSize": 100,
    }
    if category:
        params["category"] = category
    try:
        resp = requests.get(NEWSAPI_TOP_HEADLINES_URL, params=params, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"NewsAPI top-headlines failed: {e}")
        return []
    articles = []
    for item in resp.json().get("articles", []):
        try:
            pub = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
        except Exception:
            pub = datetime.now(timezone.utc)
        source_name = (item.get("source") or {}).get("name", "Unknown")
        articles.append(Article(
            title=item.get("title", "").strip(),
            url=item.get("url", ""),
            source=source_name,
            published=pub,
            snippet=item.get("description", "") or "",
        ))
    print(f"  NewsAPI.org: {len(articles)} top headlines fetched")
    return articles


def ingest_newsapi_search(query: str, language: str = "en", sort_by: str = "publishedAt") -> List[Article]:
    """
    Search NewsAPI.org for articles matching a query.
    Useful for pulling all coverage of a specific event.
    sort_by: publishedAt | relevancy | popularity
    """
    if NEWSAPI_KEY == "YOUR_NEWSAPI_KEY_HERE":
        print("⚠  NEWSAPI_KEY not set — skipping NewsAPI.org search.")
        return []
    params = {
        "apiKey": NEWSAPI_KEY,
        "q": query,
        "language": language,
        "sortBy": sort_by,
        "pageSize": 100,
    }
    try:
        resp = requests.get(NEWSAPI_EVERYTHING_URL, params=params, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"NewsAPI search failed for '{query}': {e}")
        return []
    articles = []
    for item in resp.json().get("articles", []):
        try:
            pub = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
        except Exception:
            pub = datetime.now(timezone.utc)
        source_name = (item.get("source") or {}).get("name", "Unknown")
        articles.append(Article(
            title=item.get("title", "").strip(),
            url=item.get("url", ""),
            source=source_name,
            published=pub,
            snippet=item.get("description", "") or "",
        ))
    print(f"  NewsAPI.org search '{query}': {len(articles)} articles fetched")
    return articles


def ingest_all() -> List[Article]:
    """Run all ingest sources and deduplicate by URL."""
    all_articles = []

    # NewsAPI.org top headlines (primary — requires key)
    all_articles.extend(ingest_newsapi_top(country="us"))

    # RSS feeds (free supplement / primary source)
    for feed_url in FREE_RSS_FEEDS:
        try:
            all_articles.extend(ingest_rss(feed_url))
        except Exception as e:
            print(f"RSS failed for {feed_url}: {e}")

    # Deduplicate by URL
    seen = set()
    deduped = []
    for a in all_articles:
        if a.url not in seen:
            seen.add(a.url)
            deduped.append(a)
    return sorted(deduped, key=lambda x: x.published, reverse=True)
