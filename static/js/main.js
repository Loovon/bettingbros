/**
 * BetPlatform main.js v5
 * Bet slip: sticky right panel, scrollable selections, +/- stake buttons,
 * minimize/maximize, Singles/Acca/History tabs, live odds polling.
 */
'use strict';

const q  = (s,c=document) => c.querySelector(s);
const qa = (s,c=document) => [...c.querySelectorAll(s)];

function getCsrf() {
  const v = `; ${document.cookie}`.split('; csrftoken=');
  return v.length === 2 ? v.pop().split(';')[0] : '';
}

async function apiFetch(url, method='GET', body=null) {
  const r = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await r.text();
  if (!r.ok) {
    let msg = text;
    try { msg = JSON.parse(text).error || text; } catch (_) {}
    const e = new Error(msg); e.status = r.status; throw e;
  }
  return text ? JSON.parse(text) : {};
}

function esc(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function fmtOdds(dec, fmt='decimal') {
  const d = parseFloat(dec);
  if (isNaN(d)) return String(dec);
  if (fmt === 'fractional') {
    const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
    const n = Math.round((d - 1) * 100), dn = 100, g = gcd(Math.abs(n), dn);
    return `${n/g}/${dn/g}`;
  }
  if (fmt === 'american') return d >= 2 ? `+${Math.round((d-1)*100)}` : `${Math.round(-100/(d-1))}`;
  return d.toFixed(2);
}

function showToast(msg, type='info') {
  let c = document.getElementById('toast-container');
  if (!c) {
    c = document.createElement('div');
    c.id = 'toast-container';
    c.className = 'toast-container';
    document.body.appendChild(c);
  }
  const t = document.createElement('div');
  t.className = `toast toast--${type}`;
  t.innerHTML = `<span class="toast__text">${esc(msg)}</span>`;
  c.appendChild(t);
  setTimeout(() => {
    t.style.cssText = 'opacity:0;transition:opacity .35s';
    setTimeout(() => t.remove(), 380);
  }, 4200);
}

/* ── Navbar ──────────────────────────────────────────────── */
function initNavbar() {
  const btn = q('#nav-toggle'), menu = q('#mobile-menu');
  if (!btn || !menu) return;
  btn.addEventListener('click', () => {
    const open = btn.classList.toggle('open');
    menu.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  });
  document.addEventListener('click', e => {
    if (!btn.contains(e.target) && !menu.contains(e.target)) {
      btn.classList.remove('open');
      menu.classList.remove('open');
      document.body.style.overflow = '';
    }
  });
}

/* ── Carousel ────────────────────────────────────────────── */
function initCarousel() {
  const el = q('#hero-carousel'); if (!el) return;
  const track  = el.querySelector('.carousel-track');
  const slides = qa('.carousel-slide', el);
  const dots   = qa('.carousel-dot', el);
  if (!slides.length) return;
  let cur = 0, timer = null;
  const go = i => {
    cur = ((i % slides.length) + slides.length) % slides.length;
    track.style.transform = `translateX(-${cur * 100}%)`;
    dots.forEach((d, j) => d.classList.toggle('active', j === cur));
  };
  const startAuto = () => { clearInterval(timer); timer = setInterval(() => go(cur + 1), 5000); };
  el.querySelector('.carousel-btn--next')?.addEventListener('click', () => { go(cur+1); startAuto(); });
  el.querySelector('.carousel-btn--prev')?.addEventListener('click', () => { go(cur-1); startAuto(); });
  dots.forEach((d, i) => d.addEventListener('click', () => { go(i); startAuto(); }));
  let sx = 0;
  track.addEventListener('touchstart', e => { sx = e.touches[0].clientX; clearInterval(timer); }, { passive: true });
  track.addEventListener('touchend',   e => { const dx = sx - e.changedTouches[0].clientX; if (Math.abs(dx) > 50) go(cur + (dx > 0 ? 1 : -1)); startAuto(); }, { passive: true });
  el.addEventListener('mouseenter', () => clearInterval(timer));
  el.addEventListener('mouseleave', startAuto);
  go(0); startAuto();
}

/* ═══════════════════════════════════════════════════════════
   BET SLIP
═══════════════════════════════════════════════════════════ */
const BetSlip = (() => {

  /* ── state ────────────────────────────────────────────── */
  let slip = [], tab = 'singles', busy = false, loaded = false;
  const oFmt = () => document.body.dataset.oddsFormat || 'decimal';

  /* ── DOM refs (assigned in init) ───────────────────────── */
  let rSel, rEmpty, rFooter, rSummary, rAccaSummary, rAccaOdds,
      rAccaReturn, rAccaCount, rAccaStake, rHistory, rHistSkel,
      rCollapseBtn, rExpandBtn, rPanel, rPlaceBtn;

  /* ── COLLAPSE / EXPAND ─────────────────────────────────── */
  const CKEY = 'bp_slip_v5';
  const isCollapsed  = () => localStorage.getItem(CKEY) === '1';
  const expandPanel  = () => applyCollapse(false);
  const collapsePanel= () => applyCollapse(true);
  const toggleCollapse = () => applyCollapse(!isCollapsed());

  function applyCollapse(v) {
    if (!rPanel) return;
    rPanel.classList.toggle('is-collapsed', v);
    localStorage.setItem(CKEY, v ? '1' : '0');
    if (rCollapseBtn) rCollapseBtn.setAttribute('aria-expanded', String(!v));
  }

  /* ── RENDER ────────────────────────────────────────────── */
  function render() {
    const n = slip.length;
    qa('.js-slip-count').forEach(el => el.textContent = n);

    /* Mobile FAB */
    const fab   = q('#mobile-slip-fab');
    const badge = q('#mobile-slip-count');
    if (fab)   fab.style.display   = n > 0 ? 'flex' : 'none';
    if (badge) badge.textContent   = n;

    /* Auto-expand on first selection */
    if (n === 1) expandPanel();

    if (!rSel) return;

    /* History tab */
    if (tab === 'history') {
      rEmpty.style.display            = 'none';
      rSel.style.display              = 'none';
      if (rAccaSummary) rAccaSummary.style.display = 'none';
      rFooter.style.display           = 'none';
      rHistory.style.display          = 'block';
      return;
    }

    rHistory.style.display  = 'none';
    if (rHistSkel) rHistSkel.style.display = 'none';
    rEmpty.style.display    = n === 0 ? 'flex'  : 'none';
    rSel.style.display      = n === 0 ? 'none'  : 'flex';
    rFooter.style.display   = n === 0 ? 'none'  : 'flex';

    if (n === 0) {
      if (rAccaSummary) rAccaSummary.style.display = 'none';
      return;
    }

    rSel.innerHTML = '';

    if (tab === 'singles') {
      if (rAccaSummary) rAccaSummary.style.display = 'none';
      slip.forEach(item => rSel.appendChild(buildSingleItem(item)));
    } else {
      if (rAccaSummary) rAccaSummary.style.display = 'flex';
      slip.forEach(item => rSel.appendChild(buildAccaItem(item)));
      refreshAcca();
    }

    refreshFooter();
    if (rPlaceBtn) rPlaceBtn.disabled = busy || slip.some(s => s._suspended);
  }

  function refreshAcca() {
    const odds = slip.reduce((a, s) => a * parseFloat(s.odds || 1), 1);
    if (rAccaCount)  rAccaCount.textContent  = slip.length;
    if (rAccaOdds)   rAccaOdds.textContent   = fmtOdds(odds, oFmt());
    if (rAccaStake && rAccaReturn) {
      const s = parseFloat(rAccaStake.value) || 0;
      rAccaReturn.textContent = s > 0 ? `$${(s * odds).toFixed(2)}` : '—';
    }
  }

  function refreshFooter() {
    if (!rSummary) return;
    if (tab === 'singles') {
      let ts = 0, tr = 0;
      qa('.js-stake-input', rSel).forEach(inp => {
        const s = parseFloat(inp.value) || 0, o = parseFloat(inp.dataset.odds) || 1;
        ts += s; if (s > 0) tr += s * o;
      });
      rSummary.innerHTML = ts > 0
        ? `<span>Stake: <strong>$${ts.toFixed(2)}</strong></span><span>Est. Return: <strong>$${tr.toFixed(2)}</strong></span>`
        : '';
    } else {
      const s = parseFloat(rAccaStake?.value) || 0;
      const odds = slip.reduce((a, v) => a * parseFloat(v.odds || 1), 1);
      rSummary.innerHTML = s > 0
        ? `<span>Stake: <strong>$${s.toFixed(2)}</strong></span><span>Return: <strong>$${(s * odds).toFixed(2)}</strong></span>`
        : '';
    }
  }

  /* ── BUILD SINGLE ITEM (with +/- stake buttons) ─────────── */
  function buildSingleItem(item) {
    const el  = document.createElement('div');
    el.className = 'slip-item';
    if (item._suspended) el.classList.add('slip-item--suspended');
    el.dataset.oddId = item.odd_id;

    const od = fmtOdds(item.odds, oFmt());
    const cb = buildChangeBadge(item);

    el.innerHTML = `
      <div class="slip-item__top">
        <span class="slip-item__event">${esc(item.event_name)}</span>
        <button class="slip-item__remove" data-odd="${esc(item.odd_id)}" title="Remove selection">&#10005;</button>
      </div>
      <div class="slip-item__market">${esc(item.market_name)}</div>
      <div class="slip-item__mid">
        <span class="slip-item__selection">${esc(item.selection_name)}</span>
        <span class="slip-item__odds">${esc(od)}</span>
      </div>
      ${cb}
      <div class="slip-item__stake-row">
        <button class="slip-item__stake-btn slip-item__stake-btn--minus" type="button" title="Decrease stake">&#8722;</button>
        <span class="slip-item__stake-currency">&#36;</span>
        <input class="slip-item__stake-input js-stake-input"
               type="number" min="0.01" step="1" placeholder="0.00"
               data-odd-id="${esc(item.odd_id)}" data-odds="${esc(item.odds)}"
               aria-label="Stake" />
        <button class="slip-item__stake-btn slip-item__stake-btn--plus" type="button" title="Increase stake">&#43;</button>
      </div>
      <div class="slip-item__return">
        <span>Potential return</span>
        <span class="slip-item__return-val js-return-val">&#8212;</span>
      </div>`;

    const inp = el.querySelector('.js-stake-input');
    const rv  = el.querySelector('.js-return-val');

    /* live return calc */
    inp.addEventListener('input', () => {
      const s = parseFloat(inp.value) || 0, o = parseFloat(inp.dataset.odds) || 1;
      rv.textContent = s > 0 ? `$${(s * o).toFixed(2)}` : '—';
      refreshFooter();
    });

    /* minus button */
    el.querySelector('.slip-item__stake-btn--minus').addEventListener('click', () => {
      const cur = parseFloat(inp.value) || 0;
      const next = Math.max(0, +(cur - 1).toFixed(2));
      inp.value = next > 0 ? next : '';
      inp.dispatchEvent(new Event('input'));
    });

    /* plus button */
    el.querySelector('.slip-item__stake-btn--plus').addEventListener('click', () => {
      const cur = parseFloat(inp.value) || 0;
      inp.value = +(cur + 1).toFixed(2);
      inp.dispatchEvent(new Event('input'));
    });

    /* remove */
    el.querySelector('.slip-item__remove').addEventListener('click', e => {
      removeSelection(e.currentTarget.dataset.odd);
    });

    return el;
  }

  /* ── BUILD ACCA ITEM ────────────────────────────────────── */
  function buildAccaItem(item) {
    const el = document.createElement('div');
    el.className = 'slip-item';
    if (item._suspended) el.classList.add('slip-item--suspended');
    el.innerHTML = `
      <div class="slip-item__top">
        <span class="slip-item__event">${esc(item.event_name)}</span>
        <button class="slip-item__remove" data-odd="${esc(item.odd_id)}">&#10005;</button>
      </div>
      <div class="slip-item__market">${esc(item.market_name)}</div>
      <div class="slip-item__mid">
        <span class="slip-item__selection">${esc(item.selection_name)}</span>
        <span class="slip-item__odds">${esc(fmtOdds(item.odds, oFmt()))}</span>
      </div>
      ${buildChangeBadge(item)}`;
    el.querySelector('.slip-item__remove')
      .addEventListener('click', e => removeSelection(e.currentTarget.dataset.odd));
    return el;
  }

  function buildChangeBadge(item) {
    if (!item._prev_odds) return '';
    const f = oFmt(), up = item._dir === 'up';
    return `<div class="odds-change odds-change--${item._dir || 'up'}">
      <span class="odds-change__old">${fmtOdds(item._prev_odds, f)}</span>
      <span class="odds-change__new">${fmtOdds(item.odds, f)}</span>
      <span class="odds-change__arrow">${up ? '&#9650;' : '&#9660;'}</span>
    </div>`;
  }

  /* ── TABS ──────────────────────────────────────────────── */
  function setTab(t) {
    tab = t;
    [['singles', q('#tab-singles')], ['multi', q('#tab-multi')], ['history', q('#tab-history')]]
      .forEach(([name, btn]) => {
        if (!btn) return;
        btn.classList.toggle('active', name === t);
        btn.setAttribute('aria-selected', String(name === t));
      });
    if (t === 'history') HistoryTab.load();
    render();
  }

  /* ── API: load ──────────────────────────────────────────── */
  async function loadSlip() {
    try {
      const d = await apiFetch('/api/v1/bets/slip/');
      slip = d.slip || [];
      loaded = true;
      render();
      OddsPoller.start();
    } catch (_) { loaded = true; render(); }
  }

  /* ── API: add ───────────────────────────────────────────── */
  async function addOdd(data) {
    try {
      const d = await apiFetch('/api/v1/bets/slip/add/', 'POST', { odd_id: data.odd_id });
      slip = d.slip || [];
      expandPanel();
      render();
      hlBtn(data.odd_id, true);
    } catch (e) { showToast(e.message || 'Could not add selection.', 'error'); }
  }

  /* ── API: remove (optimistic) ──────────────────────────── */
  async function removeSelection(oddId) {
    const id = String(oddId);
    /* animate the item out immediately */
    const itemEl = rSel && rSel.querySelector(`[data-odd-id="${id}"]`);
    if (itemEl) { itemEl.classList.add('removing'); setTimeout(() => itemEl.remove(), 230); }
    const prev = [...slip];
    slip = slip.filter(s => s.odd_id !== id);
    render();
    hlBtn(id, false);
    try {
      const d = await apiFetch('/api/v1/bets/slip/remove/', 'POST', { odd_id: id });
      slip = d.slip || [];
      render();
    } catch (_) { slip = prev; render(); showToast('Could not remove.', 'error'); }
  }

  /* ── API: clear ─────────────────────────────────────────── */
  async function clearAll() {
    const prev = [...slip]; slip = []; render();
    qa('.odd-btn.selected').forEach(b => b.classList.remove('selected'));
    try { await apiFetch('/api/v1/bets/slip/clear/', 'POST'); }
    catch (_) { slip = prev; render(); }
  }

  /* ── API: place bet ────────────────────────────────────── */
  async function placeBet() {
    if (busy || !rPlaceBtn) return;
    let stake, betType;

    if (tab === 'multi') {
      betType = 'accumulator';
      stake = parseFloat(rAccaStake?.value) || 0;
      if (stake <= 0) { showToast('Enter a stake in the Accumulator section.', 'error'); return; }
    } else {
      betType = slip.length > 1 ? 'accumulator' : 'single';
      const fi = rSel?.querySelector('.js-stake-input');
      stake = parseFloat(fi?.value) || 0;
      if (stake <= 0) { showToast('Enter a stake amount.', 'error'); return; }
    }

    busy = true;
    rPlaceBtn.disabled = true;
    rPlaceBtn.setAttribute('aria-busy', 'true');
    rPlaceBtn.innerHTML = '<span class="spinner"></span>';

    try {
      const d = await apiFetch('/api/v1/bets/place/', 'POST', { stake, bet_type: betType });
      rPlaceBtn.innerHTML = '&#10003; Placed!';
      rPlaceBtn.classList.add('slip-place-btn--success');
      showToast(`Bet placed! Return: $${d.potential_return}`, 'success');
      document.dispatchEvent(new CustomEvent('betplaced', { detail: d }));
      setTimeout(() => {
        slip = [];
        render();
        rPlaceBtn.innerHTML  = 'Place Bet';
        rPlaceBtn.classList.remove('slip-place-btn--success');
        rPlaceBtn.disabled   = false;
        rPlaceBtn.removeAttribute('aria-busy');
        busy = false;
        qa('.odd-btn.selected').forEach(b => b.classList.remove('selected'));
        q('#slip-drawer')?.classList.remove('open');
        q('#slip-overlay')?.classList.remove('open');
        document.body.style.overflow = '';
      }, 1800);
    } catch (e) {
      rPlaceBtn.innerHTML = 'Place Bet';
      rPlaceBtn.disabled  = false;
      rPlaceBtn.removeAttribute('aria-busy');
      busy = false;
      showToast(e.message || 'Could not place bet. Check your balance.', 'error');
    }
  }

  /* ── ODDS POLLER ───────────────────────────────────────── */
  const OddsPoller = (() => {
    let tmr = null;
    async function poll() {
      if (document.hidden || !loaded || slip.length === 0) return;
      try {
        const d = await apiFetch('/api/v1/bets/slip/');
        let changed = false;
        (d.slip || []).forEach(fresh => {
          const loc = slip.find(s => s.odd_id === fresh.odd_id);
          if (!loc) return;
          if (String(loc.odds) !== String(fresh.odds)) {
            loc._prev_odds = loc.odds;
            loc._dir = parseFloat(fresh.odds) > parseFloat(loc.odds) ? 'up' : 'down';
            loc.odds = fresh.odds;
            changed = true;
          }
          if (fresh.status && fresh.status !== 'active') { loc._suspended = true; changed = true; }
        });
        if (changed) render();
      } catch (_) {}
    }
    return {
      start() { if (!tmr) tmr = setInterval(poll, 30000); },
      stop()  { clearInterval(tmr); tmr = null; },
    };
  })();

  /* ── HISTORY TAB ───────────────────────────────────────── */
  const HistoryTab = (() => {
    const cls  = s => ({ won: 'badge--green', lost: 'badge--red', open: 'badge--blue' }[s] || 'badge--gray');
    const fdat = iso => {
      const d = new Date(iso);
      return `${String(d.getDate()).padStart(2,'0')} ${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()]} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    };
    function row(b) {
      const ret = (b.status !== 'open' && parseFloat(b.actual_return) > 0) ? b.actual_return : b.potential_return;
      const sel = b.selections?.[0];
      return `<div class="slip-history-row">
        <div class="slip-history-row__hd">
          <span class="badge ${cls(b.status)}">${esc(b.status)}</span>
          <span class="slip-history-row__type">${esc(b.bet_type)}</span>
          <span class="slip-history-row__date">${fdat(b.placed_at)}</span>
        </div>
        ${sel ? `<div class="slip-history-row__sel">${esc(sel.selection_name)} @ ${fmtOdds(sel.odds_at_placement, oFmt())}</div>` : ''}
        <div class="slip-history-row__amounts">
          <span>Stake: <strong>$${esc(b.stake)}</strong></span>
          <span>Odds: <strong>${fmtOdds(b.total_odds, oFmt())}</strong></span>
          <span style="color:var(--green)">Return: <strong>$${esc(ret)}</strong></span>
        </div>
      </div>`;
    }
    async function load() {
      if (!rHistory || !rHistSkel) return;
      rHistSkel.style.display = 'block';
      rHistory.style.display  = 'none';
      rHistory.innerHTML = '';
      try {
        const d = await apiFetch('/api/v1/bets/history/?limit=10');
        rHistory.innerHTML = (!d || !d.length)
          ? '<div class="slip-history__empty">No bets placed yet</div>'
          : d.map(row).join('');
      } catch (e) {
        rHistory.innerHTML = e.status === 401
          ? '<div class="slip-history__empty"><a href="/accounts/login/">Sign in</a> to see history</div>'
          : '<div class="slip-history__empty">Could not load history</div>';
      } finally {
        rHistSkel.style.display = 'none';
        rHistory.style.display  = 'block';
      }
    }
    return { load };
  })();

  /* ── MOBILE DRAWER ──────────────────────────────────────── */
  function initDrawer() {
    const fab     = q('#mobile-slip-fab');
    const drawer  = q('#slip-drawer');
    const overlay = q('#slip-overlay');
    const openFn  = () => { drawer?.classList.add('open'); overlay?.classList.add('open'); document.body.style.overflow = 'hidden'; };
    const closeFn = () => { drawer?.classList.remove('open'); overlay?.classList.remove('open'); document.body.style.overflow = ''; };
    fab?.addEventListener('click', openFn);
    overlay?.addEventListener('click', closeFn);
    if (drawer) {
      const handle = drawer.querySelector('.slip-drawer__handle');
      let sy = 0;
      handle?.addEventListener('touchstart', e => { sy = e.touches[0].clientY; }, { passive: true });
      handle?.addEventListener('touchend',   e => { if (e.changedTouches[0].clientY - sy > 80) closeFn(); }, { passive: true });
    }
  }

  function hlBtn(oddId, on) {
    qa(`[data-odd-id="${oddId}"].odd-btn`).forEach(b => b.classList.toggle('selected', on));
  }

  /* ── PUBLIC INIT ────────────────────────────────────────── */
  function init() {
    rSel          = q('#slip-selections');
    rEmpty        = q('#slip-empty');
    rFooter       = q('#slip-footer');
    rSummary      = q('#slip-footer-summary');
    rAccaSummary  = q('#acca-summary');
    rAccaOdds     = q('#acca-total-odds');
    rAccaReturn   = q('#acca-total-return');
    rAccaCount    = q('#acca-count');
    rAccaStake    = q('#acca-stake-input');
    rHistory      = q('#slip-history');
    rHistSkel     = q('#slip-history-skeleton');
    rCollapseBtn  = q('#slip-collapse-btn');
    rExpandBtn    = q('#slip-expand-btn');
    rPanel        = q('.bet-slip-panel');
    rPlaceBtn     = q('#slip-place-btn');

    /* Apply saved collapse state */
    applyCollapse(isCollapsed());

    /* Wiring */
    rCollapseBtn?.addEventListener('click', toggleCollapse);
    rExpandBtn?.addEventListener('click', expandPanel);
    q('#slip-collapsed-view')?.addEventListener('click', expandPanel);

    q('#tab-singles')?.addEventListener('click', () => setTab('singles'));
    q('#tab-multi')?.addEventListener('click',   () => setTab('multi'));
    q('#tab-history')?.addEventListener('click', () => setTab('history'));

    q('#slip-clear-btn')?.addEventListener('click', clearAll);
    rPlaceBtn?.addEventListener('click', placeBet);
    q('#acca-stake-input')?.addEventListener('input', () => { refreshAcca(); refreshFooter(); });

    initDrawer();
    loadSlip();

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) OddsPoller.stop();
      else if (slip.length) OddsPoller.start();
    });
    document.addEventListener('betplaced', () => { if (tab === 'history') HistoryTab.load(); });
  }

  function toggleOdd(data) {
    const exists = slip.some(s => s.odd_id === String(data.odd_id));
    if (exists) removeSelection(String(data.odd_id));
    else addOdd(data);
  }

  return { init, toggleOdd };
})();

/* ── Odd button clicks (delegated) ────────────────────────── */
document.addEventListener('click', e => {
  const btn = e.target.closest('.odd-btn');
  if (!btn || btn.classList.contains('suspended')) return;
  BetSlip.toggleOdd({
    odd_id:         btn.dataset.oddId,
    event_name:     btn.dataset.eventName,
    market_name:    btn.dataset.marketName,
    selection_name: btn.dataset.selectionName,
    odds:           btn.dataset.odds,
  });
});

/* ── Lazy load images ───────────────────────────────────────── */
if ('IntersectionObserver' in window) {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting && e.target.dataset.src) {
        e.target.src = e.target.dataset.src;
        e.target.removeAttribute('data-src');
        obs.unobserve(e.target);
      }
    });
  }, { rootMargin: '200px' });
  document.addEventListener('DOMContentLoaded', () => qa('img[data-src]').forEach(img => obs.observe(img)));
}

/* ── Auto-dismiss Django messages ───────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  qa('.toast, .message').forEach(m => {
    setTimeout(() => {
      m.style.cssText = 'opacity:0;transition:opacity .4s';
      setTimeout(() => m.remove(), 400);
    }, 5000);
  });

  /* Boot sequence */
  initNavbar();
  initCarousel();
  BetSlip.init();
});
