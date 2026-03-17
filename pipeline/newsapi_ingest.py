"""
Stage 1 — News ingest
Pull headlines and metadata from RSS feeds and optional NewsData.io API.
"""

import requests
import feedparser
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List

# Free RSS feeds — no auth required
FREE_RSS_FEEDS = [
    "https://feeds.ap.org/rss/apf-topnews",            # AP (wire service, high quality)
    "https://feeds.reuters.com/reuters/topNews",        # Reuters
    "https://content.api.nytimes.com/svc/news/v3/all/recent.rss",
    "https://www.theguardian.com/world/rss",
    "https://rss.politico.com/politics-news.xml",
    "https://feeds.npr.org/1001/rss.xml",
    "https://www.federalreserve.gov/feeds/press_all.xml",  # Primary: Fed
    "https://www.whitehouse.gov/feed/",                    # Primary: White House
    "https://www.congress.gov/rss/most-recent-bills.xml",  # Primary: Congress
]

# Optional: NewsData.io — free tier, 200 credits/day
NEWSDATA_API_KEY = "YOUR_KEY_HERE"
NEWSDATA_URL = "https://newsdata.io/api/1/news"


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


def ingest_newsdata(query: str = "", language: str = "en") -> List[Article]:
    """Pull from NewsData.io free tier (200 credits/day)."""
    params = {"apikey": NEWSDATA_API_KEY, "language": language}
    if query:
        params["q"] = query
    resp = requests.get(NEWSDATA_URL, params=params, timeout=10)
    resp.raise_for_status()
    articles = []
    for item in resp.json().get("results", []):
        try:
            pub = datetime.fromisoformat(item["pubDate"].replace("Z", "+00:00"))
        except Exception:
            pub = datetime.now(timezone.utc)
        articles.append(Article(
            title=item.get("title", ""),
            url=item.get("link", ""),
            source=item.get("source_id", ""),
            published=pub,
            snippet=item.get("description", "") or "",
        ))
    return articles


def ingest_all() -> List[Article]:
    """Run all ingest sources and deduplicate by URL."""
    all_articles = []
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
