/**
 * Clearground — NewsAPI proxy
 * Vercel serverless function at /api/news
 *
 * Proxies requests to newsapi.org so the browser avoids CORS restrictions.
 * NewsAPI free tier blocks direct browser requests from deployed domains.
 *
 * Usage:
 *   GET /api/news?q=federal+reserve           → everything endpoint (keyword search)
 *   GET /api/news?category=business           → top-headlines endpoint (by category)
 *   GET /api/news                              → top-headlines, US, all categories
 *
 * Environment variable required (set in Vercel dashboard):
 *   NEWSAPI_KEY=your_key_here
 */

export default async function handler(req, res) {
  // CORS headers — allow requests from the same Vercel deployment
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.NEWSAPI_KEY;
  if (!apiKey) {
    return res.status(500).json({
      error: 'NEWSAPI_KEY environment variable not set. Add it in your Vercel project settings under Settings → Environment Variables.'
    });
  }

  const { q, category, pageSize = '40' } = req.query;

  let newsApiUrl;
  const params = new URLSearchParams({ apiKey, pageSize, language: 'en' });

  if (q) {
    // Keyword search — /v2/everything
    params.set('q', q);
    params.set('sortBy', 'publishedAt');
    newsApiUrl = `https://newsapi.org/v2/everything?${params}`;
  } else {
    // Top headlines — /v2/top-headlines
    params.set('country', 'us');
    if (category) params.set('category', category);
    newsApiUrl = `https://newsapi.org/v2/top-headlines?${params}`;
  }

  try {
    const upstream = await fetch(newsApiUrl);
    const data = await upstream.json();

    if (data.status !== 'ok') {
      return res.status(400).json({ error: data.message || 'NewsAPI error', code: data.code });
    }

    // Cache for 5 minutes — reduces API usage on free tier
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=60');
    return res.status(200).json(data);

  } catch (err) {
    console.error('NewsAPI proxy error:', err);
    return res.status(502).json({ error: 'Failed to reach NewsAPI: ' + err.message });
  }
}
