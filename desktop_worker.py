import csv
import io
import json
import re
import sys
import uuid
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

import app as cocopress


def emit(event, **values):
    print(json.dumps({"event": event, **values}, ensure_ascii=False), flush=True)


def catalog():
    groups = cocopress.get_territorial_sources()
    sources = []
    for territory, entries in groups.items():
        for key, source in entries:
            sources.append({
                "id": key,
                "name": source["name"],
                "territory": territory,
                "feed": bool(source.get("feed")),
                "sitemap": bool(source.get("sitemap")),
                "crawler": not bool(source.get("feed") or source.get("sitemap")),
            })
    emit("catalog", sources=sources)


def safe_folder(name):
    value = re.sub(r"[^\w -]+", "-", name, flags=re.UNICODE).strip("-. ")
    return re.sub(r"\s+", " ", value)[:120] or "Mitja"


def write_medium(output_root, medium_name, archive_bytes):
    medium_dir = output_root / safe_folder(medium_name)
    text_dir = medium_dir / "txt"
    metadata_dir = medium_dir / "metadata"
    tagged_dir = medium_dir / "tagged"
    text_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    skipped = []
    with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
        for member in archive.namelist():
            data = archive.read(member)
            if member.startswith("txt/") or member.startswith("metadata/") or member.startswith("tagged/"):
                target = medium_dir / member
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            elif member == "manifest.csv":
                manifest_text = data.decode("utf-8-sig")
            elif member == "skipped.json":
                skipped = json.loads(data.decode("utf-8"))

    metadata_records = sorted(metadata_dir.glob("*.json"))
    manifest = [json.loads(record.read_text(encoding="utf-8")) for record in metadata_records]
    manifest_path = medium_dir / "manifest.csv"
    fields = [
        "title", "subtitle", "author", "publication_date", "url", "source",
        "language", "content_file", "lemmatized", "tagged_content_file",
    ]
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in manifest:
            writer.writerow({key: record.get(key, "") for key in fields})

    (medium_dir / "skipped.json").write_text(
        json.dumps(skipped, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if not tagged_dir.exists():
        tagged_dir.mkdir()
    return len(manifest), len(skipped)


def run(payload):
    source_ids = list(dict.fromkeys(payload.get("sources", [])))
    from_date = cocopress.date.fromisoformat(payload["from"])
    to_date = cocopress.date.fromisoformat(payload["to"])
    lemmatize = bool(payload.get("lemmatize"))
    output_dir = Path(payload["outputDir"]).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    unknown = [key for key in source_ids if key not in cocopress.SOURCES]
    if unknown:
        raise ValueError("Digital desconegut: " + ", ".join(unknown))
    if from_date > to_date:
        raise ValueError("La data inicial ha de ser anterior a la final")
    if not source_ids:
        raise ValueError("Selecciona almenys un digital")

    if lemmatize:
        emit("status", message="Comprovant i preparant Stanza...")
        try:
            cocopress.get_stanza_pipeline()
        except Exception as exc:
            raise RuntimeError(f"No s'ha pogut preparar Stanza: {exc}") from exc

    emit("started", total=len(source_ids))
    downloaded = 0
    skipped = 0
    all_records = []

    for index, source_id in enumerate(source_ids, start=1):
        source = cocopress.SOURCES[source_id]
        emit("source", index=index, total=len(source_ids), sourceId=source_id,
             name=source["name"], status="running")

        job_id = uuid.uuid4().hex
        with cocopress.JOBS_LOCK:
            cocopress.JOBS[job_id] = {
                "status": "queued", "message": "Preparant...", "current": 0,
                "total": 0, "downloaded": 0, "skipped": 0,
            }

        def progress(values):
            safe_values = {
                key: value
                for key, value in values.items()
                if not isinstance(value, (bytes, bytearray, io.BytesIO))
            }
            emit("progress", sourceId=source_id, name=source["name"], **safe_values)

        cocopress.JOB_PROGRESS_CALLBACKS[job_id] = progress
        try:
            cocopress.download_job(job_id, source_id, from_date, to_date, lemmatize)
        finally:
            cocopress.JOB_PROGRESS_CALLBACKS.pop(job_id, None)

        with cocopress.JOBS_LOCK:
            job = cocopress.JOBS[job_id].copy()

        if job.get("status") == "error":
            emit("source", index=index, total=len(source_ids), sourceId=source_id,
                 name=source["name"], status="error", message=job.get("message", "Error"))
            skipped += 1
            continue
        archive_bytes = job.get("archive")
        if archive_bytes:
            source_count, source_skipped = write_medium(output_dir, source["name"], archive_bytes)
            downloaded += source_count
            skipped += source_skipped
        emit("source", index=index, total=len(source_ids), sourceId=source_id,
             name=source["name"], status="done", downloaded=downloaded)

    emit("done", outputDir=str(output_dir), downloaded=downloaded, skipped=skipped)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("catalog", "run"):
        raise SystemExit("Usage: desktop_worker.py catalog|run")
    action = sys.argv[1]
    if action == "catalog":
        catalog()
        return
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    run(payload)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        emit("error", message=str(exc))
        raise
