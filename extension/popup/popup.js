// TrustLens Chrome Extension — Popup
// Sends the analyze request through the background service worker so the
// network call lives in one CORS-friendly place, and supports bilingual UI.

// ---------------------------------------------------------------------------
// i18n
// ---------------------------------------------------------------------------
const STRINGS = {
  bn: {
    placeholder: 'পোস্ট বা লিংক পেস্ট করুন...',
    analyze: 'বিশ্লেষণ করুন',
    analyzing: 'বিশ্লেষণ চলছে...',
    langBtn: 'EN',
    emptyError: 'অনুগ্রহ করে কিছু লিখুন বা লিংক দিন।',
    scrapeFailedTitle: 'কনটেন্ট আনা যায়নি',
    scrapeFailedText: 'এই লিংক থেকে লেখা সংগ্রহ করা যায়নি। সরাসরি পোস্টের লেখা কপি করে এখানে পেস্ট করুন।',
    hint: 'টিপ: যেকোনো পেজে লেখা সিলেক্ট করে ডান-ক্লিক করে "TrustLens" দিয়ে যাচাই করুন।',
    errorPrefix: 'ত্রুটি: ',
  },
  en: {
    placeholder: 'Paste a post or link...',
    analyze: 'Analyze',
    analyzing: 'Analyzing...',
    langBtn: 'বাং',
    emptyError: 'Please enter some text or a link.',
    scrapeFailedTitle: 'Could not fetch content',
    scrapeFailedText: 'We could not extract text from this link. Copy the post text directly and paste it here.',
    hint: 'Tip: select text on any page, right-click, and choose "TrustLens" to check it.',
    errorPrefix: 'Error: ',
  },
};

let lang = 'bn';

// ---------------------------------------------------------------------------
// Elements
// ---------------------------------------------------------------------------
const input = document.getElementById('input');
const btn = document.getElementById('analyzeBtn');
const langToggle = document.getElementById('langToggle');
const loadingEl = document.getElementById('loading');
const loadingText = document.getElementById('loadingText');
const resultDiv = document.getElementById('result');
const scoreEl = document.getElementById('score');
const verdictEl = document.getElementById('verdict');
const pillarsEl = document.getElementById('pillars');
const scrapeFailedEl = document.getElementById('scrapeFailed');
const scrapeFailedTitle = document.getElementById('scrapeFailedTitle');
const scrapeFailedText = document.getElementById('scrapeFailedText');
const errorEl = document.getElementById('error');
const hintEl = document.getElementById('hint');

// ---------------------------------------------------------------------------
// Apply translations to static chrome
// ---------------------------------------------------------------------------
function applyLang() {
  const t = STRINGS[lang];
  input.placeholder = t.placeholder;
  btn.textContent = t.analyze;
  langToggle.textContent = t.langBtn;
  hintEl.textContent = t.hint;
  document.documentElement.lang = lang;
}

langToggle.addEventListener('click', () => {
  lang = lang === 'bn' ? 'en' : 'bn';
  chrome.storage?.local.set({ tl_lang: lang });
  applyLang();
});

// ---------------------------------------------------------------------------
// View helpers
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
  const color = score >= 80 ? '#22c55e' : score >= 40 ? '#eab308' : '#ef4444';

  scoreEl.textContent = `${score}/100`;
  scoreEl.style.color = color;
  verdictEl.textContent = (lang === 'bn' ? data.verdict_bn : data.verdict) || data.verdict_bn || data.verdict || '';

  pillarsEl.innerHTML = '';
  (data.pillars || []).forEach((p) => {
    if (!p || !p.active) return;
    const div = document.createElement('div');
    div.className = 'pillar';
    const label = document.createElement('span');
    label.textContent = (lang === 'bn' ? p.name_bn : p.name) || p.name_bn || p.name || '';
    const value = document.createElement('span');
    value.className = 'pillar-score';
    value.textContent = String(Math.round(p.score || 0));
    div.appendChild(label);
    div.appendChild(value);
    pillarsEl.appendChild(div);
  });

  resultDiv.classList.remove('hidden');
}

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
