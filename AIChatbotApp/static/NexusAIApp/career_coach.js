/**
 * CodeVisor AI Career Suite Core Logic Controller
 * Target Namespace: NexusAIApp
 */

let currentCoachSessionId = null;
let coachSearchTimeout = null;
let originalCoachHistoryHTML = "";
const coachSynth = window.speechSynthesis;

// Markdown Initializer configuration factory
const coachMd = window.markdownit({
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
        return '<pre><button class="copy-code-btn" onclick="copyCode(this)">Copy</button><code class="hljs">' + coachMd.utils.escapeHtml(str) + '</code></pre>';
    }
});

window.onload = () => {
    const list = document.getElementById('coachHistoryList');
    if (list) originalCoachHistoryHTML = list.innerHTML;
};

// Auto-Growing Textarea Handler
const coachTextArea = document.getElementById('coachUserIn');
if (coachTextArea) {
    coachTextArea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        this.style.overflowY = this.scrollHeight > 180 ? 'auto' : 'hidden';
    });

    coachTextArea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleCoachSend();
        }
    });
}

// Trigger Input Pre-baked chips workflow
function triggerActionChip(promptText) {
    document.getElementById('welcomeDeck')?.remove();
    const input = document.getElementById('coachUserIn');
    if (input) {
        input.value = promptText;
        handleCoachSend();
    }
}

// Highlight Sidebar element helper
function highlightActiveCoachSession(sessionId) {
    document.querySelectorAll('.history-card').forEach(item => item.classList.remove('active'));
    document.querySelectorAll('.history-card').forEach(item => {
        const onClickAttr = item.getAttribute('onclick');
        if (onClickAttr && onClickAttr.includes(sessionId)) {
            item.classList.add('active');
        }
    });
}

// Load Past Session Sheets History Endpoint
async function loadCoachSession(sessionId) {
    currentCoachSessionId = sessionId;
    highlightActiveCoachSession(sessionId);
    
    const viewport = document.getElementById('coachViewport');
    viewport.innerHTML = '<div class="p-5 text-center text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading counseling records...</div>';
    
    try {
        const response = await fetch(`/ai/session/${sessionId}/`);
        const data = await response.json();
        viewport.innerHTML = '';
        
        data.history.forEach(msg => {
            appendDossierMessage(msg.content, msg.role, false);
        });
    } catch (err) {
        viewport.innerHTML = '<div class="p-5 text-center text-danger">Failed to sync session history logs.</div>';
    }
}

// 🌟 THE CORE UX MASTERPIECE: EXTRACTS DOSSIER CARDS & CHECKLISTS SEPARATELY
function appendDossierMessage(text, role, isNew = false) {
    const viewport = document.getElementById('coachViewport');
    document.getElementById('welcomeDeck')?.remove();

    const msgRow = document.createElement('div');
    msgRow.className = `msg-row ${role}`;

    const avatarHTML = role === 'bot' ? 
        '<div class="avatar-container"><i class="bi bi-briefcase-fill"></i></div>' : 
        '<div class="avatar-container"><i class="bi bi-person-fill"></i></div>';

    if (role === 'user') {
        // Simple candidate message display
        msgRow.innerHTML = `${avatarHTML}<div class="dossier-card-bubble">${text}</div>`;
        viewport.appendChild(msgRow);
        viewport.scrollTop = viewport.scrollHeight;
        return;
    }

    // AI BOT PROCESSING CORE: PARSE TEXT AND EXTRACT TO-DO ITEMS VIA REGEX BRACKETS
    let mainBodyContent = text;
    let todoItems = [];

    // Capture lines that match patterns like "- [ ] Task" or "1. [ ] Task" or "[ ] Task"
    const todoRegex = /(?:[-*+]|\d+\.)?\s*\[\s*\]\s*(.+)/g;
    let match;
    let matchesFound = [];

    while ((match = todoRegex.exec(text)) !== null) {
        todoItems.push(match[1].trim());
        matchesFound.push(match[0]);
    }

    // Clean out the raw to-do bracket syntax lines from the text so they don't print double
    matchesFound.forEach(rawLine => {
        mainBodyContent = mainBodyContent.replace(rawLine, '');
    });

    // Strip trailing empty title blocks or leftovers safely
    mainBodyContent = mainBodyContent.replace(/###?\s*(?:Immediate Action Items|To-Do List|Tasks|Homework):?\s*$/i, '').trim();

    // Build the Dossier Header Strip
    const headerStripHTML = `
        <div class="dossier-header-strip">
            <span class="text-xs font-monospace text-muted uppercase fw-bold"><i class="bi bi-info-circle-fill text-success me-1"></i>Vetting Evaluation Brief</span>
            <span class="text-xs font-monospace text-muted">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
        </div>`;

    // Build the To-Do Footer Card if items were discovered in the payload response string
    // Build the To-Do Footer Card if items were discovered in the payload response string
    let todoFooterHTML = '';
    if (todoItems.length > 0) {
        const uniqueIdPrefix = Date.now();
        
        // 🌟 THE FIX: Compile inner markdown inline tokens (like asterisks to strong bold tags) 
        // using coachMd.renderInline() before injecting them into the HTML text node!
        const checklistRows = todoItems.map((item, idx) => {
            const compiledItemText = coachMd.renderInline(item);
            return `
                <label class="todo-item-row" for="todo-${uniqueIdPrefix}-${idx}">
                    <input type="checkbox" class="todo-checkbox-input" id="todo-${uniqueIdPrefix}-${idx}">
                    <span class="todo-item-text">${compiledItemText}</span>
                </label>
            `;
        }).join('');

        todoFooterHTML = `
            <div class="dossier-todo-footer-panel">
                <div class="todo-title-row"><i class="bi bi-card-checklist"></i>Immediate Administrative Action Checklist</div>
                <div class="todo-checklist-group">${checklistRows}</div>
            </div>`;
    }

    // Update this layout block inside appendDossierMessage()
    msgRow.innerHTML = `
        <div class="row g-2 w-100 mx-0 align-items-start my-2">
            <div class="col-auto">
                ${avatarHTML}
            </div>
            <div class="col">
                <div class="dossier-card-bubble">
                    ${headerStripHTML}
                    <div class="dossier-body-text"></div>
                    ${todoFooterHTML}
                </div>
            </div>
        </div>`;

    viewport.appendChild(msgRow);
    const contentTarget = msgRow.querySelector('.dossier-body-text');

    if (isNew) {
        // Run crisp, controlled typewriter animation transitions
        let currentIdx = 0;
        const speed = 3;
        function type() {
            if (currentIdx < mainBodyContent.length) {
                let chunk = mainBodyContent.slice(0, currentIdx + 1);
                contentTarget.innerHTML = coachMd.render(chunk);
                viewport.scrollTop = viewport.scrollHeight;
                currentIdx++;
                setTimeout(type, speed);
            } else {
                contentTarget.innerHTML = coachMd.render(mainBodyContent);
                contentTarget.querySelectorAll('pre code').forEach((el) => { hljs.highlightElement(el); });
                viewport.scrollTop = viewport.scrollHeight;
            }
        }
        type();
    } else {
        contentTarget.innerHTML = coachMd.render(mainBodyContent);
        contentTarget.querySelectorAll('pre code').forEach((el) => { hljs.highlightElement(el); });
        viewport.scrollTop = viewport.scrollHeight;
    }
}

// Dispatch Post Request Payload Loop via AJAX
async function handleCoachSend() {
    const input = document.getElementById('coachUserIn');
    const submitBtn = document.getElementById('coachSubmitBtn');
    const text = input.value.trim();
    if (!text) return;

    // Lock input UI state fields during runtime
    input.disabled = true;
    submitBtn.disabled = true;

    appendDossierMessage(text, 'user', false);
    input.value = '';
    input.style.height = 'auto';

    // Append loading spinner card placeholder block
    const viewport = document.getElementById('coachViewport');
    const loader = document.createElement('div');
    loader.id = 'coach-loader';
    loader.className = 'msg-row bot';
    loader.innerHTML = '<div class="avatar-container"><i class="bi bi-briefcase-fill"></i></div><div class="dossier-card-bubble p-4 text-muted"><span class="spinner-grow spinner-grow-sm text-success me-2"></span>AI Coach compiling metric analysis strategy...</div>';
    viewport.appendChild(loader);
    viewport.scrollTop = viewport.scrollHeight;

    try {
        const response = await fetch('/ai/career-coach/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ message: text, session_id: currentCoachSessionId })
        });

        const data = await response.json();
        document.getElementById('coach-loader')?.remove();

        if (data.session_id) currentCoachSessionId = data.session_id;

        appendDossierMessage(data.response, 'bot', true);

    } catch (e) {
        document.getElementById('coach-loader')?.remove();
        appendDossierMessage("System Error: Strategy Engine response timed out.", 'bot', false);
    } finally {
        input.disabled = false;
        submitBtn.disabled = false;
        input.focus();
    }
}

// Copy source block utility helper
function copyCode(btn) {
    const code = btn.nextElementSibling.innerText;
    navigator.clipboard.writeText(code);
    btn.innerText = "Copied!";
    setTimeout(() => btn.innerText = "Copy", 1800);
}

// 🎤 VOICE DIRECTS DICTATION COMPONENT LAYER
const micBtn = document.getElementById('coachMicBtn');
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = 'en-US';

    micBtn.addEventListener('click', () => {
        if (micBtn.classList.contains('active')) {
            rec.stop();
        } else {
            rec.start();
        }
    });

    rec.onstart = () => {
        micBtn.classList.add('active');
        document.getElementById('coachUserIn').placeholder = "Listening to career focus goals...";
    };

    rec.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        const input = document.getElementById('coachUserIn');
        if (input) {
            input.value = transcript;
            input.style.height = 'auto';
            input.style.height = (input.scrollHeight) + 'px';
        }
    };

    rec.onend = () => {
        micBtn.classList.remove('active');
        document.getElementById('coachUserIn').placeholder = "Query your corporate placement advisor or pass a workflow directive...";
    };
} else {
    if (micBtn) micBtn.style.display = 'none';
}