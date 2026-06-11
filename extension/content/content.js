// TrustLens Chrome Extension — Content Script
// Renders an in-page floating "trust badge" card driven by messages from the
// background worker (triggered via the right-click context menu).

(function () {
  const CARD_ID = 'trustlens-overlay-card';

  function removeCard() {
    const existing = document.getElementById(CARD_ID);
    if (existing) existing.remove();
  }

  function createShell() {
    removeCard();
    const card = document.createElement('div');
    card.id = CARD_ID;
    card.className = 'tl-card';
    card.innerHTML = `
      <div class="tl-header">
        <div class="tl-brand"><span class="tl-logo">T</span><span>TrustLens</span></div>
        <button class="tl-close" aria-label="Close">&times;</button>
      </div>
      <div class="tl-body"></div>
    `;
    document.body.appendChild(card);
    card.querySelector('.tl-close').addEventListener('click', removeCard);
    // auto-dismiss handled per-state below
    return card;
  }

  function scoreColor(score) {
    return score >= 80 ? '#22c55e' : score >= 40 ? '#eab308' : '#ef4444';
  }

  function renderLoading() {
    const card = createShell();
    card.querySelector('.tl-body').innerHTML = `
      <div class="tl-loading">
        <div class="tl-spinner"></div>
        <span>বিশ্লেষণ চলছে…</span>
      </div>`;
  }

  function renderError(message) {
    const card = createShell();
    card.querySelector('.tl-body').innerHTML = `
      <div class="tl-error">
        <strong>সংযোগ ব্যর্থ হয়েছে</strong>
        <span>${escapeHtml(message || 'Unknown error')}</span>
      </div>`;
    setTimeout(removeCard, 8000);
  }

  function renderResult(data) {
    const card = createShell();
    const body = card.querySelector('.tl-body');

    if (data && data.scrape_failed) {
      body.innerHTML = `
        <div class="tl-error">
          <strong>কনটেন্ট আনা যায়নি</strong>
          <span>এই পোস্ট/লিংক থেকে লেখা সংগ্রহ করা যায়নি। সরাসরি লেখা কপি করে পপআপে যাচাই করুন।</span>
        </div>`;
      return;
    }

    const score = Math.round((data && data.trust_score) || 0);
    const color = scoreColor(score);
    const verdict = (data && (data.verdict_bn || data.verdict)) || '';

    const pillars = (data && Array.isArray(data.pillars) ? data.pillars : [])
      .filter((p) => p && p.active)
      .map(
        (p) => `
          <div class="tl-pillar">
            <span>${escapeHtml(p.name_bn || p.name || '')}</span>
            <span class="tl-pillar-score">${Math.round(p.score || 0)}</span>
          </div>`
      )
      .join('');

    body.innerHTML = `
      <div class="tl-score" style="color:${color}">${score}<span class="tl-score-max">/100</span></div>
      ${verdict ? `<div class="tl-verdict">${escapeHtml(verdict)}</div>` : ''}
      ${pillars ? `<div class="tl-pillars">${pillars}</div>` : ''}
    `;
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
