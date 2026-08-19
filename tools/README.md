# tools/

Four generator scripts. Run them from the repo root. They read the repo's own
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

## `build-icons.py`

Regenerates the full square-icon set from the ENYT wordmark typeface:

| File | Size | Used for |
|---|---|---|
| `favicon.svg` | vector | Modern browsers. Glyphs are converted to paths, so it needs no webfont. |
| `favicon.png` | 512×512 | General use, and the **Google News publisher logo** — Google uses your favicon for this, not an uploaded logo. |
| `favicon.ico` | 16 / 32 / 48 | Legacy browsers, multi-resolution. |
| `apple-touch-icon.png` | 180×180 | iOS home screen. |
| `enyt-square-512.png` | 512×512 | Upload copy for LION Publishers and Project Oasis. |

The mark is `EN` in off-white over `YT` in amber on the dark brand field, with the
same 12.5% corner radius as the original favicon. It was chosen over a single-line
`ENYT` or a lone `E` because it stays legible at 32px in a browser tab while still
reading as ENYT at 512px, which is the size Google News shows a publisher logo at.

Running it also writes `tools/_icon-qa-preview.png`, a strip of every size from
512px down to 16px. Look at that file after any change — small-size legibility is
the whole point of this mark and it cannot be judged at full size.

### Requires the brand font

`build-icons.py` needs Clash Display Bold, the same face as the wordmark. It is not
committed to the repo. Fetch it once:

```bash
curl -sL -o /tmp/clash700.ttf "$(curl -s 'https://api.fontshare.com/v2/css?f[]=clash-display@700' \
  | grep -o 'https\?://[^)]*\.ttf' | head -1)"
python3 tools/build-icons.py
```

Or point it somewhere else with `CLASH_TTF=/path/to/font.ttf`.

To change the mark, edit `render()` for the raster and `build_svg()` for the
vector. Both must be changed together or the SVG and PNG will disagree — compare
them after any edit.

---

## Wide wordmarks

`logo.png` (600×60) and `logo-dark.png` (1200×120) are the horizontal wordmarks.
They remain the right choice for the site masthead and for the `logo` property in
the homepage `NewsMediaOrganization` schema. Do not upload them to directories
that display a square avatar — use `enyt-square-512.png` there.
