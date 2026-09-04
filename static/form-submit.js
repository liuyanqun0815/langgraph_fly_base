(function () {
    'use strict';

    var LOADING_TEXT = '处理中…';

    function getSubmitButtons(form) {
        return Array.prototype.slice.call(form.querySelectorAll('button[type="submit"], input[type="submit"]'));
    }

    function lockForm(form) {
        if (form.dataset.submitLocked === '1') {
            return false;
        }
        form.dataset.submitLocked = '1';
        getSubmitButtons(form).forEach(function (btn) {
            btn.disabled = true;
            btn.classList.add('is-disabled');
            if (btn.tagName === 'BUTTON') {
                if (!btn.dataset.submitOriginalText) {
                    btn.dataset.submitOriginalText = btn.textContent;
                }
                btn.textContent = btn.dataset.loadingText || LOADING_TEXT;
            } else if (btn.tagName === 'INPUT') {
                if (!btn.dataset.submitOriginalValue) {
                    btn.dataset.submitOriginalValue = btn.value;
                }
                btn.value = btn.dataset.loadingText || LOADING_TEXT;
            }
        });
        return true;
    }

    function unlockForm(form) {
        delete form.dataset.submitLocked;
        getSubmitButtons(form).forEach(function (btn) {
            btn.disabled = false;
            btn.classList.remove('is-disabled');
            if (btn.tagName === 'BUTTON' && btn.dataset.submitOriginalText) {
                btn.textContent = btn.dataset.submitOriginalText;
            } else if (btn.tagName === 'INPUT' && btn.dataset.submitOriginalValue) {
                btn.value = btn.dataset.submitOriginalValue;
            }
        });
    }

    function handleAjaxForm(form, event) {
        event.preventDefault();
        if (!lockForm(form)) {
            return;
        }

        var action = form.getAttribute('action') || window.location.pathname;
        var method = (form.getAttribute('method') || 'POST').toUpperCase();
        var formData = new FormData(form);

        fetch(action, { method: method, body: formData, credentials: 'same-origin' })
            .then(function (response) {
                return response.text().then(function (text) {
                    if (!response.ok) {
                        throw new Error(text || '请求失败 (' + response.status + ')');
                    }
                    return text;
                });
            })
            .then(function (data) {
                if (form.dataset.onSuccess === 'alert') {
                    alert(data);
                }
            })
            .catch(function (err) {
                alert(err.message || '请求失败，请稍后重试');
            })
            .finally(function () {
                unlockForm(form);
            });
    }

    document.addEventListener(
        'submit',
        function (event) {
            var form = event.target;
            if (!(form instanceof HTMLFormElement)) {
                return;
            }
            if (form.dataset.noSubmitLock === 'true') {
                return;
            }

            if (form.dataset.ajaxSubmit === 'true') {
                if (form.dataset.submitLocked === '1') {
                    event.preventDefault();
                    return;
                }
                handleAjaxForm(form, event);
                return;
            }

            if (form.dataset.submitLocked === '1') {
                event.preventDefault();
                return;
            }
            lockForm(form);
        },
        true
    );

    window.FormSubmitLock = { lock: lockForm, unlock: unlockForm };
})();
