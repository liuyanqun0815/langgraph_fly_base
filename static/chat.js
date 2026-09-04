(function () {
    var input = document.getElementById('chat-input');
    var form = document.getElementById('chat-form');
    var thread = document.getElementById('chat-thread');
    var sessionInput = document.getElementById('sessionId');
    var sessionDisplay = document.getElementById('session-display');
    var copyBtn = document.getElementById('copy-session');
    var sendBtn = document.querySelector('.composer-box__send');

    if (!input || !form) return;

    var isSubmitting = false;
    var streamingMsgEl = null;
    var streamingContentEl = null;
    var workflowStepEls = {};
    var workflowStepsEl = null;
    var execResultEl = null;
    var execStatusEl = null;
    var execCountEl = null;
    var stepTotal = 0;
    var turnStartTime = 0;

    function formatTime(date) {
        return [date.getHours(), date.getMinutes(), date.getSeconds()]
            .map(function (n) {
                return String(n).padStart(2, '0');
            })
            .join(':');
    }

    function formatDuration(ms) {
        if (ms < 1000) {
            return ms + 'ms';
        }
        return (ms / 1000).toFixed(1) + 's';
    }

    function buildBotMetaText(startTime) {
        var elapsed = Date.now() - startTime;
        return formatTime(new Date()) + ' · 耗时 ' + formatDuration(elapsed);
    }

    var USER_AVATAR =
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">' +
        '<path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg>';

    var BOT_AVATAR =
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">' +
        '<path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/></svg>';

    var ICON_CHECK =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">' +
        '<path d="M20 6L9 17l-5-5"/></svg>';

    var ICON_SPINNER =
        '<svg class="exec-step__spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
        '<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/></svg>';

    var NODE_META = {
        '前置安全校验': { tone: 'green', icon: 'shield' },
        '问题修复': { tone: 'green', icon: 'start' },
        '问题分类': { tone: 'blue', icon: 'strategy' },
        '意图确认': { tone: 'blue', icon: 'strategy' },
        '信息收集': { tone: 'blue', icon: 'strategy' },
        '信息确认': { tone: 'blue', icon: 'strategy' },
        '闲聊经理': { tone: 'amber', icon: 'reply' },
        '产品解答专家': { tone: 'indigo', icon: 'model' },
        '产品推荐': { tone: 'blue', icon: 'strategy' },
        '客户转化': { tone: 'green', icon: 'shield' },
        '信息提取': { tone: 'blue', icon: 'strategy' },
    };

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function nodeMeta(nodeName) {
        return NODE_META[nodeName] || { tone: 'blue', icon: 'strategy' };
    }

    function stepIconSvg(icon) {
        if (icon === 'shield') {
            return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>';
        }
        if (icon === 'start') {
            return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/></svg>';
        }
        if (icon === 'model') {
            return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>';
        }
        if (icon === 'reply') {
            return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
        }
        return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>';
    }

    function autoResize() {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 160) + 'px';
    }

    function scrollToBottom() {
        if (thread) thread.scrollTop = thread.scrollHeight;
    }

    function ensureThreadInner() {
        var welcome = thread.querySelector('.chat-welcome');
        if (welcome) welcome.remove();
        var inner = thread.querySelector('.chat-thread__inner');
        if (!inner) {
            thread.innerHTML = '<div class="chat-thread__inner"></div>';
            inner = thread.querySelector('.chat-thread__inner');
        }
        return inner;
    }

    function buildMessageHtml(role, content, options) {
        options = options || {};
        var metaHtml = options.meta
            ? '<div class="msg__meta' + (options.metaPending ? ' msg__meta--pending' : '') + '">' + escapeHtml(options.meta) + '</div>'
            : '';
        var isUser = role === 'user';
        if (isUser) {
            return (
                '<article class="msg msg--user">' +
                '<div class="msg__avatar" aria-hidden="true">' + USER_AVATAR + '</div>' +
                '<div class="msg__body">' +
                '<div class="msg__content">' + escapeHtml(content) + '</div>' +
                metaHtml +
                '</div></article>'
            );
        }
        return (
            '<article class="msg msg--bot">' +
            '<div class="msg__avatar" aria-hidden="true">' + BOT_AVATAR + '</div>' +
            '<div class="msg__body">' +
            '<div class="msg__card">' +
            '<div class="msg__content">' + escapeHtml(content) + '</div>' +
            '</div>' +
            metaHtml +
            '</div></article>'
        );
    }

    function appendMessage(role, content, options) {
        var inner = ensureThreadInner();
        inner.insertAdjacentHTML('beforeend', buildMessageHtml(role, content, options));
        scrollToBottom();
    }

    function bindExecToggle(msgEl) {
        var exec = msgEl.querySelector('.exec-result');
        var toggle = msgEl.querySelector('.exec-result__toggle');
        if (!exec || !toggle) return;
        toggle.addEventListener('click', function () {
            var expanded = exec.classList.toggle('is-open');
            toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        });
    }

    function bindStepToggle(stepEl) {
        var row = stepEl.querySelector('.exec-step__row');
        if (!row) return;
        row.addEventListener('click', function () {
            var expanded = stepEl.classList.toggle('is-expanded');
            row.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        });
    }

    function updateExecSummary() {
        if (!execResultEl || !execCountEl) return;
        var done = execResultEl.querySelectorAll('.exec-step--done, .exec-step--blocked').length;
        if (stepTotal === 0) {
            execCountEl.textContent = '';
            return;
        }
        if (done < stepTotal) {
            execCountEl.textContent = done + ' / ' + stepTotal + ' 步';
        } else {
            execCountEl.textContent = '共 ' + stepTotal + ' 步';
        }
    }

    function revealExecResult() {
        if (execResultEl) {
            execResultEl.classList.remove('exec-result--empty');
        }
    }

    function cacheWorkflowRefs(msgEl) {
        streamingMsgEl = msgEl;
        streamingContentEl = msgEl.querySelector('.stream-text');
        execResultEl = msgEl.querySelector('.exec-result');
        execStatusEl = msgEl.querySelector('.exec-result__status');
        execCountEl = msgEl.querySelector('.exec-result__count');
        workflowStepsEl = msgEl.querySelector('.exec-result__steps');
    }

    function ensureStreamingBotMessage() {
        if (streamingContentEl) return streamingContentEl;
        removeTypingIndicator();
        var inner = ensureThreadInner();
        inner.insertAdjacentHTML(
            'beforeend',
            '<article class="msg msg--bot msg--streaming" id="streaming-bot-msg">' +
            '<div class="msg__avatar" aria-hidden="true">' + BOT_AVATAR + '</div>' +
            '<div class="msg__body">' +
            '<div class="msg__card">' +
            '<div class="exec-result exec-result--empty">' +
            '<button type="button" class="exec-result__toggle" aria-expanded="false">' +
            '<span class="exec-result__status exec-result__status--running" aria-hidden="true"></span>' +
            '<span class="exec-result__headline">' +
            '<span class="exec-result__title">执行结果</span>' +
            '<span class="exec-result__count"></span>' +
            '</span>' +
            '<svg class="exec-result__chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>' +
            '</button>' +
            '<div class="exec-result__steps"></div>' +
            '</div>' +
            '<div class="msg__content msg__content--reply">' +
            '<span class="stream-text"></span><span class="stream-cursor" aria-hidden="true"></span>' +
            '</div></div>' +
            '<div class="msg__meta msg__meta--pending">生成中…</div>' +
            '</div></article>'
        );
        var msgEl = document.getElementById('streaming-bot-msg');
        cacheWorkflowRefs(msgEl);
        bindExecToggle(msgEl);
        scrollToBottom();
        return streamingContentEl;
    }

    function appendStreamToken(text) {
        var el = ensureStreamingBotMessage();
        el.textContent += text;
        scrollToBottom();
    }

    function markExecComplete() {
        if (execStatusEl) {
            execStatusEl.classList.remove('exec-result__status--running');
            execStatusEl.classList.add('exec-result__status--done');
        }
        if (execResultEl) execResultEl.classList.add('exec-result--done');
        updateExecSummary();
    }

    function finalizeStreamingMessage() {
        var msg = document.getElementById('streaming-bot-msg');
        if (msg) {
            msg.removeAttribute('id');
            msg.classList.remove('msg--streaming');
            var cursor = msg.querySelector('.stream-cursor');
            if (cursor) cursor.remove();
            var metaEl = msg.querySelector('.msg__meta');
            if (metaEl && turnStartTime) {
                metaEl.textContent = buildBotMetaText(turnStartTime);
                metaEl.classList.remove('msg__meta--pending');
            }
            markExecComplete();
        }
        streamingMsgEl = null;
        streamingContentEl = null;
        workflowStepsEl = null;
        execResultEl = null;
        execStatusEl = null;
        execCountEl = null;
        stepTotal = 0;
        workflowStepEls = {};
    }

    function showTypingIndicator() {
        removeTypingIndicator();
        var inner = ensureThreadInner();
        inner.insertAdjacentHTML(
            'beforeend',
            '<article class="msg msg--bot msg--typing" id="typing-indicator">' +
            '<div class="msg__avatar" aria-hidden="true">' + BOT_AVATAR + '</div>' +
            '<div class="msg__body">' +
            '<div class="msg__card msg__card--typing">' +
            '<div class="msg__content"><span class="typing-dots" aria-label="正在思考"><span></span><span></span><span></span></span></div>' +
            '</div></div></article>'
        );
        scrollToBottom();
    }

    function removeTypingIndicator() {
        var el = document.getElementById('typing-indicator');
        if (el) el.remove();
    }

    function setSubmitting(blocked) {
        isSubmitting = blocked;
        input.disabled = blocked;
        if (sendBtn) {
            sendBtn.disabled = blocked;
            sendBtn.classList.toggle('is-disabled', blocked);
        }
        input.classList.toggle('is-disabled', blocked);
    }

    function updateSessionId(sessionId) {
        if (!sessionId || !sessionInput) return;
        sessionInput.value = sessionId;
        if (sessionDisplay) sessionDisplay.textContent = sessionId;
    }

    function resetWorkflowForTurn() {
        workflowStepEls = {};
        stepTotal = 0;
        ensureStreamingBotMessage();
        if (workflowStepsEl) workflowStepsEl.innerHTML = '';
        if (execResultEl) {
            execResultEl.classList.remove('exec-result--done', 'is-open');
            execResultEl.classList.add('exec-result--empty');
            var toggle = execResultEl.querySelector('.exec-result__toggle');
            if (toggle) toggle.setAttribute('aria-expanded', 'false');
        }
        if (execStatusEl) {
            execStatusEl.classList.remove('exec-result__status--done');
            execStatusEl.classList.add('exec-result__status--running');
        }
        if (execCountEl) execCountEl.textContent = '';
    }

    function updateWorkflowProgress() {
        /* 截图风格不展示进度条，保留接口兼容 SSE progress 事件 */
    }

    function handleStepStart(payload) {
        if (!workflowStepsEl) ensureStreamingBotMessage();
        if (!workflowStepsEl) return;
        revealExecResult();
        var step = payload.step;
        stepTotal = Math.max(stepTotal, step);
        var node = payload.node || '节点';
        var meta = nodeMeta(node);
        var html =
            '<div class="exec-step exec-step--running" data-step="' + step + '">' +
            '<button type="button" class="exec-step__row" aria-expanded="false">' +
            '<span class="exec-step__icon exec-step__icon--' + meta.tone + '">' + stepIconSvg(meta.icon) + '</span>' +
            '<span class="exec-step__index">步骤 ' + step + '</span>' +
            '<span class="exec-step__name">' + escapeHtml(node) + '</span>' +
            '<span class="exec-step__mark exec-step__mark--running">' + ICON_SPINNER + '</span>' +
            '<svg class="exec-step__chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>' +
            '</button>' +
            '<div class="exec-step__detail">' +
            '<div class="exec-step__io"><span class="exec-step__io-label">节点输入</span><pre class="exec-step__input">' +
            escapeHtml(payload.input || '—') + '</pre></div>' +
            '<div class="exec-step__io"><span class="exec-step__io-label">节点返回</span><pre class="exec-step__output">执行中…</pre></div>' +
            '</div></div>';
        workflowStepsEl.insertAdjacentHTML('beforeend', html);
        var stepEl = workflowStepsEl.querySelector('[data-step="' + step + '"]');
        workflowStepEls[step] = stepEl;
        bindStepToggle(stepEl);
        updateExecSummary();
        scrollToBottom();
    }

    function handleStepEnd(payload) {
        var stepEl = workflowStepEls[payload.step];
        if (!stepEl) return;
        stepTotal = Math.max(stepTotal, payload.step || 0);
        var status = payload.status === 'blocked' ? 'blocked' : 'done';
        stepEl.classList.remove('exec-step--running');
        stepEl.classList.add('exec-step--' + status);
        var markEl = stepEl.querySelector('.exec-step__mark');
        if (markEl) {
            markEl.className = 'exec-step__mark exec-step__mark--' + status;
            markEl.innerHTML = status === 'blocked'
                ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>'
                : ICON_CHECK;
        }
        var outputEl = stepEl.querySelector('.exec-step__output');
        if (outputEl) outputEl.textContent = payload.output || '—';
        updateExecSummary();
    }

    function parseSseBlock(block) {
        var line = block.trim();
        if (!line.startsWith('data:')) return null;
        try {
            return JSON.parse(line.replace(/^data:\s*/, ''));
        } catch (err) {
            return null;
        }
    }

    function consumeSseStream(response) {
        var reader = response.body.getReader();
        var decoder = new TextDecoder();
        var buffer = '';

        function pump() {
            return reader.read().then(function (result) {
                if (result.done) return;
                buffer += decoder.decode(result.value, { stream: true });
                var parts = buffer.split('\n\n');
                buffer = parts.pop() || '';
                parts.forEach(function (part) {
                    var payload = parseSseBlock(part);
                    if (!payload) return;
                    if (payload.type === 'meta' && payload.session_id) {
                        updateSessionId(payload.session_id);
                    } else if (payload.type === 'progress') {
                        updateWorkflowProgress(payload);
                    } else if (payload.type === 'step_start') {
                        handleStepStart(payload);
                    } else if (payload.type === 'step_end') {
                        handleStepEnd(payload);
                    } else if (payload.type === 'token' && payload.text) {
                        appendStreamToken(payload.text);
                    } else if (payload.type === 'error') {
                        throw new Error(payload.message || '流式响应失败');
                    } else if (payload.type === 'done' && payload.session_id) {
                        updateSessionId(payload.session_id);
                    }
                });
                return pump();
            });
        }

        return pump();
    }

    function submitFallback(formData) {
        return fetch('/api/chat', { method: 'POST', body: formData, credentials: 'same-origin' })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error(response.status === 403 ? 'CSRF 校验失败，请刷新页面' : '请求失败 (' + response.status + ')');
                }
                return response.text();
            })
            .then(function (html) {
                var doc = new DOMParser().parseFromString(html, 'text/html');
                var sessionEl = doc.getElementById('sessionId');
                if (sessionEl && sessionEl.value) updateSessionId(sessionEl.value);
                var botContents = doc.querySelectorAll('.chat-thread__inner .msg--bot .msg__content');
                var lastBot = botContents[botContents.length - 1];
                removeTypingIndicator();
                ensureStreamingBotMessage();
                if (lastBot) {
                    streamingContentEl.textContent = lastBot.textContent.trim();
                } else {
                    streamingContentEl.textContent = '未获取到回复内容';
                }
                markExecComplete();
                finalizeStreamingMessage();
            });
    }

    function handleSubmit(e) {
        if (e) e.preventDefault();
        if (isSubmitting) return;

        var text = input.value.trim();
        if (!text) return;

        setSubmitting(true);
        if (sendBtn) {
            sendBtn.dataset.submitOriginalText = sendBtn.getAttribute('aria-label') || '发送';
            sendBtn.setAttribute('aria-label', '发送中…');
        }
        var sentAt = new Date();
        turnStartTime = sentAt.getTime();
        appendMessage('user', text, { meta: formatTime(sentAt) });

        var formData = new FormData(form);
        formData.set('chat', text);

        input.value = '';
        autoResize();
        showTypingIndicator();
        streamingMsgEl = null;
        streamingContentEl = null;
        workflowStepEls = {};

        fetch('/api/chat/stream', { method: 'POST', body: formData, credentials: 'same-origin' })
            .then(function (response) {
                if (response.status === 404) {
                    return submitFallback(formData);
                }
                if (!response.ok) {
                    throw new Error(response.status === 403 ? 'CSRF 校验失败，请刷新页面' : '请求失败 (' + response.status + ')');
                }
                removeTypingIndicator();
                resetWorkflowForTurn();
                return consumeSseStream(response);
            })
            .then(function () {
                removeTypingIndicator();
                finalizeStreamingMessage();
            })
            .catch(function (err) {
                removeTypingIndicator();
                finalizeStreamingMessage();
                appendMessage('bot', '⚠ ' + (err.message || '发送失败，请稍后重试'), {
                    meta: turnStartTime ? buildBotMetaText(turnStartTime) : formatTime(new Date()),
                });
            })
            .finally(function () {
                setSubmitting(false);
                if (sendBtn) {
                    sendBtn.setAttribute('aria-label', sendBtn.dataset.submitOriginalText || '发送');
                }
                input.focus();
            });
    }

    form.addEventListener('submit', handleSubmit);

    input.addEventListener('input', autoResize);
    autoResize();

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    });

    document.querySelectorAll('[data-prompt]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (isSubmitting) return;
            input.value = btn.getAttribute('data-prompt') || '';
            autoResize();
            input.focus();
        });
    });

    if (copyBtn && sessionInput) {
        copyBtn.addEventListener('click', function () {
            var val = sessionInput.value.trim();
            if (!val) return;
            navigator.clipboard.writeText(val).then(function () {
                copyBtn.title = '已复制';
                setTimeout(function () { copyBtn.title = '复制 Session ID'; }, 1500);
            });
        });
    }

    if (sessionInput && sessionDisplay) {
        sessionInput.addEventListener('input', function () {
            sessionDisplay.textContent = sessionInput.value.trim() || '等待开始';
        });
    }

    scrollToBottom();
    input.focus();
})();
