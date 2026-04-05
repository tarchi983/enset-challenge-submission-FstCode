/* ═══════════════════════════════════════════════════════
   Darija AI — app.js
   Features: multi-session sidebar, stop generation,
             history navigation, new tab / new window,
             theme persistence, auto-resize textarea
═══════════════════════════════════════════════════════ */

// IMMEDIATE DEBUG CHECK
console.log('✓ app.js loaded at', new Date().toLocaleTimeString());
console.log('✓ document.readyState:', document.readyState);

// ── Global debug helpers ─────────────────────────────
window.onerror = (message, source, lineno, colno, error) => {
  console.error('Global JS error:', { message, source, lineno, colno, error });
};

window.onunhandledrejection = (event) => {
  console.error('Unhandled promise rejection:', event.reason);
};

// ── DOM refs ──────────────────────────────────────────
const chatArea      = document.getElementById('chat-area');
const userInput     = document.getElementById('user-input');
const sendBtn       = document.getElementById('send-btn');
const stopBtn       = document.getElementById('stop-btn');
const statusDot     = document.getElementById('status-dot');
const statusText    = document.getElementById('status-text');
const sessionLabel  = document.getElementById('session-label');
const sessionsList  = document.getElementById('sessions-list');
const historyNav    = document.getElementById('history-nav');
const backBtn       = document.getElementById('back-btn');
const fwdBtn        = document.getElementById('fwd-btn');
const historyCounter= document.getElementById('history-counter');
const themeBtn      = document.getElementById('theme-btn');
const welcomeEl     = document.getElementById('welcome');
const sidebar       = document.getElementById('sidebar');

console.log('DOM elements loaded:', {
  chatArea, userInput, sendBtn, stopBtn, statusDot, statusText,
  sessionLabel, sessionsList, historyNav, backBtn, fwdBtn,
  historyCounter, themeBtn, welcomeEl, sidebar
});

// ── State ─────────────────────────────────────────────
let sessions       = [];           // array of session objects
let currentSession = null;         // active session id
let historyIndex   = -1;           // index into rendered messages (-1 = show all)
let abortController= null;         // for stopping fetch
let isThinking     = false;

const SESSION_KEY  = 'darija_sessions';
const THEME_KEY    = 'darija_theme';
const SIDEBAR_KEY  = 'darija_sidebar';

// ── Session helpers ────────────────────────────────────
function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

function createSession(label) {
  const id = genId();
  const s = {
    id,
    name: label || 'New conversation',
    messages: [],   // { role, text, ts }
    createdAt: Date.now(),
  };
  sessions.unshift(s);
  saveData();
  return s;
}

function saveData() {
  try { localStorage.setItem(SESSION_KEY, JSON.stringify(sessions)); } catch {}
}

function loadData() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (raw) sessions = JSON.parse(raw);
  } catch { sessions = []; }
}

function getSession(id) {
  return sessions.find(s => s.id === id) || null;
}

// ── Render sidebar list ────────────────────────────────
function renderSidebar() {
  sessionsList.innerHTML = '';

  if (!sessions.length) {
    sessionsList.innerHTML = '<div style="padding:16px 10px;font-size:0.78rem;color:var(--text-muted);text-align:center">No sessions yet</div>';
    return;
  }

  // Group by today / yesterday / older
  const now   = Date.now();
  const DAY   = 86400000;
  const groups = { Today: [], Yesterday: [], Older: [] };

  sessions.forEach(s => {
    const age = now - s.createdAt;
    if (age < DAY) groups.Today.push(s);
    else if (age < 2 * DAY) groups.Yesterday.push(s);
    else groups.Older.push(s);
  });

  Object.entries(groups).forEach(([label, list]) => {
    if (!list.length) return;
    const groupLabel = document.createElement('div');
    groupLabel.className = 'session-group-label';
    groupLabel.textContent = label;
    sessionsList.appendChild(groupLabel);

    list.forEach(s => {
      const item = document.createElement('div');
      item.className = 'session-item' + (s.id === currentSession ? ' active' : '');
      item.dataset.id = s.id;

      item.innerHTML = `
        <span class="session-icon">💬</span>
        <div class="session-meta">
          <div class="session-name" title="${escHtml(s.name)}">${escHtml(s.name)}</div>
          <div class="session-time">${relTime(s.createdAt)}</div>
        </div>
        <button class="session-del" title="Delete" onclick="deleteSession(event,'${s.id}')">✕</button>
      `;

      item.addEventListener('click', (e) => {
        if (e.target.classList.contains('session-del')) return;
        switchSession(s.id);
      });

      sessionsList.appendChild(item);
    });
  });
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function relTime(ts) {
  const diff = Date.now() - ts;
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
  if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago';
  return new Date(ts).toLocaleDateString();
}

// ── Switch / create sessions ───────────────────────────
function switchSession(id) {
  currentSession = id;
  historyIndex = -1;
  renderChat();
  renderSidebar();
  const s = getSession(id);
  if (s) sessionLabel.textContent = s.name;
}

function newChat() {
  const s = createSession();
  currentSession = s.id;
  historyIndex = -1;
  renderSidebar();
  renderChat();
  sessionLabel.textContent = s.name;
  userInput.focus();
}

function deleteSession(e, id) {
  e.stopPropagation();
  sessions = sessions.filter(s => s.id !== id);
  saveData();
  if (currentSession === id) {
    if (sessions.length) {
      switchSession(sessions[0].id);
    } else {
      currentSession = null;
      renderChat();
    }
  }
  renderSidebar();
}

// ── Render chat messages ───────────────────────────────
function renderChat() {
  // Clear all messages (but keep #welcome)
  Array.from(chatArea.querySelectorAll('.msg')).forEach(el => el.remove());
  removeThinking();

  const s = getSession(currentSession);
  const msgs = s ? s.messages : [];

  // Show/hide welcome
  if (!msgs.length) {
    welcomeEl.style.display = '';
    historyNav.style.display = 'none';
    historyCounter.textContent = '';
    return;
  }

  welcomeEl.style.display = 'none';

  const limit = historyIndex === -1 ? msgs.length : historyIndex + 1;
  for (let i = 0; i < limit; i++) {
    appendBubble(msgs[i].role, msgs[i].text, false);
  }

  updateHistoryNav();
  chatArea.scrollTop = chatArea.scrollHeight;
}

function updateHistoryNav() {
  const s = getSession(currentSession);
  const total = s ? s.messages.length : 0;
  const shown = historyIndex === -1 ? total : historyIndex + 1;

  if (total > 0) {
    historyNav.style.display = 'flex';
    historyCounter.textContent = `${shown} / ${total} msgs`;
    backBtn.disabled = shown <= 1;
    fwdBtn.disabled = shown >= total;
  } else {
    historyNav.style.display = 'none';
  }
}

function navBack() {
  const s = getSession(currentSession);
  if (!s) return;
  const cur = historyIndex === -1 ? s.messages.length - 1 : historyIndex;
  if (cur > 0) {
    historyIndex = cur - 1;
    renderChat();
  }
}

function navForward() {
  const s = getSession(currentSession);
  if (!s) return;
  const cur = historyIndex === -1 ? s.messages.length - 1 : historyIndex;
  if (cur < s.messages.length - 1) {
    historyIndex = cur + 1;
    renderChat();
  } else {
    historyIndex = -1;
    renderChat();
  }
}

// ── Bubble builder ─────────────────────────────────────
function appendBubble(role, text, scroll = true) {
  const wrapper = document.createElement('div');
  wrapper.className = `msg ${role}`;

  const label = document.createElement('div');
  label.className = 'msg-label';
  label.textContent = role === 'user' ? 'You' : '🇲🇦 Darija Expert';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  wrapper.appendChild(label);
  wrapper.appendChild(bubble);
  chatArea.appendChild(wrapper);

  if (scroll) chatArea.scrollTop = chatArea.scrollHeight;
}

// ── Thinking indicator ─────────────────────────────────
function showThinking() {
  removeThinking();
  const wrapper = document.createElement('div');
  wrapper.id = 'thinking-msg';
  wrapper.className = 'msg bot';

  const label = document.createElement('div');
  label.className = 'msg-label';
  label.textContent = '🇲🇦 Darija Expert';

  const bubble = document.createElement('div');
  bubble.className = 'thinking-bubble';
  bubble.innerHTML = `
    <div class="dots">
      <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    </div>
    <span class="thinking-text">Thinking…</span>
  `;

  wrapper.appendChild(label);
  wrapper.appendChild(bubble);
  chatArea.appendChild(wrapper);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function removeThinking() {
  const el = document.getElementById('thinking-msg');
  if (el) el.remove();
}

// ── Status pill ────────────────────────────────────────
function setStatus(state) {
  // state: 'ready' | 'thinking'
  isThinking = state === 'thinking';
  if (isThinking) {
    statusDot.className = 'status-dot thinking';
    statusText.textContent = 'Thinking…';
    stopBtn.classList.add('visible');
    sendBtn.disabled = true;
  } else {
    statusDot.className = 'status-dot';
    statusText.textContent = 'Ready';
    stopBtn.classList.remove('visible');
    sendBtn.disabled = false;
  }
}

// ── Send message ───────────────────────────────────────
async function sendMessage() {
  console.log('sendMessage called');
  const text = userInput.value.trim();
  console.log('text:', text);
  if (!text || isThinking) return;

  // Auto-create session if needed
  if (!currentSession) {
    const s = createSession();
    currentSession = s.id;
  }

  const s = getSession(currentSession);
  historyIndex = -1;

  // Save user message
  s.messages.push({ role: 'user', text, ts: Date.now() });
  if (s.messages.length === 1) {
    s.name = text.slice(0, 40) + (text.length > 40 ? '…' : '');
    sessionLabel.textContent = s.name;
  }
  saveData();

  userInput.value = '';
  userInput.style.height = 'auto';
  welcomeEl.style.display = 'none';
  appendBubble('user', text);
  showThinking();
  setStatus('thinking');
  renderSidebar();

  abortController = new AbortController();

  try {
    console.log('Making fetch request to /chat');
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
      signal: abortController.signal,
    });
    console.log('Fetch response status:', res.status);

    const data = await res.json();
    console.log('Response data:', data);
    removeThinking();

    if (data.error) {
      const err = '⚠️ ' + data.error;
      s.messages.push({ role: 'bot', text: err, ts: Date.now() });
      appendBubble('bot', err);
    } else {
      s.messages.push({ role: 'bot', text: data.response, ts: Date.now() });
      appendBubble('bot', data.response);
    }
  } catch (err) {
    console.error('Error in sendMessage:', err);
    removeThinking();
    if (err.name === 'AbortError') {
      const stopped = '⏹ Generation stopped.';
      s.messages.push({ role: 'bot', text: stopped, ts: Date.now() });
      appendBubble('bot', stopped);
    } else {
      const errMsg = '⚠️ Cannot reach server. Make sure app.py is running.';
      s.messages.push({ role: 'bot', text: errMsg, ts: Date.now() });
      appendBubble('bot', errMsg);
    }
  }

  saveData();
  setStatus('ready');
  updateHistoryNav();
  userInput.focus();
}

// ── Stop generation ────────────────────────────────────
function stopGeneration() {
  if (abortController) {
    abortController.abort();
    abortController = null;
  }
  removeThinking();
  setStatus('ready');
}

// ── Clear chat ─────────────────────────────────────────
function clearChat() {
  document.getElementById('clear-modal').classList.add('open');
}

function confirmClear() {
  const s = getSession(currentSession);
  if (s) { s.messages = []; saveData(); }
  historyIndex = -1;
  closeModal('clear-modal');
  renderChat();
  renderSidebar();
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

// ── Theme ──────────────────────────────────────────────
function toggleTheme() {
  const isLight = document.body.classList.toggle('light');
  themeBtn.textContent = isLight ? '☀️' : '🌙';
  try { localStorage.setItem(THEME_KEY, isLight ? 'light' : 'dark'); } catch {}
}

function initTheme() {
  try {
    const t = localStorage.getItem(THEME_KEY);
    if (t === 'light') {
      document.body.classList.add('light');
      themeBtn.textContent = '☀️';
    }
  } catch {}
}

// ── Sidebar toggle ─────────────────────────────────────
function toggleSidebar() {
  sidebar.classList.toggle('collapsed');
  // On mobile add/remove 'open' class
  if (window.innerWidth <= 680) {
    sidebar.classList.toggle('open');
  }
  try { localStorage.setItem(SIDEBAR_KEY, sidebar.classList.contains('collapsed') ? '0' : '1'); } catch {}
}

function initSidebar() {
  try {
    const s = localStorage.getItem(SIDEBAR_KEY);
    if (s === '0') sidebar.classList.add('collapsed');
  } catch {}
}

// ── New tab / window ───────────────────────────────────
function openNewTab() {
  window.open(location.href, '_blank', 'noopener');
}

function openNewWindow() {
  window.open(location.href, '_blank', 'noopener,width=960,height=750,resizable=yes,scrollbars=yes');
}

// ── Suggestion chips ───────────────────────────────────
function useSuggestion(btn) {
  userInput.value = btn.textContent.replace(/^[^ ]+ /, ''); // strip emoji
  sendMessage();
}

// ── Auto-resize textarea ───────────────────────────────
userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
});

userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Close modal on backdrop click
document.querySelectorAll('.modal-backdrop').forEach(bd => {
  bd.addEventListener('click', (e) => {
    if (e.target === bd) bd.classList.remove('open');
  });
});

// ── Init ───────────────────────────────────────────────
function init() {
  console.log('Initializing app...');
  
  initTheme();
  initSidebar();
  loadData();

  if (sessions.length) {
    currentSession = sessions[0].id;
  } else {
    const s = createSession();
    currentSession = s.id;
  }

  renderSidebar();
  renderChat();
  setStatus('ready');
  userInput.focus();
  console.log('App initialized');

  if (!chatArea || !userInput || !sendBtn || !stopBtn || !statusDot || !statusText || !sessionLabel || !sessionsList || !historyNav || !backBtn || !fwdBtn || !historyCounter || !themeBtn || !welcomeEl || !sidebar) {
    console.error('One or more required DOM element references are missing. Make sure index.html IDs match app.js.');
    console.error('Missing:', {
      chatArea: !!chatArea,
      userInput: !!userInput,
      sendBtn: !!sendBtn,
      stopBtn: !!stopBtn,
      statusDot: !!statusDot,
      statusText: !!statusText,
      sessionLabel: !!sessionLabel,
      sessionsList: !!sessionsList,
      historyNav: !!historyNav,
      backBtn: !!backBtn,
      fwdBtn: !!fwdBtn,
      historyCounter: !!historyCounter,
      themeBtn: !!themeBtn,
      welcomeEl: !!welcomeEl,
      sidebar: !!sidebar
    });
  }

  // Add event listeners (with null checks)
  if (sendBtn) {
    sendBtn.addEventListener('click', () => {
      console.log('sendBtn clicked');
      sendMessage();
    });
  }
  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      console.log('stopBtn clicked');
      stopGeneration();
    });
  }
  if (backBtn) {
    backBtn.addEventListener('click', navBack);
  }
  if (fwdBtn) {
    fwdBtn.addEventListener('click', navForward);
  }
  if (themeBtn) {
    themeBtn.addEventListener('click', toggleTheme);
  }

  const sidebarToggle = document.getElementById('sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
      console.log('sidebar-toggle clicked');
      toggleSidebar();
    });
  }

  const newChatBtn = document.getElementById('new-chat-btn');
  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => {
      console.log('new-chat-btn clicked');
      newChat();
    });
  }

  const clearBtn = document.getElementById('clear-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      console.log('clear-btn clicked');
      clearChat();
    });
  }

  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      console.log('chip clicked:', chip.textContent);
      useSuggestion(chip);
    });
  });

  const newTabBtn = document.getElementById('new-tab-btn');
  if (newTabBtn) {
    newTabBtn.addEventListener('click', () => {
      console.log('new-tab-btn clicked');
      openNewTab();
    });
  }

  const newWindowBtn = document.getElementById('new-window-btn');
  if (newWindowBtn) {
    newWindowBtn.addEventListener('click', () => {
      console.log('new-window-btn clicked');
      openNewWindow();
    });
  }

  // Global delegated click handler as a fail-safe
  // This will catch ALL button clicks regardless of how they're triggered
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn || !btn.id) return;
    
    const id = btn.id;
    console.log('DELEGATE HANDLER: button clicked:', id);

    // Call the actual functions directly
    switch (id) {
      case 'send-btn': 
        console.log('→ calling sendMessage()');
        sendMessage(); 
        break;
      case 'stop-btn': 
        console.log('→ calling stopGeneration()');
        stopGeneration(); 
        break;
      case 'back-btn': 
        console.log('→ calling navBack()');
        navBack(); 
        break;
      case 'fwd-btn':
        console.log('→ calling navForward()');
        navForward(); 
        break;
      case 'theme-btn': 
        console.log('→ calling toggleTheme()');
        toggleTheme(); 
        break;
      case 'sidebar-toggle': 
        console.log('→ calling toggleSidebar()');
        toggleSidebar(); 
        break;
      case 'new-chat-btn': 
        console.log('→ calling newChat()');
        newChat(); 
        break;
      case 'clear-btn': 
        console.log('→ calling clearChat()');
        clearChat(); 
        break;
      case 'new-tab-btn': 
        console.log('→ calling openNewTab()');
        openNewTab(); 
        break;
      case 'new-window-btn': 
        console.log('→ calling openNewWindow()');
        openNewWindow(); 
        break;
      default: 
        console.log('→ unhandled button:', id);
        break;
    }
  }, true); // Use capture phase to catch clicks before anything else

  console.log('Event listeners added');
}

// Assign all function implementations to window object so onclick handlers can call them
function setupGlobalFunctions() {
  console.log('Setting up global functions...');
  
  // Get references to all the real functions
  const realSendMessage = sendMessage;
  const realStopGeneration = stopGeneration;
  const realNewChat = newChat;
  const realToggleTheme = toggleTheme;
  const realToggleSidebar = toggleSidebar;
  const realClearChat = clearChat;
  const realCloseModal = closeModal;
  const realConfirmClear = confirmClear;
  const realUseSuggestion = useSuggestion;
  const realOpenNewTab = openNewTab;
  const realOpenNewWindow = openNewWindow;
  const realNavBack = navBack;
  const realNavForward = navForward;
  
  // Now assign to window
  window.sendMessage = realSendMessage;
  window.stopGeneration = realStopGeneration;
  window.newChat = realNewChat;
  window.toggleTheme = realToggleTheme;
  window.toggleSidebar = realToggleSidebar;
  window.clearChat = realClearChat;
  window.closeModal = realCloseModal;
  window.confirmClear = realConfirmClear;
  window.useSuggestion = realUseSuggestion;
  window.openNewTab = realOpenNewTab;
  window.openNewWindow = realOpenNewWindow;
  window.navBack = realNavBack;
  window.navForward = realNavForward;
  
  console.log('✓ All global functions ready!');
}

init();
setupGlobalFunctions();

// Triple-safety: also expose functions explicitly to window
console.log('Exposing functions to window object...');
window.sendMessage = sendMessage;
window.stopGeneration = stopGeneration;
window.newChat = newChat;
window.toggleTheme = toggleTheme;
window.toggleSidebar = toggleSidebar;
window.clearChat = clearChat;
window.closeModal = closeModal;
window.confirmClear = confirmClear;
window.useSuggestion = useSuggestion;
window.openNewTab = openNewTab;
window.openNewWindow = openNewWindow;
window.navBack = navBack;
window.navForward = navForward;
console.log('✓ All functions are now on window object');