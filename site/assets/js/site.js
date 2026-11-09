/* HG Roof Repair concept: page behaviour. Everything is progressive: the page reads fine without this file. */
(() => {
  window.HG = {};
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = document.documentElement;
  const params = new URLSearchParams(location.search);
  // ?still = screenshot mode (final states, no motion); ?still=<id> drops the sections above that element
  const still = params.has('still');
  if (still) {
    root.classList.add('still');
    const el = params.get('still') && document.getElementById(params.get('still'));
    const sec = el && el.closest('main > section');
    if (sec) while (sec.previousElementSibling) sec.previousElementSibling.remove();
    $$('img[loading="lazy"]').forEach((i) => { i.loading = 'eager'; }); // headless captures need every photo
  }
  const reduce = still || matchMedia('(prefers-reduced-motion: reduce)').matches;
  const say = (t) => { const l = $('#sr-live'); if (l) { l.textContent = ''; setTimeout(() => { l.textContent = t; }, 30); } };

  // the concept bar's height positions the header inside the hero card
  const bar = $('.concept-bar');
  const setBar = () => bar && root.style.setProperty('--bar-h', bar.offsetHeight + 'px');
  setBar(); addEventListener('resize', setBar);

  // ---------- header: sits in the hero, becomes a floating pill after it ----------
  const header = $('[data-header]');
  const hero = $('.hero-card');
  const onScroll = () => {
    if (!header || !hero) return;
    const stuck = hero.getBoundingClientRect().bottom < 120;
    header.classList.toggle('is-stuck', stuck);
  };
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  // ---------- nav: the orange pill follows clicks and the section on screen ----------
  const spyLinks = $$('.nav-pill [data-spy]');
  const targets = spyLinks.map((a) => ({ a, el: document.getElementById(a.hash.slice(1)) })).filter((t) => t.el);
  let current = null, lockUntil = 0;
  const setActive = (a) => {
    if (!a || a === current) return;
    current = a;
    spyLinks.forEach((l) => { const on = l === a; l.classList.toggle('is-active', on); if (on) l.setAttribute('aria-current', 'true'); else l.removeAttribute('aria-current'); });
  };
  const spy = () => {
    if (!targets.length || Date.now() < lockUntil) return;
    const line = innerHeight * 0.35; // a section counts as "on screen" once its top passes this line
    let pick = targets[0];
    targets.forEach((t) => { if (t.el.getBoundingClientRect().top <= line) pick = t; });
    // at the very bottom the last section (Contact) may never reach the line
    if (innerHeight + scrollY >= document.documentElement.scrollHeight - 4) pick = targets[targets.length - 1];
    setActive(pick.a);
  };
  // a click lights its item at once and holds it until the smooth scroll ends (scrollend, or 1.6s at most)
  spyLinks.forEach((a) => a.addEventListener('click', () => {
    setActive(a);
    lockUntil = Date.now() + 1600;
    setTimeout(spy, 1650);
  }));
  addEventListener('scrollend', () => { if (lockUntil) { lockUntil = 0; spy(); } });
  // run straight from the scroll event (a handful of measurements): animation frames pause in background tabs
  addEventListener('scroll', spy, { passive: true });
  addEventListener('resize', spy);
  spy();

  // ---------- mobile menu ----------
  const menu = $('#mobile-nav');
  const openBtn = $('.menu-btn');
  const setMenu = (open) => {
    if (!menu || !openBtn) return;
    menu.hidden = !open;
    openBtn.setAttribute('aria-expanded', String(open));
    root.style.overflow = open ? 'hidden' : '';
    (open ? $('.close', menu) : openBtn).focus();
  };
  openBtn?.addEventListener('click', () => setMenu(true));
  $('.close', menu || document)?.addEventListener('click', () => setMenu(false));
  menu?.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
  addEventListener('keydown', (e) => {
    if (!menu || menu.hidden) return;
    if (e.key === 'Escape') setMenu(false);
    if (e.key === 'Tab') { // keep focus inside the open menu
      const f = $$('a, button', menu); const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  matchMedia('(min-width: 1061px)').addEventListener('change', (m) => { if (m.matches && menu && !menu.hidden) setMenu(false); });

  // ---------- reveal on scroll (timer fallback: background tabs may never fire the observer) ----------
  const reveals = $$('.reveal');
  const showAll = () => reveals.forEach((el) => el.classList.add('is-in'));
  if (reduce || !('IntersectionObserver' in window)) showAll();
  else {
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveals.forEach((el) => io.observe(el));
    setTimeout(() => reveals.forEach((el) => { if (el.getBoundingClientRect().top < innerHeight) el.classList.add('is-in'); }), 1200);
  }

  // ---------- hero ghost wordmark drifts with scroll and pointer (desktop pointers only) ----------
  const ghost = $('[data-parallax]');
  if (ghost && !reduce && matchMedia('(hover: hover) and (pointer: fine)').matches) {
    let px = 0, sy = 0, raf = 0;
    const paint = () => { raf = 0; ghost.style.transform = `translate3d(${px * 18}px, ${sy * 0.18}px, 0)`; };
    const ask = () => { if (!raf) raf = requestAnimationFrame(paint); };
    addEventListener('scroll', () => { sy = Math.min(scrollY, 900); ask(); }, { passive: true });
    hero?.addEventListener('pointermove', (e) => { const r = hero.getBoundingClientRect(); px = (e.clientX - r.left) / r.width - 0.5; ask(); });
  }

  // ---------- services rail: arrows, dots, keyboard ----------
  const rail = $('[data-rail]');
  if (rail) {
    const cards = $$('.scard', rail);
    const prev = $('[data-prev]'), next = $('[data-next]'), dotsEl = $('[data-dots]');
    const step = () => (cards[1] ? cards[1].offsetLeft - cards[0].offsetLeft : rail.clientWidth);
    const index = () => Math.round(rail.scrollLeft / step());
    const max = () => Math.max(0, Math.round((rail.scrollWidth - rail.clientWidth) / step()));
    const pages = () => max() + 1;
    let dots = [];
    const drawDots = () => {
      const n = pages();
      if (dots.length === n) return;
      dotsEl.textContent = '';
      // decorative position indicator; the arrows, swipe and arrow keys move the rail
      dotsEl.setAttribute('aria-hidden', 'true');
      dots = Array.from({ length: n }, () => { const d = document.createElement('i'); dotsEl.append(d); return d; });
    };
    const sync = () => {
      drawDots();
      const i = Math.min(index(), max());
      dots.forEach((d, k) => { d.classList.toggle('is-on', k === i); d.classList.toggle('is-near', Math.abs(k - i) === 1); });
      prev.disabled = rail.scrollLeft < 4;
      next.disabled = rail.scrollLeft > rail.scrollWidth - rail.clientWidth - 4;
    };
    const go = (i) => {
      const left = Math.max(0, Math.min(i, max())) * step();
      // the pane and some browsers skip smooth scrolling: jump if it hasn't moved
      rail.scrollTo({ left, behavior: reduce ? 'auto' : 'smooth' });
      setTimeout(() => { if (Math.abs(rail.scrollLeft - left) > 4) { rail.style.scrollSnapType = 'none'; rail.scrollLeft = left; rail.style.scrollSnapType = ''; } sync(); }, 650);
      say(`Showing ${cards[Math.min(i, cards.length - 1)].querySelector('h3').textContent}`);
    };
    prev.addEventListener('click', () => go(index() - 1));
    next.addEventListener('click', () => go(index() + 1));
    rail.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') { e.preventDefault(); go(index() + 1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); go(index() - 1); }
    });
    let t = 0;
    rail.addEventListener('scroll', () => { cancelAnimationFrame(t); t = requestAnimationFrame(sync); }, { passive: true });
    addEventListener('resize', sync);
    sync();
  }

  // ---------- open now? (San Antonio time; hours from his site: every day 8am–6pm) ----------
  const status = $('[data-open-status]');
  if (status) {
    const OPEN = 8 * 60, CLOSE = 18 * 60;
    const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: 'America/Chicago', hour: 'numeric', minute: 'numeric', hourCycle: 'h23' }).formatToParts(new Date()).map((x) => [x.type, x.value]));
    const m = +p.hour * 60 + +p.minute;
    if (!still) status.textContent = m >= OPEN && m < CLOSE ? 'Open now · until 6pm' : `Closed now · opens 8am${m >= CLOSE ? ' tomorrow' : ''}`;
  }

  // ---------- estimate form: validates, then builds an email (there is no backend, so nothing is "sent") ----------
  const form = $('[data-estimate]');
  if (form) {
    const box = $('[data-status]', form);
    const EMAIL = 'hugoroofer8888@gmail.com';
    const field = (n) => form.elements[n];
    const invalid = (el, bad) => { el.setAttribute('aria-invalid', String(bad)); return bad; };
    form.addEventListener('input', (e) => { if (e.target.matches('[aria-invalid="true"]')) invalid(e.target, false); });
    form.addEventListener('change', (e) => { if (e.target.name === 'issue') { $('.chips', form).classList.remove('is-invalid'); $('.chips', form).setAttribute('aria-invalid', 'false'); } });
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = field('name').value.trim(), phone = field('phone').value.trim(), address = field('address').value.trim();
      const issue = form.querySelector('[name="issue"]:checked')?.value || '';
      const msg = field('message').value.trim();
      const errors = [];
      if (invalid(field('name'), !name)) errors.push('your name');
      if (invalid(field('phone'), phone.replace(/\D/g, '').length < 10)) errors.push('a phone number with area code');
      if (invalid(field('address'), address.length < 5)) errors.push('an address or ZIP');
      $('.chips', form).classList.toggle('is-invalid', !issue);
      $('.chips', form).setAttribute('aria-invalid', String(!issue));
      if (!issue) errors.push('the problem');
      box.hidden = false;
      if (errors.length) {
        box.className = 'form-status is-error';
        box.textContent = `Please add ${errors.length > 1 ? errors.slice(0, -1).join(', ') + ' and ' + errors.at(-1) : errors[0]}.`;
        (form.querySelector('[aria-invalid="true"]') || form.querySelector('[name="issue"]')).focus();
        say(box.textContent);
        return;
      }
      const subject = `Roof repair estimate: ${issue} (${address})`;
      const body = `Hi Hugo,\n\nI'd like a free estimate.\n\nName: ${name}\nPhone: ${phone}\nAddress: ${address}\nProblem: ${issue}${msg ? `\n\n${msg}` : ''}\n\nThanks!`;
      const href = `mailto:${EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      box.className = 'form-status';
      box.innerHTML = '<b>Your email is ready. Nothing has been sent yet.</b> Your email app should open with this message; press send there. If it didn’t open, copy it or call instead.';
      const pre = document.createElement('pre'); pre.textContent = `To: ${EMAIL}\nSubject: ${subject}\n\n${body}`;
      const row = document.createElement('div'); row.className = 'row';
      row.innerHTML = '<a class="primary" data-open>Open email app</a><button type="button" data-copy>Copy message</button><a href="tel:+12103960922">Call (210) 396-0922</a>';
      $('[data-open]', row).href = href;
      box.append(pre, row);
      $('[data-copy]', row).addEventListener('click', async (ev) => {
        try { await navigator.clipboard.writeText(pre.textContent); ev.target.textContent = 'Copied'; }
        catch { const r = document.createRange(); r.selectNodeContents(pre); getSelection().removeAllRanges(); getSelection().addRange(r); ev.target.textContent = 'Selected: press Ctrl+C'; }
      });
      say('Your email is ready. Nothing has been sent yet.');
      if (!form.hasAttribute('data-dry-run')) location.href = href;
    });
  }
})();
