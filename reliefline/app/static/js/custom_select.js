// Custom dropdown menus used across the app.
// They replace the browser's built-in dropdowns so they look the same everywhere and match dark mode.
(function () {
    'use strict';

    var CHEVRON_SVG =
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>';
    var CHECK_SVG =
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

    // Places the dropdown list below the field, or above it if there isn't room,
    // so it always fits on the screen.
    function positionList(wrap, list, trigger) {
        if (trigger.closest('.rd-modal')) return;
        var rect = trigger.getBoundingClientRect();
        var margin = 8;
        var maxListHeight = 260;
        var minListHeight = 80;
        var spaceBelow = window.innerHeight - rect.bottom - margin;
        var spaceAbove = rect.top - margin;
        var openUpward = spaceBelow < minListHeight && spaceAbove > spaceBelow;
        list.classList.toggle('csel-list-up', openUpward);
        list.style.maxHeight = Math.max(minListHeight, Math.min(maxListHeight, openUpward ? spaceAbove : spaceBelow)) + 'px';
    }

    // Closes a dropdown.
    function closeDropdown(wrap) {
        wrap.classList.remove('is-open');
        var list = wrap.cselList;
        var trigger = wrap.querySelector('.csel-trigger');
        if (list) {
            list.hidden = true;
            list.classList.remove('csel-list-up');
            list.style.maxHeight = '';
        }
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
    }

    // Closes every open dropdown except the given one.
    function closeAllExcept(exceptWrap) {
        document.querySelectorAll('.csel-wrap.is-open').forEach(function (w) {
            if (w !== exceptWrap) closeDropdown(w);
        });
    }

    // Highlights an option in the list (for keyboard use) and scrolls it into view.
    function setActive(list, option) {
        list.querySelectorAll('.csel-option').forEach(function (o) { o.classList.remove('is-active'); });
        if (option) {
            option.classList.add('is-active');
            if (option.scrollIntoView) option.scrollIntoView({ block: 'nearest' });
        }
    }

    // Opens a dropdown (and closes any other open dropdown).
    function openDropdown(wrap) {
        if (wrap.classList.contains('is-disabled')) return;
        closeAllExcept(wrap);
        wrap.classList.add('is-open');
        var list = wrap.cselList;
        var trigger = wrap.querySelector('.csel-trigger');
        if (list) {
            list.hidden = false;
            positionList(wrap, list, trigger);
        }
        if (trigger) trigger.setAttribute('aria-expanded', 'true');
        var active = list.querySelector('.csel-option.is-selected') || list.querySelector('.csel-option');
        setActive(list, active);
    }

    // Shows the selected option's text on the dropdown button.
    function refreshTriggerLabel(wrap) {
        var select = wrap.querySelector('.csel-native');
        var valueEl = wrap.querySelector('.csel-trigger .csel-value');
        var list = wrap.querySelector('.csel-list');
        if (!select || !valueEl) return;
        var opt = select.options[select.selectedIndex];
        valueEl.textContent = opt ? opt.textContent : '';
        var isDefault = !!opt && (opt.value === '' || (!!wrap.closest('.fp') && select.selectedIndex === 0));
        valueEl.classList.toggle('csel-placeholder', isDefault);
        if (list) {
            list.querySelectorAll('.csel-option').forEach(function (o) {
                o.classList.toggle('is-selected', o.dataset.value === select.value);
            });
        }
    }

    // Selects an option, updates the real form field, and tells the page it changed.
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

    // Turns a normal dropdown into the custom dropdown
    // (supports mouse, keyboard and touch; skips dropdowns marked to keep the default).
    function enhance(select) {
        if (select.closest('.csel-wrap')) return;
        if ('noCustomSelect' in select.dataset) return;
        if (select.hidden) return;

        var wrap = document.createElement('div');
        wrap.className = 'csel-wrap' + (select.disabled ? ' is-disabled' : '');

        select.parentNode.insertBefore(wrap, select);
        wrap.appendChild(select);
        select.classList.add('csel-native');
        select.tabIndex = -1;

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
        wrap.cselList = list;

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

        select.addEventListener('change', function () { refreshTriggerLabel(wrap); });

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

    document.querySelectorAll('.rd-modal-overlay').forEach(function (overlay) {
        new MutationObserver(function () {
            if (overlay.hidden) {
                overlay.querySelectorAll('.csel-wrap.is-open').forEach(closeDropdown);
            }
        }).observe(overlay, { attributes: true, attributeFilter: ['hidden'] });
    });
})();
