#!/usr/bin/env python3
"""Generate /stories/index.html — a static, crawlable archive of every ENYT page."""
import os, re, json, html
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://eastnewyorktimes.com"

# slug -> (section, short label for headline if title is long)
EXCLUDE = {"stories", "ethics", "corrections"}

SECTIONS = {
    "housing": "Housing & NYCHA",
    "civic": "Community Board 5 & Civic Life",
    "politics": "Politics & Elections",
    "safety": "Public Safety & Justice",
    "services": "Health, Benefits & Services",
    "transit": "Transit & Development",
    "schools": "Schools & Youth",
    "culture": "Culture, Events & Neighborhood",
    "guides": "Guides & Reference",
}
ORDER = ["housing", "civic", "politics", "safety", "services", "transit",
         "schools", "culture", "guides"]

ASSIGN = {
    "ehv": "housing", "cityfheps": "housing", "rentboard": "housing", "spp": "housing",
    "banks-calls-new-nycha-leadership-public-housing-privatization": "housing",
    "letter-real-nycha-story-accountability": "housing",
    "housing-wealth-and-who-gets-to-stay-east-new-york": "housing",

    "cb5meetings": "civic", "alice-lowman-cb5-attendance-borough-hall-reversal": "civic",
    "budcity": "civic", "cannabis": "civic", "restaurant": "civic",
    "townhall": "civic", "constituent-pop-ups-district-37": "civic",
    "wellness": "civic",

    "ad54": "politics", "primary2026": "politics", "the-sit-down": "politics",
    "nikki-lucas-cb5-budget-housing-education-democratic-leadership": "politics",

    "publicsafety": "safety", "marcelin": "safety",
    "nypd-youth-commander-perez": "safety",

    "medicaid": "services", "medicaid2": "services", "essentialplan": "services",
    "snap": "services", "snap2": "services",

    "gline": "transit", "fairfares": "transit",
    "broadway-junction-local-hiring": "transit",

    "regents": "schools", "twok": "schools", "resourcefair": "schools",

    "juneteenth": "culture", "bric": "culture", "knicks": "culture",
    "seniorday": "culture", "fifty-years-on-one-block": "culture",
    "virginia-burroughs-way-video": "culture",

    "honorary-street-names": "guides", "how-to-request-street-conaming-cb5": "guides",
}

FALLBACK_DATES = {
    "honorary-street-names": "2026-08-19",
    "how-to-request-street-conaming-cb5": "2026-08-19",
    "virginia-burroughs-way-video": "2026-08-19",
}


def clean_title(t):
    t = re.sub(r"\s+", " ", t).strip()
    # strip the trailing site name in its various separators
    t = re.sub(r"\s*[\u2014\u2013|-]\s*East New York Times\s*$", "", t)
    return t.strip()


def collect():
    out = []
    for d in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, d, "index.html")
        if not os.path.isdir(os.path.join(ROOT, d)) or not os.path.exists(p):
            continue
        if d in EXCLUDE:
            continue
        h = open(p, encoding="utf-8", errors="replace").read()

        def g(pat):
            m = re.search(pat, h, re.I | re.S)
            return m.group(1).strip() if m else ""

        date = g(r'"datePublished"\s*:\s*"(.*?)"') or FALLBACK_DATES.get(d, "")
        out.append({
            "slug": d,
            "url": f"/{d}/",
            "title": clean_title(g(r"<title>(.*?)</title>")),
            "desc": re.sub(r"\s+", " ", g(r'<meta name="description" content="(.*?)"')),
            "img": g(r'<meta property="og:image" content="(.*?)"'),
            "date": date[:10],
            "section": ASSIGN.get(d, "culture"),
        })
    return out


def fmt(d):
    if not d:
        return ""
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y")
    except Exception:
        return d


def build(items):
    items.sort(key=lambda x: x["date"], reverse=True)
    total = len(items)

    # ---------- schema ----------
    itemlist = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Story Archive — East New York Times",
        "url": f"{SITE}/stories/",
        "description": f"Complete archive of all {total} East New York Times stories, "
                       "guides and reports covering East New York, Brooklyn.",
        "isPartOf": {"@type": "WebSite", "name": "East New York Times",
                     "alternateName": "ENYT", "url": f"{SITE}/"},
        "publisher": {
            "@type": "NewsMediaOrganization",
            "name": "East New York Times",
            "alternateName": "ENYT",
            "url": f"{SITE}/",
            "sameAs": [
                "https://www.instagram.com/eastnewyorktimes/",
                "https://www.youtube.com/@eastnewyorktimes",
                "https://eastnewyorktimes.substack.com",
            ],
        },
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": total,
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1,
                 "url": SITE + it["url"], "name": it["title"]}
                for i, it in enumerate(items)
            ],
        },
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Story Archive",
             "item": f"{SITE}/stories/"},
        ],
    }

    # ---------- recent list ----------
    recent = []
    for it in items[:8]:
        recent.append(f"""        <li class="recent-item">
          <a href="{it['url']}">
            <span class="recent-date">{html.escape(fmt(it['date']))}</span>
            <span class="recent-title">{html.escape(it['title'])}</span>
          </a>
        </li>""")
    recent_html = "\n".join(recent)

    # ---------- sections ----------
    secs = []
    toc = []
    for key in ORDER:
        group = [i for i in items if i["section"] == key]
        if not group:
            continue
        label = SECTIONS[key]
        toc.append(f'<li><a href="#{key}">{html.escape(label)} '
                   f'<span class="toc-count">{len(group)}</span></a></li>')
        cards = []
        for it in group:
            date_html = (f'<time class="card-date" datetime="{it["date"]}">'
                         f'{html.escape(fmt(it["date"]))}</time>') if it["date"] else ""
            cards.append(f"""        <article class="card">
          {date_html}
          <h3 class="card-title"><a href="{it['url']}">{html.escape(it['title'])}</a></h3>
          <p class="card-dek">{html.escape(it['desc'])}</p>
          <a class="card-link" href="{it['url']}">Read the story</a>
        </article>""")
        secs.append(f"""    <section class="archive-section" id="{key}">
      <div class="section-head">
        <h2>{html.escape(label)}</h2>
        <span class="section-count">{len(group)} {'story' if len(group)==1 else 'stories'}</span>
      </div>
      <div class="card-grid">
{chr(10).join(cards)}
      </div>
    </section>""")

    sections_html = "\n\n".join(secs)
    toc_html = "\n          ".join(toc)
    today = datetime.now().strftime("%Y-%m-%d")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-ESCSB47KZY"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-ESCSB47KZY');
  </script>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Story Archive — Every East New York Times Report | ENYT</title>
  <meta name="description" content="The complete East New York Times (ENYT) story archive: all {total} reports, guides and explainers on housing, NYCHA, Community Board 5, transit, schools, public safety and culture in East New York, Brooklyn." />
  <link rel="canonical" href="{SITE}/stories/" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <link href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet" />
  <link rel="icon" href="/favicon.ico" sizes="48x48" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" sizes="any" />
  <link rel="icon" type="image/png" href="/favicon.png" sizes="512x512" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="East New York Times" />
  <meta property="og:title" content="Story Archive — Every East New York Times Report" />
  <meta property="og:description" content="All {total} East New York Times reports, guides and explainers, organized by beat." />
  <meta property="og:url" content="{SITE}/stories/" />
  <meta property="og:image" content="{SITE}/broadway-junction-hire-east-ny.jpg" />
  <meta property="og:locale" content="en_US" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Story Archive — Every East New York Times Report" />
  <meta name="twitter:description" content="All {total} East New York Times reports, guides and explainers, organized by beat." />
  <meta name="twitter:image" content="{SITE}/broadway-junction-hire-east-ny.jpg" />
  <script type="application/ld+json">
{json.dumps(itemlist, indent=2)}
  </script>
  <script type="application/ld+json">
{json.dumps(breadcrumb, indent=2)}
  </script>
  <style>
    :root {{
      --bg: #0d1117; --surface: #161b22; --surface-2: #1c2128; --surface-3: #21262d;
      --border: #2d333b; --divider: #21262d;
      --text: #e6edf3; --text-muted: #8b949e; --text-faint: #484f58;
      --accent: #e8952a; --accent-hover: #d4820a; --accent-dim: rgba(232,149,42,0.12);
      --font-display: 'Clash Display', 'Georgia', serif;
      --font-body: 'Satoshi', 'Inter', sans-serif;
      --radius: 6px; --radius-lg: 12px;
      --transition: 200ms cubic-bezier(0.16,1,0.3,1);
      --max-w: 1200px;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; scroll-padding-top: 90px; -webkit-font-smoothing: antialiased; }}
    body {{ font-family: var(--font-body); font-size: 1rem; line-height: 1.6; color: var(--text); background: var(--bg); overflow-x: hidden; }}
    img {{ display: block; max-width: 100%; height: auto; }}
    a {{ color: inherit; text-decoration: none; }}
    ul {{ list-style: none; }}
    h1,h2,h3 {{ font-family: var(--font-display); line-height: 1.15; letter-spacing: -0.01em; text-wrap: balance; }}
    :focus-visible {{ outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 3px; }}
    .container {{ width: 100%; max-width: var(--max-w); margin-inline: auto; padding-inline: clamp(1.25rem, 5vw, 4rem); }}

    /* top bar + header */
    .topbar {{ background: var(--accent); color: #0d1117; font-size: 0.75rem; font-weight: 700;
      letter-spacing: 0.08em; text-transform: uppercase; padding: 0.4rem 0; text-align: center; }}
    .header {{ position: sticky; top: 0; z-index: 50; background: rgba(13,17,23,0.92);
      backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); }}
    .header-inner {{ display: flex; align-items: center; justify-content: space-between;
      gap: 1.5rem; padding-block: 0.85rem; flex-wrap: wrap; }}
    .masthead-name {{ display: block; font-family: var(--font-display); font-weight: 700;
      font-size: 1.35rem; letter-spacing: -0.02em; }}
    .masthead-name span {{ color: var(--accent); }}
    .masthead-sub {{ display: block; font-size: 0.62rem; letter-spacing: 0.16em;
      text-transform: uppercase; color: var(--text-muted); margin-top: 0.15rem; }}
    .nav ul {{ display: flex; gap: 1.4rem; flex-wrap: wrap; }}
    .nav a {{ font-size: 0.85rem; font-weight: 500; color: var(--text-muted); transition: color var(--transition); }}
    .nav a:hover {{ color: var(--text); }}
    .nav a.active {{ color: var(--accent); }}

    /* hero */
    .archive-hero {{ padding: clamp(2.5rem, 6vw, 4.5rem) 0 2rem; border-bottom: 1px solid var(--border); }}
    .eyebrow {{ display: inline-block; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.14em;
      text-transform: uppercase; color: var(--accent); background: var(--accent-dim);
      padding: 0.3rem 0.7rem; border-radius: 3px; margin-bottom: 1.1rem; }}
    .archive-hero h1 {{ font-size: clamp(2rem, 5vw, 3.1rem); margin-bottom: 1rem; }}
    .archive-hero p {{ color: var(--text-muted); font-size: 1.05rem; max-width: 62ch; }}

    /* layout */
    .archive-layout {{ display: grid; grid-template-columns: minmax(0,1fr) 300px;
      gap: clamp(2rem, 4vw, 3.5rem); padding-block: clamp(2rem, 5vw, 3.5rem); align-items: start; }}

    /* sidebar */
    .sidebar {{ position: sticky; top: 100px; display: grid; gap: 1.5rem; }}
    .panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.35rem; }}
    .panel h2 {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
      color: var(--accent); margin-bottom: 1rem; font-family: var(--font-body); }}
    .toc li + li {{ margin-top: 0.55rem; }}
    .toc a {{ display: flex; align-items: baseline; justify-content: space-between; gap: 0.6rem;
      font-size: 0.88rem; color: var(--text-muted); transition: color var(--transition); }}
    .toc a:hover {{ color: var(--accent); }}
    .toc-count {{ font-size: 0.7rem; color: var(--text-faint); font-variant-numeric: tabular-nums; }}
    .recent-item + .recent-item {{ margin-top: 0.85rem; padding-top: 0.85rem; border-top: 1px solid var(--divider); }}
    .recent-date {{ display: block; font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-faint); margin-bottom: 0.2rem; }}
    .recent-title {{ display: block; font-size: 0.88rem; font-weight: 500; line-height: 1.4; color: var(--text-muted); transition: color var(--transition); }}
    .recent-item a:hover .recent-title {{ color: var(--accent); }}
    .panel-cta p {{ font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1rem; }}
    .btn {{ display: inline-block; font-size: 0.82rem; font-weight: 600; padding: 0.6rem 1.1rem;
      border-radius: var(--radius); transition: background var(--transition); }}
    .btn-accent {{ background: var(--accent); color: #0d1117; }}
    .btn-accent:hover {{ background: var(--accent-hover); }}

    /* sections */
    .archive-section + .archive-section {{ margin-top: clamp(2.5rem, 5vw, 3.5rem); }}
    .section-head {{ display: flex; align-items: baseline; gap: 0.9rem; padding-bottom: 0.7rem;
      margin-bottom: 1.5rem; border-bottom: 2px solid var(--accent); }}
    .section-head h2 {{ font-size: clamp(1.25rem, 2.6vw, 1.6rem); }}
    .section-count {{ font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;
      color: var(--text-faint); white-space: nowrap; margin-left: auto; }}
    .card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.25rem; }}
    .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg);
      padding: 1.35rem; display: flex; flex-direction: column; gap: 0.6rem;
      transition: border-color var(--transition), transform var(--transition); }}
    .card:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
    .card-date {{ font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em;
      text-transform: uppercase; color: var(--text-faint); }}
    .card-title {{ font-size: 1.02rem; line-height: 1.3; }}
    .card-title a {{ transition: color var(--transition); }}
    .card-title a:hover {{ color: var(--accent); }}
    .card-dek {{ font-size: 0.875rem; color: var(--text-muted); line-height: 1.55; }}
    .card-link {{ margin-top: auto; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em;
      text-transform: uppercase; color: var(--accent); }}
    .card-link:hover {{ color: var(--accent-hover); }}

    /* footer */
    .footer {{ background: var(--surface); border-top: 1px solid var(--border);
      padding: clamp(2.5rem, 5vw, 3.5rem) 0 1.5rem; margin-top: clamp(2.5rem, 5vw, 4rem); }}
    .footer-grid {{ display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 2.5rem; }}
    .footer-brand h3 {{ font-size: 1.3rem; margin-bottom: 0.7rem; }}
    .footer-brand h3 span {{ color: var(--accent); }}
    .footer-brand p {{ font-size: 0.88rem; color: var(--text-muted); max-width: 42ch; }}
    .footer-col h4 {{ font-family: var(--font-body); font-size: 0.72rem; font-weight: 700;
      letter-spacing: 0.14em; text-transform: uppercase; color: var(--accent); margin-bottom: 0.9rem; }}
    .footer-col li + li {{ margin-top: 0.5rem; }}
    .footer-col a {{ font-size: 0.88rem; color: var(--text-muted); transition: color var(--transition); }}
    .footer-col a:hover {{ color: var(--text); }}
    .footer-bottom {{ margin-top: 2.5rem; padding-top: 1.25rem; border-top: 1px solid var(--border);
      display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
      font-size: 0.78rem; color: var(--text-faint); }}

    @media (max-width: 980px) {{
      .archive-layout {{ grid-template-columns: 1fr; }}
      .sidebar {{ position: static; order: -1; }}
      .footer-grid {{ grid-template-columns: 1fr; gap: 2rem; }}
    }}
    @media (max-width: 620px) {{
      .nav ul {{ gap: 1rem; }}
      .card-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

  <div class="topbar">East New York, Brooklyn · Independent Community Journalism</div>

  <header class="header">
    <div class="container header-inner">
      <a href="/" class="masthead">
        <span class="masthead-name">East New York <span>Times</span></span>
        <span class="masthead-sub">East New York · Brooklyn · Est. 2026</span>
      </a>
      <nav class="nav" aria-label="Primary">
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/stories/" class="active" aria-current="page">Archive</a></li>
          <li><a href="/honorary-street-names/">Honorary Names</a></li>
          <li><a href="/the-sit-down/">The Sit Down</a></li>
          <li><a href="/ethics/">Ethics</a></li>
          <li><a href="https://eastnewyorktimes.substack.com" target="_blank" rel="noopener">Subscribe</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main>
    <div class="archive-hero">
      <div class="container">
        <span class="eyebrow">Story Archive</span>
        <h1>Every story the East New York Times has published</h1>
        <p>The complete East New York Times (ENYT) archive — {total} reports, guides
        and explainers covering housing and NYCHA, Community Board 5, transit and development,
        schools, public safety, benefits and neighborhood life in East New York, Brooklyn.</p>
      </div>
    </div>

    <div class="container archive-layout">
      <div class="archive-main">
{sections_html}
      </div>

      <aside class="sidebar">
        <nav class="panel" aria-label="Browse by beat">
          <h2>Browse by beat</h2>
          <ul class="toc">
          {toc_html}
          </ul>
        </nav>
        <div class="panel">
          <h2>Most recent</h2>
          <ul>
{recent_html}
          </ul>
        </div>
        <div class="panel panel-cta">
          <h2>Get ENYT by email</h2>
          <p>Community reporting from East New York, delivered straight to your inbox.</p>
          <a class="btn btn-accent" href="https://eastnewyorktimes.substack.com" target="_blank" rel="noopener">Subscribe free</a>
        </div>
      </aside>
    </div>
  </main>

  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <h3>East New York <span>Times</span></h3>
          <p>Independent community journalism covering East New York, Brooklyn. Civic news,
          local stories, and community events. Also known as ENYT.</p>
        </div>
        <div class="footer-col">
          <h4>Navigate</h4>
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/stories/">Story Archive</a></li>
            <li><a href="/honorary-street-names/">Honorary Names</a></li>
            <li><a href="/how-to-request-street-conaming-cb5/">Request a Co-Naming</a></li>
            <li><a href="/the-sit-down/">The Sit Down</a></li>
            <li><a href="https://eastnewyorktimes.substack.com" target="_blank" rel="noopener">Substack</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>Standards</h4>
          <ul>
            <li><a href="/ethics/">Editorial Standards &amp; Ethics</a></li>
            <li><a href="/corrections/">Corrections Policy</a></li>
            <li><a href="mailto:info@eastnewyorktimes.com">Report an Error</a></li>
            <li><a href="mailto:info@eastnewyorktimes.com">Submit a Story Tip</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; 2026 East New York Times. A publication of Urban Version Media. All rights reserved.</p>
        <p>Archive last updated {today}</p>
      </div>
    </div>
  </footer>

</body>
</html>
"""


if __name__ == "__main__":
    items = collect()
    os.makedirs(os.path.join(ROOT, "stories"), exist_ok=True)
    out = os.path.join(ROOT, "stories", "index.html")
    open(out, "w", encoding="utf-8").write(build(items))
    print(f"wrote {out} with {len(items)} entries")
    missing = [i["slug"] for i in items if i["slug"] not in ASSIGN]
    print("unassigned (defaulted to culture):", missing or "none")
    nodate = [i["slug"] for i in items if not i["date"]]
    print("missing dates:", nodate or "none")
