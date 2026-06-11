// TrustLens Chrome Extension — Popup
// Network call lives in the background service worker (single CORS-friendly
// place). UI mirrors the website: glass cards, circular trust gauge, pillar
// bars, and a bilingual BN/EN toggle. Theme follows the browser via CSS
// prefers-color-scheme, so no JS theme handling is needed.

// ---------------------------------------------------------------------------
// i18n
// ---------------------------------------------------------------------------
const STRINGS = {
  bn: {
    subtitle: 'বিশ্বাসযোগ্যতা যাচাই',
    placeholder: 'পোস্ট বা লিংক পেস্ট করুন...',
    analyze: 'বিশ্লেষণ করুন',
    analyzing: 'বিশ্লেষণ চলছে...',
    langBtn: 'EN',
    emptyError: 'অনুগ্রহ করে কিছু লিখুন বা লিংক দিন।',
    scrapeFailedTitle: 'কনটেন্ট আনা যায়নি',
    scrapeFailedText: 'এই লিংক থেকে লেখা সংগ্রহ করা যায়নি। সরাসরি পোস্টের লেখা কপি করে এখানে পেস্ট করুন।',
    hint: 'টিপ: যেকোনো পেজে লেখা সিলেক্ট করে ডান-ক্লিক করে "TrustLens" দিয়ে যাচাই করুন।',
    errorPrefix: 'ত্রুটি: ',
    tabCheck: 'যাচাই',
    tabHistory: 'ইতিহাস',
    historyTitle: 'সাম্প্রতিক যাচাই',
    historyClear: 'মুছুন',
    historyEmpty: 'এখনও কোনো যাচাই নেই। প্রথম যাচাই করলে এখানে দেখা যাবে।',
    justNow: 'এইমাত্র',
    minsAgo: 'মিনিট আগে',
    hoursAgo: 'ঘণ্টা আগে',
    daysAgo: 'দিন আগে',
  },
  en: {
    subtitle: 'Trust verification',
    placeholder: 'Paste a post or link...',
    analyze: 'Analyze',
    analyzing: 'Analyzing...',
    langBtn: 'বাং',
    emptyError: 'Please enter some text or a link.',
    scrapeFailedTitle: 'Could not fetch content',
    scrapeFailedText: 'We could not extract text from this link. Copy the post text directly and paste it here.',
    hint: 'Tip: select text on any page, right-click, and choose "TrustLens" to check it.',
    errorPrefix: 'Error: ',
    tabCheck: 'Check',
    tabHistory: 'History',
    historyTitle: 'Recent checks',
    historyClear: 'Clear',
    historyEmpty: 'No checks yet. Your verified items will appear here.',
    justNow: 'just now',
    minsAgo: 'min ago',
    hoursAgo: 'hr ago',
    daysAgo: 'd ago',
  },
};

const HISTORY_KEY = 'tl_history';
const HISTORY_LIMIT = 25;

let lang = 'bn';

// ---------------------------------------------------------------------------
// Elements
// ---------------------------------------------------------------------------
const input = document.getElementById('input');
const btn = document.getElementById('analyzeBtn');
const langToggle = document.getElementById('langToggle');
const subtitleEl = document.getElementById('subtitle');
const loadingEl = document.getElementById('loading');
const loadingText = document.getElementById('loadingText');
const resultDiv = document.getElementById('result');
const gaugeFill = document.getElementById('gaugeFill');
const scoreEl = document.getElementById('score');
const verdictEl = document.getElementById('verdict');
const pillarsEl = document.getElementById('pillars');
const scrapeFailedEl = document.getElementById('scrapeFailed');
const scrapeFailedTitle = document.getElementById('scrapeFailedTitle');
const scrapeFailedText = document.getElementById('scrapeFailedText');
const errorEl = document.getElementById('error');
const hintEl = document.getElementById('hint');

// Tabs + history
const tabCheckBtn = document.getElementById('tabCheck');
const tabHistoryBtn = document.getElementById('tabHistory');
const viewCheck = document.getElementById('viewCheck');
const viewHistory = document.getElementById('viewHistory');
const historyTitleEl = document.getElementById('historyTitle');
const historyClearBtn = document.getElementById('historyClear');
const historyListEl = document.getElementById('historyList');
const historyEmptyEl = document.getElementById('historyEmpty');

const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 52; // r=52 → ~326.7

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function trustColor(score) {
  // Resolve against the active (light/dark) CSS variables.
  const styles = getComputedStyle(document.documentElement);
  if (score >= 70) return styles.getPropertyValue('--trust-high').trim() || '#22c55e';
  if (score >= 40) return styles.getPropertyValue('--trust-medium').trim() || '#eab308';
  return styles.getPropertyValue('--trust-low').trim() || '#ef4444';
}

function applyLang() {
  const t = STRINGS[lang];
  subtitleEl.textContent = t.subtitle;
  input.placeholder = t.placeholder;
  btn.textContent = t.analyze;
  langToggle.textContent = t.langBtn;
  hintEl.textContent = t.hint;
  tabCheckBtn.textContent = t.tabCheck;
  tabHistoryBtn.textContent = t.tabHistory;
  historyTitleEl.textContent = t.historyTitle;
  historyClearBtn.textContent = t.historyClear;
  historyEmptyEl.textContent = t.historyEmpty;
  document.documentElement.lang = lang;
  // Re-render history so item labels follow the active language.
  if (!viewHistory.classList.contains('hidden')) renderHistory();
}

langToggle.addEventListener('click', () => {
  lang = lang === 'bn' ? 'en' : 'bn';
  chrome.storage?.local.set({ tl_lang: lang });
  applyLang();
});

// ---------------------------------------------------------------------------
// View states
// ---------------------------------------------------------------------------
function hideAll() {
  loadingEl.classList.add('hidden');
  resultDiv.classList.add('hidden');
  scrapeFailedEl.classList.add('hidden');
  errorEl.classList.add('hidden');
}

function showLoading() {
  hideAll();
  loadingText.textContent = STRINGS[lang].analyzing;
  loadingEl.classList.remove('hidden');
}

function showError(message) {
  hideAll();
  errorEl.textContent = STRINGS[lang].errorPrefix + message;
  errorEl.classList.remove('hidden');
}

function showScrapeFailed() {
  hideAll();
  scrapeFailedTitle.textContent = STRINGS[lang].scrapeFailedTitle;
  scrapeFailedText.textContent = STRINGS[lang].scrapeFailedText;
  scrapeFailedEl.classList.remove('hidden');
}

function showResult(data) {
  hideAll();
  const score = Math.round(data.trust_score || 0);
  const color = trustColor(score);

  // Gauge ring
  scoreEl.textContent = String(score);
  scoreEl.style.color = color;
  gaugeFill.style.stroke = color;
  // Start from empty then animate (reflow trick keeps the transition).
  gaugeFill.style.strokeDashoffset = String(GAUGE_CIRCUMFERENCE);
  void gaugeFill.getBoundingClientRect();
  const offset = GAUGE_CIRCUMFERENCE * (1 - score / 100);
  requestAnimationFrame(() => { gaugeFill.style.strokeDashoffset = String(offset); });

  verdictEl.textContent =
    (lang === 'bn' ? data.verdict_bn : data.verdict) || data.verdict_bn || data.verdict || '';
  verdictEl.style.color = color;

  // Pillars with mini progress bars
  pillarsEl.innerHTML = '';
  (data.pillars || []).forEach((p) => {
    if (!p || !p.active) return;
    const pScore = Math.round(p.score || 0);
    const pColor = trustColor(pScore);

    const row = document.createElement('div');
    row.className = 'pillar';

    const dot = document.createElement('span');
    dot.className = 'pillar-dot';
    dot.style.background = pColor;

    const name = document.createElement('span');
    name.className = 'pillar-name';
    name.textContent = (lang === 'bn' ? p.name_bn : p.name) || p.name_bn || p.name || '';

    const bar = document.createElement('span');
    bar.className = 'pillar-bar';
    const barFill = document.createElement('span');
    barFill.className = 'pillar-bar-fill';
    barFill.style.background = pColor;
    barFill.style.width = '0%';
    bar.appendChild(barFill);

    const val = document.createElement('span');
    val.className = 'pillar-score';
    val.textContent = String(pScore);

    row.append(dot, name, bar, val);
    pillarsEl.appendChild(row);
    requestAnimationFrame(() => { barFill.style.width = `${pScore}%`; });
  });

  resultDiv.classList.remove('hidden');
  saveToHistory(data);
}

// ---------------------------------------------------------------------------
// History (chrome.storage.local) — recent checks list with re-open + clear
// ---------------------------------------------------------------------------
function getHistory() {
  return new Promise((resolve) => {
    chrome.storage?.local.get([HISTORY_KEY], (res) => {
      resolve((res && Array.isArray(res[HISTORY_KEY])) ? res[HISTORY_KEY] : []);
    });
  });
}

async function saveToHistory(data) {
  if (!data || typeof data.trust_score !== 'number') return;
  const query = input.value.trim();
  const item = {
    score: Math.round(data.trust_score),
    verdict: data.verdict || '',
    verdict_bn: data.verdict_bn || '',
    query: query.slice(0, 200),
    ts: Date.now(),
    data, // full payload so we can re-open the result instantly
  };
  const list = await getHistory();
  // De-dupe by identical query (keep newest at top).
  const filtered = list.filter((h) => h.query !== item.query);
  filtered.unshift(item);
  const trimmed = filtered.slice(0, HISTORY_LIMIT);
  chrome.storage?.local.set({ [HISTORY_KEY]: trimmed });
}

function timeAgo(ts) {
  const t = STRINGS[lang];
  const diff = Math.max(0, Date.now() - ts);
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return t.justNow;
  if (mins < 60) return `${mins} ${t.minsAgo}`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} ${t.hoursAgo}`;
  const days = Math.floor(hrs / 24);
  return `${days} ${t.daysAgo}`;
}

function looksLikeUrl(s) {
  return /^https?:\/\//i.test(s);
}

async function renderHistory() {
  const list = await getHistory();
  historyListEl.innerHTML = '';

  if (!list.length) {
    historyEmptyEl.classList.remove('hidden');
    historyClearBtn.classList.add('hidden');
    return;
  }
  historyEmptyEl.classList.add('hidden');
  historyClearBtn.classList.remove('hidden');

  list.forEach((h) => {
    const score = Math.round(h.score || 0);
    const color = trustColor(score);

    const row = document.createElement('button');
    row.className = 'history-item';
    row.type = 'button';

    const badge = document.createElement('span');
    badge.className = 'history-score';
    badge.textContent = String(score);
    badge.style.color = color;
    badge.style.borderColor = color;

    const mid = document.createElement('span');
    mid.className = 'history-mid';

    const label = document.createElement('span');
    label.className = 'history-label';
    const q = h.query || '';
    label.textContent = looksLikeUrl(q)
      ? q.replace(/^https?:\/\//i, '').slice(0, 48)
      : (q.slice(0, 48) || (lang === 'bn' ? h.verdict_bn : h.verdict) || '');
    if (looksLikeUrl(q)) label.title = q;

    const meta = document.createElement('span');
    meta.className = 'history-meta';
    const verdict = (lang === 'bn' ? h.verdict_bn : h.verdict) || h.verdict_bn || h.verdict || '';
    meta.textContent = `${verdict}${verdict ? ' · ' : ''}${timeAgo(h.ts)}`;

    mid.append(label, meta);
    row.append(badge, mid);

    // Re-open the stored result on click.
    row.addEventListener('click', () => {
      input.value = h.query || '';
      switchTab('check');
      if (h.data) showResult(h.data);
    });

    historyListEl.appendChild(row);
  });
}

historyClearBtn.addEventListener('click', () => {
  chrome.storage?.local.set({ [HISTORY_KEY]: [] }, renderHistory);
});

// ---------------------------------------------------------------------------
// Tab switching
// ---------------------------------------------------------------------------
function switchTab(name) {
  const isHistory = name === 'history';
  tabHistoryBtn.classList.toggle('active', isHistory);
  tabCheckBtn.classList.toggle('active', !isHistory);
  viewHistory.classList.toggle('hidden', !isHistory);
  viewCheck.classList.toggle('hidden', isHistory);
  if (isHistory) renderHistory();
}

tabCheckBtn.addEventListener('click', () => switchTab('check'));
tabHistoryBtn.addEventListener('click', () => switchTab('history'));

// ---------------------------------------------------------------------------
// Analyze flow (delegated to background worker)
// ---------------------------------------------------------------------------
async function runAnalyze() {
  const content = input.value.trim();
  if (!content) {
    showError(STRINGS[lang].emptyError);
    return;
  }

  btn.disabled = true;
  btn.textContent = STRINGS[lang].analyzing;
  showLoading();

  try {
    const result = await chrome.runtime.sendMessage({
      type: 'TRUSTLENS_ANALYZE',
      content,
    });

    if (!result) {
      showError('No response from background');
    } else if (!result.ok) {
      showError(result.error || 'Unknown error');
    } else if (result.data && result.data.scrape_failed) {
      showScrapeFailed();
    } else {
      showResult(result.data);
    }
  } catch (err) {
    showError(err.message || 'Unexpected error');
  } finally {
    btn.disabled = false;
    btn.textContent = STRINGS[lang].analyze;
  }
}

btn.addEventListener('click', runAnalyze);
input.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') runAnalyze();
});

// ---------------------------------------------------------------------------
// Init: restore language, prefill from the active tab URL
// ---------------------------------------------------------------------------
chrome.storage?.local.get(['tl_lang'], (res) => {
  if (res && (res.tl_lang === 'en' || res.tl_lang === 'bn')) lang = res.tl_lang;
  applyLang();
});

chrome.tabs?.query({ active: true, currentWindow: true }, (tabs) => {
  const url = tabs && tabs[0] && tabs[0].url;
  if (url && !url.startsWith('chrome://') && !url.startsWith('chrome-extension://')) {
    input.value = url;
  }
});
