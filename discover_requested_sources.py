import concurrent.futures
import json
import re
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "CoCoPress/1.0 (linguistic corpus research)"}

SOURCES = [
    ("Ara", "https://www.ara.cat/", "Catalunya"),
    ("ARA Balears", "https://www.arabalears.cat/", "Illes Balears"),
    ("Ara Multimèdia", "https://www.aramultimedia.com/", "País Valencià"),
    ("betevé", "https://beteve.cat/", "Catalunya"),
    ("Bondia", "https://lleidadiari.cat/", "Catalunya"),
    ("Catalunya Press", "https://www.catalunyapress.cat/", "Catalunya"),
    ("Cultura21", "https://cultura21.cat/", "Catalunya"),
    ("Diari d'Andorra", "https://www.diariandorra.ad/", "Andorra"),
    ("Diari de Balears", "https://www.dbalears.cat/", "Illes Balears"),
    ("Diari de Girona", "https://www.diaridegirona.cat/", "Catalunya"),
    ("Diari de Terrassa", "https://www.diarideterrassa.es/", "Catalunya"),
    ("Eco Diari", "https://www.naciodigital.cat/ecodiari/", "Catalunya"),
    ("El Dimoni", "https://www.eldimoni.com/", "Catalunya"),
    ("El Matí", "https://www.elmati.cat/", "Catalunya"),
    ("El Periódico", "https://www.elperiodico.cat/", "Catalunya"),
    ("El Punt Avui", "https://www.elpuntavui.cat/", "Catalunya"),
    ("El Singular Digital", "https://www.elsingulardigital.cat/", "Catalunya"),
    ("El Temps", "https://www.eltemps.cat/", "País Valencià"),
    ("El Web Negre", "https://www.nuvol.com/elwebnegre/", "Catalunya"),
    ("E-notícies", "https://e-noticies.cat/", "Catalunya"),
    ("Illa Global", "https://www.illaglobal.com/", "Illes Balears"),
    ("La Clau", "https://laclau.cat/", "Catalunya del Nord"),
    ("La Vanguardia", "https://www.lavanguardia.com/encatala/index.html", "Catalunya"),
    ("L'Accent", "https://www.laccent.cat/", "Catalunya"),
    ("La República", "https://www.larepublica.cat/", "Catalunya"),
    ("Nació Digital", "https://www.naciodigital.cat/", "Catalunya"),
    ("Newspapermap", "https://newspapermap.com/", "Catalunya"),
    ("Sa Veu", "https://www.saveu.cat/", "Illes Balears"),
    ("Tribuna", "https://www.tribuna.cat/", "Catalunya"),
    ("VilaWeb", "https://www.vilaweb.cat/", "Catalunya"),
    ("Premsa Forana", "https://premsaforana.cat/revistes.php", "Illes Balears"),
    ("Bellpuig", "https://www.revistabellpuig.cat/", "Illes Balears"),
    ("Mel i Sucre", "https://melisucre.cat/", "Illes Balears"),
    ("L'Estel", "https://www.revistalestel.cat/", "Illes Balears"),
    ("Pes d'Illes", "https://pescadilles.com/", "Illes Balears"),
    ("Cent per Cent", "https://www.centpercent.cat/", "Illes Balears"),
    ("Díngola", "https://dingola.net/", "Illes Balears"),
    ("Núvol", "https://www.nuvol.com/", "Catalunya"),
    ("Sa Plaça", "https://www.saplaca.cat/", "Illes Balears"),
    ("Revista Mirall", "https://revistamirall.com/", "Catalunya"),
    ("Quadern", "https://elpais.com/quadern/", "Catalunya"),
    ("Cavall Fort", "https://cavallfort.cat/cavall-fort/", "Catalunya"),
    ("El Tatano", "https://cavallfort.cat/el-tatano/", "Catalunya"),
    ("Tot Pla", "https://www.totpla.cat/", "Illes Balears"),
]


def slug(name):
    return re.sub(r"[^\w]+", "-", name.casefold(), flags=re.UNICODE).strip("-")[:60]


def probe(item):
    name, website, territory = item
    result = {
        "name": name,
        "website": website,
        "territory": territory,
        "domain": urlparse(website).netloc.lower().removeprefix("www."),
    }
    try:
        response = requests.get(website, headers=HEADERS, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.select('link[type*="rss"], link[type*="atom"], link[href*="feed"], link[href*="rss"]'):
            feed = urljoin(response.url, link.get("href", ""))
            if feed:
                parsed = feedparser.parse(feed)
                if parsed.entries:
                    result["feed"] = feed
                    return result

        base = f"{urlparse(response.url).scheme}://{urlparse(response.url).netloc}"
        for path in ("/feed", "/rss", "/feed.xml", "/rss.xml", "/feed/", "/rss/"):
            feed = base.rstrip("/") + path
            try:
                parsed = feedparser.parse(feed)
                if parsed.entries:
                    result["feed"] = feed
                    return result
            except Exception:
                pass

        for path in ("/sitemap.xml", "/wp-sitemap.xml", "/sitemap_index.xml"):
            sitemap = base.rstrip("/") + path
            try:
                sitemap_response = requests.get(sitemap, headers=HEADERS, timeout=8)
                if sitemap_response.status_code == 200 and b"<url" in sitemap_response.content[:1000]:
                    result["sitemap"] = sitemap
                    return result
            except requests.RequestException:
                pass
    except requests.RequestException:
        pass
    return result


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(probe, SOURCES))

    unique = {}
    for item in results:
        unique.setdefault(item["name"].casefold(), item)
    values = list(unique.values())
    with open("requested_sources_verified.json", "w", encoding="utf-8") as handle:
        json.dump(values, handle, ensure_ascii=False, indent=2)
    print(len(values), sum(bool(x.get("feed") or x.get("sitemap")) for x in values))


if __name__ == "__main__":
    main()
