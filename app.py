import io
import json
import os
import re
import threading
import time
import uuid
import zipfile
from pathlib import Path
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import PurePosixPath
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

SOURCES = {
    "diarilaveu": {
        "name": "La Veu",
        "feed": "https://www.diarilaveu.cat/feed",
        "domain": "diarilaveu.cat",
    },
    "sao": {
        "name": "Saó",
        "feed": "https://revistasao.cat/feed",
        "domain": "revistasao.cat",
    },
    "tresdeu": {
        "name": "Tresdeu",
        "feed": "https://www.tresdeu.com/feed",
        "domain": "tresdeu.com",
    },
    "barcella": {
        "name": "Barcella",
        "feed": None,
        "domain": "barcella.cat",
    },
    "elpenjoll": {
        "name": "El Penjoll",
        "feed": None,
        "domain": "",
    },
    "lafalzia": {
        "name": "La Falzia",
        "feed": None,
        "domain": "",
    },
    "ara": {
        "name": "ARA",
        "feed": "https://www.ara.cat/rss/",
        "domain": "ara.cat",
    },
    "elpuntavui": {
        "name": "El Punt Avui",
        "feed": "https://www.elpuntavui.cat/feed/",
        "domain": "elpuntavui.cat",
    },
    "diaridegirona": {
        "name": "Diari de Girona",
        "feed": "https://www.diaridegirona.cat/rss/",
        "domain": "diaridegirona.cat",
    },
    "vilaweb": {
        "name": "VilaWeb",
        "feed": "https://www.vilaweb.cat/rss/",
        "domain": "vilaweb.cat",
    },
    "beteve": {
        "name": "betevé",
        "feed": "https://beteve.cat/feed/",
        "domain": "beteve.cat",
    },
    "catalunyadiari": {
        "name": "Catalunya Diari",
        "feed": "https://catalunyadiari.com/rss/last-posts",
        "domain": "catalunyadiari.com",
    },
    "catalunyaplural": {
        "name": "Catalunya Plural",
        "feed": "https://catalunyaplural.cat/feed/",
        "domain": "catalunyaplural.cat",
    },
    "catalunyapress": {
        "name": "CatalunyaPress",
        "feed": "https://www.catalunyapress.cat/feed/all",
        "domain": "catalunyapress.cat",
    },
    "dbalears": {
        "name": "dBalears",
        "feed": "https://www.dbalears.cat/feed.rss",
        "domain": "dbalears.cat",
    },
    "directa": {
        "name": "La Directa",
        "feed": "https://directa.cat/feed",
        "domain": "directa.cat",
    },
    "economiadigital": {
        "name": "Economia Digital",
        "feed": "https://economiadigital.es/feed",
        "domain": "economiadigital.es",
    },
    "elcritic": {
        "name": "Crític",
        "feed": "https://www.elcritic.cat/feed",
        "domain": "elcritic.cat",
    },
    "elmon": {
        "name": "El Món",
        "feed": "https://elmon.cat/politica/feed/",
        "domain": "elmon.cat",
    },
    "elnacional": {
        "name": "El Nacional",
        "feed": "https://www.elnacional.cat/uploads/feeds/feed_ca.xml",
        "domain": "elnacional.cat",
    },
    "naciodigital": {
        "name": "Nació Digital",
        "feed": "https://naciodigital.cat/feed",
        "domain": "naciodigital.cat",
    },
    "nuvol": {
        "name": "Núvol",
        "feed": "https://www.nuvol.com/feed",
        "domain": "nuvol.com",
    },
    "eltemps": {
        "name": "El Temps",
        "feed": "https://www.eltemps.cat/sindica",
        "domain": "eltemps.cat",
    },
    "totbarcelona": {
        "name": "Tot Barcelona",
        "feed": "https://totbarcelona.cat/feed",
        "domain": "totbarcelona.cat",
    },
    "terrassadigital": {
        "name": "Canal Terrassa",
        "feed": "https://canalterrassa.cat/feed/",
        "domain": "canalterrassa.cat",
    },
    "diaridetarragona": {
        "name": "Diari de Tarragona",
        "feed": "https://www.diaridetarragona.com/rss",
        "domain": "diaridetarragona.com",
    },
    "arabalears": {
        "name": "ARA Balears",
        "feed": "https://www.arabalears.cat/rss",
        "domain": "arabalears.cat",
    },
    "apunt": {
        "name": "À Punt",
        "feed": "https://www.apuntmedia.es/rss",
        "domain": "apuntmedia.es",
    },
    "canalblau": {
        "name": "Canal Blau",
        "feed": "https://www.canalblau.cat/feed",
        "domain": "canalblau.cat",
    },
    "mallorcadiario": {
        "name": "Mallorca Diario",
        "feed": None,
        "sitemap": "https://www.mallorcadiario.com/wp-sitemap.xml",
        "domain": "mallorcadiario.com",
    },
    "mallorcaconfidencial": {
        "name": "Mallorca Confidencial",
        "feed": None,
        "sitemap": "https://www.mallorcaconfidencial.com/sitemap.xml",
        "domain": "mallorcaconfidencial.com",
    },
    "ultimahora": {
        "name": "Última Hora",
        "feed": None,
        "sitemap": "https://www.ultimahora.es/sitemap.xml",
        "domain": "ultimahora.es",
    },
    "ib3": {
        "name": "IB3 Notícies",
        "feed": None,
        "sitemap": "https://ib3.org/sitemap.xml",
        "domain": "ib3.org",
    },
}

verified_sources_path = Path(__file__).with_name("verified_sources.json")
if verified_sources_path.exists():
    with verified_sources_path.open("r", encoding="utf-8") as handle:
        for source in json.load(handle):
            key = re.sub(r"[^\w]+", "-", source["name"].casefold(), flags=re.UNICODE).strip("-")[:60]
            SOURCES.setdefault(key, {
                "name": source["name"],
                "domain": source["domain"],
                "feed": source.get("feed"),
                "sitemap": source.get("sitemap"),
            })

premsa_forana_path = Path(__file__).with_name("premsaforana_sources.json")
if premsa_forana_path.exists():
    with premsa_forana_path.open("r", encoding="utf-8") as handle:
        for source in json.load(handle):
            key = re.sub(r"[^\w]+", "-", source["name"].casefold(), flags=re.UNICODE).strip("-")[:60]
            SOURCES.setdefault(f"pf-{key}", {
                "name": source["name"],
                "domain": source["domain"],
                "feed": None,
                "sitemap": None,
                "premsa_forana": True,
            })

premsa_comarcal_path = Path(__file__).with_name("premsacomarcal_sources_verified.json")
if premsa_comarcal_path.exists():
    with premsa_comarcal_path.open("r", encoding="utf-8") as handle:
        for source in json.load(handle):
            name = source["name"]
            key = re.sub(r"[^\w]+", "-", name.casefold(), flags=re.UNICODE).strip("-")[:60]
            SOURCES.setdefault(f"pc-{key}", {
                "name": name,
                "domain": source.get("domain", "premsacomarcal.cat"),
                "feed": source.get("feed"),
                "sitemap": source.get("sitemap"),
                "premsa_comarcal": True,
                "website": source.get("website"),
            })

requested_sources_path = Path(__file__).with_name("requested_sources_verified.json")
if requested_sources_path.exists():
    with requested_sources_path.open("r", encoding="utf-8") as handle:
        for source in json.load(handle):
            name = source["name"]
            key = re.sub(r"[^\w]+", "-", name.casefold(), flags=re.UNICODE).strip("-")[:60]
            requested_entry = {
                "name": name,
                "domain": source.get("domain", ""),
                "feed": source.get("feed"),
                "sitemap": source.get("sitemap"),
                "territory": source.get("territory"),
                "website": source.get("website"),
            }
            if key in SOURCES:
                SOURCES[key].update(requested_entry)
            else:
                SOURCES[key] = requested_entry

JOBS = {}
JOBS_LOCK = threading.Lock()
JOB_PROGRESS_CALLBACKS = {}
STANZA_PIPELINE = None
STANZA_LOCK = threading.Lock()


def get_stanza_pipeline():
    global STANZA_PIPELINE
    if STANZA_PIPELINE is not None:
        return STANZA_PIPELINE

    with STANZA_LOCK:
        if STANZA_PIPELINE is not None:
            return STANZA_PIPELINE
        import os
        os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
        import stanza
        try:
            stanza.download("ca", verbose=False)
        except Exception:
            pass
        STANZA_PIPELINE = stanza.Pipeline(
            "ca",
            processors="tokenize,mwt,pos,lemma",
            use_gpu=False,
            verbose=False,
            resources_dir=os.environ.get("STANZA_RESOURCES_DIR"),
        )
    return STANZA_PIPELINE


def tag_text(text):
    pipeline = get_stanza_pipeline()
    document = pipeline(text)
    tagged_sentences = []
    for sentence in document.sentences:
        tagged_tokens = []
        for word in sentence.words:
            surface = word.text or ""
            lemma = word.lemma or surface
            pos = word.upos or "_"
            tagged_tokens.append(f"{surface}_{pos}_{lemma}")
        tagged_sentences.append(" ".join(tagged_tokens))
    return "\n".join(tagged_sentences)


def clean_text(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", BeautifulSoup(value, "html.parser").get_text(" ", strip=True)).strip()


def entry_date(entry):
    if isinstance(entry, dict):
        for key in ("published", "updated", "created", "lastmod"):
            value = entry.get(key)
            if value:
                try:
                    parsed = parsedate_to_datetime(value)
                except (TypeError, ValueError):
                    try:
                        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except (TypeError, ValueError):
                        continue
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
        return None

    for key in ("published", "updated", "created"):
        value = getattr(entry, key, None)
        if value:
            try:
                parsed = parsedate_to_datetime(value)
            except (TypeError, ValueError, OverflowError):
                try:
                    parsed = datetime(*entry[key + "_parsed"][:6], tzinfo=timezone.utc)
                except (AttributeError, KeyError, TypeError):
                    continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
    return None


def safe_stem(title, article_url, index):
    stem = re.sub(r"[^\w]+", "-", title.casefold(), flags=re.UNICODE).strip("-")
    stem = stem[:100] or "article"
    article_id = re.search(r"/([^/?#]+?)(?:/)?$", urlparse(article_url).path)
    suffix = article_id.group(1) if article_id else str(index)
    return f"{stem}-{re.sub(r'[^\w-]+', '-', suffix)}"[:140]


def extract_article(source, article_url):
    headers = {"User-Agent": "LinguaCorpusDownloader/1.0 (research corpus tool)"}
    response = requests.get(article_url, headers=headers, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title_node = soup.select_one("h1")
    if title_node:
        title = clean_text(title_node.get_text(" ", strip=True))
    else:
        title = clean_text(soup.title.get_text(" ", strip=True)) if soup.title else ""

    subtitle = ""
    for selector in ("h2", ".subtitle", ".subtitulo", ".subtitol", ".dek"):
        node = soup.select_one(selector)
        if node:
            subtitle = clean_text(node.get_text(" ", strip=True))
            if subtitle:
                break

    candidate_selectors = [
        "article",
        '[itemprop="articleBody"]',
        ".article-body",
        ".article__body",
        ".c-article-body",
        ".entry-content",
        ".noticia",
    ]
    body = ""
    for selector in candidate_selectors:
        container = soup.select_one(selector)
        if not container:
            continue
        paragraphs = container.select("p")
        text = "\n\n".join(clean_text(p.get_text(" ", strip=True)) for p in paragraphs if clean_text(p.get_text(" ", strip=True)))
        if len(text) > len(body):
            body = text

    if not body:
        paragraphs = soup.select("main p, .content p")
        body = "\n\n".join(clean_text(p.get_text(" ", strip=True)) for p in paragraphs if clean_text(p.get_text(" ", strip=True)))

    author = ""
    author_node = soup.select_one('[rel="author"], [itemprop="author"], .author, .authors')
    if author_node:
        author = clean_text(author_node.get_text(" ", strip=True))

    return {
        "title": title,
        "subtitle": subtitle,
        "body": body,
        "author": author,
        "language": "ca",
    }


def set_job(job_id, **values):
    with JOBS_LOCK:
        JOBS[job_id].update(values)
    callback = JOB_PROGRESS_CALLBACKS.get(job_id)
    if callback:
        callback(values)


def discover_sitemap_entries(sitemap_url, limit=2500):
    headers = {"User-Agent": "CoCoPress/1.0 (research corpus tool)"}
    response = requests.get(sitemap_url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "xml")
    entries = []

    sitemap_nodes = soup.select("sitemap loc")
    if sitemap_nodes:
        for sitemap_node in sitemap_nodes[:30]:
            child_url = clean_text(sitemap_node.get_text(" ", strip=True))
            if not child_url:
                continue
            try:
                child_response = requests.get(child_url, headers=headers, timeout=30)
                child_response.raise_for_status()
                child_soup = BeautifulSoup(child_response.content, "xml")
                for url_node in child_soup.select("url"):
                    loc = url_node.select_one("loc")
                    lastmod = url_node.select_one("lastmod")
                    if loc:
                        entries.append({
                            "link": clean_text(loc.get_text(" ", strip=True)),
                            "title": "",
                            "lastmod": clean_text(lastmod.get_text(" ", strip=True)) if lastmod else "",
                        })
                        if len(entries) >= limit:
                            return entries
            except requests.RequestException:
                continue
    else:
        for url_node in soup.select("url"):
            loc = url_node.select_one("loc")
            lastmod = url_node.select_one("lastmod")
            if loc:
                entries.append({
                    "link": clean_text(loc.get_text(" ", strip=True)),
                    "title": "",
                    "lastmod": clean_text(lastmod.get_text(" ", strip=True)) if lastmod else "",
                })
                if len(entries) >= limit:
                    break
    return entries


def discover_site_entries(source, limit=160):
    website = source.get("website")
    if not website:
        website = f"https://{source['domain']}/" if source.get("domain") else None
    if not website:
        return []

    headers = {"User-Agent": "CoCoPress/1.0 (research corpus tool)"}
    robots = robotparser.RobotFileParser()
    robots.set_url(urljoin(website, "/robots.txt"))
    try:
        robots.read()
    except Exception:
        pass
    if not robots.can_fetch(headers["User-Agent"], website):
        return []

    response = requests.get(website, headers=headers, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    base_domain = urlparse(response.url).netloc.lower().removeprefix("www.")
    candidates = []

    for anchor in soup.select("a[href]"):
        article_url = urljoin(response.url, anchor.get("href", "").strip())
        parsed = urlparse(article_url)
        article_domain = parsed.netloc.lower().removeprefix("www.")
        if parsed.scheme not in ("http", "https") or article_domain != base_domain:
            continue
        if any(fragment in parsed.path.lower() for fragment in (
            "/tag/", "/categoria/", "/category/", "/autor/", "/author/",
            "/search/", "/busca/", "/cerca/", "/page/",
        )):
            continue
        candidates.append(article_url)

    entries = []
    for article_url in list(dict.fromkeys(candidates))[:limit]:
        try:
            article_response = requests.get(article_url, headers=headers, timeout=12)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, "html.parser")

            published = None
            for selector in (
                'meta[property="article:published_time"]',
                'meta[name="date"]',
                'meta[name="pubdate"]',
                'time[datetime]',
            ):
                node = article_soup.select_one(selector)
                if not node:
                    continue
                value = node.get("content") or node.get("datetime") or node.get_text(" ", strip=True)
                if value:
                    try:
                        published = parsedate_to_datetime(value)
                    except (TypeError, ValueError, OverflowError):
                        try:
                            published = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        except (TypeError, ValueError):
                            published = None
                    if published:
                        break

            title = ""
            title_node = article_soup.select_one("h1")
            if title_node:
                title = clean_text(title_node.get_text(" ", strip=True))
            if not title and article_soup.title:
                title = clean_text(article_soup.title.get_text(" ", strip=True))

            entries.append({
                "link": article_url,
                "title": title,
                "published": published.isoformat() if published else None,
            })
            time.sleep(0.12)
        except requests.RequestException:
            continue
    return entries


def download_job(job_id, source_id, from_date, to_date, lemmatize=False):
    source = SOURCES[source_id]
    set_job(
        job_id,
        source_name=source["name"],
        source_key=source_id,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
    )
    start = datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc)
    entries = []

    if source.get("feed"):
        set_job(job_id, status="running", message="Llegint el canal RSS...")
        try:
            parsed_feed = feedparser.parse(source["feed"])
        except Exception as exc:
            parsed_feed = None
            set_job(job_id, status="running", message=f"RSS no disponible; provant alternatives... ({exc})")
        feed_entries = parsed_feed.entries if parsed_feed is not None else []

        if not feed_entries:
            set_job(job_id, status="running", message="RSS buit; provant el mapa del lloc...")
            try:
                if source.get("sitemap"):
                    feed_entries = discover_sitemap_entries(source["sitemap"])
                else:
                    set_job(job_id, status="running", message="No hi ha RSS ni sitemap; cercant enllaços a la web...")
                    feed_entries = discover_site_entries(source)
            except Exception as exc:
                set_job(job_id, status="error", message=f"No s'ha pogut llegir cap font de descoberta: {exc}")
                return
    elif source.get("premsa_forana"):
        set_job(
            job_id,
            status="done",
            message="La publicació està registrada, però encara no disposa d'un canal RSS o mapa del lloc verificat.",
            downloaded=0,
            skipped=0,
        )
        return
    else:
        set_job(job_id, status="running", message="Cercant notícies al mapa del lloc...")
        try:
            if source.get("sitemap"):
                feed_entries = discover_sitemap_entries(source["sitemap"])
            else:
                set_job(job_id, status="running", message="No hi ha RSS ni sitemap; cercant enllaços a la web...")
                feed_entries = discover_site_entries(source)
        except Exception as exc:
            set_job(job_id, status="error", message=f"No s'ha pogut llegir el mapa del lloc: {exc}")
            return

    for entry in feed_entries:
        published = entry_date(entry)
        if published and start <= published <= end:
            entries.append((published, entry))

    set_job(job_id, total=len(entries), message=f"S'han trobat {len(entries)} notícies al canal")
    if not entries:
        set_job(job_id, status="done", message="No s'han trobat notícies en aquest interval.")
        return

    archives = io.BytesIO()
    manifest = []
    skipped = []

    with zipfile.ZipFile(archives, "w", zipfile.ZIP_DEFLATED) as archive:
        for index, (published, entry) in enumerate(entries, start=1):
            article_url = entry.get("link", "")
            set_job(job_id, current=index, message=f"Processant {index}/{len(entries)}")

            try:
                title = clean_text(entry.get("title", ""))
                extracted = extract_article(source, article_url)
                if not extracted["title"]:
                    extracted["title"] = title
                if not extracted["body"]:
                    raise ValueError("No s'ha pogut extreure el cos de la notícia")

                stem = safe_stem(extracted["title"], article_url, index)
                text_parts = [extracted["title"]]
                if extracted["subtitle"]:
                    text_parts.append(extracted["subtitle"])
                text_parts.append(extracted["body"])

                metadata = {
                    "title": extracted["title"],
                    "subtitle": extracted["subtitle"],
                    "author": extracted["author"],
                    "publication_date": published.isoformat(),
                    "url": article_url,
                    "source": source["name"],
                    "language": extracted["language"],
                    "downloaded_at": datetime.now(timezone.utc).isoformat(),
                    "content_file": f"{stem}.txt",
                    "lemmatized": bool(lemmatize),
                }

                archive.writestr(f"txt/{stem}.txt", ("\n\n".join(text_parts)).encode("utf-8"))
                archive.writestr(
                    f"metadata/{stem}.json",
                    json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"),
                )
                if lemmatize:
                    set_job(job_id, message=f"Etiquetant {index}/{len(entries)}")
                    tagged_text = tag_text("\n\n".join(text_parts))
                    metadata["tagged_content_file"] = f"tagged/{stem}.txt"
                    archive.writestr(f"tagged/{stem}.txt", tagged_text.encode("utf-8"))
                    archive.writestr(
                        f"metadata/{stem}.json",
                        json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"),
                    )
                manifest.append(metadata)
            except Exception as exc:
                skipped.append({"url": article_url, "error": str(exc)})

            time.sleep(0.25)

    if manifest:
        csv_lines = ["title,subtitle,author,publication_date,url,source,language,content_file,lemmatized,tagged_content_file"]
        for item in manifest:
            row = [json.dumps(item.get(key, ""), ensure_ascii=False) for key in (
                "title", "subtitle", "author", "publication_date", "url", "source", "language",
                "content_file", "lemmatized", "tagged_content_file",
            )]
            csv_lines.append(",".join(row))
        with zipfile.ZipFile(archives, "a", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.csv", ("\ufeff" + "\n".join(csv_lines)).encode("utf-8"))
            archive.writestr(
                "skipped.json",
                json.dumps(skipped, ensure_ascii=False, indent=2).encode("utf-8"),
            )

    archives.seek(0)
    set_job(
        job_id,
        status="done",
        message=f"S'ha compilat un corpus de {len(manifest)} notícies.",
        downloaded=len(manifest),
        skipped=len(skipped),
        archive=archives.getvalue(),
    )


def download_many(job_id, source_ids, from_date, to_date, lemmatize=False):
    source_progress = {
        source_id: {"status": "queued", "current": 0, "total": 0}
        for source_id in source_ids
    }
    set_job(
        job_id,
        status="running",
        message="Preparant els mitjans seleccionats...",
        total=len(source_ids),
        current=0,
        downloaded=0,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        source_key="cocopress",
        lemmatize=lemmatize,
        source_progress=source_progress,
    )

    batch = io.BytesIO()
    created = 0
    with zipfile.ZipFile(batch, "w", zipfile.ZIP_DEFLATED) as batch_archive:
        for index, source_id in enumerate(source_ids, start=1):
            set_job(job_id, current=index, message=f"Preparant {index}/{len(source_ids)}: {SOURCES[source_id]['name']}")
            subjob_id = uuid.uuid4().hex
            with JOBS_LOCK:
                JOBS[subjob_id] = {
                    "status": "queued",
                    "message": "Preparant...",
                    "current": 0,
                    "total": 0,
                    "downloaded": 0,
                    "skipped": 0,
                }
            def sync_subjob(values):
                source_progress[source_id].update({
                    "status": values.get("status", "running"),
                    "current": values.get("current", source_progress[source_id]["current"]),
                    "total": values.get("total", source_progress[source_id]["total"]),
                    "message": values.get("message", ""),
                })
                set_job(job_id, source_progress=source_progress)

            JOB_PROGRESS_CALLBACKS[subjob_id] = sync_subjob
            download_job(subjob_id, source_id, from_date, to_date, lemmatize)
            JOB_PROGRESS_CALLBACKS.pop(subjob_id, None)
            with JOBS_LOCK:
                subjob = JOBS[subjob_id]
            if subjob.get("archive"):
                source_folder = re.sub(r"[^\w-]+", "-", SOURCES[source_id]["name"].casefold()).strip("-")
                with zipfile.ZipFile(io.BytesIO(subjob["archive"]), "r") as source_archive:
                    for member in source_archive.namelist():
                        batch_archive.writestr(
                            f"{source_folder}/{member}",
                            source_archive.read(member),
                        )
                created += subjob.get("downloaded", 0)

    batch.seek(0)
    set_job(
        job_id,
        status="done",
        message=f"Paquet preparat amb {len(source_ids)} mitjans.",
        downloaded=created,
        archive=batch.getvalue(),
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


def get_territorial_sources():
    territories = {
        "Catalunya": [],
        "País Valencià": [],
        "Illes Balears": [],
        "Catalunya del Nord": [],
        "Andorra": [],
        "l'Alguer": [],
    }

    deduplicated_sources = {}
    for key, source in SOURCES.items():
        name_key = re.sub(r"\s+", " ", source["name"].casefold()).strip()
        existing = deduplicated_sources.get(name_key)
        if existing:
            existing_key, existing_source = existing
            existing_downloadable = bool(existing_source.get("feed") or existing_source.get("sitemap"))
            downloadable = bool(source.get("feed") or source.get("sitemap"))
            if downloadable and not existing_downloadable:
                deduplicated_sources[name_key] = (key, source)
        else:
            deduplicated_sources[name_key] = (key, source)

    for name_key, (key, source) in deduplicated_sources.items():
        name = source["name"].casefold()
        domain = source.get("domain", "").casefold()
        explicit_territory = source.get("territory")
        if explicit_territory in territories:
            territory = explicit_territory
        elif key in ("diarilaveu", "eltemps", "sao", "tresdeu", "barcella", "elpenjoll", "lafalzia"):
            territory = "País Valencià"
        elif key.startswith("pf-") or any(word in name for word in (
            "mallorca", "balears", "ib3", "sóller", "inca", "felanitx",
            "pollença", "llucmajor", "manacor", "capdepera"
        )) or "balears" in domain:
            territory = "Illes Balears"
        elif "andorra" in name or domain.endswith(".ad"):
            territory = "Andorra"
        elif "alguer" in name or "lalguer" in key:
            territory = "l'Alguer"
        elif "catalunya nord" in name or "catnord" in key:
            territory = "Catalunya del Nord"
        elif domain.endswith(".es") and any(word in name for word in (
            "valència", "valencià", "levant", "superdeporte"
        )) or ".val." in domain:
            territory = "País Valencià"
        else:
            territory = "Catalunya"
        territories[territory].append((key, source))

    return {name: values for name, values in territories.items() if values}


@app.route("/")
def index():
    return render_template(
        "index.html",
        sources=SOURCES,
        territorial_sources=get_territorial_sources(),
    )


@app.post("/api/download")
def start_download():
    source_ids = list(dict.fromkeys(request.form.getlist("source")))
    lemmatize = request.form.get("lemmatize") == "1"
    if not source_ids:
        return jsonify({"error": "Selecciona almenys un digital"}), 400
    unknown = [source_id for source_id in source_ids if source_id not in SOURCES]
    if unknown:
        return jsonify({"error": "Digital desconegut"}), 400

    try:
        from_date = date.fromisoformat(request.form["from"])
        to_date = date.fromisoformat(request.form["to"])
    except (KeyError, ValueError):
        return jsonify({"error": "Interval de dates invàlid"}), 400
    if from_date > to_date:
        return jsonify({"error": "La data inicial ha de ser anterior a la final"}), 400

    job_id = uuid.uuid4().hex
    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": "queued",
            "message": "Preparant la descàrrega...",
            "current": 0,
            "total": 0,
            "downloaded": 0,
            "skipped": 0,
            "lemmatize": lemmatize,
        }

    thread = threading.Thread(
        target=download_many,
        args=(job_id, source_ids, from_date, to_date, lemmatize),
        daemon=True,
    )
    thread.start()
    return jsonify({"job_id": job_id})


@app.get("/api/jobs/<job_id>")
def job_status(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Tasca desconeguda"}), 404
    return jsonify({key: value for key, value in job.items() if key != "archive"})


@app.get("/api/jobs/<job_id>/download")
def job_download(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Tasca desconeguda"}), 404
    if job["status"] != "done" or "archive" not in job:
        return jsonify({"error": "La descàrrega encara no està preparada"}), 409
    from_date = job.get("from_date", "").replace("-", "_")
    to_date = job.get("to_date", "").replace("-", "_")
    source_key = re.sub(r"[^\w-]+", "-", job.get("source_key", "premsa").casefold())
    download_name = f"{from_date}-{to_date}_{source_key}.zip"
    return send_file(
        io.BytesIO(job["archive"]),
        mimetype="application/zip",
        as_attachment=True,
        download_name=download_name,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "7860")), debug=True)
