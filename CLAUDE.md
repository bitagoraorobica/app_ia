# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Cos'è questo progetto

AI Compass (repo pubblico `bitagoraorobica/app_ia`, branch `main`) è un aggregatore automatico di contenuti
divulgativi sull'intelligenza artificiale per BitAgorà Orobica srl. Legge feed RSS + una lista curata a mano,
filtra e classifica gli articoli, genera un sito statico (`index.html`) e lo pubblica su GitHub Pages.

- Sito pubblicato: https://bitagoraorobica.github.io/app_ia/
- Gira su **GitHub Actions** (`.github/workflows/aggiorna.yml`): ogni giorno alle 05:00 UTC, a ogni push che
  tocca CSV/script/logo/workflow, e a mano con "Run workflow". Nessun PC coinvolto, nessun token personale.

## Comandi

    pip install -r requirements.txt
    python aggiorna_feed.py     # pipeline completa: CSV + feed RSS → JSON → index.html, aggiorna already_seen
    python generate_html.py     # rigenera solo index.html da ai-compass-feed.json

Non ci sono test automatici, linter o build step.

Il repo è pubblico: i commit vanno fatti con l'email noreply di GitHub, non con quella aziendale. Dopo un
clone su un PC nuovo:

    git config user.email "223838967+bitagoraorobica@users.noreply.github.com"

Actions (al commit esatto) e pacchetti Python (alla versione esatta, comprese le dipendenze indirette) sono
fissati di proposito; li aggiorna Dependabot (`.github/dependabot.yml`) con una pull request al mese. Le
pull request non fanno partire il workflow, che parte solo dopo il merge su `main`. Una run locale di `aggiorna_feed.py` modifica lo stato
(`data/already_seen.txt`, `ai-compass-feed.json`): per provare senza sporcare il repo, lanciarla su una copia.

## Architettura

`aggiorna_feed.py` (orchestratore):

1. **Voci manuali** — `data/voci_manuali.csv` (colonne Date/Title/Description/Category/Link/Source), sempre
   incluse, senza filtri di punteggio.
2. **Archivio** — dal `ai-compass-feed.json` precedente tiene le voci RSS degli ultimi `max_age_days` (30)
   giorni. Senza questo passaggio ogni giro mostrerebbe solo gli articoli nuovi di quel giro.
3. **Raccolta RSS** — itera `rss_feeds`; per ogni voce scarta: link non http/https o fuori dal dominio del feed
   (`dominio_base`: ultimi due livelli, es. `blog.n8n.io` → `n8n.io`; una fonte nuova i cui articoli stanno su
   un altro dominio verrebbe scartata in blocco), link già in `data/already_seen.txt`, più vecchia
   di 30 giorni, score < `min_score_required` (5). Lo score somma i pesi del dizionario `keywords` trovati in
   titolo+descrizione (arXiv −1): le keyword di 1-3 lettere ("ai", "gpt", "llm") solo come parola intera, le
   altre a inizio parola — mai come sottostringa, altrimenti "ai" scatta in "said", "email", "OpenAI". Solo per i domini fuori da `skip_check_domains` fa una
   HEAD request di verifica. Max `max_items_per_feed` (5) voci accettate per fonte. Categoria
   `Paper`/`Automation`/`News` da dominio; per le News badge ⭐ da 8 punti e 🔥 da 10. I summary vengono ridotti a testo semplice.
4. **Output** — scrive `ai-compass-feed.json` (manuali + archivio + nuove, per data decrescente), richiama
   `generate_html.main()`, aggiunge in append i nuovi link a `data/already_seen.txt`.

Le fonti tolte perché senza feed RSS sono elencate in un commento sotto `rss_feeds`: prima di
reinserirne una, verificare che il feed esista davvero.

`generate_html.py` rigenera da zero `index.html` (CSS/JS inline, dati inline come JSON, filtri lato client per
categoria/fonte/periodo, ricerca, dark mode). Le opzioni dei filtri categoria e fonte derivano dai dati.

Il workflow ha due job: `aggiorna` (esegue lo script, committa JSON/HTML/already_seen come
`github-actions[bot]`, prepara `_site/` con `index.html`, `ai-compass-feed.json`, `logo.png`) e `pubblica`
(`actions/deploy-pages`). GitHub Pages è configurato con sorgente "GitHub Actions", non "deploy from branch":
i push fatti con `GITHUB_TOKEN` non farebbero ripartire la build da branch.
