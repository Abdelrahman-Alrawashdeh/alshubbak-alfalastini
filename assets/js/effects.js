(() => {
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const header = document.querySelector('header');
  const progress = document.querySelector('.scroll-progress');
  const backTop = document.querySelector('.back-top');
  const showcase = document.querySelector('.window-showcase');
  const model = document.querySelector('.window-object');
  let scheduled = false;
  function updateScroll() {
    const range = document.documentElement.scrollHeight - innerHeight;
    progress.style.transform = `scaleX(${range > 0 ? scrollY / range : 0})`;
    header.classList.toggle('scrolled', scrollY > 20);
    backTop.classList.toggle('visible', scrollY > 650);
    if (!reduceMotion.matches && scrollY < innerHeight * 1.5) {
      model.style.setProperty('--scroll-turn', `${Math.min(scrollY / innerHeight, 1) * -14}deg`);
      model.style.setProperty('--scroll-lift', `${Math.min(scrollY / innerHeight, 1) * -35}px`);
    }
    scheduled = false;
  }
  addEventListener('scroll', () => { if (!scheduled) { scheduled = true; requestAnimationFrame(updateScroll); } }, { passive: true });
  addEventListener('resize', updateScroll);
  updateScroll();
  showcase.addEventListener('pointermove', event => {
    if (reduceMotion.matches || event.pointerType !== 'mouse') return;
    const rect = showcase.getBoundingClientRect();
    model.style.setProperty('--ry', `${18 + (event.clientX - rect.left) / rect.width * 14}deg`);
    model.style.setProperty('--rx', `${5 - (event.clientY - rect.top) / rect.height * 12}deg`);
  });
  showcase.addEventListener('pointerleave', () => { model.style.removeProperty('--rx'); model.style.removeProperty('--ry'); });
  document.querySelector('.window-control').addEventListener('click', event => {
    const open = showcase.classList.toggle('is-open');
    event.currentTarget.setAttribute('aria-pressed', String(open));
    event.currentTarget.textContent = open ? 'إغلاق الشباك ↗' : 'جرّب فتح الشباك ↗';
  });
  document.querySelectorAll('.product-card').forEach((card, index) => {
    card.style.setProperty('--delay', `${index % 3 * 80}ms`);
  });
  const menu = document.getElementById('mobileMenu');
  const toggle = document.getElementById('navToggle');
  toggle.setAttribute('aria-controls', 'mobileMenu');
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.classList.contains('open')) {
      menu.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus();
    }
  });
  matchMedia('(min-width: 900px)').addEventListener('change', event => {
    if (event.matches) { menu.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); }
  });
  if ('IntersectionObserver' in window) {
    const links = [...document.querySelectorAll('.nav-links a')];
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) links.forEach(link => {
        const active = link.hash === `#${entry.target.id}`;
        link.classList.toggle('active', active);
        if (active) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
      }); });
    }, { rootMargin: '-15% 0px -50% 0px' });
    document.querySelectorAll('section[id]').forEach(section => observer.observe(section));
  }
})();
