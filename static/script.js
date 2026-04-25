// ── Helper: safe element getter ───────────────────────────────────
const el = (id) => document.getElementById(id);

// ── DOM refs ──────────────────────────────────────────────────────
const form        = el('debug-form');
const submitBtn   = el('submit-btn');
const btnText     = el('btn-text');
const btnLoader   = el('btn-loader');
const placeholder = el('results-placeholder');
const resultsCont = el('results-content');

// ── State for follow-up chat ──────────────────────────────────────
let lastDebugContext = null;

// ── Language → Prism class mapping ────────────────────────────────
const LANG_MAP = {
    'python':     'language-python',
    'javascript': 'language-javascript',
    'java':       'language-java',
    'c++':        'language-cpp',
    'c#':         'language-csharp',
    'php':        'language-php',
    'rust':       'language-rust',
    'go':         'language-go',
    'sql':        'language-sql',
    'sqlite':     'language-sql',
    'postgresql': 'language-sql',
    'mysql':      'language-sql',
};

function getPrismClass(lang) {
    if (!lang) return '';
    return LANG_MAP[lang.toLowerCase()] || '';
}

// ── Example Presets ───────────────────────────────────────────────
const PRESETS = {
    python: {
        error: `ZeroDivisionError: division by zero
Traceback (most recent call last):
  File "calc.py", line 5, in <module>
    result = divide(10, 0)
  File "calc.py", line 3, in divide
    return a / b`,
        code: `def divide(a, b):
    """Divide two numbers."""
    return a / b

result = divide(10, 0)
print(f"Result: {result}")`
    },
    js: {
        error: `TypeError: Cannot read properties of undefined (reading 'map')
    at renderList (app.js:12:24)
    at main (app.js:18:5)`,
        code: `function renderList(data) {
    const items = data.users.map(user => {
        return \`<li>\${user.name}</li>\`;
    });
    return items.join('');
}

function main() {
    const response = {};  // API returned empty object
    const html = renderList(response);
    console.log(html);
}

main();`
    },
    sql: {
        error: `ERROR: division by zero
SQL state: 22012
Character: 47`,
        code: `SELECT
    product_name,
    total_revenue / total_units AS avg_price
FROM sales_summary
WHERE category = 'Electronics';`
    },
    url: {
        error: `Invalid URL: missing scheme, no TLD found`,
        code: `www.example`
    }
};

el('preset-python')?.addEventListener('click', () => fillPreset('python'));
el('preset-js')?.addEventListener('click', () => fillPreset('js'));
el('preset-sql')?.addEventListener('click', () => fillPreset('sql'));
el('preset-url')?.addEventListener('click', () => fillPreset('url'));

function fillPreset(key) {
    const preset = PRESETS[key];
    if (!preset) return;
    const errorInput = el('error-input');
    const codeInput = el('code-input');
    if (errorInput) errorInput.value = preset.error;
    if (codeInput) codeInput.value = preset.code;
    // Animate the preset button
    const btn = el(`preset-${key}`);
    if (btn) {
        btn.classList.add('preset-active');
        setTimeout(() => btn.classList.remove('preset-active'), 600);
    }
}

// ── Pipeline Status Helpers ───────────────────────────────────────
const STEP_ORDER = ['pattern_lookup', 'analyzing', 'fixing', 'validating', 'executing', 'optimizing'];
const STEP_MAP = {
    pattern_lookup: 'pipe-pattern',
    analyzing: 'pipe-analyze',
    fixing: 'pipe-fix',
    retrying: 'pipe-fix',
    validating: 'pipe-validate',
    executing: 'pipe-execute',
    optimizing: 'pipe-optimize',
};

function showPipeline() {
    const ps = el('pipeline-status');
    if (ps) ps.style.display = 'block';
    // Reset all steps
    document.querySelectorAll('.pipe-step').forEach(s => {
        s.classList.remove('active', 'done');
    });
}

function hidePipeline() {
    const ps = el('pipeline-status');
    if (ps) ps.style.display = 'none';
}

function updatePipeline(step, message) {
    const msgEl = el('pipeline-msg');
    if (msgEl) msgEl.textContent = message || '';

    const currentId = STEP_MAP[step];
    if (!currentId) return;

    // Mark previous steps as done
    const currentIndex = STEP_ORDER.indexOf(step);
    STEP_ORDER.forEach((s, idx) => {
        const stepEl = el(STEP_MAP[s]);
        if (!stepEl) return;
        if (idx < currentIndex) {
            stepEl.classList.remove('active');
            stepEl.classList.add('done');
        } else if (idx === currentIndex) {
            stepEl.classList.add('active');
            stepEl.classList.remove('done');
        }
    });
}


// ── Submit handler — SSE Streaming ────────────────────────────────
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const errorInput = el('error-input')?.value?.trim();
    const codeInput  = el('code-input')?.value?.trim();
    if (!errorInput || !codeInput) return;

    setLoading(true);
    showPipeline();
    resetResults();

    // Store context for follow-up chat
    lastDebugContext = {
        original_error: errorInput,
        original_code: codeInput,
        fixed_code: '',
        analysis: {},
        fix_explanation: '',
    };

    try {
        const res = await fetch('/debug-stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ error: errorInput, code: codeInput })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Server error ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // SSE messages are separated by double newlines
            const messages = buffer.split('\n\n');
            // Last element might be incomplete — keep it in buffer
            buffer = messages.pop() || '';

            for (const msg of messages) {
                if (!msg.trim()) continue;

                let eventType = null;
                let dataStr = null;

                for (const line of msg.split('\n')) {
                    if (line.startsWith('event: ')) {
                        eventType = line.slice(7).trim();
                    } else if (line.startsWith('data: ')) {
                        dataStr = line.slice(6);
                    }
                }

                if (eventType && dataStr) {
                    try {
                        const data = JSON.parse(dataStr);
                        handleSSEEvent(eventType, data);
                    } catch (parseErr) {
                        console.warn('SSE parse error:', parseErr, dataStr?.substring(0, 100));
                    }
                }
            }
        }
    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
        hidePipeline();
    }
});


// ── SSE Event Handler ─────────────────────────────────────────────
function handleSSEEvent(event, data) {
    switch (event) {
        case 'status':
            updatePipeline(data.step, data.message);
            break;

        case 'pattern_match':
            showPatternMatch(data);
            break;

        case 'analysis':
            showAnalysis(data);
            break;

        case 'fix':
            showFix(data);
            break;

        case 'retry':
            // Could show a retry indicator
            break;

        case 'execution':
            showExecution(data);
            break;

        case 'optimization':
            showOptimization(data);
            break;

        case 'complete':
            showComplete(data);
            break;

        case 'error':
            showError(data.detail || 'Unknown error');
            break;
    }
}


// ── Progressive Rendering Functions ───────────────────────────────
function resetResults() {
    if (placeholder)  placeholder.style.display  = 'none';
    if (resultsCont)  resultsCont.style.display   = 'block';

    // Hide optional cards
    ['card-confidence', 'card-pattern', 'card-optimization', 'card-diff',
     'card-execution', 'card-chat'].forEach(id => {
        const c = el(id);
        if (c) c.style.display = 'none';
    });

    // Clear content
    setText('lang-text', '—');
    setText('type-text', '—');
    setText('retry-text', '0 retries');
    setText('res-fix-explanation', '');
    const analysisEl = el('res-analysis');
    if (analysisEl) analysisEl.textContent = '';
    const codeEl = el('res-updated-code');
    if (codeEl) codeEl.textContent = '';
    const stepsList = el('res-steps-list');
    if (stepsList) stepsList.innerHTML = '';
    const chatMsgs = el('chat-messages');
    if (chatMsgs) chatMsgs.innerHTML = '';
}

function showPatternMatch(data) {
    const card = el('card-pattern');
    if (!card) return;
    card.style.display = 'flex';
    setText('pattern-detail', `${data.error_type}: ${data.fix_explanation || data.cause}`);
    setText('pattern-similarity', `${data.similarity}% match`);
    card.style.animation = 'slideUpFade 0.4s ease-out forwards';
}

function showAnalysis(data) {
    const detectedLang = (data.detected_language || '').toLowerCase();
    setText('lang-text', data.detected_language || '—');
    setText('type-text', (data.problem_type || '—').replace(/_/g, ' '));
    setText('editor-lang-label', (data.detected_language || 'code').toLowerCase());

    const analysisEl = el('res-analysis');
    if (analysisEl) {
        const analysis = data.analysis;
        const analysisText = typeof analysis === 'object' && analysis !== null
            ? JSON.stringify(analysis, null, 2)
            : (analysis || 'No analysis provided.');
        analysisEl.className = 'language-json';
        analysisEl.textContent = analysisText;
        Prism.highlightElement(analysisEl);
    }

    // Update context
    if (lastDebugContext) {
        lastDebugContext.analysis = data.analysis;
    }

    // Animate card
    animateCard('card-analysis');
}

function showFix(data) {
    const fix = data.fix;
    const detectedLang = el('lang-text')?.textContent?.toLowerCase() || '';
    const prismClass = getPrismClass(detectedLang);

    // Steps
    renderSteps(data.steps || []);

    // Fix explanation
    let explanation = 'No explanation.';
    let code = '';
    if (fix && typeof fix === 'object') {
        explanation = fix.explanation || JSON.stringify(fix, null, 2);
        code = fix.updated_code || fix.code || '';
    } else if (typeof fix === 'string') {
        explanation = fix;
    }
    setText('res-fix-explanation', explanation);
    setText('retry-text', retryLabel(data.retries_taken));

    // Fixed code
    const codeEl = el('res-updated-code');
    if (codeEl) {
        codeEl.className = prismClass || '';
        codeEl.textContent = code;
        if (prismClass) Prism.highlightElement(codeEl);
    }

    // Validation
    const isValid = data.validation?.valid === true;
    const reason = typeof data.validation?.reason === 'object'
        ? JSON.stringify(data.validation.reason)
        : (data.validation?.reason || '');

    const elVal = el('res-validation');
    const cardVal = el('card-validation');
    if (elVal) {
        elVal.textContent = isValid
            ? '✓  Fix is Valid'
            : `✗  Validation failed: ${reason}`;
        elVal.className = `validation-pill ${isValid ? 'success' : 'error'}`;
    }
    if (cardVal) {
        cardVal.classList.toggle('valid-card', isValid);
        cardVal.classList.toggle('invalid-card', !isValid);
    }

    // Update context
    if (lastDebugContext) {
        lastDebugContext.fixed_code = code;
        lastDebugContext.fix_explanation = explanation;
    }

    // Animate cards
    ['card-steps', 'card-explanation', 'card-code', 'card-validation'].forEach((id, i) => {
        setTimeout(() => animateCard(id), i * 80);
    });
}

function showExecution(data) {
    const card = el('card-execution');
    if (!card) return;
    card.style.display = 'block';

    const output = el('execution-output');
    const timeEl = el('execution-time');

    if (output) {
        if (data.success) {
            output.textContent = data.output || '(no output)';
            output.className = 'terminal-output terminal-success';
        } else {
            output.textContent = data.error || 'Execution failed';
            output.className = 'terminal-output terminal-error';
        }
    }
    if (timeEl) {
        timeEl.textContent = `${data.execution_time_ms}ms`;
    }

    animateCard('card-execution');
}

function showOptimization(data) {
    if (!data.optimization_note) return;
    const card = el('card-optimization');
    if (!card) return;
    card.style.display = 'block';
    setText('res-optimization-note', data.optimization_note);

    // Update the code if simplified
    if (data.simplified && data.updated_code) {
        const codeEl = el('res-updated-code');
        const detectedLang = el('lang-text')?.textContent?.toLowerCase() || '';
        const prismClass = getPrismClass(detectedLang);
        if (codeEl) {
            codeEl.textContent = data.updated_code;
            if (prismClass) {
                codeEl.className = prismClass;
                Prism.highlightElement(codeEl);
            }
        }
        if (lastDebugContext) {
            lastDebugContext.fixed_code = data.updated_code;
        }
    }

    animateCard('card-optimization');
}

function showComplete(data) {
    // Confidence score
    showConfidence(data.confidence_score);

    // Code diff
    const originalCode = data.original_code || '';
    const fixedCode = data.fix?.updated_code || '';
    renderDiff(originalCode, fixedCode);

    // Pattern count footer
    setText('pattern-count-footer', data.patterns_stored || 0);

    // Show chat card
    const chatCard = el('card-chat');
    if (chatCard) {
        chatCard.style.display = 'block';
        animateCard('card-chat');
    }

    // Save to history
    saveToHistory(data);

    // Cascade animation for all visible cards
    resultsCont?.querySelectorAll('.card:not([style*="display: none"]):not([style*="display:none"])').forEach((card, idx) => {
        if (card.style.opacity !== '1') {
            card.style.animation = 'none';
            void card.offsetHeight;
            card.style.animation = `slideUpFade 0.38s ease-out ${idx * 0.06}s forwards`;
        }
    });
}

function showConfidence(score) {
    const card = el('card-confidence');
    if (!card) return;
    card.style.display = 'flex';

    const ring = el('confidence-ring-fill');
    const valueEl = el('confidence-value');
    const descEl = el('confidence-desc');

    if (ring) {
        const circumference = 2 * Math.PI * 42;
        ring.style.strokeDasharray = `${circumference}`;
        const offset = circumference - (score / 100) * circumference;

        // Animate the ring
        ring.style.strokeDashoffset = circumference;
        setTimeout(() => {
            ring.style.transition = 'stroke-dashoffset 1.2s ease-out';
            ring.style.strokeDashoffset = offset;
        }, 100);

        // Color based on score
        if (score >= 75) {
            ring.style.stroke = 'var(--green)';
        } else if (score >= 50) {
            ring.style.stroke = 'var(--yellow)';
        } else {
            ring.style.stroke = 'var(--red)';
        }
    }

    // Animate counter
    if (valueEl) {
        animateCounter(valueEl, score);
    }

    if (descEl) {
        if (score >= 80) descEl.textContent = 'High confidence — fix is very likely correct';
        else if (score >= 60) descEl.textContent = 'Moderate confidence — review recommended';
        else if (score >= 40) descEl.textContent = 'Low confidence — manual review needed';
        else descEl.textContent = 'Very low confidence — fix may be incorrect';
    }

    card.style.animation = 'slideUpFade 0.5s ease-out forwards';
}

function animateCounter(element, target) {
    let current = 0;
    const duration = 1200;
    const step = target / (duration / 16);
    function tick() {
        current += step;
        if (current >= target) {
            element.textContent = `${target}%`;
            return;
        }
        element.textContent = `${Math.floor(current)}%`;
        requestAnimationFrame(tick);
    }
    tick();
}

function animateCard(id) {
    const card = el(id);
    if (!card) return;
    card.style.animation = 'none';
    card.style.opacity = '0';
    void card.offsetHeight;
    card.style.animation = 'slideUpFade 0.38s ease-out forwards';
}


// ── Loading state ─────────────────────────────────────────────────
function setLoading(on) {
    if (submitBtn) submitBtn.disabled = on;
    if (btnText)   btnText.style.display   = on ? 'none' : 'flex';
    if (btnLoader) btnLoader.style.display = on ? 'flex' : 'none';
}

// ── Error display ─────────────────────────────────────────────────
function showError(msg) {
    if (!placeholder) return;
    placeholder.style.display = 'flex';
    placeholder.innerHTML = `
        <div class="empty-icon" style="border-color:rgba(244,63,94,0.3);">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#f43f5e" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
        </div>
        <p class="empty-title" style="color:#f43f5e;">Agent Error</p>
        <p class="empty-sub">${escapeHtml(msg)}</p>`;
    if (resultsCont) resultsCont.style.display = 'none';
}


// ── Diff renderer ─────────────────────────────────────────────────
function renderDiff(original, fixed) {
    const diffCard = el('card-diff');
    const diffEl   = el('res-diff');
    if (!diffCard || !diffEl) return;

    if (!original || !fixed || original.trim() === fixed.trim()) {
        diffCard.style.display = 'none';
        return;
    }

    const origLines = original.split('\n');
    const fixedLines = fixed.split('\n');
    const diffHtml = computeLineDiff(origLines, fixedLines);

    diffEl.innerHTML = diffHtml;
    diffCard.style.display = 'block';
    animateCard('card-diff');
}

function computeLineDiff(oldLines, newLines) {
    const results = [];
    const oldSet = new Set(oldLines.map(l => l.trimEnd()));
    const newSet = new Set(newLines.map(l => l.trimEnd()));

    let oi = 0, ni = 0;

    while (oi < oldLines.length || ni < newLines.length) {
        const oldLine = oi < oldLines.length ? oldLines[oi] : null;
        const newLine = ni < newLines.length ? newLines[ni] : null;

        if (oldLine !== null && newLine !== null && oldLine.trimEnd() === newLine.trimEnd()) {
            results.push(`<span class="diff-ctx"> ${escapeHtml(oldLine)}</span>`);
            oi++; ni++;
        } else if (oldLine !== null && !newSet.has(oldLine.trimEnd())) {
            results.push(`<span class="diff-del">-${escapeHtml(oldLine)}</span>`);
            oi++;
        } else if (newLine !== null && !oldSet.has(newLine.trimEnd())) {
            results.push(`<span class="diff-add">+${escapeHtml(newLine)}</span>`);
            ni++;
        } else {
            if (oldLine !== null) {
                results.push(`<span class="diff-del">-${escapeHtml(oldLine)}</span>`);
                oi++;
            }
            if (newLine !== null) {
                results.push(`<span class="diff-add">+${escapeHtml(newLine)}</span>`);
                ni++;
            }
        }
    }

    return results.join('\n');
}

// ── Steps renderer ────────────────────────────────────────────────
function renderSteps(steps) {
    const list = el('res-steps-list');
    if (!list) return;
    list.innerHTML = '';
    if (!steps.length) {
        const li = document.createElement('li');
        li.textContent = 'No steps recorded.';
        list.appendChild(li);
        return;
    }
    steps.forEach(step => {
        const li = document.createElement('li');
        li.textContent = step;
        const s = step.toLowerCase();
        if (s.includes('validation passed'))     li.classList.add('validation-step');
        else if (s.startsWith('optimization'))   li.classList.add('optimization-step');
        list.appendChild(li);
    });
}


// ── Follow-Up Chat ────────────────────────────────────────────────
const chatInput = el('chat-input');
const chatSendBtn = el('chat-send-btn');

function sendFollowUp() {
    const question = chatInput?.value?.trim();
    if (!question || !lastDebugContext) return;

    // Show user message
    appendChatMessage('user', question);
    chatInput.value = '';
    chatSendBtn.disabled = true;

    // Show typing indicator
    const typingId = appendChatMessage('assistant', '...');
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.classList.add('chat-typing');

    fetch('/followup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question,
            original_error: lastDebugContext.original_error,
            original_code: lastDebugContext.original_code,
            fixed_code: lastDebugContext.fixed_code,
            analysis: lastDebugContext.analysis,
            fix_explanation: lastDebugContext.fix_explanation,
        })
    })
    .then(res => res.json())
    .then(data => {
        if (typingEl) {
            typingEl.classList.remove('chat-typing');
            typingEl.querySelector('.chat-text').textContent = data.answer || 'No response.';
        }
    })
    .catch(err => {
        if (typingEl) {
            typingEl.classList.remove('chat-typing');
            typingEl.querySelector('.chat-text').textContent = `Error: ${err.message}`;
        }
    })
    .finally(() => {
        chatSendBtn.disabled = false;
        chatInput.focus();
    });
}

chatSendBtn?.addEventListener('click', sendFollowUp);
chatInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendFollowUp();
    }
});

let chatMsgCounter = 0;
function appendChatMessage(role, text) {
    const container = el('chat-messages');
    if (!container) return;

    const id = `chat-msg-${++chatMsgCounter}`;
    const wrapper = document.createElement('div');
    wrapper.className = `chat-bubble chat-${role}`;
    wrapper.id = id;

    const avatar = role === 'user' ? '👤' : '🤖';
    wrapper.innerHTML = `
        <span class="chat-avatar">${avatar}</span>
        <span class="chat-text">${escapeHtml(text)}</span>
    `;

    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
    return id;
}


// ── Debug History (localStorage) ──────────────────────────────────
const HISTORY_KEY = 'autodebug_history';
const MAX_HISTORY = 15;

function getHistory() {
    try {
        return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    } catch { return []; }
}

function saveToHistory(data) {
    const history = getHistory();
    const entry = {
        id: Date.now(),
        timestamp: new Date().toLocaleString(),
        error_type: data.analysis?.error_type || 'Unknown',
        language: data.detected_language || '—',
        problem_type: data.problem_type || '—',
        valid: data.validation?.valid === true,
        confidence: data.confidence_score || 0,
        data: data,
    };
    history.unshift(entry);
    if (history.length > MAX_HISTORY) history.length = MAX_HISTORY;
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderHistory();
}

function renderHistory() {
    const section = el('history-section');
    const list = el('history-list');
    if (!section || !list) return;

    const history = getHistory();
    if (!history.length) {
        section.style.display = 'none';
        return;
    }
    section.style.display = 'block';
    list.innerHTML = '';

    history.forEach(entry => {
        const item = document.createElement('button');
        item.className = 'history-item';
        item.type = 'button';
        const statusIcon = entry.valid ? '✓' : '✗';
        const statusClass = entry.valid ? 'history-valid' : 'history-invalid';
        const confBadge = entry.confidence
            ? `<span class="history-conf">${entry.confidence}%</span>`
            : '';
        item.innerHTML = `
            <span class="history-status ${statusClass}">${statusIcon}</span>
            <div class="history-info">
                <span class="history-error">${escapeHtml(entry.error_type)}</span>
                <span class="history-meta">${escapeHtml(entry.language)} · ${escapeHtml(entry.timestamp)}</span>
            </div>
            ${confBadge}
        `;
        item.addEventListener('click', () => renderFullResults(entry.data));
        list.appendChild(item);
    });
}

// Render full results from history (non-streaming fallback)
function renderFullResults(data) {
    resetResults();

    lastDebugContext = {
        original_error: '',
        original_code: data.original_code || '',
        fixed_code: data.fix?.updated_code || '',
        analysis: data.analysis || {},
        fix_explanation: data.fix?.explanation || '',
    };

    showAnalysis({
        analysis: data.analysis,
        detected_language: data.detected_language,
        problem_type: data.problem_type,
    });

    showFix({
        fix: data.fix,
        validation: data.validation,
        steps: data.steps,
        retries_taken: data.retries_taken,
    });

    if (data.sandbox_result) {
        showExecution(data.sandbox_result);
    }

    if (data.optimization_note) {
        showOptimization({
            optimization_note: data.optimization_note,
            simplified: false,
        });
    }

    showComplete(data);
}

// Clear history
el('clear-history-btn')?.addEventListener('click', () => {
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
});

// Load history on page load
renderHistory();

// ── Utilities ─────────────────────────────────────────────────────
function setText(id, text) {
    const node = el(id);
    if (node) node.textContent = text ?? '';
}

function retryLabel(n) {
    if (n === undefined || n === null) return '0 retries';
    return `${n} ${n === 1 ? 'retry' : 'retries'}`;
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

// ── Copy button ───────────────────────────────────────────────────
el('copy-btn')?.addEventListener('click', () => {
    const code = el('res-updated-code')?.textContent;
    if (!code) return;
    navigator.clipboard.writeText(code).then(() => {
        const btn = el('copy-btn');
        if (!btn) return;
        const orig = btn.innerHTML;
        btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
        btn.style.color = 'var(--green)';
        setTimeout(() => { btn.innerHTML = orig; btn.style.color = ''; }, 2200);
    }).catch(() => {});
});
