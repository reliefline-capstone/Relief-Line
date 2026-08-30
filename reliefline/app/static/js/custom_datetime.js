// Custom calendar + time pickers that replace the browser-native
// <input type="date"> / <input type="time"> popups. Same rationale and
// pattern as custom_select.js: the native picker's calendar / spinner is
// drawn by the OS, unstyleable, and looks nothing like the rest of the UI.
//
// The original input is kept in the DOM (visually hidden, tabindex -1) so
// name/value submission, `required`, `min`/`max` and every existing
// `change` listener keep working untouched — this only adds a visual layer
// and writes back a valid value string ("YYYY-MM-DD" / "HH:MM").
//
// Opt out on a specific field with `data-no-custom-picker`.
(function () {
    'use strict';

    var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    var MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var WEEKDAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

    function svg(inner) {
        return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + inner + '</svg>';
    }
    var CAL_ICON = svg('<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>' +
        '<line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>');
    var CLOCK_ICON = svg('<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/>');
    var CHEV_L = svg('<polyline points="15 18 9 12 15 6"/>');
    var CHEV_R = svg('<polyline points="9 18 15 12 9 6"/>');

    function pad(n) { return n < 10 ? '0' + n : '' + n; }

    function parseISO(s) {
        if (!s) return null;
        var p = String(s).split('-');
        if (p.length !== 3) return null;
        var d = new Date(+p[0], +p[1] - 1, +p[2]);
        return isNaN(d.getTime()) ? null : d;
    }
    function toISO(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
    function startOfDay(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
    function sameDay(a, b) {
        return a && b && a.getFullYear() === b.getFullYear() &&
            a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
    }

    function closeAll(except) {
        document.querySelectorAll('.cdt-wrap.is-open').forEach(function (w) {
            if (w !== except) close(w);
        });
    }

    // The popup is position:fixed and (while open) parented to <body> — the
    // page's .dashboard-main keeps a retained transform from its entrance
    // animation, which would otherwise make it the containing block for
    // position:fixed and throw the coordinates off. Moving to <body> also
    // means no scrollable modal / table wrapper can clip the calendar.
    var openWrap = null;
    function reposition() {
        if (!openWrap) return;
        var trig = openWrap._trig, pop = openWrap._pop;
        var r = trig.getBoundingClientRect();
        var ph = pop.offsetHeight, pw = pop.offsetWidth;
        var below = window.innerHeight - r.bottom;
        var top = (below >= ph + 8 || r.top < ph + 8) ? r.bottom + 4 : r.top - ph - 4;
        var left = Math.max(8, Math.min(r.left, window.innerWidth - pw - 8));
        pop.style.top = Math.max(8, top) + 'px';
        pop.style.left = left + 'px';
    }
    window.addEventListener('scroll', reposition, true);
    window.addEventListener('resize', reposition);

    function close(wrap) {
        wrap.classList.remove('is-open');
        var pop = wrap._pop, trig = wrap._trig;
        pop.hidden = true;
        pop.style.top = pop.style.left = '';
        if (pop.parentNode !== wrap) wrap.appendChild(pop);
        trig.setAttribute('aria-expanded', 'false');
        if (openWrap === wrap) openWrap = null;
    }
    function open(wrap) {
        if (wrap.classList.contains('is-disabled')) return;
        closeAll(wrap);
        wrap.classList.add('is-open');
        openWrap = wrap;
        var pop = wrap._pop, trig = wrap._trig;
        if (pop.parentNode !== document.body) document.body.appendChild(pop);
        pop.hidden = false;
        trig.setAttribute('aria-expanded', 'true');
        if (wrap._render) wrap._render();
        reposition();
    }

    function commit(input, value) {
        if (input.value === value) return;
        input.value = value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function baseWrap(input, kind) {
        var wrap = document.createElement('div');
        wrap.className = 'cdt-wrap cdt-' + kind + (input.disabled ? ' is-disabled' : '');
        input.parentNode.insertBefore(wrap, input);
        wrap.appendChild(input);
        input.classList.add('cdt-native');
        input.tabIndex = -1;

        var trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'cdt-trigger';
        trigger.setAttribute('aria-haspopup', 'dialog');
        trigger.setAttribute('aria-expanded', 'false');
        if (input.disabled) trigger.disabled = true;
        wrap.appendChild(trigger);

        var popup = document.createElement('div');
        popup.className = 'cdt-popup';
        popup.hidden = true;
        wrap.appendChild(popup);

        wrap._trig = trigger;
        wrap._pop = popup;

        trigger.addEventListener('click', function () {
            if (wrap.classList.contains('is-open')) close(wrap);
            else open(wrap);
        });
        trigger.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && wrap.classList.contains('is-open')) { e.preventDefault(); close(wrap); }
            else if ((e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') && !wrap.classList.contains('is-open')) {
                e.preventDefault(); open(wrap);
            }
        });

        if (input.id) {
            var lab = document.querySelector('label[for="' + input.id + '"]');
            if (lab) lab.addEventListener('click', function (e) {
                e.preventDefault(); trigger.focus(); open(wrap);
            });
        }

        input.addEventListener('invalid', function () { trigger.classList.add('cdt-invalid'); });
        input.addEventListener('change', function () { trigger.classList.remove('cdt-invalid'); });

        return { wrap: wrap, trigger: trigger, popup: popup };
    }

    // ---------------------------------------------------------------- DATE
    function enhanceDate(input) {
        var b = baseWrap(input, 'date');
        var minD = parseISO(input.getAttribute('min'));
        var maxD = parseISO(input.getAttribute('max'));
        var view = null;

        function selected() { return parseISO(input.value); }
        function inRange(d) {
            var s = startOfDay(d);
            if (minD && s < startOfDay(minD)) return false;
            if (maxD && s > startOfDay(maxD)) return false;
            return true;
        }
        function syncLabel() {
            var d = selected();
            b.trigger.innerHTML = '<span class="cdt-value' + (d ? '' : ' cdt-placeholder') + '">' +
                (d ? (MONTHS_SHORT[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear()) : 'Select date') +
                '</span>' + CAL_ICON;
        }

        function render() {
            var sel = selected();
            var today = startOfDay(new Date());
            if (!view) {
                var anchor = sel || today;
                view = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
            }
            var y = view.getFullYear(), m = view.getMonth();
            var gridStart = new Date(y, m, 1 - new Date(y, m, 1).getDay());

            var html = '<div class="cdt-cal-head">' +
                '<button type="button" class="cdt-nav" data-nav="-1" aria-label="Previous month">' + CHEV_L + '</button>' +
                '<span class="cdt-cal-title">' + MONTHS[m] + ' ' + y + '</span>' +
                '<button type="button" class="cdt-nav" data-nav="1" aria-label="Next month">' + CHEV_R + '</button>' +
                '</div><div class="cdt-cal-grid">';
            for (var i = 0; i < 7; i++) html += '<span class="cdt-dow">' + WEEKDAYS[i] + '</span>';
            for (var k = 0; k < 42; k++) {
                var d = new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + k);
                var cls = 'cdt-day';
                if (d.getMonth() !== m) cls += ' is-outside';
                if (sameDay(d, today)) cls += ' is-today';
                if (sel && sameDay(d, sel)) cls += ' is-selected';
                var off = !inRange(d);
                if (off) cls += ' is-disabled';
                html += '<button type="button" class="' + cls + '" data-date="' + toISO(d) + '"' +
                    (off ? ' disabled' : '') + '>' + d.getDate() + '</button>';
            }
            html += '</div><div class="cdt-cal-foot">' +
                '<button type="button" class="cdt-foot-btn" data-action="clear">Clear</button>' +
                '<button type="button" class="cdt-foot-btn cdt-foot-primary" data-action="today">Today</button>' +
                '</div>';
            b.popup.innerHTML = html;
        }
        b.wrap._render = render;

        b.popup.addEventListener('click', function (e) {
            var nav = e.target.closest('[data-nav]');
            if (nav) { view.setMonth(view.getMonth() + (+nav.dataset.nav)); render(); return; }

            var day = e.target.closest('[data-date]');
            if (day && !day.disabled) {
                var iso = day.dataset.date;
                commit(input, iso);
                view = parseISO(iso); view.setDate(1);
                syncLabel();
                close(b.wrap);
                b.trigger.focus();
                return;
            }

            var act = e.target.closest('[data-action]');
            if (!act) return;
            if (act.dataset.action === 'clear') {
                commit(input, ''); view = null; syncLabel(); render();
            } else {
                var t = new Date();
                if (inRange(t)) {
                    commit(input, toISO(t));
                    view = new Date(t.getFullYear(), t.getMonth(), 1);
                    syncLabel(); close(b.wrap); b.trigger.focus();
                }
            }
        });

        input.addEventListener('change', function () { view = null; syncLabel(); });
        syncLabel();
    }

    // ---------------------------------------------------------------- TIME
    function enhanceTime(input) {
        var b = baseWrap(input, 'time');
        var state = { h: null, m: null, p: null }; // h 1-12, m 0-59, p AM/PM

        function fromValue() {
            var v = input.value || '';
            if (!/^\d{2}:\d{2}/.test(v)) { state = { h: null, m: null, p: null }; return; }
            var H = +v.slice(0, 2), M = +v.slice(3, 5);
            state.p = H < 12 ? 'AM' : 'PM';
            state.h = H % 12 || 12;
            state.m = M;
        }
        function writeIfReady() {
            if (state.h == null) return;
            var mm = state.m == null ? 0 : state.m;
            var p = state.p || 'AM';
            var H = p === 'PM' ? (state.h % 12) + 12 : (state.h % 12);
            commit(input, pad(H) + ':' + pad(mm));
        }
        function syncLabel() {
            var has = state.h != null;
            var txt = has ? (state.h + ':' + pad(state.m == null ? 0 : state.m) + ' ' + (state.p || 'AM')) : 'Select time';
            b.trigger.innerHTML = '<span class="cdt-value' + (has ? '' : ' cdt-placeholder') + '">' +
                txt + '</span>' + CLOCK_ICON;
        }

        function column(name, items, current, fmt) {
            var h = '<ul class="cdt-col" data-col="' + name + '">';
            items.forEach(function (it) {
                var on = String(it) === String(current);
                h += '<li class="cdt-col-item' + (on ? ' is-selected' : '') + '" data-val="' + it + '">' +
                    (fmt ? fmt(it) : it) + '</li>';
            });
            return h + '</ul>';
        }
        function render() {
            var hrs = [], mins = [], i;
            for (i = 1; i <= 12; i++) hrs.push(i);
            for (i = 0; i < 60; i++) mins.push(i);
            b.popup.innerHTML = '<div class="cdt-time-cols">' +
                column('h', hrs, state.h) +
                column('m', mins, state.m, pad) +
                column('p', ['AM', 'PM'], state.p) +
                '</div>';
            b.popup.querySelectorAll('.cdt-col-item.is-selected').forEach(function (el) {
                el.scrollIntoView({ block: 'center' });
            });
        }
        b.wrap._render = render;

        b.popup.addEventListener('click', function (e) {
            var item = e.target.closest('.cdt-col-item');
            if (!item) return;
            var col = item.parentNode.dataset.col;
            if (col === 'h') state.h = +item.dataset.val;
            else if (col === 'm') state.m = +item.dataset.val;
            else state.p = item.dataset.val;
            item.parentNode.querySelectorAll('.cdt-col-item').forEach(function (o) {
                o.classList.toggle('is-selected', o === item);
            });
            writeIfReady();
            syncLabel();
        });

        input.addEventListener('change', function () { fromValue(); syncLabel(); });
        fromValue();
        syncLabel();
    }

    function enhance(input) {
        if (input.closest('.cdt-wrap')) return;
        if ('noCustomPicker' in input.dataset) return;
        if (input.type === 'date') enhanceDate(input);
        else if (input.type === 'time') enhanceTime(input);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('input[type="date"], input[type="time"]').forEach(enhance);
    });
    document.addEventListener('click', function (e) {
        if (e.target.closest('.cdt-wrap') || e.target.closest('.cdt-popup')) return;
        document.querySelectorAll('.cdt-wrap.is-open').forEach(close);
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') document.querySelectorAll('.cdt-wrap.is-open').forEach(close);
    });
})();
