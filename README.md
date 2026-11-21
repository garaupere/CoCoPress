---
title: CoCoPress
emoji: "\U0001F4DA"
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
python_version: "3.11"
---

# CoCoPress

**Compilació de Corpus de Premsa Escrita**

## Aplicació d'escriptori local

CoCoPress inclou una interfície Electron independent del servidor web. Reutilitza
el catàleg i els descobridors RSS/sitemap/crawler de `app.py`.

En una màquina de desenvolupament:

```text
npm install
npm run setup-python
npm start
```

Els paquets d’instal·lació es poden generar sense publicar-los:

```text
npm run dist:win
npm run dist:mac
npm run dist:linux
```

Per empaquetar Stanza i les seves dependències, executeu `npm run setup-python`
abans de construir. En desenvolupament també pot utilitzar un Python 3 disponible
al PATH. La configuració de l’instal·lador no publica, signa ni puja els fitxers.

Aplicació web per compilar corpus de premsa escrita i mitjans digitals en català.
Cada notícia es desa com a fitxer TXT i té un fitxer JSON associat amb títol,
subtítol, autor, data, URL, font i idioma. El ZIP inclou també `manifest.csv`
i `skipped.json`.

Les metadades són compatibles amb AntConc: `manifest.csv` i
`metadata/*.csv` contenen les columnes `filename` i `doc_id`, i `filename`
identifica exactament el TXT associat. El codificació és UTF-8 i el separador
principal és la coma. Els JSON continuen disponibles com a còpia de metadades.

Si s'activa el processament lingüístic, també es genera `tagged/*.txt`
amb Stanza i les etiquetes UD-UPOS seguint `paraula_POS_lemma`.

El descobriment prioritza RSS i mapes del lloc. Si no n'hi ha cap,
l'aplicació pot cercar enllaços d'articles a la portada amb límits de volum,
filtre del domini i respectant `robots.txt`.

## Desplegament a Hugging Face Spaces

L'aplicació està preparada per al SDK Docker de Hugging Face Spaces i escolta
al port `7860` per defecte. Si Spaces proporciona la variable `PORT`, el Dockerfile
l'utilitza també.

Python està fixat en la versió 3.11 (imatge Docker
`python:3.11.10-slim-bookworm`).

El punt de salut es troba a `/health` i retorna `{"status":"ok"}`.

### Execució local amb Docker

```text
docker build -t cocopress .
docker run --rm -p 7860:7860 -e PORT=7860 cocopress
```

## Altres plataformes PaaS

La configuració següent és una opció genèrica per plataformes PaaS que
exposen un procés web:

```text
gunicorn app:app --bind 0.0.0.0:${PORT:-7860} --timeout 600
```

Cal tenir en compte que les tasques llargues i els models Stanza necessiten
memòria i processos persistents. Un servidor WSGI no és adequat per a tasques
massives sense una cua de treballadors i emmagatzematge persistent.

### Compatibilitat opcional amb Render

`render.yaml` i `Procfile` es conserven com a configuració opcional i
heretada; Hugging Face Spaces no les necessita. Si no feu servir Render,
ignoreu aquests fitxers.

1. Obriu el repositori a Render i seleccioneu «New > Blueprint».
2. Indiqueu el repositori `garaupere/CoCoPress`.
3. Render crearà el servei web usant `Dockerfile`.
4. El pla gratuït pot suspendre processos i no garanteix persistència:
   els ZIP i les tasques actualment són en memòria.

## Desplegament gratuït a PythonAnywhere

PythonAnywhere executa una aplicació WSGI sense Docker. Aquesta configuració
és adequada per a proves i ús moderat; el pla gratuït limita CPU, processos,
memòria i connexions externes.

1. Creeu un compte gratuït i obriu una consola Bash.
2. Cloneu el repositori:

```bash
git clone https://github.com/garaupere/CoCoPress.git
cd CoCoPress
bash pythonanywhere_setup.sh
```

3. Creeu una aplicació web Flask des del panell «Web».
4. Trieu l’intèrpret Python 3.11 i editeu el WSGI perquè importi
   `pythonanywhere_wsgi.py`.
5. Configureu el virtualenv com
   `/home/<usuari>/CoCoPress/venv`.
6. Establiu el directori de l’aplicació com
   `/home/<usuari>/CoCoPress`.
7. Recàrregueu l’aplicació des del botó «Reload».

Stanza pot consumir la major part de la memòria disponible al pla gratuït.
Per a un primer desplegament, és recomanable deixar el POS tagging desactivat
fins comprovar que el servei inicia amb estabilitat.
## Aplicació d'escriptori local

CoCoPress també es pot executar com a aplicació local Electron per a Windows,
macOS i Linux. No necessita Flask ni servidor públic.

```powershell
npm install
npm run setup-python
npm start
```

Per generar instal·ladors:

```powershell
npm run dist:win
npm run dist:mac
npm run dist:linux
```

La compilació macOS i Linux ha de fer-se al sistema o per una CI que executi
aquell sistema. Windows i macOS poden mostrar avisos si no hi ha certificat
comercial de signatura.

