import html
import json
import re


def main():
    with open("premsacomarcal.html", "r", encoding="utf-8") as handle:
        source = handle.read()

    pattern = r'/publicacio/([^"\s]+)[^>]*>([^<]+)</a><br />([^"<]+)'
    publications = {}
    for slug, name, location in re.findall(pattern, source):
        publications[slug] = {
            "name": html.unescape(name).strip(),
            "location": html.unescape(location).strip(),
            "slug": slug,
            "website": f"https://www.premsacomarcal.cat/publicacio/{slug}",
        }

    result = list(publications.values())
    with open("premsacomarcal_sources.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(len(result))


if __name__ == "__main__":
    main()
