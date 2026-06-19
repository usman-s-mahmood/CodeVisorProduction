/**
 * CodeVisor-AI Core Logic v2.5
 * Features: Typewriter, 3-Tier Search, Global Voice Sync, Auto-Resize Textarea
 */

// 1. GLOBAL STATE & INITIALIZATION
let currentSessionId = null;
let searchController = null; 
let searchTimeout = null;    
let originalHistoryHTML = "";
let currentUtterance = null; 
let userUsedVoice = false; 
const synth = window.speechSynthesis;

function highlightActiveSession(sessionId) {
    // 1. Remove 'active' from all items everywhere
    document.querySelectorAll('.history-item').forEach(item => {
        item.classList.remove('active');
    });

    // 2. Find the item that matches this ID
    document.querySelectorAll('.history-item').forEach(item => {
        // Get the custom data-id (for search items)
        const dataId = item.getAttribute('data-id');
        // Get the onclick text (for normal sidebar items)
        const onClickAttr = item.getAttribute('onclick');

        // Check if either one matches the sessionId
        // We use == instead of === because sessionId might be a string or a number
        if (dataId == sessionId || (onClickAttr && onClickAttr.includes(sessionId))) {
            item.classList.add('active');
        }
    });
}


// function highlightActiveSession(sessionId) {
//     // 1. Remove 'active' from all items in both sidebars
//     document.querySelectorAll('.history-item').forEach(item => {
//         item.classList.remove('active');
//     });

//     // 2. Find the item that matches this ID and highlight it
//     // We check both the main list and search results
//     document.querySelectorAll('.history-item').forEach(item => {
//         // We look for the ID inside the onclick attribute or a data-id if you have one
//         if (item.getAttribute('onclick')?.includes(sessionId)) {
//             item.classList.add('active');
//         }
//     });
// }

const md = window.markdownit({
    html: true,
    linkify: true,
    highlight: function (str, lang) {
        if (lang && hljs.getLanguage(lang)) {
            try {
                return '<pre><button class="copy-code-btn" onclick="copyCode(this)">Copy</button><code class="hljs">' +
                       hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
                       '</code></pre>';
            } catch (__) {}
        }
        return '<pre><button class="copy-code-btn" onclick="copyCode(this)">Copy</button><code class="hljs">' + md.utils.escapeHtml(str) + '</code></pre>';
    }
});

// 2. VOICE ENGINE (Cross-Platform)
// GLOBAL VOICE STATE - Essential to prevent the "Stopping" bug
window.currentUtterance = null;

function getBestVoice() {
    const voices = synth.getVoices();
    return voices.find(v => (v.name.includes('Google') || v.name.includes('Natural')) && v.name.includes('Male')) || 
           voices.find(v => v.name.toLowerCase().includes('male')) || 
           voices.find(v => v.lang.startsWith('en')) || 
           voices[0];
}

// 🔥 REPLACE THIS FUNCTION WITH THE NEW VERSION


function speakText(text, btnElement = null) {
    // Find the action container (the parent div of the buttons)
    const actionContainer = btnElement ? btnElement.closest('.msg-actions') : null;

    if (synth.speaking) {
        synth.cancel();
        document.querySelectorAll('.msg-actions').forEach(el => el.classList.remove('speaking'));
    }

    const cleanText = text
        .replace(/```[\s\S]*?```/g, ' [Code block omitted] ')
        .replace(/[*#_~`]/g, '')
        .trim();

    window.currentUtterance = new SpeechSynthesisUtterance(cleanText);
    window.currentUtterance.voice = getBestVoice();
    
    // Toggle the UI state
    window.currentUtterance.onstart = () => {
        if (actionContainer) actionContainer.classList.add('speaking');
    };

    window.currentUtterance.onend = () => {
        if (actionContainer) actionContainer.classList.remove('speaking');
    };

    window.currentUtterance.onerror = () => {
        if (actionContainer) actionContainer.classList.remove('speaking');
    };

    // The Heartbeat Hack (Keep this!)
    const r = setInterval(() => {
        if (!synth.speaking) {
            clearInterval(r);
        } else {
            synth.pause();
            synth.resume();
        }
    }, 10000);

    synth.speak(window.currentUtterance);
}

function stopSpeaking() {
    synth.cancel();
    // Globally reset all button states
    document.querySelectorAll('.msg-actions').forEach(el => el.classList.remove('speaking'));
}
// =============================
// 🔊 SPEAK CONTROL (CHUNKED)
// =============================
let isSpeaking = false;

// function stopSpeaking() {
//     synth.cancel();
//     document.querySelectorAll('.voice-play-btn').forEach(btn => btn.classList.remove('speaking'));
// }

function speakChunk(text, btn = null) {
    return new Promise(resolve => {
        if (!text) return resolve();

        const utter = new SpeechSynthesisUtterance(text);
        utter.voice = getBestVoice();
        utter.rate = 1.0;
        utter.pitch = 0.9;

        utter.onstart = () => {
            isSpeaking = true;
            if (btn) btn.style.display = 'inline-flex';
        };

        utter.onend = () => resolve();
        utter.onerror = () => resolve();

        synth.speak(utter);
    });
}


// 3. CORE CHAT FUNCTIONS (loadSession must be early)
async function loadSession(sessionId) {

    highlightActiveSession(sessionId);
    const viewport = document.getElementById('viewport');
    viewport.innerHTML = '<div class="p-5 text-center text-white">Synchronizing with CodeVisor AI...</div>';
    currentSessionId = sessionId;

    try {
        const response = await fetch(`/ai/session/${sessionId}/`);
        const data = await response.json();
        viewport.innerHTML = ''; 
        data.history.forEach(msg => appendMessage(msg.content, msg.role, null, false));
    } catch (err) {
        viewport.innerHTML = '<div class="p-5 text-center text-danger">Failed to load history.</div>';
    }
}

function typewriterEffect(element, rawText, callback) {
    let index = 0;
    const speed = 2.5; 
    function type() {
        if (index < rawText.length) {
            let partialText = rawText.slice(0, index + 1);
            element.innerHTML = md.render(partialText);
            document.getElementById('viewport').scrollTop = document.getElementById('viewport').scrollHeight;
            if (partialText.includes('```')) {
                element.querySelectorAll('pre code').forEach((el) => { hljs.highlightElement(el); });
            }
            index++;
            setTimeout(type, speed);
        } else {
            if (callback) callback();
        }
    }
    type();
}
// 🔥 Update: added 'sources' parameter
function appendMessage(text, role, onComplete, isNew = false, sources = []) {
    const viewport = document.getElementById('viewport');
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${role}`;
    
    const avatar = role === 'bot' ? 
        '<div class="avatar bot-avatar"><i class="bi bi-robot"></i></div>' : 
        '<div class="avatar user-avatar"><i class="bi bi-person"></i></div>';
    
    // 🔥 Build the Sources HTML if they exist
    let sourcesHTML = '';
    if (role === 'bot' && sources && sources.length > 0) {
        sourcesHTML = `<div class="sources-container mt-2">
            <small class="text-muted" style="font-size: 0.65rem; display: block; margin-bottom: 4px;">REFERENCED FILES:</small>
            <div class="d-flex flex-wrap gap-1">
                ${sources.map(src => `<span class="badge bg-secondary" style="font-size: 0.7rem; opacity: 0.8;">${src}</span>`).join('')}
            </div>
        </div>`;
    }

    let actionButtons = '';
    if (role === 'bot') {
        const escapedText = text.replace(/`/g, '\\`').replace(/\${/g, '\\${').replace(/"/g, '&quot;');
        actionButtons = `
            <div class="msg-actions d-flex gap-2 mt-2">
                <div class="full-msg-copy pointer" onclick="copyFullMsg(this)">
                    <i class="bi bi-clipboard"></i> Copy
                </div>
                <div class="voice-play-btn pointer" onclick="speakText(\`${escapedText}\`, this)">
                    <i class="bi bi-volume-up-fill"></i> Read
                </div>
                <div class="voice-stop-btn pointer" onclick="stopSpeaking()">
                    <i class="bi bi-stop-circle-fill"></i> Stop
                </div>
            </div>`;
    }

    // 🔥 Added ${sourcesHTML} inside the bubble
    msgDiv.innerHTML = `${avatar}<div class="bubble"><div class="content-text"></div>${sourcesHTML}${actionButtons}</div>`;
    viewport.appendChild(msgDiv);
    const contentDiv = msgDiv.querySelector('.content-text');

    if (role === 'bot' && isNew) {
        typewriterEffect(contentDiv, text, () => {
            if (onComplete) onComplete();
            if (userUsedVoice) {
                speakText(text, msgDiv.querySelector('.voice-play-btn'));
                userUsedVoice = false; 
            }
        });
    } else {
        contentDiv.innerHTML = md.render(text);
        if (onComplete) onComplete();
        viewport.scrollTop = viewport.scrollHeight;
        contentDiv.querySelectorAll('pre code').forEach((el) => { hljs.highlightElement(el); });
    }
}

async function handleSend() {
    const input = document.getElementById('userIn');
    const text = input.value.trim();
    if (!text) return;

    stopSpeaking();
    toggleInputState(true);
    // User message never has sources, so we pass an empty array or nothing
    appendMessage(text, 'user', null, false);
    input.value = '';
    input.style.height = 'auto';
    showThinking();

    try {
        const response = await fetch('/ai/api/chat/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value 
            },
            body: JSON.stringify({ message: text, session_id: currentSessionId })
        });
        
        const data = await response.json();
        removeThinking();

        if (data.session_id) currentSessionId = data.session_id;

        // 🔥 THE FIX: We pass data.sources as the 5th argument
        appendMessage(
            data.response, 
            'bot', 
            () => toggleInputState(false), 
            true, 
            data.sources || [] 
        );

    } catch (e) {
        removeThinking();
        toggleInputState(false);
        appendMessage("Error: CodeVisor Core timed out.", 'bot', null, false);
    }
}

// 4. UI HELPERS
function toggleInputState(disabled) {
    const input = document.getElementById('userIn');
    input.disabled = disabled;
    input.style.opacity = disabled ? "0.5" : "1";
    input.style.cursor = disabled ? "not-allowed" : "text";
    if (!disabled) input.focus();
}

function showThinking() {
    const viewport = document.getElementById('viewport');
    const loaderDiv = document.createElement('div');
    loaderDiv.id = 'nexus-loader';
    loaderDiv.className = 'msg bot';
    loaderDiv.innerHTML = `<div class="avatar bot-avatar"><i class="bi bi-robot"></i></div><div class="bubble" style="background: rgba(168, 85, 247, 0.05); border: 1px dashed var(--accent);"><div class="content-text"><span class="spinner-grow spinner-grow-sm" role="status" style="color: var(--accent);"></span><span class="ms-2">CodeVisor-AI is thinking...</span></div></div>`;
    viewport.appendChild(loaderDiv);
    viewport.scrollTop = viewport.scrollHeight;
}

function removeThinking() { document.getElementById('nexus-loader')?.remove(); }

function copyCode(btn) {
    const code = btn.nextElementSibling.innerText;
    navigator.clipboard.writeText(code);
    btn.innerText = "Copied!";
    setTimeout(() => btn.innerText = "Copy", 2000);
}

function copyFullMsg(btn) {
    // Navigate up to the bubble, then down to the content
    const bubble = btn.closest('.bubble');
    const contentText = bubble.querySelector('.content-text');
    
    if (contentText) {
        const text = contentText.innerText;
        navigator.clipboard.writeText(text).then(() => {
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-check-all"></i> Copied!';
            setTimeout(() => btn.innerHTML = originalHTML, 2000);
        });
    }
}

// 5. INPUT & KEYBOARD CONTROLLER
const userIn = document.getElementById('userIn');

userIn.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    this.style.overflowY = this.scrollHeight > 200 ? 'auto' : 'hidden';
});



userIn.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        if (e.shiftKey) {
            // 1️⃣ Insert newline at cursor
            const start = this.selectionStart;
            const end = this.selectionEnd;
            this.value = this.value.slice(0, start) + '\n' + this.value.slice(end);
            this.selectionStart = this.selectionEnd = start + 1;

            // 2️⃣ Auto-resize the textarea
            this.style.height = 'auto'; // reset
            this.style.height = this.scrollHeight + 'px';

            // 3️⃣ Scroll cursor into view if necessary
            this.scrollTop = this.scrollHeight;

            e.preventDefault(); // prevent default behavior
        } else {
            // Enter alone → send message
            e.preventDefault();
            handleSend();
        }
    }
});



// 6. SEARCH LOGIC
const searchInput = document.getElementById('searchInput');
window.addEventListener('DOMContentLoaded', () => {
    const list = document.getElementById('historyList');
    if (list) originalHistoryHTML = list.innerHTML;
});

searchInput.addEventListener('input', (e) => {
    const term = e.target.value.trim();
    const historyList = document.getElementById('historyList');
    clearTimeout(searchTimeout);
    if (term.length === 0) { historyList.innerHTML = originalHistoryHTML; return; }
    if (term.length < 2) return;
    historyList.innerHTML = '<div class="p-3 text-center text-white"><span class="spinner-border spinner-border-sm me-2"></span>Searching...</div>';
    searchTimeout = setTimeout(async () => {
        if (searchController) searchController.abort();
        searchController = new AbortController();
        try {
            const response = await fetch(`/ai/search/?q=${encodeURIComponent(term)}`, { signal: searchController.signal });
            const data = await response.json();
            historyList.innerHTML = ''; 
            if (data.results.length === 0) { historyList.innerHTML = '<div class="p-3 text-white text-center">No matches.</div>'; return; }
            data.results.forEach(res => {
                const div = document.createElement('div');
                div.className = 'history-item';
                div.setAttribute('data-id', res.id); 
    
                div.onclick = () => loadSession(res.id);
                div.addEventListener('click', () => loadSession(res.id));
                div.innerHTML = `<div class="d-flex justify-content-between align-items-center" style="pointer-events: none;"><span class="text-truncate"><i class="bi bi-search me-2"></i>${res.title}</span><span class="badge bg-dark">${res.type}</span></div>`;
                historyList.appendChild(div);
            });
        } catch (err) { if (err.name !== 'AbortError') historyList.innerHTML = 'Error.'; }
    }, 400); 
});

// 7. SPEECH RECOGNITION
const micBtn = document.getElementById('micBtn');
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.continuous = true; 
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    let silenceTimer = null;

    micBtn.addEventListener('click', () => {
        stopSpeaking();

        if (micBtn.classList.contains('active')) {
            clearTimeout(silenceTimer);
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    recognition.onstart = () => {
        userUsedVoice = true; 
        micBtn.classList.add('active');
        userIn.placeholder = "CodeVisor-AI is listening...";
    };

    recognition.onresult = (event) => {
        clearTimeout(silenceTimer);
        let transcript = "";
        for (let i = 0; i < event.results.length; i++) { transcript += event.results[i][0].transcript; }
        userIn.value = transcript;
        userIn.style.height = 'auto';
        userIn.style.height = (userIn.scrollHeight) + 'px';
        silenceTimer = setTimeout(() => { recognition.stop(); }, 3000);
    };

    recognition.onend = () => {
        micBtn.classList.remove('active');
        userIn.placeholder = "Type your message here...";
        if (userIn.value.trim().length > 0) handleSend();
    };
} else { micBtn.style.display = 'none'; }


// MOBILE SIDEBAR TOGGLE
const menuBtn = document.querySelector('.mobile-menu-btn');

if (menuBtn) {
    const sidebar = document.querySelector('.sidebar');

    // Create overlay dynamically
    const overlay = document.createElement('div');
    overlay.classList.add('sidebar-overlay');
    document.body.appendChild(overlay);

    menuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    });

    overlay.addEventListener('click', () => {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });
}