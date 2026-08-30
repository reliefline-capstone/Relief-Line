document.addEventListener('DOMContentLoaded', function () {
    // Generic conditional-field toggle (e.g. "Source: Donation" revealing a
    // Donor Name field) — same pattern as admin.js's role-field toggle, scoped
    // here to whatever form the triggering select lives in.
    function syncToggleFields(select) {
        var form = select.closest('form');
        if (!form) return;
        var value = select.value;
        form.querySelectorAll('[data-toggle-field]').forEach(function (field) {
            var values = field.dataset.toggleField.split(',');
            field.classList.toggle('is-visible', values.indexOf(value) !== -1);
        });
    }

    document.querySelectorAll('select[data-toggle-select]').forEach(function (select) {
        syncToggleFields(select);
        select.addEventListener('change', function () { syncToggleFields(select); });
    });

    // While any modal is open, lock the page behind it so the mouse wheel
    // scrolls the modal (or nothing), never the list underneath.
    function syncScrollLock() {
        var anyOpen = document.querySelector('.rd-modal-overlay:not([hidden])');
        document.documentElement.classList.toggle('rd-modal-open', !!anyOpen);
        // .dashboard-main is the scroll container on these pages; belt-and-
        // braces inline lock in case a stylesheet rule doesn't win.
        var main = document.querySelector('.dashboard-main');
        if (main) main.style.overflow = anyOpen ? 'hidden' : '';
    }
    function openModal(modal) {
        if (!modal) return;
        // .dashboard-main keeps a retained transform from its entrance
        // animation, which makes it the containing block for position:fixed —
        // so an overlay nested inside it is offset by the sidebar and scrolls
        // away with the list. Re-parenting to <body> pins it to the viewport.
        if (modal.parentNode !== document.body) document.body.appendChild(modal);
        modal.hidden = false;
        syncScrollLock();
    }
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

    // Catch every other way a modal gets shown/hidden (e.g. weather_widget.js
    // toggling .hidden directly) so the scroll-lock stays in sync regardless.
    document.querySelectorAll('.rd-modal-overlay').forEach(function (overlay) {
        new MutationObserver(syncScrollLock).observe(overlay, {
            attributes: true, attributeFilter: ['hidden'],
        });
    });

    // Live "stock after transfer" calculation for warehouse -> warehouse moves
    // (Pre-position Stock modal + Approve Stock Request modal).
    function fmt(n) { return n.toLocaleString('en-US'); }

    function initTransferCalc(form) {
        var sourceSel = form.querySelector('[data-transfer-source]');
        var destSel = form.querySelector('[data-transfer-dest]');
        var qtyInput = form.querySelector('[data-transfer-qty]');
        var preview = form.querySelector('[data-transfer-preview]');
        if (!sourceSel || !qtyInput || !preview) return;

        function optName(sel) {
            var opt = sel.options[sel.selectedIndex];
            if (!opt || !opt.value) return null;
            return (opt.textContent.split(' — ')[0] || opt.textContent).trim();
        }
        function num(v) { var n = parseInt(v, 10); return isNaN(n) ? 0 : n; }

        function selectedSource() {
            var opt = sourceSel.options[sourceSel.selectedIndex];
            if (!opt || !opt.value) return null;
            return { name: optName(sourceSel), available: num(opt.dataset.available) };
        }
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

        function row(label, before, after, extraClass, note) {
            return '<div class="tcp-row">' +
                '<span class="tcp-label">' + label + '</span>' +
                '<span class="tcp-flow"><span>' + fmt(before) + '</span>' +
                '<span class="tcp-arrow">&rarr;</span>' +
                '<strong class="' + (extraClass || '') + '">' + fmt(after) + '</strong></span>' +
                (note ? '<span class="tcp-note ' + (extraClass || '') + '">' + note + '</span>' : '') +
                '</div>';
        }

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
