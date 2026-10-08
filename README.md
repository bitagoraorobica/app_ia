# app_ia, una bussola automatica tra i contenuti divulgativi sul tema dell'intelligenza artificiale

**AI Compass** di [BitAgorà Orobica srl](https://www.bitagoraorobica.it) raccoglie ogni giorno articoli,
paper e video sull'IA da una quarantina di feed RSS, li filtra per pertinenza e li pubblica su
https://bitagoraorobica.github.io/app_ia/

## Come funziona

Ogni mattina il workflow [`aggiorna.yml`](.github/workflows/aggiorna.yml) esegue `aggiorna_feed.py`, che:

1. legge le voci aggiunte a mano in [`data/voci_manuali.csv`](data/voci_manuali.csv);
2. scarica i feed RSS, scarta i link già visti ([`data/already_seen.txt`](data/already_seen.txt)), quelli più
   vecchi di 30 giorni e quelli con punteggio troppo basso (somma dei pesi delle keyword trovate);
3. unisce i nuovi articoli a quelli degli ultimi 30 giorni già in archivio e scrive `ai-compass-feed.json`;
4. rigenera `index.html` con `generate_html.py` (stile e filtri in `static/`, nello stile di
   www.bitagoraorobica.it).

Il workflow poi salva i file aggiornati nel repo e pubblica il sito su GitHub Pages.

## Aggiungere una voce a mano

Modifica `data/voci_manuali.csv` (anche dal browser, con la matita di GitHub) aggiungendo una riga:

    Date,Title,Description,Category,Link,Source
    2026-10-08,Titolo,Descrizione breve,News,https://esempio.it/articolo,Nome fonte

Al salvataggio il sito si aggiorna da solo in un paio di minuti. Le voci manuali restano sempre visibili, in
evidenza nel riquadro "Dalla redazione" sopra gli articoli.

## Aggiornare subito il sito

Tab **Actions** → **Aggiorna AI Compass** → **Run workflow**.

## Lavorare in locale

    git clone https://github.com/bitagoraorobica/app_ia.git
    cd app_ia
    pip install -r requirements.txt
    python aggiorna_feed.py     # aggiorna feed, pagina e link già visti
    python generate_html.py     # rigenera solo index.html dal JSON esistente

Non serve nessun token: la pubblicazione la fa il workflow. Se lanci `aggiorna_feed.py` in locale, ricordati
di committare e pushare `ai-compass-feed.json`, `index.html` e `data/already_seen.txt`, altrimenti il
prossimo giro automatico riproporrà gli stessi articoli.
