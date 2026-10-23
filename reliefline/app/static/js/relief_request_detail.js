// Pop-up windows (modals) used on many pages: opening, closing, and fields that depend on a choice.
// Also the live 'before -> after' stock preview on transfer forms.
document.addEventListener('DOMContentLoaded', function () {
    // Shows only the form fields that match the selected option
    // (e.g. extra fields that appear only for 'Partial' or 'Damaged').
    function syncToggleFields(select) {
        var form = select.closest('form');
        if (!form) return;
        var value = select.value;
        var scope = select.dataset.toggleScope || '';
        form.querySelectorAll('[data-toggle-field]').forEach(function (field) {
            if ((field.dataset.toggleScope || '') !== scope) return;
            var values = field.dataset.toggleField.split(',');
            field.classList.toggle('is-visible', values.indexOf(value) !== -1);
        });
    }

    document.querySelectorAll('select[data-toggle-select]').forEach(function (select) {
        syncToggleFields(select);
        select.addEventListener('change', function () { syncToggleFields(select); });
    });

    // Stops the page behind an open pop-up from scrolling.
    function syncScrollLock() {
        var anyOpen = document.querySelector('.rd-modal-overlay:not([hidden])');
        document.documentElement.classList.toggle('rd-modal-open', !!anyOpen);
        var main = document.querySelector('.dashboard-main');
        if (main) main.style.overflow = anyOpen ? 'hidden' : '';
    }
    // Opens a pop-up window.
    function openModal(modal) {
        if (!modal) return;
        if (modal.parentNode !== document.body) document.body.appendChild(modal);
        modal.hidden = false;
        syncScrollLock();
    }
    // Closes a pop-up window.
    function closeModal(overlay) {
        overlay.hidden = true;
        syncScrollLock();
    }

    document.querySelectorAll('[data-open-modal]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            openModal(document.getElementById(btn.dataset.openModal));
        });
    });

    document.querySelectorAll('.rd-modal-overlay').forEach(function (overlay) {
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeModal(overlay);
        });
        overlay.querySelectorAll('[data-close-modal]').forEach(function (btn) {
            btn.addEventListener('click', function () { closeModal(overlay); });
        });
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.rd-modal-overlay').forEach(function (overlay) {
                overlay.hidden = true;
            });
            syncScrollLock();
        }
    });

    document.querySelectorAll('.rd-modal-overlay').forEach(function (overlay) {
        new MutationObserver(syncScrollLock).observe(overlay, {
            attributes: true, attributeFilter: ['hidden'],
        });
    });

    document.querySelectorAll('[data-batch-toggle]').forEach(function (btn) {
        var list = btn.closest('.wh-batch-contents').querySelector('.wh-batch-list');
        var label = btn.querySelector('.wh-batch-toggle-label');
        var count = btn.dataset.count;
        if (!list || !label) return;
        btn.addEventListener('click', function () {
            var open = btn.getAttribute('aria-expanded') === 'true';
            if (open) {
                list.style.maxHeight = list.scrollHeight + 'px';
                requestAnimationFrame(function () { list.style.maxHeight = '0px'; });
                btn.setAttribute('aria-expanded', 'false');
                label.textContent = 'View contents (' + count + ')';
            } else {
                btn.setAttribute('aria-expanded', 'true');
                list.style.maxHeight = list.scrollHeight + 'px';
                label.textContent = 'Hide contents (' + count + ')';
            }
        });
    });

    // Formats a number with commas (e.g. 12,345).
    function fmt(n) { return n.toLocaleString('en-US'); }

    // Sets up the live preview on a transfer form:
    // shows each warehouse's stock before and after the transfer as you type.
    function initTransferCalc(form) {
        var sourceSel = form.querySelector('[data-transfer-source]');
        var destSel = form.querySelector('[data-transfer-dest]');
        var qtyInput = form.querySelector('[data-transfer-qty]');
        var preview = form.querySelector('[data-transfer-preview]');
        if (!sourceSel || !qtyInput || !preview) return;

        // The name of the selected warehouse.
        function optName(sel) {
            var opt = sel.options[sel.selectedIndex];
            if (!opt || !opt.value) return null;
            return (opt.textContent.split(' - ')[0] || opt.textContent).trim();
        }
        // Reads a number (0 if empty or not a number).
        function num(v) { var n = parseInt(v, 10); return isNaN(n) ? 0 : n; }

        // The chosen 'from' warehouse and how many packs it has.
        function selectedSource() {
            var opt = sourceSel.options[sourceSel.selectedIndex];
            if (!opt || !opt.value) return null;
            return { name: optName(sourceSel), available: num(opt.dataset.available) };
        }
        // The chosen 'to' warehouse, its current stock and its capacity.
        function selectedDest() {
            if (destSel) {
                var opt = destSel.options[destSel.selectedIndex];
                if (!opt || !opt.value) return null;
                return { name: optName(destSel), current: num(opt.dataset.current), capacity: num(opt.dataset.capacity) };
            }
            return {
                name: form.dataset.destName || 'Destination',
                current: num(form.dataset.destCurrent),
                capacity: num(form.dataset.destCapacity),
            };
        }

        // Builds one 'before -> after' line of the preview.
        function row(label, before, after, extraClass, note) {
            return '<div class="tcp-row">' +
                '<span class="tcp-label">' + label + '</span>' +
                '<span class="tcp-flow"><span>' + fmt(before) + '</span>' +
                '<span class="tcp-arrow">&rarr;</span>' +
                '<strong class="' + (extraClass || '') + '">' + fmt(after) + '</strong></span>' +
                (note ? '<span class="tcp-note ' + (extraClass || '') + '">' + note + '</span>' : '') +
                '</div>';
        }

        // Updates the preview when the user changes the form,
        // and warns if the source doesn't have enough stock or the destination would be over capacity.
        function update() {
            var src = selectedSource();
            var dst = selectedDest();
            var qty = num(qtyInput.value);

            if (!src || !dst || qty <= 0) { preview.hidden = true; preview.innerHTML = ''; return; }

            var srcAfter = src.available - qty;
            var dstAfter = dst.current + qty;
            var html = '';

            var srcNote = srcAfter < 0 ? ('Short ' + fmt(Math.abs(srcAfter)) + ' packs') : 'remaining';
            html += row('From ' + src.name, src.available, srcAfter, srcAfter < 0 ? 'tcp-bad' : '', srcNote);

            var dstNote = 'projected';
            var dstClass = 'tcp-good';
            if (dst.capacity > 0) {
                var pct = Math.round((dstAfter / dst.capacity) * 100);
                dstNote = pct + '% of capacity';
                if (dstAfter > dst.capacity) { dstClass = 'tcp-warn'; dstNote = 'Over capacity by ' + fmt(dstAfter - dst.capacity); }
            }
            html += row('To ' + dst.name, dst.current, dstAfter, dstClass, dstNote);

            preview.innerHTML = html;
            preview.hidden = false;
        }

        [sourceSel, destSel, qtyInput].forEach(function (el) {
            if (!el) return;
            el.addEventListener('input', update);
            el.addEventListener('change', update);
        });
        update();
    }

    document.querySelectorAll('form[data-transfer-calc]').forEach(initTransferCalc);
});

document.addEventListener('change', function (e) {
    var t = e.target;
    if (t.matches('[data-fp-include]')) {
        var row = t.closest('.fp-content-row');
        var date = row.querySelector('[data-fp-date]');
        var qty = row.querySelector('[data-fp-qty]');
        if (date) {
            date.hidden = !t.checked;
            if (!t.checked) date.value = '';
        }
        if (qty) qty.hidden = !t.checked;
    } else if (t.matches('[data-fp-others-toggle]')) {
        var wrap = t.closest('[data-fp-contents]').querySelector('[data-fp-others]');
        wrap.hidden = !t.checked;
        if (!t.checked) {
            wrap.querySelectorAll('input').forEach(function (i) { i.value = ''; });
        }
    }
});

document.addEventListener('click', function (e) {
    var add = e.target.closest('[data-fp-other-add]');
    if (add) {
        var list = add.closest('[data-fp-others]').querySelector('[data-fp-others-list]');
        var clone = list.querySelector('[data-fp-other-row]').cloneNode(true);
        clone.querySelectorAll('input').forEach(function (i) { i.value = ''; });
        list.appendChild(clone);
        return;
    }
    var rm = e.target.closest('[data-fp-other-remove]');
    if (rm) {
        var row = rm.closest('[data-fp-other-row]');
        var rows = row.parentNode.querySelectorAll('[data-fp-other-row]');
        if (rows.length > 1) row.remove();
        else row.querySelectorAll('input').forEach(function (i) { i.value = ''; });
    }
});
