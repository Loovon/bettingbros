/**
 * Betting Platform — Main JavaScript
 * Handles: navbar, carousel, bet slip, mobile drawer, misc UI.
 * No jQuery — vanilla JS only.
 */

'use strict';

/* ============================================================
   UTILITIES
   ============================================================ */

const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

async function api(url, method = 'GET', body = null) {
  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

/* ============================================================
   NAVBAR — mobile toggle
   ============================================================ */

function initNavbar() {
  const toggle = $('#nav-toggle');
  const mobileMenu = $('#mobile-menu');
  if (!toggle || !mobileMenu) return;

  toggle.addEventListener('click', () => {
    const open = toggle.classList.toggle('open');
    mobileMenu.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!toggle.contains(e.target) && !mobileMenu.contains(e.target)) {
      toggle.classList.remove('open');
      mobileMenu.classList.remove('open');
      document.body.style.overflow = '';
    }
  });
}

/* ============================================================
   HERO CAROUSEL
   ============================================================ */

function initCarousel() {
  const carousel = $('#hero-carousel');
  if (!carousel) return;

  const track = carousel.querySelector('.carousel-track');
  const slides = $$('.carousel-slide', carousel);
  const dots   = $$('.carousel-dot', carousel);
  const prevBtn = carousel.querySelector('.carousel-btn--prev');
  const nextBtn = carousel.querySelector('.carousel-btn--next');

  if (!slides.length) return;

  let current = 0;
  let autoTimer = null;
  let startX = 0;
  let isDragging = false;

  function goTo(index) {
    current = (index + slides.length) % slides.length;
    track.style.transform = `translateX(-${current * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle('active', i === current));
  }

  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }

  function startAuto() {
    clearInterval(autoTimer);
    autoTimer = setInterval(next, 5000);
  }

  function stopAuto() { clearInterval(autoTimer); }

  // Controls
  nextBtn && nextBtn.addEventListener('click', () => { next(); startAuto(); });
  prevBtn && prevBtn.addEventListener('click', () => { prev(); startAuto(); });
  dots.forEach((d, i) => d.addEventListener('click', () => { goTo(i); startAuto(); }));

  // Touch/swipe support
  track.addEventListener('touchstart', (e) => {
    startX = e.touches[0].clientX;
    isDragging = true;
    stopAuto();
  }, { passive: true });

  track.addEventListener('touchend', (e) => {
    if (!isDragging) return;
    const diff = startX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) diff > 0 ? next() : prev();
    isDragging = false;
    startAuto();
  }, { passive: true });

  // Pause on hover
  carousel.addEventListener('mouseenter', stopAuto);
  carousel.addEventListener('mouseleave', startAuto);

  goTo(0);
  startAuto();
}

/* ============================================================
   BET SLIP — Enhanced with sub-modules
   ============================================================ */

const BetSlip = (() => {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────────────
  let slip = [];
  let activeTab = 'singles';
  let inFlight = false;
  let firstLoadDone = false;
  const oddsFormat = () => document.body.dataset.oddsFormat || 'decimal';

  // ── DOM refs ───────────────────────────────────────────────────────────────
  let selectionsEl, countEls, emptyEl, footerEl, tabSingles, tabMulti, tabHistory;
  let accaSummaryEl, totalOddsEl, totalReturnEl, placeBtnEl;
  let historyEl, historySkeletonEl, collapseBtn, slipPanel;

  // ── OddsFormatter ──────────────────────────────────────────────────────────
  const OddsFormatter = (() => {
    function gcd(a, b) { return b === 0 ? a : gcd(b, a % b); }
    function formatOdds(decimal, format) {
      const d = parseFloat(decimal);
      if (isNaN(d)) return String(decimal);
      if (format === 'fractional') {
        const denom = 100;
        const num = Math.round((d - 1) * denom);
        const g = gcd(Math.abs(num), denom);
        return `${num / g}/${denom / g}`;
      }
      if (format === 'american') {
        if (d >= 2.0) return `+${Math.round((d - 1) * 100)}`;
        return `${Math.round(-100 / (d - 1))}`;
      }
      return d.toFixed(2);
    }
    return { formatOdds };
  })();

  // ── CollapseManager ────────────────────────────────────────────────────────
  const CollapseManager = (() => {
    function isCollapsed() {
      return localStorage.getItem('slip_collapsed') === 'true';
    }
    function applyState(collapsed) {
      if (!slipPanel || !collapseBtn) return;
      slipPanel.classList.toggle('collapsed', collapsed);
      collapseBtn.setAttribute('aria-expanded', String(!collapsed));
      localStorage.setItem('slip_collapsed', String(collapsed));
    }
    function toggle() { applyState(!isCollapsed()); }
    function expand() { if (isCollapsed()) applyState(false); }
    function init() {
      if (collapseBtn) {
        collapseBtn.addEventListener('click', toggle);
        collapseBtn.addEventListener('keydown', e => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
        });
      }
      // Wire expand label click
      const _expLbl = document.getElementById('slip-expand-label');
      if (_expLbl) _expLbl.addEventListener('click', expand);
      applyState(isCollapsed());
    }
    return { init, toggle, expand };
  })();

  // ── OddsPoller ─────────────────────────────────────────────────────────────
  const OddsPoller = (() => {
    let timer = null;
    async function poll() {
      if (document.hidden || slip.length === 0 || !firstLoadDone) return;
      try {
        const data = await api('/api/v1/bets/slip/');
        const fresh = data.slip || [];
        let changed = false;
        fresh.forEach(freshItem => {
          const local = slip.find(s => s.odd_id === freshItem.odd_id);
          if (!local) return;
          if (String(local.odds) !== String(freshItem.odds)) {
            local._prev_odds = local.odds;
            local._new_odds = freshItem.odds;
            local._odds_direction = parseFloat(freshItem.odds) > parseFloat(local.odds) ? 'up' : 'down';
            local.odds = freshItem.odds;
            changed = true;
          }
          if (freshItem.status && freshItem.status !== 'active') {
            local._suspended = true;
            changed = true;
          }
        });
        if (changed) render();
      } catch (_) { /* silent skip */ }
    }
    function start() {
      if (timer) return;
      timer = setInterval(poll, 30000);
    }
    function stop() { clearInterval(timer); timer = null; }
    function onVisibility() {
      if (document.hidden) stop();
      else if (slip.length > 0) start();
    }
    function init() {
      document.addEventListener('visibilitychange', onVisibility);
      start();
    }
    return { init, start, stop };
  })();

  // ── RemovalAnimator ────────────────────────────────────────────────────────
  const RemovalAnimator = (() => {
    function animateRemove(el, onDone) {
      const h = el.offsetHeight;
      el.style.maxHeight = h + 'px';
      el.style.overflow = 'hidden';
      requestAnimationFrame(() => {
        el.classList.add('slip-item--removing');
        setTimeout(() => { el.remove(); if (onDone) onDone(); }, 240);
      });
    }
    function animateClearAll(els, onDone) {
      if (!els.length) { if (onDone) onDone(); return; }
      els.forEach((el, i) => setTimeout(() => animateRemove(el, null), i * 40));
      setTimeout(() => { if (onDone) onDone(); }, els.length * 40 + 260);
    }
    return { animateRemove, animateClearAll };
  })();

  // ── PlaceBetFlow ───────────────────────────────────────────────────────────
  const PlaceBetFlow = (() => {
    function start(btn) {
      inFlight = true;
      btn.disabled = true;
      btn.setAttribute('aria-busy', 'true');
      btn.innerHTML = '<span class="spinner"></span>';
    }
    function succeed(btn, data) {
      btn.innerHTML = '<span>&#10003; Placed!</span>';
      btn.classList.add('slip-place-btn--success');
      document.dispatchEvent(new CustomEvent('betplaced', {
        detail: {
          bet_id: data.bet_id,
          stake: data.stake,
          total_odds: data.total_odds,
          potential_return: data.potential_return,
        },
      }));
      setTimeout(() => {
        const items = selectionsEl ? [...selectionsEl.querySelectorAll('.slip-item')] : [];
        RemovalAnimator.animateClearAll(items, () => {
          slip = [];
          render();
          btn.innerHTML = 'Place Bet';
          btn.classList.remove('slip-place-btn--success');
          btn.disabled = false;
          btn.removeAttribute('aria-busy');
          inFlight = false;
          // close mobile drawer on success
          const drawer = document.getElementById('slip-drawer');
          const overlay = document.getElementById('slip-overlay');
          if (drawer) drawer.classList.remove('open');
          if (overlay) overlay.classList.remove('open');
          document.body.style.overflow = '';
        });
      }, 1500);
    }
    function fail(btn, msg) {
      btn.innerHTML = 'Place Bet';
      btn.classList.remove('slip-place-btn--loading');
      btn.disabled = false;
      btn.setAttribute('aria-busy', 'false');
      inFlight = false;
      showToast(msg || 'Something went wrong. Please try again.', 'error');
    }
    return { start, succeed, fail };
  })();

  // ── EditMode ───────────────────────────────────────────────────────────────
  const EditMode = (() => {
    function activate(wrapEl) {
      const input = wrapEl.querySelector('.js-stake-input');
      if (!input) return;
      input.classList.add('stake-input--active');
      input.focus();
    }
    function deactivate(wrapEl) {
      const input = wrapEl.querySelector('.js-stake-input');
      if (input) input.classList.remove('stake-input--active');
    }
    return { activate, deactivate };
  })();

  // ── HistoryTab ─────────────────────────────────────────────────────────────
  const HistoryTab = (() => {
    function statusBadgeClass(s) {
      if (s === 'won') return 'badge--green';
      if (s === 'lost') return 'badge--red';
      if (s === 'open') return 'badge--blue';
      return 'badge--gray';
    }
    function formatDate(isoStr) {
      const d = new Date(isoStr);
      const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      const day = String(d.getDate()).padStart(2, '0');
      const hr  = String(d.getHours()).padStart(2, '0');
      const min = String(d.getMinutes()).padStart(2, '0');
      return `${day} ${months[d.getMonth()]} ${hr}:${min}`;
    }
    function renderRow(bet) {
      const returnVal = (bet.status !== 'open' && parseFloat(bet.actual_return) > 0)
        ? bet.actual_return : bet.potential_return;
      const fmtOdds = OddsFormatter.formatOdds(bet.total_odds, oddsFormat());
      const selText = bet.selections.length
        ? escHtml(bet.selections[0].selection_name) + (bet.selections.length > 1 ? ` +${bet.selections.length - 1}` : '')
        : '';
      return `<div class="slip-history-row">
        <div class="slip-history-row__header">
          <span class="badge ${statusBadgeClass(bet.status)}">${escHtml(bet.status)}</span>
          <span class="slip-history-row__type">${escHtml(bet.bet_type)}</span>
          <span class="slip-history-row__date">${formatDate(bet.placed_at)}</span>
        </div>
        ${selText ? `<div class="slip-history-row__selection">${selText}</div>` : ''}
        <div class="slip-history-row__amounts">
          <span>Stake: <strong>$${escHtml(bet.stake)}</strong></span>
          <span>Odds: <strong>${escHtml(fmtOdds)}</strong></span>
          <span>Return: <strong style="color:var(--green);">$${escHtml(returnVal)}</strong></span>
        </div>
      </div>`;
    }
    async function load() {
      if (!historyEl || !historySkeletonEl) return;
      historySkeletonEl.style.display = 'block';
      historyEl.style.display = 'none';
      historyEl.innerHTML = '';
      try {
        const data = await api('/api/v1/bets/history/?limit=10');
        if (!Array.isArray(data) || data.length === 0) {
          historyEl.innerHTML = '<div class="slip-history__empty">No bets yet</div>';
        } else {
          historyEl.innerHTML = data.map(renderRow).join('');
        }
      } catch (e) {
        if (e.message && e.message.includes('401')) {
          historyEl.innerHTML = `<div class="slip-history__empty"><a href="/accounts/login/">Sign in</a> to see your bet history</div>`;
        } else {
          historyEl.innerHTML = '<div class="slip-history__empty">Could not load history</div>';
        }
      } finally {
        historySkeletonEl.style.display = 'none';
        historyEl.style.display = 'block';
      }
    }
    return { load };
  })();

  // ── DrawerGestures ─────────────────────────────────────────────────────────
  const DrawerGestures = (() => {
    let startY = 0;
    let fromHandle = false;
    function getFocusable(el) {
      return [...el.querySelectorAll(
        'a[href],button:not([disabled]),input,select,textarea,[tabindex]:not([tabindex="-1"])'
      )];
    }
    function trapFocus(drawerEl, e) {
      const focusable = getFocusable(drawerEl);
      if (!focusable.length) return;
      const first = focusable[0];
      const last  = focusable[focusable.length - 1];
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === first) { e.preventDefault(); last.focus(); }
        } else {
          if (document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
      }
    }
    function init(drawerEl, closeFn) {
      if (!drawerEl) return;
      const handle = drawerEl.querySelector('.slip-drawer__handle');
      if (handle) {
        handle.addEventListener('touchstart', e => {
          startY = e.touches[0].clientY;
          fromHandle = true;
        }, { passive: true });
      }
      drawerEl.addEventListener('touchend', e => {
        if (!fromHandle) return;
        fromHandle = false;
        if (e.changedTouches[0].clientY - startY > 80) closeFn();
      }, { passive: true });
      // Focus trap via MutationObserver watching 'open' class
      const trapHandler = e => trapFocus(drawerEl, e);
      const openObs = new MutationObserver(() => {
        if (drawerEl.classList.contains('open')) {
          drawerEl.addEventListener('keydown', trapHandler);
        } else {
          drawerEl.removeEventListener('keydown', trapHandler);
        }
      });
      openObs.observe(drawerEl, { attributes: true, attributeFilter: ['class'] });
    }
    return { init };
  })();

  // ── Helpers ────────────────────────────────────────────────────────────────
  function renderOddsChangeBadge(item) {
    if (!item._prev_odds) return '';
    const fmt = oddsFormat();
    const arrow = item._odds_direction === 'up'
      ? '<span class="odds-change-badge__arrow--up">&#9650;</span>'
      : '<span class="odds-change-badge__arrow--down">&#9660;</span>';
    return `<div class="odds-change-badge">
      <span class="odds-change-badge__old">${OddsFormatter.formatOdds(item._prev_odds, fmt)}</span>
      <span class="odds-change-badge__new">${OddsFormatter.formatOdds(item._new_odds || item.odds, fmt)}</span>
      ${arrow}
    </div>`;
  }

  function renderSingleItem(item) {
    const wrap = document.createElement('div');
    wrap.className = 'slip-item';
    if (item._suspended) wrap.classList.add('slip-item--suspended');
    wrap.dataset.oddId = item.odd_id;
    wrap.innerHTML = `
      <button class="slip-item__remove" title="Remove">&#10005;</button>
      <button class="slip-item__edit" title="Edit stake" aria-label="Edit stake">&#9999;&#65039;</button>
      <div class="slip-item__event">${escHtml(item.event_name)}</div>
      <div class="slip-item__market">${escHtml(item.market_name)}</div>
      <div class="slip-item__selection">${escHtml(item.selection_name)}</div>
      <div class="slip-item__odds">${OddsFormatter.formatOdds(item.odds, oddsFormat())}</div>
      ${renderOddsChangeBadge(item)}
      <div class="stake-wrap">
        <input class="stake-input js-stake-input" type="number" min="0.01" step="0.01"
               placeholder="Stake" data-odd-id="${item.odd_id}" data-odds="${item.odds}" />
        <div class="stake-return">
          <span>Potential return</span>
          <span class="stake-return__value js-return-val">—</span>
        </div>
      </div>
    `;
    wrap.querySelector('.slip-item__remove').addEventListener('click', () => removeSelection(item.odd_id));
    wrap.querySelector('.slip-item__edit').addEventListener('click', () => EditMode.activate(wrap));
    const stakeInput = wrap.querySelector('.js-stake-input');
    stakeInput.addEventListener('input', e => {
      const stake = parseFloat(e.target.value) || 0;
      const odds  = parseFloat(e.target.dataset.odds) || 1;
      const ret   = (stake * odds).toFixed(2);
      wrap.querySelector('.js-return-val').textContent = stake > 0 ? `$${ret}` : '—';
    });
    stakeInput.addEventListener('blur', () => EditMode.deactivate(wrap));
    return wrap;
  }

  // ── Core render ────────────────────────────────────────────────────────────
  function render() {
    const count = slip.length;
    countEls = $$('.js-slip-count');
    countEls.forEach(el => { el.textContent = count; });

    // Mobile FAB
    const fab      = document.getElementById('mobile-slip-fab');
    const fabCount = document.getElementById('mobile-slip-count');
    if (fab) fab.style.display = count > 0 ? 'flex' : 'none';
    if (fabCount) fabCount.textContent = count;

    // Auto-expand panel when first selection added
    if (count === 1) CollapseManager.expand();

    if (!selectionsEl) return;

    if (count === 0) {
      emptyEl       && (emptyEl.style.display = 'flex');
      footerEl      && (footerEl.style.display = 'none');
      accaSummaryEl && (accaSummaryEl.style.display = 'none');
      selectionsEl.innerHTML = '';
      return;
    }

    emptyEl  && (emptyEl.style.display = 'none');
    footerEl && (footerEl.style.display = 'block');

    if (activeTab === 'singles') {
      accaSummaryEl && (accaSummaryEl.style.display = 'none');
      selectionsEl.innerHTML = '';
      slip.forEach(item => selectionsEl.appendChild(renderSingleItem(item)));
    } else if (activeTab === 'multi') {
      accaSummaryEl && (accaSummaryEl.style.display = slip.length > 1 ? 'block' : 'none');
      selectionsEl.innerHTML = '';
      slip.forEach(item => {
        const el = document.createElement('div');
        el.className = 'slip-item';
        if (item._suspended) el.classList.add('slip-item--suspended');
        el.innerHTML = `
          <button class="slip-item__remove" data-odd-id="${item.odd_id}" title="Remove">&#10005;</button>
          <div class="slip-item__event">${escHtml(item.event_name)}</div>
          <div class="slip-item__market">${escHtml(item.market_name)}</div>
          <div class="slip-item__selection">${escHtml(item.selection_name)}</div>
          <div class="slip-item__odds">${OddsFormatter.formatOdds(item.odds, oddsFormat())}</div>
          ${renderOddsChangeBadge(item)}
        `;
        el.querySelector('.slip-item__remove').addEventListener('click', e =>
          removeSelection(e.currentTarget.dataset.oddId)
        );
        selectionsEl.appendChild(el);
      });
      if (slip.length > 1) {
        const totalOdds = slip.reduce((acc, s) => acc * parseFloat(s.odds), 1);
        if (totalOddsEl) totalOddsEl.textContent = OddsFormatter.formatOdds(totalOdds, oddsFormat());
      }
    }

    // Disable place btn if any suspended
    const hasSuspended = slip.some(s => s._suspended);
    if (placeBtnEl) placeBtnEl.disabled = hasSuspended || inFlight;
  }

  // ── Tab management ─────────────────────────────────────────────────────────
  function setTab(tab) {
    activeTab = tab;

    tabSingles && tabSingles.classList.toggle('active', tab === 'singles');
    tabSingles && tabSingles.setAttribute('aria-selected', String(tab === 'singles'));
    tabMulti   && tabMulti.classList.toggle('active', tab === 'multi');
    tabMulti   && tabMulti.setAttribute('aria-selected', String(tab === 'multi'));
    tabHistory && tabHistory.classList.toggle('active', tab === 'history');
    tabHistory && tabHistory.setAttribute('aria-selected', String(tab === 'history'));

    if (historyEl)         historyEl.style.display         = tab === 'history' ? 'block' : 'none';
    if (historySkeletonEl) historySkeletonEl.style.display  = 'none';
    if (selectionsEl)      selectionsEl.style.display      = tab !== 'history' ? 'block' : 'none';
    if (accaSummaryEl)     accaSummaryEl.style.display      = (tab === 'multi' && slip.length > 1) ? 'block' : 'none';
    if (emptyEl)           emptyEl.style.display            = (tab !== 'history' && slip.length === 0) ? 'flex' : 'none';
    if (footerEl)          footerEl.style.display           = (tab !== 'history' && slip.length > 0) ? 'block' : 'none';

    if (tab === 'history') HistoryTab.load();
    else render();
  }

  // ── API actions ────────────────────────────────────────────────────────────
  async function loadSlip() {
    try {
      const data = await api('/api/v1/bets/slip/');
      slip = data.slip || [];
      firstLoadDone = true;
      render();
    } catch (_) {
      firstLoadDone = true;
    }
  }

  async function addSelection(oddData) {
    try {
      const data = await api('/api/v1/bets/slip/add/', 'POST', { odd_id: oddData.odd_id });
      slip = data.slip || [];
      CollapseManager.expand();
      render();
      highlightOddBtn(oddData.odd_id, true);
    } catch (_) {
      showToast('Could not add selection. Please try again.', 'error');
    }
  }

  async function removeSelection(oddId) {
    const itemEl = selectionsEl && selectionsEl.querySelector(`[data-odd-id="${oddId}"]`);
    if (itemEl) {
      RemovalAnimator.animateRemove(itemEl, null);
    }
    try {
      const data = await api('/api/v1/bets/slip/remove/', 'POST', { odd_id: String(oddId) });
      slip = data.slip || [];
      render();
      highlightOddBtn(oddId, false);
    } catch (_) {
      // Reverse: reload slip from server to restore state
      await loadSlip();
      showToast('Could not remove selection.', 'error');
    }
  }

  async function clearAll() {
    const items = selectionsEl ? [...selectionsEl.querySelectorAll('.slip-item')] : [];
    RemovalAnimator.animateClearAll(items, async () => {
      try {
        await api('/api/v1/bets/slip/clear/', 'POST');
        slip = [];
        $$('.odd-btn.selected').forEach(btn => btn.classList.remove('selected'));
        render();
      } catch (_) {
        await loadSlip();
      }
    });
  }

  async function placeBet() {
    if (inFlight || !placeBtnEl) return;
    const betType = activeTab === 'multi' ? 'accumulator' : 'single';
    let stake;

    if (betType === 'accumulator') {
      const si = document.getElementById('acca-stake-input');
      stake = si ? parseFloat(si.value) : 0;
    } else {
      const si = selectionsEl && selectionsEl.querySelector('.js-stake-input');
      stake = si ? parseFloat(si.value) : 0;
    }

    if (!stake || stake <= 0) {
      showToast('Please enter a valid stake.', 'error');
      return;
    }

    PlaceBetFlow.start(placeBtnEl);
    try {
      const data = await api('/api/v1/bets/place/', 'POST', { stake, bet_type: betType });
      PlaceBetFlow.succeed(placeBtnEl, data);
    } catch (e) {
      let msg = 'Something went wrong. Please try again.';
      try { const parsed = JSON.parse(e.message); msg = parsed.error || msg; } catch (_) {}
      PlaceBetFlow.fail(placeBtnEl, msg);
    }
  }

  function highlightOddBtn(oddId, selected) {
    $$(`[data-odd-id="${oddId}"]`).forEach(btn => {
      if (btn.classList.contains('odd-btn')) btn.classList.toggle('selected', selected);
    });
  }

  // ── Mobile drawer init ─────────────────────────────────────────────────────
  function initDrawer() {
    const fab      = document.getElementById('mobile-slip-fab');
    const drawer   = document.getElementById('slip-drawer');
    const overlay  = document.getElementById('slip-overlay');
    const closeBtn = document.getElementById('slip-drawer-close');

    function openDrawer() {
      drawer  && drawer.classList.add('open');
      overlay && overlay.classList.add('open');
      document.body.style.overflow = 'hidden';
    }
    function closeDrawer() {
      drawer  && drawer.classList.remove('open');
      overlay && overlay.classList.remove('open');
      document.body.style.overflow = '';
    }

    fab     && fab.addEventListener('click', openDrawer);
    overlay && overlay.addEventListener('click', closeDrawer);
    closeBtn && closeBtn.addEventListener('click', closeDrawer);

    DrawerGestures.init(drawer, closeDrawer);
  }

  // ── Listen for betplaced to refresh history ────────────────────────────────
  document.addEventListener('betplaced', () => {
    if (activeTab === 'history') HistoryTab.load();
  });

  // ── Public init ────────────────────────────────────────────────────────────
  function init() {
    selectionsEl      = document.getElementById('slip-selections');
    emptyEl           = document.getElementById('slip-empty');
    footerEl          = document.getElementById('slip-footer');
    tabSingles        = document.getElementById('tab-singles');
    tabMulti          = document.getElementById('tab-multi');
    tabHistory        = document.getElementById('tab-history');
    accaSummaryEl     = document.getElementById('acca-summary');
    totalOddsEl       = document.getElementById('acca-total-odds');
    totalReturnEl     = document.getElementById('acca-total-return');
    placeBtnEl        = document.getElementById('slip-place-btn');
    historyEl         = document.getElementById('slip-history');
    historySkeletonEl = document.getElementById('slip-history-skeleton');
    collapseBtn       = document.getElementById('slip-collapse-btn');
    slipPanel         = document.querySelector('.bet-slip-panel');

    // Load slip then start polling
    loadSlip().then(() => OddsPoller.init());

    // Tab switching
    tabSingles && tabSingles.addEventListener('click', () => setTab('singles'));
    tabMulti   && tabMulti.addEventListener('click',   () => setTab('multi'));
    tabHistory && tabHistory.addEventListener('click',  () => setTab('history'));

    // Place bet
    placeBtnEl && placeBtnEl.addEventListener('click', placeBet);

    // Clear all
    const clearBtn = document.getElementById('slip-clear-btn');
    clearBtn && clearBtn.addEventListener('click', clearAll);

    // Collapse
    CollapseManager.init();

    // Mobile drawer
    initDrawer();

    // Acca stake input live calc
    document.addEventListener('input', e => {
      if (e.target && e.target.id === 'acca-stake-input') {
        const stake = parseFloat(e.target.value) || 0;
        const totalOdds = slip.reduce((acc, s) => acc * parseFloat(s.odds), 1);
        const ret = (stake * totalOdds).toFixed(2);
        const retEl = document.getElementById('acca-total-return');
        if (retEl) retEl.textContent = stake > 0 ? `$${ret}` : '—';
      }
    });
  }

  // Public: called from odd-btn click handlers
  function toggleOdd(oddData) {
    const exists = slip.some(s => s.odd_id === String(oddData.odd_id));
    if (exists) removeSelection(String(oddData.odd_id));
    else addSelection(oddData);
  }

  return { init, toggleOdd, loadSlip };
})();

/* ============================================================
   ODD BUTTONS — delegated click handler
   ============================================================ */

function initOddButtons() {
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.odd-btn');
    if (!btn) return;
    if (btn.classList.contains('suspended')) return;

    BetSlip.toggleOdd({
      odd_id:         btn.dataset.oddId,
      event_name:     btn.dataset.eventName,
      market_name:    btn.dataset.marketName,
      selection_name: btn.dataset.selectionName,
      odds:           btn.dataset.odds,
    });
  });
}

/* ============================================================
   TOAST NOTIFICATIONS
   ============================================================ */

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'messages-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `message message--${type}`;
  toast.innerHTML = `<span>${escHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

/* ============================================================
   DISMISS DJANGO MESSAGES
   ============================================================ */

function initMessages() {
  $$('.message').forEach(msg => {
    setTimeout(() => {
      msg.style.opacity = '0';
      msg.style.transition = 'opacity 0.4s ease';
      setTimeout(() => msg.remove(), 400);
    }, 5000);
  });
}

/* ============================================================
   LAZY LOAD IMAGES
   ============================================================ */

function initLazyLoad() {
  if (!('IntersectionObserver' in window)) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        if (img.dataset.src) {
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
        }
        observer.unobserve(img);
      }
    });
  }, { rootMargin: '200px' });

  $$('img[data-src]').forEach(img => observer.observe(img));
}

/* ============================================================
   SEARCH
   ============================================================ */

function initSearch() {
  const searchInput = document.getElementById('navbar-search');
  if (!searchInput) return;

  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const q = searchInput.value.trim();
      // Future: show instant search results dropdown
    }, 300);
  });
}

/* ============================================================
   HELPERS
   ============================================================ */

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/* ============================================================
   INIT
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initCarousel();
  BetSlip.init();
  initOddButtons();
  initMessages();
  initLazyLoad();
  initSearch();
});
