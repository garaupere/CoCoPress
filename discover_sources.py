import concurrent.futures
import json
import re
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

LIST_URL = "https://ca.wikipedia.org/wiki/Llista_de_premsa_en_catal%C3%A0"
HEADERS = {"User-Agent": "CoCoPress/1.0 (linguistic corpus research)"}


def slug(value):
    value = re.sub(r"[^\w]+", "-", value.casefold(), flags=re.UNICODE)
    return value.strip("-")[:60]


def extract_sources():
    response = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    sources = {}

    for table in soup.select("table.wikitable"):
        for row in table.select("tr")[1:]:
            cells = row.select("th, td")
            if len(cells) < 6:
                continue
            name = re.sub(r"\[[^\]]*\]", "", " ".join(cells[1].get_text(" ", strip=True).split())).strip()
            if not name:
                continue

            website = ""
            for cell in cells:
                for link in cell.select("a[href]"):
                    href = link.get("href", "")
                    if href.startswith(("http://", "https://")) and "wikipedia.org" not in href:
                        website = href
                        break
                if website:
                    break

            if not website:
                continue
            parsed = urlparse(website)
            if not parsed.netloc:
                continue
            key = slug(name)
            sources.setdefault(key, {
                "name": name,
                "domain": parsed.netloc.lower().removeprefix("www."),
                "website": f"{parsed.scheme}://{parsed.netloc}",
                "support": " ".join(cells[0].get_text(" ", strip=True).split()),
            })
    return list(sources.values())


def probe(source):
    base = source["website"]
    try:
        response = requests.get(base, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        feed_links = []
        for link in soup.select('link[type*="rss"], link[type*="atom"], link[href*="feed"], link[href*="rss"]'):
            href = link.get("href")
            if href:
                feed_links.append(urljoin(response.url, href))

        for href in feed_links:
            try:
                parsed = feedparser.parse(href)
                if parsed.entries:
                    source["feed"] = href
                    return source
            except Exception:
                pass

        if feed_links:
            return None

        for path in ("/feed", "/rss", "/feed.xml", "/rss.xml", "/feed/", "/rss/"):
            url = base.rstrip("/") + path
            try:
                parsed = feedparser.parse(url)
                if parsed.entries:
                    source["feed"] = url
                    return source
            except Exception:
                pass

        for path in ("/sitemap.xml", "/wp-sitemap.xml", "/sitemap_index.xml"):
            url = base.rstrip("/") + path
            try:
                sitemap_response = requests.get(url, headers=HEADERS, timeout=8)
                if sitemap_response.status_code == 200 and b"<url" in sitemap_response.content[:1000]:
                    source["sitemap"] = url
                    return source
            except requests.RequestException:
                pass
    except requests.RequestException:
        pass
    return None


def main():
    candidates = extract_sources()
    verified = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        for result in executor.map(probe, candidates):
            if result:
                verified.append(result)

    verified.sort(key=lambda item: item["name"].casefold())
    with open("verified_sources.json", "w", encoding="utf-8") as handle:
        json.dump(verified, handle, ensure_ascii=False, indent=2)
    print(f"{len(candidates)} candidates, {len(verified)} verified")


if __name__ == "__main__":
    main()
