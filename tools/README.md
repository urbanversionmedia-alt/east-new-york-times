# tools/

Three generator scripts. Run them from the repo root. They read the repo's own
files, so they never need editing when you add a story — just run them.

## Whenever you publish or update a story

```bash
python3 tools/build-archive.py     # regenerates /stories/
python3 tools/build-sitemaps.py    # regenerates sitemap.xml and news-sitemap.xml
```

Then commit the changed files along with your story.

Do not hand-edit `sitemap.xml`, `news-sitemap.xml`, or `stories/index.html`.
They are generated, and hand edits will be overwritten.

---

## `build-archive.py`

Generates `/stories/index.html`, the full crawlable story archive.

Reads every folder in the repo that contains an `index.html` and pulls the
headline from `<title>`, the summary from `<meta name="description">`, and the
date from that page's `datePublished` in its NewsArticle JSON-LD. This is why
the archive stays accurate without a database — each story page is its own
source of truth.

Emits `CollectionPage` + `ItemList` + `BreadcrumbList` structured data.

**When you add a new story, add its slug to the `ASSIGN` dictionary** near the
top so it lands in the right beat. Anything missing from `ASSIGN` silently falls
into "Culture, Events & Neighborhood" — the script prints a warning listing any
unassigned slugs, so read its output.

Beats are defined in `SECTIONS` and their display order in `ORDER`.
Pages that should never appear in the archive go in `EXCLUDE`.

## `build-sitemaps.py`

Generates two files:

- **`sitemap.xml`** — every page, with per-page `lastmod` read from each page's
  own `datePublished` rather than a single build date.
- **`news-sitemap.xml`** — the Google News sitemap. Per Google's spec this holds
  only articles published in the **last 2 days**, so it is short by design and
  **must be regenerated every time you publish**. If nothing is inside the
  window it writes a valid empty `<urlset>`, which correctly tells Google there
  is nothing new.

Reference pages that aren't dated news articles belong in `NOT_NEWS`.
Undated pages can get a fixed date via `STATIC_LASTMOD`.

After a publish, resubmit both sitemaps in Google Search Console.

## `build-policy-pages.py`

Generates `/ethics/index.html` and `/corrections/index.html`.

Run this only when a policy actually changes. The full policy text lives in this
script in the `ETHICS_BODY` and `CORRECTIONS_BODY` constants — edit it there, not
in the generated HTML, or your change will be lost on the next run.

Dates are controlled by three constants at the top:

- `EFFECTIVE` / `EFFECTIVE_ISO` — when the policy takes force (currently
  September 1, 2026). Shown to readers.
- `PUBLISHED_ISO` / `PUBLISHED_LABEL` — when the page went live (August 19,
  2026). Used for schema `datePublished`.

**When you publish a correction,** add it to the log in the `#log` section of
`CORRECTIONS_BODY`, replacing the `empty-log` block, and bump `PUBLISHED_ISO`
and `PUBLISHED_LABEL`.

---

## Known gap: logo sizes

Google News uses your **site favicon** as the publisher logo on standard News
surfaces, not an uploaded logo. Current assets:

| File | Size | Note |
|---|---|---|
| `favicon.png` | 32×32 | Too small for a publisher logo |
| `logo.png` | 600×60 | Wide wordmark |
| `logo-dark.png` | 1200×120 | Wide wordmark |

There is no square logo in the repo. A **512×512 square** version of the ENYT
mark is needed for Google News and for directory listings such as LION
Publishers and Project Oasis. This is a design task, not a script task.
