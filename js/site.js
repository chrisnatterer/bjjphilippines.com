// Shared behaviour for all pages except the homepage: solid nav on scroll,
// mobile menu, fade-up reveal.
(() => {
  const nav = document.getElementById('nav');
  if (nav) {
    const solid = () => nav.classList.toggle('solid', scrollY > 40);
    addEventListener('scroll', solid, { passive: true });
    solid();
  }

  const menu = document.getElementById('mobile-menu');
  const open = document.getElementById('menu-toggle');
  const close = document.getElementById('menu-close');
  if (menu && open && close) {
    const setMenu = on => {
      menu.classList.toggle('open', on);
      menu.setAttribute('aria-hidden', String(!on));
      document.body.style.overflow = on ? 'hidden' : '';
    };
    open.addEventListener('click', () => setMenu(true));
    close.addEventListener('click', () => setMenu(false));
    menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setMenu(false)));
  }

  const io = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.fade-up').forEach(el => io.observe(el));
})();
