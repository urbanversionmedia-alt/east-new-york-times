#!/usr/bin/env python3
"""
Regenerate sitemap.xml and news-sitemap.xml for eastnewyorktimes.com.

Run this from the repo root every time you publish or update a story:

    python3 tools/build-sitemaps.py

What it does
------------
sitemap.xml       Every folder in the repo that contains an index.html, plus the
                  homepage and /stories/. Per-page <lastmod> is read from each
                  page's own "datePublished" in its NewsArticle JSON-LD, so the
                  dates stay honest instead of all sharing one build date.

news-sitemap.xml  Google News sitemap. Per Google's spec this must contain ONLY
                  articles published in the last 2 days, so it is short by design
                  and must be regenerated on every publish. If nothing was
                  published in the window, the file is written with an empty
                  <urlset>, which is valid and simply tells Google there is
                  nothing new.
                  https://developers.google.com/search/docs/crawling-indexing/sitemaps/news-sitemap

Both files are written to the repo root. Commit them with your story.
"""

import os
import re
import sys
from datetime import datetime, timedelta, timezone

SITE = "https://eastnewyorktimes.com"
PUBLICATION_NAME = "East New York Times"
LANGUAGE = "en"
NEWS_WINDOW_DAYS = 2

# Pages that are reference/landing pages rather than dated news articles.
# They belong in sitemap.xml but never in news-sitemap.xml.
NOT_NEWS = {
    "stories",
    "honorary-street-names",
    "how-to-request-street-conaming-cb5",
}

# Undated pages: give sitemap.xml a sensible lastmod without faking a news date.
STATIC_LASTMOD = {
    "honorary-street-names": "2026-08-19",
    "how-to-request-street-conaming-cb5": "2026-08-19",
    "virginia-burroughs-way-video": "2026-08-19",
}

TZ = timezone(timedelta(hours=-4))  # America/New_York, EDT


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def story_dirs(root: str):
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if name.startswith(".") or not os.path.isdir(path):
            continue
        if os.path.exists(os.path.join(path, "index.html")):
            yield name


def published_iso(root: str, slug: str) -> str:
    """Full ISO datePublished string from the page's JSON-LD, or ''."""
    path = os.path.join(root, slug, "index.html")
    with open(path, encoding="utf-8", errors="replace") as fh:
        html = fh.read()
    match = re.search(r'"datePublished"\s*:\s*"(.*?)"', html)
    return match.group(1).strip() if match else ""


def parse_iso(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def build_sitemap(root: str, slugs, today: str) -> str:
    entries = [
        (f"{SITE}/", today, "daily", "1.0"),
        (f"{SITE}/stories/", today, "daily", "0.9"),
    ]
    for slug in slugs:
        if slug == "stories":
            continue
        iso = published_iso(root, slug)
        lastmod = (iso[:10] if iso else STATIC_LASTMOD.get(slug, today))
        entries.append((f"{SITE}/{slug}/", lastmod, "monthly", "0.8"))

    body = "\n".join(
        f"  <url>\n"
        f"    <loc>{loc}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{freq}</changefreq>\n"
        f"    <priority>{prio}</priority>\n"
        f"  </url>"
        for loc, lastmod, freq, prio in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )


def build_news_sitemap(root: str, slugs, now: datetime):
    cutoff = now - timedelta(days=NEWS_WINDOW_DAYS)
    recent = []
    for slug in slugs:
        if slug in NOT_NEWS:
            continue
        iso = published_iso(root, slug)
        published = parse_iso(iso)
        if published is None:
            continue
        if published.tzinfo is None:
            published = published.replace(tzinfo=TZ)
        if published >= cutoff:
            recent.append((slug, published))

    recent.sort(key=lambda pair: pair[1], reverse=True)

    body = "\n".join(
        f"  <url>\n"
        f"    <loc>{SITE}/{slug}/</loc>\n"
        f"    <news:news>\n"
        f"      <news:publication>\n"
        f"        <news:name>{PUBLICATION_NAME}</news:name>\n"
        f"        <news:language>{LANGUAGE}</news:language>\n"
        f"      </news:publication>\n"
        f"      <news:publication_date>{published.isoformat()}</news:publication_date>\n"
        f"    </news:news>\n"
        f"  </url>"
        for slug, published in recent
    )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + (f"{body}\n" if body else "")
        + "</urlset>\n"
    )
    return xml, recent


def main() -> int:
    root = repo_root()
    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")
    slugs = list(story_dirs(root))

    sitemap = build_sitemap(root, slugs, today)
    with open(os.path.join(root, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(sitemap)

    news_xml, recent = build_news_sitemap(root, slugs, now)
    with open(os.path.join(root, "news-sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(news_xml)

    total = sitemap.count("<loc>")
    print(f"sitemap.xml       {total} URLs")
    print(f"news-sitemap.xml  {len(recent)} article(s) in the last {NEWS_WINDOW_DAYS} days")
    for slug, published in recent:
        print(f"                  /{slug}/  {published.isoformat()}")
    if not recent:
        print("                  (empty urlset — nothing published in the window; this is valid)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
