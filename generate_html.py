# Genera index.html a partire da ai-compass-feed.json.
# Richiamato da aggiorna_feed.py; si può lanciare anche da solo per rigenerare la pagina.

import json
from html import escape

INPUT_JSON = "ai-compass-feed.json"
OUTPUT_HTML = "index.html"
LOGO_FILE = "logo.png"


def opzioni(valori):
    return "".join(f'\n      <option value="{escape(v)}">{escape(v)}</option>' for v in valori)


def build_html(all_entries):
    # Ordina per data decrescente
    all_entries = sorted(all_entries, key=lambda x: x["date"], reverse=True)

    # Estrai fonti e categorie per i filtri
    sources = sorted(set(entry['source'] for entry in all_entries))
    categories = sorted(set(entry['category'] for entry in all_entries))

    # Codifica tutto il JSON inline come stringa JS ("</" spezzato per non chiudere lo <script>)
    entry_data_js = json.dumps(all_entries, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    # HTML completo
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <title>AI Compass – BitAgorà Orobica</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://fonts.googleapis.com/css2?family=Inter&display=swap" rel="stylesheet">
  <style>
    * {{
      box-sizing: border-box;
    }}
    body {{
      font-family: 'Inter', sans-serif;
      background: #eef1f5;
      padding: 1em;
      margin: 0;
      transition: background 0.3s, color 0.3s;
    }}
    body.dark {{
      background: #181818;
      color: #e0e0e0;
    }}
    header {{
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 2em;
      text-align: center;
    }}
    header h1 {{
      font-size: 2em;
      margin: 0.5em 0;
    }}
    header img {{
      max-width: 100%;
      height: auto;
    }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 1em;
      justify-content: center;
      margin-bottom: 2em;
    }}
    .controls input,
    .controls select,
    .controls button {{
      font-size: 1em;
      padding: 0.5em;
      flex: 1 1 200px;
      max-width: 300px;
      border: 1px solid #ccc;
      border-radius: 6px;
      transition: border 0.3s;
    }}
    .controls input:hover,
    .controls select:hover {{
      border-color: #007acc;
    }}
    .entry {{
      background: #ffffff;
      border-radius: 12px;
      padding: 1em;
      margin-bottom: 1.5em;
      box-shadow: 0 4px 10px rgba(0,0,0,0.08);
      border-left: 4px solid transparent;
    }}
    .entry[data-category="News"] {{
      border-left-color: #007acc;
    }}
    .entry[data-category="Paper"] {{
      border-left-color: #e67e22;
    }}
    .entry[data-category="Course"] {{
      border-left-color: #27ae60;
    }}
    .entry[data-category="Automation"] {{
      border-left-color: #9b59b6; /* viola brillante */
    }}
    body.dark .entry {{
      background: #1e1e1e;
    }}
    .entry .title {{
      font-size: 1.2em;
      font-weight: bold;
      color: #007acc;
      text-decoration: none;
      display: block;
      margin-bottom: 0.5em;
    }}
    body.dark .title {{
      color: #4fc3f7;
    }}
    .entry p {{
      margin: 0.5em 0;
      line-height: 1.4;
    }}
    .entry .meta {{
      font-size: 0.85em;
      color: #666;
      margin-top: 0.5em;
    }}
    body.dark .meta {{
      color: #aaa;
    }}
    .entry .badge {{
      margin-right: 0.5em;
      font-size: 1.2em;
    }}
    @media (max-width: 600px) {{
      .controls {{
        flex-direction: column;
        align-items: stretch;
      }}
      .controls input,
      .controls select,
      .controls button {{
        flex: 1 1 auto;
        max-width: 100%;
      }}
    }}
    
    .entries-grid {{
        display: grid;
        grid-template-columns: 1fr;
        gap: 1.5em;
    }}
    @media (min-width: 700px) {{
  .entries-grid {{
    grid-template-columns: 1fr 1fr;
  }}
}}
@media (min-width: 1000px) {{
  .entries-grid {{
    grid-template-columns: 1fr 1fr 1fr;
  }}
}}
.entry {{
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.5s ease;
  opacity: 0;
}}
.entry.show {{
  opacity: 1;
}}
.entry:hover {{
  transform: scale(1.02);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}}
  </style>
</head>
<body>
  <header>
    <h1>AI Compass</h1>
    <img src="{LOGO_FILE}" alt="Logo">
  </header>
  <p><em>Selezione curata da <a href="https://www.bitagoraorobica.it" target="_blank">BitAgorà Orobica srl</a></em></p>

  <div class="controls">
    <input type="text" id="search" placeholder="Cerca per titolo o descrizione...">
    <select id="category">
      <option value="">Tutte le categorie</option>{opzioni(categories)}
    </select>
    <select id="source">
      <option value="">Tutte le fonti</option>{opzioni(sources)}
    </select>
    <select id="days">
      <option value="">Qualsiasi data</option>
      <option value="7">Ultimi 7 giorni</option>
      <option value="15">Ultimi 15 giorni</option>
      <option value="30">Ultimi 30 giorni</option>
    </select>
    <button id="toggleDark">🌗 Modalità scura</button>
    <button id="resetFilters">🔄 Reset filtri</button>
  </div>

  <div id="entries" class="entries-grid"></div>


  <script>
    const entryData = """ + entry_data_js + """;

    const searchInput = document.getElementById('search');
    const categoryFilter = document.getElementById('category');
    const sourceFilter = document.getElementById('source');
    const daysFilter = document.getElementById('days');
    const toggleDark = document.getElementById('toggleDark');
    const resetFilters = document.getElementById('resetFilters');
    const entriesDiv = document.getElementById('entries');

    const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})[c]);

    function createEntry(item) {
      const div = document.createElement('div');
      div.className = 'entry';
      div.dataset.text = (item.title + ' ' + item.description).toLowerCase();
      div.dataset.category = item.category;
      div.dataset.source = item.source;
      div.dataset.date = item.date;
      div.innerHTML = `
        <a href="${/^https?:/i.test(item.link) ? esc(item.link) : "#"}" class="title" target="_blank" rel="noopener">
          <span class="badge">${esc(item.badge)}</span>${esc(item.title)}
        </a>
        <p>${esc(item.description)}</p>
        <div class="meta">${esc(item.source)} – ${esc(item.date)} – ${esc(item.category)}</div>
      `;
      return div;
    }

    function render() {
      const q = searchInput.value.toLowerCase();
      const cat = categoryFilter.value;
      const src = sourceFilter.value;
      const days = parseInt(daysFilter.value);
      const now = new Date();

      entriesDiv.innerHTML = "";
entryData.forEach(item => {
  const entryDate = new Date(item.date);
  const diffDays = (now - entryDate) / (1000 * 60 * 60 * 24);
  if (
    (!q || (item.title + item.description).toLowerCase().includes(q)) &&
    (!cat || item.category === cat) &&
    (!src || item.source === src) &&
    (isNaN(days) || diffDays <= days)
  ) {
    const el = createEntry(item);
    entriesDiv.appendChild(el);
    // trigger animazione
    requestAnimationFrame(() => el.classList.add("show"));
  }
});

      
      
    }

    resetFilters.addEventListener("click", () => {
      searchInput.value = "";
      categoryFilter.value = "";
      sourceFilter.value = "";
      daysFilter.value = "";
      render();
    });

    searchInput.addEventListener("input", render);
    categoryFilter.addEventListener("change", render);
    sourceFilter.addEventListener("change", render);
    daysFilter.addEventListener("change", render);
    toggleDark.addEventListener("click", () => document.body.classList.toggle("dark"));

    render();
  </script>
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
