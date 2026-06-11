// TrustLens Chrome Extension — Background Service Worker (MV3)
// Responsibilities:
//   1. Register right-click context menus (selected text / link / page).
//   2. Centralize all API calls to the TrustLens backend.
//   3. Relay results to the content script (in-page badge overlay) and popup.

const API_URL = 'http://107.161.168.216:8000';

// ---------------------------------------------------------------------------
// Context menus
// ---------------------------------------------------------------------------
const MENU_SELECTION = 'trustlens-analyze-selection';
const MENU_LINK = 'trustlens-analyze-link';
const MENU_PAGE = 'trustlens-analyze-page';

function setupContextMenus() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: MENU_SELECTION,
      title: 'TrustLens: এই লেখা যাচাই করুন',
      contexts: ['selection'],
    });
    chrome.contextMenus.create({
      id: MENU_LINK,
      title: 'TrustLens: এই লিংক যাচাই করুন',
      contexts: ['link'],
    });
    chrome.contextMenus.create({
      id: MENU_PAGE,
      title: 'TrustLens: এই পেজ যাচাই করুন',
      contexts: ['page'],
    });
  });
}

chrome.runtime.onInstalled.addListener(setupContextMenus);
chrome.runtime.onStartup.addListener(setupContextMenus);

// ---------------------------------------------------------------------------
// API call — single source of truth for hitting the backend.
// Returns { ok, data } or { ok:false, error }.
// ---------------------------------------------------------------------------
async function analyzeContent(content) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 45000);
    const res = await fetch(`${API_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (!res.ok) {
      return { ok: false, error: `HTTP ${res.status}` };
    }
    const data = await res.json();
    return { ok: true, data };
  } catch (err) {
    const msg = err.name === 'AbortError' ? 'Request timed out' : (err.message || 'Network error');
    return { ok: false, error: msg };
  }
}

// ---------------------------------------------------------------------------
// Toolbar action badge — quick visual cue of the last score.
// ---------------------------------------------------------------------------
function setActionBadge(tabId, data) {
  if (!data || typeof data.trust_score !== 'number' || data.scrape_failed) {
    chrome.action.setBadgeText({ tabId, text: data && data.scrape_failed ? '?' : '' });
    chrome.action.setBadgeBackgroundColor({ tabId, color: '#52525b' });
    return;
  }
  const score = Math.round(data.trust_score);
  const color = score >= 80 ? '#22c55e' : score >= 40 ? '#eab308' : '#ef4444';
  chrome.action.setBadgeText({ tabId, text: String(score) });
  chrome.action.setBadgeBackgroundColor({ tabId, color });
}

// ---------------------------------------------------------------------------
// Context menu click → analyze → push result to the content script overlay.
// ---------------------------------------------------------------------------
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  let content = '';
  if (info.menuItemId === MENU_SELECTION && info.selectionText) {
    content = info.selectionText.trim();
  } else if (info.menuItemId === MENU_LINK && info.linkUrl) {
    content = info.linkUrl;
  } else if (info.menuItemId === MENU_PAGE) {
    content = info.pageUrl || (tab && tab.url) || '';
  }
  if (!content || !tab || tab.id == null) return;

  // Tell the content script to show a loading overlay.
  chrome.tabs.sendMessage(tab.id, { type: 'TRUSTLENS_LOADING' }).catch(() => {});

  const result = await analyzeContent(content);

  if (result.ok) {
    setActionBadge(tab.id, result.data);
    chrome.tabs
      .sendMessage(tab.id, { type: 'TRUSTLENS_RESULT', data: result.data })
      .catch(() => {});
  } else {
    chrome.tabs
      .sendMessage(tab.id, { type: 'TRUSTLENS_ERROR', error: result.error })
      .catch(() => {});
  }
});

// ---------------------------------------------------------------------------
// Message router — popup (and content script) ask us to analyze.
// ---------------------------------------------------------------------------
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === 'TRUSTLENS_ANALYZE' && typeof msg.content === 'string') {
    analyzeContent(msg.content).then((result) => {
      if (result.ok && sender.tab && sender.tab.id != null) {
        setActionBadge(sender.tab.id, result.data);
      }
      sendResponse(result);
    });
    return true; // keep the channel open for the async response
  }
  return false;
});
