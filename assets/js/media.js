(() => {
  'use strict';
  const items = window.COMPANY_MEDIA.items;
  const byId = new Map(items.map(item => [item.id, item]));
  const grid = document.getElementById('mediaGrid');
  const cards = [...grid.querySelectorAll('.media-card')];
  const categoryButtons = [...document.querySelectorAll('[data-category]')].filter(el => el.tagName === 'BUTTON');
  const typeButtons = [...document.querySelectorAll('.type-filters button')];
  const more = document.getElementById('loadMore');
  const dialog = document.getElementById('mediaDialog');
  const stage = document.getElementById('viewerStage');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let category = 'all', type = 'all', limit = 9, filtered = [], viewerItems = [], current = 0;
  let opener = null, scrollPosition = 0;

  function filter(reset = true) {
    if (reset) limit = 9;
    filtered = cards.filter(card => (category === 'all' || card.dataset.category === category) && (type === 'all' || card.dataset.type === type));
    cards.forEach(card => { card.hidden = true; });
    filtered.slice(0, limit).forEach(card => { card.hidden = false; });
    categoryButtons.forEach(button => {
      const selected = button.dataset.category === category;
      button.classList.toggle('active', selected); button.setAttribute('aria-pressed', String(selected));
    });
    typeButtons.forEach(button => {
      const selected = button.dataset.type === type;
      button.classList.toggle('active', selected); button.setAttribute('aria-pressed', String(selected));
    });
    const photos = filtered.filter(card => card.dataset.type === 'image').length;
    const films = filtered.length - photos;
    document.getElementById('mediaCount').textContent = `${photos} صورة · ${films} فيديو`;
    document.getElementById('mediaEmpty').hidden = filtered.length > 0;
    more.hidden = limit >= filtered.length;
    more.firstChild.textContent = `عرض المزيد (${Math.max(0, filtered.length - limit)}) `;
  }
  categoryButtons.forEach(button => button.addEventListener('click', () => { category = button.dataset.category; filter(); }));
  typeButtons.forEach(button => button.addEventListener('click', () => { type = button.dataset.type; filter(); }));
  more.addEventListener('click', () => {
    const firstNew = filtered[limit]; limit += 9; filter(false);
    firstNew?.querySelector('a').focus({ preventScroll: true });
  });
  document.querySelectorAll('[data-category-link]').forEach(link => link.addEventListener('click', () => {
    category = link.dataset.categoryLink; type = 'all'; filter();
    categoryButtons.find(button => button.dataset.category === category)?.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'instant' });
  }));
  filter();

  function stopMedia() {
    stage.querySelectorAll('video').forEach(video => { video.pause(); video.removeAttribute('src'); video.load(); });
    stage.replaceChildren();
  }
  function renderViewer() {
    stopMedia();
    const item = viewerItems[current];
    document.getElementById('viewerTitle').textContent = item.title;
    document.getElementById('viewerCategory').textContent = item.categoryLabel;
    document.getElementById('viewerPosition').textContent = `${current + 1} / ${viewerItems.length} · ${item.type === 'video' ? 'تحكّم بالصوت من مشغّل الفيديو' : 'الصورة كاملة دون اقتصاص'}`;
    const original = document.getElementById('viewerOriginal');
    original.href = item.src;
    const media = document.createElement(item.type === 'video' ? 'video' : 'img');
    if (item.type === 'video') {
      media.controls = true; media.playsInline = true; media.preload = 'metadata'; media.poster = item.thumbnail; media.volume = 0.65;
      media.setAttribute('aria-label', item.title);
    } else { media.alt = item.title; media.decoding = 'async'; }
    media.src = item.src;
    media.addEventListener('error', () => {
      const note = document.createElement('p'); note.className = 'playback-note';
      note.textContent = 'تعذّر تحميل الملف. يمكنك إعادة المحاولة أو فتحه في صفحة مستقلة.';
      stage.append(note);
    });
    stage.append(media);
    // A user click opens the film; sound is never started by scrolling or page load.
    if (item.type === 'video') media.play().catch(() => {});
    document.getElementById('previousMedia').disabled = viewerItems.length < 2;
    document.getElementById('nextMedia').disabled = viewerItems.length < 2;
  }
  document.querySelectorAll('[data-media]').forEach(link => link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || typeof dialog.showModal !== 'function') return;
    const item = byId.get(link.dataset.media);
    if (!item) return;
    event.preventDefault(); opener = link;
    viewerItems = link.closest('#mediaGrid') ? filtered.map(card => byId.get(card.querySelector('[data-media]').dataset.media)) : items.filter(entry => entry.category === item.category);
    current = viewerItems.findIndex(entry => entry.id === item.id);
    scrollPosition = scrollY;
    dialog.showModal(); document.body.classList.add('viewer-open'); renderViewer();
    dialog.querySelector('.viewer-close').focus();
  }));
  function navigate(direction) { current = (current + direction + viewerItems.length) % viewerItems.length; renderViewer(); }
  document.getElementById('previousMedia').addEventListener('click', () => navigate(-1));
  document.getElementById('nextMedia').addEventListener('click', () => navigate(1));
  dialog.querySelector('.viewer-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    stopMedia(); document.body.classList.remove('viewer-open');
    window.scrollTo({ top: scrollPosition, behavior: 'instant' }); opener?.focus({ preventScroll: true });
  });
  dialog.addEventListener('keydown', event => {
    if (event.target.tagName === 'VIDEO') return;
    if (event.key === 'ArrowLeft') { event.preventDefault(); navigate(1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); navigate(-1); }
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) stage.querySelector('video')?.pause(); });

  // Lightweight perspective interaction: no scroll hijacking, no animation loop while idle.
  grid.addEventListener('pointermove', event => {
    if (event.pointerType !== 'mouse' || reduced.matches) return;
    const visual = event.target.closest('.media-card-visual');
    if (!visual) return;
    const rect = visual.getBoundingClientRect();
    visual.style.setProperty('--tilt-x', `${(0.5 - (event.clientY - rect.top) / rect.height) * 4}deg`);
    visual.style.setProperty('--tilt-y', `${((event.clientX - rect.left) / rect.width - 0.5) * 5}deg`);
  });
  cards.forEach(card => card.addEventListener('pointerleave', () => {
    const visual = card.querySelector('.media-card-visual'); visual.style.removeProperty('--tilt-x'); visual.style.removeProperty('--tilt-y');
  }));
  const targets = document.querySelectorAll('.company-feature, .craft-card');
  if ('IntersectionObserver' in window && !reduced.matches) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('in'); observer.unobserve(entry.target); }
    }), { threshold: 0.12 });
    targets.forEach(target => { target.classList.add('reveal'); observer.observe(target); });
  }
})();
