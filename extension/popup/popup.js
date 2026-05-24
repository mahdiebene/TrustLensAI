// TrustLens Chrome Extension - Popup
const API_URL = 'http://localhost:8000';

const input = document.getElementById('input');
const btn = document.getElementById('analyzeBtn');
const resultDiv = document.getElementById('result');
const scoreEl = document.getElementById('score');
const verdictEl = document.getElementById('verdict');
const pillarsEl = document.getElementById('pillars');
const errorEl = document.getElementById('error');

btn.addEventListener('click', async () => {
  const content = input.value.trim();
  if (!content) return;

  btn.disabled = true;
  btn.textContent = 'বিশ্লেষণ চলছে...';
  resultDiv.classList.add('hidden');
  errorEl.classList.add('hidden');

  try {
    const response = await fetch(`${API_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    displayResult(data);
  } catch (err) {
    errorEl.textContent = `Error: ${err.message}`;
    errorEl.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.textContent = 'বিশ্লেষণ করুন';
  }
});

function displayResult(data) {
  const color = data.trust_score >= 80 ? '#22c55e' :
                data.trust_score >= 40 ? '#eab308' : '#ef4444';

  scoreEl.textContent = `${Math.round(data.trust_score)}/100`;
  scoreEl.style.color = color;
  verdictEl.textContent = data.verdict_bn || data.verdict;

  pillarsEl.innerHTML = '';
  (data.pillars || []).forEach(p => {
    if (!p.active) return;
    const div = document.createElement('div');
    div.className = 'pillar';
    div.innerHTML = `<span>${p.name_bn || p.name}</span><span class="pillar-score">${Math.round(p.score)}</span>`;
    pillarsEl.appendChild(div);
  });

  resultDiv.classList.remove('hidden');
}

// Auto-fill from active tab URL
chrome.tabs?.query({ active: true, currentWindow: true }, (tabs) => {
  if (tabs[0]?.url && !tabs[0].url.startsWith('chrome://')) {
    input.value = tabs[0].url;
  }
});
