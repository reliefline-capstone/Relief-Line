// Replaces every plain <select> on the page with a custom-styled dropdown.
// Loaded globally (base.html) so every page gets this without needing
// template-by-template changes — see custom_select.css for why (a native
// select's open listbox can't be restyled with CSS at all).
//
// The original <select> is kept in the DOM (visually hidden, not removed)
// so name/value form submission, `required` validation, and any existing
// `select.addEventListener('change', ...)` wiring elsewhere in the
// codebase (admin.js's role-field toggle, relief_request_detail.js's
// transfer-calc preview, weather_widget.js's Declare Event modal, etc.)
// keep working completely unchanged — this only adds a visual layer on
// top and forwards real `change`/`input` events onto the original select.
(function () {
    'use strict';

    var CHEVRON_SVG =
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>';
    var CHECK_SVG =
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

    function closeDropdown(wrap) {
        wrap.classList.remove('is-open');
        var list = wrap.querySelector('.csel-list');
        var trigger = wrap.querySelector('.csel-trigger');
        if (list) list.hidden = true;
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
    }

    function closeAllExcept(exceptWrap) {
        document.querySelectorAll('.csel-wrap.is-open').forEach(function (w) {
            if (w !== exceptWrap) closeDropdown(w);
        });
    }

    function setActive(list, option) {
        list.querySelectorAll('.csel-option').forEach(function (o) { o.classList.remove('is-active'); });
        if (option) {
            option.classList.add('is-active');
            if (option.scrollIntoView) option.scrollIntoView({ block: 'nearest' });
        }
    }

    function openDropdown(wrap) {
        if (wrap.classList.contains('is-disabled')) return;
        closeAllExcept(wrap);
        wrap.classList.add('is-open');
        var list = wrap.querySelector('.csel-list');
        var trigger = wrap.querySelector('.csel-trigger');
        if (list) list.hidden = false;
        if (trigger) trigger.setAttribute('aria-expanded', 'true');
        var active = list.querySelector('.csel-option.is-selected') || list.querySelector('.csel-option');
        setActive(list, active);
    }

    function refreshTriggerLabel(wrap) {
        var select = wrap.querySelector('.csel-native');
        var valueEl = wrap.querySelector('.csel-trigger .csel-value');
        var list = wrap.querySelector('.csel-list');
        if (!select || !valueEl) return;
        var opt = select.options[select.selectedIndex];
        valueEl.textContent = opt ? opt.textContent : '';
        valueEl.classList.toggle('csel-placeholder', !!(opt && opt.value === ''));
        if (list) {
            list.querySelectorAll('.csel-option').forEach(function (o) {
                o.classList.toggle('is-selected', o.dataset.value === select.value);
            });
        }
    }

    function selectOption(wrap, optionEl) {
        var select = wrap.querySelector('.csel-native');
        if (!select || optionEl.getAttribute('aria-disabled') === 'true') return;
        if (select.value !== optionEl.dataset.value) {
            select.value = optionEl.dataset.value;
            refreshTriggerLabel(wrap);
            select.dispatchEvent(new Event('input', { bubbles: true }));
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }
        closeDropdown(wrap);
        var trigger = wrap.querySelector('.csel-trigger');
        if (trigger) trigger.focus();
    }

    function enhance(select) {
        if (select.closest('.csel-wrap')) return; // already enhanced
        if ('noCustomSelect' in select.dataset) return; // explicit opt-out

        var wrap = document.createElement('div');
        wrap.className = 'csel-wrap' + (select.disabled ? ' is-disabled' : '');

        select.parentNode.insertBefore(wrap, select);
        wrap.appendChild(select);
        select.classList.add('csel-native');
        select.tabIndex = -1; // keyboard interaction goes through the trigger button

        var trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'csel-trigger';
        trigger.setAttribute('aria-haspopup', 'listbox');
        trigger.setAttribute('aria-expanded', 'false');
        if (select.disabled) trigger.disabled = true;
        trigger.innerHTML = '<span class="csel-value"></span>' + CHEVRON_SVG;
        wrap.appendChild(trigger);

        var list = document.createElement('ul');
        list.className = 'csel-list';
        list.setAttribute('role', 'listbox');
        list.hidden = true;

        Array.prototype.forEach.call(select.options, function (opt) {
            var li = document.createElement('li');
            li.className = 'csel-option' + (opt.value === '' ? ' csel-placeholder' : '');
            li.setAttribute('role', 'option');
            li.dataset.value = opt.value;
            if (opt.disabled) li.setAttribute('aria-disabled', 'true');
            li.innerHTML = '<span>' + opt.textContent + '</span>' + CHECK_SVG;
            li.addEventListener('click', function () { selectOption(wrap, li); });
            list.appendChild(li);
        });
        wrap.appendChild(list);

        refreshTriggerLabel(wrap);

        trigger.addEventListener('click', function () {
            if (wrap.classList.contains('is-open')) closeDropdown(wrap);
            else openDropdown(wrap);
        });

        trigger.addEventListener('keydown', function (e) {
            var options = Array.prototype.slice.call(list.querySelectorAll('.csel-option'));
            var current = list.querySelector('.csel-option.is-active');
            var idx = current ? options.indexOf(current) : -1;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (!wrap.classList.contains('is-open')) { openDropdown(wrap); return; }
                setActive(list, options[Math.min(idx + 1, options.length - 1)]);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (!wrap.classList.contains('is-open')) { openDropdown(wrap); return; }
                setActive(list, options[Math.max(idx - 1, 0)]);
            } else if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                if (!wrap.classList.contains('is-open')) { openDropdown(wrap); return; }
                if (current) selectOption(wrap, current);
            } else if (e.key === 'Escape') {
                if (wrap.classList.contains('is-open')) { e.preventDefault(); closeDropdown(wrap); }
            } else if (e.key === 'Tab') {
                closeDropdown(wrap);
            }
        });

        // Keeps the widget in sync if something else on the page sets
        // select.value directly and fires 'change' itself.
        select.addEventListener('change', function () { refreshTriggerLabel(wrap); });

        // Native constraint validation (`required`) still fires on the
        // hidden select — surface it visually on the trigger instead of
        // leaving no visible cue near the widget the user actually sees.
        select.addEventListener('invalid', function () {
            trigger.classList.add('csel-invalid');
            trigger.focus();
        });
        select.addEventListener('change', function () { trigger.classList.remove('csel-invalid'); });
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('select').forEach(enhance);
    });

    document.addEventListener('click', function (e) {
        if (e.target.closest('.csel-wrap')) return;
        document.querySelectorAll('.csel-wrap.is-open').forEach(closeDropdown);
    });
})();
