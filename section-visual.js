(() => {
  const path = location.pathname.toLowerCase();
  const page = path.includes('catalogo') ? 'catalogo' : path.includes('marcas') || path.includes('marca') ? 'marcas' : path.includes('tipos') ? 'tipos' : 'inicio';
  document.documentElement.dataset.section = page;
  document.body.dataset.section = page;
  document.querySelectorAll('[data-section-link]').forEach(a => a.classList.toggle('active', a.dataset.sectionLink === page));
  const search = document.querySelector('[data-section-search]');
  const cards = [...document.querySelectorAll('[data-searchable]')];
  search?.addEventListener('input', () => {
    const q = search.value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
    cards.forEach(card => {
      const hay = (card.dataset.searchable || card.textContent).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
      card.hidden = !!q && !hay.includes(q);
    });
  });
})();
