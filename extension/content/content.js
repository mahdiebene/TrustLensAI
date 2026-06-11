// TrustLens Chrome Extension — Content Script
// Renders an in-page floating "trust badge" card driven by messages from the
// background worker (triggered via the right-click context menu). UI mirrors
// the website: glass card, circular trust gauge, pillar bars. The card auto-
// adapts to the page's light/dark via prefers-color-scheme in content.css.

(function () {
  const CARD_ID = 'trustlens-overlay-card';
  const GAUGE_C = 2 * Math.PI * 26; // r=26 → ~163.4

  // Canonical TrustLens mark — shield + scanning lens (matches favicon.svg).
  const LOGO_SVG =
    '<svg viewBox="0 0 32 32" width="18" height="18" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
    '<path d="M16 5 L25 8.2 V15 C25 20.2 21.4 24.2 16 26.5 C10.6 24.2 7 20.2 7 15 V8.2 Z" stroke="#3b82f6" stroke-width="1.6" stroke-linejoin="round" fill="none"></path>' +
    '<circle cx="14.5" cy="14" r="3.6" stroke="#3b82f6" stroke-width="1.6" fill="none"></circle>' +
    '<path d="M17.2 16.5 L20.5 19.8" stroke="#3b82f6" stroke-width="1.6" stroke-linecap="round"></path>' +
    '<circle cx="14.5" cy="14" r="0.95" fill="#3b82f6"></circle>' +
    '</svg>';

  function removeCard() {
    const existing = document.getElementById(CARD_ID);
    if (existing) existing.remove();
  }

  function createShell() {
    removeCard();
    const card = document.createElement('div');
    card.id = CARD_ID;
    card.className = 'tl-card';
    card.innerHTML =
      '<div class="tl-grain"></div>' +
      '<div class="tl-header">' +
        '<div class="tl-brand"><span class="tl-logo">' + LOGO_SVG + '</span><span class="tl-title">TrustLens</span></div>' +
        '<button class="tl-close" aria-label="Close">&times;</button>' +
      '</div>' +
      '<div class="tl-body"></div>';
    document.body.appendChild(card);
    card.querySelector('.tl-close').addEventListener('click', removeCard);
    requestAnimationFrame(() => card.classList.add('tl-show'));
    return card;
  }

  function scoreColor(score) {
    return score >= 70 ? '#16a34a' : score >= 40 ? '#ca8a04' : '#dc2626';
  }

  function renderLoading() {
    const card = createShell();
    card.querySelector('.tl-body').innerHTML =
      '<div class="tl-loading"><div class="tl-spinner"></div><span>বিশ্লেষণ চলছে…</span></div>';
  }

  function renderError(message) {
    const card = createShell();
    card.querySelector('.tl-body').innerHTML =
      '<div class="tl-note tl-note-error">' +
        '<strong>সংযোগ ব্যর্থ হয়েছে</strong>' +
        '<span>' + escapeHtml(message || 'Unknown error') + '</span>' +
      '</div>';
    setTimeout(removeCard, 8000);
  }

  function renderScrapeFailed() {
    const card = createShell();
    card.querySelector('.tl-body').innerHTML =
      '<div class="tl-note tl-note-warn">' +
        '<strong>কনটেন্ট আনা যায়নি</strong>' +
        '<span>এই পোস্ট/লিংক থেকে লেখা সংগ্রহ করা যায়নি। সরাসরি লেখা কপি করে পপআপে যাচাই করুন।</span>' +
      '</div>';
  }

  function renderResult(data) {
    if (data && data.scrape_failed) {
      renderScrapeFailed();
      return;
    }

    const card = createShell();
    const body = card.querySelector('.tl-body');

    const score = Math.round((data && data.trust_score) || 0);
    const color = scoreColor(score);
    const verdict = (data && (data.verdict_bn || data.verdict)) || '';
    const offset = GAUGE_C * (1 - score / 100);

    const pillars = (data && Array.isArray(data.pillars) ? data.pillars : [])
      .filter((p) => p && p.active)
      .map((p) => {
        const ps = Math.round(p.score || 0);
        const pc = scoreColor(ps);
        return (
          '<div class="tl-pillar">' +
            '<span class="tl-pillar-dot" style="background:' + pc + '"></span>' +
            '<span class="tl-pillar-name">' + escapeHtml(p.name_bn || p.name || '') + '</span>' +
            '<span class="tl-pillar-bar"><span class="tl-pillar-bar-fill" style="width:' + ps + '%;background:' + pc + '"></span></span>' +
            '<span class="tl-pillar-score">' + ps + '</span>' +
          '</div>'
        );
      })
      .join('');

    body.innerHTML =
      '<div class="tl-gauge">' +
        '<svg viewBox="0 0 64 64">' +
          '<circle class="tl-gauge-track" cx="32" cy="32" r="26"></circle>' +
          '<circle class="tl-gauge-fill" cx="32" cy="32" r="26" ' +
            'style="stroke:' + color + ';stroke-dasharray:' + GAUGE_C.toFixed(1) + ';stroke-dashoffset:' + GAUGE_C.toFixed(1) + '"></circle>' +
        '</svg>' +
        '<span class="tl-gauge-num" style="color:' + color + '">' + score + '</span>' +
      '</div>' +
      (verdict ? '<div class="tl-verdict" style="color:' + color + '">' + escapeHtml(verdict) + '</div>' : '') +
      (pillars ? '<div class="tl-hr"></div><div class="tl-pillars">' + pillars + '</div>' : '');

    // animate the ring after layout
    const fill = body.querySelector('.tl-gauge-fill');
    if (fill) requestAnimationFrame(() => { fill.style.strokeDashoffset = String(offset); });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (!msg || !msg.type) return;
    if (msg.type === 'TRUSTLENS_LOADING') renderLoading();
    else if (msg.type === 'TRUSTLENS_RESULT') renderResult(msg.data);
    else if (msg.type === 'TRUSTLENS_ERROR') renderError(msg.error);
  });
})();
