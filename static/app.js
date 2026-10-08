// AI Compass: filtri, date relative e comparsa delle schede.
// Le schede sono già nell'HTML generato da generate_html.py: qui si mostrano o nascondono soltanto.
(function () {
  const cards = Array.from(document.querySelectorAll('.grid .card'));
  const search = document.getElementById('search');
  const source = document.getElementById('source');
  const days = document.getElementById('days');
  const chips = Array.from(document.querySelectorAll('.chip'));
  const count = document.getElementById('count');
  const countLabel = document.getElementById('count-label');
  const reset = document.getElementById('reset');
  const empty = document.getElementById('empty');
  const emptyReset = document.getElementById('empty-reset');

  const DAY = 24 * 60 * 60 * 1000;
  const today = new Date();
  const todayUtc = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  const ageInDays = (iso) => Math.round((todayUtc - Date.parse(iso)) / DAY);

  let category = '';

  function apply() {
    const q = search.value.trim().toLowerCase();
    const src = source.value;
    const maxAge = parseInt(days.value, 10);
    let visible = 0;

    for (const card of cards) {
      const show =
        (!q || card.dataset.text.includes(q)) &&
        (!category || card.dataset.category === category) &&
        (!src || card.dataset.source === src) &&
        (isNaN(maxAge) || ageInDays(card.dataset.date) <= maxAge);
      card.hidden = !show;
      if (show) visible++;
    }

    count.textContent = visible;
    countLabel.textContent = visible === 1 ? 'contenuto' : 'contenuti';
    const filtered = Boolean(q || category || src || !isNaN(maxAge));
    reset.hidden = !filtered;
    empty.hidden = visible > 0;
  }

  function clearFilters() {
    search.value = '';
    source.value = '';
    days.value = '';
    setCategory('');
  }

  function setCategory(value) {
    category = value;
    for (const chip of chips) chip.setAttribute('aria-pressed', String(chip.dataset.category === value));
    apply();
  }

  search.addEventListener('input', apply);
  source.addEventListener('change', apply);
  days.addEventListener('change', apply);
  for (const chip of chips) chip.addEventListener('click', () => setCategory(chip.dataset.category));
  reset.addEventListener('click', clearFilters);
  emptyReset.addEventListener('click', clearFilters);

  // "Oggi", "Ieri", "3 giorni fa" per l'ultima settimana; oltre resta la data scritta in pagina
  for (const time of document.querySelectorAll('time[data-relative]')) {
    const age = ageInDays(time.getAttribute('datetime'));
    if (age === 0) time.textContent = 'Oggi';
    else if (age === 1) time.textContent = 'Ieri';
    else if (age > 1 && age < 7) time.textContent = age + ' giorni fa';
  }

  // Comparsa delle schede allo scorrimento (saltata se l'utente preferisce meno animazioni)
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduceMotion && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        }
      },
      { rootMargin: '0px 0px -40px 0px' }
    );
    for (const card of cards) {
      card.classList.add('reveal');
      observer.observe(card);
    }
  }

  apply();
})();
