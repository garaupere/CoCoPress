# CoCoPress

**Compilació de Corpus de Premsa Escrita**

CoCoPress és una aplicació d'escriptori local per a Windows, macOS i Linux.
No necessita servidor públic ni compte d'usuari.

## Instal·lació i ús

### Windows

Podeu baixar i executar:

- `CoCoPress Setup 1.0.0.exe`: instal·lador NSIS.
- `CoCoPress 1.0.0.exe`: versió portable.

Actualment aquests fitxers s'han generat localment i encara no formen part
d'una publicació oficial al repositori.

Ambdós executables inclouen el runtime Python i les dependències necessàries,
inclòs el model català de Stanza per a l'opció opcional de lematització i POS tagging.

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
Windows i macOS poden mostrar avisos quan no hi ha un certificat comercial de signatura.

## Utilització

1. Trieu un o diversos mitjans i un interval de dates.
2. Trieu el directori local on voleu guardar el corpus.
3. Activeu opcionalment la lematització i el POS tagging amb Stanza.
4. Compilau el corpus.

Cada mitjà se guarda en una carpeta independent.

## Sortida

La compilació genera fitxers UTF-8:

- `txt/*.txt`: text original de cada notícia.
- `metadata/*.json`: metadades en JSON.
- `metadata/*.csv`: metadades en CSV compatibles amb AntConc.
- `tagged/*.txt`: versió etiquetada `paraula_POS_lemma`.
- `manifest.csv`: índex global amb `filename` i `doc_id`.

Les metadades CSV tenen una fila per notícia i una capçalera que inclou
`filename`, `doc_id`, `title`, `author`, `publication_date`, `url`, `source`
i `language`. El camp `filename` coincideix exactament amb el nom del TXT associat.

## Descobriment de notícies

El procés prioritza aquest ordre:

1. Canal RSS.
2. Sitemap XML.
3. Crawling controlat de la portada i els enllaços d'article.

El crawling respecta `robots.txt`, limita el nombre d'adreces i només segueix
enllaços del mateix domini.
