# CoCoPress

**Compilació de Corpus de Premsa Escrita**

CoCoPress és una aplicació d'escriptori local per a Windows, macOS i Linux.
No necessita servidor públic ni compte d'usuari.

## Instal·lació i ús

### Windows

Podeu baixar i executar:

- `CoCoPress Setup 1.0.0.exe`: instal·lador NSIS.
- `CoCoPress 1.0.0.exe`: versió portable.

### macOS i Linux

- macOS: `.dmg` i `.zip` sense signatura Apple.

Aquests paquets es generen automàticament a GitHub Actions amb l'etiqueta `v1.0.0`
i les versions posteriors. macOS pot demanar permisos addicionals quan l'app no té
signatura Apple.

Els executables inclouen el runtime Python i les dependències necessàries,
també inclouen el model català de Stanza per a l'opció de lematització i POS-tagging.

### Compilació des del codi

És necessari tenir Node.js i npm:

```powershell
npm install
npm run setup-python
npm start
```

Per generar instal·ladors locals:

```powershell
npm run dist:win
npm run dist:mac
npm run dist:linux
```

Els paquets macOS i Linux han de generar-se al sistema corresponent o mitjançant CI.
Windows i macOS poden mostrar una alerta d'instal·lació, perquè no hi ha un certificat comercial de signatura.

## Utilització

1. Triau un o diversos mitjans i un interval de dates.
2. Triau el directori local on voleu guardar el corpus.
3. Activau opcionalment la lematització i el POS-tagging amb Stanza.
4. Compilau el corpus.

Cada mitjà es guarda en una carpeta independent.

## Sortida

La compilació genera fitxers UTF-8:

- `txt/*.txt`: text original de cada notícia.
- `metadata/*.json`: metadades en JSON.
- `metadata/*.csv`: metadades en CSV.
- `tagged/*.txt`: versió etiquetada `paraula_POS_lemma` (compatible amb AntConc).
- `manifest.csv`: índex global amb `filename` i `doc_id`.

Les metadades CSV tenen una fila per notícia i una capçalera que inclou
`filename`, `doc_id`, `title`, `author`, `publication_date`, `url`, `source`
i `language`. El camp `filename` coincideix exactament amb el nom del TXT associat.

## Descobriment de notícies

El procés prioritza aquest ordre per obtenir notícies dels mitjans:

1. Canal RSS.
2. Sitemap XML.
3. Crawling controlat de la portada i els enllaços d'articles.

