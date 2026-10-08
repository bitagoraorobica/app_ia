# Raccoglie i feed RSS + le voci manuali, filtra e classifica gli articoli,
# aggiorna ai-compass-feed.json e rigenera index.html.
# Non pubblica nulla: lo fa il workflow .github/workflows/aggiorna.yml.

import csv
import html
import json
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import feedparser
import requests

import generate_html

# === FILE ===
FEED_JSON = "ai-compass-feed.json"
MANUAL_CSV = os.path.join("data", "voci_manuali.csv")
SEEN_FILE = os.path.join("data", "already_seen.txt")

# === FONTI ===
rss_feeds = {
    # Fonti originali
    "OpenAI": "https://openai.com/news/rss.xml",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "DeepMind": "https://deepmind.google/blog/rss.xml",
    "Meta AI": "https://engineering.fb.com/category/ai-research/feed/",
    "arXiv AI": "https://export.arxiv.org/rss/cs.AI",

    # Ricerca e paper
    "Google Research": "https://research.google/blog/rss/",
    "Microsoft Research": "https://www.microsoft.com/en-us/research/feed/",
    "MIT AI News": "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",

    # Aziende AI e modelli
    "Stability AI": "https://stability.ai/news-updates?format=rss",
    "Replicate": "https://replicate.com/blog/rss",
    "LangChain": "https://www.langchain.com/blog/rss.xml",
    "Weights & Biases": "https://wandb.ai/fully-connected/rss.xml",
    "Berkeley BAIR": "https://bair.berkeley.edu/blog/feed.xml",
    "NVIDIA AI": "https://blogs.nvidia.com/blog/category/generative-ai/feed/",
    "IBM Research AI": "https://research.ibm.com/rss",

    # Etica, policy, impatto
    "AI Now Institute": "https://ainowinstitute.org/feed",
    "Partnership on AI": "https://partnershiponai.org/feed/",

    # Media & Portali
    "The Batch (deeplearning.ai)": "https://charonhub.deeplearning.ai/rss/",
    "TLDR AI": "https://tldr.tech/api/rss/ai",

    # Automation tools
    "n8n Blog": "https://blog.n8n.io/rss/",
    "Zapier Blog": "https://zapier.com/blog/feeds/latest/",
    "Activepieces": "https://www.activepieces.com/rss.xml",

    # YouTube (via RSS ufficiale) https://www.youtube.com/feeds/videos.xml?channel_id=YOUR_CHANNEL_ID
    "YouTube – OpenAI": "https://www.youtube.com/feeds/videos.xml?channel_id=UCXZCJLdBC09xxGZ6gcdrc6A",
    "YouTube – DeepMind": "https://www.youtube.com/feeds/videos.xml?channel_id=UCP7jMXSY2xbc3KCAE0MHQ-A",
    "YouTube – Google Research": "https://www.youtube.com/feeds/videos.xml?channel_id=UCT-VzthVAM_4ohDdKa-BbXA",
    "YouTube – Yannic Kilcher": "https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew",
    "YouTube – Two Minute Papers": "https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg",
    "YouTube – Raffaele Gaito": "https://www.youtube.com/feeds/videos.xml?channel_id=UCrebGs3b-Z7JLKQM2YOpUKA",
    "YouTube – Computerphile": "https://www.youtube.com/feeds/videos.xml?channel_id=UC9-y-6csu5WGm29I7JiwpnA",
    "YouTube – Andrej Karpathy": "https://www.youtube.com/feeds/videos.xml?channel_id=UCXUPKJO5MZQN11PqgIvyuvQ",
    "YouTube – AI Explained": "https://www.youtube.com/feeds/videos.xml?channel_id=UC5c-DuzPdH9iaWYdI0v0uzw",
    "YouTube - Gabry Solutions": "https://www.youtube.com/feeds/videos.xml?channel_id=UC8oBIE88TrCD1b-gnVqXzgw",
    "YouTube - Marco Montemagno": "https://www.youtube.com/feeds/videos.xml?channel_id=UCNg4RDHGls-HpbV10kWPlsw",
}

# Fonti tolte l'08/10/2026 perché non hanno (più) un feed RSS utilizzabile: Anthropic, Cohere, Stanford HAI,
# Semantic Scholar, Papers with Code (chiuso), AI Ethics Journal, Center for Humane Technology,
# Make (403 Cloudflare), Pipedream, VentureBeat (429), Synced Review (fermo da agosto 2025).
# TLDR "tech" sostituito da TLDR AI: nessun articolo superava la soglia.

# === PUNTEGGIO ===
keywords = {
    "workflow": 2,
    "automation": 2,
    "gpt": 3,
    "benchmark": 2,
    "llm": 3,
    "transformer": 2,
    "text-to": 1,
    "evaluation": 1,
    "multimodal": 2,
    "diffusion": 1,
    "openai": 2,
    "zapier": 2,
    "n8n": 2,
    "make.com": 1,
    "low-code": 1,
    "no-code": 1,
    "webhook": 1,
    "integration": 1,
    "ai": 3,
    "intelligenza artificiale": 3,
    "startup": 2,
    "imprenditore": 2,
    "tecnologia": 2,
    "future": 1,
    "chatgpt": 3,
    "innovazione": 1,
    "strategie": 1,
    "business": 0.5,
    "montemagno": 1,
    "deepfake": 2,
    "lavoro": 1,
    "linkedin": 1,
    "personal brand": 1,
    "robot": 2,
}

min_score_required = 5
max_items_per_feed = 5
max_age_days = 30  # vale sia per i nuovi articoli sia per quelli già in archivio

automation_domains = ["n8n.io", "zapier.com", "activepieces.com"]

# Domini affidabili per cui non serve verificare il link con una HEAD request
skip_check_domains = [
    # Fonti ufficiali e ricerca
    "openai.com",
    "huggingface.co",
    "deepmind.google",
    "fb.com",
    "arxiv.org",
    "research.google",
    "microsoft.com",
    "news.mit.edu",
    "bair.berkeley.edu",
    "blogs.nvidia.com",
    "research.ibm.com",

    # Aziende AI & modelli
    "stability.ai",
    "replicate.com",
    "langchain.com",
    "wandb.ai",

    # Etica e policy
    "ainowinstitute.org",
    "partnershiponai.org",

    # Media & news
    "deeplearning.ai",
    "tldr.tech",

    # Automation tools
    *automation_domains,

    # YouTube e divulgatori
    "youtube.com",
    "youtu.be",
]

HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AICompass/1.0; +https://bitagoraorobica.github.io/app_ia/)"}
FEED_TIMEOUT = 20
LINK_TIMEOUT = 5


def _pattern_keyword(parola):
    # Le keyword corte ("ai", "gpt", "llm", "n8n") contano solo come parola intera, al massimo al plurale:
    # come sottostringa "ai" scatterebbe in "said", "email", "train", "OpenAI"... Le altre devono
    # almeno iniziare una parola ("robot" vale anche per "robotics").
    p = re.escape(parola)
    return re.compile(rf"\b{p}s?\b" if len(parola) <= 3 else rf"\b{p}")


keyword_patterns = {parola: _pattern_keyword(parola) for parola in keywords}


def calcola_score(titolo, descrizione):
    text = (titolo + " " + descrizione).lower()
    return sum(peso for parola, peso in keywords.items() if keyword_patterns[parola].search(text))


def testo_semplice(s):
    """Toglie i tag HTML dai summary dei feed: tagliati a 300 caratteri romperebbero la pagina."""
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def data_pubblicazione(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return datetime(*parsed[:6], tzinfo=timezone.utc) if parsed else None


def link_raggiungibile(link):
    try:
        r = requests.head(link, timeout=LINK_TIMEOUT, headers=HTTP_HEADERS)
        return r.status_code < 400
    except requests.RequestException:
        return False


def leggi_voci_manuali():
    voci = []
    with open(MANUAL_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            campo = lambda nome: (row.get(nome) or "").strip()
            if not campo("Link"):
                continue
            voci.append({
                "date": campo("Date"),
                "title": campo("Title"),
                "description": campo("Description"),
                "category": campo("Category"),
                "link": campo("Link"),
                "source": campo("Source"),
                "badge": "",
            })
    return voci


def leggi_feed(url):
    resp = requests.get(url, timeout=FEED_TIMEOUT, headers=HTTP_HEADERS)
    resp.raise_for_status()
    return feedparser.parse(resp.content).entries


def raccogli_rss(seen_links, cutoff):
    nuove = []
    for source, url in rss_feeds.items():
        try:
            entries = leggi_feed(url)
        except Exception as e:
            print(f"⛔ {source}: feed non leggibile ({e})")
            continue

        accettate = 0
        scartate = {"già visti": 0, "vecchi": 0, "punteggio basso": 0, "link non validi": 0, "altro": 0}
        for entry in entries:
            if accettate >= max_items_per_feed:
                break
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            description = testo_semplice(entry.get("summary", ""))
            # Solo link web: un feed compromesso potrebbe inserire link "javascript:" che eseguono codice
            if not title or urlparse(link).scheme not in ("http", "https") or len(title) > 250:
                scartate["altro"] += 1
                continue
            if link in seen_links:
                scartate["già visti"] += 1
                continue
            published = data_pubblicazione(entry)
            if not published or published < cutoff:
                scartate["vecchi"] += 1
                continue
            if len(description) < 30:
                description += " [...]"

            score = calcola_score(title, description)
            if "arxiv" in url:
                score -= 1
            if score < min_score_required:
                scartate["punteggio basso"] += 1
                continue

            domain = urlparse(link).netloc
            if not any(d in domain for d in skip_check_domains) and not link_raggiungibile(link):
                scartate["link non validi"] += 1
                continue

            # Assegna categoria e badge personalizzati
            if "arxiv" in url:
                category, badge = "Paper", "📜"
            elif any(d in domain for d in automation_domains):
                category, badge = "Automation", "🔁"
            else:
                category = "News"
                badge = "🔥" if score >= 10 else "⭐" if score >= 8 else ""

            nuove.append({
                "date": published.strftime("%Y-%m-%d"),
                "title": title,
                "description": description[:300],
                "category": category,
                "link": link,
                "source": source,
                "badge": badge,
            })
            seen_links.add(link)
            accettate += 1
            print(f"✅ {source}: [{score}] {title[:80]}")

        dettaglio = ", ".join(f"{k} {v}" for k, v in scartate.items() if v)
        print(f"🌐 {source}: {len(entries)} voci nel feed, {accettate} accettate" + (f" (scartate: {dettaglio})" if dettaglio else ""))
    return nuove


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_age_days)

    seen_links = set()
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, encoding="utf-8") as f:
            seen_links = {line.strip() for line in f if line.strip()}

    # === 1. VOCI MANUALI ===
    manual_entries = leggi_voci_manuali()
    manual_links = {e["link"] for e in manual_entries}
    print(f"📗 Voci manuali: {len(manual_entries)}")

    # === 2. ARCHIVIO: articoli RSS dei giri precedenti ancora negli ultimi max_age_days ===
    archivio = []
    if os.path.exists(FEED_JSON):
        with open(FEED_JSON, encoding="utf-8") as f:
            archivio = [
                e for e in json.load(f)
                if e["link"] not in manual_links and e["date"] >= cutoff.strftime("%Y-%m-%d")
            ]
    print(f"🗂️ Articoli in archivio ancora validi: {len(archivio)}")

    # === 3. RACCOLTA RSS ===
    rss_entries = raccogli_rss(seen_links | manual_links, cutoff)
    print(f"📰 Nuovi articoli RSS: {len(rss_entries)}")

    # === 4. FUSIONE E SALVATAGGIO ===
    all_entries = manual_entries + archivio + rss_entries
    all_entries.sort(key=lambda e: e["date"], reverse=True)
    with open(FEED_JSON, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"💾 {FEED_JSON}: {len(all_entries)} voci")

    generate_html.main()

    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        for e in rss_entries:
            f.write(e["link"] + "\n")
    print(f"📝 {SEEN_FILE}: aggiunti {len(rss_entries)} link")


if __name__ == "__main__":
    main()
