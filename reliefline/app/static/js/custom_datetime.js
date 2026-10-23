// Custom date and time pickers used across the app.
// They replace the browser's built-in pickers so they look the same on every computer and phone.
(function () {
    'use strict';

    var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    var MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var WEEKDAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

    // Builds a small icon (calendar, clock or arrow).
    function svg(inner) {
        return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + inner + '</svg>';
    }
    var CAL_ICON = svg('<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>' +
        '<line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>');
    var CLOCK_ICON = svg('<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/>');
    var CHEV_L = svg('<polyline points="15 18 9 12 15 6"/>');
    var CHEV_R = svg('<polyline points="9 18 15 12 9 6"/>');

    // Adds a leading zero to a number (e.g. 7 -> 07).
    function pad(n) { return n < 10 ? '0' + n : '' + n; }

    // Reads a date written like 2026-10-23.
    function parseISO(s) {
        if (!s) return null;
        var p = String(s).split('-');
        if (p.length !== 3) return null;
        var d = new Date(+p[0], +p[1] - 1, +p[2]);
        return isNaN(d.getTime()) ? null : d;
    }
    // Writes a date like 2026-10-23 (the format forms send to the server).
    function toISO(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
    // The same date at midnight (so only the day is compared, not the time).
    function startOfDay(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
    // True if two dates are the same day.
    function sameDay(a, b) {
        return a && b && a.getFullYear() === b.getFullYear() &&
            a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
    }

    // Closes every open picker except the given one.
    function closeAll(except) {
        document.querySelectorAll('.cdt-wrap.is-open').forEach(function (w) {
            if (w !== except) close(w);
        });
    }

    var openWrap = null;
    // Keeps the open picker right next to its field when the page scrolls or resizes.
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

    // Closes a picker.
    function close(wrap) {
        wrap.classList.remove('is-open');
        var pop = wrap._pop, trig = wrap._trig;
        pop.hidden = true;
        pop.style.top = pop.style.left = '';
        if (pop.parentNode !== wrap) wrap.appendChild(pop);
        trig.setAttribute('aria-expanded', 'false');
        if (openWrap === wrap) openWrap = null;
    }
    // Opens a picker (and closes any other open picker).
    function open(wrap) {
        if (wrap.classList.contains('is-disabled')) return;
        closeAll(wrap);
        wrap.classList.add('is-open');
        openWrap = wrap;
        var pop = wrap._pop, trig = wrap._trig;
        if (pop.parentNode !== document.body) document.body.appendChild(pop);
        pop.hidden = false;
        trig.setAttribute('aria-expanded', 'true');
        if (wrap._onOpen) wrap._onOpen();
        if (wrap._render) wrap._render();
        reposition();
    }

    // Saves the picked value into the real form field, so the form sends it.
    function commit(input, value) {
        if (input.value === value) return;
        input.value = value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // Builds the shared picker frame around a field: the button you click and the pop-up.
    function baseWrap(input, kind, opts) {
        opts = opts || {};
        var wrap = document.createElement('div');
        wrap.className = 'cdt-wrap cdt-' + kind + (input.disabled ? ' is-disabled' : '');
        input.parentNode.insertBefore(wrap, input);
        wrap.appendChild(input);
        input.classList.add('cdt-native');
        input.tabIndex = -1;

        var trigger, icon = null;
        if (opts.typeable) {
            trigger = document.createElement('input');
            trigger.type = 'text';
            trigger.className = 'cdt-trigger cdt-trigger-typeable';
            trigger.autocomplete = 'off';
            trigger.spellcheck = false;
            trigger.placeholder = opts.placeholder || '';
            if (input.disabled) trigger.disabled = true;
            wrap.appendChild(trigger);

            icon = document.createElement('span');
            icon.className = 'cdt-trigger-icon';
            icon.innerHTML = opts.icon || '';
            wrap.appendChild(icon);
        } else {
            trigger = document.createElement('button');
            trigger.type = 'button';
            trigger.className = 'cdt-trigger';
            trigger.setAttribute('aria-haspopup', 'dialog');
            trigger.setAttribute('aria-expanded', 'false');
            if (input.disabled) trigger.disabled = true;
            wrap.appendChild(trigger);
        }

        var popup = document.createElement('div');
        popup.className = 'cdt-popup';
        popup.hidden = true;
        wrap.appendChild(popup);

        wrap._trig = trigger;
        wrap._pop = popup;

        if (opts.typeable) {
            trigger.addEventListener('focus', function () { open(wrap); });
            trigger.addEventListener('blur', function () {
                if (opts.onCommitText) opts.onCommitText();
                close(wrap);
            });
            trigger.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && wrap.classList.contains('is-open')) { e.preventDefault(); trigger.blur(); }
                else if (e.key === 'Enter') { e.preventDefault(); if (opts.onCommitText) opts.onCommitText(); }
            });
            popup.addEventListener('mousedown', function (e) { e.preventDefault(); });
        } else {
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
        }

        if (input.id) {
            var lab = document.querySelector('label[for="' + input.id + '"]');
            if (lab) lab.addEventListener('click', function (e) {
                e.preventDefault(); trigger.focus(); if (!opts.typeable) open(wrap);
            });
        }

        input.addEventListener('invalid', function () { trigger.classList.add('cdt-invalid'); });
        input.addEventListener('change', function () { trigger.classList.remove('cdt-invalid'); });

        return { wrap: wrap, trigger: trigger, popup: popup, icon: icon };
    }

    // Turns a date field into the custom calendar picker
    // (day, month and year views; respects the earliest/latest allowed dates).
    function enhanceDate(input) {
        var b = baseWrap(input, 'date');
        var minD = parseISO(input.getAttribute('min'));
        var maxD = parseISO(input.getAttribute('max'));
        var yearFirst = input.hasAttribute('data-year-first');
        var view = null;
        var mode = null;
        var yearPage = null;

        // The currently picked date.
        function selected() { return parseISO(input.value); }
        // True if a day is allowed (between the earliest and latest allowed dates).
        function inRange(d) {
            var s = startOfDay(d);
            if (minD && s < startOfDay(minD)) return false;
            if (maxD && s > startOfDay(maxD)) return false;
            return true;
        }
        // True if a month is allowed.
        function monthInRange(y, m) {
            if (minD && new Date(y, m + 1, 0) < startOfDay(minD)) return false;
            if (maxD && new Date(y, m, 1) > startOfDay(maxD)) return false;
            return true;
        }
        // True if a year is allowed.
        function yearInRange(y) {
            if (minD && y < minD.getFullYear()) return false;
            if (maxD && y > maxD.getFullYear()) return false;
            return true;
        }
        // Shows the picked date on the picker button (e.g. 'Oct 23, 2026').
        function syncLabel() {
            var d = selected();
            b.trigger.innerHTML = '<span class="cdt-value' + (d ? '' : ' cdt-placeholder') + '">' +
                (d ? (MONTHS_SHORT[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear()) : 'Select date') +
                '</span>' + CAL_ICON;
        }

        // Builds the top of the calendar: the title and the previous/next arrows.
        function head(title, prevLabel, nextLabel, upLabel) {
            return '<div class="cdt-cal-head">' +
                '<button type="button" class="cdt-nav" data-nav="-1" aria-label="' + prevLabel + '">' + CHEV_L + '</button>' +
                (upLabel
                    ? '<button type="button" class="cdt-cal-title cdt-cal-title-btn" data-up aria-label="' + upLabel + '">' + title + '</button>'
                    : '<span class="cdt-cal-title">' + title + '</span>') +
                '<button type="button" class="cdt-nav" data-nav="1" aria-label="' + nextLabel + '">' + CHEV_R + '</button>' +
                '</div>';
        }
        // Builds the bottom of the calendar: the 'Clear' and 'Today' buttons.
        function foot() {
            return '<div class="cdt-cal-foot">' +
                '<button type="button" class="cdt-foot-btn" data-action="clear">Clear</button>' +
                '<button type="button" class="cdt-foot-btn cdt-foot-primary" data-action="today">Today</button>' +
                '</div>';
        }

        // Draws the calendar in its current view (days, months or years).
        function render() {
            var sel = selected();
            var today = startOfDay(new Date());
            if (!view) {
                var anchor = sel || today;
                view = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
            }
            if (!mode) mode = (yearFirst && !sel) ? 'years' : 'days';
            var y = view.getFullYear(), m = view.getMonth();
            var html = '';

            if (mode === 'years') {
                if (yearPage === null) yearPage = y - 1;
                var first = yearPage;
                html += head(first + ' ' + String.fromCharCode(8211) + ' ' + (first + 11), 'Previous years', 'Next years', null);
                html += '<div class="cdt-cal-grid cdt-grid-3">';
                for (var yy = first; yy < first + 12; yy++) {
                    var ycls = 'cdt-day cdt-cell';
                    if (yy === today.getFullYear()) ycls += ' is-today';
                    if (sel && yy === sel.getFullYear()) ycls += ' is-selected';
                    var yoff = !yearInRange(yy);
                    if (yoff) ycls += ' is-disabled';
                    html += '<button type="button" class="' + ycls + '" data-year="' + yy + '"' + (yoff ? ' disabled' : '') + '>' + yy + '</button>';
                }
                html += '</div>';
            } else if (mode === 'months') {
                html += head(String(y), 'Previous year', 'Next year', 'Choose year');
                html += '<div class="cdt-cal-grid cdt-grid-3">';
                for (var mm = 0; mm < 12; mm++) {
                    var mcls = 'cdt-day cdt-cell';
                    if (y === today.getFullYear() && mm === today.getMonth()) mcls += ' is-today';
                    if (sel && y === sel.getFullYear() && mm === sel.getMonth()) mcls += ' is-selected';
                    var moff = !monthInRange(y, mm);
                    if (moff) mcls += ' is-disabled';
                    html += '<button type="button" class="' + mcls + '" data-month="' + mm + '"' + (moff ? ' disabled' : '') + '>' + MONTHS_SHORT[mm] + '</button>';
                }
                html += '</div>';
            } else {
                var gridStart = new Date(y, m, 1 - new Date(y, m, 1).getDay());
                html += head(MONTHS[m] + ' ' + y, 'Previous month', 'Next month', 'Choose month and year');
                html += '<div class="cdt-cal-grid">';
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
                html += '</div>';
            }
            b.popup.innerHTML = html + foot();
            reposition();
        }
        b.wrap._render = render;

        b.popup.addEventListener('click', function (e) {
            var nav = e.target.closest('[data-nav]');
            if (nav) {
                var step = +nav.dataset.nav;
                if (mode === 'years') yearPage += 12 * step;
                else if (mode === 'months') view = new Date(view.getFullYear() + step, view.getMonth(), 1);
                else view = new Date(view.getFullYear(), view.getMonth() + step, 1);
                render();
                return;
            }
            if (e.target.closest('[data-up]')) {
                mode = mode === 'days' ? 'months' : 'years';
                yearPage = null;
                render();
                return;
            }
            var yearBtn = e.target.closest('[data-year]');
            if (yearBtn && !yearBtn.disabled) {
                view = new Date(+yearBtn.dataset.year, view.getMonth(), 1);
                mode = 'months';
                render();
                return;
            }
            var monthBtn = e.target.closest('[data-month]');
            if (monthBtn && !monthBtn.disabled) {
                view = new Date(view.getFullYear(), +monthBtn.dataset.month, 1);
                mode = 'days';
                render();
                return;
            }

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
                commit(input, ''); view = null; mode = null; syncLabel(); render();
            } else {
                var t = new Date();
                if (inRange(t)) {
                    commit(input, toISO(t));
                    view = new Date(t.getFullYear(), t.getMonth(), 1);
                    syncLabel(); close(b.wrap); b.trigger.focus();
                }
            }
        });

        // Resets the calendar to the picked date's month each time it opens.
        b.wrap._onOpen = function () { view = null; mode = null; yearPage = null; };
        input.addEventListener('change', function () { view = null; mode = null; syncLabel(); });
        syncLabel();
    }

    // Reads a time the user typed, like '2:30 pm' or '14:30'.
    function parseTypedTime(text) {
        var m = /^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/i.exec((text || '').trim());
        if (!m) return null;
        var h = parseInt(m[1], 10);
        var mins = m[2] !== undefined ? parseInt(m[2], 10) : 0;
        var period = m[3] ? m[3].toUpperCase() : null;
        if (mins > 59) return null;
        if (period) {
            if (h < 1 || h > 12) return null;
            return { h: h, m: mins, p: period };
        }
        if (h >= 0 && h <= 23) return { h: (h % 12) || 12, m: mins, p: h < 12 ? 'AM' : 'PM' };
        return null;
    }

    // Turns a time field into the custom time picker (hour, minute, AM/PM columns).
    // The user can also type the time.
    function enhanceTime(input) {
        var state = { h: null, m: null, p: null };

        // Reads the field's current time into the picker.
        function fromValue() {
            var v = input.value || '';
            if (!/^\d{2}:\d{2}/.test(v)) { state = { h: null, m: null, p: null }; return; }
            var H = +v.slice(0, 2), M = +v.slice(3, 5);
            state.p = H < 12 ? 'AM' : 'PM';
            state.h = H % 12 || 12;
            state.m = M;
        }
        // Saves the picked time into the real form field (in 24-hour format).
        function writeIfReady() {
            if (state.h == null) return;
            var mm = state.m == null ? 0 : state.m;
            var p = state.p || 'AM';
            var H = p === 'PM' ? (state.h % 12) + 12 : (state.h % 12);
            commit(input, pad(H) + ':' + pad(mm));
        }
        // Shows the picked time in the field (e.g. '2:30 PM').
        function syncLabel() {
            b.trigger.value = state.h != null ?
                (state.h + ':' + pad(state.m == null ? 0 : state.m) + ' ' + (state.p || 'AM')) : '';
        }
        // Saves a time the user typed in (or clears it if left empty).
        function commitTypedText() {
            var raw = b.trigger.value.trim();
            if (!raw) {
                state = { h: null, m: null, p: null };
                commit(input, '');
            } else {
                var parsed = parseTypedTime(raw);
                if (parsed) { state = parsed; writeIfReady(); }
            }
            syncLabel();
            if (b.wrap._render) b.wrap._render();
        }

        var b = baseWrap(input, 'time', {
            typeable: true, placeholder: 'Select time', icon: CLOCK_ICON,
            onCommitText: commitTypedText,
        });

        // Builds one column of the time picker (hours, minutes, or AM/PM).
        function column(name, items, current, fmt) {
            var h = '<ul class="cdt-col" data-col="' + name + '">';
            items.forEach(function (it) {
                var on = String(it) === String(current);
                h += '<li class="cdt-col-item' + (on ? ' is-selected' : '') + '" data-val="' + it + '">' +
                    (fmt ? fmt(it) : it) + '</li>';
            });
            return h + '</ul>';
        }
        // Draws the time picker with the current choice highlighted.
        function render() {
            var hrs = [], mins = [], i;
            for (i = 1; i <= 12; i++) hrs.push(i);
            for (i = 0; i < 60; i++) mins.push(i);
            b.popup.innerHTML =
                '<div class="cdt-time-head"><span>Hour</span><span>Min</span><span>AM/PM</span></div>' +
                '<div class="cdt-time-cols">' +
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

    // Turns a date or time field into its custom picker (skips fields marked to keep the default).
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
        var path = e.composedPath ? e.composedPath() : [];
        for (var i = 0; i < path.length; i++) {
            var el = path[i];
            if (el.classList && (el.classList.contains('cdt-wrap') || el.classList.contains('cdt-popup'))) return;
        }
        if (e.target.closest && (e.target.closest('.cdt-wrap') || e.target.closest('.cdt-popup'))) return;
        document.querySelectorAll('.cdt-wrap.is-open').forEach(close);
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') document.querySelectorAll('.cdt-wrap.is-open').forEach(close);
    });
})();
