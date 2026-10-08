# Genera index.html a partire da ai-compass-feed.json.
# Richiamato da aggiorna_feed.py; si può lanciare anche da solo per rigenerare la pagina.
# Qui si costruisce solo il markup: stile e filtri stanno in static/style.css e static/app.js.

import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from html import escape
from urllib.parse import urlparse

try:
    from zoneinfo import ZoneInfo
    FUSO = ZoneInfo("Europe/Rome")
except Exception:  # database dei fusi orari assente: si ripiega su UTC
    FUSO = timezone.utc

INPUT_JSON = "ai-compass-feed.json"
OUTPUT_HTML = "index.html"
SITE_URL = "https://bitagoraorobica.github.io/app_ia/"

MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]

# Nome mostrato per ogni categoria (il valore nel JSON resta quello originale) e ordine nei filtri
ETICHETTE_CATEGORIE = {"News": "News", "Paper": "Paper", "Automation": "Automazione", "Course": "Corsi", "Tool": "Strumenti"}
ORDINE_CATEGORIE = ["News", "Paper", "Automation", "Course", "Tool"]

# I badge emoji del JSON diventano etichette; 📜 e 🔁 ripetono la categoria e non si mostrano
ETICHETTE_BADGE = {"🔥": ("In evidenza", "flag flag-hot"), "⭐": ("Da leggere", "flag")}

PREFISSO_ARXIV = re.compile(r"^arXiv:\S+\s+Announce Type:\s*\S+\s+Abstract:\s*", re.IGNORECASE)

ICONA_CERCA = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
)


def pulisci_descrizione(testo):
    testo = PREFISSO_ARXIV.sub("", testo or "")
    return re.sub(r"\s*\[\.\.\.\]$", "", testo).strip()


def link_sicuro(link):
    return link if urlparse(link or "").scheme in ("http", "https") else "#"


def data_breve(iso):
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{d.day} {MESI[d.month - 1]} {d.year}"


def etichetta_categoria(categoria):
    return ETICHETTE_CATEGORIE.get(categoria, categoria)


def ordina_categorie(categorie):
    return sorted(categorie, key=lambda c: (ORDINE_CATEGORIE.index(c) if c in ORDINE_CATEGORIE else len(ORDINE_CATEGORIE), c))


def versione(percorso):
    """Impronta del file, aggiunta all'URL: i browser riscaricano CSS e JS solo quando cambiano."""
    with open(percorso, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


def scheda(e):
    descrizione = pulisci_descrizione(e.get("description", ""))
    testo_ricerca = f'{e["title"]} {descrizione} {e["source"]}'.lower()
    badge = ETICHETTE_BADGE.get(e.get("badge", ""))
    flag = f'<span class="{badge[1]}">{badge[0]}</span>' if badge else ""
    paragrafo = f"\n        <p>{escape(descrizione)}</p>" if descrizione else ""
    return f"""      <article class="card" data-category="{escape(e["category"])}" data-source="{escape(e["source"])}" data-date="{escape(e["date"])}" data-text="{escape(testo_ricerca)}">
        <div class="card-top"><span class="tag">{escape(etichetta_categoria(e["category"]))}</span>{flag}</div>
        <h3><a href="{escape(link_sicuro(e["link"]))}" target="_blank" rel="noopener">{escape(e["title"])}</a></h3>{paragrafo}
        <div class="card-meta"><span class="source">{escape(e["source"])}</span><span aria-hidden="true">·</span><time datetime="{escape(e["date"])}" data-relative>{escape(data_breve(e["date"]))}</time><span class="arrow" aria-hidden="true">↗</span></div>
      </article>"""


def voce_redazione(e):
    descrizione = pulisci_descrizione(e.get("description", ""))
    return f"""      <div class="pick">
        <div>
          <p class="eyebrow">Dalla redazione</p>
          <h2><a href="{escape(link_sicuro(e["link"]))}" target="_blank" rel="noopener">{escape(e["title"])}</a></h2>
          <p>{escape(descrizione)}</p>
        </div>
        <span class="pick-cta" aria-hidden="true">Leggi ↗</span>
      </div>"""


def build_html(all_entries, generato=None):
    generato = generato or datetime.now(FUSO)
    manuali = [e for e in all_entries if e.get("manual")]
    # Per data, dal più recente; nello stesso giorno prima "In evidenza" e "Da leggere", poi News,
    # Automazione e Paper (il sito è divulgativo: i paper restano, ma non aprono la giornata)
    priorita_badge = {"🔥": 0, "⭐": 1}
    priorita_categoria = {"News": 0, "Automation": 1, "Paper": 2}
    articoli = sorted(
        (e for e in all_entries if not e.get("manual")),
        key=lambda e: (priorita_badge.get(e.get("badge"), 2), priorita_categoria.get(e["category"], 1)),
    )
    articoli.sort(key=lambda e: e["date"], reverse=True)

    per_categoria = Counter(e["category"] for e in articoli)
    per_fonte = Counter(e["source"] for e in articoli)

    chips = [f'<button type="button" class="chip" data-category="" aria-pressed="true">Tutti<span class="count">{len(articoli)}</span></button>']
    chips += [
        f'<button type="button" class="chip" data-category="{escape(c)}" aria-pressed="false">'
        f'{escape(etichetta_categoria(c))}<span class="count">{per_categoria[c]}</span></button>'
        for c in ordina_categorie(per_categoria)
    ]
    fonti = "".join(
        f'\n            <option value="{escape(s)}">{escape(s)} ({n})</option>' for s, n in sorted(per_fonte.items(), key=lambda x: x[0].lower())
    )
    redazione = ""
    if manuali:
        redazione = '    <section class="picks" aria-label="Dalla redazione">\n' + "\n".join(voce_redazione(e) for e in manuali) + "\n    </section>\n\n"
    chips_html = "\n      ".join(chips)
    schede_html = "\n".join(scheda(e) for e in articoli)
    aggiornato = f"{generato.day} {MESI[generato.month - 1]}, {generato:%H:%M}"
    descrizione_sito = (
        "Articoli, paper e video sull'intelligenza artificiale selezionati ogni giorno da BitAgorà Orobica "
        "tra laboratori di ricerca, aziende dell'IA e strumenti di automazione."
    )

    return f"""<!DOCTYPE html>
<html lang="it" class="no-js">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Compass · BitAgorà Orobica</title>
  <meta name="description" content="{escape(descrizione_sito)}">
  <link rel="canonical" href="{SITE_URL}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="BitAgorà Orobica">
  <meta property="og:locale" content="it_IT">
  <meta property="og:title" content="AI Compass · la bussola sull'intelligenza artificiale">
  <meta property="og:description" content="{escape(descrizione_sito)}">
  <meta property="og:url" content="{SITE_URL}">
  <meta name="theme-color" content="#121214">
  <link rel="icon" type="image/png" sizes="32x32" href="static/favicon-32.png">
  <link rel="apple-touch-icon" href="static/apple-touch-icon.png">
  <link rel="preload" href="static/fonts/inter-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="static/fonts/space-grotesk-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="static/style.css?v={versione("static/style.css")}">
  <script>document.documentElement.classList.replace('no-js', 'js');</script>
  <script src="static/app.js?v={versione("static/app.js")}" defer></script>
</head>
<body>
  <header class="site-header">
    <div class="wrap bar">
      <a class="brand" href="./" aria-label="AI Compass, torna all'inizio">
        <img src="static/logo-white.png" alt="Gruppo BitAgorà Smart Network" width="87" height="40">
        <span class="brand-name">AI Compass</span>
      </a>
      <a class="header-link" href="https://www.bitagoraorobica.it" target="_blank" rel="noopener">Visita bitagoraorobica.it ↗</a>
    </div>
  </header>

  <section class="hero">
    <div class="glow" aria-hidden="true"></div>
    <div class="wrap">
      <p class="eyebrow">Selezione curata da BitAgorà Orobica</p>
      <h1>La bussola sull'intelligenza artificiale</h1>
      <p class="subtitle">Ogni mattina raccogliamo in automatico articoli, paper e video da decine di fonti (laboratori di ricerca, aziende dell'IA, strumenti di automazione) e teniamo i più pertinenti degli ultimi 30 giorni.</p>
      <dl class="stats">
        <div><dt>contenuti</dt><dd>{len(articoli)}</dd></div>
        <div><dt>fonti attive</dt><dd>{len(per_fonte)}</dd></div>
        <div><dt>ultimo aggiornamento</dt><dd>{aggiornato}</dd></div>
      </dl>
    </div>
  </section>

  <main class="wrap">
{redazione}    <div class="toolbar">
      <div class="search">
        <label class="sr-only" for="search">Cerca</label>
        {ICONA_CERCA}
        <input id="search" type="search" placeholder="Cerca per titolo, argomento o fonte…" autocomplete="off">
      </div>
      <div class="select">
        <label class="sr-only" for="source">Fonte</label>
        <select id="source">
          <option value="">Tutte le fonti</option>{fonti}
        </select>
      </div>
      <div class="select">
        <label class="sr-only" for="days">Periodo</label>
        <select id="days">
          <option value="">Tutte le date</option>
          <option value="3">Ultimi 3 giorni</option>
          <option value="7">Ultima settimana</option>
          <option value="15">Ultimi 15 giorni</option>
        </select>
      </div>
    </div>

    <div class="chips" role="group" aria-label="Categoria">
      {chips_html}
    </div>

    <p class="results" aria-live="polite"><span><strong id="count">{len(articoli)}</strong> <span id="count-label">contenuti</span></span><button type="button" id="reset" class="link-button" hidden>Azzera filtri</button></p>

    <div class="grid">
{schede_html}
    </div>

    <div class="empty" id="empty" hidden>
      <h2>Nessun contenuto trovato</h2>
      <p>Prova con un'altra parola o allarga i filtri.</p>
      <button type="button" id="empty-reset" class="link-button">Azzera filtri</button>
    </div>
  </main>

  <footer class="site-footer">
    <div class="wrap footer-grid">
      <img src="static/logo-white.png" alt="Gruppo BitAgorà Smart Network" width="74" height="34" loading="lazy">
      <p>AI Compass è una selezione automatica di BitAgorà Orobica srl. Titoli ed estratti appartengono ai rispettivi autori: ogni scheda rimanda alla fonte originale.</p>
      <nav class="footer-links" aria-label="BitAgorà Orobica">
        <a href="https://www.bitagoraorobica.it" target="_blank" rel="noopener">Sito</a>
        <a href="https://newsletter.bitagoraorobica.it" target="_blank" rel="noopener">Newsletter</a>
      </nav>
    </div>
  </footer>
</body>
</html>
"""


def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        all_entries = json.load(f)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(build_html(all_entries))
    print(f"✅ {OUTPUT_HTML} generato ({len(all_entries)} voci).")


if __name__ == "__main__":
    main()
