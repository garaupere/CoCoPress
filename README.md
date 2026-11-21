# CoCoPress

**Compilació de Corpus de Premsa Escrita**

Aplicació web per compilar corpus de premsa escrita i mitjans digitals en català.
Cada notícia es desa com a fitxer TXT i té un fitxer JSON associat amb títol,
subtítol, autor, data, URL, font i idioma. El ZIP inclou també `manifest.csv`
i `skipped.json`.

Si s'activa el processament lingüístic, també es genera `tagged/*.txt`
amb Stanza i les etiquetes UD-UPOS seguint `paraula_POS_lemma`.

El descobriment prioritza RSS i mapes del lloc. Si no n'hi ha cap,
l'aplicació pot cercar enllaços d'articles a la portada amb límits de volum,
filtre del domini i respectant `robots.txt`.

## Desplegament web

L'aplicació és compatible amb plataformes PaaS que executen un procés web:

```text
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300
```

Cal tenir en compte que les tasques llargues i els models Stanza necessiten
memòria i processos persistents. Un servidor WSGI no és adequat per a tasques
massives sense una cua de treballadors i emmagatzematge persistent.

### Desplegament a Render

La configuració `render.yaml` desplega l'aplicació amb Docker:

1. Obriu el repositori a Render i seleccioneu «New > Blueprint».
2. Indiqueu el repositori `garaupere/CoCoPress`.
3. Render crearà el servei web usant `Dockerfile`.
4. El pla gratuït pot suspendre processos i no garanteix persistència:
   els ZIP i les tasques actualment són en memòria.
