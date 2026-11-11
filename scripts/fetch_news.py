#!/usr/bin/env python3
"""Fetch headlines from international news feeds and write docs/news.json.

Standard library only. A feed that fails is skipped and recorded in the
"sources" list, so one broken outlet never stops the update.

We store only the headline, the link, the outlet name and the time.
Readers click through to the outlet for the full story.
"""
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
FEEDS_FILE = ROOT / "feeds.json"
OUT_FILE = ROOT / "docs" / "news.json"

USER_AGENT = "TheInternationalInsideReport-NewsDesk/1.0 (headline aggregator)"
TIMEOUT = 20
PER_FEED = 15          # newest headlines kept per outlet
MAX_AGE_DAYS = 3       # drop anything older
MAX_ITEMS = 600        # size cap for news.json

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def local(tag):
    """Tag name without its XML namespace."""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def clean(text):
    text = html.unescape(text or "")
    text = TAG_RE.sub("", text)
    return SPACE_RE.sub(" ", text).strip()


def parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        dt = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        dt = None
    if dt is None:
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def entry_link(entry):
    """RSS puts the link in text; Atom puts it in an href attribute."""
    href = None
    for child in entry:
        if local(child.tag) != "link":
            continue
        if child.get("href"):
            if child.get("rel") in (None, "alternate"):
                return child.get("href").strip()
            href = href or child.get("href").strip()
        elif child.text and child.text.strip():
            return child.text.strip()
    return href


def parse_feed(xml_bytes, now=None):
    """Return a list of {title, link, date} from RSS 2.0, RDF or Atom."""
    now = now or datetime.now(timezone.utc)
    root = ET.fromstring(xml_bytes)
    items = []
    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        title, date_text = "", None
        for child in el:
            name = local(child.tag)
            if name == "title":
                title = clean("".join(child.itertext()))
            elif name in ("pubDate", "published", "updated", "date") and not date_text:
                date_text = child.text
        link = entry_link(el)
        if not title or not link or not link.lower().startswith(("http://", "https://")):
            continue
        items.append({"title": title, "link": link, "date": parse_date(date_text) or now})
    return items


def fetch_one(feed):
    result = {"feed": feed, "items": [], "ok": False, "error": ""}
    try:
        req = Request(feed["url"], headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read(5_000_000)
        result["items"] = parse_feed(data)
        result["ok"] = True
    except Exception as exc:  # one bad feed must not stop the run
        result["error"] = f"{type(exc).__name__}: {exc}"[:160]
    return result


def normalize(title):
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def build(results, now=None):
    now = now or datetime.now(timezone.utc)
    items, seen_links, seen_titles, sources = [], set(), set(), []
    for res in results:
        feed = res["feed"]
        cutoff = now - timedelta(days=feed.get("max_age_days", MAX_AGE_DAYS))
        kept = 0
        fresh = [i for i in res["items"] if cutoff <= i["date"] <= now + timedelta(hours=1)]
        for it in sorted(fresh, key=lambda i: i["date"], reverse=True)[:PER_FEED]:
            key = normalize(it["title"])
            if it["link"] in seen_links or (key and key in seen_titles):
                continue
            seen_links.add(it["link"])
            seen_titles.add(key)
            items.append({
                "t": it["title"],
                "u": it["link"],
                "s": feed["name"],
                "r": feed["region"],
                "y": feed["type"],
                "d": it["date"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
            kept += 1
        sources.append({"name": feed["name"], "region": feed["region"], "ok": res["ok"], "count": kept, "error": res["error"]})
    items.sort(key=lambda i: i["d"], reverse=True)
    return {
        "updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": sources,
        "items": items[:MAX_ITEMS],
    }


def main():
    feeds = json.loads(FEEDS_FILE.read_text(encoding="utf-8"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch_one, feeds))
    data = build(results)
    live = sum(1 for s in data["sources"] if s["ok"])
    if live == 0:
        print("No feed answered; keeping the previous news.json.", file=sys.stderr)
        return 1
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(data['items'])} headlines from {live}/{len(feeds)} outlets")
    for s in data["sources"]:
        if not s["ok"]:
            print(f"  skipped {s['name']}: {s['error']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
