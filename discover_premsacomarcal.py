import concurrent.futures
import json
import re
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "CoCoPress/1.0 (linguistic corpus research)"}


def probe(publication):
    page_url = publication["website"]
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        candidates = []
        for link in soup.select("a[href]"):
            href = link.get("href", "").strip()
            if not href:
                continue
            href = urljoin(response.url, href)
            parsed = urlparse(href)
            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc in ("www.premsacomarcal.cat", "premsacomarcal.cat"):
                continue
            if any(host in parsed.netloc for host in (
                "facebook.", "instagram.", "x.com", "linkedin.", "youtube.",
                "google.", "gencat.", "govern.", "wan-ifra.", "cic.", "uab.",
                "vives.", "focir.", "drac.", "tirabol.",
            )):
                continue
            candidates.append(href)

        for candidate in list(dict.fromkeys(candidates))[:20]:
            base = f"{urlparse(candidate).scheme}://{urlparse(candidate).netloc}"
            try:
                page = requests.get(base, headers=HEADERS, timeout=10)
                page.raise_for_status()
                page_soup = BeautifulSoup(page.text, "html.parser")

                for link in page_soup.select('link[type*="rss"], link[type*="atom"], link[href*="feed"], link[href*="rss"]'):
                    feed = urljoin(page.url, link.get("href", ""))
                    parsed_feed = feedparser.parse(feed)
                    if parsed_feed.entries:
                        publication["feed"] = feed
                        publication["domain"] = urlparse(base).netloc.lower().removeprefix("www.")
                        return publication

                for path in ("/feed", "/rss", "/feed.xml", "/rss.xml", "/feed/", "/rss/"):
                    feed = base.rstrip("/") + path
                    parsed_feed = feedparser.parse(feed)
                    if parsed_feed.entries:
                        publication["feed"] = feed
                        publication["domain"] = urlparse(base).netloc.lower().removeprefix("www.")
                        return publication

                for path in ("/sitemap.xml", "/wp-sitemap.xml", "/sitemap_index.xml"):
                    sitemap = base.rstrip("/") + path
                    sitemap_response = requests.get(sitemap, headers=HEADERS, timeout=8)
                    if sitemap_response.status_code == 200 and b"<url" in sitemap_response.content[:1000]:
                        publication["sitemap"] = sitemap
                        publication["domain"] = urlparse(base).netloc.lower().removeprefix("www.")
                        return publication
            except requests.RequestException:
                continue
    except requests.RequestException:
        pass

    publication["domain"] = "premsacomarcal.cat"
    return publication


def main():
    with open("premsacomarcal_sources.json", "r", encoding="utf-8") as handle:
        publications = json.load(handle)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        verified = list(executor.map(probe, publications))

    with open("premsacomarcal_sources_verified.json", "w", encoding="utf-8") as handle:
        json.dump(verified, handle, ensure_ascii=False, indent=2)
    print(len(verified))
    print(sum(1 for item in verified if item.get("feed") or item.get("sitemap")))


if __name__ == "__main__":
    main()
