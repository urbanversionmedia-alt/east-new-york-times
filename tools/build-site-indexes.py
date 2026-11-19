#!/usr/bin/env python3
"""
Rebuild the small auto-generated parts of eastnewyorktimes.com.

Run from the repo root (the daily GitHub Action runs it right after
build-sitemaps.py):

    python3 tools/build-site-indexes.py

What it updates
---------------
feed.xml                 RSS 2.0 feed of the 30 newest dated stories. News
                         directories (Feedspot and others), feed readers and
                         AI search tools use it to find new ENYT stories.

deric-johnson/index.html The "Recent stories by Deric Johnson" list on the
                         author page, between the AUTHOR-STORIES markers.

cb5meetings/index.html   The next date for every CB5 meeting, between the
                         CB5-NEXT and CB5-TABLE markers. Dates are calculated
                         from CB5's published monthly schedule
                         (https://www.nyc.gov/site/brooklyncb5/meetings/meetings.page).
                         July and August are skipped for the summer recess.
                         If the board changes a date, edit OVERRIDES below.

Only files whose content actually changes are rewritten.
"""

import html as htmllib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

SITE = "https://eastnewyorktimes.com"
FEED_SIZE = 30
AUTHOR_LIST_SIZE = 25
AUTHOR_NAME = "Deric Johnson"
TZ = timezone(timedelta(hours=-5))  # Eastern; only used for undated-time stories

NOT_STORIES = {
    "stories", "ethics", "corrections", "about", "deric-johnson", "cb5meetings",
    "honorary-street-names", "how-to-request-street-conaming-cb5",
}

# ---------------------------------------------------------------------------
# CB5 schedule, from the board's published meetings page.
# (label, tag class, tag text, name, weekday 0=Mon, nth week, time, room)
# ---------------------------------------------------------------------------
CB5 = [
    ("general", "ct-general", "General Board", "Full Board Meeting", 2, 4, "6:30 PM", "3rd Floor"),
    ("housing", "ct-housing", "Housing", "Land Use &amp; Housing", 1, 3, "6:30 PM", "2nd Floor, Main Office"),
    ("safety", "ct-safety", "Public Safety", "Public Safety &amp; Quality of Life", 0, 2, "6:00 PM", "2nd Floor, Conference Room"),
    ("transit", "ct-transit", "Transit", "Transportation &amp; TLC", 0, 3, "6:00 PM", "2nd Floor, Conference Room"),
    ("edu", "ct-edu", "Education", "Education &amp; Youth Services", 3, 1, "6:30 PM", "1st Floor, Aviation Room"),
    ("health", "ct-health", "Health", "Aging, Health &amp; Social Services", 1, 2, "6:30 PM", "2nd Floor, Conference Room"),
    ("parks", "ct-parks", "Environment", "Parks, Sanitation &amp; Environment", 1, 1, "6:00 PM", "2nd Floor, Conference Room"),
    ("econ", "ct-econ", "Economic Dev", "Economic Development, IBZ &amp; BIDs", 2, 2, "6:30 PM", "2nd Floor, Conference Room"),
    ("cannabis", "ct-cannabis", "Cannabis", "Cannabis Committee", 0, 1, "6:30 PM", "2nd Floor, Conference Room"),
]
RECESS_MONTHS = {7, 8}
# Board-announced changes: {("general", "2026-11"): "2026-11-18"} moves that
# month's meeting; use None to mark it cancelled.
OVERRIDES = {
    # Moved up a week for Thanksgiving; held Wednesday, Nov. 18, 2026.
    ("general", "2026-11"): "2026-11-18",
}

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def write_if_changed(path, text):
    old = read(path) if os.path.exists(path) else None
    if old == text:
        return False
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return True


def clean(text):
    text = htmllib.unescape(text.replace('\\"', '"')).strip()
    return re.split(r"\s+[\u2014|]\s+East New York Times\s*$", text)[0].strip()


def story_meta(root, slug):
    page = read(os.path.join(root, slug, "index.html"))
    pub = re.search(r'"datePublished"\s*:\s*"(.*?)"', page)
    if not pub:
        return None
    try:
        published = datetime.fromisoformat(pub.group(1).strip())
    except ValueError:
        return None
    if published.tzinfo is None:
        published = published.replace(hour=9, tzinfo=TZ) if len(pub.group(1).strip()) == 10 else published.replace(tzinfo=TZ)
    head = re.search(r'"headline"\s*:\s*"((?:[^"\\]|\\.)*)"', page) or re.search(r"<title>(.*?)</title>", page, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', page)
    section = re.search(r'"articleSection"\s*:\s*"([^"]*)"', page)
    authors = re.findall(r'"@type"\s*:\s*"Person"\s*,\s*"name"\s*:\s*"([^"]+)"', page)
    authors += re.findall(r'"name"\s*:\s*"([^"]+)"\s*,\s*"@type"\s*:\s*"Person"', page)
    if not head:
        return None
    return {
        "slug": slug,
        "url": f"{SITE}/{slug}/",
        "title": clean(head.group(1)),
        "description": clean(desc.group(1)) if desc else "",
        "section": section.group(1) if section else "",
        "published": published,
        "authors": authors,
    }


def stories(root):
    out = []
    for name in sorted(os.listdir(root)):
        if name.startswith(".") or name in NOT_STORIES:
            continue
        if not os.path.exists(os.path.join(root, name, "index.html")):
            continue
        meta = story_meta(root, name)
        if meta:
            out.append(meta)
    out.sort(key=lambda m: m["published"], reverse=True)
    return out


def build_feed(items):
    newest = items[0]["published"] if items else datetime.now(TZ)
    entries = []
    for m in items[:FEED_SIZE]:
        creator = ", ".join(m["authors"]) or "East New York Times"
        cat = f"      <category>{escape(m['section'])}</category>\n" if m["section"] else ""
        entries.append(
            "    <item>\n"
            f"      <title>{escape(m['title'])}</title>\n"
            f"      <link>{m['url']}</link>\n"
            f"      <guid isPermaLink=\"true\">{m['url']}</guid>\n"
            f"      <pubDate>{format_datetime(m['published'])}</pubDate>\n"
            f"      <dc:creator>{escape(creator)}</dc:creator>\n"
            f"{cat}"
            f"      <description>{escape(m['description'])}</description>\n"
            "    </item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        "  <channel>\n"
        "    <title>East New York Times</title>\n"
        f"    <link>{SITE}/</link>\n"
        f'    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml" />\n'
        "    <description>Independent community news for East New York, Cypress Hills, City Line, "
        "Starrett City and Brownsville, Brooklyn.</description>\n"
        "    <language>en-us</language>\n"
        f"    <lastBuildDate>{format_datetime(newest)}</lastBuildDate>\n"
        "    <image>\n"
        f"      <url>{SITE}/enyt-mark-512.png</url>\n"
        "      <title>East New York Times</title>\n"
        f"      <link>{SITE}/</link>\n"
        "    </image>\n"
        + "\n".join(entries)
        + "\n  </channel>\n</rss>\n"
    )


def replace_between(text, start, end, inner):
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        return text
    return pattern.sub(lambda _m: start + inner + end, text, count=1)


def author_list(items):
    mine = [m for m in items if AUTHOR_NAME in m["authors"]][:AUTHOR_LIST_SIZE]
    lines = ["\n          <ul>"]
    for m in mine:
        when = m["published"].strftime("%B %-d, %Y")
        lines.append(
            f'            <li><a class="inline" href="/{m["slug"]}/">{escape(m["title"])}</a> '
            f'<span class="story-date">{when}</span></li>'
        )
    lines.append("          </ul>\n          ")
    return "\n".join(lines)


def nth_weekday(year, month, weekday, n):
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def next_meeting(key, weekday, n, today):
    y, mth = today.year, today.month
    for _ in range(14):
        if mth not in RECESS_MONTHS:
            ym = f"{y}-{mth:02d}"
            if (key, ym) in OVERRIDES:
                val = OVERRIDES[(key, ym)]
                day = date.fromisoformat(val) if val else None
            else:
                day = nth_weekday(y, mth, weekday, n)
            if day and day >= today:
                return day
        mth += 1
        if mth == 13:
            y, mth = y + 1, 1
    return None


def fmt(day):
    return f"{WEEKDAYS[day.weekday()]}, {day.strftime('%B')} {day.day}, {day.year}"


def build_cb5(page, today):
    rows, upcoming = [], []
    for key, cls, tag, name, wd, n, time, room in CB5:
        nxt = next_meeting(key, wd, n, today)
        upcoming.append((nxt, name, time, room))
        when = f"<strong>Next: {fmt(nxt)}</strong>" if nxt else ""
        rows.append(
            "          <tr>\n"
            f'            <td><span class="committee-tag {cls}">{tag}</span><br/><strong>{name}</strong></td>\n'
            f"            <td>Every {ORDINALS[n]} {WEEKDAYS[wd]}<br/>{when}</td>\n"
            f"            <td>{time}</td>\n"
            f"            <td>{room}</td>\n"
            "          </tr>"
        )
    table = "\n" + "\n".join(rows) + "\n          "

    general = upcoming[0][0]
    soon = sorted([u for u in upcoming if u[0]], key=lambda u: u[0])[:4]
    soon_html = "".join(
        f"<br/>{WEEKDAYS[d.weekday()][:3]}, {d.strftime('%b')} {d.day}: {nm} ({tm})" for d, nm, tm, _r in soon
    )
    box = (
        "\n"
        '      <div class="alert-box">\n'
        '        <div class="alert-label">Next General Board Meeting</div>\n'
        f'        <div class="alert-title">{fmt(general)} at 6:30 PM</div>\n'
        '        <div class="alert-details">\n'
        "          <strong>Where:</strong> 127 Pennsylvania Avenue, 3rd Floor, Brooklyn, NY 11207<br/>\n"
        "          <strong>Who can attend:</strong> Open to all residents. Public comment is part of the agenda.<br/><br/>\n"
        f"          <strong>Coming up next:</strong>{soon_html}<br/><br/>\n"
        "          Dates follow CB5's published monthly schedule. The board announces holiday and other changes in advance, "
        'so confirm with the board office at <a href="https://www.nyc.gov/site/brooklyncb5/meetings/meetings.page" target="_blank" rel="noopener" style="color:var(--accent);">nyc.gov/brooklyncb5</a> before you go.\n'
        "        </div>\n"
        "      </div>\n      "
    )
    page = replace_between(page, "<!-- CB5-NEXT:START -->", "<!-- CB5-NEXT:END -->", box)
    page = replace_between(page, "<!-- CB5-TABLE:START -->", "<!-- CB5-TABLE:END -->", table)
    return page


def main() -> int:
    root = repo_root()
    today = datetime.now(TZ).date()
    items = stories(root)
    changed = []

    if write_if_changed(os.path.join(root, "feed.xml"), build_feed(items)):
        changed.append("feed.xml")

    author_path = os.path.join(root, "deric-johnson", "index.html")
    if os.path.exists(author_path):
        page = read(author_path)
        new = replace_between(page, "<!-- AUTHOR-STORIES:START -->", "<!-- AUTHOR-STORIES:END -->", author_list(items))
        if write_if_changed(author_path, new):
            changed.append("deric-johnson/index.html")

    cb5_path = os.path.join(root, "cb5meetings", "index.html")
    if os.path.exists(cb5_path):
        if write_if_changed(cb5_path, build_cb5(read(cb5_path), today)):
            changed.append("cb5meetings/index.html")

    print(f"feed.xml          {min(len(items), FEED_SIZE)} stories")
    print("updated:          " + (", ".join(changed) if changed else "nothing changed"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
